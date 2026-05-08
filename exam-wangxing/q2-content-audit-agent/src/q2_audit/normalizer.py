"""Normalize text for robust matching."""

from __future__ import annotations

import re


_WS = re.compile(r"\s+", re.UNICODE)
_ZERO_WIDTH = re.compile(r"[\u200b\u200c\u200d\ufeff]")


def normalize(text: str) -> str:
    t = text or ""
    t = _ZERO_WIDTH.sub("", t)
    t = _WS.sub(" ", t).strip()
    return t
