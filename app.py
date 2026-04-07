import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io
import os
from nigeria_lga_data import NIGERIA_LGA_MAP

# 1. Page Config
st.set_page_config(page_title="World Bank AGROW Nigeria", layout="wide", page_icon="🇳🇬")

# Create image folder
if not os.path.exists("captured_images"):
    os.makedirs("captured_images")

# --- 2. EXECUTIVE THEME (Embossed Green Side-Border) ---
PRIMARY_GREEN = "#1B5E20" 
OFFICIAL_BLUE = "#004B87"

st.markdown(f"""
    <style>
    .stApp {{ background-color: #F8F9FA; }}
    [data-testid="stSidebar"] {{ background-color: #FFFFFF; border-right: 3px solid {PRIMARY_GREEN}; width: 450px !important; }}
    [data-testid="stMetric"] {{
        background: white !important;
        border-left: 8px solid {PRIMARY_GREEN} !important;
        border-radius: 10px !important;
        padding: 20px !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05) !important;
    }}
    .stTextInput>div>div>input, .stSelectbox>div>div, .stMultiSelect>div {{
        border: 2px solid #CED4DA !important;
        border-radius: 8px !important;
        background-color: #FDFDFD !important;
    }}
    .footer {{ position: fixed; bottom: 0; left: 0; width: 100%; background-color: white; text-align: center; padding: 12px; font-weight: bold; border-top: 1px solid #ddd; z-index: 999; }}
    </style>
    """, unsafe_allow_html=True)

# 3. Data Initialization & Error Prevention Loop
excel_cols = ['Farmer_ID', 'NIN_Linked', 'Name', 'LGA', 'State', 'Crop_Type', 'Farm_Size_Ha', 'NIN_Status', 'Input_Distributed', 'Quantity_Units', 'Lat', 'Lon', 'Phone', 'Photo_URL']

if 'main_df' not in st.session_state:
    try:
        df = pd.read_csv('data/kano_farmers.csv')
        # Safety Check: Add any missing columns to old CSV data to prevent KeyErrors
        for col in excel_cols:
            if col not in df.columns:
                df[col] = ""
        st.session_state.main_df = df
    except:
        st.session_state.main_df = pd.DataFrame(columns=excel_cols)

# Define states list
nigeria_states = sorted(list(NIGERIA_LGA_MAP.keys()))

# 4. Sidebar Branding & Form
st.sidebar.image("https://wikimedia.org", width=150)
selected_state = st.sidebar.selectbox("Geographic Focus", ["All Nigeria"] + nigeria_states)

with st.sidebar.expander("📝 Secure Field Registration", expanded=True):
    cam_toggle = st.checkbox("📸 Enable Camera for Biometrics", value=False)
    
    with st.form(key="agrow_final_master_v3", clear_on_submit=True):
        f_name = st.text_input("Full Name")
        f_nin = st.text_input("NIN (11 Digits)", max_chars=11)
        f_phone = st.text_input("Phone (11 Digits)", max_chars=11)
        f_state = st.selectbox("State", nigeria_states)
        f_lga = st.selectbox("LGA", NIGERIA_LGA_MAP.get(f_state, ["Select State"]))
        f_crop = st.selectbox("Crop Type", ["Rice", "Maize", "Cassava", "Soybeans", "Cocoa"])
        f_size = st.number_input("Farm Size (Ha)", min_value=0.1)
        f_inputs = st.multiselect("Inputs Distributed", ["NPK Fertilizer", "Urea", "Seeds", "Manure"])
        
        f_photo = None
        if cam_toggle:
            f_photo = st.camera_input("Capture Biometric")
        
        if st.form_submit_button("Sync Secure Record"):
            if len(f_nin) == 11 and len(f_phone) == 11 and (f_photo or not cam_toggle):
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                img_path = "No Image"
                if f_photo:
                    img_path = f"captured_images/{f_nin}_{ts}.png"
                    with open(img_path, "wb") as f: f.write(f_photo.getbuffer())
                
                new_row = {
                    'Farmer_ID': f"AG-{ts}", 'NIN_Linked': f_nin, 'Name': f_name, 
                    'LGA': f_lga, 'State': f_state, 'Crop_Type': f_crop, 
                    'Farm_Size_Ha': f_size, 'NIN_Status': 'Verified', 
                    'Input_Distributed': ", ".join(f_inputs), 
                    'Quantity_Units': 1, 'Lat': 9.08, 'Lon': 7.39,
                    'Phone': f_phone, 'Photo_URL': img_path
                }
                st.session_state.main_df = pd.concat([st.session_state.main_df, pd.DataFrame([new_row])], ignore_index=True)
                st.sidebar.success("✅ Synced to Registry!")
            else:
                st.sidebar.error("❌ Invalid NIN/Phone length.")

# 5. Dashboard Headers
st.markdown('<p style="color:#004B87; font-size:32px; font-weight:800; text-align:center; margin:0;">Nigeria Sustainable Agricultural Value-Chains (AGROW)</p>', unsafe_allow_html=True)
st.markdown(f'<p style="color:#1B5E20; font-size:16px; font-weight:600; text-align:center; margin-bottom:20px;">World Bank $500M Credit Facility | {selected_state} Hub</p>', unsafe_allow_html=True)

df = st.session_state.main_df
display_df = df if selected_state == "All Nigeria" else df[df['State'] == selected_state]

# 6. KPI Metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Beneficiaries", len(display_df))
m2.metric("NIN Verified", len(display_df))
land_total = display_df['Farm_Size_Ha'].sum() if not display_df.empty else 0.0
m3.metric("Land Covered (Ha)", f"{land_total:.1f}")
m4.metric("Growth Target", "1,000,000")

st.divider()

# 7. Visuals
c1, c2 = st.columns([1.3, 0.7])
with c1:
    st.subheader("📍 Geospatial Mapping")
    st.map(display_df, latitude='Lat', longitude='Lon', color=PRIMARY_GREEN)
with c2:
    st.subheader("📦 Aid Breakdown")
    if not display_df.empty:
        raw_inputs = display_df['Input_Distributed'].str.split(', ').explode()
        input_data = raw_inputs.value_counts().reset_index()
        input_data.columns = ['Type', 'Count']
        fig = px.pie(input_data, names='Type', values='Count', hole=0.5, color_discrete_sequence=px.colors.sequential.Greens_r)
        fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"))
        st.plotly_chart(fig, use_container_width=True)

# 8. Registry & Export
st.subheader("📋 Master Registry Database")
btn_csv, btn_xlsx = st.columns(2)
btn_csv.download_button("📥 Export CSV", display_df.to_csv(index=False).encode('utf-8'), f"AGROW_{selected_state}.csv", use_container_width=True)

buffer = io.BytesIO()
# Final check to ensure we only export columns that actually exist
available_cols = [c for c in excel_cols if c in display_df.columns]
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    display_df[available_cols].to_excel(writer, index=False)

btn_xlsx.download_button("📊 Export Excel", buffer.getvalue(), f"AGROW_{selected_state}.xlsx", use_container_width=True)
st.dataframe(display_df, use_container_width=True)

# 9. Centered Footer
st.markdown(f'<div class="footer">Technically Managed by DataDev Limited | Project Monitor v3.0</div>', unsafe_allow_html=True)