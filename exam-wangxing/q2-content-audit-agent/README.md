# Q2 · 评论内容审核 Agent

短剧评论区 **pass / review / block** 自动审核：**Python（FastAPI）+ SQLite（可编辑规则库）+ 前端 Ant Design**。规则与 OCR、可选 LLM 组合；**模型不可用时仅用规则仍可出结论**。

## 架构概要

| 组件 | 作用 |
|------|------|
| `rules.yaml` | 首次种子；可通过 API/页面 **覆写入库** |
| `data/audit.db` | SQLite 表 `audit_rules`，运行时唯一直读来源（满足「不写死在代码里」） |
| `q2_audit/rule_engine.py` | 按 kind 调度：词表 / 正则 / 连续数字 等 |
| `q2_audit/ocr_adapter.py` | **图床 OCR 接入点**（mock；query 参数或域名启发） |
| `q2_audit/llm_adapter.py` | OpenAI Chat Completions 兼容接口；超时/异常 → `None`，上层降级 |
| `q2_audit/auditor.py` | 流水线合并与证据汇总 |

优先级：`block`（规则合并）先于 `review`；规则未定罪且开启 LLM 时再参考模型输出。

## 运行

### Docker Compose（推荐一键启动）

在项目根目录 `q2-content-audit-agent/`（与 `Dockerfile`、`docker-compose.yml` 同级）执行：

```bash
docker compose up --build
```

- **前端 + 后端**：镜像内会先 `npm run build` Ant Design SPA，再由 FastAPI 挂载 `frontend/dist`；浏览器访问 **`http://localhost:8009`**（`docker-compose` 映射 `8009:8000`）。
- **`/api`**：与静态页同源，无需再配 Vite 代理。
- **SQLite**：`data/audit.db` 落在命名卷 `q2_audit_data`，重启规则与审核记录可保留；首次空库会从镜像内的 `rules.yaml` 播种。
- **可选模型**：按需设置环境变量：`OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL`。

### 1. Python 后端

建议在项目根目录使用虚拟环境；若环境为 PEP 668，可用 `pip install --break-system-packages -r requirements.txt` 或自备 venv。

```bash
cd q2-content-audit-agent
python3 -m pip install -r requirements.txt            # 或 venv / uv
cd src && PYTHONPATH=. python3 run_server.py
```

默认 `http://127.0.0.1:8000`，健康检查：`GET /api/health`。

### 2. Ant Design 前端（开发态）

```bash
cd frontend
npm install && npm run dev
```

浏览器打开终端提示地址（通常为 `http://localhost:5173`）。`/api` 由 Vite 代理到后端。

### 3. 生产一体化（可选）

```bash
cd frontend && npm run build
cd ../src && PYTHONPATH=. python3 -m uvicorn q2_audit.main:app --host 0.0.0.0 --port 8000
```

若存在 `frontend/dist`，FastAPI 会挂载静态资源，可同时访问后端与打包后的 SPA。

### 4. CLI 批跑 → 报告

默认 **不使用 LLM**（与试卷「可降级、规则独立跑通」一致）：

```bash
cd src && PYTHONPATH=. python3 run_cli.py --input ../dataset.json --out ../run_report.md
```

启用模型（需 `OPENAI_API_KEY`）：

```bash
export OPENAI_API_KEY=...
PYTHONPATH=. python3 run_cli.py --input ../dataset.json --out ../run_report.md --use-llm
```

可调：`OPENAI_BASE_URL`、`OPENAI_MODEL`。

## 如何新增规则（不改业务代码）

1. **改库**：前端「规则（SQLite）」页新增/编辑，或调用 `POST /api/rules`（upsert）。
2. **改 YAML**：编辑根目录 `rules.yaml`，调用 `POST /api/rules/reimport-yaml` 全量写入/更新。
3. 审核请求下次即加载新规则；无需改 `rule_engine` 的类型分支——新词条/正则均放在 `config` JSON 内。

## 如何替换 OCR / LLM

- **OCR**：改 `ocr_adapter.fetch_ocr_text` 内实现对真实厂商 SDK 或 HTTP API 的调用，保持返回值 `(text|None, note)`。
- **LLM**：改 `llm_adapter.classify_comment`；或仅用环境变量指向自建网关（OpenAI schema）。

## 交付文件

| 路径 | 说明 |
|------|------|
| `rules.yaml` | 外置规则种子 |
| `dataset.json` | ≥30 条，含多条刁钻样例（拼音拆写、emoji、首字母、图床 OCR 等） |
| `run_report.md` | `run_cli.py` 自动生成 + 每条合理性说明 |

## 试卷 `exam-paper.md` · 硬性要求自检

| # | 要求 | 完成情况 | 佐证 |
|---|------|----------|------|
| R1 | 规则外置（yaml/json/db），新规则不改业务代码 | ✅ | `rules.yaml` + SQLite `audit_rules`；`POST /api/rules`、前端规则页 |
| R2 | 模型超时/不可用时规则独立跑通 | ✅ | `run_cli.py` 默认无 LLM；`auditor.py` + `llm_adapter` 失败走降级 |
| R3 | 每条输出含「为何如此判」证据 | ✅ | `reasons[]`（rule / ocr / model / system）；`run_report.md` |
| R4 | ≥30 条数据，≥5 刁钻；人工取舍说明 | ✅ | `dataset.json`（34 条）；`run_report.md` 末「取舍」节 |
| R5 | 跑批 Markdown 报告 | ✅ | `run_report.md`（`run_cli.py` 生成） |

## 交付目录（本题）

| 试卷条目 | 路径 |
|----------|------|
| Agent 代码 | `src/` |
| 外置规则 | `rules.yaml`（可再入库） |
| 数据集 | `dataset.json` |
| 报告 | `run_report.md` |
| Transcript | `transcript.md`；全卷见 **`../TRANSCRIPT.md`**、**`../../chat.html`** |

## Transcript

**`transcript.md`** 为索引；完整多题对话未美化归档：**[`../../chat.html`](../../chat.html)**（说明 **`../TRANSCRIPT.md`**）。提交时可附 IDE 原始导出。
