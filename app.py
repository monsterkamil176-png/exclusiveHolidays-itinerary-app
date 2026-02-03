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
if "form_reset_counter" not in st.session_state:
    st.session_state.form_reset_counter = 0

# ================= HELPERS =================
def get_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def clean_for_pdf(text):
    if not text: return ""
    # Strip emojis and symbols like the 'link' icon that cause PDF crashes
    return re.sub(r'[^a-zA-Z0-9\s\.,\-\(\):/]', '', str(text))

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
/* This makes placeholder text darker and visible */
input::placeholder, textarea::placeholder {{
    color: #555555 !important; opacity: 1 !important;
}}
.stButton > button {{
    background-color: #ffffff !important; color: #000000 !important; font-weight: 800; border-radius: 8px;
}}
h1, h2, h3, p, label {{ color: white !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.8); }}
</style>
""", unsafe_allow_html=True)

# ================= LOGIN SYSTEM =================
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
                    # Get first name only
                    st.session_state.display_name = u.split('_')[0].split('.')[0].capitalize()
                    st.rerun()
                else: st.error("Invalid credentials")
    st.stop()

# ================= SHARED HEADER =================
c_head, c_logout = st.columns([8, 2])
with c_head:
    st.markdown(f"## Hello, {st.session_state.display_name}!")
with c_logout:
    if st.button("Logout & Reset"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ================= ADMIN PAGE =================
if st.session_state.user_role == "Admin":
    st.subheader("🛠️ Admin Panel: User Management")
    with st.container(border=True):
        st.write("### Register New User")
        new_u = st.text_input("Username")
        new_p = st.text_input("Password", type="password")
        if st.button("Add User"):
            if new_u and new_p:
                df = load_user_db()
                if new_u not in df["username"].values:
                    new_data = pd.DataFrame([{"username": new_u, "password": new_p}])
                    updated = pd.concat([df, new_data], ignore_index=True)
                    conn.update(worksheet="Sheet1", data=updated)
                    st.success("User added!")
                    st.rerun()
    st.write("### Current Users")
    st.dataframe(load_user_db(), use_container_width=True)

# ================= STAFF PAGE =================
else:
    st.subheader("✈️ Itinerary Builder")
    
    # ITINERARY NAME
    it_name = st.text_input("Itinerary Name", placeholder="Relax on Beach – 10 Days")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1: 
        route = st.text_input("Route", placeholder="Airport - Negombo", key=f"r_{st.session_state.form_reset_counter}")
    with col2: 
        dist = st.text_input("Distance", placeholder="9.5KM", key=f"d_{st.session_state.form_reset_counter}")
    with col3: 
        dur = st.text_input("Duration", placeholder="30 Minutes", key=f"t_{st.session_state.form_reset_counter}")
    
    # ACTIVITIES FIRST
    num_acts = st.selectbox("How many activities?", range(0, 11))
    act_list = []
    for i in range(num_acts):
        a = st.text_input(f"Activity {i+1}", placeholder="Relaxing on the beach", key=f"a_{st.session_state.form_reset_counter}_{i}")
        if a: act_list.append(f"• {a}")
    
    # DESCRIPTION SECOND
    desc = st.text_area("Description", placeholder="Negombo is a bustling,, historic coastal city.......", key=f"desc_{st.session_state.form_reset_counter}")
    
    if st.button("➕ Add Day"):
        if route:
            full_desc = ("Activities:\n" + "\n".join(act_list) + "\n\n" if act_list else "") + desc
            st.session_state.itinerary.append({
                "Route": route, "Distance": dist, "Time": dur, "Description": full_desc
            })
            st.session_state.form_reset_counter += 1
            st.rerun()

    # DISPLAY LIST & EXPORT
    if st.session_state.itinerary:
        st.write("---")
        # PDF/Excel/Word Buttons here...
        for i, d in enumerate(st.session_state.itinerary):
            with st.expander(f"Day {i+1}: {d['Route']}", expanded=True):
                st.write(f"**{d['Distance']} | {d['Time']}**")
                st.write(d['Description'])
                if st.button(f"Remove Day {i+1}", key=f"rem_{i}"):
                    st.session_state.itinerary.pop(i)
                    st.rerun()
