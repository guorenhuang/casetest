# Exam materials organization
_Exported on 2026/5/8 at GMT+8 17:31:29 from Cursor (3.3.12)_

---

**User**

帮我按照@exam-paper.md 拆成多个exam 的资料库 
然后在每个库里面定义好系统设计 和 需求规则 还有原型html

---

**Cursor**

正在阅读 `exam-paper.md` 以了解结构与内容，随后拆分为多个资料库并补充系统设计、需求规则与原型 HTML。



正在将笔试卷拆成四个题目资料库，每个库包含 `system-design.md`、`requirements.md` 和 `prototype.html`，并添加总览库与根目录 `index.html` 便于导航。



添加 `exam-libraries/index.html` 作为入口，便于从文件夹直接打开。



已按 `exam-paper.md` 拆成 **5 个资料库目录**（总览 + Q1–Q4），每个库内都有 **`system-design.md`**（系统设计）、**`requirements.md`**（需求/硬性规则）、**`prototype.html`**（可本地打开的原型页）。

## 目录结构

| 路径 | 内容 |
|------|------|
| [`exam-libraries/index.html`](file:///Users/mac/Desktop/casetest/exam-libraries/index.html) | 入口，自动跳到总览原型 |
| [`exam-libraries/00-overview/`](exam-libraries/00-overview/) | 提交要求、评分维度、打包结构 · 总览导航页 |
| [`exam-libraries/q1-shortdrama-backend/`](exam-libraries/q1-shortdrama-backend/) | 订阅 + Stripe/Apple mock · 订单控制台原型（含示意状态与 webhook 日志） |
| [`exam-libraries/q2-content-audit-agent/`](exam-libraries/q2-content-audit-agent/) | 规则引擎 + 降级 + 证据链 · 审核台原型 |
| [`exam-libraries/q3-prompt-rescue/`](exam-libraries/q3-prompt-rescue/) | 观测→issues→修复映射流程 · 诊断工作台原型（含原样 prompt） |
| [`exam-libraries/q4-vibe-coding/`](exam-libraries/q4-vibe-coding/) | 三选题架构 · 选题卡片原型 |

## 怎么用

1. 用浏览器打开 **`/Users/mac/Desktop/casetest/exam-libraries/index.html`**（或 `00-overview/prototype.html`），可从总览跳到各题原型。  
2. 各题的设计与规则写在对应目录的 **`system-design.md`** / **`requirements.md`**；内容与试卷里的分值、交付物、硬性要求对齐并做了结构化整理。  
3. **`prototype.html`** 为静态示意 UI（含少量前端演示逻辑），真实笔试实现仍以各题 README/代码为准。

原始试卷仍保留在根目录 **`exam-paper.md`**，未被修改。若你希望把「资料库」改成 JSON/SQLite 或统一 frontmatter 方便检索，可以说明格式我再加一层。

---

**User**

从现在开始，把我们所有的对话，都记录到chat.html 中，放到跟目录， 包括刚才到对话

---

**Cursor**

正在查找是否有可用的对话转录以准确还原首轮内容，随后在根目录创建 `chat.html`。



正在创建根目录的 `chat.html`，收录首轮对话的要点与本轮请求；首轮完整技术细节以已生成的 `exam-libraries/` 文件为准，不在 HTML 中重复粘贴大量工具输出。



已在项目**根目录**创建 **`/Users/mac/Desktop/casetest/chat.html`**。

其中已写入：

1. **第一轮**：你要求按 `exam-paper.md` 拆资料库并补系统设计 / 需求规则 / 原型 HTML；助手回复用**摘要**呈现（含目录表与使用说明）。大段工具输出和已落盘文件的正文没有整段贴进页面，避免臃肿，实体内容仍在 **`exam-libraries/`** 里。  
2. **第二轮**：你要求从现在开始把所有对话记进根目录 `chat.html`（含上一轮）；以及本条说明。

页面顶部有一条**约定**：后续在本项目里的对话，你可以再说一声「追加到 chat.html」，我可以按同样结构在文件**末尾**继续补 `<article class="turn">` 条目。

本地查看：用浏览器打开 **`file:///Users/mac/Desktop/casetest/chat.html`** 即可。

