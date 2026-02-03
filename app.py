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
        return pd.DataFrame(columns=["username", "password"])

# ================= SESSION STATE =================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "display_name" not in st.session_state:
    st.session_state.display_name = ""
if "itinerary" not in st.session_state:
    st.session_state.itinerary = []
if "builder_form_key" not in st.session_state:
    st.session_state.builder_form_key = 0

# ================= HELPERS =================
def clean_for_pdf(text):
    if not text: return ""
    # Filter to prevent FPDFUnicodeEncodingException (strips emojis/special symbols)
    return re.sub(r'[^a-zA-Z0-9\s\.,\-\(\):/]', '', str(text))

def clean_filename(text):
    if not text: return "itinerary"
    text = re.sub(r"[^A-Za-z0-9_-]+", "_", text)
    return text.strip("_")

# ================= EXPORT FUNCTIONS =================
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
h1, h2, h3, p, label {{ color: white !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.8); }}
</style>
""", unsafe_allow_html=True)

# ================= LOGIN =================
if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align:center;'>EXCLUSIVE HOLIDAYS</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                db = load_user_db()
                user_row = db[(db["username"] == u) & (db["password"].astype(str) == p)]
                if not user_row.empty:
                    st.session_state.authenticated = True
                    st.session_state.user_role = "Admin" if u.lower() in ["admin", "admin01"] else "Staff"
                    # Set the First Name for the greeting
                    st.session_state.display_name = u.split('_')[0].split('.')[0].capitalize()
                    st.rerun()
                else: st.error("Invalid credentials")
    st.stop()

# ================= HEADER =================
c_greet, c_logout = st.columns([8, 2])
with c_greet:
    st.markdown(f"## Hello, {st.session_state.display_name}!")
with c_logout:
    if st.button("Logout & Reset"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# ================= MAIN APP =================
if st.session_state.user_role == "Admin":
    st.subheader("🛠️ Admin Panel: User Management")
    # Admin User management logic goes here
    st.dataframe(load_user_db(), use_container_width=True)

else:
    st.subheader("✈️ Itinerary Builder")
    
    # 1. ITINERARY NAME WITH PLACEHOLDER
    it_name = st.text_input("Itinerary Name", placeholder="Relax on Beach – 10 Days")
    
    colA, colB, colC = st.columns([2, 1, 1])
    with colA: r = st.text_input("Route", placeholder="Airport - Negombo", key=f"r_{st.session_state.builder_form_key}")
    with colB: dist = st.text_input("Distance", placeholder="9.5KM", key=f"d_{st.session_state.builder_form_key}")
    with colC: dur = st.text_input("Duration", placeholder="30 Minutes", key=f"t_{st.session_state.builder_form_key}")
    
    # 2. ACTIVITIES (BEFORE DESCRIPTION)
    num_a = st.selectbox("How many activities?", range(0, 11))
    acts = []
    for i in range(num_a):
        a_val = st.text_input(f"Activity {i+1}", placeholder="Relaxing on the beach", key=f"act_{st.session_state.builder_form_key}_{i}")
        if a_val: acts.append(f"• {a_val}")
    
    # 3. DESCRIPTION (AFTER ACTIVITIES)
    main_d = st.text_area("Description", placeholder="Negombo is a bustling,, historic coastal city.......", key=f"desc_{st.session_state.builder_form_key}")
    
    if st.button("➕ Add Day"):
        if r:
            full_text = ("Activities:\n" + "\n".join(acts) + "\n\n" if acts else "") + main_d
            st.session_state.itinerary.append({"Route": r, "Distance": dist, "Time": dur, "Description": full_text})
            st.session_state.builder_form_key += 1
            st.rerun()

    # ================= EXPORT BUTTONS SECTION =================
    if st.session_state.itinerary:
        st.markdown("---")
        st.write("### Export Options")
        safe_name = clean_filename(it_name)
        
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        
        with btn_col1:
            df_export = pd.DataFrame(st.session_state.itinerary)
            st.download_button("📊 Download Excel", df_export.to_csv(index=False).encode('utf-8'), f"{safe_name}.csv")
            
        with btn_col2:
            word_file = create_word(it_name, st.session_state.itinerary)
            st.download_button("📝 Download Word", word_file, f"{safe_name}.docx")
            
        with btn_col3:
            try:
                pdf_file = create_pdf(it_name, st.session_state.itinerary)
                st.download_button("📄 Download PDF", pdf_file, f"{safe_name}.pdf", mime="application/pdf")
            except Exception as e:
                st.error("Error generating PDF. Please remove any special symbols.")

        # DISPLAY ADDED DAYS
        for i, d in enumerate(st.session_state.itinerary):
            with st.expander(f"Day {i+1}: {d['Route']}", expanded=True):
                st.write(f"**{d['Distance']} | {d['Time']}**")
                st.write(d['Description'])
                if st.button(f"Remove Day {i+1}", key=f"rem_{i}"):
                    st.session_state.itinerary.pop(i)
                    st.rerun()
