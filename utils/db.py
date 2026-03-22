import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "subjects.db")

def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def get_credit(subject_code: str) -> int | None:
    with _conn() as con:
        row = con.execute(
            "SELECT credits FROM subjects WHERE code=?", (subject_code.upper(),)
        ).fetchone()
    return row[0] if row else None

def save_credit(subject_code: str, credits: int):
    with _conn() as con:
        con.execute(
            "CREATE TABLE IF NOT EXISTS subjects (code TEXT PRIMARY KEY, credits INTEGER)"
        )
        con.execute(
            "INSERT OR REPLACE INTO subjects (code, credits) VALUES (?,?)",
            (subject_code.upper(), credits),
        )

def all_subjects() -> dict:
    with _conn() as con:
        con.execute(
            "CREATE TABLE IF NOT EXISTS subjects (code TEXT PRIMARY KEY, credits INTEGER)"
        )
        rows = con.execute("SELECT code, credits FROM subjects ORDER BY code").fetchall()
    return {r[0]: r[1] for r in rows}
