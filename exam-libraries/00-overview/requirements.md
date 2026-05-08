# 资料库总览 — 需求规则（提交与评分）

## 提交硬门槛（缺一按 0 分）

1. **最终代码/产出物**：可运行仓库（zip 或私有 GitHub）+ 必要 README  
2. **完整 AI transcript**：覆盖全部 4 题，禁止编辑美化  
3. **Reflection**：≤600 字，回答：  
   - 哪一步 AI 最帮到你（具体 prompt → output）  
   - 哪一步弯路最多  
   - 如何拉回；若重做会怎么问  

## 打包示例

本工作区实际代码与交付物请置于 **`exam-wangxing/`** 目录，与下表「打包示例」目录名一致，便于对照 `exam-paper.md` 提交。

```
exam-{你的名字}/
  q1-shortdrama-backend/
  q2-content-audit-agent/
  q3-prompt-rescue/
  q4-vibe-coding/
  reflection.md
  README.md
```

## 评分维度（总分 100）

| 维度 | 分值 |
|------|------|
| 技术正确性 | 20 |
| AI 协同质量 | 30 |
| 问题反应力 | 20 |
| 工程化判断 | 15 |
| Reflection 深度 | 15 |

## 通用工程规则

- 技术栈、模型不限；参考开源须在 README/transcript 标注来源  
- 耗时如实写在 reflection；不诚实耗时可一票否决  
- 题 4：业务代码须由 AI 生成/修改，并满足该题 transcript 与时间戳等硬性要求  

## 各题分值与建议用时

| 题 | 分值 | 建议时间 |
|----|------|----------|
| Q1 | 30 | ~80 min |
| Q2 | 25 | ~60 min |
| Q3 | 25 | ~60 min |
| Q4 | 20 | ~40 min |
