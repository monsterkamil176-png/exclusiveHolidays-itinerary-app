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
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{ background-color: rgba(255, 255, 255, 0.95) !important; color: #1e1e1e !important; }}
    .stButton > button {{ color: #000000 !important; font-weight: 800 !important; background-color: #ffffff !important; border-radius: 8px; width: 100%; }}
    h1, h2, h3, p, label {{ color: white !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.8); }}
    </style>
    """, unsafe_allow_html=True)

def display_branding():
    logo_base64 = get_base64("logo.png")
    if logo_base64:
        st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_base64}" width="80"></div>', unsafe_allow_html=True)
    st.markdown('<h1 style="text-align: center; font-size: 28px; margin-bottom:0;">EXCLUSIVE HOLIDAYS</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-style: italic; margin-top:0;">"Unforgettable Island Adventures Awaits"</p>', unsafe_allow_html=True)

# --- TEXT CLEANER (Prevents PDF Encoding Crashes) ---
def clean_for_pdf(text):
    if not text: return ""
    # Strips non-Latin1 characters (emojis, link icons) that crash FPDF
    return text.encode('latin-1', 'replace').decode('latin-1').replace('?', '')

# --- EXPORT FUNCTIONS ---
def create_word(title, itinerary):
    doc = Document()
    doc.add_heading(f'Itinerary: {title}', 0)
    for i, item in enumerate(itinerary):
        doc.add_heading(f'Day {i+1}: {item["Route"]}', level=1)
        doc.add_paragraph(f"Distance: {item['Distance']} | Duration: {item['Time']}")
        doc.add_paragraph(item['Description'])
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

def create_pdf(title, itinerary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 16)
    pdf.cell(0, 10, 'EXCLUSIVE HOLIDAYS SRI LANKA', 0, 1, 'C')
    pdf.ln(10)
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 10, f"Trip Plan: {clean_for_pdf(title)}", 0, 1, 'L')
    
    for i, day in enumerate(itinerary):
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 10, clean_for_pdf(f"Day {i+1}: {day['Route']}"), 1, 1, 'L')
        pdf.set_font('helvetica', 'I', 10)
        pdf.cell(0, 7, clean_for_pdf(f"Distance: {day['Distance']} | Duration: {day['Time']}"), 0, 1, 'L')
        pdf.set_font('helvetica', '', 11)
        pdf.multi_cell(0, 7, clean_for_pdf(day['Description']))
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
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
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

# --- APP HEADER & LOGOUT RESET ---
display_branding()
c_space, c_logout = st.columns([9, 1.5])
with c_logout:
    if st.button("Logout & Reset"):
        # Wipes everything on exit
        st.session_state.authenticated = False
        st.session_state.itinerary = []
        st.session_state.builder_form_key = 0
        st.rerun()

tab_build, tab_set = st.tabs(["✈️ Itinerary Builder", "Settings ⚙️"])

with tab_build:
    tour_title = st.text_input("Client Name", placeholder="e.g. Smith Family Tour", key="title_main")
    
    # Input Row
    colA, colB, colC = st.columns([2, 1, 1])
    with colA: r_in = st.text_input("Route", placeholder="Airport -> Colombo", key=f"r_{st.session_state.builder_form_key}")
    with colB: d_in = st.text_input("Distance", placeholder="35 KM", key=f"d_{st.session_state.builder_form_key}")
    with colC: t_in = st.text_input("Duration", placeholder="1 Hr", key=f"t_{st.session_state.builder_form_key}")
    
    # Description & Dynamic Activities
    desc_box = st.text_area("Main Description", placeholder="General info for the day...", key=f"desc_{st.session_state.builder_form_key}")
    
    num_act = st.selectbox("How many specific activities?", range(0, 11), index=0)
    act_list = []
    for j in range(num_act):
        act_text = st.text_input(f"Activity {j+1}", key=f"act_{st.session_state.builder_form_key}_{j}")
        if act_text: act_list.append(f"• {act_text}")
    
    full_desc = desc_box + ("\n\n" + "\n".join(act_list) if act_list else "")
    
    # Action Buttons
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("➕ Add Day to Itinerary"):
            if r_in:
                st.session_state.itinerary.append({
                    "Route": r_in, "Distance": d_in, "Time": t_in, "Description": full_desc
                })
                st.session_state.builder_form_key += 1
                st.rerun()
    with col_btn2:
        if st.button("🗑️ Clear All Entry"):
            st.session_state.itinerary = []
            st.rerun()

    # --- THE EXPORT SECTION ---
    if st.session_state.itinerary:
        st.markdown("---")
        st.subheader("Download Options")
        e1, e2, e3 = st.columns(3)
        
        # 1. EXCEL
        with e1:
            df_itiner = pd.DataFrame(st.session_state.itinerary)
            st.download_button("📥 Excel File", data=to_excel(df_itiner), file_name=f"{tour_title}.xlsx")
        
        # 2. WORD (Restored)
        with e2:
            word_data = create_word(tour_title, st.session_state.itinerary)
            st.download_button("📥 Word Doc", data=word_data, file_name=f"{tour_title}.docx")
            
        # 3. PDF (Robust Version)
        with e3:
            try:
                pdf_data = create_pdf(tour_title, st.session_state.itinerary)
                st.download_button("📥 PDF File", data=pdf_data, file_name=f"{tour_title}.pdf", mime="application/pdf")
            except Exception:
                st.error("Text error! Remove symbols/emojis from input.")

        # --- PREVIEW SECTION ---
        st.markdown("---")
        for i, item in enumerate(st.session_state.itinerary):
            with st.expander(f"Day {i+1}: {item['Route']}", expanded=True):
                st.write(f"**📍 Distance:** {item['Distance']} | **⏳ Duration:** {item['Time']}")
                st.write(item['Description'])
                if st.button(f"Remove Day {i+1}", key=f"rem_{i}"):
                    st.session_state.itinerary.pop(i)
                    st.rerun()

with tab_set:
    st.write("Settings & Password Management")
