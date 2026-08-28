"""SQLite 연결, 스키마, 계정 비밀번호 해시."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src.config import USERS, primary_role

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "yi_factory.db"


def resolve_db_path() -> Path:
    """사내 서버는 YI_FACTORY_DATA_DIR 로 저장 위치를 바꿀 수 있다. 테스트는 DB_PATH를 직접 바꾼다."""
    override = os.environ.get("YI_FACTORY_DATA_DIR", "").strip()
    if override:
        return Path(override) / "yi_factory.db"
    return DB_PATH


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    path = resolve_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {str(row["name"]) for row in rows}


def _ensure_users_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            role TEXT,
            team TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )
    cols = _columns(conn, "users")
    if "display_name" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN display_name TEXT")
    if "role" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN role TEXT")
    if "team" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN team TEXT")


def _ensure_survey_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS surveys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            period_start TEXT NOT NULL,
            period_end TEXT NOT NULL,
            deadline_at TEXT NOT NULL,
            is_published INTEGER NOT NULL DEFAULT 0,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            kind TEXT NOT NULL DEFAULT 'overtime',
            schema_json TEXT,
            FOREIGN KEY (created_by) REFERENCES users(username)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            survey_id INTEGER NOT NULL,
            team TEXT NOT NULL,
            seq_no INTEGER,
            rank TEXT,
            name TEXT NOT NULL,
            work_date TEXT NOT NULL,
            work_hours REAL NOT NULL DEFAULT 0,
            meal_count REAL,
            note TEXT,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (survey_id) REFERENCES surveys(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS submissions (
            survey_id INTEGER NOT NULL,
            team TEXT NOT NULL,
            is_submitted INTEGER NOT NULL DEFAULT 0,
            submitted_at TEXT,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (survey_id, team),
            FOREIGN KEY (survey_id) REFERENCES surveys(id)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_entries_survey_team ON entries (survey_id, team)"
    )
    entry_cols = _columns(conn, "entries")
    if "company" not in entry_cols:
        conn.execute("ALTER TABLE entries ADD COLUMN company TEXT")
    if "employment_type" not in entry_cols:
        conn.execute("ALTER TABLE entries ADD COLUMN employment_type TEXT")
    if "is_manual" not in entry_cols:
        conn.execute("ALTER TABLE entries ADD COLUMN is_manual INTEGER NOT NULL DEFAULT 0")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company TEXT NOT NULL,
            team TEXT NOT NULL,
            employment_type TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_employees_team ON employees (team, name)"
    )

    survey_cols = _columns(conn, "surveys")
    if "kind" not in survey_cols:
        conn.execute("ALTER TABLE surveys ADD COLUMN kind TEXT NOT NULL DEFAULT 'overtime'")
    if "schema_json" not in survey_cols:
        conn.execute("ALTER TABLE surveys ADD COLUMN schema_json TEXT")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            survey_id INTEGER NOT NULL,
            team TEXT NOT NULL,
            seq_no INTEGER,
            payload_json TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (survey_id) REFERENCES surveys(id)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_responses_survey_team ON responses (survey_id, team)"
    )


def sync_user_profiles(conn: sqlite3.Connection | None = None) -> None:
    own_conn = conn is None
    if own_conn:
        conn = get_connection()
    assert conn is not None
    try:
        for username, meta in USERS.items():
            conn.execute(
                """
                UPDATE users
                SET display_name = ?, role = ?, team = ?
                WHERE username = ?
                """,
                (
                    meta["display_name"],
                    primary_role(username),
                    meta["team"],
                    username,
                ),
            )
        if own_conn:
            conn.commit()
    finally:
        if own_conn:
            conn.close()


def init_db() -> None:
    conn = get_connection()
    try:
        _ensure_users_table(conn)
        _ensure_survey_tables(conn)
        sync_user_profiles(conn)
        conn.commit()
    finally:
        conn.close()


def _profile_for(username: str) -> tuple[str, str, str | None]:
    meta = USERS.get(username)
    if meta is None:
        return username, "team", None
    return str(meta["display_name"]), primary_role(username), meta["team"]


def get_password_hash(username: str) -> str | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return None if row is None else str(row["password_hash"])
    finally:
        conn.close()


def upsert_password_hash(username: str, password_hash: str) -> None:
    display_name, role, team = _profile_for(username)
    now = _now()
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO users (username, password_hash, display_name, role, team, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                password_hash = excluded.password_hash,
                display_name = excluded.display_name,
                role = excluded.role,
                team = excluded.team,
                updated_at = excluded.updated_at
            """,
            (username, password_hash, display_name, role, team, now),
        )
        conn.commit()
    finally:
        conn.close()
