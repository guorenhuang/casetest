# Q3 Prompt 救火 — 工作台 + 试卷交付物

对应 `exam-paper.md`：除五份 Markdown 外，本目录提供 **Python（FastAPI）+ SQLite + Ant Design** 的可运行工作台，用于完成 R1–R5 流程并一键导出。

## 交付物（试卷）

- `observations.md` · `issues.md` · `fixed_prompt.md` · `before_after.md` · `transcript.md`（可用 UI **导出** 生成/覆盖）
- 另需在本目录或总览中保留完整 **AI 对话 transcript**（见试卷说明）

## 目录说明

- `backend/` — API + SQLite 逻辑
- `frontend/` — React + Vite + Ant Design（生产构建进镜像）
- `Dockerfile` / `docker-compose.yml` — 本题独立编排

## 运行

**Docker（推荐）** — 在 `exam-wangxing` 根目录统一起四题时见上级 `README.md`；仅本题时：

```bash
cd exam-wangxing/q3-prompt-rescue
docker compose up --build -d
```

浏览器：<http://127.0.0.1:8765>。导出 Markdown 将写入 **本目录**（通过 `Q3_EXPORT_DIR=/publish` 与卷挂载，与试卷文件树一致）。

**本地开发**：`backend` 下 `uv venv` + `uv pip install -r requirements.txt`，`uvicorn app.main:app --port 8765`；`frontend` 下 `npm install && npm run build`（或 `npm run dev` 代理 `/api`）。

## 环境变量

| 变量 | 说明 |
|------|------|
| `OPENAI_API_KEY` | 可选；不设则使用可复现 mock 推理 |
| `OPENAI_BASE_URL` / `OPENAI_MODEL` | 可选 |
| `Q3_SQLITE_PATH` | SQLite 路径（容器内默认 `/data/q3_workbench.db`） |
| `Q3_EXPORT_DIR` | 导出 md 目录（容器内默认 `/publish` 即本题根目录挂载） |

## 与仓库其他路径的关系

本目录即 **`exam-paper.md` 要求下 `exam-wangxing/q3-prompt-rescue/` 的完整实现**，无另外一份重复工程目录。

---

## 试卷 `exam-paper.md` · 硬性流程自检

| # | 要求 | 完成情况 | 佐证 |
|---|------|----------|------|
| 1 | ≥5 条不同题材真实跑，原始输出贴出 | ✅ | `observations.md`（各 Run 原文） |
| 2 | 问题清单：现象 + 证据片段 + 为何是问题，≥4 条 | ✅ | `issues.md` |
| 3 | 与 AI 协同诊断须可见「逼出真问题」策略 | ✅ | `transcript.md` 中 **【策略标记】** 段；全量语境见 **`../TRANSCRIPT.md`** / **`../../chat.html`** |
| 4 | 修复后 prompt + 改动与问题 **一一映射** | ✅ | `fixed_prompt.md` 内映射表 |
| 5 | ≥2 组 before/after 证明有效 | ✅ | `before_after.md` |

## 交付文件（五份 + 工作台）

| 试卷要求 | 路径 |
|----------|------|
| observations.md | 本目录 |
| issues.md | 本目录 |
| fixed_prompt.md | 本目录 |
| before_after.md | 本目录 |
| transcript.md | 本目录（**全卷**另见 `../TRANSCRIPT.md`） |
| 可运行代码（题目外加分） | `backend/`、`frontend/`、`Dockerfile` |
