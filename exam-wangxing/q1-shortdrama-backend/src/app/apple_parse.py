"""从 Apple ASN 风格 body 解析订单 ID：mock JWT `signedTransactionInfo` → payload.appAccountToken。"""
from __future__ import annotations

import base64
import binascii
import json
from typing import Any


def _b64url_decode(seg: str) -> bytes:
    pad = "=" * ((4 - len(seg) % 4) % 4)
    return base64.urlsafe_b64decode(seg + pad)


def decode_jwt_payload_unverified(token: str) -> dict[str, Any] | None:
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return None
        raw = _b64url_decode(parts[1])
        return json.loads(raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError, binascii.Error):
        return None


def extract_order_id_from_apple_body(body: dict[str, Any]) -> str | None:
    data = body.get("data")
    if isinstance(data, dict):
        st = data.get("signedTransactionInfo")
        if isinstance(st, str):
            pl = decode_jwt_payload_unverified(st)
            if pl:
                tok = pl.get("appAccountToken")
                if isinstance(tok, str) and tok.startswith("ord_"):
                    return tok
        # 兼容：部分 mock 直接把业务单号放在 appAccountToken（明文 UUID 外允许演示用 ord_）
        tok2 = data.get("appAccountToken")
        if isinstance(tok2, str) and tok2.startswith("ord_"):
            return tok2
    return None


def apple_notification_uuid(body: dict[str, Any]) -> str | None:
    u = body.get("notificationUUID")
    return u if isinstance(u, str) else None
