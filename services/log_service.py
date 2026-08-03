from datetime import datetime
from sqlalchemy import text
from core.db import get_engine
engine=get_engine()

def log_action(username: str, action: str, details: str=''):
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO audit_logs (username,action,details,timestamp) VALUES (:u,:a,:d,:t)"),
                     {'u':username,'a':action,'d':details,'t':datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
