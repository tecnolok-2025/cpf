import os
import sqlite3
from pathlib import Path
from datetime import datetime

APP_NAME = "CPF"


def _data_dir() -> Path:
    # Directorio escribible (evita fallas cuando corre como .exe onefile)
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    d = base / APP_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


DB_PATH = _data_dir() / "cpf.db"


def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    c = conn()
    cur = c.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chambers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            province TEXT,
            city TEXT,
            created_at TEXT NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            company TEXT NOT NULL,
            phone TEXT,
            chamber_id INTEGER,
            role TEXT NOT NULL, -- admin | chamber_admin | user
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY(chamber_id) REFERENCES chambers(id)
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS requirements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            chamber_id INTEGER,
            req_type TEXT NOT NULL, -- offer | need
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            tags TEXT,
            category TEXT,
            location TEXT,
            urgency TEXT,
            status TEXT NOT NULL DEFAULT 'open', -- open | closed
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(chamber_id) REFERENCES chambers(id)
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS contact_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id INTEGER NOT NULL,
            to_user_id INTEGER NOT NULL,
            requirement_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending', -- pending | accepted | declined
            created_at TEXT NOT NULL,
            responded_at TEXT,
            FOREIGN KEY(from_user_id) REFERENCES users(id),
            FOREIGN KEY(to_user_id) REFERENCES users(id),
            FOREIGN KEY(requirement_id) REFERENCES requirements(id)
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor_user_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            created_at TEXT NOT NULL
        );
    """)
    c.commit()
    c.close()


def now_iso():
    return datetime.utcnow().isoformat(timespec="seconds")


def log(actor_user_id, action, details=""):
    c = conn()
    c.execute(
        "INSERT INTO audit_log(actor_user_id, action, details, created_at) VALUES(?,?,?,?)",
        (actor_user_id, action, details, now_iso())
    )
    c.commit()
    c.close()
