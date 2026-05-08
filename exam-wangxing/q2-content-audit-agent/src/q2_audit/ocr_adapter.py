"""
图片 OCR 接入点：生产可替换为腾讯云/百度/阿里云等；此处 mock ——根据 URL query 注入「识别文本」演示证据链。
真实接入：实现 fetch_ocr_text(url: str) -> str 并保持函数签名不变即可。
"""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse


def fetch_ocr_text(image_url: str) -> tuple[str | None, str]:
    """Return (recognized_text, adapter_note). None text => skip."""
    if not image_url or not image_url.strip():
        return None, "empty_url"
    if not (image_url.startswith("http://") or image_url.startswith("https://")):
        return None, "invalid_scheme"

    # --- Mock: 若 URL 带 ?ocr= 或 ?text= 则视为「图内文字」 ---
    parsed = urlparse(image_url)
    qs = parse_qs(parsed.query)
    for key in ("ocr", "text", "mock"):
        if key in qs and qs[key]:
            raw = qs[key][0]
            note = f"mock_ocr_param:{key}"
            return raw.replace("+", " "), note

    host = (parsed.hostname or "").lower()
    if "img.example.com" in host or "cdn.quiz.test" in host:
        # 预设：图床上「招商」贴片
        guessed = "[图内 OCR mock] V➕ 18812345678 限时进群"
        return guessed, "mock_host_heuristic"

    return None, "mock_no_hit"
