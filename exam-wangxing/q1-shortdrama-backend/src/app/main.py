"""FastAPI 应用：REST API + Stripe / Apple Webhook。"""
from __future__ import annotations

import json
import os
import sqlite3
from typing import Any, Generator

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import config
from .apple_parse import apple_notification_uuid, extract_order_id_from_apple_body
from .db import get_connection, init_db
from .services import (
    create_order,
    expire_subscription_demo,
    get_order_bundle,
    mark_order_expired_if_period_passed,
    process_apple_notification,
    process_stripe_checkout_completed,
)
from .stripe_verify import verify_stripe_signature

app = FastAPI(title="Short Drama Subscription API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


class CreateOrderBody(BaseModel):
    user_id: str = Field(..., min_length=1)
    plan_id: str = Field(..., min_length=1)
    idempotency_key: str = Field(..., min_length=4)


def db() -> Generator[sqlite3.Connection, None, None]:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/plans")
def list_plans(conn: sqlite3.Connection = Depends(db)) -> list[dict[str, Any]]:
    cur = conn.execute("SELECT id, name, price_cents, currency, duration_days, stock_remaining FROM plans")
    return [dict(r) for r in cur.fetchall()]


@app.get("/api/orders")
def list_orders(user_id: str | None = None, conn: sqlite3.Connection = Depends(db)) -> list[dict[str, Any]]:
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id_required")
    cur = conn.execute(
        "SELECT id FROM orders WHERE user_id = ? ORDER BY datetime(created_at) DESC LIMIT 100",
        (user_id,),
    )
    out: list[dict[str, Any]] = []
    for r in cur.fetchall():
        oid = r["id"]
        try:
            out.append(mark_order_expired_if_period_passed(conn, oid))
        except KeyError:
            continue
    return out


@app.post("/api/orders")
def post_order(body: CreateOrderBody, conn: sqlite3.Connection = Depends(db)) -> dict[str, Any]:
    try:
        return create_order(
            conn,
            user_id=body.user_id,
            plan_id=body.plan_id,
            idempotency_key=body.idempotency_key,
        )
    except ValueError as e:
        code = str(e)
        if code == "unknown_plan":
            raise HTTPException(status_code=400, detail="unknown_plan")
        if code == "plan_out_of_stock":
            raise HTTPException(status_code=409, detail="plan_out_of_stock")
        raise


@app.get("/api/orders/{order_id}")
def get_order(order_id: str, conn: sqlite3.Connection = Depends(db)) -> dict[str, Any]:
    try:
        return mark_order_expired_if_period_passed(conn, order_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="order_not_found")


@app.post("/api/orders/{order_id}/expire")
def post_expire(order_id: str, conn: sqlite3.Connection = Depends(db)) -> dict[str, Any]:
    """演示：将 active 订阅强制迁移到 expired（非法迁移会 409）。"""
    try:
        return expire_subscription_demo(conn, order_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="order_not_found")
    except Exception as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request, conn: sqlite3.Connection = Depends(db)) -> Response:
    body = await request.body()
    sig = request.headers.get("stripe-signature") or request.headers.get("Stripe-Signature") or ""
    ok, reason = verify_stripe_signature(
        body,
        sig,
        config.STRIPE_WEBHOOK_SECRET,
        config.STRIPE_SIGNATURE_TOLERANCE_SECONDS,
    )
    if not ok:
        return JSONResponse(status_code=401, content={"error": "invalid_signature", "reason": reason})

    try:
        event = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content={"error": "invalid_json"})

    evt_id = event.get("id")
    evt_type = event.get("type")
    if not evt_id or not evt_type:
        return JSONResponse(status_code=400, content={"error": "invalid_event_envelope"})

    obj = event.get("data", {}).get("object", {})
    metadata = obj.get("metadata") or {}
    order_id = metadata.get("order_id")
    if not order_id:
        return JSONResponse(status_code=400, content={"error": "missing_order_id_metadata"})

    raw = body.decode("utf-8")
    result = process_stripe_checkout_completed(
        conn,
        provider_event_id=str(evt_id),
        order_id=str(order_id),
        raw_payload=raw,
        signature_valid=True,
    )

    if not result.get("ok"):
        err = result.get("error", "")
        if err == "unknown_order":
            return JSONResponse(status_code=404, content=result)
        if err == "order_terminal_state":
            return JSONResponse(status_code=409, content=result)
        return JSONResponse(status_code=400, content=result)

    return JSONResponse(status_code=200, content=result)


@app.post("/webhooks/apple")
async def apple_webhook(
    request: Request,
    conn: sqlite3.Connection = Depends(db),
    x_apple_receipt_secret: str | None = Header(default=None, alias="X-Apple-Receipt-Secret"),
) -> Response:
    if x_apple_receipt_secret != config.APPLE_SHARED_SECRET:
        return JSONResponse(status_code=401, content={"error": "apple_auth_failed"})

    try:
        body = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content={"error": "invalid_json"})

    if not isinstance(body, dict):
        return JSONResponse(status_code=400, content={"error": "invalid_body"})

    ntype = body.get("notificationType")
    nu = apple_notification_uuid(body)
    if not ntype or not nu:
        return JSONResponse(status_code=400, content={"error": "missing_notification_fields"})

    order_id = extract_order_id_from_apple_body(body)
    raw = json.dumps(body, ensure_ascii=False)
    result = process_apple_notification(
        conn,
        provider_event_id=str(nu),
        notification_type=str(ntype),
        order_id=order_id,
        raw_payload=raw,
        apple_ok=True,
    )

    if not result.get("ok"):
        err = result.get("error", "")
        if err == "unknown_order":
            return JSONResponse(status_code=404, content=result)
        if err == "order_terminal_state":
            return JSONResponse(status_code=409, content=result)
        if "missing_order" in err:
            return JSONResponse(status_code=400, content=result)
        return JSONResponse(status_code=400, content=result)

    return JSONResponse(status_code=200, content=result)


static_dir = os.environ.get("STATIC_DIR")
if static_dir and os.path.isdir(static_dir):
    from pathlib import Path

    from fastapi.responses import FileResponse

    _root = Path(static_dir)

    @app.get("/", include_in_schema=False)
    def spa_root() -> FileResponse:
        return FileResponse(_root / "index.html")

    _assets = _root / "assets"
    if _assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(_assets)), name="assets")
