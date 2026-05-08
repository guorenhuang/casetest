"""Stripe Webhook 签名校验（Stripe-Signature：t + v1 HMAC-SHA256，时间戳容忍）。"""
from __future__ import annotations

import hashlib
import hmac
import time
from typing import Tuple


def parse_stripe_signature_header(header_value: str) -> tuple[int, str] | None:
    """
    解析 Stripe-Signature: t=xxx,v1=yyy[,v0=...]
    返回 (timestamp, v1_hex_signature)
    """
    if not header_value:
        return None
    ts = None
    v1 = None
    for part in header_value.split(","):
        part = part.strip()
        if "=" not in part:
            continue
        k, _, v = part.partition("=")
        k, v = k.strip(), v.strip()
        if k == "t":
            try:
                ts = int(v)
            except ValueError:
                return None
        elif k == "v1":
            v1 = v
    if ts is None or not v1:
        return None
    return ts, v1


def compute_stripe_v1(secret: str, payload: bytes, timestamp: int) -> str:
    """signed_payload = "{t}." + raw_body (utf-8), HMAC-SHA256 hex."""
    signed = f"{timestamp}.".encode("ascii") + payload
    digest = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return digest


def verify_stripe_signature(
    payload: bytes,
    stripe_signature_header: str,
    secret: str,
    tolerance_seconds: int,
) -> Tuple[bool, str]:
    parsed = parse_stripe_signature_header(stripe_signature_header)
    if not parsed:
        return False, "missing_or_invalid_stripe_signature_header"
    ts, expected_v1 = parsed
    now = int(time.time())
    if abs(now - ts) > tolerance_seconds:
        return False, "timestamp_outside_tolerance"
    digest = compute_stripe_v1(secret, payload, ts)
    if not hmac.compare_digest(digest, expected_v1):
        return False, "signature_mismatch"
    return True, "ok"
