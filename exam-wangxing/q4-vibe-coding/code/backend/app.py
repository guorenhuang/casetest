"""Storyboard → English art prompt API backed by SQLite."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

DB_PATH = Path(
    os.getenv(
        "STORYBOARD_DB_PATH",
        str(Path(__file__).resolve().parent / "storyboard.db"),
    )
)


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS shots (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              shot_no INTEGER NOT NULL DEFAULT 1,
              scene TEXT DEFAULT '',
              action TEXT DEFAULT '',
              mood TEXT DEFAULT '',
              camera TEXT DEFAULT '',
              notes TEXT DEFAULT '',
              english_prompt TEXT DEFAULT '',
              created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


class ShotIn(BaseModel):
    shot_no: int = Field(ge=1, description="分镜序号")
    scene: str = ""
    action: str = ""
    mood: str = ""
    camera: str = ""
    notes: str = ""
    english_prompt: str = ""


class ShotOut(ShotIn):
    id: int
    created_at: str | None = None


class ShotPatch(BaseModel):
    shot_no: int | None = None
    scene: str | None = None
    action: str | None = None
    mood: str | None = None
    camera: str | None = None
    notes: str | None = None
    english_prompt: str | None = None


app = FastAPI(title="Storyboard Prompt API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def row_to_shot(r: sqlite3.Row) -> dict:
    return {
        "id": r["id"],
        "shot_no": r["shot_no"],
        "scene": r["scene"] or "",
        "action": r["action"] or "",
        "mood": r["mood"] or "",
        "camera": r["camera"] or "",
        "notes": r["notes"] or "",
        "english_prompt": r["english_prompt"] or "",
        "created_at": r["created_at"],
    }


def template_prompt(shot: ShotIn) -> str:
    parts = [
        f"Cinematic storyboard shot {shot.shot_no}, single frame.",
        f"Scene: {shot.scene.strip() or '—'}." if shot.scene.strip() else "",
        f"Action: {shot.action.strip() or '—'}." if shot.action.strip() else "",
        f"Mood/lighting: {shot.mood.strip() or 'neutral dramatic lighting'}."
        if shot.mood.strip()
        else "Mood/lighting: neutral cinematic lighting.",
        f"Camera: {shot.camera.strip() or 'medium shot'}." if shot.camera.strip() else "Camera: medium shot.",
    ]
    if shot.notes.strip():
        parts.append(f"Notes: {shot.notes.strip()}.")
    parts.append(
        "Highly detailed, film grain, professional concept art, 8k, no text, no watermark."
    )
    return " ".join(p for p in parts if p)


async def openai_prompt(shot: ShotIn) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return template_prompt(shot)
    user_block = json.dumps(
        {
            "shot_no": shot.shot_no,
            "scene": shot.scene,
            "action": shot.action,
            "mood": shot.mood,
            "camera": shot.camera,
            "notes": shot.notes,
        },
        ensure_ascii=False,
    )
    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "messages": [
            {
                "role": "system",
                "content": (
                    "You write concise English prompts for text-to-image / storyboard frames. "
                    "Output ONE paragraph only, no markdown, no bullet list. "
                    "Style: cinematic, specific, suitable for Midjourney or SDXL."
                ),
            },
            {
                "role": "user",
                "content": f"Turn this storyboard row into one English image prompt:\n{user_block}",
            },
        ],
        "temperature": 0.7,
        "max_tokens": 400,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
    if r.status_code >= 400:
        return template_prompt(shot)
    data = r.json()
    try:
        return (data["choices"][0]["message"]["content"] or "").strip() or template_prompt(
            shot
        )
    except (KeyError, IndexError, TypeError):
        return template_prompt(shot)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "db": str(DB_PATH)}


@app.get("/api/shots", response_model=list[ShotOut])
def list_shots() -> list[dict]:
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM shots ORDER BY shot_no ASC, id ASC")
        return [row_to_shot(r) for r in cur.fetchall()]


@app.post("/api/shots", response_model=ShotOut)
def create_shot(body: ShotIn) -> dict:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO shots (shot_no, scene, action, mood, camera, notes, english_prompt)
            VALUES (?,?,?,?,?,?,?)
            """,
            (
                body.shot_no,
                body.scene,
                body.action,
                body.mood,
                body.camera,
                body.notes,
                body.english_prompt,
            ),
        )
        conn.commit()
        sid = cur.lastrowid
        row = conn.execute("SELECT * FROM shots WHERE id = ?", (sid,)).fetchone()
    assert row is not None
    return row_to_shot(row)


@app.patch("/api/shots/{shot_id}", response_model=ShotOut)
def patch_shot(shot_id: int, body: ShotPatch) -> dict:
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        with get_conn() as conn:
            row = conn.execute("SELECT * FROM shots WHERE id = ?", (shot_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        return row_to_shot(row)
    cols = ", ".join(f"{k} = ?" for k in fields)
    vals = list(fields.values())
    vals.append(shot_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE shots SET {cols} WHERE id = ?", vals)
        conn.commit()
        row = conn.execute("SELECT * FROM shots WHERE id = ?", (shot_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    return row_to_shot(row)


@app.delete("/api/shots/{shot_id}")
def delete_shot(shot_id: int) -> dict:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM shots WHERE id = ?", (shot_id,))
        conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="not found")
    return {"deleted": shot_id}


@app.post("/api/shots/{shot_id}/generate-prompt", response_model=ShotOut)
async def generate_prompt(shot_id: int) -> dict:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM shots WHERE id = ?", (shot_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    shot = ShotIn(
        shot_no=row["shot_no"],
        scene=row["scene"] or "",
        action=row["action"] or "",
        mood=row["mood"] or "",
        camera=row["camera"] or "",
        notes=row["notes"] or "",
    )
    text = await openai_prompt(shot)
    with get_conn() as conn:
        conn.execute(
            "UPDATE shots SET english_prompt = ? WHERE id = ?",
            (text, shot_id),
        )
        conn.commit()
        row2 = conn.execute("SELECT * FROM shots WHERE id = ?", (shot_id,)).fetchone()
    assert row2 is not None
    return row_to_shot(row2)


@app.post("/api/seed-demo")
def seed_demo() -> dict:
    """Insert ≥3 demo rows so first run has something on screen."""
    demos = [
        (1, "雨夜小巷", "主角抬头看霓虹招牌", "冷色调、潮湿反光", "低角度广角", "节奏：铺垫"),
        (2, "办公室日戏", "两人隔着玻璃对峙", "高对比侧光", "过肩镜头", ""),
        (3, "天台黄昏", "衣角被风吹起，远处城市剪影", "金色逆光", "航拍缓缓推进", "高潮前一刻"),
    ]
    with get_conn() as conn:
        conn.execute("DELETE FROM shots")
        for shot_no, scene, action, mood, camera, notes in demos:
            prompt = template_prompt(
                ShotIn(
                    shot_no=shot_no,
                    scene=scene,
                    action=action,
                    mood=mood,
                    camera=camera,
                    notes=notes,
                )
            )
            conn.execute(
                """
                INSERT INTO shots (shot_no, scene, action, mood, camera, notes, english_prompt)
                VALUES (?,?,?,?,?,?,?)
                """,
                (shot_no, scene, action, mood, camera, notes, prompt),
            )
        conn.commit()
    return {"seeded": len(demos)}


_static_root = os.getenv("STATIC_DIR", "").strip()
if _static_root:
    _p = Path(_static_root)
    if _p.is_dir():
        app.mount(
            "/",
            StaticFiles(directory=str(_p), html=True),
            name="static",
        )
