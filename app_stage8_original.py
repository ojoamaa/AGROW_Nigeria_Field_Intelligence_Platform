import os
import qrcode
from io import BytesIO
from datetime import datetime
import hmac
import hashlib
import time

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from dotenv import load_dotenv
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFont
import re

from nigeria_lga_data import NIGERIA_LGA_MAP
from core.db import get_connection, init_db
from core.config import AGENT_PHOTO_DIR
from services.log_service import log_action
from services.farmer_service import (
    fetch_farmers,
    farmer_exists_today,
    insert_farmer,
    save_to_offline_queue,
    fetch_offline_queue,
    sync_offline_queue,
)
from services.user_service import (
    fetch_user,
    insert_user,
    update_user_password,
    fetch_all_agents,
    generate_agent_id_db,
)

load_dotenv()
APP_BASE_URL = os.getenv(
    "APP_BASE_URL",
    "https://agrow-nigeria-field-intelligence-platform.onrender.com",
).rstrip("/")


def seed_default_users():
    admin_user = fetch_user("admin")
    if not admin_user:
        insert_user(
            "admin",
            "agrow2026",
            "admin",
            "System Administrator",
            "08000000000",
            "00000000000",
            "FCT",
            "Abuja Municipal",
            "admin@datadev.local"
        )


def seed_demo_agents():
    if not fetch_user("FCT-01"):
        insert_user(
            "FCT-01",
            "agent2026",
            "agent",
            "Demo FCT Agent",
            "08011111111",
            "11111111111",
            "FCT",
            "Abaji",
            "fctagent@datadev.local"
        )

    if not fetch_user("KN-01"):
        insert_user(
            "KN-01",
            "agent2026",
            "agent",
            "Demo Kano Agent",
            "08022222222",
            "22222222222",
            "Kano",
            "Nassarawa",
            "kanoagent@datadev.local"
        )


def seed_demo_data():
    df = fetch_farmers()

    if not df.empty:
        return

    demo_rows = [
        {
            "Farmer_ID": "AG-202604220001",
            "Registration_Date": "2026-04-22 08:15:00",
            "Agent_ID": "FCT-01",
            "Farmer_Full_Name": "Musa Ibrahim",
            "Gender": "Male",
            "Date_of_Birth": "1988-05-12",
            "Phone_Number": "08031234567",
            "Alternate_Phone": "08141234567",
            "Email_Address": "musa@example.com",
            "NIN": "12345678901",
            "State": "FCT",
            "LGA": "Abaji",
            "Ward": "Ward 1",
            "Community_Village": "Yaba",
            "Residential_Address": "Abaji, FCT",
            "Primary_Crop": "Rice",
            "Secondary_Crop": "Maize",
            "Farm_Size_Ha": 3.5,
            "Input_Distributed": "Rice Seeds, NPK, Urea",
            "Quantity_Units": 3,
            "NIN_Status": "Verified",
            "ID_Type": "NIN Slip",
            "ID_Number": "NIN-001",
            "Latitude": 8.4732,
            "Longitude": 6.9421,
            "Enumerator_Remarks": "Demo registered farmer",
            "Photo_Path": "",
            "Photo_Status": "No Photo",
        },
        {
            "Farmer_ID": "AG-202604220002",
            "Registration_Date": "2026-04-22 08:35:00",
            "Agent_ID": "FCT-01",
            "Farmer_Full_Name": "Aisha Bello",
            "Gender": "Female",
            "Date_of_Birth": "1992-09-18",
            "Phone_Number": "08039876543",
            "Alternate_Phone": "",
            "Email_Address": "aisha@example.com",
            "NIN": "12345678902",
            "State": "FCT",
            "LGA": "Gwagwalada",
            "Ward": "Ward 2",
            "Community_Village": "Paiko",
            "Residential_Address": "Gwagwalada, FCT",
            "Primary_Crop": "Maize",
            "Secondary_Crop": "Soybean",
            "Farm_Size_Ha": 2.0,
            "Input_Distributed": "Maize Seeds, Organic Fertilizer",
            "Quantity_Units": 2,
            "NIN_Status": "Pending",
            "ID_Type": "Voter Card",
            "ID_Number": "PVC-002",
            "Latitude": 8.9390,
            "Longitude": 7.0819,
            "Enumerator_Remarks": "Awaiting NIN verification",
            "Photo_Path": "",
            "Photo_Status": "No Photo",
        },
        {
            "Farmer_ID": "AG-202604220003",
            "Registration_Date": "2026-04-22 09:05:00",
            "Agent_ID": "KN-01",
            "Farmer_Full_Name": "Sani Yakubu",
            "Gender": "Male",
            "Date_of_Birth": "1985-03-03",
            "Phone_Number": "08052345678",
            "Alternate_Phone": "",
            "Email_Address": "sani@example.com",
            "NIN": "12345678903",
            "State": "Kano",
            "LGA": "Nassarawa",
            "Ward": "Ward 3",
            "Community_Village": "Tudun Wada",
            "Residential_Address": "Kano",
            "Primary_Crop": "Rice",
            "Secondary_Crop": "Groundnut",
            "Farm_Size_Ha": 4.2,
            "Input_Distributed": "Rice Seeds, NPK, Herbicide, Sprayer",
            "Quantity_Units": 4,
            "NIN_Status": "Verified",
            "ID_Type": "Driver's License",
            "ID_Number": "DL-003",
            "Latitude": 11.9790,
            "Longitude": 8.5214,
            "Enumerator_Remarks": "Demo record from Kano cluster",
            "Photo_Path": "",
            "Photo_Status": "No Photo",
        },
    ]

    for row in demo_rows:
        insert_farmer(row)


init_db()
seed_default_users()
seed_demo_agents()
seed_demo_data()

if "farmer_form_version" not in st.session_state:
    st.session_state["farmer_form_version"] = 0

form_v = st.session_state["farmer_form_version"]
# =========================================================
# 1. PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="AGROW — Agricultural Geographic Registration & Operations Workspace",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================================================
# 2. ENV / DATABASE
# =========================================================


# =========================================================
# 3. BRANDING / COLORS
# =========================================================
PRIMARY_GREEN = "#1B5E20"
OFFICIAL_BLUE = "#004B87"
LIGHT_BG = "#F8F9FA"
TEXT_GREY = "#5F6368"

LOGO_CANDIDATES = [
    "proposal_logo.png",
    "logo.png",
    "static/proposal_logo.png",
    "static/logo.png",
]

# =========================================================
# 4. GLOBAL STYLING
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
        overflow-y: auto !important;
    }}

    section[data-testid="stSidebar"] {{
        width: 320px !important;
    }}

    @media (max-width: 768px) {{
        section[data-testid="stSidebar"] {{
            width: 68vw !important;
            min-width: 68vw !important;
            max-width: 68vw !important;
        }}

        .block-container {{
            padding-top: 1rem !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
            padding-bottom: 1rem !important;
        }}

        .main-title {{
            font-size: 16px !important;
            line-height: 1.25 !important;
            margin-bottom: 2px !important;
        }}

        .sub-title {{
            font-size: 10px !important;
            line-height: 1.3 !important;
            margin-bottom: 4px !important;
        }}

        .small-note {{
            font-size: 9px !important;
            line-height: 1.3 !important;
            margin-bottom: 8px !important;
        }}

        .top-title {{
            font-size: 11px !important;
            line-height: 1.2 !important;
        }}

        [data-testid="stMetric"] {{
            padding: 10px !important;
            border-radius: 10px !important;
        }}

        [data-testid="stMetricValue"] {{
            font-size: 20px !important;
        }}

        .footer {{
            display: none !important;
        }}

        .stButton > button,
        .stDownloadButton > button {{
            width: 100% !important;
            min-height: 44px !important;
            font-size: 14px !important;
        }}

        .stTextInput input,
        .stNumberInput input,
        .stDateInput input,
        .stTextArea textarea {{
            font-size: 14px !important;
        }}

        .auth-card {{
            max-width: 100% !important;
            padding: 12px !important;
            border-radius: 10px !important;
            margin-top: 6px !important;
        }}
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

    label,
    .stSelectbox label,
    .stMultiSelect label,
    .stTextInput label,
    .stDateInput label,
    .stNumberInput label,
    .stTextArea label {{
        font-weight: 700 !important;
        color: #1f1f1f !important;
    }}

    .stTextInput input,
    .stNumberInput input,
    .stDateInput input,
    .stTextArea textarea {{
        border: 1.5px solid #D0D7DE !important;
        border-radius: 10px !important;
        background-color: #FFFFFF !important;
        color: #111111 !important;
        -webkit-text-fill-color: #111111 !important;
        caret-color: #111111 !important;
        padding: 0.65rem !important;
        font-size: 16px !important;
        opacity: 1 !important;
    }}

    div[data-baseweb="input"] input {{
        color: #111111 !important;
        -webkit-text-fill-color: #111111 !important;
        caret-color: #111111 !important;
        background-color: #FFFFFF !important;
    }}

    textarea {{
        color: #111111 !important;
        -webkit-text-fill-color: #111111 !important;
        caret-color: #111111 !important;
        background-color: #FFFFFF !important;
    }}

    input::placeholder,
    textarea::placeholder {{
        color: #777777 !important;
        opacity: 1 !important;
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

    .stButton > button,
    .stDownloadButton > button {{
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
    unsafe_allow_html=True,
)

def generate_qr_code(url):
    qr = qrcode.make(url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", str(value or "").strip())
    return cleaned.strip("_") or "farmer"

def build_farmer_qr_identity_image(farmer, verification_url: str):
    width, height = 900, 1100
    card = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(card)
    font = ImageFont.load_default()
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(verification_url); qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_img.thumbnail((620, 620))
    draw.rectangle((20, 20, width-20, height-20), outline=(0,83,141), width=8)
    details = [
        "AGROW FARMER IDENTIFICATION QR",
        f"Name: {farmer.get('farmer_full_name', '-')}",
        f"Farmer ID: {farmer.get('farmer_id', '-')}",
        f"State: {normalize_state_name(farmer.get('state', '-'))}",
        f"LGA: {farmer.get('lga', '-')}",
        f"Community: {farmer.get('community', '-')}",
        f"Primary Crop: {farmer.get('primary_crop', '-')}",
    ]
    y=55
    for line in details:
        draw.text((55,y), line, fill=(0,83,141) if y==55 else "black", font=font); y += 40
    card.paste(qr_img, ((width-qr_img.width)//2, 360))
    draw.text((55,1020), "Scan to verify this farmer's AGROW record.", fill=(55,55,55), font=font)
    out=BytesIO(); card.save(out, format="PNG"); out.seek(0); return out

STATE_GPS_ENVELOPES = {
    "Jigawa": (10.5, 13.2, 8.0, 10.7),
    "Kano": (10.4, 12.7, 7.5, 9.7),
    "Kaduna": (9.0, 11.8, 6.0, 9.0),
    "FCT": (8.2, 9.4, 6.6, 7.8),
    "Federal Capital Territory": (8.2, 9.4, 6.6, 7.8),
}

def gps_matches_assigned_state(state_name, latitude, longitude):
    bounds = STATE_GPS_ENVELOPES.get(str(state_name or "").strip())
    if not bounds: return None
    a,b,c,d = bounds
    return a <= latitude <= b and c <= longitude <= d

QR_SECRET_KEY = os.getenv("QR_SECRET_KEY", "change-this-secret-key")

def generate_qr_signature(farmer_id):
    message = farmer_id.encode()
    secret = QR_SECRET_KEY.encode()
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def verify_qr_signature(farmer_id, sig):
    expected_sig = generate_qr_signature(farmer_id)
    return hmac.compare_digest(expected_sig, sig)

# =========================================================
# 5. HELPERS
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

def save_uploaded_photo(photo_file, folder: str, filename: str) -> str:
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, filename)

    with open(file_path, "wb") as f:
        f.write(photo_file.getbuffer())

    return file_path

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
        "Zamfara": "ZF",
    }
    return special_map.get(state_name, state_name[:2].upper())


def valid_phone(phone):
    return phone.isdigit() and 10 <= len(phone) <= 11


def valid_nin(nin: str) -> bool:
    return nin.isdigit() and len(nin) == 11

def valid_id_number(id_number: str) -> bool:
    cleaned = id_number.strip()
    return 1 <= len(cleaned) <= 20

def valid_email(email: str) -> bool:
    return "@" in email and "." in email


def table_to_csv_download(df: pd.DataFrame, filename: str):
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"⬇️ Download {filename}",
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        width="stretch",
    )


def table_to_excel_download(df: pd.DataFrame, filename: str):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Report")

    output.seek(0)

    st.download_button(
        label=f"⬇️ Download {filename}",
        data=output.getvalue(),
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )

def is_db_available() -> bool:
    try:
        conn = get_connection()
        conn.execute("SELECT 1")
        conn.close()
        return True
    except Exception:
        return False
    
def generate_farmer_qr_code(farmer_id: str):
    verification_url = f"{APP_BASE_URL}?farmer_id={farmer_id}"

    qr = qrcode.make(verification_url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer

def generate_farmer_id_card_pdf(selected_row, photo_path, logo_path=None):
    buffer = BytesIO()

    # Standard CR80 ID card size
    card_width = 85.6 * mm
    card_height = 54 * mm

    c = canvas.Canvas(buffer, pagesize=(card_width, card_height))
    width, height = card_width, card_height

    padding = 4 * mm

    # Outer border
    c.setStrokeColorRGB(0.12, 0.35, 0.18)
    c.setLineWidth(1)
    c.roundRect(1.5, 1.5, width - 3, height - 3, 3, stroke=1, fill=0)

    # Header bar
    header_h = 10 * mm
    c.setFillColorRGB(0.0, 0.29, 0.53)
    c.roundRect(1.5, height - header_h - 1.5, width - 3, header_h, 3, stroke=0, fill=1)

    # Logo
    if logo_path and os.path.exists(logo_path):
        try:
            c.drawImage(
                logo_path,
                padding,
                height - 8.8 * mm,
                width=7 * mm,
                height=7 * mm,
                preserveAspectRatio=True,
                mask='auto'
            )
        except Exception:
            pass

    # Header title
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawCentredString(width / 2, height - 6.8 * mm, "AGROW FARMER ID CARD")

    # Photo box
    photo_x = padding
    photo_y = 14 * mm
    photo_w = 23 * mm
    photo_h = 18 * mm

    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.rect(photo_x, photo_y, photo_w, photo_h, stroke=1, fill=0)

    if photo_path and os.path.exists(photo_path):
        try:
            c.drawImage(
                photo_path,
                photo_x + 1,
                photo_y + 1,
                width=photo_w - 2,
                height=photo_h - 2,
                preserveAspectRatio=True,
                mask='auto'
            )
        except Exception:
            c.setFont("Helvetica", 6)
            c.drawString(photo_x + 3, photo_y + photo_h / 2, "No Photo")
    else:
        c.setFont("Helvetica", 6)
        c.drawString(photo_x + 3, photo_y + photo_h / 2, "No Photo")

    # Farmer text details
    text_x = photo_x + photo_w + 4 * mm
    text_y = height - 15 * mm

    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 6.7)

    line_gap = 4.2 * mm
    c.drawString(text_x, text_y, f"Name: {selected_row.get('farmer_full_name', '-')}")
    c.drawString(text_x, text_y - line_gap, f"Farmer ID: {selected_row.get('farmer_id', '-')}")
    c.drawString(text_x, text_y - (2 * line_gap), f"State: {normalize_state_name(selected_row.get('state', '-'))}")
    c.drawString(text_x, text_y - (3 * line_gap), f"LGA: {selected_row.get('lga', '-')}")
    c.drawString(text_x, text_y - (4 * line_gap), f"Phone: {selected_row.get('phone_number', '-')}")
    c.drawString(text_x, text_y - (5 * line_gap), f"Crop: {selected_row.get('primary_crop', '-')}")

    # QR content
    def generate_farmer_id_card_pdf(selected_row):

     farmer_id_value = selected_row.get("farmer_id", "")

    farmer_id_value = selected_row.get("farmer_id", selected_row.get("Farmer_ID", ""))
    sig = generate_qr_signature(farmer_id_value)

    verification_url = f"{APP_BASE_URL}?farmer_id={farmer_id_value}&sig={sig}"

    qr = qrcode.make(verification_url)
    qr_buffer = BytesIO()
    qr.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    # continue PDF drawing...

    qr_size = 16 * mm
    qr_x = width - qr_size - padding
    qr_y = 14 * mm

    c.drawImage(
        ImageReader(qr_buffer),
        qr_x,
        qr_y,
        width=qr_size,
        height=qr_size,
        mask='auto'
    )

  # Footer / Disclaimer Section
    footer_y = 6 * mm

    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.setFont("Helvetica", 5.5)
    c.drawString(padding, footer_y + 3 * mm, f"Issue Date: {datetime.now().strftime('%Y-%m-%d')}")

    c.setFont("Helvetica-Bold", 5.5)
    c.drawString(padding, footer_y, "Valid for AGROW program identification only")

    c.setFont("Helvetica", 5)
    c.drawString(padding, footer_y - 2.5 * mm, "Not a National ID. Subject to verification.")

    c.setFont("Helvetica-Oblique", 5)
    c.drawRightString(width - padding, footer_y + 2.5 * mm, "Issued by DataDev Limited")

    sig_x1 = width - 30 * mm
    sig_x2 = width - 8 * mm
    sig_y = footer_y - 1 * mm

    c.setStrokeColorRGB(0.4, 0.4, 0.4)
    c.line(sig_x1, sig_y, sig_x2, sig_y)

    c.setFont("Helvetica", 5)
    c.drawCentredString((sig_x1 + sig_x2) / 2, sig_y - 3 * mm, "Authorized Officer")

    c.save()
    buffer.seek(0)
    return buffer

# =========================================================
# 7. SESSION STATE INIT
# =========================================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "user_id" not in st.session_state:
    st.session_state["user_id"] = None

if "role" not in st.session_state:
    st.session_state["role"] = None

if "farmer_form_version" not in st.session_state:
    st.session_state["farmer_form_version"] = 0

if "post_signup_redirect" not in st.session_state:
    st.session_state["post_signup_redirect"] = False

if "last_created_agent_id" not in st.session_state:
    st.session_state["last_created_agent_id"] = ""

# online / offline + sync monitor
if "db_online" not in st.session_state:
    st.session_state["db_online"] = True

if "last_auto_sync" not in st.session_state:
    st.session_state["last_auto_sync"] = None

if "last_sync_message" not in st.session_state:
    st.session_state["last_sync_message"] = ""

if "last_sync_status" not in st.session_state:
    st.session_state["last_sync_status"] = ""

if "auto_sync_ran" not in st.session_state:
    st.session_state["auto_sync_ran"] = False
# =========================================================
# 8. AUTH SCREEN
# =========================================================
def show_auth():
    logo_path = get_logo_path()

    st.markdown('<div class="auth-card">', unsafe_allow_html=True)

    if logo_path and os.path.exists(logo_path):
      try:
          col1, col2 = st.columns([1, 6])
          with col1:
            st.image(logo_path, width=90)
      except Exception:
            st.markdown(
                f"""
                <div style="text-align:center; margin-bottom:10px;">
                    <div style="font-size:20px; font-weight:900; color:{PRIMARY_GREEN};">
                        DataDev Limited
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
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
            unsafe_allow_html=True,
        )

    st.markdown(
    """
    <div class="top-title">FEDERAL MINISTRY DIGITAL TRANSFORMATION PROPOSAL</div>
    <div class="main-title">AGROW — Agricultural Geographic Registration & Operations Workspace</div>
    <div class="sub-title">Farmer Enumeration, Geographic Intelligence, Verification and Field Operations</div>
    <div class="small-note">Powered by DataDev Limited | Supporting World Bank AGROW Initiative</div>
    """,
    unsafe_allow_html=True,
)
    if st.session_state.get("post_signup_redirect", False):
        created_agent_id = st.session_state.get("last_created_agent_id", "")
        st.success(f"Agent account created successfully. Username: {created_agent_id}. Use this username and the password you created to log in.")
        st.session_state["post_signup_redirect"] = False

    st.markdown("### Public Farmer Verification")
    st.caption("Farmers, field agents and input-distribution teams can confirm an enumeration record using a Farmer ID, phone number or the QR code printed on an AGROW Farmer ID card.")
    show_public_farmer_verification(compact=True)
    st.divider()
    st.markdown("### Secure Workspace Access")

    tab1, tab2, tab3 = st.tabs(["Login", "Agent Signup", "Password"])

    with tab1:
        default_username = st.session_state.get("prefill_login_username", "")

        login_user = st.text_input(
            "Username",
            value=default_username,
            key="login_username"
        )


        login_pw = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button("🚀 Access Portal", width="stretch"):
            normalized_login_user = str(login_user or "").strip().upper()
            normalized_login_pw = str(login_pw or "").strip()
            user = fetch_user(normalized_login_user)

            if user and str(user["pw"]).strip() == normalized_login_pw:
                st.session_state.logged_in = True
                st.session_state.user_id = normalized_login_user
                st.session_state.role = user["role"]
                log_action(normalized_login_user, "LOGIN", "Successful login")
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with tab2:
        st.markdown("### Agent Registration Details")

        full_name = st.text_input("Full Name", key="signup_full_name")
        phone = st.text_input("Phone Number", max_chars=11, key="signup_phone")
        nin = st.text_input("NIN", max_chars=11, key="signup_nin")
        email = st.text_input("Email Address", key="signup_email")

        state_options = sorted(list(NIGERIA_LGA_MAP.keys()))
        state = st.selectbox("State of Coverage", state_options, key="signup_state")
        lga_options = NIGERIA_LGA_MAP.get(state, [])
        lga_coverage = st.selectbox(
            "LGA of Coverage",
            lga_options if lga_options else ["N/A"],
            key="signup_lga",
        )

        password = st.text_input("Create Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")
        invite_code = st.text_input("Ministry Invite Code", key="signup_invite")

        st.markdown("### Agent Photo Capture")
        signup_enable_camera = st.checkbox("Enable Agent Camera", key="signup_enable_camera")
        signup_photo = st.camera_input("Capture Agent Photo", key="signup_photo") if signup_enable_camera else None

        state_prefix = get_state_prefix(state)
        preview_id = generate_agent_id_db(state_prefix)
        st.info(f"Generated Agent Username: {preview_id}")

        if st.button("Create Agent Account", width="stretch"):
            normalized_invite_code = str(invite_code or "").strip().upper()
            ministry_invite_code = os.getenv("MINISTRY_INVITE_CODE", "DATADEV").strip().upper()
            existing = fetch_user(preview_id)

            if normalized_invite_code != ministry_invite_code:
                st.error("Invalid ministry invite code.")
            elif existing:
                st.error("Generated agent ID already exists. Please try again.")
            elif not full_name.strip():
                st.error("Full name is required.")
            elif not valid_phone(phone):
                st.error("Phone Number must be exactly 11 digits.")
            elif not valid_nin(nin):
                st.error("NIN must be exactly 11 digits.")
            elif not valid_email(email):
                st.error("A valid email address is required.")
            elif not password.strip():
                st.error("Password is required.")
            elif len(password.strip()) < 6:
                st.error("Password must be at least 6 characters.")
            elif password.strip() != confirm_password.strip():
                st.error("Passwords do not match.")
            elif not signup_enable_camera or signup_photo is None:
                st.error("Agent photo capture is required.")
            else:
                agent_id = preview_id
                clean_password = password.strip()
                insert_user(agent_id, clean_password, "agent", full_name, phone, nin, state, lga_coverage, email)
                saved_user = fetch_user(agent_id)
                if not saved_user or str(saved_user["pw"]).strip() != clean_password:
                    st.error("The account could not be verified after registration. Please try again.")
                    st.stop()
                save_uploaded_photo(signup_photo, str(AGENT_PHOTO_DIR), f"{agent_id}.png")
                log_action(agent_id, "AGENT_CREATED", f"{state} / {lga_coverage}")

                st.session_state["prefill_login_username"] = agent_id
                st.session_state["last_created_agent_id"] = agent_id
                st.session_state["post_signup_redirect"] = True

                signup_keys = [
                    "signup_full_name",
                    "signup_phone",
                    "signup_nin",
                    "signup_email",
                    "signup_state",
                    "signup_lga",
                    "signup_password",
                    "signup_confirm_password",
                    "signup_invite",
                    "signup_enable_camera",
                    "signup_photo",
                ]

                for k in signup_keys:
                    if k in st.session_state:
                        del st.session_state[k]

                st.rerun()

    with tab3:
        st.markdown("### Change Existing Password")

        cp_user = st.text_input("Username", key="cp_user")
        cp_old = st.text_input("Current Password", type="password", key="cp_old")
        cp_new = st.text_input("New Password", type="password", key="cp_new")
        cp_confirm = st.text_input("Confirm New Password", type="password", key="cp_confirm")

        if st.button("Update Password", width="stretch"):
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

def generate_qr_code(url):
    qr = qrcode.make(url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def show_public_farmer_verification(compact=False, key_prefix="public"):
    if not compact:
        st.markdown("### 🔎 Farmer Verification Portal")
    st.info("Scan an AGROW Farmer ID QR code or search using Farmer ID / Phone Number.")

    query_params = st.query_params
    farmer_id_lookup = query_params.get("farmer_id", "")
    sig = query_params.get("sig", "")
    phone_lookup = ""

    if farmer_id_lookup and sig:
        if not verify_qr_signature(farmer_id_lookup, sig):
            st.error("❌ Invalid or tampered QR code.")
            return

    if not farmer_id_lookup:
        col1, col2 = st.columns(2)

        with col1:
            farmer_id_lookup = st.text_input(
                "Enter Farmer ID",
                placeholder="e.g. AG-20260416074143",
                key=f"{key_prefix}_farmer_id_lookup",
            )

        with col2:
            phone_lookup = st.text_input(
                "Enter Phone Number",
                placeholder="e.g. 08123456789",
                key=f"{key_prefix}_phone_lookup",
            )

        search_col, clear_col = st.columns([4, 1])
        with search_col:
            search_clicked = st.button("🔎 Search Farmer Record", key=f"{key_prefix}_farmer_search", width="stretch", type="primary")
        with clear_col:
            clear_clicked = st.button("Clear", key=f"{key_prefix}_farmer_clear", width="stretch")
        if clear_clicked:
            st.session_state.pop(f"{key_prefix}_farmer_id_lookup", None)
            st.session_state.pop(f"{key_prefix}_phone_lookup", None)
            st.rerun()
        if not search_clicked:
            return

        if not farmer_id_lookup.strip() and not phone_lookup.strip():
            st.warning("Enter Farmer ID or Phone Number.")
            return

    df = fetch_farmers()

    if df.empty:
        st.warning("No farmer records available.")
        return

    record = df.copy()

    if farmer_id_lookup.strip():
        record = record[
            record["farmer_id"].astype(str).str.strip().str.upper()
            == farmer_id_lookup.strip().upper()
        ]
    elif phone_lookup.strip():
        record = record[
            record["phone_number"].astype(str).str.strip()
            == phone_lookup.strip()
        ]

    if record.empty:
        st.error("❌ INVALID FARMER RECORD")
        return

    farmer = record.iloc[0]
    photo_path = farmer.get("photo_path", "")

    st.success("✅ Farmer Verified")

    col1, col2 = st.columns([1, 2])

    with col1:
        if photo_path and os.path.exists(photo_path):
            st.image(photo_path, width=220)
        else:
            st.warning("No photo available.")

    with col2:
        st.markdown(f"""
**Farmer ID:** {farmer.get('farmer_id', '-')}  
**Name:** {farmer.get('farmer_full_name', '-')}  
**Phone:** {farmer.get('phone_number', '-')}  
**State:** {normalize_state_name(farmer.get('state', '-'))}  
**LGA:** {farmer.get('lga', '-')}  
**Crop:** {farmer.get('primary_crop', '-')}  
**NIN Status:** {farmer.get('nin_status', '-')}  
        """)

    pdf_file = generate_farmer_id_card_pdf(
        selected_row=farmer,
        photo_path=photo_path,
        logo_path=get_logo_path(),
    )

    st.download_button(
        label="⬇️ Download Farmer ID Card",
        data=pdf_file.getvalue(),
        file_name=f"{safe_filename(farmer.get('farmer_full_name', 'Farmer'))}_{safe_filename(farmer.get('farmer_id', 'farmer'))}_ID_Card.pdf",
        mime="application/pdf",
        width="stretch",
    )

# =========================================================
# 9. APP BODY
# =========================================================
if not st.session_state.logged_in:
    show_auth()

else:
    user_id = st.session_state.user_id
    role = st.session_state.role
    user_meta = fetch_user(user_id) or {}

    # continue dashboard here...

    # logged-in dashboard continues here

    if not user_id or not role:
     st.session_state.logged_in = False
     st.session_state.user_id = None
     st.session_state.role = None
     st.warning("Session expired. Please log in again.")
     show_auth()
     st.stop()

    def is_db_available():
        try:
            conn = get_connection()
            conn.close()
            return True
        except Exception:
            return False

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
                unsafe_allow_html=True,
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
                unsafe_allow_html=True,
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
            unsafe_allow_html=True,
        )

    st.sidebar.subheader(f"👤 User: {user_id or 'Guest'}")
    st.sidebar.write(f"**Role:** {(role or 'Guest').title()}")

    if role == "agent":
        st.sidebar.write(f"**Coverage State:** {normalize_state_name(user_meta.get('state', '-'))}")
        st.sidebar.write(f"**Coverage LGA:** {user_meta.get('lga_coverage', '-')}")

    if st.sidebar.button("Logout", width="stretch"):
        log_action(user_id, "LOGOUT", "User logged out")
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.role = None
        st.rerun()

    with st.sidebar.expander("🔑 Change Password"):
        old_pw = st.text_input("Current Password", type="password", key="side_old_pw")
        new_pw = st.text_input("New Password", type="password", key="side_new_pw")
        confirm_pw = st.text_input("Confirm New Password", type="password", key="side_confirm_pw")

        if st.button("Save New Password", width="stretch"):
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

    st.markdown(
        """
        <div style="text-align:center; margin-bottom:18px; padding: 0 10px;">
            <div style="font-size:clamp(22px, 4vw, 32px); font-weight:900; color:#004B87; line-height:1.2;">
                AGROW — Agricultural Geographic Registration & Operations Workspace
            </div>
            <div style="font-size:clamp(13px, 2.2vw, 16px); font-weight:700; color:#1B5E20; margin-top:6px; line-height:1.4;">
                Ministry Deployment Prototype for National Farmer Registration and Input Monitoring
            </div>
            <div style="font-size:clamp(11px, 1.8vw, 14px); color:#555; margin-top:6px; line-height:1.5;">
                Connecting verified farmer records, geographic field intelligence, input distribution and accountable agricultural operations
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info("⚠️ Demo Mode: Sample data displayed for presentation purposes")
    st.caption("Powered by DataDev Limited | National Digital Agriculture Prototype")

    if is_db_available():
        st.success("🟢 ONLINE MODE: Data syncing to central database")
    else:
        st.warning("🟡 OFFLINE MODE: Data stored locally and will sync later")

    if role == "admin":
        st.markdown("### 🌐 AGROW Platform Access")

        qr_img = generate_qr_code(APP_BASE_URL)

        qr_col1, qr_col2 = st.columns([1, 4])

        with qr_col1:
            st.image(qr_img, width=150)

        with qr_col2:
            st.caption("Scan this platform QR to open the public verification and secure workspace landing page on another device.")
            st.download_button(
                label="⬇️ Download QR Code",
                data=qr_img.getvalue(),
                file_name="agrow_platform_qr.png",
                mime="image/png",
                width="content",
            )

        st.divider()

    st.caption(f"Last sync check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # -------------------------
    # Dashboard data
    # -------------------------
    df = fetch_farmers()

    if selected_state != "All Nigeria" and not df.empty:
        df = df[df["state"] == selected_state]

    if role == "agent" and not df.empty:
        df = df[df["agent_id"] == user_id]

    total_beneficiaries = len(df)
    total_verified = len(df[df["nin_status"] == "Verified"]) if not df.empty else 0
    total_land = float(df["farm_size_ha"].sum()) if not df.empty else 0.0
    verification_rate = round((total_verified / total_beneficiaries) * 100, 1) if total_beneficiaries > 0 else 0.0

    # =========================================================
    # TAB LAYOUT
    # =========================================================
    tab_dashboard, tab_farmer_registration, tab_distribution, tab_verification, tab_analytics = st.tabs(
        ["📊 Dashboard", "📝 Farmer Registration", "📦 Distribution", "🔎 Farmer Verification", "📈 Analytics"]
    )

    # =========================================================
    # TAB 1: DASHBOARD
    # =========================================================
    with tab_dashboard:
        total_agents = len(fetch_all_agents()) if role == "admin" else 0

        registrations_today = 0
        pending_nin = 0
        rejected_nin = 0
        captured_photos = 0

        if not df.empty:
            today_str = datetime.now().strftime("%Y-%m-%d")
            registrations_today = len(
                df[df["registration_date"].astype(str).str.startswith(today_str)]
            )
            pending_nin = len(df[df["nin_status"] == "Pending"])
            rejected_nin = len(df[df["nin_status"] == "Rejected"])
            captured_photos = len(df[df["photo_status"] == "Captured"])

        st.markdown("### National Performance Overview")

        row1 = st.columns(4)
        row1[0].metric("Beneficiaries", total_beneficiaries)
        row1[1].metric("Verified NIN", total_verified)
        row1[2].metric("Land Coverage (Ha)", f"{total_land:.1f}")
        row1[3].metric("Verification Rate", f"{verification_rate}%")

        row2 = st.columns(4)
        row2[0].metric("Registrations Today", registrations_today)
        row2[1].metric("Pending NIN", pending_nin)
        row2[2].metric("Rejected NIN", rejected_nin)
        row2[3].metric("Captured Photos", captured_photos)

        if role == "admin":
            st.markdown("### Admin Monitoring Snapshot")
            a1, a2 = st.columns(2)
            a3, a4 = st.columns(2)

            a1.info(f"Registered Agents: {total_agents}")
            a2.info("Target Beneficiaries: 1,000,000")
            a3.info("Target States Covered: 36 + FCT")
            a4.info("Target Verification Rate: 95%")
        else:
            st.markdown("### Field Agent Monitoring Snapshot")
            st.info(f"Coverage State: {normalize_state_name(user_meta.get('state', '-'))}")
            st.info(f"Coverage LGA: {user_meta.get('lga_coverage', '-')}")
            st.info("Target Agent Uptime: 99%")

        st.divider()

        st.subheader("Geospatial Mapping")
        if not df.empty:
            map_df = df.rename(columns={"latitude": "lat", "longitude": "lon"})
            st.map(map_df)
        else:
            st.info("No field data available for mapping.")

        st.divider()

        c1, c2 = st.columns(2)

        with c1:
            st.subheader("Registrations by State")
            if not df.empty:
                state_counts = df["state"].value_counts().reset_index()
                state_counts.columns = ["State", "Count"]
                state_counts["State"] = state_counts["State"].apply(normalize_state_name)
                st.plotly_chart(px.bar(state_counts, x="State", y="Count"), width="stretch")
            else:
                st.info("No state data")

        with c2:
            st.subheader("Registrations by Agent")
            if not df.empty:
                agent_counts = df["agent_id"].value_counts().reset_index()
                agent_counts.columns = ["Agent_ID", "Count"]
                st.plotly_chart(px.bar(agent_counts, x="Agent_ID", y="Count"), width="stretch")
            else:
                st.info("No agent data")

        st.divider()

        d1, d2 = st.columns(2)

        with d1:
            st.subheader("NIN Status Distribution")
            if not df.empty:
                nin_counts = df["nin_status"].value_counts().reset_index()
                nin_counts.columns = ["NIN_Status", "Count"]
                st.plotly_chart(
                    px.pie(nin_counts, names="NIN_Status", values="Count", hole=0.45),
                    width="stretch",
                )
            else:
                st.info("No NIN data")

        with d2:
            st.subheader("Photo Capture Status")
            if not df.empty:
                photo_counts = df["photo_status"].value_counts().reset_index()
                photo_counts.columns = ["Photo_Status", "Count"]
                st.plotly_chart(
                    px.pie(photo_counts, names="Photo_Status", values="Count", hole=0.45),
                    width="stretch",
                )
            else:
                st.info("No photo data")

        st.divider()

        st.subheader("Input Distribution Summary")
        if not df.empty:
            input_counts = df["input_distributed"].fillna("").str.split(", ").explode()
            input_counts = input_counts[input_counts != ""].value_counts().reset_index()
            input_counts.columns = ["Input_Type", "Count"]
            st.plotly_chart(px.bar(input_counts, x="Input_Type", y="Count"), width="stretch")
        else:
            st.info("No input data")

        st.divider()

        st.subheader("Recent Farmer Registrations")
        if not df.empty:
            recent_df = df.sort_values(by="registration_date", ascending=False).head(10)
            st.dataframe(recent_df, width="stretch")
        else:
            st.info("No farmer records yet")

        st.divider()

        st.markdown("### Offline Queue Monitor")
        queue_df = fetch_offline_queue()

        pending_count = len(queue_df[queue_df["sync_status"] == "PENDING"]) if not queue_df.empty else 0
        failed_count = len(queue_df[queue_df["sync_status"] == "FAILED"]) if not queue_df.empty else 0
        synced_count = len(queue_df[queue_df["sync_status"] == "SYNCED"]) if not queue_df.empty else 0

        q1, q2, q3 = st.columns(3)
        q1.metric("Pending", pending_count)
        q2.metric("Synced", synced_count)
        q3.metric("Failed", failed_count)

        if st.button("Sync Pending Records", width="stretch"):
            synced, failed = sync_offline_queue()
            st.success(f"{synced} synced")
            if failed:
                st.warning(f"{failed} failed")
            st.rerun()

        if not queue_df.empty:
            st.dataframe(queue_df, width="stretch")
        else:
            st.info("No queue records")

    # =========================================================
    # TAB 2: REGISTER FARMER
    # =========================================================
    @st.fragment
    def render_farmer_registration():
        st.info("Complete each section carefully and click 'Sync Secure Record' only after all required information has been entered.")

        if "registration_success" in st.session_state:
            st.success(st.session_state["registration_success"])
            del st.session_state["registration_success"]

        form_v = st.session_state.get("farmer_form_version", 0)

        input_options = [
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
            "Extension Support",
        ]

        # Every successful submission increments this version. Streamlit then
        # creates a fresh set of widget keys, giving the agent a clean form.
        form_v = st.session_state.get("farmer_form_version", 0)

        st.markdown("### Section 1: Farmer Identity")
        farmer_full_name = st.text_input("Farmer Full Name", key=f"farmer_full_name_{form_v}")
        identity_col1, identity_col2 = st.columns(2)
        with identity_col1:
            gender = st.selectbox("Gender", ["Male", "Female"], key=f"gender_{form_v}")
        with identity_col2:
            dob = st.date_input("Date of Birth", key=f"dob_{form_v}")

        st.markdown("---")
        st.markdown("### Section 2: Contact Information")
        contact_col1, contact_col2 = st.columns(2)
        with contact_col1:
            phone_number = st.text_input("Phone Number", max_chars=11, key=f"phone_number_{form_v}")
        with contact_col2:
            alternate_phone = st.text_input(
                "Alternate Phone Number",
                max_chars=11,
                placeholder="Optional 11-digit phone number",
                key=f"alternate_phone_{form_v}",
            )
        email_address = st.text_input("Email Address", key=f"email_address_{form_v}")

        st.markdown("---")
        st.markdown("### Section 3: Coverage and Location")
        if role == "admin":
            farmer_state = st.selectbox("State", state_options, key=f"farmer_state_{form_v}")
        else:
            farmer_state = user_meta.get("state", "")
            st.text_input("State", value=farmer_state, disabled=True, key=f"farmer_state_display_{form_v}")

        lga_list = NIGERIA_LGA_MAP.get(farmer_state, [])
        if role == "admin":
            farmer_lga = st.selectbox("LGA", lga_list if lga_list else ["N/A"], key=f"farmer_lga_{form_v}")
        else:
            assigned_lga = user_meta.get("lga_coverage", "")
            farmer_lga = assigned_lga if assigned_lga in lga_list or assigned_lga else (lga_list[0] if lga_list else "N/A")
            st.text_input("LGA", value=farmer_lga, disabled=True, key=f"farmer_lga_display_{form_v}")

        location_col1, location_col2 = st.columns(2)
        with location_col1:
            ward = st.text_input("Ward", key=f"ward_{form_v}")
        with location_col2:
            community = st.text_input("Community / Village", key=f"community_{form_v}")
        residential_address = st.text_area("Residential Address", key=f"residential_address_{form_v}")

        st.markdown("---")
        st.markdown("### Section 4: Farm Profile")
        crop_col1, crop_col2 = st.columns(2)
        with crop_col1:
            primary_crop = st.selectbox(
                "Primary Crop",
                ["Rice", "Maize", "Cassava", "Sorghum", "Soybean", "Groundnut", "Millet"],
                key=f"primary_crop_{form_v}",
            )
        with crop_col2:
            secondary_crop = st.selectbox(
                "Secondary Crop",
                ["None", "Rice", "Maize", "Cassava", "Sorghum", "Soybean", "Groundnut", "Millet"],
                key=f"secondary_crop_{form_v}",
            )
        farm_size = st.number_input("Farm Size (Hectares)", min_value=0.0, step=0.1, key=f"farm_size_{form_v}")

        st.markdown("---")
        st.markdown("### Section 5: Support Delivered")
        input_list = st.multiselect("Inputs Distributed", input_options, key=f"input_list_{form_v}")
        quantity_units = len(input_list)
        st.caption(f"Total input types selected: {quantity_units}")

        st.markdown("---")
        st.markdown("### Section 6: NIN Verification")
        nin_col1, nin_col2 = st.columns(2)
        with nin_col1:
            nin = st.text_input("NIN", max_chars=11, key=f"nin_{form_v}")
        with nin_col2:
            nin_status = st.selectbox(
                "NIN Verification Status",
                ["Verified", "Pending", "Rejected"],
                key=f"nin_status_{form_v}",
            )

        st.markdown("---")
        st.markdown("### Section 7: Identification Document")
        id_col1, id_col2 = st.columns(2)
        with id_col1:
            id_type = st.selectbox(
                "ID Type",
                ["NIN Slip", "Voter Card", "Driver's License", "National ID Card", "Other"],
                key=f"id_type_{form_v}",
            )
        with id_col2:
            id_number = st.text_input("ID Number", max_chars=20, key=f"id_number_{form_v}")

        st.markdown("---")
        st.markdown("### Section 8: Automatic Farm Geo-tagging")
        st.caption(
            "Capture the device GPS position at the farm. The browser will request location permission the first time. "
            "Coordinates remain editable when a field agent needs to correct a weak GPS reading."
        )

        location = streamlit_geolocation()
        lat_key = f"latitude_{form_v}"
        lon_key = f"longitude_{form_v}"
        accuracy_key = f"gps_accuracy_{form_v}"

        if isinstance(location, dict):
            detected_lat = location.get("latitude")
            detected_lon = location.get("longitude")
            detected_accuracy = location.get("accuracy")
            if detected_lat is not None and detected_lon is not None:
                st.session_state[lat_key] = float(detected_lat)
                st.session_state[lon_key] = float(detected_lon)
                st.session_state[accuracy_key] = detected_accuracy
                accuracy_text = f" ±{float(detected_accuracy):.1f} m" if detected_accuracy is not None else ""
                st.success(f"GPS captured: {float(detected_lat):.6f}, {float(detected_lon):.6f}{accuracy_text}")
        else:
            st.info("Tap the location button and allow GPS access before submitting this farmer record.")

        geo_col1, geo_col2 = st.columns(2)
        with geo_col1:
            latitude = st.number_input("Latitude", format="%.6f", key=lat_key)
        with geo_col2:
            longitude = st.number_input("Longitude", format="%.6f", key=lon_key)

        if role == "agent" and latitude and longitude:
            geofence_result = gps_matches_assigned_state(farmer_state, float(latitude), float(longitude))
            if geofence_result is False:
                st.error(f"GPS is outside the broad {normalize_state_name(farmer_state)} operating envelope.")
            elif geofence_result is True:
                st.success(f"GPS is consistent with the assigned state: {normalize_state_name(farmer_state)}.")
            else:
                st.info("State and LGA are locked to the agent assignment. Precise boundary validation requires official GIS polygons.")

        st.markdown("---")
        st.markdown("### Section 9: Farmer Photo Capture")
        enable_camera_main = st.checkbox("Enable Camera", key=f"enable_camera_main_{form_v}")
        photo_capture = None
        if enable_camera_main:
            photo_capture = st.camera_input("Capture Farmer Photo", key=f"photo_capture_{form_v}")

        st.markdown("---")
        st.markdown("### Section 10: Enumerator Remarks and Confirmation")
        remarks = st.text_area("Enumerator Remarks", key=f"remarks_{form_v}")
        record_confirmed = st.checkbox(
            "I confirm that the information above has been reviewed with the farmer and is ready for submission.",
            key=f"record_confirmed_{form_v}",
        )

        st.markdown("---")
        st.markdown("### Section 11: Submission")
        submitted = st.button("Sync Secure Record", width="stretch", key=f"submit_farmer_{form_v}")

        if submitted:
            if not farmer_full_name.strip():
                st.error("Farmer full name is required.")
            elif not valid_phone(phone_number):
                st.error("Phone Number must be exactly 11 digits.")
            elif alternate_phone and not valid_phone(alternate_phone):
                st.error("Alternate Phone Number must be exactly 11 digits.")
            elif not valid_nin(nin):
                st.error("NIN must be exactly 11 digits.")
            elif not valid_id_number(id_number):
                st.error("ID Number must be between 1 and 20 characters.")
            elif not farmer_lga or farmer_lga == "N/A":
                st.error("LGA is required.")
            elif len(input_list) == 0:
                st.error("Please select at least one distributed input.")
            elif photo_capture is None:
                st.error("Farmer photo capture is required.")
            elif latitude == 0.0 and longitude == 0.0:
                st.error("Capture the farm GPS location before submission. Allow browser location access and try again.")
            elif role == "agent" and gps_matches_assigned_state(farmer_state, float(latitude), float(longitude)) is False:
                st.error("Submission blocked: GPS is outside the agent's assigned-state operating envelope.")
            elif not record_confirmed:
                st.error("Please confirm that the farmer's information has been reviewed before submission.")
            elif farmer_exists_today(phone_number, nin, farmer_full_name):
                st.warning("This farmer appears to have already been registered today.")
            else:
                now = datetime.now()
                farmer_id = f"AG-{now.strftime('%Y%m%d%H%M%S')}"

                photo_path = ""
                if photo_capture is not None:
                    photo_filename = f"{farmer_id}.jpg"
                    photo_path = save_uploaded_photo(
                        photo_capture,
                        folder="uploads/farmers",
                        filename=photo_filename,
                    )

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
                    "Photo_Path": photo_path,
                    "Photo_Status": "Captured" if photo_path else "No Photo",
                }

                if is_db_available():
                    insert_farmer(row)
                    log_action(user_id, "FARMER_REGISTERED", farmer_id)
                    success_text = "✅ Farmer record saved directly to the main database."
                else:
                    save_to_offline_queue(row)
                    log_action(user_id, "FARMER_QUEUED", farmer_id)
                    success_text = "✅ Offline Mode: farmer record saved locally and queued for sync."

                # Preserve the confirmation across the rerun, while assigning a
                # new widget-key version so the registration screen is blank.
                st.session_state["registration_success"] = f"{success_text} Farmer ID: {farmer_id}"
                st.session_state["farmer_form_version"] = form_v + 1
                st.rerun(scope="app")


    with tab_farmer_registration:
        render_farmer_registration()

    # =========================================================
    # TAB 3: DISTRIBUTION
    # =========================================================
    with tab_distribution:
        st.subheader("Input Breakdown")

        if not df.empty:
            input_counts = df["input_distributed"].fillna("").str.split(", ").explode()
            input_counts = input_counts[input_counts != ""].value_counts().reset_index()
            input_counts.columns = ["Input_Type", "Count"]

            pie_fig = px.pie(
                input_counts,
                names="Input_Type",
                values="Count",
                hole=0.5,
            )
            st.plotly_chart(pie_fig, width="stretch")
        else:
            st.info("No input distribution data available.")

        st.subheader("📋 Master Registry Database")

        if st.button("Reset Filters", key="reset_distribution_filters"):
            st.session_state["search_name"] = ""
            st.session_state["search_agent"] = ""
            st.session_state["filter_nin_status"] = "All"
            st.session_state["filter_photo_status"] = "All"
            st.session_state["filter_state"] = "All"
            st.session_state["filter_lga"] = "All"
            st.session_state["search_phone"] = ""

            if "photo_preview_select" in st.session_state:
                del st.session_state["photo_preview_select"]

            st.rerun()

        search_col1, search_col2, search_col3, search_col4 = st.columns(4)

        with search_col1:
            search_name = st.text_input("Search Farmer Name", key="search_name")

        with search_col2:
            search_agent = st.text_input("Search Agent ID", key="search_agent", placeholder="e.g. FCT-01")

        with search_col3:
            filter_nin_status = st.selectbox(
                "Filter NIN Status",
                ["All", "Verified", "Pending", "Rejected"],
                key="filter_nin_status"
            )

        with search_col4:
            filter_photo_status = st.selectbox(
                "Filter Photo Status",
                ["All", "Captured", "No Photo"],
                key="filter_photo_status"
            )

        filter_col1, filter_col2, filter_col3 = st.columns(3)

        with filter_col1:
            state_filter_options = ["All"] + sorted(df["state"].dropna().unique().tolist()) if not df.empty else ["All"]
            filter_state = st.selectbox("Filter State", state_filter_options, key="filter_state")

        with filter_col2:
            lga_filter_options = ["All"]
            if not df.empty and filter_state != "All":
                lga_filter_options += sorted(df[df["state"] == filter_state]["lga"].dropna().unique().tolist())
            elif not df.empty:
                lga_filter_options += sorted(df["lga"].dropna().unique().tolist())
            filter_lga = st.selectbox("Filter LGA", lga_filter_options, key="filter_lga")

        with filter_col3:
            search_phone = st.text_input("Search Phone Number", key="search_phone")

        filtered_df = df.copy()

        if search_name:
            filtered_df = filtered_df[
                filtered_df["farmer_full_name"].astype(str).str.contains(search_name, case=False, na=False)
            ]

        if search_agent:
            filtered_df = filtered_df[
                filtered_df["agent_id"].astype(str).str.contains(search_agent, case=False, na=False)
            ]

        if search_phone:
            filtered_df = filtered_df[
                filtered_df["phone_number"].astype(str).str.contains(search_phone, case=False, na=False)
            ]

        if filter_nin_status != "All":
            filtered_df = filtered_df[filtered_df["nin_status"] == filter_nin_status]

        if filter_photo_status != "All":
            filtered_df = filtered_df[filtered_df["photo_status"] == filter_photo_status]

        if filter_state != "All":
            filtered_df = filtered_df[filtered_df["state"] == filter_state]

        if filter_lga != "All":
            filtered_df = filtered_df[filtered_df["lga"] == filter_lga]

        st.caption(f"Showing {len(filtered_df)} record(s)")

        if filtered_df.empty:
            st.warning("No farmer record matched the current search/filter selection. Click 'Reset Filters' and try again.")

        display_df = filtered_df.rename(columns={
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
            "photo_status": "Photo_Status",
            "photo_path": "Photo_Path",
        })

        preferred_columns = [
            "Farmer_ID", "Registration_Date", "Agent_ID", "Farmer_Full_Name", "Gender",
            "Date_of_Birth", "Phone_Number", "Alternate_Phone", "Email_Address", "NIN",
            "State", "LGA", "Ward", "Community_Village", "Residential_Address",
            "Primary_Crop", "Secondary_Crop", "Farm_Size_Ha", "Input_Distributed",
            "Quantity_Units", "NIN_Status", "ID_Type", "ID_Number", "Latitude",
            "Longitude", "Enumerator_Remarks", "Photo_Status", "Photo_Path",
        ]

        available_columns = [col for col in preferred_columns if col in display_df.columns]
        display_df = display_df[available_columns]

        screen_columns = [
            "Farmer_ID", "Registration_Date", "Agent_ID", "Farmer_Full_Name", "Gender",
            "Phone_Number", "State", "LGA", "Primary_Crop", "Quantity_Units",
            "NIN_Status", "Photo_Status",
        ]

        available_screen_columns = [col for col in screen_columns if col in display_df.columns]
        st.dataframe(display_df[available_screen_columns], width="stretch")

        st.markdown("### Farmer ID Preview")

        if "photo_path" in filtered_df.columns:
            photo_records = filtered_df[
                filtered_df["photo_path"].notna() & (filtered_df["photo_path"] != "")
            ]
        else:
            photo_records = pd.DataFrame()

        if not photo_records.empty:
            photo_options = (
                photo_records["farmer_full_name"].fillna("Unknown").astype(str)
                + " | "
                + photo_records["farmer_id"].fillna("").astype(str)
            ).tolist()

            selected_photo_label = st.selectbox(
                "Select farmer photo to preview",
                photo_options,
                key="photo_preview_select"
            )

            selected_index = photo_options.index(selected_photo_label)
            selected_row = photo_records.iloc[selected_index]
            selected_photo_path = selected_row["photo_path"]

            if selected_photo_path and os.path.exists(selected_photo_path):
                col1, col2 = st.columns([1, 2])

                with col1:
                    st.image(selected_photo_path, width=220)

                with col2:
                    st.markdown(f"""
**Farmer ID:** {selected_row['farmer_id']}  
**Name:** {selected_row['farmer_full_name']}  
**Phone:** {selected_row['phone_number']}  
**State:** {normalize_state_name(selected_row['state'])}  
**LGA:** {selected_row['lga']}  
**Crop:** {selected_row.get('primary_crop', '-')}  
**Photo Status:** {selected_row['photo_status']}
                    """)

                farmer_id_value = str(selected_row['farmer_id'])
                verification_url = f"{APP_BASE_URL}?farmer_id={farmer_id_value}&sig={generate_qr_signature(farmer_id_value)}"
                farmer_qr = generate_qr_code(verification_url)
                farmer_qr_identity = build_farmer_qr_identity_image(selected_row, verification_url)
                qr1, qr2 = st.columns([1, 3])
                with qr1:
                    st.image(farmer_qr, width=150, caption="Individual Farmer QR")
                with qr2:
                    st.caption("Scan during input distribution or field verification to open this farmer's authenticated enumeration record.")
                    st.download_button(
                        "Download Named Farmer QR ID",
                        data=farmer_qr_identity.getvalue(),
                        file_name=f"{safe_filename(selected_row.get('farmer_full_name', 'Farmer'))}_{safe_filename(farmer_id_value)}_QR_ID.png",
                        mime="image/png",
                        key=f"download_farmer_qr_{farmer_id_value}",
                        width="content",
                    )
            else:
                st.warning("Photo file path exists in record, but image file was not found on disk.")
        else:
            st.info("No captured farmer photos available for preview yet.")

        download_col1, download_col2 = st.columns(2)

        with download_col1:
            table_to_csv_download(display_df, "agrow_master_registry.csv")

        with download_col2:
            table_to_excel_download(display_df, "agrow_master_registry.xlsx")       

    # =========================================================
    # TAB 4: FARMER VERIFICATION
    # =========================================================
    with tab_verification:
        st.markdown("### Verify an Enumerated Farmer")
        st.caption("Use this workspace during input distribution, field monitoring or farmer support. A valid QR scan opens the same verified record without requiring administrator access.")
        show_public_farmer_verification(compact=True, key_prefix="workspace")

    # =========================================================
    # TAB 5: ANALYTICS
    # =========================================================
    with tab_analytics:
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("Crop Distribution")
            if not df.empty:
                crop_counts = df["primary_crop"].value_counts().reset_index()
                crop_counts.columns = ["Primary_Crop", "Count"]
                bar_fig = px.bar(crop_counts, x="Primary_Crop", y="Count")
                st.plotly_chart(bar_fig, width="stretch")
            else:
                st.info("No crop data available.")

        with c2:
            st.subheader("NIN Verification Status")
            if not df.empty:
                nin_counts = df["nin_status"].value_counts().reset_index()
                nin_counts.columns = ["NIN_Status", "Count"]
                status_fig = px.bar(nin_counts, x="NIN_Status", y="Count")
                st.plotly_chart(status_fig, width="stretch")
            else:
                st.info("No verification data available.")

        st.subheader("Geographic Farmer Clusters")
        if not df.empty and {"state", "lga", "community", "latitude", "longitude"}.issubset(df.columns):
            cluster_df = df.copy()
            cluster_df["community"] = cluster_df["community"].fillna("Not specified").replace("", "Not specified")
            cluster_summary = (
                cluster_df.groupby(["state", "lga", "community"], dropna=False)
                .agg(
                    Farmers=("farmer_id", "count"),
                    Total_Land_Ha=("farm_size", "sum"),
                    Centre_Latitude=("latitude", "mean"),
                    Centre_Longitude=("longitude", "mean"),
                )
                .reset_index()
                .sort_values(["Farmers", "Total_Land_Ha"], ascending=False)
            )
            st.dataframe(cluster_summary, width="stretch")
            valid_cluster_points = cluster_df[(cluster_df["latitude"] != 0) | (cluster_df["longitude"] != 0)]
            if not valid_cluster_points.empty:
                cluster_map = valid_cluster_points.rename(columns={"latitude": "lat", "longitude": "lon"})
                st.map(cluster_map[["lat", "lon"]])
            st.caption("Use these community clusters to plan input allocation, extension visits, monitoring routes and other farmer support.")
        else:
            st.info("Community cluster analysis will appear after geotagged farmer records are available.")

        if role == "admin":
            st.subheader("👥 Registered Agents")
            agent_df = pd.DataFrame(fetch_all_agents())

            if not agent_df.empty:
                agent_df["State"] = agent_df["State"].apply(normalize_state_name)
                st.dataframe(agent_df, width="stretch")

                a1, a2 = st.columns(2)
                with a1:
                    table_to_csv_download(agent_df, "agrow_registered_agents.csv")
                with a2:
                    table_to_excel_download(agent_df, "agrow_registered_agents.xlsx")
            else:
                st.info("No registered agents yet.")

    st.markdown(
        '<div class="footer">© DataDev Limited | AGROW Operations Workspace v4.1 | Ministry Deployment Prototype</div>',
        unsafe_allow_html=True,
    )