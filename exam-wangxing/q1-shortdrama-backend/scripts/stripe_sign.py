#!/usr/bin/env python3
"""根据 Stripe 规则生成 v1 签名：signed = f\"{t}.\" + raw_body_bytes，HMAC-SHA256(secret, signed) hex。"""
import hashlib
import hmac
import os
import sys

SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_test_local_default_secret")


def main() -> None:
    ts = sys.argv[1]
    body = sys.stdin.buffer.read()
    signed = f"{ts}.".encode("ascii") + body
    dig = hmac.new(SECRET.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    print(dig, end="")


if __name__ == "__main__":
    main()
