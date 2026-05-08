from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from q2_audit.auditor import AuditItemIn, audit_batch
from q2_audit.db import connect, delete_rule, fetch_enabled_rules, get_db_path, init_db, upsert_rule
from q2_audit.seed import ensure_seeded

ROOT = Path(__file__).resolve().parents[2]


class CommentDTO(BaseModel):
    id: str = Field(..., description="Stable id within batch")
    text: str
    image_urls: list[str] = Field(default_factory=list)


class AuditRequest(BaseModel):
    comments: list[CommentDTO]
    use_llm: bool = True
    llm_timeout_ms: float = 800.0


class RuleDTO(BaseModel):
    id: str
    kind: str
    action: str
    priority: int = 100
    description: str = ""
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


def create_app() -> FastAPI:
    ensure_seeded(None, yaml_rel="rules.yaml")

    app = FastAPI(title="Q2 Comment Audit Agent", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:4173",
            "http://localhost:4173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    db_path = get_db_path(ROOT)

    def _conn():
        c = connect(db_path)
        init_db(c)
        return c

    @app.get("/api/health")
    def health():
        return {"ok": True, "db": str(db_path)}

    @app.post("/api/audit")
    def audit(body: AuditRequest):
        conn = _conn()
        try:
            rules = fetch_enabled_rules(conn)
        finally:
            conn.close()
        items = [
            AuditItemIn(id=c.id, text=c.text, image_urls=c.image_urls) for c in body.comments
        ]
        outs = audit_batch(
            items,
            rules,
            use_llm=body.use_llm,
            llm_timeout_ms=body.llm_timeout_ms,
        )
        return {
            "results": [
                {
                    "id": o.id,
                    "verdict": o.verdict,
                    "reasons": [
                        {"type": r.type, "id": r.id, "detail": r.detail} for r in o.reasons
                    ],
                    "combined_text_sample": o.combined_text_sample,
                }
                for o in outs
            ]
        }

    @app.get("/api/rules")
    def list_rules():
        conn = _conn()
        try:
            cur = conn.execute(
                """
                SELECT id, kind, action, priority, description, enabled, config
                FROM audit_rules
                ORDER BY priority ASC, id ASC
                """
            )
            rows = []
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
        finally:
            conn.close()

    @app.post("/api/rules")
    def create_rule(rule: RuleDTO):
        conn = _conn()
        try:
            upsert_rule(
                conn,
                rule.id,
                rule.kind,
                rule.action,
                rule.priority,
                rule.description,
                rule.enabled,
                rule.config,
            )
            return {"ok": True, "id": rule.id}
        finally:
            conn.close()

    @app.put("/api/rules/{rule_id}")
    def update_rule(rule_id: str, rule: RuleDTO):
        if rule.id != rule_id:
            raise HTTPException(400, "id mismatch")
        conn = _conn()
        try:
            upsert_rule(
                conn,
                rule.id,
                rule.kind,
                rule.action,
                rule.priority,
                rule.description,
                rule.enabled,
                rule.config,
            )
            return {"ok": True}
        finally:
            conn.close()

    @app.delete("/api/rules/{rule_id}")
    def remove_rule(rule_id: str):
        conn = _conn()
        try:
            ok = delete_rule(conn, rule_id)
            if not ok:
                raise HTTPException(404, "not found")
            return {"ok": True}
        finally:
            conn.close()

    @app.post("/api/rules/reimport-yaml")
    def reimport_yaml():
        """Dev helper: re-read rules.yaml into DB (upsert all)."""
        from q2_audit.seed import seed_from_yaml

        yml = ROOT / "rules.yaml"
        if not yml.exists():
            raise HTTPException(400, "rules.yaml missing")
        conn = _conn()
        try:
            n = seed_from_yaml(conn, yml)
            return {"ok": True, "upserted": n}
        finally:
            conn.close()

    static_dir = ROOT / "frontend" / "dist"
    if static_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app


app = create_app()
