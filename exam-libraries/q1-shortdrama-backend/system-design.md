# Q1 系统设计 — 短剧会员订阅 + 多渠道支付

## 1. 目标与边界

- **目标**：最小可运行后端，完成「选套餐 → 建单 → 模拟支付回调 → 订阅生效/过期」闭环。
- **边界**：支付为 **mock webhook**；字段命名贴近 Stripe / Apple 真实风格；生产密钥管理不在本题范围，但需体现签名校验设计位。

## 2. 逻辑架构

```
┌─────────────┐     ┌──────────────────┐     ┌───────────────┐
│  Client/API │────▶│ Subscription API │────▶│  PostgreSQL   │
└─────────────┘     │  Order / Sub SM  │     │ orders,subs,  │
                    └────────┬─────────┘     │ payment_events│
                             │                └───────────────┘
                    ┌────────▼─────────┐
                    │ Webhook Ingress  │◀── mock_stripe / mock_apple
                    │ Verify + Idempotent│
                    └──────────────────┘
```

- **Subscription API**：创建订单、查询订单/订阅（如需要 demo）。
- **Webhook Ingress**：按渠道解析 payload → 验签（至少 Stripe 风格 HMAC + 时间窗）→ 幂等写入 `payment_events` → 驱动状态机。
- **状态机**：集中在一个模块（或服务层）显式定义合法迁移，非法迁移拒绝并记录。

## 3. 数据模型（最少三表）

| 表 | 职责 | 关键字段要点 |
|----|------|----------------|
| `orders` | 商业订单 | PK、用户/套餐、金额、币种、`idempotency_key`（客户端或业务层）、当前状态 |
| `subscriptions` | 会员周期 | FK→order、周期起止、`status`、与订单 1:1 或 1:n 按你文档说明 |
| `payment_events` | 原始支付事实 | PK、渠道 (`stripe`/`apple`)、外部事件 ID、**唯一去重**（渠道+外部 ID 或 payload hash）、验签结果、raw payload 引用 |

**索引建议**：`payment_events (channel, provider_event_id)` UNIQUE；`orders (idempotency_key)` UNIQUE（若适用）。

## 4. 状态机（订单/订阅）

显式状态与迁移（试卷要求）：

- `pending` → `paid`（支付成功确认）
- `paid` → `active`（开通会员，可与 `paid` 合并看实现，但须在文档中说明）
- `active` → `expired`（到期）
- 任意允许状态 → `refunded`（若实现退款回调）

**非法迁移**：集中校验函数返回错误码，不静默覆盖状态。

## 5. 幂等与并发

- Webhook 重放：`payment_events` 唯一键保证「同一事件只处理一次」；订单状态迁移使用「仅允许的当前状态 + 事务」避免双开。
- 可选：行锁或 `SELECT ... FOR UPDATE` 在订单行上处理竞态（README 说明取舍）。

## 6. 签名校验（Stripe 推荐）

- Header：`Stripe-Signature` 风格或等价自定义 header（文档写明）。
- 算法：HMAC-SHA256，payload 为 raw body；时间戳容忍窗口（如 ±5 分钟）防重放。
- 失败路径：401/400 + 不落库或不推进状态（与测试一致）。

## 7. 可运行性与脚本

- `docker compose up`（或等价）单命令起服务 + 数据库。
- `scripts/`: `mock_stripe_webhook.sh`、`mock_apple_iap.sh`、`happy_path.sh`（端到端 curl/httpie）。
- `state-machine.md`：Mermaid `graph TD` + 文字说明非法迁移行为。

## 8. 测试（至少 3 类异常）

1. 重复 webhook：第二次不重复开通/不发会员。
2. 签名校验失败：拒绝且不推进状态。
3. 未知或已过期订单 ID：明确错误，无副作用。

## 9. 交付目录（对齐试卷）

```
q1-shortdrama-backend/
  src/
  schema.sql or migrations/
  state-machine.md
  scripts/
  tests/
  README.md
  transcript.md
```
