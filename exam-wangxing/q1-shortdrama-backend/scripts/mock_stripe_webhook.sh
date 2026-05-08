#!/usr/bin/env bash
# 向 /webhooks/stripe 发送 checkout.session.completed 风格事件（metadata.order_id）
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="${BASE_URL:-http://127.0.0.1:8000}"
export STRIPE_WEBHOOK_SECRET="${STRIPE_WEBHOOK_SECRET:-whsec_test_local_default_secret}"

ORDER_ID="${1:?用法: $0 <order_id> [evt_id]}"
EVT_ID="${2:-evt_$(openssl rand -hex 12)}"

BODY="$(python3 - "$ORDER_ID" "$EVT_ID" <<'PY'
import json, os, sys, uuid
order_id, evt_id = sys.argv[1], sys.argv[2]
print(json.dumps({
  "id": evt_id,
  "object": "event",
  "api_version": "2023-10-16",
  "type": "checkout.session.completed",
  "data": {
    "object": {
      "id": "cs_test_" + uuid.uuid4().hex[:20],
      "object": "checkout.session",
      "metadata": {"order_id": order_id},
      "payment_status": "paid",
    }
  },
}))
PY
)"

TS="$(python3 -c "import time; print(int(time.time()))")"
SIG="$(printf '%s' "$BODY" | python3 "$SCRIPT_DIR/stripe_sign.py" "$TS")"

curl -sS -X POST "${BASE}/webhooks/stripe" \
  -H "Content-Type: application/json; charset=utf-8" \
  -H "Stripe-Signature: t=${TS},v1=${SIG}" \
  -d "$BODY" | python3 -m json.tool
