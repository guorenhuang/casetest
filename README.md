# QUICK START · casetest

部署为静态站时，默认打开根目录 **[`index.html`](index.html)** 即可浏览官网式总览（题面精要、四题工程、文档地图与 Docker 端口表）。

本仓库为笔试工程：**题面**在根目录 [`exam-paper.md`](exam-paper.md)，**可提交代码与四题说明**在 **[`exam-wangxing/`](exam-wangxing/README.md)**。

---

## 一键起四题（Docker）

```bash
cd exam-wangxing
docker compose up --build
```

| 服务 | 地址 |
|------|------|
| Q1 短剧后端 + 控制台 | http://127.0.0.1:8001 |
| Q3 Prompt 救火工作台 | http://127.0.0.1:8765 |
| Q2 评论审核 | http://127.0.0.1:8080 |
| Q4 分镜 → 英文 Prompt | http://127.0.0.1:8004 |

可选：`export OPENAI_API_KEY=...`（Q2/Q3/Q4 用模型时）。

---

## 不交 Docker 时（各题本地）

每题细节以 **`exam-wangxing/q*/**/README.md`** 为准：

- **Q1**：建 venv、`PYTHONPATH`、`scripts/happy_path.sh`、`pytest tests/`
- **Q2**：`q2-content-audit-agent/src` + `frontend` dev，或题目内单机 `docker compose`
- **Q3**：`q3-prompt-rescue/backend` + `frontend` 或本题 `docker compose`
- **Q4**：`q4-vibe-coding/code/backend` + `code/frontend`

---

## 还看哪些文件

| 文件 | 说明 |
|------|------|
| [`index.html`](index.html) | 静态部署首页：题面介绍、四题平台、文档入口 |
| [`exam-wangxing/README.md`](exam-wangxing/README.md) | 提交目录总览、自检、Compose 说明 |
| [`exam-wangxing/reflection.md`](exam-wangxing/reflection.md) | 试卷 Reflection（≤600 字） |
| [`exam-wangxing/TRANSCRIPT.md`](exam-wangxing/TRANSCRIPT.md) | 全卷 transcript 索引 |
| [`chat.html`](chat.html) | 工作区会话 HTML 归档 |

---

## 忽略与提交建议

仓库根 [.gitignore](.gitignore) 已忽略 `node_modules/`、`.venv/`、运行时 `*.db` 等；打 zip 前见 `exam-wangxing/README.md` 「打包 zip 提示」。
