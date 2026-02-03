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
if "form_key" not in st.session_state:
    st.session_state.form_key = 0

# ================= HELPERS =================
def clean_for_pdf(text):
    """Forcefully removes emojis and symbols like 🔗 that crash FPDF."""
    if not text: return ""
    # This regex only keeps standard English letters, numbers, and basic punctuation
    return re.sub(r'[^a-zA-Z0-9\s\.,\-\(\):/!\?]', '', str(text))

def clean_filename(text):
    if not text: return "itinerary"
    return re.sub(r"[^A-Za-z0-9_-]+", "_", text).strip("_")

# ================= EXPORT LOGIC =================
def create_pdf(title, itinerary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "EXCLUSIVE HOLIDAYS SRI LANKA", 0, 1, "C")
    pdf.ln(8)
    
    # Cleaning title to remove that link symbol
    safe_title = clean_for_pdf(title)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Itinerary: {safe_title}", 0, 1)
    
    for i, day in enumerate(itinerary):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, clean_for_pdf(f"Day {i+1}: {day['Route']}"), 1, 1)
        pdf.set_font("Arial", "I", 10)
        pdf.cell(0, 7, clean_for_pdf(f"{day['Distance']} | {day['Time']}"), 0, 1)
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
/* Forces placeholder text to be visible */
::placeholder {{ color: #666666 !important; opacity: 1 !important; }}
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
                    st.session_state.display_name = u.split('_')[0].split('.')[0].capitalize()
                    st.rerun()
                else: st.error("Invalid credentials")
    st.stop()

# ================= APP HEADER =================
c1, c2 = st.columns([8, 2])
with c1: st.markdown(f"## Hello, {st.session_state.display_name}!")
with c2: 
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# ================= BUILDER =================
if st.session_state.user_role == "Admin":
    st.subheader("🛠️ Admin: User Management")
    st.dataframe(load_user_db(), use_container_width=True)
else:
    st.subheader("✈️ Itinerary Builder")
    
    # PLACEHOLDERS HARDCODED
    it_name = st.text_input("Itinerary Name", placeholder="Relax on Beach – 10 Days")
    
    cA, cB, cC = st.columns([2, 1, 1])
    with cA: r = st.text_input("Route", placeholder="Airport - Negombo", key=f"r_{st.session_state.form_key}")
    with cB: d = st.text_input("Distance", placeholder="9.5KM", key=f"d_{st.session_state.form_key}")
    with cC: t = st.text_input("Duration", placeholder="30 Minutes", key=f"t_{st.session_state.form_key}")
    
    num_a = st.selectbox("How many activities?", range(0, 11))
    acts = []
    for i in range(num_a):
        av = st.text_input(f"Activity {i+1}", placeholder="Relaxing on the beach", key=f"a_{st.session_state.form_key}_{i}")
        if av: acts.append(f"• {av}")
    
    desc = st.text_area("Description", placeholder="Negombo is a bustling,, historic coastal city.......", key=f"desc_{st.session_state.form_key}")
    
    if st.button("➕ Add Day"):
        if r:
            full_desc = ("Activities:\n" + "\n".join(acts) + "\n\n" if acts else "") + desc
            st.session_state.itinerary.append({"Route": r, "Distance": d, "Time": t, "Description": full_desc})
            st.session_state.form_key += 1 # Resetting key keeps placeholders visible
            st.rerun()

    # ================= EXPORTS =================
    if st.session_state.itinerary:
        st.markdown("---")
        st.write("### Download Files")
        safe_fn = clean_filename(it_name)
        
        ex1, ex2, ex3 = st.columns(3)
        with ex1:
            st.download_button("📊 Excel", pd.DataFrame(st.session_state.itinerary).to_csv(index=False).encode('utf-8'), f"{safe_fn}.csv")
        with ex2:
            # Word logic remains the same
            st.button("📝 Word (Coming soon)") 
        with ex3:
            try:
                p_out = create_pdf(it_name, st.session_state.itinerary)
                st.download_button("📄 PDF", p_out, f"{safe_fn}.pdf", mime="application/pdf")
            except Exception as err:
                st.error(f"PDF Error: {err}. Please check for symbols.")

        for i, item in enumerate(st.session_state.itinerary):
            with st.expander(f"Day {i+1}: {item['Route']}", expanded=True):
                st.write(item['Description'])
                if st.button(f"Remove Day {i+1}", key=f"rem_{i}"):
                    st.session_state.itinerary.pop(i)
                    st.rerun()
