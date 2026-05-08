"""业务：创建订单、处理 Stripe / Apple 回调、幂等、库存扣减。"""
from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import sqlite3

from . import config
from .state_machine import OrderStatus, StateMachineError, SubscriptionStatus, transition_order, transition_subscription


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def generate_order_id() -> str:
    return f"ord_{secrets.token_hex(8)}"


def create_order(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    plan_id: str,
    idempotency_key: str,
) -> dict[str, Any]:
    cur = conn.execute("SELECT stock_remaining FROM plans WHERE id = ?", (plan_id,))
    row = cur.fetchone()
    if not row:
        raise ValueError("unknown_plan")
    if row["stock_remaining"] <= 0:
        raise ValueError("plan_out_of_stock")

    cur = conn.execute(
        "SELECT id FROM orders WHERE idempotency_key = ?", (idempotency_key,)
    )
    existing = cur.fetchone()
    if existing:
        return get_order_bundle(conn, existing["id"])

    p = conn.execute(
        "SELECT price_cents, currency, duration_days FROM plans WHERE id = ?", (plan_id,)
    ).fetchone()
    assert p

    oid = generate_order_id()
    conn.execute(
        """
        INSERT INTO orders (id, user_id, plan_id, idempotency_key, status, amount_cents, currency)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            oid,
            user_id,
            plan_id,
            idempotency_key,
            OrderStatus.pending.value,
            p["price_cents"],
            p["currency"],
        ),
    )
    conn.execute(
        """
        INSERT INTO subscriptions (order_id, user_id, status)
        VALUES (?, ?, ?)
        """,
        (oid, user_id, SubscriptionStatus.pending.value),
    )
    conn.commit()
    return get_order_bundle(conn, oid)


def get_order_bundle(conn: sqlite3.Connection, order_id: str) -> dict[str, Any]:
    o = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not o:
        raise KeyError("order_not_found")
    s = conn.execute(
        "SELECT * FROM subscriptions WHERE order_id = ?", (order_id,)
    ).fetchone()
    od = dict(o)
    sd = dict(s) if s else None
    return {"order": od, "subscription": sd}


def mark_order_expired_if_period_passed(conn: sqlite3.Connection, order_id: str) -> dict[str, Any]:
    """若当前时间已超过订阅结束时间，则将订单/订阅推进到 expired。"""
    bundle = get_order_bundle(conn, order_id)
    o, s = bundle["order"], bundle.get("subscription")
    if not s:
        return bundle
    if o["status"] != OrderStatus.active.value or s["status"] != SubscriptionStatus.active.value:
        return bundle
    end = s.get("current_period_end")
    if not end:
        return bundle
    try:
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
    except ValueError:
        return bundle
    if datetime.now(timezone.utc) <= end_dt:
        return bundle

    transition_order(o["status"], OrderStatus.expired)
    transition_subscription(s["status"], SubscriptionStatus.expired)
    conn.execute(
        "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
        (OrderStatus.expired.value, _now_iso(), order_id),
    )
    conn.execute(
        "UPDATE subscriptions SET status = ?, updated_at = ? WHERE order_id = ?",
        (SubscriptionStatus.expired.value, _now_iso(), order_id),
    )
    conn.commit()
    return get_order_bundle(conn, order_id)


def process_stripe_checkout_completed(
    conn: sqlite3.Connection,
    *,
    provider_event_id: str,
    order_id: str,
    raw_payload: str,
    signature_valid: bool,
) -> dict[str, Any]:
    """Stripe checkout.session.completed / invoice.payment_succeeded 等：metadata.order_id。"""
    if not signature_valid:
        return {"ok": False, "error": "invalid_signature", "idempotent": False}

    try:
        conn.execute("BEGIN IMMEDIATE")
        dup = conn.execute(
            """
            SELECT order_id FROM payment_events
            WHERE channel = 'stripe' AND provider_event_id = ?
            """,
            (provider_event_id,),
        ).fetchone()
        if dup:
            oid = dup["order_id"]
            conn.commit()
            bundle = get_order_bundle(conn, oid) if oid else None
            return {"ok": True, "idempotent": True, "duplicate": True, "order": bundle}

        o = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not o:
            conn.rollback()
            return {"ok": False, "error": "unknown_order", "idempotent": False}

        if o["status"] in (OrderStatus.expired.value, OrderStatus.refunded.value):
            conn.rollback()
            return {"ok": False, "error": "order_terminal_state", "idempotent": False}

        if o["status"] in (OrderStatus.paid.value, OrderStatus.active.value):
            conn.execute(
                """
                INSERT INTO payment_events
                  (channel, provider_event_id, order_id, idempotency_key, signature_valid, raw_payload)
                VALUES ('stripe', ?, ?, ?, 1, ?)
                """,
                (provider_event_id, order_id, f"stripe:{provider_event_id}", raw_payload),
            )
            conn.commit()
            return {
                "ok": True,
                "idempotent": True,
                "already_fulfilled": True,
                "order": get_order_bundle(conn, order_id),
            }

        conn.execute(
            """
            INSERT INTO payment_events
              (channel, provider_event_id, order_id, idempotency_key, signature_valid, raw_payload)
            VALUES ('stripe', ?, ?, ?, 1, ?)
            """,
            (provider_event_id, order_id, f"stripe:{provider_event_id}", raw_payload),
        )

        _fulfill_order_after_payment(conn, order_id)
        conn.commit()
        return {"ok": True, "idempotent": False, "order": get_order_bundle(conn, order_id)}
    except StateMachineError as e:
        conn.rollback()
        return {"ok": False, "error": str(e), "idempotent": False}


def _fulfill_order_after_payment(conn: sqlite3.Connection, order_id: str) -> None:
    o = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    s = conn.execute(
        "SELECT * FROM subscriptions WHERE order_id = ?", (order_id,)
    ).fetchone()
    if not o or not s:
        raise KeyError("order_or_subscription_missing")

    transition_order(o["status"], OrderStatus.paid)
    conn.execute(
        "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
        (OrderStatus.paid.value, _now_iso(), order_id),
    )

    plan = conn.execute(
        "SELECT duration_days, stock_remaining FROM plans WHERE id = ?", (o["plan_id"],)
    ).fetchone()
    if not plan:
        raise ValueError("plan_missing")

    u = conn.execute(
        """
        UPDATE plans SET stock_remaining = stock_remaining - 1
        WHERE id = ? AND stock_remaining > 0
        """,
        (o["plan_id"],),
    )
    if u.rowcount != 1:
        raise ValueError("stock_decrement_failed")

    start = datetime.now(timezone.utc)
    end = start + timedelta(days=int(plan["duration_days"]))

    transition_order(OrderStatus.paid.value, OrderStatus.active)
    conn.execute(
        "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
        (OrderStatus.active.value, _now_iso(), order_id),
    )

    transition_subscription(s["status"], SubscriptionStatus.active)
    conn.execute(
        """
        UPDATE subscriptions
        SET status = ?, current_period_start = ?, current_period_end = ?, updated_at = ?
        WHERE order_id = ?
        """,
        (
            SubscriptionStatus.active.value,
            start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            _now_iso(),
            order_id,
        ),
    )


def process_apple_notification(
    conn: sqlite3.Connection,
    *,
    provider_event_id: str,
    notification_type: str,
    order_id: str | None,
    raw_payload: str,
    apple_ok: bool,
) -> dict[str, Any]:
    if not apple_ok:
        return {"ok": False, "error": "apple_auth_failed", "idempotent": False}

    if not order_id:
        return {"ok": False, "error": "missing_order_in_payload", "idempotent": False}

    try:
        conn.execute("BEGIN IMMEDIATE")
        dup = conn.execute(
            """
            SELECT order_id FROM payment_events
            WHERE channel = 'apple' AND provider_event_id = ?
            """,
            (provider_event_id,),
        ).fetchone()
        if dup:
            oid = dup["order_id"]
            conn.commit()
            return {
                "ok": True,
                "idempotent": True,
                "duplicate": True,
                "order": get_order_bundle(conn, oid),
            }

        o = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not o:
            conn.rollback()
            return {"ok": False, "error": "unknown_order", "idempotent": False}

        if o["status"] in (OrderStatus.expired.value, OrderStatus.refunded.value):
            conn.rollback()
            return {"ok": False, "error": "order_terminal_state", "idempotent": False}

        if o["status"] in (OrderStatus.paid.value, OrderStatus.active.value):
            conn.execute(
                """
                INSERT INTO payment_events
                  (channel, provider_event_id, order_id, idempotency_key, signature_valid, raw_payload)
                VALUES ('apple', ?, ?, ?, 1, ?)
                """,
                (provider_event_id, order_id, f"apple:{provider_event_id}", raw_payload),
            )
            conn.commit()
            return {
                "ok": True,
                "idempotent": True,
                "already_fulfilled": True,
                "order": get_order_bundle(conn, order_id),
            }

        if notification_type in (
            "SUBSCRIBED",
            "DID_RENEW",
            "INITIAL_BUY",
            "ONE_TIME_CHARGE",
        ):
            conn.execute(
                """
                INSERT INTO payment_events
                  (channel, provider_event_id, order_id, idempotency_key, signature_valid, raw_payload)
                VALUES ('apple', ?, ?, ?, 1, ?)
                """,
                (provider_event_id, order_id, f"apple:{provider_event_id}", raw_payload),
            )
            _fulfill_order_after_payment(conn, order_id)
            conn.commit()
            return {"ok": True, "idempotent": False, "order": get_order_bundle(conn, order_id)}

        conn.rollback()
        return {"ok": False, "error": f"unhandled_notification_type:{notification_type}", "idempotent": False}
    except StateMachineError as e:
        conn.rollback()
        return {"ok": False, "error": str(e), "idempotent": False}


def expire_subscription_demo(conn: sqlite3.Connection, order_id: str) -> dict[str, Any]:
    """人工触发到期（演示 expired 迁移）。"""
    bundle = get_order_bundle(conn, order_id)
    o = bundle["order"]
    s = bundle.get("subscription")
    if not s:
        raise KeyError("no_subscription")
    transition_order(o["status"], OrderStatus.expired)
    transition_subscription(s["status"], SubscriptionStatus.expired)
    conn.execute(
        "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
        (OrderStatus.expired.value, _now_iso(), order_id),
    )
    conn.execute(
        "UPDATE subscriptions SET status = ?, updated_at = ? WHERE order_id = ?",
        (SubscriptionStatus.expired.value, _now_iso(), order_id),
    )
    conn.commit()
    return get_order_bundle(conn, order_id)
