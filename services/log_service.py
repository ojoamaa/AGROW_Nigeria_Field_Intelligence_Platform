from datetime import datetime
from core.db import get_connection


def log_action(username: str, action: str, details: str = ""):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            action TEXT,
            details TEXT,
            timestamp TEXT
        )
    """)

    cursor.execute(
        """
        INSERT INTO audit_logs (username, action, details, timestamp)
        VALUES (?, ?, ?, ?)
        """,
        (
            username,
            action,
            details,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )

    conn.commit()
    conn.close()
