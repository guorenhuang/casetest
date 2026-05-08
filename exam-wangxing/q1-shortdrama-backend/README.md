# Q1 短剧会员订阅后端（Python + SQLite + Ant Design）

## 能力与契合题目

- **创建订单**：`POST /api/orders`（套餐 + 用户 + 业务幂等键 `idempotency_key`）。
- **多渠道回调**：`POST /webhooks/stripe`（Stripe 真实风格 `Stripe-Signature` + `checkout.session.completed` + `metadata.order_id`）；`POST /webhooks/apple`（App Store Server Notifications 风格：`notificationType` / `notificationUUID` / `data.signedTransactionInfo` 内嵌 `appAccountToken`）。
- **状态机**：`pending → paid → active → expired | refunded`，非法迁移拒绝；见 `state-machine.md` 与 `src/app/state_machine.py`。
- **幂等**：`payment_events` 表 `(channel, provider_event_id)` 唯一；重复 Webhook 不重开会员、不重复扣 `plans.stock_remaining`。
- **Stripe 验签**：HMAC-SHA256，`t` 时间戳 ±300s（可配 `STRIPE_SIGNATURE_TOLERANCE_SECONDS`）；失败返回 401，不推进订单。
- **Apple mock 鉴权**：请求头 `X-Apple-Receipt-Secret` 与 `APPLE_SHARED_SECRET` 一致（真实环境应校验 JWS + Apple 根证书，此处为演示位）。

## 一键启动

```bash
cd q1-shortdrama-backend
docker compose up --build
```

打开 **http://127.0.0.1:8000/** 使用 Ant Design 控制台（同源托管于 FastAPI `STATIC_DIR`）。

## 本地开发（前后端分离）

```bash
# 终端 A
cd q1-shortdrama-backend
export PYTHONPATH=src
export DATABASE_PATH=./data/app.db
export STATIC_DIR=./frontend/dist   # 可选；不设则仅 API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 终端 B
cd q1-shortdrama-backend/frontend
npm install
npm run dev
```

Vite 将 `/api`、`/webhooks` 代理到 `localhost:8000`。

## 端到端脚本

```bash
export BASE_URL=http://127.0.0.1:8000
./scripts/happy_path.sh
./scripts/mock_stripe_webhook.sh <order_id>
./scripts/mock_apple_iap.sh <order_id>
```

## 测试

```bash
export PYTHONPATH=src
python -m pytest tests/ -v
```

## 环境变量摘要

| 变量 | 说明 |
|------|------|
| `DATABASE_PATH` | SQLite 文件路径 |
| `STRIPE_WEBHOOK_SECRET` | 与 `scripts/stripe_sign.py` / 前端 HMAC 使用同一字符串 |
| `STRIPE_SIGNATURE_TOLERANCE_SECONDS` | Stripe 签名时间窗（秒） |
| `APPLE_SHARED_SECRET` | Mock Apple 请求头密钥 |
| `STATIC_DIR` | 若设置则托管前端 `dist`（`index.html` + `assets/`） |

## 设计取舍

- **订单与订阅双表状态**：与阅卷示例图一致；支付入库在一次事务中完成 `paid→active`，避免中间态被外部读到。
- **库存**：`plans.stock_remaining` 仅在首次履约扣减，重复 Webhook 在插入支付事件阶段即短路。
- **假密钥**：演示用固定 `whsec_...` 风格字符串；生产应使用 Stripe Dashboard 密钥与 Secret Manager。

---

## 试卷 `exam-paper.md` · 硬性要求自检

| # | 要求 | 完成情况 | 佐证 |
|---|------|----------|------|
| 1 | 一条命令可起（`docker compose up` 或同等） | ✅ | 上级 **`exam-wangxing/docker-compose.yml`** 含本题；本题目录内亦可 `docker compose up --build` |
| 2 | 订单 / 订阅 / 支付事件 ≥3 表 + 主外键 / 唯一 / 幂等键 | ✅ | `schema.sql`（含 `payment_events` 渠道+事件号唯一） |
| 3 | Mock Stripe / Apple 脚本，字段命名贴近真实 | ✅ | `scripts/mock_stripe_webhook.sh`、`mock_apple_iap.sh`、`stripe_sign.py` |
| 4 | 状态机显式 + 非法迁移保护 | ✅ | `state-machine.md`（含迁移图）、`src/app/state_machine.py` |
| 5 | 测试覆盖 ≥3 类异常路径 | ✅ | `tests/test_webhooks.py`（幂等重复、Stripe 签失败、未知/非法订单） |
| 6 | Stripe 风格 HMAC 验签 + 时间窗 | ✅ | `src/app/stripe_verify.py`，可配 `STRIPE_SIGNATURE_TOLERANCE_SECONDS` |

## 交付目录（本题）

| 试卷条目 | 本仓库路径 |
|---------|-------------|
| 服务代码 | `src/` |
| 表结构 | `schema.sql` |
| 状态迁移图 | `state-machine.md` |
| 脚本 | `scripts/happy_path.sh` 等 |
| 测试 | `tests/` |
| Transcript | `transcript.md`（全卷汇总见 **`../TRANSCRIPT.md`**、`../chat.html`） |

## Transcript

- 本题：**`transcript.md`**  
- **全卷 4 题**未剪裁归档：**工作区 [`../../chat.html`](../../chat.html)**；说明见 **`../TRANSCRIPT.md`**。
