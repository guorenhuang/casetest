# 全卷 · Transcript 索引（非正文）

`exam-paper.md` 要求：**完整 AI 对话记录覆盖全部 4 题**，且 **不允许编辑美化**。

**本文件作用**：说明各 **transcript 文件谁对应谁**（公共部分 / 全卷归档 / 各题实现）。**这里不放对话原文**，原文见下表路径。

---

## 文件分工一览

| 类型 | 路径（相对本目录 `exam-wangxing/`） | 说明 |
|------|--------------------------------------|------|
| **公共部分** | [`agent0_transcript.md`](agent0_transcript.md) | 完成 **公共工程** 时的协同导出：如 `exam-libraries`（系统设计 / 需求 / 原型）、根目录 `index.html` / `chat.html` 等；**不属于 Q1–Q4 任一题**。 |
| **全卷时序** | [`../chat.html`](../chat.html) | 工作区根目录、按轮次追加的 HTML 归档；**多题与公共部分可能交叉**，时间线以此为准。 |
| **Q1** | `q1-shortdrama-backend/transcript.md` | 本题实现过程；可附 IDE 原始导出，与 `chat.html` 互证。 |
| **Q2** | `q2-content-audit-agent/transcript.md` | 同上。 |
| **Q3** | `q3-prompt-rescue/transcript.md` | 同上；含诊断策略节选，完整语境见 [`../chat.html`](../chat.html)。 |
| **Q4** | `q4-vibe-coding/transcript_with_ts.md` | 本题实现过程；**须带相对分钟时间戳**（试卷硬性）。 |

阅卷可按上表逐文件打开；**不要把公共部分对话只塞进某一道题的 `transcript.md`**，公共部分以 **`agent0_transcript.md`** 与 **`../chat.html`** 对应段落为准。

---

## 导出与提交

提交 zip 时，可将 Cursor / VS Code 等 **原始 Markdown 导出**追加到各题 `transcript.md` 末尾，或单独附 `transcript/*.md`；**勿删改失败与纠偏段落**。
