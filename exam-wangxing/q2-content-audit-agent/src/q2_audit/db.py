"""SQLite persistence for editable rules."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS audit_rules (
  id TEXT PRIMARY KEY NOT NULL,
  kind TEXT NOT NULL,
  action TEXT NOT NULL CHECK (action IN ('block', 'review')),
  priority INTEGER NOT NULL DEFAULT 100,
  description TEXT DEFAULT '',
  enabled INTEGER NOT NULL DEFAULT 1,
  config TEXT NOT NULL DEFAULT '{}',
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_rules_enabled_priority ON audit_rules (enabled, priority);
"""


def get_db_path(base: Path | None = None) -> Path:
    root = base or Path(__file__).resolve().parents[2]
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "audit.db"


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or get_db_path()
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def fetch_enabled_rules(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    cur = conn.execute(
        """
        SELECT id, kind, action, priority, description, enabled, config
        FROM audit_rules
        WHERE enabled = 1
        ORDER BY priority ASC, id ASC
        """
    )
    rows: list[dict[str, Any]] = []
    for r in cur.fetchall():
        rows.append(
            {
                "id": r["id"],
                "kind": r["kind"],
                "action": r["action"],
                "priority": int(r["priority"]),
                "description": r["description"],
                "enabled": bool(r["enabled"]),
                "config": json.loads(r["config"] or "{}"),
            }
        )
    return rows


def upsert_rule(
    conn: sqlite3.Connection,
    rule_id: str,
    kind: str,
    action: str,
    priority: int,
    description: str,
    enabled: bool,
    config: dict[str, Any],
) -> None:
    conn.execute(
        """
        INSERT INTO audit_rules (id, kind, action, priority, description, enabled, config, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(id) DO UPDATE SET
          kind = excluded.kind,
          action = excluded.action,
          priority = excluded.priority,
          description = excluded.description,
          enabled = excluded.enabled,
          config = excluded.config,
          updated_at = excluded.updated_at
        """,
        (
            rule_id,
            kind,
            action,
            priority,
            description,
            1 if enabled else 0,
            json.dumps(config, ensure_ascii=False),
        ),
    )
    conn.commit()


def delete_rule(conn: sqlite3.Connection, rule_id: str) -> bool:
    cur = conn.execute("DELETE FROM audit_rules WHERE id = ?", (rule_id,))
    conn.commit()
    return cur.rowcount > 0
