"""异常路径：重复 webhook 幂等、签名校验失败、未知 / 已终止订单。"""
from __future__ import annotations

import hashlib
import hmac
import json
import time

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

SECRET = "whsec_test_fixture_secret"


def sign_stripe(body: bytes, ts: int | None = None) -> str:
    t = int(time.time()) if ts is None else ts
    signed = f"{t}.".encode("ascii") + body
    v1 = hmac.new(SECRET.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return f"t={t},v1={v1}"


async def _create_order(client: AsyncClient) -> str:
    r = await client.post(
        "/api/orders",
        json={
            "user_id": "u_webhook",
            "plan_id": "plan_monthly",
            "idempotency_key": "idem-test-webhook-1",
        },
    )
    assert r.status_code == 200
    return r.json()["order"]["id"]


async def test_duplicate_stripe_webhook_idempotent_no_extra_stock(client: AsyncClient) -> None:
    oid = await _create_order(client)
    evt = {
        "id": "evt_dup_test_001",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_dup",
                "object": "checkout.session",
                "metadata": {"order_id": oid},
            }
        },
    }
    raw = json.dumps(evt).encode()
    sig = sign_stripe(raw)
    r1 = await client.post("/webhooks/stripe", content=raw, headers={"Stripe-Signature": sig})
    assert r1.status_code == 200
    r2 = await client.post("/webhooks/stripe", content=raw, headers={"Stripe-Signature": sig})
    assert r2.status_code == 200
    j = r2.json()
    assert j.get("duplicate") is True or j.get("idempotent") is True

    # 再次建单前查库存
    plans = await client.get("/api/plans")
    stocks = {p["id"]: p["stock_remaining"] for p in plans.json()}
    # 只扣一次：与种子 500 相比应只少 1（若其它测试污染则至少重复请求不会继续扣）
    assert stocks.get("plan_monthly") == 499


async def test_stripe_signature_invalid(client: AsyncClient) -> None:
    oid = await _create_order(client)
    evt = {
        "id": "evt_sig_bad",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_bad",
                "object": "checkout.session",
                "metadata": {"order_id": oid},
            }
        },
    }
    raw = json.dumps(evt).encode()
    r = await client.post(
        "/webhooks/stripe",
        content=raw,
        headers={"Stripe-Signature": "t=123,v1=deadbeef"},
    )
    assert r.status_code == 401


async def test_unknown_order_id(client: AsyncClient) -> None:
    evt = {
        "id": "evt_unknown_order",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_unknown",
                "object": "checkout.session",
                "metadata": {"order_id": "ord_nonexistent_aaaaaaaa"},
            }
        },
    }
    raw = json.dumps(evt).encode()
    sig = sign_stripe(raw)
    r = await client.post("/webhooks/stripe", content=raw, headers={"Stripe-Signature": sig})
    assert r.status_code == 404
    assert r.json().get("error") == "unknown_order"


async def test_expired_order_webhook_rejected(client: AsyncClient) -> None:
    oid = await _create_order(client)
    evt = {
        "id": "evt_after_expire",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_exp",
                "object": "checkout.session",
                "metadata": {"order_id": oid},
            }
        },
    }
    raw = json.dumps(evt).encode()
    sig = sign_stripe(raw)
    pay = await client.post("/webhooks/stripe", content=raw, headers={"Stripe-Signature": sig})
    assert pay.status_code == 200

    ex = await client.post(f"/api/orders/{oid}/expire")
    assert ex.status_code == 200

    evt2 = {
        "id": "evt_after_expire_2",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_exp2",
                "object": "checkout.session",
                "metadata": {"order_id": oid},
            }
        },
    }
    raw2 = json.dumps(evt2).encode()
    sig2 = sign_stripe(raw2)
    r = await client.post("/webhooks/stripe", content=raw2, headers={"Stripe-Signature": sig2})
    assert r.status_code == 409
