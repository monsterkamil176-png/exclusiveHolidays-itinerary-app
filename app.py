import streamlit as st
import os
import base64
import pandas as pd
import re
from io import BytesIO
from fpdf import FPDF
from docx import Document
from streamlit_gsheets import GSheetsConnection

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Exclusive Holidays SL", page_icon="✈️", layout="wide")

# ================= DATABASE =================
conn = st.connection("gsheets", type=GSheetsConnection)

def load_user_db():
    try:
        return conn.read(worksheet="Sheet1", ttl=0)
    except:
        return None

# ================= SESSION STATE =================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "itinerary" not in st.session_state:
    st.session_state.itinerary = []
if "builder_form_key" not in st.session_state:
    st.session_state.builder_form_key = 0

# ================= HELPERS =================
def get_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def clean_for_pdf(text):
    """Aggressively removes any non-standard character to stop PDF crashes."""
    if not text: return ""
    # Only allows standard letters, numbers, and basic punctuation
    return re.sub(r'[^a-zA-Z0-9\s\.,\-\(\):/]', '', str(text))

def clean_filename(text):
    if not text: return "itinerary"
    text = re.sub(r"[^A-Za-z0-9_-]+", "_", text)
    return text.strip("_")

# ================= STYLING =================
bg_img = "https://images.unsplash.com/photo-1586500036706-41963de24d8b?q=80&w=2574&auto=format&fit=crop"
st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
    background: linear-gradient(rgba(0,0,0,0.55), rgba(0,0,0,0.55)), url("{bg_img}");
    background-size: cover; background-position: center; background-attachment: fixed;
}}
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{
    background-color: rgba(255,255,255,0.95) !important; color: #1e1e1e !important;
}}
.stButton > button {{
    background-color: #ffffff !important; color: #000000 !important; font-weight: 800; border-radius: 8px;
}}
h1, h2, h3, p, label {{ color: white !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.8); }}
</style>
""", unsafe_allow_html=True)

def display_branding():
    logo = get_base64("logo.png")
    if logo:
        st.markdown(f"<div style='text-align:center;'><img src='data:image/png;base64,{logo}' width='80'></div>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center;margin-bottom:0;'>EXCLUSIVE HOLIDAYS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;font-style:italic;margin-top:0;'>Unforgettable Island Adventures Awaits</p>", unsafe_allow_html=True)

# ================= EXPORT LOGIC =================
def create_word(title, itinerary):
    doc = Document()
    doc.add_heading(f"Itinerary: {title}", 0)
    for i, day in enumerate(itinerary):
        doc.add_heading(f"Day {i+1}: {day['Route']}", level=1)
        doc.add_paragraph(f"Distance: {day['Distance']} | Duration: {day['Time']}")
        doc.add_paragraph(day["Description"])
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

def create_pdf(title, itinerary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "EXCLUSIVE HOLIDAYS SRI LANKA", 0, 1, "C")
    pdf.ln(8)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Itinerary: {clean_for_pdf(title)}", 0, 1)
    for i, day in enumerate(itinerary):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, clean_for_pdf(f"Day {i+1}: {day['Route']}"), 1, 1)
        pdf.set_font("Arial", "I", 10)
        pdf.cell(0, 7, clean_for_pdf(f"Distance: {day['Distance']} | Duration: {day['Time']}"), 0, 1)
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 7, clean_for_pdf(day["Description"]))
        pdf.ln(4)
    return pdf.output(dest='S')

# ================= LOGIN SYSTEM =================
if not st.session_state.authenticated:
    display_branding()
    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                db = load_user_db()
                if db is not None:
                    user_row = db[(db["username"] == u) & (db["password"].astype(str) == p)]
                    if not user_row.empty:
                        st.session_state.authenticated = True
                        st.session_state.user_role = "Admin" if u.lower() == "admin" else "Staff"
                        st.rerun()
                    else: st.error("Invalid credentials")
    st.stop()

# ================= SHARED HEADER =================
display_branding()
c_role, c_logout = st.columns([8, 2])
with c_role:
    st.markdown(f"**Logged in as:** {st.session_state.user_role}")
with c_logout:
    if st.button("Logout & Reset"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ================= ROLE BASED NAVIGATION =================
if st.session_state.user_role == "Admin":
    st.subheader("Admin Control Panel")
    # Admin only sees Management, NOT the builder
    with st.expander("User Management (Google Sheets Connection)", expanded=True):
        st.info("Direct management is available via your Google Sheet. Refresh below to see current users.")
        if st.button("Refresh User List"):
            st.dataframe(load_user_db())
else:
    # Staff only sees the Builder
    st.subheader("✈️ Itinerary Builder")
    
    it_name = st.text_input("Itinerary Name", placeholder="Relax on Beach – 10 Days")
    
    colA, colB, colC = st.columns([2, 1, 1])
    with colA: r = st.text_input("Route", placeholder="Airport - Negombo", key=f"r_{st.session_state.builder_form_key}")
    with colB: dist = st.text_input("Distance", placeholder="9.5KM", key=f"d_{st.session_state.builder_form_key}")
    with colC: dur = st.text_input("Duration", placeholder="30 Minutes", key=f"t_{st.session_state.builder_form_key}")
    
    num_a = st.selectbox("How many activities?", range(0, 11))
    acts = []
    for i in range(num_a):
        a_val = st.text_input(f"Activity {i+1}", placeholder="Relaxing on the beach", key=f"act_{st.session_state.builder_form_key}_{i}")
        if a_val: acts.append(f"• {a_val}")
    
    main_d = st.text_area("Description", placeholder="Negombo is a bustling,, historic coastal city...", key=f"desc_{st.session_state.builder_form_key}")
    
    if st.button("➕ Add Day"):
        if r:
            full_text = ("Activities:\n" + "\n".join(acts) + "\n\n" if acts else "") + main_d
            st.session_state.itinerary.append({"Route": r, "Distance": dist, "Time": dur, "Description": full_text})
            st.session_state.builder_form_key += 1
            st.rerun()

    if st.session_state.itinerary:
        st.markdown("---")
        safe_name = clean_filename(it_name)
        d1, d2, d3 = st.columns(3)
        with d1:
            st.download_button("📥 Excel", pd.DataFrame(st.session_state.itinerary).to_csv(index=False).encode('utf-8'), f"{safe_name}.csv")
        with d2:
            st.download_button("📥 Word", create_word(it_name, st.session_state.itinerary), f"{safe_name}.docx")
        with d3:
            try:
                p_data = create_pdf(it_name, st.session_state.itinerary)
                st.download_button("📥 PDF", p_data, f"{safe_name}.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"PDF Error: {e}")

        for i, d in enumerate(st.session_state.itinerary):
            with st.expander(f"Day {i+1}: {d['Route']}", expanded=True):
                st.write(f"**{d['Distance']} | {d['Time']}**")
                st.write(d['Description'])
                if st.button("Remove", key=f"del_{i}"):
                    st.session_state.itinerary.pop(i)
                    st.rerun()
