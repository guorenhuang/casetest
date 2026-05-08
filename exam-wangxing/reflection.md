# Reflection（≤600 字）

**1. AI 最帮到我的时刻**  
把 Q2 硬性条款（外置规则、命中证据、LLM 不可用仍可判、CLI 报告）丢给 AI 做模块化拆分，得到「SQLite + `rules.yaml` 种子、`ocr_adapter`/`llm_adapter` 分界线、`run_cli.py`」的方案，省了在骨架上打转的时间。

**2. 弯路最多**  
Docker 构建前端时报 `dataset.json` 无法解析——构建上下文起初只有 `frontend/`。我让 AI「改 Vite」一度跑偏；根因是 **镜像未 COPY 仓库根的 JSON**，与配置无关。

**3. 如何拉回 · 重做会怎么问**  
按报错锁定「谁 import 了工作区外的文件」，在 Dockerfile `/workspace` 先复制 `dataset.json` 再 `npm run build`。重做会先问：**列全跨目录 import 与每层镜像 COPY**，再动工具链。

**实际总耗时：** 四题跨日完成（含试错），约 **12～16 小时**。
