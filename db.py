
import sqlite3
import json
import datetime
from constants import DB_PATH


def _get_columns(conn):
    rows = conn.execute("PRAGMA table_info(sessions)").fetchall()
    return {row[1] for row in rows}


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            ts                  TEXT,
            argument            TEXT,
            mode                TEXT,
            base_intensity      INTEGER,
            effective_intensity REAL,
            strength_score      INTEGER,
            fallacy_count       INTEGER,
            fallacy_types       TEXT,
            session_tag         TEXT,
            counterargument     TEXT,
            flaws               TEXT,
            facts               TEXT,
            points              INTEGER DEFAULT 0
        )
    """)
    columns = _get_columns(conn)
    if "points" not in columns:
        conn.execute("ALTER TABLE sessions ADD COLUMN points INTEGER DEFAULT 0")
    conn.commit()
    conn.close()

def save_session(d):
    conn = sqlite3.connect(DB_PATH)
    columns = _get_columns(conn)
    has_points = "points" in columns
    points_value = int(d.get("points", 0)) if has_points else None
    if has_points:
        conn.execute("""
            INSERT INTO sessions
            (ts,argument,mode,base_intensity,effective_intensity,
             strength_score,fallacy_count,fallacy_types,session_tag,
             counterargument,flaws,facts,points)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            datetime.datetime.now().isoformat(),
            d.get("argument",""), d.get("mode",""),
            d.get("base_intensity",3), d.get("effective_intensity",3.0),
            d.get("strength_score",0), d.get("fallacy_count",0),
            json.dumps(d.get("fallacy_types",[])),
            d.get("session_tag",""),
            d.get("counterargument",""),
            json.dumps(d.get("flaws",[])),
            json.dumps(d.get("facts",[])),
            points_value,
        ))
    else:
        conn.execute("""
            INSERT INTO sessions
            (ts,argument,mode,base_intensity,effective_intensity,
             strength_score,fallacy_count,fallacy_types,session_tag,
             counterargument,flaws,facts)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            datetime.datetime.now().isoformat(),
            d.get("argument",""), d.get("mode",""),
            d.get("base_intensity",3), d.get("effective_intensity",3.0),
            d.get("strength_score",0), d.get("fallacy_count",0),
            json.dumps(d.get("fallacy_types",[])),
            d.get("session_tag",""),
            d.get("counterargument",""),
            json.dumps(d.get("flaws",[])),
            json.dumps(d.get("facts",[])),
        ))
    conn.commit()
    conn.close()

def load_sessions(n=20):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT * FROM sessions ORDER BY id DESC LIMIT ?", (n,)
    ).fetchall()
    conn.close()
    cols = ["id","ts","argument","mode","base_intensity","effective_intensity",
            "strength_score","fallacy_count","fallacy_types","session_tag",
            "counterargument","flaws","facts","points"]
    return [dict(zip(cols, r)) for r in rows]
