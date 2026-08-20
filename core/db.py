import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from core.config import APP_DATA_DIR

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
    DB_BACKEND = "postgresql"
else:
    db_path = APP_DATA_DIR / "agrow.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False, "timeout": 10},
        future=True,
    )
    DB_BACKEND = "sqlite"

def get_engine():
    return engine

def get_connection():
    return engine.connect()

def init_db():
    id_column = "INTEGER PRIMARY KEY AUTOINCREMENT" if DB_BACKEND == "sqlite" else "BIGSERIAL PRIMARY KEY"
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY, pw TEXT, role TEXT, full_name TEXT, phone TEXT,
            nin TEXT, state TEXT, lga TEXT, email TEXT
        )
        """))
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS farmers (
            id {id_column}, farmer_id TEXT UNIQUE, registration_date TEXT, agent_id TEXT,
            farmer_full_name TEXT, gender TEXT, date_of_birth TEXT, phone_number TEXT,
            alternate_phone TEXT, email_address TEXT, nin TEXT, state TEXT, lga TEXT,
            ward TEXT, community_village TEXT, residential_address TEXT, primary_crop TEXT,
            secondary_crop TEXT, farm_size_ha REAL, support_needs TEXT, support_priority TEXT,
            programme_name TEXT, input_distributed TEXT, quantity_units INTEGER,
            nin_status TEXT, id_type TEXT, id_number TEXT, latitude REAL, longitude REAL,
            enumerator_remarks TEXT, photo_path TEXT, photo_status TEXT
        )
        """))
        # Backward-compatible farmer profile extensions for reusable programme support needs.
        if DB_BACKEND == "sqlite":
            farmer_columns = {row[1] for row in conn.execute(text("PRAGMA table_info(farmers)"))}
        else:
            farmer_columns = {row[0] for row in conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='farmers'"
            ))}
        for column_name in ("support_needs", "support_priority", "programme_name"):
            if column_name not in farmer_columns:
                conn.execute(text(f"ALTER TABLE farmers ADD COLUMN {column_name} TEXT"))

        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS offline_queue (
            id {id_column}, farmer_id TEXT, payload TEXT NOT NULL, sync_status TEXT DEFAULT 'PENDING',
            created_at TEXT, synced_at TEXT, error_message TEXT
        )
        """))
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id {id_column}, username TEXT, action TEXT, details TEXT, timestamp TEXT
        )
        """))
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS programme_interventions (
            id {id_column}, intervention_id TEXT UNIQUE, farmer_id TEXT NOT NULL,
            programme_name TEXT, intervention_type TEXT, support_items TEXT, quantity REAL,
            unit TEXT, intervention_date TEXT, status TEXT DEFAULT 'Delivered', agent_id TEXT,
            remarks TEXT, created_at TEXT
        )
        """))
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS market_listings (
            id {id_column}, farmer_id TEXT NOT NULL, commodity TEXT NOT NULL, product TEXT NOT NULL,
            quantity REAL NOT NULL, available_quantity REAL NOT NULL, unit TEXT NOT NULL, price REAL NOT NULL,
            ready_date TEXT, state TEXT, lga TEXT, community TEXT, description TEXT,
            status TEXT DEFAULT 'AVAILABLE', created_by TEXT, created_at TEXT, updated_at TEXT
        )
        """))
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS input_products (
            id {id_column}, supplier_name TEXT NOT NULL, supplier_phone TEXT, category TEXT NOT NULL,
            product_name TEXT NOT NULL, applicable_commodities TEXT, quantity REAL, unit TEXT, price REAL,
            state TEXT, lga TEXT, description TEXT, status TEXT DEFAULT 'AVAILABLE',
            created_by TEXT, created_at TEXT, updated_at TEXT
        )
        """))
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS market_enquiries (
            id {id_column}, listing_id BIGINT NOT NULL, buyer_name TEXT NOT NULL, buyer_phone TEXT NOT NULL,
            quantity_requested REAL, message TEXT, status TEXT DEFAULT 'NEW', created_at TEXT
        )
        """))
        existing = conn.execute(text("SELECT id FROM users WHERE UPPER(id)='ADMIN'")).first()
        if not existing:
            conn.execute(text("""
                INSERT INTO users (id,pw,role,full_name,phone,nin,state,lga,email)
                VALUES (:id,:pw,:role,:full_name,:phone,:nin,:state,:lga,:email)
            """), dict(id="ADMIN", pw="agrow2026", role="admin", full_name="System Admin",
                       phone="00000000000", nin="00000000000", state="FCT", lga="Abuja",
                       email="admin@datadev.com"))
