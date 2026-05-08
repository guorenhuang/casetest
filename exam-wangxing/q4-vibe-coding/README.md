# Q4 Vibe Coding — 分镜表 → 英文美术 Prompt

## 选题

- **(b) 分镜表 → 英文美术 prompt**  
- **理由**：与 **Ant Design 表格 + 一键导出** 高度贴合；后端用 Python 聚合字段并（可选）调用大模型，**SQLite** 落库，可在离线环境下仍跑通「模板生成」演示路径。

## 技术栈

- **Python 3.11+**：FastAPI + `httpx`（可选 OpenAI）+ SQLite（`storyboard.db`）
- **前端**：Vite + React + TypeScript + **Ant Design 5**

## 运行方式

以下路径均以 **`exam-wangxing/q4-vibe-coding/`** 为当前工作目录。

### 1. 后端

```bash
cd code/backend
# 任选其一：uv（推荐，适合 PEP 668 / uv 管理的 Python）或标准 venv
uv venv .venv && uv pip install -r requirements.txt
# python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
source .venv/bin/activate   # Windows: .venv\Scripts\activate
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

可选环境变量（启用真实 AI 改写时）：

- `OPENAI_API_KEY`：若为空，则使用内置 **英文模板** 生成 prompt，核心路径仍可演示。
- `OPENAI_MODEL`：默认 `gpt-4o-mini`。

### 2. 前端

```bash
cd code/frontend
npm install
npm run dev
```

浏览器打开 Vite 提示的地址（默认 `http://127.0.0.1:5173`）。开发模式下 `/api` 会代理到 `http://127.0.0.1:8000`。

### Docker（与 `exam-wangxing/docker-compose.yml` 中 Q4 服务一致）

在 **`exam-wangxing/`**（本题的上一级投递包根目录）执行：

```bash
cd exam-wangxing
docker compose up --build
```

其中 Q4 构建上下文为 **`q4-vibe-coding/code`**（相对 `exam-wangxing`），映射 **8004 → 8000**，同一端口提供静态页与 `/api`。

### 3. 演示路径（须通）

1. 点击 **加载示例分镜** → SQLite 写入示例行并在表格展示。  
2. 编辑单元格失焦自动 PATCH 保存。  
3. 点击 **AI 生成** → 无 Key 时模板生成英文；有 Key 时走 OpenAI。  
4. **导出 JSON / CSV** 下载当前表数据。

## 试卷 `exam-paper.md` · 硬性要求自检（Q4 · Vibe）

| # | 要求 | 完成情况 | 佐证 |
|---|------|----------|------|
| 1 | 业务逻辑由 AI 生成/修改为主 | ✅ | 见 `transcript_with_ts.md` 中生成/纠偏轮次（本人配 env、依赖、端口） |
| 2 | Transcript **带时间戳** | ✅ | **`transcript_with_ts.md`**（`T0+分钟`） |
| 3 | 核心 demo 可运行 | ✅ | `code/`；或与上级 **`exam-wangxing/docker-compose.yml`** 中联编 Q4 服务 **8004** |
| 4 | Transcript 中框出「关键转折点」 | ✅ | **`key_turning_point.md`**（与 transcript 交叉引用） |
| 5 | 标注一次「不接受 AI 建议」 | ✅ | **`rejected_suggestion.md`** |
| （荐）≤10s 录屏 | 可选 | 未附带时可本地补录 `/` 演示路径 |

## 交付物位置

| 文件 | 说明 |
|------|------|
| **`transcript_with_ts.md`** | 带相对开工时刻的节选（试卷硬性） |
| **`key_turning_point.md`** | 关键转折点 + 一句话为何重要 |
| **`rejected_suggestion.md`** | 拒绝的建议 + 理由 |
| `README.md` | 选题 *(b)*、理由与运行（**本文件**） |
| `code/` | 可运行源码 |
| 全卷 Transcript | 另见 **`../TRANSCRIPT.md`**、[`../../chat.html`](../../chat.html) |

## API 摘要

- `GET /api/shots` — 列表  
- `POST /api/shots` — 新增  
- `PATCH /api/shots/{id}` — 更新  
- `DELETE /api/shots/{id}` — 删除  
- `POST /api/shots/{id}/generate-prompt` — 生成/刷新英文 prompt  
- `POST /api/seed-demo` — 载入示例数据  
