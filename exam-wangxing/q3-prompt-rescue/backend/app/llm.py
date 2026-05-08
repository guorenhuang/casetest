"""可选真实模型调用；无密钥时使用可复现的模拟输出以支撑流程演示。"""
from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any

import httpx

from .constants import BROKEN_SYSTEM_PROMPT


def llm_configured() -> bool:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    return bool(key)


def _plot_fingerprint(plot: str) -> int:
    return int(hashlib.sha256(plot.encode("utf-8")).hexdigest()[:8], 16)


def mock_broken_agent_output(plot: str, topic: str | None = None) -> str:
    """模拟「坏 prompt」常见问题：超长、非严格 JSON、改写剧情、字段漂移。"""
    fp = _plot_fingerprint(plot)
    long_fluff = ("并且这里要加年轻人喜欢的梗，" * 8) + "\n\n"
    altered = plot
    if "不" not in altered[:20]:
        altered = re.sub(r"^", "【为短剧爽感已改写】男主角改为霸总，", altered, count=1)

    shots = [
        {
            "镜头序号": i,
            "超长文学化描述": "慢镜头推进，情绪层层叠加，配合鼓点与反转预告，制造抖音式停留。" * 3,
            "台词": f'他说："我不接受"{i}"',
        }
        for i in range(1, 18 + (fp % 5))
    ]

    raw_obj = {
        "氛围": "韩系甜宠混合赛博朋克" if fp % 3 == 0 else "王家卫式悬疑狂欢",
        "魔改剧情摘要": altered[:200],
        "分镜": shots[:25],
    }

    prefix = f"（模拟·题材tag:{topic or '未标注'}）\n以下为分镜 JSON，可能含解释性前后文：\n"
    mid = long_fluff + json.dumps(raw_obj, ensure_ascii=False, indent=2)
    if fp % 2 == 0:
        # 尾逗号 + 说明：常见 parse 失败
        return prefix + mid[:-1] + ',\n  "备注": "故意尾逗号",\n}'
    return prefix + mid + "\n/* 又混入了注释，严格 JSON 解析会挂 */"


async def run_broken_prompt(plot: str, topic: str | None = None) -> tuple[str, str, bool]:
    """Returns (raw_output, model_name, used_real_llm)."""
    user_content = BROKEN_SYSTEM_PROMPT.format(plot=plot)
    if not llm_configured():
        return mock_broken_agent_output(plot, topic), "mock-broken-agent", False

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    key = os.environ.get("OPENAI_API_KEY", "").strip()

    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": user_content},
            {"role": "user", "content": "请直接输出结果。"},
        ],
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json=payload,
        )
        r.raise_for_status()
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        return text, model, True


async def run_fixed_prompt(plot: str, fixed_instruction: str) -> tuple[str, str, bool]:
    """fixed_instruction 为替换 {plot} 前的完整 system 侧指令文本。"""
    text_body = fixed_instruction.replace("{plot}", plot)
    if not llm_configured():
        fp = _plot_fingerprint(plot)
        ok = {
            "style_anchor": "克制纪实·固定锚点",
            "shots": [
                {
                    "idx": 1,
                    "duration_s": min(6.0, 4 + (fp % 3)),
                    "scene": plot[:40] + ("…" if len(plot) > 40 else ""),
                    "action": "固定镜头观察，不对剧情做臆断增补",
                    "camera": "中景固定",
                    "dialogue": "",
                },
                {
                    "idx": 2,
                    "duration_s": 5.0,
                    "scene": "同上一场延续",
                    "action": "角色情绪递进，不改变原著设定",
                    "camera": "手持微晃",
                    "dialogue": '\\"我在这里。\\"',
                },
            ],
        }
        raw = json.dumps(ok, ensure_ascii=False)
        return raw, "mock-fixed-agent", False

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": text_body},
            {"role": "user", "content": "仅输出 JSON 对象本体。"},
        ],
        "temperature": 0.2,
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json=payload,
        )
        r.raise_for_status()
        data = r.json()
        text = data["choices"][0]["message"]["content"].strip()
        return text, model, True
