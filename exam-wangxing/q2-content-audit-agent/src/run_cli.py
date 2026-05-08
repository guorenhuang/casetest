#!/usr/bin/env python3
"""CLI: cd src && PYTHONPATH=. python run_cli.py --input ../dataset.json --out ../run_report.md"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
sys.path.insert(0, str(SRC))

from q2_audit.auditor import AuditItemIn, audit_batch  # noqa: E402
from q2_audit.db import connect, fetch_enabled_rules, get_db_path, init_db  # noqa: E402
from q2_audit.seed import ensure_seeded  # noqa: E402


def load_dataset(path: Path) -> tuple[list[AuditItemIn], dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("comments") if isinstance(data, dict) else data
    items: list[AuditItemIn] = []
    expect: dict[str, str] = {}
    for row in rows:
        rid = str(row["id"])
        items.append(
            AuditItemIn(
                id=rid,
                text=str(row.get("text", "")),
                image_urls=list(row.get("image_urls") or []),
            )
        )
        if row.get("expect"):
            expect[rid] = str(row["expect"])
    return items, expect


def fmt_reason(ev) -> str:
    eid = ev.get("id") or "-"
    return f'`{ev["type"]}` **{eid}**: {ev["detail"]}'


def fairness_line(verdict: str, expect: str | None) -> str:
    if not expect:
        return "未标注预期：从运营视角看，证据链是否自洽需结合业务微调规则优先级。"
    if verdict == expect:
        return f"与标注预期 `{expect}` 一致，当前规则优先级可接受。"
    return (
        f"与标注预期 `{expect}` **不一致**：可能因 URL/正则过宽或 LLM 关闭导致；"
        f"建议收紧/放宽对应规则或补充词表。"
    )


def write_report(path: Path, results: list[dict], expect_map: dict[str, str]) -> None:
    lines = [
        "# 评论审核批量报告（Q2 · 自动生成）",
        "",
        "本报告由 `run_cli.py` **默认不调用 LLM**（需显传 `--use-llm`）生成，用于展示 **规则 + OCR 可独立跑通** 与每条 **命中证据**；线上可常驻开启 LLM 作为补充信号。",
        "",
        "---",
        "",
    ]
    for r in results:
        rid = r["id"]
        ex = expect_map.get(rid)
        lines.append(f"## {rid}")
        lines.append("")
        lines.append(f"- **结论**: `{r['verdict']}`")
        lines.append("- **证据**:")
        if not r["reasons"]:
            lines.append(
                "  - _无命中项：规则/OCR 未触发；本条未启用 LLM，按 `pass` 放行（见设计要求：模型不可用仍可出结论）_"
            )
        else:
            for ev in r["reasons"]:
                lines.append(f"  - {fmt_reason(ev)}")
        lines.append(f"- **是否合理（实现侧复核）**: {fairness_line(r['verdict'], ex)}")
        if r.get("combined_text_sample"):
            lines.append("- **合并文本截断**:")
            lines.append("")
            lines.append("```text")
            lines.append(r["combined_text_sample"][:800])
            lines.append("```")
        lines.append("")
    lines.extend(
        [
            "---",
            "",
            "## 数据集与刁钻样本取舍",
            "",
            "- 正常讨论、玩梗、剧情吐槽占多数，应大量 `pass`。",
            "- 明显辱骂命中 `PROFAN_LEXICON_L1` → `block`。",
            "- 显性「加微信」类命中词表或正则 → `block`。",
            "- 拼音拆写、首字母、emoji+V+数字等 **刻意绕审** 样本推向 `review`，避免误杀正常英文/数字讨论。",
            "- 图床 URL 走 `ocr_adapter` mock：query 参数或域名启发式注入「图中文字」，用于演示 **图片 OCR 证据**。",
            "- 若启用 LLM：超时/异常时仍可返回上面规则结果（见 auditor 降级分支）。",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Batch audit → markdown report")
    ap.add_argument("--input", type=Path, default=ROOT / "dataset.json")
    ap.add_argument("--out", type=Path, default=ROOT / "run_report.md")
    ap.add_argument("--use-llm", action="store_true", help="Call model (needs OPENAI_API_KEY)")
    args = ap.parse_args()

    ensure_seeded(ROOT / "data" / "audit.db", yaml_rel="rules.yaml")
    dbp = get_db_path(ROOT)
    conn = connect(dbp)
    try:
        init_db(conn)
        rules = fetch_enabled_rules(conn)
    finally:
        conn.close()

    items, expect_map = load_dataset(args.input)
    outs = audit_batch(items, rules, use_llm=args.use_llm, llm_timeout_ms=800.0)
    results = [
        {
            "id": o.id,
            "verdict": o.verdict,
            "reasons": [
                {"type": r.type, "id": r.id, "detail": r.detail} for r in o.reasons
            ],
            "combined_text_sample": o.combined_text_sample,
        }
        for o in outs
    ]
    write_report(args.out, results, expect_map)
    print(f"Wrote {args.out} ({len(results)} items)")


if __name__ == "__main__":
    main()
