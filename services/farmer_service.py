import json
from datetime import datetime
import pandas as pd
from sqlalchemy import text
from core.db import get_engine

engine = get_engine()

def fetch_farmers():
    return pd.read_sql_query(text("SELECT * FROM farmers ORDER BY registration_date DESC"), engine)

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
    mapping = {
      "farmer_id":"Farmer_ID","registration_date":"Registration_Date","agent_id":"Agent_ID",
      "farmer_full_name":"Farmer_Full_Name","gender":"Gender","date_of_birth":"Date_of_Birth",
      "phone_number":"Phone_Number","alternate_phone":"Alternate_Phone","email_address":"Email_Address",
      "nin":"NIN","state":"State","lga":"LGA","ward":"Ward","community_village":"Community_Village",
      "residential_address":"Residential_Address","primary_crop":"Primary_Crop","secondary_crop":"Secondary_Crop",
      "farm_size_ha":"Farm_Size_Ha","input_distributed":"Input_Distributed","quantity_units":"Quantity_Units",
      "nin_status":"NIN_Status","id_type":"ID_Type","id_number":"ID_Number","latitude":"Latitude",
      "longitude":"Longitude","enumerator_remarks":"Enumerator_Remarks","photo_path":"Photo_Path",
      "photo_status":"Photo_Status"}
    params={db: row.get(src) for db,src in mapping.items()}
    cols=", ".join(mapping.keys()); vals=", ".join(f":{k}" for k in mapping)
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
        rows=conn.execute(text("SELECT id,payload FROM offline_queue WHERE sync_status IN ('PENDING','FAILED') ORDER BY created_at")).mappings().all()
    synced=failed=0
    for item in rows:
        try:
            payload=json.loads(item['payload'])
            with engine.connect() as conn:
                exists=conn.execute(text("SELECT 1 FROM farmers WHERE farmer_id=:fid"), {'fid':payload['Farmer_ID']}).first()
            if not exists: insert_farmer(payload)
            with engine.begin() as conn:
                conn.execute(text("UPDATE offline_queue SET sync_status='SYNCED',synced_at=:t,error_message=NULL WHERE id=:id"), {'t':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'id':item['id']})
            synced+=1
        except Exception as exc:
            with engine.begin() as conn:
                conn.execute(text("UPDATE offline_queue SET sync_status='FAILED',error_message=:e WHERE id=:id"), {'e':str(exc)[:500],'id':item['id']})
            failed+=1
    return synced, failed
