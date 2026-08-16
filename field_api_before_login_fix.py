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

class Login(BaseModel): username:str; password:str
class FieldRecord(BaseModel):
    farmer_id:str; registration_date:str; farmer_full_name:str; gender:str=''; date_of_birth:str=''; phone_number:str; alternate_phone:str=''; email_address:str=''; nin:str=''; state:str; lga:str; ward:str=''; community_village:str=''; residential_address:str=''; primary_crop:str=''; secondary_crop:str=''; farm_size_ha:float=0; input_distributed:str=''; quantity_units:int=0; nin_status:str='Pending'; id_type:str=''; id_number:str=''; latitude:float; longitude:float; gps_accuracy:Optional[float]=None; enumerator_remarks:str=''; photo_data:str=''; photo_mime:str='image/jpeg'
class SyncPayload(BaseModel): records:List[FieldRecord]

@app.post('/api/field/login')
def login(data:Login):
    u=fetch_user(data.username)
    if not u or u['role']!='agent' or str(u['pw'])!=data.password: raise HTTPException(401,'Invalid agent credentials')
    country='Nigeria'; state=u.get('state') or ''; lga=u.get('lga_coverage') or ''
    return {'token':make_token(u['username']),'agent':{'id':u['username'],'name':u['full_name'],'country':country,'state':state,'lga':lga,'bounds':territory_bounds(country,state)}}

@app.get('/api/field/health')
def health(): return {'ok':True,'service':'AGROW Field Sync API'}

@app.post('/api/field/sync')
def sync(data:SyncPayload, authorization:Optional[str]=Header(None)):
    agent=auth(authorization); engine=get_engine(); results=[]
    user=fetch_user(agent); country='Nigeria'; assigned_state=user.get('state') if user else ''
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
            results.append({'farmer_id':r.farmer_id,'status':'SYNCED'})
        except Exception as e: results.append({'farmer_id':r.farmer_id,'status':'FAILED','error':str(e)[:300]})
    return {'results':results}

app.mount('/assets', StaticFiles(directory=STATIC), name='assets')
@app.get('/')
def root(): return FileResponse(STATIC/'index.html')
@app.get('/manifest.webmanifest')
def manifest(): return FileResponse(STATIC/'manifest.webmanifest', media_type='application/manifest+json')
@app.get('/sw.js')
def sw(): return FileResponse(STATIC/'sw.js', media_type='application/javascript')
