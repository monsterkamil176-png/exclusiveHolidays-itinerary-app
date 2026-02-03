import streamlit as st
import os
import base64
import pandas as pd
from io import BytesIO
from docx import Document
from streamlit_gsheets import GSheetsConnection

# 1. Page Config
st.set_page_config(page_title="Exclusive Holidays SL", page_icon="✈️", layout="wide")

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_user_db():
    try:
        df = conn.read(worksheet="Sheet1", ttl=0) #
        if 'username' in df.columns and 'password' in df.columns:
            return df
        return None
    except:
        return None

def update_password_in_db(username, new_password):
    df = conn.read(worksheet="Sheet1", ttl=0)
    df.loc[df['username'] == username, 'password'] = str(new_password)
    conn.update(worksheet="Sheet1", data=df)
    st.cache_data.clear()

# Initialize Session States
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = []
if 'needs_password_change' not in st.session_state:
    st.session_state.needs_password_change = False

def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

# 2. Global Styling
st.markdown("""
    <style>
    header {visibility: hidden;}
    .stApp { background-color: #f4f7f9; }
    .stButton > button {
        background-color: #6495ED !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        height: 45px;
        width: 100%;
    }
    .main-card {
        background-color: #ffffff; padding: 40px; border-radius: 15px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); max-width: 600px; margin: auto;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN LOGIC ---
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        logo_base64 = get_base64("logo.png")
        if logo_base64:
            st.markdown(f'<div style="text-align: center; margin-top: 80px;"><img src="data:image/png;base64,{logo_base64}" width="180"></div>', unsafe_allow_html=True)
        st.markdown('<h2 style="text-align: center; color: #444;">Sign in</h2>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            u_input = st.text_input("Username", placeholder="Username", label_visibility="collapsed")
            p_input = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
            if st.form_submit_button("Sign In"):
                df = load_user_db()
                if df is not None:
                    user_row = df[df['username'] == u_input]
                    if not user_row.empty and str(user_row.iloc[0]['password']) == p_input:
                        st.session_state.authenticated = True
                        st.session_state.current_user = u_input
                        # Trigger password change for everyone except admin on their first login
                        if u_input != "admin01":
                            st.session_state.needs_password_change = True
                        st.rerun()
                    else:
                        st.error("Invalid Credentials")
    st.stop()

# --- FORCE PASSWORD CHANGE SCREEN ---
if st.session_state.needs_password_change:
    st.markdown('<div class="main-card" style="margin-top: 50px;">', unsafe_allow_html=True)
    st.subheader("🔒 Security Update Required")
    st.write("Please set a new password for your account before proceeding.")
    
    with st.form("change_pass_form"):
        new_p = st.text_input("New Password", type="password")
        conf_p = st.text_input("Confirm New Password", type="password")
        if st.form_submit_button("Update Password"):
            if new_p == conf_p and len(new_p) > 3:
                update_password_in_db(st.session_state.current_user, new_p)
                st.session_state.needs_password_change = False
                st.success("Password updated successfully!")
                st.rerun()
            else:
                st.error("Passwords do not match or are too short.")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- REST OF THE APP (Admin or Staff View) ---
# [Insert previous Admin/Staff Builder logic here...]
