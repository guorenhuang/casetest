# 资料库总览 — 系统设计（考试交付架构）

## 目的

支撑「AI 平台工程师 Take-home」的全链路交付：代码可运行、transcript 完整、reflection 诚实、四题独立可评。

## 顶层结构（与试卷一致）

```
exam-{考生名}/
  q1-shortdrama-backend/
  q2-content-audit-agent/
  q3-prompt-rescue/
  q4-vibe-coding/
  reflection.md
  README.md
```

## 跨题能力

| 能力 | 说明 |
|------|------|
| 过程可追溯 | 每题 `transcript.md` 覆盖全程，不美化 |
| 可复现 | README 写清一条命令启动与验证路径 |
| 诚实记录 | reflection ≤600 字，含帮到你 / 弯路 / 如何拉回 |

## 与本题库的映射

- `../q1-shortdrama-backend/`：订阅 + 多渠道支付后端
- `../q2-content-audit-agent/`：评论审核 Skill/Agent
- `../q3-prompt-rescue/`：Prompt 诊断与修复
- `../q4-vibe-coding/`：30 分钟 Vibe Coding 小工具

本文件不重复各题细节，细节以各子库 `system-design.md` 与 `requirements.md` 为准。
