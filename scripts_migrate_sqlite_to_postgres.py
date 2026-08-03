"""One-time migration from local agrow.db to DATABASE_URL PostgreSQL.
Run only after setting DATABASE_URL and backing up agrow.db.
"""
import os, sqlite3
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("DATABASE_URL", "").strip()
if not url:
    raise SystemExit("DATABASE_URL is required.")
if url.startswith("postgres://"):
    url = "postgresql+psycopg2://" + url[len("postgres://"):]
elif url.startswith("postgresql://"):
    url = "postgresql+psycopg2://" + url[len("postgresql://"):]

sqlite_path = Path(os.getenv("SQLITE_SOURCE_PATH", "agrow.db"))
if not sqlite_path.exists():
    raise SystemExit(f"SQLite source not found: {sqlite_path}")

from core.db import init_db
init_db()
engine = create_engine(url, pool_pre_ping=True)
src = sqlite3.connect(sqlite_path)
src.row_factory = sqlite3.Row

for table in ("users", "farmers", "offline_queue", "audit_logs"):
    try:
        rows = [dict(r) for r in src.execute(f"SELECT * FROM {table}").fetchall()]
    except sqlite3.OperationalError:
        rows = []
    if not rows:
        print(f"{table}: no rows")
        continue
    with engine.begin() as dest:
        for row in rows:
            row.pop("id", None) if table in ("farmers", "offline_queue", "audit_logs") else None
            columns = list(row)
            col_sql = ", ".join(columns)
            val_sql = ", ".join(f":{c}" for c in columns)
            conflict = " ON CONFLICT DO NOTHING" if table in ("users", "farmers") else ""
            dest.execute(text(f"INSERT INTO {table} ({col_sql}) VALUES ({val_sql}){conflict}"), row)
    print(f"{table}: migrated {len(rows)} row(s)")

src.close()
print("Migration complete.")
