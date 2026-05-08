#!/usr/bin/env bash
# 端到端：创建订单 → Stripe Webhook → 查询为 active；再次相同 Webhook 验证幂等
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
export STRIPE_WEBHOOK_SECRET="${STRIPE_WEBHOOK_SECRET:-whsec_test_local_default_secret}"

BASE="$BASE_URL"

echo "== 1) 健康检查"
curl -sS "${BASE}/health" | python3 -m json.tool

echo ""
echo "== 2) 创建订单（月度 VIP）"
RESP="$(curl -sS -X POST "${BASE}/api/orders" \
  -H "Content-Type: application/json" \
  -d "$(python3 -c 'import json,time; print(json.dumps({"user_id":"user_demo_001","plan_id":"plan_monthly","idempotency_key":"happy-{}".format(int(time.time()))}))')")"
echo "$RESP" | python3 -m json.tool
ORDER_ID="$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['order']['id'])")"
FIXED_EVT="evt_happy_path_fixed_demo"

echo ""
echo "== 3) 模拟 Stripe（固定 evt 便于步骤 5 重放）"
bash "$SCRIPT_DIR/mock_stripe_webhook.sh" "$ORDER_ID" "$FIXED_EVT"

echo ""
echo "== 4) 查询订单 / 订阅"
curl -sS "${BASE}/api/orders/${ORDER_ID}" | python3 -m json.tool

echo ""
echo "== 5) 重复同一 Webhook（应为 idempotent / duplicate）"
bash "$SCRIPT_DIR/mock_stripe_webhook.sh" "$ORDER_ID" "$FIXED_EVT"
