# Q4 · Transcript（带时间戳节选）

> 试卷要求能看出「发生在第几分钟」；本节为节选，**语义未美化**。会话实际发生在 IDE/Cursor，时间线为相对 **T0 = 本题开工时刻**。

## T0 · 选题与约束确认（约第 0 分钟）

**User**：按计划做选题 **(b) 分镜表 → 英文美术 prompt**，技术栈 FastAPI + SQLite + Ant Design，30 分钟内先跑 UI 骨架再补 API。

**Assistant**：拆分 `shots` CRUD、`POST /seed-demo`、`POST generate-prompt`（无 Key 走模板）。

## T0+8 · 卡住：代理与同源（约第 8 分钟）

**User**：`npm run dev` 前端 5173，`/api/shots` 404。

**Assistant**：核对 `vite.config.ts` proxy 目标端口与后端是否一致（8000）。

**User**：改完仍偶发——发现后端未 `--reload` 导致旧路由。

## T0+18 · 转折点（见 `key_turning_point.md`）

**Assistant**：给出「单进程 FastAPI 托管 `dist` + `STATIC_DIR`」与 `index.html` fallback 的极简部署片段，避免 dev/prod 双栈分叉。

## T0+22 · 拒绝 AI 建议（见 `rejected_suggestion.md`）

**Assistant**：建议把分镜 JSON 完全交给模型自由发挥字段名。

**User**：拒绝——规定 `shot_number / description / mood / camera` 等列，避免下游解析再炸。

## T0+28 · 收尾

**User**：补 CSV/JSON 导出与 demo 数据；准备录屏（可选 `demo.gif`）。

---

> 若阅卷需全量逐句 transcript，请以 IDE 导出或工作区归档 `chat.html` / Cursor 会话导出为准，并与本题时间标注交叉比对。
