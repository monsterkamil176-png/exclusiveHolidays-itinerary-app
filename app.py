import streamlit as st
import os
import base64
import pandas as pd
from io import BytesIO
from docx import Document
from streamlit_gsheets import GSheetsConnection

# 1. Page Config - ALWAYS FIRST
st.set_page_config(page_title="Exclusive Holidays SL", page_icon="✈️", layout="wide")

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_user_db():
    try:
        # worksheet="Sheet1" matches your screenshot tab
        df = conn.read(worksheet="Sheet1", ttl=0)
        if 'username' in df.columns and 'password' in df.columns:
            return dict(zip(df.username.astype(str), df.password.astype(str)))
        return None
    except:
        return None

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

# 2. CSS STYLING (Forced Background and Sidebar visibility)
st.markdown("""
    <style>
    /* Force Background Color */
    .stApp {
        background-color: #f4f7f9 !important;
    }

    /* Ensure Sidebar is visible and styled */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e0e0e0;
    }

    /* The White Card for the Builder */
    .builder-card {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }

    /* Blue Button Styling */
    .stButton > button {
        background-color: #6495ED !important;
        color: white !important;
        border-radius: 8px !important;
        height: 45px;
        font-weight: 600 !important;
        width: 100%;
    }
    
    /* Hide top header bar */
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN LOGIC ---
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        logo_path = "logo.png"
        logo_base64 = get_base64(logo_path)
        if logo_base64:
            st.markdown(f'<div style="text-align: center; margin-top: 50px;"><img src="data:image/png;base64,{logo_base64}" width="200"></div>', unsafe_allow_html=True)
        
        # Transparent Login Area
        st.markdown('<h2 style="text-align: center; color: #444; margin-top: 20px;">Sign in</h2>', unsafe_allow_html=True)
        u_input = st.text_input("Username", placeholder="Username", label_visibility="collapsed")
        p_input = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
        
        if st.button("Sign In"):
            user_db = load_user_db()
            if user_db and u_input in user_db and str(user_db[u_input]) == p_input:
                st.session_state.authenticated = True
                st.session_state.current_user = u_input
                st.rerun()
            else:
                st.error("Invalid Username or Password")
        
        st.markdown(f'<div style="text-align: center; margin-top: 20px;"><a href="mailto:monsterkamil176@gmail.com" style="color: #6495ED; text-decoration: none;">Unable to sign in?</a></div>', unsafe_allow_html=True)
    st.stop()

# --- SIDEBAR (ONLY SHOWS AFTER LOGIN) ---
with st.sidebar:
    st.image("logo.png", width=150) if os.path.exists("logo.png") else None
    st.write(f"👤 **{st.session_state.current_user}**")
    st.divider()
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

# --- MAIN BUILDER INTERFACE ---
# We use a standard Streamlit container instead of complex HTML to prevent "vanishing" content
main_col1, main_col2, main_col3 = st.columns([0.1, 0.8, 0.1])

with main_col2:
    # Header Branding
    st.markdown('<h1 style="text-align: center; color: #333;">Exclusive Holidays Itinerary Builder</h1>', unsafe_allow_html=True)
    
    # White Card Start
    st.markdown('<div class="builder-card">', unsafe_allow_html=True)
    
    st.subheader("📝 Create New Journey")
    tour_title = st.text_input("Tour Title / Client Name", placeholder="e.g. 10 Days Luxury Tour")
    
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: r_in = st.text_input("Route", placeholder="Airport to Negombo")
    with c2: d_in = st.text_input("Distance", placeholder="35 KM")
    with c3: t_in = st.text_input("Time", placeholder="45 Mins")
    
    desc_in = st.text_area("Description", placeholder="Enter highlights...")
    
    if st.button("➕ Add Day to Itinerary"):
        if r_in:
            st.session_state.itinerary.append({"Route": r_in, "Distance": d_in, "Time": t_in, "Description": desc_in})
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True) # White Card End

    # Preview Section
    if st.session_state.itinerary:
        st.divider()
        for i, item in enumerate(st.session_state.itinerary):
            with st.expander(f"📍 Day {i+1}: {item['Route']}", expanded=True):
                st.write(f"**Distance:** {item['Distance']} | **Time:** {item['Time']}")
                st.write(item['Description'])
                if st.button(f"Remove Day {i+1}", key=f"del_{i}"):
                    st.session_state.itinerary.pop(i)
                    st.rerun()
