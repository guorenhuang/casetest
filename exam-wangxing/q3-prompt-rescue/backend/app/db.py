"""SQLite access and schema init."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

_env_sqlite = os.environ.get("Q3_SQLITE_PATH", "").strip()
DB_PATH = (
    Path(_env_sqlite).expanduser().resolve()
    if _env_sqlite
    else Path(__file__).resolve().parent.parent / "data" / "q3_workbench.db"
)


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS observation_runs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              plot TEXT NOT NULL,
              topic TEXT,
              raw_output TEXT NOT NULL,
              model_name TEXT,
              used_real_llm INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS issues (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              issue_key TEXT NOT NULL UNIQUE,
              title TEXT,
              phenomenon TEXT NOT NULL,
              evidence TEXT NOT NULL,
              why_problem TEXT NOT NULL,
              sort_order INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS transcript_messages (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              role TEXT NOT NULL,
              content TEXT NOT NULL,
              strategy_note INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS fixed_prompt (
              id INTEGER PRIMARY KEY CHECK (id = 1),
              content TEXT NOT NULL,
              updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS prompt_change_mappings (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              issue_key TEXT NOT NULL,
              change_summary TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS before_after (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              label TEXT,
              plot TEXT NOT NULL,
              before_output TEXT NOT NULL,
              after_output TEXT NOT NULL,
              notes TEXT,
              created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        cur = conn.execute("SELECT COUNT(*) AS c FROM fixed_prompt WHERE id = 1")
        if cur.fetchone()["c"] == 0:
            conn.execute(
                """INSERT INTO fixed_prompt (id, content) VALUES (1, ?)""",
                (_default_fixed_prompt(),),
            )
        conn.commit()
    finally:
        conn.close()


def _default_fixed_prompt() -> str:
    return """你是短剧分镜生成器。必须严格遵守用户剧情，不得改人设、时间线、结局走向；仅做分镜层面的镜头与节奏拆解。

输出：仅输出一个 UTF-8 JSON 对象（不要 markdown 代码块、不要前后解释文字）。
JSON Schema（字段名固定，顺序不限）：
{
  "style_anchor": "string，固定短语，例如 冷色调悬疑·快切",
  "shots": [
    {
      "idx": "integer，从 1 递增",
      "duration_s": "number，<=8，单镜头时长上限",
      "scene": "string，一句场景",
      "action": "string，演员动作",
      "camera": "string，机位/运镜",
      "dialogue": "string，台词或空字符串"
    }
  ]
}

硬性约束：
- shots 数组长度 ≤ 12；每条字段单行短句，禁止长篇文学描写。
- dialogue 内双引号必须转义为 \\"；禁止输出未转义的裸换行。
- 若剧情敏感或不合规：保留用户设定不动，用 shots 为空数组并在顶层增加 "blocked_reason": "string"。

剧情：
{plot}"""
