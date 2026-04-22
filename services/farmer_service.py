import json
from datetime import datetime

import pandas as pd
from core.db import get_connection


def fetch_farmers():
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM farmers ORDER BY registration_date DESC",
        conn
    )
    conn.close()
    return df


def farmer_exists_today(phone_number: str, nin: str, farmer_full_name: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT farmer_id
        FROM farmers
        WHERE phone_number = ?
          AND nin = ?
          AND LOWER(farmer_full_name) = LOWER(?)
          AND date(registration_date) = date('now', 'localtime')
        LIMIT 1
        """,
        (phone_number, nin, farmer_full_name),
    )

    row = cursor.fetchone()
    conn.close()
    return row is not None


def insert_farmer(row: dict):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO farmers (
            farmer_id,
            registration_date,
            agent_id,
            farmer_full_name,
            gender,
            date_of_birth,
            phone_number,
            alternate_phone,
            email_address,
            nin,
            state,
            lga,
            ward,
            community_village,
            residential_address,
            primary_crop,
            secondary_crop,
            farm_size_ha,
            input_distributed,
            quantity_units,
            nin_status,
            id_type,
            id_number,
            latitude,
            longitude,
            enumerator_remarks,
            photo_path,
            photo_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["Farmer_ID"],
            row["Registration_Date"],
            row["Agent_ID"],
            row["Farmer_Full_Name"],
            row["Gender"],
            row["Date_of_Birth"],
            row["Phone_Number"],
            row["Alternate_Phone"],
            row["Email_Address"],
            row["NIN"],
            row["State"],
            row["LGA"],
            row["Ward"],
            row["Community_Village"],
            row["Residential_Address"],
            row["Primary_Crop"],
            row["Secondary_Crop"],
            row["Farm_Size_Ha"],
            row["Input_Distributed"],
            row["Quantity_Units"],
            row["NIN_Status"],
            row["ID_Type"],
            row["ID_Number"],
            row["Latitude"],
            row["Longitude"],
            row["Enumerator_Remarks"],
            row["Photo_Path"],
            row["Photo_Status"],
        ),
    )

    conn.commit()
    conn.close()


def save_to_offline_queue(row: dict):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO offline_queue (
            farmer_id,
            payload,
            sync_status,
            created_at,
            synced_at,
            error_message
        )
        VALUES (?, ?, 'PENDING', ?, NULL, NULL)
        """,
        (
            row["Farmer_ID"],
            json.dumps(row),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )

    conn.commit()
    conn.close()


def fetch_offline_queue():
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM offline_queue ORDER BY created_at DESC",
        conn
    )
    conn.close()
    return df


def sync_offline_queue():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, payload
        FROM offline_queue
        WHERE sync_status IN ('PENDING', 'FAILED')
        ORDER BY created_at ASC
    """)
    queue_rows = cursor.fetchall()

    synced_count = 0
    failed_count = 0

    for queue_id, payload in queue_rows:
        try:
            row = json.loads(payload)

            # avoid duplicate insert by farmer_id
            cursor.execute(
                "SELECT farmer_id FROM farmers WHERE farmer_id = ? LIMIT 1",
                (row["Farmer_ID"],)
            )
            existing = cursor.fetchone()

            if existing is None:
                cursor.execute(
                    """
                    INSERT INTO farmers (
                        farmer_id,
                        registration_date,
                        agent_id,
                        farmer_full_name,
                        gender,
                        date_of_birth,
                        phone_number,
                        alternate_phone,
                        email_address,
                        nin,
                        state,
                        lga,
                        ward,
                        community_village,
                        residential_address,
                        primary_crop,
                        secondary_crop,
                        farm_size_ha,
                        input_distributed,
                        quantity_units,
                        nin_status,
                        id_type,
                        id_number,
                        latitude,
                        longitude,
                        enumerator_remarks,
                        photo_path,
                        photo_status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["Farmer_ID"],
                        row["Registration_Date"],
                        row["Agent_ID"],
                        row["Farmer_Full_Name"],
                        row["Gender"],
                        row["Date_of_Birth"],
                        row["Phone_Number"],
                        row["Alternate_Phone"],
                        row["Email_Address"],
                        row["NIN"],
                        row["State"],
                        row["LGA"],
                        row["Ward"],
                        row["Community_Village"],
                        row["Residential_Address"],
                        row["Primary_Crop"],
                        row["Secondary_Crop"],
                        row["Farm_Size_Ha"],
                        row["Input_Distributed"],
                        row["Quantity_Units"],
                        row["NIN_Status"],
                        row["ID_Type"],
                        row["ID_Number"],
                        row["Latitude"],
                        row["Longitude"],
                        row["Enumerator_Remarks"],
                        row["Photo_Path"],
                        row["Photo_Status"],
                    ),
                )

            cursor.execute(
                """
                UPDATE offline_queue
                SET sync_status = 'SYNCED',
                    synced_at = ?,
                    error_message = NULL
                WHERE id = ?
                """,
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), queue_id),
            )

            synced_count += 1

        except Exception as e:
            cursor.execute(
                """
                UPDATE offline_queue
                SET sync_status = 'FAILED',
                    error_message = ?
                WHERE id = ?
                """,
                (str(e), queue_id),
            )
            failed_count += 1

    conn.commit()
    conn.close()

    return synced_count, failed_count