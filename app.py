import streamlit as st
import os, base64
import pandas as pd
from io import BytesIO
from docx import Document

# 1. Page Config
st.set_page_config(page_title="Exclusive Holidays SL", page_icon="✈️", layout="wide")

# HELPER: Image to Base64
def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

# 2. USER DATABASE INITIALIZATION
if 'user_db' not in st.session_state:
    # Default Admin Account
    st.session_state.user_db = {
        "admin01": "JklgHCnn#23"
    }

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# 3. LOGIN / LOGOUT FUNCTIONS
def login_user(user, pwd):
    if user in st.session_state.user_db and st.session_state.user_db[user] == pwd:
        st.session_state.logged_in = True
        st.session_state.current_user = user
        st.rerun()
    else:
        st.error("❌ Invalid Username or Password")

def logout_user():
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.rerun()

# 4. STYLING
st.markdown("""
    <style>
    header {visibility: hidden;}
    .main .block-container {padding-top: 1rem;}
    .stApp {
        background: linear-gradient(rgba(255,255,255,0.85), rgba(255,255,255,0.85)), 
                    url("https://images.unsplash.com/photo-1528127269322-539801943592?q=80&w=2070&auto=format&fit=crop");
        background-size: cover; background-attachment: fixed;
    }
    .main-container {
        background-color: rgba(255, 255, 255, 0.95); padding: 25px; border-radius: 20px;
        max-width: 900px; margin: auto; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.05);
    }
    button p { color: white !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# 5. UI LOGIC
if not st.session_state.logged_in:
    # --- LOGIN SCREEN ---
    st.markdown('<div class="main-container" style="max-width:400px; margin-top:100px; text-align:center;">', unsafe_allow_html=True)
    st.title("🔒 Login")
    user_input = st.text_input("Username")
    pass_input = st.text_input("Password", type="password")
    if st.button("Enter App", use_container_width=True):
        login_user(user_input, pass_input)
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- AUTHENTICATED APP ---
    
    # SIDEBAR: Admin Controls & Logout
    with st.sidebar:
        st.write(f"👤 Logged in as: **{st.session_state.current_user}**")
        if st.button("Logout", use_container_width=True):
            logout_user()
        
        st.divider()
        # ADMIN ONLY SECTION
        if st.session_state.current_user == "admin01":
            st.subheader("🛠️ Admin: Manage Users")
            new_user = st.text_input("New Username", key="new_u")
            new_pass = st.text_input("New Password", type="password", key="new_p")
            if st.button("Create User"):
                if new_user and new_pass:
                    st.session_state.user_db[new_user] = new_pass
                    st.success(f"User '{new_user}' created!")
                else:
                    st.warning("Please enter both fields.")

    # MAIN CONTENT
    logo_base64 = get_base64("logo.png")
    if logo_base64:
        st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_base64}" style="width: 220px; opacity: 0.8;"></div>', unsafe_allow_html=True)

    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.title("✈️ Exclusive Holidays SL")

    # (ITINERARY LOGIC STARTS HERE)
    if 'itinerary' not in st.session_state:
        st.session_state.itinerary = []
    
    # Summary Section
    if st.session_state.itinerary:
        total_days = len(st.session_state.itinerary)
        st.info(f"📅 Current Plan: {total_days} Days / {total_days - 1 if total_days > 0 else 0} Nights")

    # --- YOUR ITINERARY CODE CONTINUES BELOW ---
    st.markdown("### 📝 Build Your Journey")
    # ... [Rest of your text inputs and "Add Day" logic] ...
    
    st.markdown('</div>', unsafe_allow_html=True)
