"""Q3 Prompt 救火 — FastAPI + SQLite。"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Annotated, Any, Generator

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import export_md
from .constants import BROKEN_SYSTEM_PROMPT
from .db import get_connection, init_db
from .llm import llm_configured, run_broken_prompt, run_fixed_prompt

def export_target_dir() -> Path:
    raw = os.environ.get("Q3_EXPORT_DIR", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    # 默认：本题目录（与试卷要求的 observations.md 等交付物同级，便于打包 exam-wangxing）
    return Path(__file__).resolve().parents[2].resolve()


app = FastAPI(title="Q3 Prompt Rescue Workbench", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


def db_conn() -> Generator[sqlite3.Connection, None, None]:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


Db = Annotated[sqlite3.Connection, Depends(db_conn)]


@app.get("/api/meta")
def api_meta() -> dict[str, Any]:
    return {
        "broken_prompt_template": BROKEN_SYSTEM_PROMPT,
        "llm_configured": llm_configured(),
        "export_dir": str(export_target_dir()),
    }


@app.get("/api/observations")
def list_observations(conn: Db) -> list[dict[str, Any]]:
    cur = conn.execute(
        "SELECT id, plot, topic, raw_output, model_name, used_real_llm, created_at "
        "FROM observation_runs ORDER BY id DESC LIMIT 200"
    )
    return [dict(r) for r in cur.fetchall()]


class RunObservationBody(BaseModel):
    plot: str = Field(..., min_length=4)
    topic: str | None = None


@app.post("/api/observations/run")
async def run_observation(body: RunObservationBody, conn: Db) -> dict[str, Any]:
    raw, model, real = await run_broken_prompt(body.plot, body.topic)
    cur = conn.execute(
        """INSERT INTO observation_runs (plot, topic, raw_output, model_name, used_real_llm)
           VALUES (?, ?, ?, ?, ?)""",
        (body.plot, body.topic, raw, model, 1 if real else 0),
    )
    conn.commit()
    rid = cur.lastrowid
    row = conn.execute("SELECT * FROM observation_runs WHERE id = ?", (rid,)).fetchone()
    return dict(row) if row else {"id": rid}


@app.get("/api/issues")
def list_issues(conn: Db) -> list[dict[str, Any]]:
    cur = conn.execute("SELECT * FROM issues ORDER BY sort_order ASC, id ASC")
    return [dict(r) for r in cur.fetchall()]


class IssueBody(BaseModel):
    issue_key: str = Field(..., min_length=1)
    title: str | None = None
    phenomenon: str
    evidence: str
    why_problem: str
    sort_order: int = 0


@app.post("/api/issues")
def create_issue(body: IssueBody, conn: Db) -> dict[str, Any]:
    try:
        cur = conn.execute(
            """INSERT INTO issues (issue_key, title, phenomenon, evidence, why_problem, sort_order)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                body.issue_key,
                body.title,
                body.phenomenon,
                body.evidence,
                body.why_problem,
                body.sort_order,
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"duplicate_issue_key: {e}") from e
    rid = cur.lastrowid
    row = conn.execute("SELECT * FROM issues WHERE id = ?", (rid,)).fetchone()
    return dict(row) if row else {"id": rid}


class IssuePatch(BaseModel):
    title: str | None = None
    phenomenon: str | None = None
    evidence: str | None = None
    why_problem: str | None = None
    sort_order: int | None = None


@app.patch("/api/issues/{issue_id}")
def patch_issue(issue_id: int, body: IssuePatch, conn: Db) -> dict[str, Any]:
    existing = conn.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="not_found")
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        return dict(existing)
    cols = ", ".join(f"{k} = ?" for k in fields)
    vals = list(fields.values()) + [issue_id]
    conn.execute(f"UPDATE issues SET {cols} WHERE id = ?", vals)
    conn.commit()
    row = conn.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    return dict(row) if row else {}


@app.delete("/api/issues/{issue_id}")
def delete_issue(issue_id: int, conn: Db) -> dict[str, str]:
    conn.execute("DELETE FROM issues WHERE id = ?", (issue_id,))
    conn.commit()
    return {"ok": "true"}


@app.get("/api/transcript")
def list_transcript(conn: Db) -> list[dict[str, Any]]:
    cur = conn.execute("SELECT * FROM transcript_messages ORDER BY id ASC LIMIT 500")
    return [dict(r) for r in cur.fetchall()]


class TranscriptBody(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|coach)$")
    content: str = Field(..., min_length=1)
    strategy_note: bool = False


@app.post("/api/transcript")
def add_transcript(body: TranscriptBody, conn: Db) -> dict[str, Any]:
    cur = conn.execute(
        """INSERT INTO transcript_messages (role, content, strategy_note)
           VALUES (?, ?, ?)""",
        (body.role, body.content, 1 if body.strategy_note else 0),
    )
    conn.commit()
    rid = cur.lastrowid
    row = conn.execute("SELECT * FROM transcript_messages WHERE id = ?", (rid,)).fetchone()
    return dict(row) if row else {"id": rid}


@app.delete("/api/transcript")
def clear_transcript(conn: Db) -> dict[str, str]:
    conn.execute("DELETE FROM transcript_messages")
    conn.commit()
    return {"ok": "true"}


class FixedPromptBody(BaseModel):
    content: str = Field(..., min_length=10)


@app.get("/api/fixed-prompt")
def get_fixed(conn: Db) -> dict[str, Any]:
    row = conn.execute("SELECT content, updated_at FROM fixed_prompt WHERE id = 1").fetchone()
    cur = conn.execute("SELECT id, issue_key, change_summary FROM prompt_change_mappings ORDER BY id ASC")
    return {
        "content": row["content"] if row else "",
        "updated_at": row["updated_at"] if row else "",
        "mappings": [dict(r) for r in cur.fetchall()],
    }


@app.put("/api/fixed-prompt")
def put_fixed(body: FixedPromptBody, conn: Db) -> dict[str, str]:
    conn.execute(
        "UPDATE fixed_prompt SET content = ?, updated_at = datetime('now') WHERE id = 1",
        (body.content,),
    )
    conn.commit()
    return {"ok": "true"}


class MappingItem(BaseModel):
    issue_key: str
    change_summary: str


@app.put("/api/fixed-prompt/mappings")
def put_mappings(items: list[MappingItem], conn: Db) -> dict[str, str]:
    conn.execute("DELETE FROM prompt_change_mappings")
    for it in items:
        conn.execute(
            "INSERT INTO prompt_change_mappings (issue_key, change_summary) VALUES (?, ?)",
            (it.issue_key, it.change_summary),
        )
    conn.commit()
    return {"ok": "true"}


@app.get("/api/before-after")
def list_before_after(conn: Db) -> list[dict[str, Any]]:
    cur = conn.execute("SELECT * FROM before_after ORDER BY id ASC")
    return [dict(r) for r in cur.fetchall()]


class BeforeAfterBody(BaseModel):
    label: str | None = None
    plot: str
    before_output: str
    after_output: str
    notes: str | None = None


@app.post("/api/before-after")
def create_ba(body: BeforeAfterBody, conn: Db) -> dict[str, Any]:
    cur = conn.execute(
        """INSERT INTO before_after (label, plot, before_output, after_output, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (body.label, body.plot, body.before_output, body.after_output, body.notes),
    )
    conn.commit()
    rid = cur.lastrowid
    row = conn.execute("SELECT * FROM before_after WHERE id = ?", (rid,)).fetchone()
    return dict(row) if row else {"id": rid}


class GenerateBeforeAfterBody(BaseModel):
    plot: str = Field(..., min_length=4)
    label: str | None = None


@app.post("/api/before-after/generate")
async def generate_ba(body: GenerateBeforeAfterBody, conn: Db) -> dict[str, Any]:
    before_raw, bmodel, _ = await run_broken_prompt(body.plot, None)
    row_fp = conn.execute("SELECT content FROM fixed_prompt WHERE id = 1").fetchone()
    fixed = row_fp["content"] if row_fp else ""
    after_raw, amodel, _ = await run_fixed_prompt(body.plot, fixed)
    cur = conn.execute(
        """INSERT INTO before_after (label, plot, before_output, after_output, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (
            body.label,
            body.plot,
            before_raw,
            after_raw,
            f"before_model={bmodel}; after_model={amodel}",
        ),
    )
    conn.commit()
    rid = cur.lastrowid
    row = conn.execute("SELECT * FROM before_after WHERE id = ?", (rid,)).fetchone()
    return dict(row) if row else {"id": rid}


@app.delete("/api/before-after/{ba_id}")
def delete_ba(ba_id: int, conn: Db) -> dict[str, str]:
    conn.execute("DELETE FROM before_after WHERE id = ?", (ba_id,))
    conn.commit()
    return {"ok": "true"}


@app.post("/api/export/markdown")
def export_markdown(conn: Db) -> dict[str, Any]:
    warnings: list[str] = []
    n_obs = conn.execute("SELECT COUNT(*) AS c FROM observation_runs").fetchone()["c"]
    n_issue = conn.execute("SELECT COUNT(*) AS c FROM issues").fetchone()["c"]
    n_ba = conn.execute("SELECT COUNT(*) AS c FROM before_after").fetchone()["c"]
    n_tr = conn.execute("SELECT COUNT(*) AS c FROM transcript_messages").fetchone()["c"]
    if n_obs < 5:
        warnings.append(f"R1：观测不足 5 条（当前 {n_obs}）")
    if n_issue < 4:
        warnings.append(f"问题清单不足 4 条（当前 {n_issue}）")
    if n_ba < 2:
        warnings.append(f"R5：before/after 不足 2 组（当前 {n_ba}）")
    if n_tr < 1:
        warnings.append("R3：transcript 为空，建议记录协同诊断过程")
    n_map = conn.execute("SELECT COUNT(*) AS c FROM prompt_change_mappings").fetchone()["c"]
    if n_map < 1:
        warnings.append("R4：fixed_prompt 映射表为空")
    out = export_target_dir()
    written = export_md.write_deliverables(conn, out)
    return {"written": written, "export_dir": str(out), "warnings": warnings}


class SeedBody(BaseModel):
    include_transcript_templates: bool = True


@app.post("/api/seed/demo")
async def seed_demo(body: SeedBody, conn: Db) -> dict[str, Any]:
    """若库为空：写入 ≥5 条观测 + ≥4 issues + transcript 范例 + prompt 映射。"""
    cur = conn.execute("SELECT COUNT(*) AS c FROM observation_runs")
    n = cur.fetchone()["c"]
    demo_plots = [
        ("甜宠", "电梯里误会霸总是快递员，三句话内反转成甲方；全程办公室。"),
        ("悬疑", "雨夜老宅，女主收到十年前失踪父亲的短信，只能回答是否。"),
        ("复仇", "豪门宴上，被换肾的养女当场播放手术录音，全场静音十秒。"),
        ("穿越", "古装宫女醒来发现手中是 iPhone 闹钟，御花园直播社死。"),
        ("家庭伦理", "婆婆把婚房过户给外甥，儿媳拿出婚前公证与缴费记录当庭对质。"),
        ("极短", "离。" * 8),
    ]
    created_runs = 0
    if n == 0:
        for topic, plot in demo_plots:
            raw, model, real = await run_broken_prompt(plot, topic)
            conn.execute(
                """INSERT INTO observation_runs (plot, topic, raw_output, model_name, used_real_llm)
                   VALUES (?, ?, ?, ?, ?)""",
                (plot, topic, raw, model, 1 if real else 0),
            )
            created_runs += 1
        conn.commit()

    cur2 = conn.execute("SELECT COUNT(*) AS c FROM issues")
    created_issues = 0
    if cur2.fetchone()["c"] == 0:
        samples = [
            (
                "I-1",
                "输出超长且字段不可控",
                "单次分镜条目数远超下游可承载，字段名中英文混用。",
                "observations Run#1 raw 中出现 18+ 条分镜且含「超长文学化描述」。",
                "拖垮 token 与下游 schema 校验，解析成本不可控。",
                1,
            ),
            (
                "I-2",
                "非合法 JSON",
                "输出夹带说明文字、注释或尾逗号。",
                "raw 中含“以下为分镜 JSON”前缀或 `/* 注释 */`。",
                "strict JSON.parse 失败，线上流水线直接报错。",
                2,
            ),
            (
                "I-3",
                "风格锚点主观漂移",
                "同一任务多次运行风格描述互相矛盾。",
                "不同 run 的「氛围」在甜宠/赛博/文艺间跳变。",
                "后期无法统一调色与剪辑节奏。",
                3,
            ),
            (
                "I-4",
                "篡改用户设定",
                "在未授权情况下改写人设或主线。",
                "raw 出现「魔改剧情摘要」「为短剧爽感已改写」前缀。",
                "用户核心设定丢失，合规与舆情风险上升。",
                4,
            ),
        ]
        conn.executemany(
            """INSERT INTO issues (issue_key, title, phenomenon, evidence, why_problem, sort_order)
               VALUES (?, ?, ?, ?, ?, ?)""",
            samples,
        )
        conn.commit()
        created_issues = len(samples)

    if body.include_transcript_templates:
        cur3 = conn.execute("SELECT COUNT(*) AS c FROM transcript_messages")
        if cur3.fetchone()["c"] == 0:
            msgs = [
                (
                    "coach",
                    "不要泛泛评价 prompt。请逐条对应 observations.md 的运行编号给出证据片段。",
                    1,
                ),
                ("assistant", "收到。我将从 Run #1 开始引用原文中的 JSON 前缀与字段名。", 0),
                ("user", "若 JSON 不合格，请说明是 trailing comma、注释还是非对象根节点。", 1),
            ]
            conn.executemany(
                "INSERT INTO transcript_messages (role, content, strategy_note) VALUES (?, ?, ?)",
                msgs,
            )
            conn.commit()

    if created_issues > 0:
        mappings = [
            ("I-1", "增加 shots≤12、单行短句与 duration 上限；禁止自由扩写字段"),
            ("I-2", "要求仅输出 JSON 本体且 dialogue 内的引号转义"),
            ("I-3", "引入固定 style_anchor 枚举短语，单次输出锁定"),
            ("I-4", "明示禁止改写剧情；敏感则 blocked_reason"),
        ]
        conn.execute("DELETE FROM prompt_change_mappings")
        conn.executemany(
            "INSERT INTO prompt_change_mappings (issue_key, change_summary) VALUES (?, ?)",
            mappings,
        )
        conn.commit()

    cur_ba = conn.execute("SELECT COUNT(*) AS c FROM before_after").fetchone()["c"]
    created_ba = 0
    if cur_ba < 2:
        row_fp = conn.execute("SELECT content FROM fixed_prompt WHERE id = 1").fetchone()
        fixed_txt = row_fp["content"] if row_fp else ""
        ba_samples = [
            ("自动·甜宠短路", demo_plots[0][1]),
            ("自动·悬疑短路", demo_plots[1][1]),
        ]
        for lab, plt in ba_samples:
            nba = conn.execute("SELECT COUNT(*) AS c FROM before_after").fetchone()["c"]
            if nba >= 2:
                break
            before_raw, bmodel, _ = await run_broken_prompt(plt, None)
            after_raw, amodel, _ = await run_fixed_prompt(plt, fixed_txt)
            conn.execute(
                """INSERT INTO before_after (label, plot, before_output, after_output, notes)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    lab,
                    plt,
                    before_raw,
                    after_raw,
                    f"before_model={bmodel}; after_model={amodel}; seed_auto",
                ),
            )
            created_ba += 1
        conn.commit()

    return {
        "created_runs": created_runs,
        "created_issues": created_issues,
        "created_before_after": created_ba,
    }


# Static frontend (vite build → ../frontend/dist)
_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(_DIST), html=True), name="static")
