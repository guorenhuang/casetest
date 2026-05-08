# exam-wangxing — 笔试提交目录

本目录对齐 `exam-paper.md` **提交方式**约定的 zip 树形（阅卷时请将本目录视作 `exam-{姓名}/`）。

## 1. 目录结构是否满足试卷？

对照题面给出的打包示例，**已实现**：

```
exam-wangxing/
  q1-shortdrama-backend/     # schema.sql · state-machine.md · scripts/ · tests/ · README · transcript.md
  q2-content-audit-agent/    # rules.yaml · dataset.json · run_report.md · src/ · README · transcript.md
  q3-prompt-rescue/          # observations/issues/fixed_prompt/before_after/transcript · 工作台 backend+frontend
  q4-vibe-coding/            # code/ · README · transcript_with_ts.md · key_turning_point.md · rejected_suggestion.md
  reflection.md              # ≤600 字，回答三问 + 诚实耗时（见文末「硬门槛自检」）
  README.md                   # 本文件：总入口
  TRANSCRIPT.md               # 全卷 transcript 归档说明（与 chat.html 的关系）
  docker-compose.yml          # 四题同启（端口见下）
```

**根目录另附**（在打包 zip 时可将 `exam-paper.md` 与归档 `chat.html` 一并放在 **上一级**仓库中，本题不强制塞进 zip）：

| 路径 | 作用 |
|------|------|
| `../exam-paper.md` | 原始题面 |
| `../chat.html` | **全卷 AI 会话** HTML 归档（未美化）；与 `TRANSCRIPT.md` 互证 |

---

## 2. 三门「硬门槛」自检（任一缺失按 0 分）

| 试卷要求 | 本仓库落实 |
|---------|-------------|
| **最终代码 + README** | 四题均在各自目录 **`README.md`**，且含 **`试卷 exam-paper.md · 硬性要求自检`** 表，逐条 ✅ + 佐证路径 |
| **完整 transcript 覆盖四题** | **`TRANSCRIPT.md`** 索引；`**../chat.html**` 主归档；各题 **`transcript.md`** / **`transcript_with_ts.md`**（Q4 带相对时间戳为硬性） |
| **Reflection ≤600 字** | 根目录 **`reflection.md`**（已从模板改为可提交正文；提交前仍可按真实情况微调用词） |

---

## 如何运行（总览）

| 题目 | 说明 |
|------|------|
| **Q1** | `q1-shortdrama-backend/README.md`，`docker compose up`/脚本/`pytest` |
| **Q2** | `q2-content-audit-agent/README.md`，`dataset.json`、`run_report.md`、`run_cli.py` |
| **Q3** | `q3-prompt-rescue/README.md`，8765 |
| **Q4** | `q4-vibe-coding/README.md`，源码在 `code/` |

## Docker Compose（四题）

在 **`exam-wangxing`** 目录：

```bash
cd exam-wangxing
docker compose up --build
```

端口：**Q1 → 8001**，**Q3 → 8765**，**Q2 → 8080**，**Q4 → 8004**。仅保留本目录 `docker-compose.yml` 编排四题；开发时请先 `cd` 到 **`exam-wangxing`**。

可选环境变量：`OPENAI_*`（Q2/Q3/Q4）；Q1 见 compose 默认 Stripe/Apple mock 密钥。

## 原始试卷与资料库

- 题面：`../exam-paper.md`
- 资料库：`../exam-libraries/`（其中 **`q4-vibe-coding` 为指向本目录的符号链接**，便于原型页跳转）

## 打包 zip 提示

建议 **排除** 各题 `node_modules/`、`.venv/`，附带各题 **`README.md`** + **`reflection.md`** + **`TRANSCRIPT.md`**（及按需附带 `chat.html` 或与 IDE 导出 MD）。
