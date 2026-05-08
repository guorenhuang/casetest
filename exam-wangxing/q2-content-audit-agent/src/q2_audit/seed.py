"""Load rules YAML into SQLite (idempotent upsert)."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import yaml

from q2_audit.db import get_db_path, init_db, upsert_rule


def load_yaml(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    return yaml.safe_load(raw) or {}


def seed_from_yaml(conn: sqlite3.Connection, yaml_path: Path) -> int:
    data = load_yaml(yaml_path)
    rules = data.get("rules") or []
    n = 0
    for r in rules:
        rid = str(r["id"])
        upsert_rule(
            conn,
            rule_id=rid,
            kind=str(r.get("kind", "regex")),
            action=str(r.get("action", "review")),
            priority=int(r.get("priority", 100)),
            description=str(r.get("description", "")),
            enabled=bool(r.get("enabled", True)),
            config=dict(r.get("config") or {}),
        )
        n += 1
    return n


def ensure_seeded(sqlite_path: Path | None = None, yaml_rel: str = "rules.yaml") -> None:
    root = Path(__file__).resolve().parents[2]
    dbp = sqlite_path or get_db_path(root)
    dbp.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(dbp))
    try:
        init_db(conn)
        yml = root / yaml_rel
        if yml.exists():
            n = fetch_rule_count(conn)
            if n == 0:
                seed_from_yaml(conn, yml)
    finally:
        conn.close()


def fetch_rule_count(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(1) AS c FROM audit_rules").fetchone()
    return int(row[0]) if row else 0
