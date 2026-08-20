import base64
import json
import mimetypes
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from core.db import get_engine

engine = get_engine()

FARMER_PHOTO_DIR = Path("uploads") / "farmers"


def _ensure_photo_columns():
    """Add persistent photo and reusable programme-context columns to an existing farmers table when needed.

    photo_data stores the image as base64 text so the same farmer photograph is
    available from PostgreSQL on every device/Render instance. Existing
    photo_path/photo_status columns are retained for backward compatibility.
    """
    try:
        with engine.begin() as conn:
            dialect = engine.dialect.name
            if dialect == "sqlite":
                columns = {row[1] for row in conn.execute(text("PRAGMA table_info(farmers)"))}
            else:
                columns = {
                    row[0]
                    for row in conn.execute(text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name='farmers'"
                    ))
                }

            if not columns:
                return
            if "photo_data" not in columns:
                conn.execute(text("ALTER TABLE farmers ADD COLUMN photo_data TEXT"))
            if "photo_mime" not in columns:
                conn.execute(text("ALTER TABLE farmers ADD COLUMN photo_mime TEXT"))
            if "support_needs" not in columns:
                conn.execute(text("ALTER TABLE farmers ADD COLUMN support_needs TEXT"))
            if "support_priority" not in columns:
                conn.execute(text("ALTER TABLE farmers ADD COLUMN support_priority TEXT"))
            if "programme_name" not in columns:
                conn.execute(text("ALTER TABLE farmers ADD COLUMN programme_name TEXT"))
    except Exception:
        # init_db() may not have created the table yet during first import.
        # fetch_farmers()/insert_farmer() call this again after table creation.
        pass


def _read_photo_as_base64(photo_path):
    raw = str(photo_path or "").strip()
    if not raw or raw.lower() == "nan":
        return "", ""

    path = Path(raw)
    if not path.is_file():
        # Handle Windows paths saved with backslashes on another platform.
        path = Path(raw.replace("\\", "/"))
    if not path.is_file():
        return "", ""

    data = path.read_bytes()
    if not data:
        return "", ""

    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    return base64.b64encode(data).decode("ascii"), mime


def _restore_photo_file(farmer_id, photo_path, photo_data, photo_mime):
    """Restore a missing local photo from the database and return its path."""
    raw_path = str(photo_path or "").strip()
    if raw_path and raw_path.lower() != "nan":
        candidate = Path(raw_path)
        if candidate.is_file() and candidate.stat().st_size > 0:
            return candidate.as_posix()
        normalized = Path(raw_path.replace("\\", "/"))
        if normalized.is_file() and normalized.stat().st_size > 0:
            return normalized.as_posix()

    encoded = str(photo_data or "").strip()
    if not encoded or encoded.lower() == "nan":
        return raw_path

    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except Exception:
        return raw_path
    if not image_bytes:
        return raw_path

    FARMER_PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    mime = str(photo_mime or "").lower()
    extension = {
        "image/png": ".png",
        "image/webp": ".webp",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
    }.get(mime, ".jpg")
    restored = FARMER_PHOTO_DIR / f"{farmer_id}{extension}"
    try:
        restored.write_bytes(image_bytes)
        return restored.as_posix()
    except Exception:
        return raw_path


def fetch_farmers():
    _ensure_photo_columns()
    df = pd.read_sql_query(text("SELECT * FROM farmers ORDER BY registration_date DESC"), engine)

    # Rehydrate photographs from PostgreSQL when Render/local disk does not have
    # the original upload. This keeps the existing app.py photo preview, QR
    # verification and ID-card generation code working unchanged.
    if not df.empty and "photo_data" in df.columns:
        restored_paths = []
        for _, row in df.iterrows():
            restored_paths.append(
                _restore_photo_file(
                    row.get("farmer_id", ""),
                    row.get("photo_path", ""),
                    row.get("photo_data", ""),
                    row.get("photo_mime", ""),
                )
            )
        if "photo_path" not in df.columns:
            df["photo_path"] = restored_paths
        else:
            df.loc[:, "photo_path"] = restored_paths
    return df


def farmer_exists_today(phone_number: str, nin: str, farmer_full_name: str) -> bool:
    today = datetime.now().strftime("%Y-%m-%d")
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT farmer_id FROM farmers
            WHERE phone_number=:phone AND nin=:nin
              AND LOWER(farmer_full_name)=LOWER(:name)
              AND SUBSTRING(registration_date,1,10)=:today
            LIMIT 1
        """), dict(phone=phone_number, nin=nin, name=farmer_full_name, today=today)).first()
    return row is not None


def insert_farmer(row: dict):
    _ensure_photo_columns()

    photo_data = row.get("Photo_Data", "")
    photo_mime = row.get("Photo_Mime", "")
    if not photo_data:
        photo_data, detected_mime = _read_photo_as_base64(row.get("Photo_Path", ""))
        if detected_mime:
            photo_mime = detected_mime

    enriched_row = dict(row)
    enriched_row["Photo_Data"] = photo_data
    enriched_row["Photo_Mime"] = photo_mime

    mapping = {
      "farmer_id":"Farmer_ID","registration_date":"Registration_Date","agent_id":"Agent_ID",
      "farmer_full_name":"Farmer_Full_Name","gender":"Gender","date_of_birth":"Date_of_Birth",
      "phone_number":"Phone_Number","alternate_phone":"Alternate_Phone","email_address":"Email_Address",
      "nin":"NIN","state":"State","lga":"LGA","ward":"Ward","community_village":"Community_Village",
      "residential_address":"Residential_Address","primary_crop":"Primary_Crop","secondary_crop":"Secondary_Crop",
      "farm_size_ha":"Farm_Size_Ha","support_needs":"Support_Needs","support_priority":"Support_Priority",
      "programme_name":"Programme_Name","input_distributed":"Input_Distributed","quantity_units":"Quantity_Units",
      "nin_status":"NIN_Status","id_type":"ID_Type","id_number":"ID_Number","latitude":"Latitude",
      "longitude":"Longitude","enumerator_remarks":"Enumerator_Remarks","photo_path":"Photo_Path",
      "photo_status":"Photo_Status","photo_data":"Photo_Data","photo_mime":"Photo_Mime"}
    params = {db: enriched_row.get(src) for db, src in mapping.items()}
    cols = ", ".join(mapping.keys())
    vals = ", ".join(f":{k}" for k in mapping)
    with engine.begin() as conn:
        conn.execute(text(f"INSERT INTO farmers ({cols}) VALUES ({vals})"), params)


def save_to_offline_queue(row: dict):
    with engine.begin() as conn:
        conn.execute(text("""INSERT INTO offline_queue
            (farmer_id,payload,sync_status,created_at,synced_at,error_message)
            VALUES (:farmer_id,:payload,'PENDING',:created_at,NULL,NULL)"""),
            dict(farmer_id=row["Farmer_ID"], payload=json.dumps(row), created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")))


def fetch_offline_queue():
    return pd.read_sql_query(text("SELECT * FROM offline_queue ORDER BY created_at DESC"), engine)


def sync_offline_queue():
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT id,payload FROM offline_queue WHERE sync_status IN ('PENDING','FAILED') ORDER BY created_at")).mappings().all()
    synced = failed = 0
    for item in rows:
        try:
            payload = json.loads(item['payload'])
            with engine.connect() as conn:
                exists = conn.execute(text("SELECT 1 FROM farmers WHERE farmer_id=:fid"), {'fid': payload['Farmer_ID']}).first()
            if not exists:
                insert_farmer(payload)
            with engine.begin() as conn:
                conn.execute(text("UPDATE offline_queue SET sync_status='SYNCED',synced_at=:t,error_message=NULL WHERE id=:id"), {'t': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'id': item['id']})
            synced += 1
        except Exception as exc:
            with engine.begin() as conn:
                conn.execute(text("UPDATE offline_queue SET sync_status='FAILED',error_message=:e WHERE id=:id"), {'e': str(exc)[:500], 'id': item['id']})
            failed += 1
    return synced, failed
