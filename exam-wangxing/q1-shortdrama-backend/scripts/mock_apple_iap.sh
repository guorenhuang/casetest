#!/usr/bin/env bash
# App Store Server Notifications 风格 JSON：notificationType / notificationUUID / data.signedTransactionInfo(JWT payload 内含 appAccountToken=订单号)
set -euo pipefail
BASE="${BASE_URL:-http://127.0.0.1:8000}"
export APPLE_SHARED_SECRET="${APPLE_SHARED_SECRET:-apple_shared_mock_secret}"

ORDER_ID="${1:?用法: $0 <order_id>}"

BODY="$(python3 - "$ORDER_ID" <<'PY'
import base64, json, os, sys, uuid

def b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")

order_id = sys.argv[1]
inner = {"appAccountToken": order_id, "transactionId": "2000000" + str(abs(hash(order_id)) % 10**8)}
# 两段的 mock JWT，仅用于 payload 可被服务端无校验解码（真实环境需 JWS + Apple 证书）
payload = b64url(json.dumps(inner).encode())
header = b64url(json.dumps({"alg": "none", "typ": "JWT"}).encode())
signed_transaction_info = header + "." + payload

body = {
    "notificationType": "SUBSCRIBED",
    "subtype": "INITIAL_BUY",
    "notificationUUID": str(uuid.uuid4()),
    "data": {
        "appAppleId": 1234567890,
        "bundleId": "com.example.shortdrama",
        "bundleVersion": "1",
        "environment": "Sandbox",
        "signedTransactionInfo": signed_transaction_info,
    },
}
print(json.dumps(body))
PY
)"

curl -sS -X POST "${BASE}/webhooks/apple" \
  -H "Content-Type: application/json; charset=utf-8" \
  -H "X-Apple-Receipt-Secret: ${APPLE_SHARED_SECRET}" \
  -d "$BODY" | python3 -m json.tool
