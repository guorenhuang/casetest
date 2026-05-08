"""Evaluate externalized rules against combined text (+ optional OCR)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class RuleHit:
    rule_id: str
    action: str
    kind: str
    detail: str


def _flag_set(name: str) -> int:
    if not name:
        return 0
    bits = 0
    up = name.upper()
    if "IGNORECASE" in up:
        bits |= re.IGNORECASE
    if "MULTILINE" in up:
        bits |= re.MULTILINE
    return bits


def _lexicon_hit(config: dict[str, Any], text: str) -> str | None:
    terms = config.get("terms") or []
    case_insensitive = bool(config.get("case_insensitive", True))
    hay = text.lower() if case_insensitive else text
    for term in terms:
        if not term:
            continue
        needle = str(term).lower() if case_insensitive else str(term)
        if needle in hay:
            return f"命中词表: 「{term}」"
    return None


def _regex_hit(rule: dict[str, Any], text: str) -> str | None:
    cfg = rule.get("config") or {}
    pattern = cfg.get("pattern")
    if not pattern:
        return None
    flags = _flag_set(str(cfg.get("flags", "IGNORECASE")))
    try:
        m = re.search(pattern, text, flags)
    except re.error:
        return None
    if m:
        snippet = m.group(0)[:80]
        tmpl = cfg.get("detail_template")
        if tmpl:
            try:
                return tmpl.format(snippet=snippet)
            except Exception:
                pass
        return f"正则命中: 「{snippet}」"
    return None


def _digit_hit(rule: dict[str, Any], text: str) -> str | None:
    cfg = rule.get("config") or {}
    min_digits = int(cfg.get("min_digits", 8))
    alt = cfg.get("alternate_regex")
    if alt:
        try:
            if re.search(str(alt), text, re.IGNORECASE):
                return "数字/分段号码模式命中"
        except re.error:
            pass
    runs = re.findall(r"\d+", text)
    if runs and max(len(x) for x in runs) >= min_digits:
        return f"连续数字 ≥{min_digits}"
    return None


def evaluate_rules(
    rules: list[dict[str, Any]],
    *,
    text: str,
    has_image: bool,
) -> list[RuleHit]:
    hits: list[RuleHit] = []
    for r in rules:
        cfg = r.get("config") or {}
        if cfg.get("apply_when_image") and not has_image:
            continue
        kind = r.get("kind")
        action = r.get("action")
        rid = r.get("id", "?")
        detail: str | None = None
        if kind == "lexicon":
            detail = _lexicon_hit(cfg, text)
        elif kind == "regex":
            detail = _regex_hit(r, text)
        elif kind == "digit_sequence":
            detail = _digit_hit(r, text)
        else:
            detail = _regex_hit(r, text) or _lexicon_hit(cfg, text)

        if detail:
            hits.append(
                RuleHit(
                    rule_id=str(rid),
                    action=str(action),
                    kind=str(kind),
                    detail=detail,
                )
            )
    return hits


def merge_rule_actions(hits: list[RuleHit]) -> str | None:
    """If any block -> block; elif any review -> review; else None (defer to model/default pass)."""
    if any(h.action == "block" for h in hits):
        return "block"
    if any(h.action == "review" for h in hits):
        return "review"
    return None
