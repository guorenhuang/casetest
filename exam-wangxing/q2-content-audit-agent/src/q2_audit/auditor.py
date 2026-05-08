"""Orchestrate normalizer, OCR, rules, optional LLM, and evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from q2_audit.llm_adapter import classify_comment
from q2_audit.normalizer import normalize
from q2_audit.ocr_adapter import fetch_ocr_text
from q2_audit.rule_engine import RuleHit, evaluate_rules, merge_rule_actions


@dataclass
class AuditItemIn:
    id: str
    text: str
    image_urls: list[str] = field(default_factory=list)


@dataclass
class AuditEvidence:
    type: str  # rule | ocr | model | system
    id: str | None
    detail: str


@dataclass
class AuditItemOut:
    id: str
    verdict: str
    reasons: list[AuditEvidence]
    combined_text_sample: str


def audit_one(
    item: AuditItemIn,
    rules: list[dict[str, Any]],
    *,
    use_llm: bool = True,
    llm_timeout_ms: float = 800.0,
) -> AuditItemOut:
    reasons: list[AuditEvidence] = []
    base = normalize(item.text)
    ocr_chunks: list[str] = []
    for url in item.image_urls or []:
        ocr_text, note = fetch_ocr_text(url)
        reasons.append(AuditEvidence(type="ocr", id="ocr_adapter", detail=f"{note}:{url[:120]}"))
        if ocr_text:
            ocr_chunks.append(ocr_text)
            reasons.append(
                AuditEvidence(
                    type="ocr",
                    id="ocr_text",
                    detail=f"识别文本片段: {ocr_text[:200]}",
                )
            )

    combined = base
    if ocr_chunks:
        combined = f"{base}\n[OCR]\n" + "\n".join(ocr_chunks)

    has_image = bool(item.image_urls)
    hits = evaluate_rules(rules, text=combined, has_image=has_image)
    for h in hits:
        reasons.append(
            AuditEvidence(type="rule", id=h.rule_id, detail=f"[{h.kind}] {h.detail}")
        )

    rule_verdict = merge_rule_actions(hits)
    if rule_verdict == "block":
        return AuditItemOut(
            id=item.id,
            verdict="block",
            reasons=reasons,
            combined_text_sample=combined[:500],
        )
    if rule_verdict == "review":
        return AuditItemOut(
            id=item.id,
            verdict="review",
            reasons=reasons,
            combined_text_sample=combined[:500],
        )

    model_v: str | None = None
    model_reason: str | None = None
    if use_llm:
        model_v, model_reason = classify_comment(combined, timeout_ms=llm_timeout_ms)
        if model_v:
            reasons.append(
                AuditEvidence(type="model", id="llm_adapter", detail=model_reason or "model")
            )
        else:
            reasons.append(
                AuditEvidence(
                    type="system",
                    id="llm_degrade",
                    detail=f"模型不可用，规则未命中可疑项，按 pass 放行；{model_reason or ''}",
                )
            )

    if model_v in ("block", "review"):
        return AuditItemOut(
            id=item.id,
            verdict=model_v,
            reasons=reasons,
            combined_text_sample=combined[:500],
        )

    return AuditItemOut(
        id=item.id,
        verdict="pass",
        reasons=reasons,
        combined_text_sample=combined[:500],
    )


def audit_batch(
    items: list[AuditItemIn],
    rules: list[dict[str, Any]],
    **kw: Any,
) -> list[AuditItemOut]:
    return [audit_one(x, rules, **kw) for x in items]
