import streamlit as st
import os
import base64
import pandas as pd
from io import BytesIO
from fpdf import FPDF
from docx import Document
from streamlit_gsheets import GSheetsConnection

# 1. Page Config
st.set_page_config(page_title="Exclusive Holidays SL", page_icon="✈️", layout="wide")

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_user_db():
    try:
        df = conn.read(worksheet="Sheet1", ttl=0)
        return df
    except: return None

# Initialize Session States
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'itinerary' not in st.session_state: st.session_state.itinerary = []
if 'builder_form_key' not in st.session_state: st.session_state.builder_form_key = 0

def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

# 2. CSS Styling
bg_img = "https://images.unsplash.com/photo-1586500036706-41963de24d8b?q=80&w=2574&auto=format&fit=crop"
st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url("{bg_img}");
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    .stTextInput input, .stTextArea textarea {{ background-color: rgba(255, 255, 255, 0.95) !important; color: #1e1e1e !important; }}
    .stButton > button {{ color: #000000 !important; font-weight: 800 !important; background-color: #ffffff !important; border-radius: 8px; }}
    h1, h2, h3, p, label {{ color: white !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.8); }}
    </style>
    """, unsafe_allow_html=True)

def display_branding():
    logo_base64 = get_base64("logo.png")
    if logo_base64:
        st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_base64}" width="80"></div>', unsafe_allow_html=True)
    st.markdown('<h1 style="text-align: center; font-size: 28px; margin-bottom:0;">EXCLUSIVE HOLIDAYS</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-style: italic; margin-top:0;">"Unforgettable Island Adventures Awaits"</p>', unsafe_allow_html=True)

# --- PDF TEXT CLEANER ---
def safe_text(text):
    if not text: return ""
    # This force-cleans any symbols like 🔗 or emojis that crash FPDF
    return text.encode('ascii', 'ignore').decode('ascii')

# --- EXPORT LOGIC ---
def create_pdf(title, itinerary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 16)
    pdf.cell(0, 10, 'EXCLUSIVE HOLIDAYS SRI LANKA', 0, 1, 'C')
    pdf.ln(10)
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 10, f"Trip Plan: {safe_text(title)}", 0, 1, 'L')
    
    for i, day in enumerate(itinerary):
        pdf.set_font('helvetica', 'B', 12)
        header = f"Day {i+1}: {day['Route']} | Distance: {day['Distance']} | Duration: {day['Time']}"
        pdf.cell(0, 10, safe_text(header), 1, 1, 'L')
        pdf.set_font('helvetica', '', 11)
        pdf.multi_cell(0, 7, safe_text(day['Description']))
        pdf.ln(5)
    return pdf.output()

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Itinerary')
    return output.getvalue()

# --- LOGIN SCREEN ---
if not st.session_state.authenticated:
    display_branding()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_gate"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                df = load_user_db()
                if df is not None:
                    user_row = df[(df['username'] == u) & (df['password'].astype(str) == p)]
                    if not user_row.empty:
                        st.session_state.authenticated = True
                        st.rerun()
                    else: st.error("Invalid Credentials")
    st.stop()

# --- APP HEADER ---
display_branding()
c_space, c_logout = st.columns([9, 1.2])
with c_logout:
    if st.button("Logout", key="top_logout"):
        st.session_state.authenticated = False
        st.rerun()

tab_build, tab_set = st.tabs(["✈️ Itinerary Builder", "Settings ⚙️"])

with tab_build:
    tour_title = st.text_input("Client Name", placeholder="e.g. John Doe", key="title_main")
    
    colA, colB, colC = st.columns([2, 1, 1])
    with colA: r_in = st.text_input("Route", placeholder="Airport -> Negombo", key=f"r_{st.session_state.builder_form_key}")
    with colB: d_in = st.text_input("Distance", placeholder="35 KM", key=f"d_{st.session_state.builder_form_key}")
    with colC: t_in = st.text_input("Time/Duration", placeholder="1 Hr 15 Mins", key=f"t_{st.session_state.builder_form_key}")
    
    desc_box = st.text_area("Daily Description", placeholder="Enter highlights...", key=f"desc_{st.session_state.builder_form_key}")
    
    num_activities = st.selectbox("Add Activities?", range(0, 6), index=0)
    activity_list = []
    for j in range(num_activities):
        act = st.text_input(f"Activity {j+1}", key=f"act_{st.session_state.builder_form_key}_{j}")
        if act: activity_list.append(f"• {act}")
    
    full_description = desc_box + ("\n\n" + "\n".join(activity_list) if activity_list else "")
    
    b1, b2 = st.columns([1, 1])
    with b1:
        if st.button("➕ Add Day"):
            if r_in:
                st.session_state.itinerary.append({"Route": r_in, "Distance": d_in, "Time": t_in, "Description": full_description})
                st.session_state.builder_form_key += 1
                st.rerun()
    with b2:
        if st.button("🗑️ Clear All"):
            st.session_state.itinerary = []
            st.rerun()

    if st.session_state.itinerary:
        st.markdown("---")
        # Export Buttons
        ex1, ex2, ex3 = st.columns(3)
        with ex1:
            st.download_button("📥 Excel", data=to_excel(pd.DataFrame(st.session_state.itinerary)), file_name=f"{tour_title}.xlsx")
        with ex2:
            try:
                pdf_bytes = create_pdf(tour_title, st.session_state.itinerary)
                st.download_button("📥 PDF", data=pdf_bytes, file_name=f"{tour_title}.pdf", mime="application/pdf")
            except Exception as e:
                st.warning("⚠️ PDF button hidden due to special characters. Remove emojis to enable.")
        
        # Display list with Distance and Duration
        for i, item in enumerate(st.session_state.itinerary):
            st.markdown(f"### Day {i+1}: {item['Route']}")
            st.markdown(f"**📍 Distance:** {item['Distance']} | **⏳ Duration:** {item['Time']}")
            st.info(item['Description'])
            if st.button(f"Remove Day {i+1}", key=f"rem_{i}"):
                st.session_state.itinerary.pop(i)
                st.rerun()
            st.markdown("---")
