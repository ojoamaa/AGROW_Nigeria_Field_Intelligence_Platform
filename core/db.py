import sqlite3
from pathlib import Path
from core.config import APP_DATA_DIR

DB_PATH = APP_DATA_DIR / "agrow.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        pw TEXT,
        role TEXT,
        full_name TEXT,
        phone TEXT,
        nin TEXT,
        state TEXT,
        lga TEXT,
        email TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS farmers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        farmer_id TEXT,
        registration_date TEXT,
        agent_id TEXT,
        farmer_full_name TEXT,
        gender TEXT,
        date_of_birth TEXT,
        phone_number TEXT,
        alternate_phone TEXT,
        email_address TEXT,
        nin TEXT,
        state TEXT,
        lga TEXT,
        ward TEXT,
        community_village TEXT,
        residential_address TEXT,
        primary_crop TEXT,
        secondary_crop TEXT,
        farm_size_ha REAL,
        input_distributed TEXT,
        quantity_units INTEGER,
        nin_status TEXT,
        id_type TEXT,
        id_number TEXT,
        latitude REAL,
        longitude REAL,
        enumerator_remarks TEXT,
        photo_path TEXT,
        photo_status TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS offline_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        farmer_id TEXT,
        payload TEXT NOT NULL,
        sync_status TEXT DEFAULT 'PENDING',
        created_at TEXT,
        synced_at TEXT,
        error_message TEXT
    )
    """)

    # Seed default admin user
cursor.execute("SELECT * FROM users WHERE id = 'admin'")
admin_exists = cursor.fetchone()

if not admin_exists:
    cursor.execute("""
    INSERT INTO users (id, pw, role, full_name, phone, nin, state, lga, email)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "admin",
        "agrow2026",
        "admin",
        "System Admin",
        "00000000000",
        "00000000000",
        "FCT",
        "Abuja",
        "admin@datadev.com"
    ))
    # Backward-safe column patch
    try:
        cursor.execute("ALTER TABLE farmers ADD COLUMN photo_path TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE farmers ADD COLUMN photo_status TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()