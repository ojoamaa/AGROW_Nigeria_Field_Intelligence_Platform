import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

import pandas as pd
import plotly.express as px
import streamlit as st
from nigeria_lga_data import NIGERIA_LGA_MAP

load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    st.error("DATABASE_URL is not set. Please configure your PostgreSQL connection.")
    st.stop()

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# =========================================================
# 1. PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="AGROW Nigeria Digital Field Intelligence Platform",
    page_icon="🌾",
    layout="wide"
)

# =========================================================
# 2. BRANDING / COLORS
# =========================================================
PRIMARY_GREEN = "#1B5E20"
OFFICIAL_BLUE = "#004B87"
LIGHT_BG = "#F8F9FA"
TEXT_GREY = "#5F6368"

LOGO_CANDIDATES = [
    "proposal_logo.png",
    "logo.png",
    "static/proposal_logo.png",
    "static/logo.png"
]

# =========================================================
# 3. GLOBAL STYLING
# =========================================================
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {LIGHT_BG};
    }}

    [data-testid="stSidebar"] {{
        background-color: #FFFFFF;
        border-right: 3px solid {PRIMARY_GREEN};
        min-width: 320px !important;
        max-width: 420px !important;
        overflow-y: auto !important;
    }}

    [data-testid="stSidebar"]::-webkit-scrollbar {{
        width: 10px;
    }}

    [data-testid="stSidebar"]::-webkit-scrollbar-track {{
        background: #F1F3F5;
        border-radius: 10px;
    }}

    [data-testid="stSidebar"]::-webkit-scrollbar-thumb {{
        background: #B0B8C1;
        border-radius: 10px;
    }}

    [data-testid="stSidebar"]::-webkit-scrollbar-thumb:hover {{
        background: #8C959F;
    }}

    [data-testid="stMetric"] {{
        background: white !important;
        border-left: 8px solid {PRIMARY_GREEN} !important;
        border-radius: 14px !important;
        padding: 16px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06) !important;
    }}

    [data-testid="stMetricValue"] {{
        color: {OFFICIAL_BLUE} !important;
        font-size: 28px !important;
        font-weight: 800 !important;
    }}

    .auth-card {{
        padding: 18px 24px 24px 24px;
        background: white;
        border-radius: 16px;
        border-top: 8px solid {PRIMARY_GREEN};
        box-shadow: 0 12px 30px rgba(0,0,0,0.10);
        max-width: 760px;
        margin: auto;
    }}

    .top-title {{
        text-align: center;
        font-size: 14px;
        font-weight: 800;
        color: {PRIMARY_GREEN};
        letter-spacing: 0.3px;
    }}

    .main-title {{
        text-align: center;
        font-size: 34px;
        font-weight: 900;
        color: {OFFICIAL_BLUE};
        margin-top: 2px;
        margin-bottom: 4px;
        line-height: 1.2;
    }}

    .sub-title {{
        text-align: center;
        font-size: 15px;
        font-weight: 700;
        color: {PRIMARY_GREEN};
        margin-bottom: 6px;
        line-height: 1.4;
    }}

    .small-note {{
        text-align: center;
        font-size: 13px;
        color: {TEXT_GREY};
        margin-bottom: 14px;
        line-height: 1.4;
    }}

    label, .stSelectbox label, .stMultiSelect label, .stTextInput label, .stDateInput label, .stNumberInput label, .stTextArea label {{
        font-weight: 700 !important;
        color: #1f1f1f !important;
    }}

    .stTextInput input,
    .stNumberInput input,
    .stDateInput input,
    .stTextArea textarea {{
        border: 1.5px solid #D0D7DE !important;
        border-radius: 10px !important;
        background-color: #FAFBFC !important;
        padding: 0.65rem !important;
    }}

    div[data-baseweb="select"] > div {{
        border: 1.5px solid #D0D7DE !important;
        border-radius: 10px !important;
        background-color: #FAFBFC !important;
    }}

    .sidebar-form-note {{
        background: #F4F8F4;
        border-left: 4px solid {PRIMARY_GREEN};
        padding: 10px 12px;
        border-radius: 8px;
        font-size: 13px;
        margin-bottom: 10px;
        color: #2f3b2f;
    }}

    .stButton > button, .stDownloadButton > button {{
        border-radius: 10px !important;
        font-weight: 700 !important;
        min-height: 44px !important;
    }}

    .stApp::after {{
        content: "DataDev Limited";
        position: fixed;
        bottom: 90px;
        right: 20px;
        font-size: 36px;
        color: rgba(0, 0, 0, 0.03);
        transform: rotate(-20deg);
        z-index: 0;
        pointer-events: none;
    }}

    @media (max-width: 768px) {{
        .main-title {{
            font-size: 24px !important;
        }}

        .sub-title {{
            font-size: 13px !important;
        }}

        .small-note {{
            font-size: 12px !important;
        }}

        [data-testid="stSidebar"] {{
            min-width: 100% !important;
            max-width: 100% !important;
        }}
    }}

    .footer {{
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: white;
        text-align: center;
        padding: 10px;
        font-weight: 700;
        border-top: 1px solid #ddd;
        z-index: 999;
        font-size: 12px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 4. HELPERS
# =========================================================
def get_logo_path():
    for path in LOGO_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def normalize_state_name(state_name: str) -> str:
    if state_name == "FCT":
        return "Federal Capital Territory"
    return state_name


def get_state_prefix(state_name: str) -> str:
    special_map = {
        "Abia": "AB",
        "Adamawa": "AD",
        "Akwa Ibom": "AI",
        "Anambra": "AN",
        "Bauchi": "BC",
        "Bayelsa": "BY",
        "Benue": "BN",
        "Borno": "BO",
        "Cross River": "CR",
        "Delta": "DT",
        "Ebonyi": "EB",
        "Edo": "ED",
        "Ekiti": "EK",
        "Enugu": "EN",
        "FCT": "FC",
        "Federal Capital Territory": "FC",
        "Gombe": "GM",
        "Imo": "IM",
        "Jigawa": "JG",
        "Kaduna": "KD",
        "Kano": "KN",
        "Katsina": "KT",
        "Kebbi": "KB",
        "Kogi": "KG",
        "Kwara": "KW",
        "Lagos": "LG",
        "Nasarawa": "NS",
        "Niger": "NG",
        "Ogun": "OG",
        "Ondo": "OD",
        "Osun": "OS",
        "Oyo": "OY",
        "Plateau": "PL",
        "Rivers": "RV",
        "Sokoto": "SK",
        "Taraba": "TR",
        "Yobe": "YB",
        "Zamfara": "ZF"
    }
    return special_map.get(state_name, state_name[:2].upper())


def valid_phone(phone: str) -> bool:
    digits = "".join([c for c in phone if c.isdigit()])
    return len(digits) >= 11


def valid_nin(nin: str) -> bool:
    return nin.isdigit() and len(nin) == 11


def valid_email(email: str) -> bool:
    return "@" in email and "." in email


def table_to_csv_download(df: pd.DataFrame, filename: str):
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"⬇️ Download {filename}",
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        use_container_width=True
    )


# =========================================================
# 5. DATABASE
# =========================================================
def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                full_name TEXT,
                phone TEXT,
                nin TEXT,
                state TEXT,
                lga_coverage TEXT,
                email TEXT,
                created_at TEXT
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS farmers (
                farmer_id TEXT PRIMARY KEY,
                registration_date TEXT,
                agent_id TEXT,
                farmer_full_name TEXT,
                gender TEXT,
                date_of_birth TEXT,
                phone_number TEXT,
                alternate_phone TEXT,
                email_address TEXT,
                nin TEXT,
                state TEXT,
                lga TEXT,
                ward TEXT,
                community_village TEXT,
                residential_address TEXT,
                primary_crop TEXT,
                secondary_crop TEXT,
                farm_size_ha DOUBLE PRECISION,
                input_distributed TEXT,
                quantity_units INTEGER,
                nin_status TEXT,
                id_type TEXT,
                id_number TEXT,
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                enumerator_remarks TEXT,
                photo_status TEXT
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                username TEXT,
                action TEXT,
                details TEXT,
                timestamp TEXT
            )
        """))


def log_action(username: str, action: str, details: str = ""):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO audit_logs (username, action, details, timestamp)
                VALUES (:username, :action, :details, :timestamp)
            """),
            {
                "username": username,
                "action": action,
                "details": details,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )


def seed_db():
    with engine.begin() as conn:
        user_count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()

        if user_count == 0:
            users = [
                {
                    "username": "admin",
                    "password": "agrow2026",
                    "role": "admin",
                    "full_name": "National AGROW Administrator",
                    "phone": "08000000000",
                    "nin": "00000000000",
                    "state": "All Nigeria",
                    "lga_coverage": "All",
                    "email": "admin@agrow-proposal.ng",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                {
                    "username": "KN-01",
                    "password": "agent123",
                    "role": "agent",
                    "full_name": "Kano Field Agent 1",
                    "phone": "08030000001",
                    "nin": "11111111111",
                    "state": "Kano",
                    "lga_coverage": "Nasarawa",
                    "email": "kn01@agrow-proposal.ng",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                {
                    "username": "KD-01",
                    "password": "agent123",
                    "role": "agent",
                    "full_name": "Kaduna Field Agent 1",
                    "phone": "08030000002",
                    "nin": "22222222222",
                    "state": "Kaduna",
                    "lga_coverage": "Chikun",
                    "email": "kd01@agrow-proposal.ng",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                {
                    "username": "FC-01",
                    "password": "agent123",
                    "role": "agent",
                    "full_name": "FCT Field Agent 1",
                    "phone": "08030000003",
                    "nin": "33333333333",
                    "state": "FCT",
                    "lga_coverage": "Gwagwalada",
                    "email": "fc01@agrow-proposal.ng",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
            ]

            for user in users:
                conn.execute(text("""
                    INSERT INTO users (
                        username, password, role, full_name, phone, nin,
                        state, lga_coverage, email, created_at
                    )
                    VALUES (
                        :username, :password, :role, :full_name, :phone, :nin,
                        :state, :lga_coverage, :email, :created_at
                    )
                """), user)

        farmer_count = conn.execute(text("SELECT COUNT(*) FROM farmers")).scalar()

        if farmer_count == 0:
            farmers = [
                {
                    "farmer_id": "AG-20260409-001",
                    "registration_date": "2026-04-09 08:45:00",
                    "agent_id": "KN-01",
                    "farmer_full_name": "Musa Ibrahim",
                    "gender": "Male",
                    "date_of_birth": "1988-05-13",
                    "phone_number": "08031234567",
                    "alternate_phone": "08052345678",
                    "email_address": "musa.ibrahim@example.com",
                    "nin": "12345678901",
                    "state": "Kano",
                    "lga": "Nasarawa",
                    "ward": "Ward 1",
                    "community_village": "Danbatta Cluster",
                    "residential_address": "No. 12 Farm Settlement, Kano",
                    "primary_crop": "Rice",
                    "secondary_crop": "Maize",
                    "farm_size_ha": 2.5,
                    "input_distributed": "Rice Seeds, NPK, Urea, Herbicide",
                    "quantity_units": 8,
                    "nin_status": "Verified",
                    "id_type": "NIN Slip",
                    "id_number": "12345678901",
                    "latitude": 11.990000,
                    "longitude": 8.520000,
                    "enumerator_remarks": "Active and verified beneficiary",
                    "photo_status": "No Photo"
                },
                {
                    "farmer_id": "AG-20260409-002",
                    "registration_date": "2026-04-09 09:10:00",
                    "agent_id": "KD-01",
                    "farmer_full_name": "Aisha Bello",
                    "gender": "Female",
                    "date_of_birth": "1992-03-08",
                    "phone_number": "08042345678",
                    "alternate_phone": "",
                    "email_address": "aisha.bello@example.com",
                    "nin": "23456789012",
                    "state": "Kaduna",
                    "lga": "Chikun",
                    "ward": "Ward 3",
                    "community_village": "Sabon Tasha",
                    "residential_address": "Sabon Tasha, Kaduna",
                    "primary_crop": "Maize",
                    "secondary_crop": "Soybean",
                    "farm_size_ha": 1.8,
                    "input_distributed": "Maize Seeds, NPK, Urea, Pesticide",
                    "quantity_units": 6,
                    "nin_status": "Verified",
                    "id_type": "Voter Card",
                    "id_number": "PVC-334455",
                    "latitude": 10.450000,
                    "longitude": 7.430000,
                    "enumerator_remarks": "Ready for next disbursement batch",
                    "photo_status": "No Photo"
                },
                {
                    "farmer_id": "AG-20260409-003",
                    "registration_date": "2026-04-09 09:30:00",
                    "agent_id": "FC-01",
                    "farmer_full_name": "Grace Philip",
                    "gender": "Female",
                    "date_of_birth": "1985-09-11",
                    "phone_number": "08061234567",
                    "alternate_phone": "07039876543",
                    "email_address": "grace.philip@example.com",
                    "nin": "34567890123",
                    "state": "FCT",
                    "lga": "Gwagwalada",
                    "ward": "Ward 2",
                    "community_village": "Paiko",
                    "residential_address": "Paiko, Gwagwalada, Abuja",
                    "primary_crop": "Cassava",
                    "secondary_crop": "Groundnut",
                    "farm_size_ha": 3.0,
                    "input_distributed": "Cassava Stems, NPK, Insecticide, Sprayer",
                    "quantity_units": 7,
                    "nin_status": "Pending",
                    "id_type": "Driver's License",
                    "id_number": "DL-556677",
                    "latitude": 8.943000,
                    "longitude": 7.081000,
                    "enumerator_remarks": "Pending NIN confirmation",
                    "photo_status": "No Photo"
                }
            ]

            for farmer in farmers:
                conn.execute(text("""
                    INSERT INTO farmers (
                        farmer_id, registration_date, agent_id, farmer_full_name, gender, date_of_birth,
                        phone_number, alternate_phone, email_address, nin, state, lga, ward,
                        community_village, residential_address, primary_crop, secondary_crop,
                        farm_size_ha, input_distributed, quantity_units, nin_status, id_type,
                        id_number, latitude, longitude, enumerator_remarks, photo_status
                    )
                    VALUES (
                        :farmer_id, :registration_date, :agent_id, :farmer_full_name, :gender, :date_of_birth,
                        :phone_number, :alternate_phone, :email_address, :nin, :state, :lga, :ward,
                        :community_village, :residential_address, :primary_crop, :secondary_crop,
                        :farm_size_ha, :input_distributed, :quantity_units, :nin_status, :id_type,
                        :id_number, :latitude, :longitude, :enumerator_remarks, :photo_status
                    )
                """), farmer)


def fetch_user(username: str):
    with engine.begin() as conn:
        row = conn.execute(text("""
            SELECT username, password, role, full_name, phone, nin, state, lga_coverage, email
            FROM users
            WHERE username = :username
        """), {"username": username}).fetchone()

    if row:
        return {
            "username": row[0],
            "pw": row[1],
            "role": row[2],
            "full_name": row[3],
            "phone": row[4],
            "nin": row[5],
            "state": row[6],
            "lga_coverage": row[7],
            "email": row[8]
        }
    return None


def fetch_all_agents():
    query = """
        SELECT username AS "Agent_ID",
               full_name AS "Full_Name",
               phone AS "Phone",
               nin AS "NIN",
               state AS "State",
               lga_coverage AS "LGA_Coverage",
               email AS "Email"
        FROM users
        WHERE role = 'agent'
        ORDER BY username
    """
    return pd.read_sql(query, engine)


def fetch_farmers():
    return pd.read_sql("SELECT * FROM farmers ORDER BY registration_date DESC", engine)


def insert_user(username, password, role, full_name, phone, nin, state, lga_coverage, email):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO users (
                username, password, role, full_name, phone, nin, state, lga_coverage, email, created_at
            )
            VALUES (
                :username, :password, :role, :full_name, :phone, :nin, :state, :lga_coverage, :email, :created_at
            )
        """), {
            "username": username,
            "password": password,
            "role": role,
            "full_name": full_name,
            "phone": phone,
            "nin": nin,
            "state": state,
            "lga_coverage": lga_coverage,
            "email": email,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })


def update_user_password(username, new_password):
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE users SET password = :password WHERE username = :username"),
            {"password": new_password, "username": username}
        )


def generate_agent_id_db(state_name: str) -> str:
    prefix = get_state_prefix(state_name)
    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT username FROM users WHERE role = 'agent' AND username LIKE :pattern"),
            {"pattern": f"{prefix}-%"}
        ).fetchall()
    next_num = len(rows) + 1
    return f"{prefix}-{next_num:02d}"


def insert_farmer(row: dict):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO farmers (
                farmer_id, registration_date, agent_id, farmer_full_name, gender, date_of_birth,
                phone_number, alternate_phone, email_address, nin, state, lga, ward,
                community_village, residential_address, primary_crop, secondary_crop,
                farm_size_ha, input_distributed, quantity_units, nin_status, id_type,
                id_number, latitude, longitude, enumerator_remarks, photo_status
            )
            VALUES (
                :farmer_id, :registration_date, :agent_id, :farmer_full_name, :gender, :date_of_birth,
                :phone_number, :alternate_phone, :email_address, :nin, :state, :lga, :ward,
                :community_village, :residential_address, :primary_crop, :secondary_crop,
                :farm_size_ha, :input_distributed, :quantity_units, :nin_status, :id_type,
                :id_number, :latitude, :longitude, :enumerator_remarks, :photo_status
            )
        """), {
            "farmer_id": row["Farmer_ID"],
            "registration_date": row["Registration_Date"],
            "agent_id": row["Agent_ID"],
            "farmer_full_name": row["Farmer_Full_Name"],
            "gender": row["Gender"],
            "date_of_birth": row["Date_of_Birth"],
            "phone_number": row["Phone_Number"],
            "alternate_phone": row["Alternate_Phone"],
            "email_address": row["Email_Address"],
            "nin": row["NIN"],
            "state": row["State"],
            "lga": row["LGA"],
            "ward": row["Ward"],
            "community_village": row["Community_Village"],
            "residential_address": row["Residential_Address"],
            "primary_crop": row["Primary_Crop"],
            "secondary_crop": row["Secondary_Crop"],
            "farm_size_ha": row["Farm_Size_Ha"],
            "input_distributed": row["Input_Distributed"],
            "quantity_units": row["Quantity_Units"],
            "nin_status": row["NIN_Status"],
            "id_type": row["ID_Type"],
            "id_number": row["ID_Number"],
            "latitude": row["Latitude"],
            "longitude": row["Longitude"],
            "enumerator_remarks": row["Enumerator_Remarks"],
            "photo_status": row["Photo_Status"]
        })


init_db()
seed_db()


# =========================================================
# 6. SESSION STATE INIT
# =========================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "role" not in st.session_state:
    st.session_state.role = None


# =========================================================
# 7. AUTH SCREEN
# =========================================================
def show_auth():
    logo_path = get_logo_path()

    st.markdown('<div class="auth-card">', unsafe_allow_html=True)

    if logo_path and os.path.exists(logo_path):
        try:
            col1, col2, col3 = st.columns([1, 1.2, 1])
            with col2:
                st.image(logo_path, width=120)
        except Exception:
            st.markdown(
                f"""
                <div style="text-align:center; margin-bottom:10px;">
                    <div style="font-size:20px; font-weight:900; color:{PRIMARY_GREEN};">
                        DataDev Limited
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.markdown(
            f"""
            <div style="text-align:center; margin-bottom:10px;">
                <div style="font-size:20px; font-weight:900; color:{PRIMARY_GREEN};">
                    DataDev Limited
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        """
        <div class="top-title">FEDERAL MINISTRY DIGITAL TRANSFORMATION PROPOSAL</div>
        <div class="main-title">AGROW Nigeria Digital Field Intelligence Platform</div>
        <div class="sub-title">National Farmer Registration, Input Distribution and Monitoring System</div>
        <div class="small-note">Powered by DataDev Limited | Supporting World Bank AGROW Initiative</div>
        """,
        unsafe_allow_html=True
    )

    tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Agent Signup", "🔑 Change Password"])

    with tab1:
        login_user = st.text_input("Username", key="login_username")
        login_pw = st.text_input("Password", type="password", key="login_password")

        if st.button("🚀 Access Portal", use_container_width=True):
            user = fetch_user(login_user)
            if user and user["pw"] == login_pw:
                st.session_state.logged_in = True
                st.session_state.user_id = login_user
                st.session_state.role = user["role"]
                log_action(login_user, "LOGIN", "Successful login")
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with tab2:
        st.markdown("### Agent Registration Details")

        full_name = st.text_input("Full Name", key="signup_full_name")
        phone = st.text_input("Phone Number", key="signup_phone")
        nin = st.text_input("NIN", max_chars=11, key="signup_nin")
        email = st.text_input("Email Address", key="signup_email")

        state_options = sorted(list(NIGERIA_LGA_MAP.keys()))
        state = st.selectbox("State of Coverage", state_options, key="signup_state")
        lga_options = NIGERIA_LGA_MAP.get(state, [])
        lga_coverage = st.selectbox("LGA of Coverage", lga_options if lga_options else ["N/A"], key="signup_lga")

        password = st.text_input("Create Password", type="password", key="signup_password")
        invite_code = st.text_input("Ministry Invite Code", key="signup_invite")

        preview_id = generate_agent_id_db(state)
        st.info(f"Generated Agent Username: {preview_id}")

        if st.button("Create Agent Account", use_container_width=True):
            existing = fetch_user(preview_id)
            if invite_code != "DATADEV":
                st.error("Invalid ministry invite code.")
            elif existing:
                st.error("Generated agent ID already exists. Please try again.")
            elif not full_name.strip():
                st.error("Full name is required.")
            elif not valid_phone(phone):
                st.error("A valid phone number is required.")
            elif not valid_nin(nin):
                st.error("NIN must be exactly 11 digits.")
            elif not valid_email(email):
                st.error("A valid email address is required.")
            elif not password.strip():
                st.error("Password is required.")
            else:
                agent_id = generate_agent_id_db(state)
                insert_user(agent_id, password, "agent", full_name, phone, nin, state, lga_coverage, email)
                log_action(agent_id, "AGENT_CREATED", f"{state} / {lga_coverage}")
                st.success(f"Agent account created successfully. Username: {agent_id}")

    with tab3:
        st.markdown("### Change Existing Password")

        cp_user = st.text_input("Username", key="cp_user")
        cp_old = st.text_input("Current Password", type="password", key="cp_old")
        cp_new = st.text_input("New Password", type="password", key="cp_new")
        cp_confirm = st.text_input("Confirm New Password", type="password", key="cp_confirm")

        if st.button("Update Password", use_container_width=True):
            user = fetch_user(cp_user)
            if not user:
                st.error("User does not exist.")
            elif user["pw"] != cp_old:
                st.error("Current password is incorrect.")
            elif not cp_new.strip():
                st.error("New password cannot be empty.")
            elif len(cp_new) < 6:
                st.error("New password must be at least 6 characters.")
            elif cp_new != cp_confirm:
                st.error("New passwords do not match.")
            else:
                update_user_password(cp_user, cp_new)
                log_action(cp_user, "PASSWORD_CHANGED", "Password updated from login screen")
                st.success("Password updated successfully.")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# 8. APP BODY
# =========================================================
if not st.session_state.logged_in:
    show_auth()

else:
    user_id = st.session_state.user_id
    role = st.session_state.role
    user_meta = fetch_user(user_id) or {}

    logo_path = get_logo_path()

    if logo_path and os.path.exists(logo_path):
        try:
            col1, col2, col3 = st.sidebar.columns([1, 1.3, 1])
            with col2:
                st.image(logo_path, width=95)

            st.sidebar.markdown(
                f"""
                <div style="text-align:center; margin-top:-2px; margin-bottom:14px;">
                    <div style="font-size:17px; font-weight:800; color:{PRIMARY_GREEN};">
                        DataDev Limited
                    </div>
                    <div style="font-size:10px; color:#666;">
                        Digital Systems for Development
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        except Exception:
            st.sidebar.markdown(
                f"""
                <div style="text-align:center; margin-top:10px; margin-bottom:12px;">
                    <div style="font-size:20px; font-weight:900; color:{PRIMARY_GREEN};">
                        DataDev Limited
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.sidebar.markdown(
            f"""
            <div style="text-align:center; margin-top:10px; margin-bottom:12px;">
                <div style="font-size:20px; font-weight:900; color:{PRIMARY_GREEN};">
                    DataDev Limited
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.sidebar.subheader(f"👤 User: {user_id}")
    st.sidebar.write(f"**Role:** {role.title()}")

    if role == "agent":
        st.sidebar.write(f"**Coverage State:** {normalize_state_name(user_meta.get('state', '-'))}")
        st.sidebar.write(f"**Coverage LGA:** {user_meta.get('lga_coverage', '-')}")

    if st.sidebar.button("Logout", use_container_width=True):
        log_action(user_id, "LOGOUT", "User logged out")
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.role = None
        st.rerun()

    with st.sidebar.expander("🔑 Change Password"):
        old_pw = st.text_input("Current Password", type="password", key="side_old_pw")
        new_pw = st.text_input("New Password", type="password", key="side_new_pw")
        confirm_pw = st.text_input("Confirm New Password", type="password", key="side_confirm_pw")

        if st.button("Save New Password", use_container_width=True):
            user = fetch_user(user_id)
            if not user or user["pw"] != old_pw:
                st.error("Current password is incorrect.")
            elif not new_pw.strip():
                st.error("New password cannot be empty.")
            elif len(new_pw) < 6:
                st.error("New password must be at least 6 characters.")
            elif new_pw != confirm_pw:
                st.error("New passwords do not match.")
            else:
                update_user_password(user_id, new_pw)
                log_action(user_id, "PASSWORD_CHANGED", "Password updated from sidebar")
                st.success("Password changed successfully.")

    state_options = sorted(list(NIGERIA_LGA_MAP.keys()))

    if role == "admin":
        selected_state = st.sidebar.selectbox("Region Focus", ["All Nigeria"] + state_options)
    else:
        selected_state = user_meta.get("state", "All Nigeria")
        st.sidebar.info(f"Access restricted to {normalize_state_name(selected_state)}")

    with st.sidebar.expander("📝 Secure Field Registration", expanded=True):
        enable_camera = st.checkbox("Enable Camera")

        st.markdown(
            """
            <div class="sidebar-form-note">
                Complete all farmer identity, location, and support details before syncing the record.
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.form("field_registration_form", clear_on_submit=True):
            st.markdown("### 1. Farmer Bio-Data")
            farmer_full_name = st.text_input("Farmer Full Name")
            gender = st.selectbox("Gender", ["Male", "Female"])
            dob = st.date_input("Date of Birth")
            phone_number = st.text_input("Phone Number")
            alternate_phone = st.text_input("Alternate Phone Number")
            email_address = st.text_input("Email Address")
            nin = st.text_input("NIN", max_chars=11)

            st.markdown("---")
            st.markdown("### 2. Coverage and Location")
            if role == "admin":
                farmer_state = st.selectbox("State", state_options)
            else:
                farmer_state = user_meta.get("state", "")

            lga_list = NIGERIA_LGA_MAP.get(farmer_state, [])
            farmer_lga = st.selectbox("LGA", lga_list if lga_list else ["N/A"])
            ward = st.text_input("Ward")
            community = st.text_input("Community / Village")
            residential_address = st.text_area("Residential Address")

            st.markdown("---")
            st.markdown("### 3. Farm Details")
            primary_crop = st.selectbox(
                "Primary Crop",
                ["Rice", "Maize", "Cassava", "Sorghum", "Soybean", "Groundnut", "Millet"]
            )
            secondary_crop = st.selectbox(
                "Secondary Crop",
                ["None", "Rice", "Maize", "Cassava", "Sorghum", "Soybean", "Groundnut", "Millet"]
            )
            farm_size = st.number_input("Farm Size (Hectares)", min_value=0.1, step=0.1)

            st.markdown("---")
            st.markdown("### 4. Support Delivered")
            input_list = st.multiselect(
                "Inputs Distributed",
                [
                    "Rice Seeds",
                    "Maize Seeds",
                    "Cassava Stems",
                    "Sorghum Seeds",
                    "Soybean Seeds",
                    "Groundnut Seeds",
                    "NPK",
                    "Urea",
                    "Organic Fertilizer",
                    "Herbicide",
                    "Pesticide",
                    "Insecticide",
                    "Sprayer",
                    "Water Pump",
                    "Extension Support"
                ]
            )
            quantity_units = st.number_input("Total Input Units", min_value=1, step=1)

            st.markdown("---")
            st.markdown("### 5. Verification")
            nin_status = st.selectbox("NIN Verification Status", ["Verified", "Pending", "Rejected"])
            id_type = st.selectbox(
                "ID Type",
                ["NIN Slip", "Voter Card", "Driver's License", "National ID Card", "Other"]
            )
            id_number = st.text_input("ID Number")

            st.markdown("---")
            st.markdown("### 6. Geo-tagging and Notes")
            latitude = st.number_input("Latitude", format="%.6f")
            longitude = st.number_input("Longitude", format="%.6f")
            remarks = st.text_area("Enumerator Remarks")
            photo_capture = st.camera_input("Capture Farmer Photo") if enable_camera else None

            submitted = st.form_submit_button("Sync Secure Record", use_container_width=True)

            if submitted:
                if not farmer_full_name.strip():
                    st.error("Farmer full name is required.")
                elif not valid_phone(phone_number):
                    st.error("A valid phone number is required.")
                elif not valid_nin(nin):
                    st.error("NIN must be exactly 11 digits.")
                elif not farmer_lga:
                    st.error("LGA is required.")
                elif len(input_list) == 0:
                    st.error("Please select at least one distributed input.")
                else:
                    now = datetime.now()
                    farmer_id = f"AG-{now.strftime('%Y%m%d%H%M%S')}"

                    row = {
                        "Farmer_ID": farmer_id,
                        "Registration_Date": now.strftime("%Y-%m-%d %H:%M:%S"),
                        "Agent_ID": user_id,
                        "Farmer_Full_Name": farmer_full_name,
                        "Gender": gender,
                        "Date_of_Birth": str(dob),
                        "Phone_Number": phone_number,
                        "Alternate_Phone": alternate_phone,
                        "Email_Address": email_address,
                        "NIN": nin,
                        "State": farmer_state,
                        "LGA": farmer_lga,
                        "Ward": ward,
                        "Community_Village": community,
                        "Residential_Address": residential_address,
                        "Primary_Crop": primary_crop,
                        "Secondary_Crop": secondary_crop,
                        "Farm_Size_Ha": farm_size,
                        "Input_Distributed": ", ".join(input_list),
                        "Quantity_Units": quantity_units,
                        "NIN_Status": nin_status,
                        "ID_Type": id_type,
                        "ID_Number": id_number,
                        "Latitude": latitude,
                        "Longitude": longitude,
                        "Enumerator_Remarks": remarks,
                        "Photo_Status": "Captured" if photo_capture else "No Photo"
                    }

                    insert_farmer(row)
                    log_action(user_id, "FARMER_REGISTERED", farmer_id)
                    st.success("✅ Farmer record synced successfully.")

    st.markdown(
        """
        <div style="text-align:center; margin-bottom: 18px;">
            <div style="font-size:32px; font-weight:900; color:#004B87;">
                AGROW Nigeria Digital Field Intelligence Platform
            </div>
            <div style="font-size:16px; font-weight:700; color:#1B5E20;">
                Ministry Deployment Prototype for National Farmer Registration and Input Monitoring
            </div>
            <div style="font-size:14px; color:#555;">
                Supporting beneficiary verification, field intelligence capture, geospatial tracking and agent coordination
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    df = fetch_farmers()

    if selected_state != "All Nigeria":
        df = df[df["state"] == selected_state]

    if role == "agent":
        df = df[df["agent_id"] == user_id]

    total_beneficiaries = len(df)
    total_verified = len(df[df["nin_status"] == "Verified"]) if not df.empty else 0
    total_land = float(df["farm_size_ha"].sum()) if not df.empty else 0.0
    verification_rate = round((total_verified / total_beneficiaries) * 100, 1) if total_beneficiaries > 0 else 0.0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Beneficiaries", total_beneficiaries)
    m2.metric("Verified NIN", total_verified)
    m3.metric("Land Coverage (Ha)", f"{total_land:.1f}")
    m4.metric("Verification Rate", f"{verification_rate}%")

    st.markdown("### National Monitoring Targets")
    k1, k2, k3, k4 = st.columns(4)
    k1.info("Target Beneficiaries: 1,000,000")
    k2.info("Target States Covered: 36 + FCT")
    k3.info("Target Verification Rate: 95%")
    k4.info("Target Agent Uptime: 99%")

    st.divider()

    tab_a, tab_b, tab_c = st.tabs(["📍 Mapping", "📦 Distribution", "📊 Analytics"])

    with tab_a:
        st.subheader("Geospatial Mapping")
        if not df.empty:
            map_df = df.rename(columns={"latitude": "lat", "longitude": "lon"})
            st.map(map_df, latitude="lat", longitude="lon")
        else:
            st.info("No field data available for mapping.")

    with tab_b:
        st.subheader("Input Breakdown")
        if not df.empty:
            input_counts = df["input_distributed"].str.split(", ").explode().value_counts().reset_index()
            input_counts.columns = ["Input_Type", "Count"]
            pie_fig = px.pie(
                input_counts,
                names="Input_Type",
                values="Count",
                hole=0.5,
                color_discrete_sequence=px.colors.sequential.Greens_r
            )
            st.plotly_chart(pie_fig, use_container_width=True)
        else:
            st.info("No input distribution data available.")

    with tab_c:
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("Crop Distribution")
            if not df.empty:
                crop_counts = df["primary_crop"].value_counts().reset_index()
                crop_counts.columns = ["Primary_Crop", "Count"]
                bar_fig = px.bar(crop_counts, x="Primary_Crop", y="Count")
                st.plotly_chart(bar_fig, use_container_width=True)
            else:
                st.info("No crop data available.")

        with c2:
            st.subheader("NIN Verification Status")
            if not df.empty:
                nin_counts = df["nin_status"].value_counts().reset_index()
                nin_counts.columns = ["NIN_Status", "Count"]
                status_fig = px.bar(nin_counts, x="NIN_Status", y="Count")
                st.plotly_chart(status_fig, use_container_width=True)
            else:
                st.info("No verification data available.")

    st.markdown("### Executive Summary")
    st.success(
        "This prototype demonstrates a ministry-ready digital workflow for farmer enrollment, "
        "beneficiary verification, input tracking, field agent coordination, and geospatial oversight."
    )

    st.subheader("📋 Master Registry Database")
    display_df = df.rename(columns={
        "farmer_id": "Farmer_ID",
        "registration_date": "Registration_Date",
        "agent_id": "Agent_ID",
        "farmer_full_name": "Farmer_Full_Name",
        "gender": "Gender",
        "date_of_birth": "Date_of_Birth",
        "phone_number": "Phone_Number",
        "alternate_phone": "Alternate_Phone",
        "email_address": "Email_Address",
        "nin": "NIN",
        "state": "State",
        "lga": "LGA",
        "ward": "Ward",
        "community_village": "Community_Village",
        "residential_address": "Residential_Address",
        "primary_crop": "Primary_Crop",
        "secondary_crop": "Secondary_Crop",
        "farm_size_ha": "Farm_Size_Ha",
        "input_distributed": "Input_Distributed",
        "quantity_units": "Quantity_Units",
        "nin_status": "NIN_Status",
        "id_type": "ID_Type",
        "id_number": "ID_Number",
        "latitude": "Latitude",
        "longitude": "Longitude",
        "enumerator_remarks": "Enumerator_Remarks",
        "photo_status": "Photo_Status"
    })
    st.dataframe(display_df, use_container_width=True)
    table_to_csv_download(display_df, "agrow_master_registry.csv")

    if role == "admin":
        st.subheader("👥 Registered Agents")
        agent_df = fetch_all_agents()
        if not agent_df.empty:
            agent_df["State"] = agent_df["State"].apply(normalize_state_name)
            st.dataframe(agent_df, use_container_width=True)
            table_to_csv_download(agent_df, "agrow_registered_agents.csv")
        else:
            st.info("No registered agents yet.")

st.markdown(
    '<div class="footer">© DataDev Limited | AGROW Field Intelligence Suite v4.0 | Ministry Deployment Prototype</div>',
    unsafe_allow_html=True
)