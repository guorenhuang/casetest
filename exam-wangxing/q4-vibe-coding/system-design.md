# Q4 系统设计 — Vibe Coding 小工具

## 1. 目标

在约 **30 分钟编码**内，从零交付**可运行**小工具；选题三选一（试卷原文）：

- **(a) 短剧标题批量改写器**：≥10 条原标题 → AI 批量「更有点击欲」→ 对比 CSV（CLI 或 Web）。
- **(b) 分镜表 → 美术 prompt**：自定义分镜 schema → 逐条英文 prompt（文生图/视频）；**前端表格 + 一键导出**。
- **(c) 投放素材合规预检**：广告文案 + 配图 URL → 合规报告（风险 + 改写建议）。

## 2. 工程形态建议（自选题调整）

| 选题 | 建议栈 | 核心模块 |
|------|--------|----------|
| (a) | CLI + CSV / 或极简 Web | 批量 prompt、结果表、错误重试 |
| (b) | 前端表格 + 导出 | schema 校验、行级转换、download |
| (c) | 小服务或脚本 | 文本规则 + 可选视觉 API、报告模板 |

## 3. 「Vibe」约束下的最小架构

- **业务逻辑**：必须由 **AI 生成/修改**；人力仅限改 env、改名、拷贝依赖等琐事。
- **可运行优先**：允许轻微 bug，**核心 demo 路径**必通。
- **文档**：`README.md` 说明选题理由、运行方式、环境变量。

## 4. transcript 与元信息

- `transcript_with_ts.md`：**时间戳**可看出交互发生在第几分钟。
- `key_turning_point.md`：框出一次从「卡住」到「能跑」的 AI 产出 + 一句话为何关键。
- `rejected_suggestion.md`：一次**拒绝 AI 建议**及理由（若全程未拒绝需写出 — 试卷说明）。

## 5. 可选

- `demo.gif` / `demo.mp4` ≤10s 录屏（推荐）。

## 6. 交付目录

```
q4-vibe-coding/
  code/
  README.md
  transcript_with_ts.md
  key_turning_point.md
  rejected_suggestion.md
  (optional demo.gif / demo.mp4)
```

## 7. 硬性扣分点（试卷）

违反下列 ≈ **扣 50%**：

- 非 Vibe 写业务、无时间戳 transcript、核心跑不通、缺转折点/拒绝说明等（以 `requirements.md` 为准）。
