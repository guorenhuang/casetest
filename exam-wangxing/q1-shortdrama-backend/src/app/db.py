"""SQLite 连接与初始化。"""
import os
import sqlite3
from pathlib import Path
from typing import Generator


def get_connection() -> sqlite3.Connection:
    path_str = os.environ.get("DATABASE_PATH", "./data/app.db")
    path = Path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    schema = Path(__file__).resolve().parent.parent.parent / "schema.sql"
    sql = schema.read_text(encoding="utf-8")
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    schema = Path(__file__).resolve().parent.parent.parent / "schema.sql"
    sql = schema.read_text(encoding="utf-8")
    conn = get_connection()
    try:
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()


def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
