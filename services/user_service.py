from datetime import datetime
from core.db import get_connection
import pandas as pd

def fetch_user(username: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, pw, role, full_name, phone, nin, state, lga, email
        FROM users
        WHERE id = ?
        """,
        (username,),
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "username": row["id"],
            "pw": row["pw"],
            "role": row["role"],
            "full_name": row["full_name"],
            "phone": row["phone"],
            "nin": row["nin"],
            "state": row["state"],
            "lga_coverage": row["lga"],
            "email": row["email"],
        }
    return None


def insert_user(username, password, role, full_name, phone, nin, state, lga_coverage, email):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO users (id, pw, role, full_name, phone, nin, state, lga, email)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (username, password, role, full_name, phone, nin, state, lga_coverage, email),
    )

    conn.commit()
    conn.close()


def update_user_password(username, new_password):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET pw = ?
        WHERE id = ?
        """,
        (new_password, username),
    )

    conn.commit()
    conn.close()


def fetch_all_agents():
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT
            id AS Agent_ID,
            full_name AS Full_Name,
            phone AS Phone,
            nin AS NIN,
            state AS State,
            lga AS LGA_Coverage,
            email AS Email
        FROM users
        WHERE role = 'agent'
        ORDER BY id
        """,
        conn,
    )
    conn.close()
    return df


def seed_default_users():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE id = ?", ("admin",))
    existing_admin = cursor.fetchone()

    if not existing_admin:
        cursor.execute(
            """
            INSERT INTO users (id, pw, role, full_name, phone, nin, state, lga, email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "admin",
                "agrow2026",
                "admin",
                "National AGROW Administrator",
                "08000000000",
                "00000000000",
                "All Nigeria",
                "All",
                "admin@agrow-proposal.ng",
            ),
        )

    conn.commit()
    conn.close()


def generate_agent_id_db(state_prefix: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE id LIKE ?
        ORDER BY id
        """,
        (f"{state_prefix}-%",),
    )
    rows = cursor.fetchall()
    conn.close()

    next_num = len(rows) + 1
    return f"{state_prefix}-{next_num:02d}"