import pandas as pd
from sqlalchemy import text
from core.db import get_engine
engine=get_engine()

def fetch_user(username: str):
    username=str(username or '').strip().upper()
    if not username: return None
    with engine.connect() as conn:
        row=conn.execute(text("SELECT id,pw,role,full_name,phone,nin,state,lga,email FROM users WHERE UPPER(id)=:id"), {'id':username}).mappings().first()
    if not row: return None
    return {'username':row['id'],'pw':row['pw'],'role':row['role'],'full_name':row['full_name'],'phone':row['phone'],'nin':row['nin'],'state':row['state'],'lga_coverage':row['lga'],'email':row['email']}

def insert_user(username,password,role,full_name,phone,nin,state,lga_coverage,email):
    username=str(username or '').strip().upper(); password=str(password or '').strip()
    if not username or not password: raise ValueError('Username and password are required.')
    with engine.begin() as conn:
        conn.execute(text("""INSERT INTO users (id,pw,role,full_name,phone,nin,state,lga,email)
        VALUES (:id,:pw,:role,:full_name,:phone,:nin,:state,:lga,:email)"""),
        dict(id=username,pw=password,role=role,full_name=full_name,phone=phone,nin=nin,state=state,lga=lga_coverage,email=email))

def update_user_password(username,new_password):
    with engine.begin() as conn:
        conn.execute(text("UPDATE users SET pw=:pw WHERE UPPER(id)=:id"), {'pw':str(new_password).strip(),'id':str(username).strip().upper()})

def fetch_all_agents():
    return pd.read_sql_query(text("""SELECT id AS "Agent_ID", full_name AS "Full_Name", phone AS "Phone", nin AS "NIN", state AS "State", lga AS "LGA_Coverage", email AS "Email" FROM users WHERE role='agent' ORDER BY id"""), engine)

def seed_default_users():
    if not fetch_user('ADMIN'):
        insert_user('ADMIN','agrow2026','admin','National AGROW Administrator','08000000000','00000000000','All Nigeria','All','admin@agrow-proposal.ng')

def generate_agent_id_db(state_prefix: str):
    prefix=str(state_prefix or 'AG').strip().upper()
    with engine.connect() as conn:
        rows=conn.execute(text("SELECT id FROM users WHERE UPPER(id) LIKE :pattern"), {'pattern':f'{prefix}-%'}).all()
    nums=[]
    for row in rows:
        try: nums.append(int(str(row[0]).rsplit('-',1)[1]))
        except (IndexError,ValueError): pass
    return f'{prefix}-{max(nums,default=0)+1:02d}'
