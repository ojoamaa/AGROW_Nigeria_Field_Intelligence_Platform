from datetime import datetime
import pandas as pd
from sqlalchemy import text
from core.db import get_engine

engine = get_engine()


def create_intervention(row: dict):
    params = {
        "intervention_id": row.get("Intervention_ID"),
        "farmer_id": row.get("Farmer_ID"),
        "programme_name": row.get("Programme_Name", ""),
        "intervention_type": row.get("Intervention_Type", ""),
        "support_items": row.get("Support_Items", ""),
        "quantity": row.get("Quantity", 0),
        "unit": row.get("Unit", ""),
        "intervention_date": row.get("Intervention_Date", ""),
        "status": row.get("Status", "Delivered"),
        "agent_id": row.get("Agent_ID", ""),
        "remarks": row.get("Remarks", ""),
        "created_at": row.get("Created_At") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO programme_interventions
            (intervention_id, farmer_id, programme_name, intervention_type, support_items,
             quantity, unit, intervention_date, status, agent_id, remarks, created_at)
            VALUES (:intervention_id, :farmer_id, :programme_name, :intervention_type, :support_items,
                    :quantity, :unit, :intervention_date, :status, :agent_id, :remarks, :created_at)
        """), params)


def fetch_interventions(farmer_ids=None):
    if farmer_ids is not None:
        farmer_ids = [str(x) for x in farmer_ids if str(x).strip()]
        if not farmer_ids:
            return pd.DataFrame()
        placeholders = ",".join(f":fid{i}" for i in range(len(farmer_ids)))
        params = {f"fid{i}": fid for i, fid in enumerate(farmer_ids)}
        sql = text(f"""
            SELECT * FROM programme_interventions
            WHERE farmer_id IN ({placeholders})
            ORDER BY intervention_date DESC, id DESC
        """)
        return pd.read_sql_query(sql, engine, params=params)
    return pd.read_sql_query(
        text("SELECT * FROM programme_interventions ORDER BY intervention_date DESC, id DESC"),
        engine,
    )
