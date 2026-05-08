# Q3 需求规则 — Prompt 救火（25 分 · 建议 60 分钟）

## 原始任务

诊断并修复离职同事留下的分镜 Agent system prompt；试卷声明 **≥4 个隐藏问题**。

## 硬性流程（违反扣分）

| # | 规则 |
|---|------|
| R1 | **勿立刻改**：先 ≥5 条不同长度/题材剧情**真实跑模型**，原始输出写入 `observations.md` |
| R2 | **问题清单**：`issues.md` 每条含 **现象 + 证据片段 + 为何是问题** |
| R3 | **防 AI 敷衍**：与 AI 协同诊断时，transcript 可见**逼出真问题**的策略，而非泛泛「挺好」 |
| R4 | **修复映射**：`fixed_prompt.md` 含新 prompt；**每处改动 ↔ 解决的问题** 一一对应，禁止笼统「一锅端」 |
| R5 | **对比**：`before_after.md` **≥2 组** before/after，证明有效 |

## 交付物

- `observations.md`、`issues.md`、`fixed_prompt.md`、`before_after.md`、`transcript.md`

## 质量提示

- 证据片段宜短而准（可直接指向 observations 中某次运行）。
- 修复后 prompt 应显式约束：JSON schema、长度/条数上限、风格锚点、禁止篡改用户设定等（以你的 issues 为准）。
