# Q4 需求规则 — Vibe Coding（20 分 · 建议 40 分钟）

## 选题（三选一）

- **(a)** 短剧标题批量改写器 — ≥10 条标题，AI 改写，输出对比 CSV  
- **(b)** 分镜表 → 英文美术 prompt — 表格 UI + 一键导出  
- **(c)** 投放素材合规预检 — 文案 + 图 URL → 风险与改写建议  

## 硬性要求（违反扣 50%）

| # | 规则 |
|---|------|
| R1 | **Vibe Coding**：业务代码须由 **AI 生成/修改**；env、变量名、拷依赖可手动 |
| R2 | **Transcript 带时间戳**：能看出第几分钟发生的交互 |
| R3 | **必须可运行**：可有 bug，核心 demo 路径要通 |
| R4 | **关键转折点**：`key_turning_point.md` 框出一次扭转局面的 AI 产出 + 一句话解释 |
| R5 | **拒绝 AI 建议**：`rejected_suggestion.md` 记录一次拒绝及理由（无则写明试卷允许情况） |

## 交付物

```
q4-vibe-coding/
  code/
  README.md
  transcript_with_ts.md
  key_turning_point.md
  rejected_suggestion.md
  demo.gif or demo.mp4   # 可选
```

## README 须说明

- 选了哪题、为何选它、如何运行（含 API Key 等）。
