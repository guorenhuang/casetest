"""Generate markdown deliverables (R1–R5)."""
from __future__ import annotations

import sqlite3
from pathlib import Path


def build_observations_md(conn: sqlite3.Connection) -> str:
    cur = conn.execute(
        "SELECT id, plot, topic, raw_output, model_name, used_real_llm, created_at "
        "FROM observation_runs ORDER BY id ASC"
    )
    rows = cur.fetchall()
    lines = [
        "# observations.md",
        "",
        "> R1：≥5 条不同长度/题材的真实推理原始输出（此处为工作台导出）。",
        "",
    ]
    for r in rows:
        lines.append(f"## Run #{r['id']} · {r['created_at']} · model=`{r['model_name']}` · real_llm={bool(r['used_real_llm'])}")
        lines.append(f"- topic: {r['topic'] or '(未填)'}")
        lines.append("")
        lines.append("### Plot")
        lines.append("")
        lines.append("```text")
        lines.append(r["plot"])
        lines.append("```")
        lines.append("")
        lines.append("### Raw output")
        lines.append("")
        lines.append("```text")
        lines.append(r["raw_output"])
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def build_issues_md(conn: sqlite3.Connection) -> str:
    cur = conn.execute(
        "SELECT issue_key, title, phenomenon, evidence, why_problem "
        "FROM issues ORDER BY sort_order ASC, id ASC"
    )
    rows = cur.fetchall()
    lines = ["# issues.md", "", "> R2：每条含 **现象 + 证据片段 + 为何是问题**。", ""]
    for r in rows:
        title = r["title"] or r["issue_key"]
        lines.extend(
            [
                f"## {r['issue_key']} — {title}",
                "",
                f"- **现象**：{r['phenomenon']}",
                f"- **证据片段**：{r['evidence']}",
                f"- **为何是问题**：{r['why_problem']}",
                "",
            ]
        )
    return "\n".join(lines)


def build_fixed_prompt_md(conn: sqlite3.Connection) -> str:
    cur = conn.execute("SELECT content FROM fixed_prompt WHERE id = 1")
    row = cur.fetchone()
    content = row["content"] if row else ""
    cur2 = conn.execute("SELECT issue_key, change_summary FROM prompt_change_mappings ORDER BY id ASC")
    maps = cur2.fetchall()
    lines = [
        "# fixed_prompt.md",
        "",
        "> R4：新 prompt + **每处改动 ↔ 解决的问题** 映射；禁止笼统一锅端。",
        "",
        "## 新 System Prompt",
        "",
        "```text",
        content,
        "```",
        "",
        "## 改动 ↔ Issue 映射表",
        "",
        "| Issue | 改动要点 |",
        "|---|---|",
    ]
    for m in maps:
        lines.append(f"| {m['issue_key']} | {m['change_summary']} |")
    if not maps:
        lines.append("| （空） | 请在 UI 中补充映射 |")
    lines.append("")
    return "\n".join(lines)


def build_before_after_md(conn: sqlite3.Connection) -> str:
    cur = conn.execute(
        "SELECT id, label, plot, before_output, after_output, notes FROM before_after ORDER BY id ASC"
    )
    rows = cur.fetchall()
    lines = [
        "# before_after.md",
        "",
        "> R5：≥2 组 before/after，证明对 JSON/长度/风格/忠实度等有效。",
        "",
    ]
    for r in rows:
        lab = r["label"] or f"组 #{r['id']}"
        lines.extend(
            [
                f"## {lab}",
                "",
                "### Plot",
                "",
                "```text",
                r["plot"],
                "```",
                "",
                "### Before",
                "",
                "```text",
                r["before_output"],
                "```",
                "",
                "### After",
                "",
                "```text",
                r["after_output"],
                "```",
                "",
            ]
        )
        if r["notes"]:
            lines.extend(["### 备注", "", r["notes"], ""])
    return "\n".join(lines)


def build_transcript_md(conn: sqlite3.Connection) -> str:
    cur = conn.execute(
        "SELECT role, content, strategy_note, created_at FROM transcript_messages ORDER BY id ASC"
    )
    rows = cur.fetchall()
    lines = [
        "# transcript.md",
        "",
        "> R3：与 AI 协同诊断时，可见**逼出真问题**的策略，而非泛泛「挺好」。",
        "",
    ]
    for r in rows:
        strat = "【策略标记】" if r["strategy_note"] else ""
        lines.append(f"## {strat}{r['role']} · {r['created_at']}")
        lines.append("")
        lines.append(r["content"])
        lines.append("")
    return "\n".join(lines)


def write_deliverables(conn: sqlite3.Connection, out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "observations.md": build_observations_md(conn),
        "issues.md": build_issues_md(conn),
        "fixed_prompt.md": build_fixed_prompt_md(conn),
        "before_after.md": build_before_after_md(conn),
        "transcript.md": build_transcript_md(conn),
    }
    written: dict[str, str] = {}
    for name, body in files.items():
        p = out_dir / name
        p.write_text(body, encoding="utf-8")
        written[name] = str(p.resolve())
    return written
