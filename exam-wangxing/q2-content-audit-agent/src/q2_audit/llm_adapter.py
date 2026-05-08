"""
可选 LLM 分类；超时或失败返回 None（调用方仅用规则链路决策 + 写明降级证据）。
替换模型：环境变量 OPENAI_BASE_URL（默认 https://api.openai.com/v1）、OPENAI_MODEL、OPENAI_API_KEY。
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

try:
    import httpx
except ImportError:
    httpx = None


def classify_comment(
    text: str,
    *,
    timeout_ms: float = 800.0,
) -> tuple[str | None, str | None]:
    """
    Returns (verdict_pass_review_block | None, model_reason_or_error).
    None verdict => caller uses rule-only outcome.
    """
    api_key = os.getenv("OPENAI_API_KEY") or ""
    base_url = (os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL") or os.getenv("LLM_MODEL") or "gpt-4o-mini"

    if not api_key or httpx is None:
        return None, "llm_disabled_or_no_httpx"

    url = f"{base_url}/chat/completions"

    system = (
        '你是短剧评论审核员。仅输出紧凑 JSON（不要 markdown）：'
        '{"verdict":"pass|review|block","reason":"简短中文"}。'
        "block=明确违规；review=疑似需人工；pass=正常讨论。"
    )
    user = f"评论：\n{text[:4000]}"

    payload: dict[str, Any] = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }

    try:
        with httpx.Client(timeout=timeout_ms / 1000.0) as client:
            r = client.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
            content = data["choices"][0]["message"]["content"].strip()
            # 兼容模型偶发包裹代码块
            if content.startswith("```"):
                content = content.strip("`").split("\n", 1)[-1].strip()
            obj = json.loads(content)
            v = str(obj.get("verdict", "")).lower()
            reason = str(obj.get("reason", "")).strip()
            if v not in ("pass", "review", "block"):
                return None, f"invalid_model_json:{content[:200]}"
            return v, reason or "model_classify"
    except Exception as e:
        logger.warning("llm_classify_failed: %s", e)
        return None, f"llm_error:{type(e).__name__}"
