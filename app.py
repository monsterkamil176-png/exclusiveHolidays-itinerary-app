import streamlit as st
import os
import base64
import pandas as pd
from io import BytesIO
from docx import Document
from streamlit_gsheets import GSheetsConnection

# 1. Page Config - Must be the first Streamlit command
st.set_page_config(page_title="Exclusive Holidays SL", page_icon="✈️", layout="wide")

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_user_db():
    try:
        # worksheet="Sheet1" matches your spreadsheet tab
        df = conn.read(worksheet="Sheet1", ttl=0)
        if 'username' in df.columns and 'password' in df.columns:
            return dict(zip(df.username.astype(str), df.password.astype(str)))
        return None
    except:
        return None

def add_user_to_db(new_u, new_p):
    df = conn.read(worksheet="Sheet1", ttl=0)
    new_row = pd.DataFrame([{"username": str(new_u), "password": str(new_p)}])
    updated_df = pd.concat([df, new_row], ignore_index=True)
    conn.update(worksheet="Sheet1", data=updated_df)
    st.cache_data.clear()

# Initialize Session States
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = []

# HELPER: Image to base64
def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

# 2. Global Styling (Ensures Sidebar and Background are visible)
st.markdown("""
    <style>
    /* Hide default header but keep sidebar accessible */
    header {visibility: hidden;}
    
    /* Set a light grey background for the whole app */
    .stApp {
        background-color: #f4f7f9 !important;
    }
    
    /* Main Content Card styling */
    .main-container {
        background-color: white; 
        padding: 40px; 
        border-radius: 15px;
        max-width: 1000px; 
        margin: auto; 
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
    }
    
    /* Blue button styling */
    .stButton > button {
        background-color: #6495ED !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        height: 48px;
        font-weight: 600 !important;
    }
    
    /* Itinerary card styling */
    .itinerary-card {
        background-color: #f8f9fa; 
        padding: 25px; 
        border-radius: 12px; 
        margin-bottom: 20px; 
        border-left: 8px solid #6495ED; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN LOGIC ---
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        logo_path = "logo.png"
        logo_base64 = get_base64(logo_path)
        if logo_base64:
            st.markdown(f'<div style="text-align: center; margin-top: 80px;"><img src="data:image/png;base64,{logo_base64}" width="200"></div>', unsafe_allow_html=True)
        
        st.markdown('<h2 style="text-align: center; color: #444; font-weight: 500; margin-top: 20px;">Sign in to your account</h2>', unsafe_allow_html=True)

        u_input = st.text_input("Username", placeholder="Username", label_visibility="collapsed")
        p_input = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
        
        if st.button("Sign In", use_container_width=True):
            user_db = load_user_db()
            if user_db and u_input in user_db and str(user_db[u_input]) == p_input:
                st.session_state.authenticated = True
                st.session_state.current_user = u_input
                st.rerun()
            else:
                st.error("Access Denied: Invalid Credentials")
        
        st.markdown(f'<div style="text-align: center; margin-top: 20px;"><a href="mailto:monsterkamil176@gmail.com" style="color: #6495ED; text-decoration: none; font-size: 14px;">Unable to sign in?</a></div>', unsafe_allow_html=True)
    st.stop()

# --- SIDEBAR (Now properly defined for authenticated users) ---
with st.sidebar:
    st.markdown(f"### 👤 Logged in as: **{st.session_state.current_user}**")
    if st.button("Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()
    
    if st.session_state.current_user == "admin01":
        st.divider()
        st.subheader("🛠️ Admin Panel")
        with st.expander("➕ Add Staff"):
            n_u = st.text_input("New Username")
            n_p = st.text_input("New Password")
            if st.button("Save Staff"):
                if n_u and n_p:
                    add_user_to_db(n_u, n_p)
                    st.success("User Added")
                    st.rerun()
        with st.expander("🗑️ Remove Staff"):
            df_u = conn.read(worksheet="Sheet1", ttl=0)
            others = df_u[df_u['username'] != 'admin01']['username'].tolist()
            if others:
                u_del = st.selectbox("Select Staff", options=others)
                if st.button("Delete Forever", type="primary"):
                    up_df = df_u[df_u['username'] != u_del]
                    conn.update(worksheet="Sheet1", data=up_df)
                    st.cache_data.clear()
                    st.rerun()

# --- MAIN CONTENT AREA ---
# Wrap the whole builder in the main-container div for the white card look
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Logo and Company Header
logo_path = "logo.png"
logo_base64 = get_base64(logo_path)
if logo_base64:
    st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_base64}" width="180"></div>', unsafe_allow_html=True)

st.markdown('<h1 style="text-align: center; color: #333; margin-top: 10px;">Exclusive Holidays Itinerary Builder</h1>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# Builder Inputs
st.markdown("### 📝 Create New Journey")
tour_title = st.text_input("📍 Tour Title / Client Name", placeholder="e.g. 10 Days Luxury Tour - Mr. Smith")

c1, c2, c3 = st.columns([2, 1, 1])
with c1: r_in = st.text_input("Route", placeholder="Airport to Negombo")
with c2: d_in = st.text_input("Distance", placeholder="35 KM")
with c3: t_in = st.text_input("Time", placeholder="45 Mins")

desc_in = st.text_area("Description", placeholder="Describe the day's events...")

if st.button("➕ Add Day to Itinerary", use_container_width=True):
    if r_in:
        st.session_state.itinerary.append({
            "Route": r_in, "Distance": d_in, "Time": t_in, "Description": desc_in
        })
        st.rerun()

# Preview Area
if st.session_state.itinerary:
    st.markdown("---")
    st.markdown("### 🗺️ Itinerary Preview")
    for i, item in enumerate(st.session_state.itinerary):
        st.markdown(f'''
            <div class="itinerary-card">
                <h4 style="margin:0; color: #6495ED;">Day {i+1}: {item["Route"]}</h4>
                <p style="margin: 5px 0; font-weight: 600; color: #666;">
                    📏 {item["Distance"]} | ⏱️ {item["Time"]}
                </p>
                <p style="margin-top: 10px; color: #444;">{item["Description"]}</p>
            </div>
        ''', unsafe_allow_html=True)
        if st.button(f"🗑️ Remove Day {i+1}", key=f"rem_{i}"):
            st.session_state.itinerary.pop(i)
            st.rerun()

    if st.button("🔴 Clear All Data", use_container_width=True):
        st.session_state.itinerary = []
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
