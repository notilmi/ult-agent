import os
from pathlib import Path
import psycopg
from src.config import NEON_DATABASE_URL

def get_connection_string() -> str:
    """Returns normalized SQLAlchemy/psycopg connection URL for NeonDB."""
    url = NEON_DATABASE_URL
    if not url:
        return ""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+psycopg://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url

def get_raw_psycopg_url() -> str:
    """Returns standard libpq postgresql connection URL for psycopg direct connection."""
    url = NEON_DATABASE_URL
    if not url:
        return ""
    if url.startswith("postgresql+psycopg://"):
        url = url.replace("postgresql+psycopg://", "postgresql://", 1)
    return url

def execute_init_sql():
    """Executes init_db.sql on the target NeonDB instance to ensure tables and indexes exist."""
    url = get_raw_psycopg_url()
    if not url:
        print("[WARN] NEON_DATABASE_URL is not set. Skipping DB initialization.")
        return False

    sql_path = Path(__file__).resolve().parent.parent.parent / "scripts" / "init_db.sql"
    if not sql_path.exists():
        print(f"[ERROR] SQL file not found at {sql_path}")
        return False

    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()

    try:
        with psycopg.connect(url) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        print("[INFO] NeonDB schema initialized successfully.")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to execute init_db.sql: {e}")
        return False

if __name__ == "__main__":
    execute_init_sql()
