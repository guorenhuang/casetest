# Q1 需求规则 — 短剧后台（30 分 · 建议 80 分钟）

## 功能需求

1. **创建订阅订单**：用户选择套餐 → 后端生成订单。
2. **多渠道支付回调**：至少模拟 **Stripe** 与 **Apple IAP**；独立脚本 POST 伪造回调。
3. **状态机**：`pending` → `paid` → `active` → `expired` / `refunded`；非法迁移需保护。
4. **幂等**：同一支付回调重复推送不得重复发会员、不得重复库存类副作用（若建模中有库存）。

## 硬性要求（扣分/作废风险）

| # | 规则 |
|---|------|
| R1 | **必须可运行**：一条命令起服务；至少 1 条端到端 happy path 的 curl/httpie 脚本 |
| R2 | **数据建模**：订单、订阅、支付事件 ≥3 表；PK/FK/唯一索引、幂等去重键写清 |
| R3 | **Mock 回调**：脚本伪造 webhook；**真实渠道字段命名风格**，禁止随意字段名 |
| R4 | **状态机显式**：代码/注释/文档 Mermaid；非法迁移有保护 |
| R5 | **测试**：≥3 类异常：重复 webhook 幂等、验签失败、未知/已过期订单 ID |
| R6 | **签名校验**：至少一渠道（推荐 Stripe）真实风格 HMAC + 时间容忍；禁止裸收 webhook |

## 交付物清单

- `src/`、`schema.sql` 或 `migrations/`、`state-machine.md`
- `scripts/mock_stripe_webhook.sh`、`mock_apple_iap.sh`、`happy_path.sh`
- `tests/`、`README.md`、`transcript.md`

## 非功能需求

- README：启动步骤、验证方式、设计取舍（幂等、状态合并、验签假密钥等）。
- Transcript：完整协同过程，含走弯路与纠正。
