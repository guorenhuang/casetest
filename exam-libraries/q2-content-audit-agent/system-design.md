# Q2 系统设计 — 评论审核 Agent / Skill

## 1. 目标与边界

- **输入**：一批评论文本（可含图床 URL）。
- **输出**：每条 `pass` | `review` | `block`，且必须带**可回查的命中证据**（规则 ID / 模型 reason）。
- **边界**：模型可配置；超时或不可用时**规则引擎单独可跑**（降级）。

## 2. 流水线架构

```
                    ┌─────────────────┐
  Comment batch ──▶ │ Normalizer      │ (URL、空白、轻度规范化)
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │ Rule Engine  │   │ OCR Adapter  │   │ LLM Classify │
   │ yaml/json    │   │ (real / mock)│   │ (optional)   │
   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
                    ┌─────────────────┐
                    │ Decision Merge  │  pass > block > review 或配置优先级
                    │ Evidence Store  │  每条 comment 输出 reasons[]
                    └─────────────────┘
```

## 3. 规则引擎（必须外置配置）

- 配置文件：`rules.yaml` 或 `rules.json`，由加载器映射为内存结构。
- **新增规则**：只改配置 +（如需）热加载或重启进程；**不改业务代码**。
- 能力覆盖（试卷最低要求，每条可演示）：
  - 敏感词词库（多词表、级别可选）
  - 正则规则（广告、引流模式）
  - 拼音 / 谐音 / 拆字 / emoji 替代（如「加 wei xin」「jia v」、首字母）
  - 连续数字（QQ/手机/微信号形态）
  - 图片：图床 URL → OCR 适配器（真实 API 或 mock，**接入点单独模块**）

## 4. LLM 与降级

- **正常**：规则命中可与 LLM 结果合并（例如规则 `block` 直接短路）。
- **降级**：模型超时 / SDK 错误 → 仅用规则 + OCR 文本输出最终标签与证据；README 写明行为。
- **命中证据**：`reasons: [{ "type": "rule", "id": "...", "detail": "..." }, { "type": "model", "detail": "..." }]`。

## 5. 数据与报告

- `dataset.json`：≥30 条，含正常、广告、骂人、绕词、含图；其中 **≥5 条刁钻**；人工 review 后在报告说明取舍。
- `run_report.md`：跑批结果每条：结论 + 规则/模型 reason + 是否合理（考官可读）。

## 6. 运行形态

- CLI：`audit --input dataset.json --out report.md`  
- 或 HTTP：`POST /audit { "comments": [...] }`  
- README：架构、部署、**如何加规则**、**如何换模型**。

## 7. 交付目录

```
q2-content-audit-agent/
  src/
  rules.yaml or rules.json
  dataset.json
  run_report.md
  README.md
  transcript.md
```
