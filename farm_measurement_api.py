"""Phase 1.6A additive farm boundary measurement endpoints.

No changes to existing farmer registration or declared area.
Measurements remain PENDING_REVIEW after successful upload.
"""
import json
import math
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from core.db import get_engine

router = APIRouter(prefix='/api/field/measurements', tags=['Farm measurements'])

class Point(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    accuracy_m: Optional[float] = Field(default=None, ge=0, le=10000)
    recorded_at: Optional[str] = None

class Measurement(BaseModel):
    measurement_id: str = Field(min_length=10, max_length=100)
    farmer_id: str = Field(min_length=1, max_length=150)
    points: List[Point] = Field(min_length=3, max_length=2000)
    capture_method: str = Field(default='WALK_GPS')
    completed_at: str


def area_ha(points):
    """Spherical geodesic polygon approximation, latitude/longitude degrees.

    Not cadastral-grade; for field estimation only. Handles the closing edge.
    """
    earth_radius = 6371008.8
    vertices = [(math.radians(p.lon), math.radians(p.lat)) for p in points]
    acc = 0.0
    for i, (lon1, lat1) in enumerate(vertices):
        lon2, lat2 = vertices[(i + 1) % len(vertices)]
        dlon = (lon2 - lon1 + math.pi) % (2 * math.pi) - math.pi
        acc += dlon * (2 + math.sin(lat1) + math.sin(lat2))
    return abs(acc) * earth_radius * earth_radius / 2 / 10000


def ensure_table():
    with get_engine().begin() as conn:
        conn.execute(text('''CREATE TABLE IF NOT EXISTS farm_measurements (
            measurement_id TEXT PRIMARY KEY, farmer_id TEXT NOT NULL,
            agent_id TEXT NOT NULL, state TEXT NOT NULL, lga TEXT NOT NULL,
            polygon_json TEXT NOT NULL, area_ha REAL NOT NULL,
            capture_method TEXT NOT NULL, completed_at TEXT NOT NULL,
            received_at TEXT NOT NULL, verification_status TEXT NOT NULL DEFAULT 'PENDING_REVIEW'
        )'''))
        conn.execute(text('CREATE INDEX IF NOT EXISTS ix_farm_measurements_farmer ON farm_measurements(farmer_id)'))


def get_agent(authorization):
    # Reuse the existing signed field token and agent account validation.
    from field_api import auth
    agent_id = auth(authorization)
    with get_engine().connect() as conn:
        row = conn.execute(text('SELECT id, role, state, lga FROM users WHERE UPPER(id)=:id'),
                           {'id':agent_id.upper()}).mappings().first()
    if not row or str(row['role']).lower() != 'agent':
        raise HTTPException(403, 'Active agent account required')
    return dict(row)


@router.post('/sync')
def sync_measurement(data: Measurement, authorization: Optional[str] = Header(None)):
    agent = get_agent(authorization)
    if data.capture_method not in ('WALK_GPS', 'MANUAL_ADJUSTED'):
        raise HTTPException(422, 'Unsupported capture method')
    if len({(round(p.lat, 7), round(p.lon, 7)) for p in data.points}) < 3:
        raise HTTPException(422, 'At least three distinct boundary points required')
    from field_api import validate_territory
    for p in data.points:
        if validate_territory('Nigeria', agent['state'], p.lat, p.lon) is not True:
            raise HTTPException(422, 'Boundary point outside assigned state envelope')
    area = area_ha(data.points)
    if not math.isfinite(area) or area < 0.0001 or area > 100000:
        raise HTTPException(422, 'Invalid or implausible polygon area')
    ensure_table()
    engine = get_engine()
    with engine.begin() as conn:
        farmer = conn.execute(text('''SELECT farmer_id, agent_id, state, lga FROM farmers
                                     WHERE farmer_id=:fid'''), {'fid':data.farmer_id}).mappings().first()
        if not farmer:
            raise HTTPException(409, 'Farmer must be synced before farm measurement')
        if str(farmer['agent_id']).upper() != str(agent['id']).upper():
            raise HTTPException(403, 'Farmer is not assigned to this agent')
        if str(farmer['state']).strip().lower() != str(agent['state']).strip().lower():
            raise HTTPException(403, 'Farmer outside assigned state')
        existing = conn.execute(text('SELECT farmer_id, agent_id, area_ha FROM farm_measurements WHERE measurement_id=:mid'),
                                {'mid':data.measurement_id}).mappings().first()
        if existing:
            if existing['farmer_id'] != data.farmer_id or str(existing['agent_id']).upper() != str(agent['id']).upper():
                raise HTTPException(409, 'Measurement ID already assigned to another record')
            return {'measurement_id':data.measurement_id, 'status':'SYNCED',
                    'verification_status':'PENDING_REVIEW', 'area_ha':existing['area_ha'], 'duplicate':True}
        conn.execute(text('''INSERT INTO farm_measurements
            (measurement_id,farmer_id,agent_id,state,lga,polygon_json,area_ha,capture_method,completed_at,received_at,verification_status)
            VALUES (:mid,:fid,:aid,:state,:lga,:poly,:area,:method,:completed,:received,'PENDING_REVIEW')'''), {
            'mid':data.measurement_id, 'fid':data.farmer_id, 'aid':agent['id'],
            'state':farmer['state'], 'lga':farmer['lga'],
            'poly':json.dumps([p.model_dump() if hasattr(p,'model_dump') else p.dict() for p in data.points]),
            'area':round(area,6), 'method':data.capture_method, 'completed':data.completed_at,
            'received':datetime.now(timezone.utc).isoformat()})
    return {'measurement_id':data.measurement_id, 'status':'SYNCED',
            'verification_status':'PENDING_REVIEW', 'area_ha':round(area,4), 'duplicate':False}


@router.get('/mine')
def my_measurements(authorization: Optional[str] = Header(None)):
    agent = get_agent(authorization)
    ensure_table()
    with get_engine().connect() as conn:
        rows = conn.execute(text('''SELECT measurement_id,farmer_id,area_ha,capture_method,
                                  verification_status,received_at FROM farm_measurements
                                  WHERE agent_id=:agent ORDER BY received_at DESC LIMIT 250'''),
                            {'agent':agent['id']}).mappings().all()
    return {'results':[dict(r) for r in rows]}
