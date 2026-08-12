import base64, hashlib, hmac, json, os, time
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import text

from core.db import get_engine, init_db
from services.farmer_service import insert_farmer
from services.user_service import fetch_user

init_db()
app = FastAPI(title='AGROW Field Sync API', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
STATIC = Path(__file__).parent / 'agrow_field' / 'static'
SECRET = os.getenv('FIELD_API_SECRET', os.getenv('QR_SECRET_KEY', 'change-this-field-secret'))

COUNTRY_GPS_ENVELOPES = {
    'Nigeria': (4.0, 14.0, 2.5, 15.0), 'Ghana': (4.5, 11.5, -3.5, 1.5), 'Kenya': (-5.0, 5.5, 33.5, 42.5),
}
NIGERIA_STATE_ENVELOPES = {
    'Abia': (4.6,6.1,7.0,8.3),'Adamawa':(7.0,11.0,11.2,14.0),'Akwa Ibom':(4.3,5.6,7.4,8.7),'Anambra':(5.6,6.8,6.5,7.6),'Bauchi':(9.0,12.6,8.5,12.0),'Bayelsa':(4.0,5.5,5.5,6.8),'Benue':(6.4,8.3,7.5,10.2),'Borno':(10.0,14.2,11.5,14.8),'Cross River':(4.3,7.1,7.6,9.6),'Delta':(5.0,6.5,5.0,6.8),'Ebonyi':(5.5,6.9,7.4,8.5),'Edo':(5.6,7.6,5.0,6.9),'Ekiti':(7.2,8.1,4.8,5.9),'Enugu':(5.9,7.0,6.8,7.9),'FCT':(8.2,9.4,6.6,7.8),'Gombe':(9.5,11.5,10.5,12.0),'Imo':(5.0,5.9,6.6,7.5),'Jigawa':(10.5,13.2,8.0,10.7),'Kaduna':(9.0,11.8,6.0,9.0),'Kano':(10.4,12.7,7.5,9.7),'Katsina':(11.0,13.4,6.8,9.3),'Kebbi':(10.0,13.3,3.5,6.8),'Kogi':(6.5,8.5,5.3,7.9),'Kwara':(7.5,10.0,2.7,6.2),'Lagos':(6.2,6.8,2.6,4.5),'Nasarawa':(7.0,9.5,7.5,9.7),'Niger':(8.0,11.0,3.0,7.8),'Ogun':(6.2,7.9,2.6,4.8),'Ondo':(5.7,7.8,4.3,6.2),'Osun':(6.8,8.2,4.0,5.2),'Oyo':(7.0,9.0,2.7,4.7),'Plateau':(8.3,10.7,8.2,10.7),'Rivers':(4.3,5.8,6.2,7.7),'Sokoto':(11.5,13.8,4.0,7.2),'Taraba':(6.4,9.8,9.0,12.2),'Yobe':(10.5,13.4,9.5,13.0),'Zamfara':(10.5,13.2,5.5,7.7),
}

def territory_bounds(country, region):
    raw=os.getenv('AGROW_TERRITORY_BOUNDS_JSON','').strip()
    if raw:
        try:
            v=json.loads(raw).get(f'{country}|{region}')
            if isinstance(v,list) and len(v)==4: return tuple(map(float,v))
        except Exception: pass
    if country.lower()=='nigeria': return NIGERIA_STATE_ENVELOPES.get(region)
    return None

def validate_territory(country, region, lat, lon):
    cb=COUNTRY_GPS_ENVELOPES.get(country)
    if cb and not (cb[0] <= lat <= cb[1] and cb[2] <= lon <= cb[3]): return False
    rb=territory_bounds(country, region)
    if rb is None: return None
    return rb[0] <= lat <= rb[1] and rb[2] <= lon <= rb[3]

def make_token(agent_id):
    exp=int(time.time())+60*60*24*30
    payload=f'{agent_id}|{exp}'
    sig=hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f'{payload}|{sig}'.encode()).decode()

def auth(authorization: Optional[str]):
    if not authorization or not authorization.startswith('Bearer '): raise HTTPException(401,'Missing token')
    try:
        raw=base64.urlsafe_b64decode(authorization[7:].encode()).decode(); agent, exp, sig=raw.split('|',2)
        payload=f'{agent}|{exp}'; expected=hmac.new(SECRET.encode(),payload.encode(),hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig,expected) or int(exp)<time.time(): raise ValueError()
        return agent
    except Exception: raise HTTPException(401,'Invalid or expired token')

def ensure_sync_receipts_table():
    """Server-side audit trail for Field-device synchronization.

    Device-local PENDING records are intentionally invisible to the central
    AGROW server until the device reconnects. Once a sync attempt reaches this
    API, the receipt is recorded here for central monitoring.
    """
    engine = get_engine()
    id_column = "INTEGER PRIMARY KEY AUTOINCREMENT" if engine.dialect.name == "sqlite" else "BIGSERIAL PRIMARY KEY"
    ddl = f"""
    CREATE TABLE IF NOT EXISTS field_sync_receipts (
        id {id_column},
        farmer_id TEXT NOT NULL,
        agent_id TEXT NOT NULL,
        sync_status TEXT NOT NULL,
        received_at TEXT NOT NULL,
        error_message TEXT
    )
    """
    with engine.begin() as conn:
        conn.execute(text(ddl))


def record_sync_receipt(farmer_id: str, agent_id: str, status: str, error: str = ""):
    ensure_sync_receipts_table()
    with get_engine().begin() as conn:
        conn.execute(
            text("""
                INSERT INTO field_sync_receipts
                    (farmer_id, agent_id, sync_status, received_at, error_message)
                VALUES (:farmer_id, :agent_id, :sync_status, :received_at, :error_message)
            """),
            {
                "farmer_id": farmer_id,
                "agent_id": agent_id,
                "sync_status": status,
                "received_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "error_message": error[:500] if error else None,
            },
        )


ensure_sync_receipts_table()

class Login(BaseModel): username:str; password:str
class FieldRecord(BaseModel):
    farmer_id:str; registration_date:str; farmer_full_name:str; gender:str=''; date_of_birth:str=''; phone_number:str; alternate_phone:str=''; email_address:str=''; nin:str=''; state:str; lga:str; ward:str=''; community_village:str=''; residential_address:str=''; primary_crop:str=''; secondary_crop:str=''; farm_size_ha:float=0; input_distributed:str=''; quantity_units:int=0; nin_status:str='Pending'; id_type:str=''; id_number:str=''; latitude:float; longitude:float; gps_accuracy:Optional[float]=None; enumerator_remarks:str=''; photo_data:str=''; photo_mime:str='image/jpeg'
class SyncPayload(BaseModel): records:List[FieldRecord]

@app.post('/api/field/login')
def login(data: Login):
    username = str(data.username or '').strip().upper()
    password = str(data.password or '').strip()

    if not username or not password:
        raise HTTPException(401, 'Invalid agent credentials')

    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT id, pw, role, full_name, phone, nin, state, lga, email
                FROM users
                WHERE UPPER(id) = :username
                LIMIT 1
            """),
            {'username': username},
        ).mappings().first()

    if not row:
        raise HTTPException(401, 'Invalid agent credentials')

    u = dict(row)
    stored_password = str(u.get('pw') or '').strip()
    role = str(u.get('role') or '').strip().lower()

    if role != 'agent' or stored_password != password:
        raise HTTPException(401, 'Invalid agent credentials')

    agent_id = str(u.get('id') or username).strip().upper()
    country = 'Nigeria'
    state = str(u.get('state') or '').strip()
    lga = str(u.get('lga') or '').strip()

    return {
        'token': make_token(agent_id),
        'agent': {
            'id': agent_id,
            'name': str(u.get('full_name') or agent_id).strip(),
            'country': country,
            'state': state,
            'lga': lga,
            'bounds': territory_bounds(country, state),
        },
    }

@app.get('/api/field/health')
def health(): return {'ok':True,'service':'AGROW Field Sync API'}

@app.post('/api/field/sync')
def sync(data:SyncPayload, authorization:Optional[str]=Header(None)):
    agent=auth(authorization); engine=get_engine(); results=[]
    with engine.connect() as conn:
        user_row = conn.execute(
            text("SELECT id, role, state, lga FROM users WHERE UPPER(id)=:agent LIMIT 1"),
            {'agent': str(agent).strip().upper()},
        ).mappings().first()
    user = dict(user_row) if user_row else None
    country='Nigeria'; assigned_state=str(user.get('state') or '').strip() if user else ''
    for r in data.records:
        try:
            if r.state != assigned_state: raise ValueError(f'Record state {r.state} does not match assigned state {assigned_state}')
            valid=validate_territory(country, assigned_state, r.latitude, r.longitude)
            if valid is not True: raise ValueError('GPS did not validate inside assigned territory')
            with engine.connect() as conn:
                exists=conn.execute(text('SELECT 1 FROM farmers WHERE farmer_id=:fid'),{'fid':r.farmer_id}).first()
            if not exists:
                row={'Farmer_ID':r.farmer_id,'Registration_Date':r.registration_date,'Agent_ID':agent,'Farmer_Full_Name':r.farmer_full_name,'Gender':r.gender,'Date_of_Birth':r.date_of_birth,'Phone_Number':r.phone_number,'Alternate_Phone':r.alternate_phone,'Email_Address':r.email_address,'NIN':r.nin,'State':r.state,'LGA':r.lga,'Ward':r.ward,'Community_Village':r.community_village,'Residential_Address':r.residential_address,'Primary_Crop':r.primary_crop,'Secondary_Crop':r.secondary_crop,'Farm_Size_Ha':r.farm_size_ha,'Input_Distributed':r.input_distributed,'Quantity_Units':r.quantity_units,'NIN_Status':r.nin_status,'ID_Type':r.id_type,'ID_Number':r.id_number,'Latitude':r.latitude,'Longitude':r.longitude,'Enumerator_Remarks':f'{r.enumerator_remarks} | GPS accuracy: {r.gps_accuracy or "-"}m | Territory: VALIDATED','Photo_Path':'','Photo_Status':'Captured' if r.photo_data else 'No Photo','Photo_Data':r.photo_data,'Photo_Mime':r.photo_mime}
                insert_farmer(row)
            record_sync_receipt(r.farmer_id, agent, 'SYNCED')
            results.append({'farmer_id':r.farmer_id,'status':'SYNCED'})
        except Exception as e:
            err = str(e)[:300]
            record_sync_receipt(r.farmer_id, agent, 'FAILED', err)
            results.append({'farmer_id':r.farmer_id,'status':'FAILED','error':err})
    return {'results':results}

@app.get('/api/field/sync/receipts')
def sync_receipts(authorization:Optional[str]=Header(None), limit:int=100):
    agent=auth(authorization)
    ensure_sync_receipts_table()
    with get_engine().connect() as conn:
        rows=conn.execute(text("""
            SELECT farmer_id, agent_id, sync_status, received_at, error_message
            FROM field_sync_receipts
            WHERE agent_id=:agent
            ORDER BY id DESC
            LIMIT :limit
        """), {'agent':agent, 'limit':max(1,min(int(limit),500))}).mappings().all()
    return {'results':[dict(r) for r in rows]}

app.mount('/assets', StaticFiles(directory=STATIC), name='assets')
@app.get('/')
def root(): return FileResponse(STATIC/'index.html')
@app.get('/manifest.webmanifest')
def manifest(): return FileResponse(STATIC/'manifest.webmanifest', media_type='application/manifest+json')
@app.get('/sw.js')
def sw(): return FileResponse(STATIC/'sw.js', media_type='application/javascript')
