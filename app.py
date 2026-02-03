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
    df = conn.read(ttl=0) 
    return dict(zip(df.username.astype(str), df.password.astype(str)))

def add_user_to_db(new_u, new_p):
    df = conn.read(ttl=0)
    new_row = pd.DataFrame([{"username": str(new_u), "password": str(new_p)}])
    updated_df = pd.concat([df, new_row], ignore_index=True)
    conn.update(data=updated_df)
    st.cache_data.clear()

# Initialize Session States
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# HELPER: Image to base64
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
    .stApp {
        background: #f4f7f9; /* Light grey/blue background like the screenshot */
        background-size: cover;
    }
    .main-container {
        background-color: white; padding: 30px; border-radius: 15px;
        max-width: 900px; margin: auto; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    }
    /* Sign In Button Style */
    .stButton > button {
        background-color: #6495ED !important; /* Soft blue like the screenshot */
        color: white !important;
        border: none !important;
        border-radius: 5px !important;
        height: 45px;
        font-weight: 600 !important;
    }
    .itinerary-card {
        background-color: #ffffff; padding: 20px; border-radius: 15px; 
        margin-bottom: 15px; border-left: 6px solid #6495ED; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN LOGIC (MintHRM Style) ---
if not st.session_state.authenticated:
    # Centered Container for Login
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        st.write("") # Spacer
        # Display Logo
        logo_path = "logo.png"
        logo_base64 = get_base64(logo_path)
        if logo_base64:
            st.markdown(f'<div style="text-align: center; margin-top: 60px;"><img src="data:image/png;base64,{logo_base64}" width="180"></div>', unsafe_allow_html=True)
        
        # Login Card
        st.markdown("""
            <div style="background-color: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-top: 30px;">
                <h2 style="text-align: center; color: #555; font-weight: 400; margin-bottom: 30px; font-size: 22px;">Sign in to your account</h2>
            </div>
        """, unsafe_allow_html=True)

        # We place inputs over the visual card using a container
        with st.container():
            u_input = st.text_input("Username", placeholder="Username", label_visibility="collapsed")
            p_input = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
            
            if st.button("Sign In", use_container_width=True):
                try:
                    user_db = load_user_db()
                    if u_input in user_db and str(user_db[u_input]) == p_input:
                        st.session_state.authenticated = True
                        st.session_state.current_user = u_input
                        st.rerun()
                    else:
                        st.error("Invalid Username or Password")
                except:
                    st.error("Connection error with database.")
            
            st.markdown('<p style="text-align: center; color: #6495ED; font-size: 14px; margin-top: 15px;">Unable to sign in?</p>', unsafe_allow_html=True)
            
        st.markdown('<p style="text-align: center; color: #888; font-size: 13px; margin-top: 40px;">Exclusive Holidays Itinerary Portal</p>', unsafe_allow_html=True)
    st.stop()

# --- ADMIN SIDEBAR (Visible after login) ---
with st.sidebar:
    st.write(f"👤 User: **{st.session_state.current_user}**")
    if st.button("Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()
    
    if st.session_state.current_user == "admin01":
        st.divider()
        st.subheader("🛠️ Admin Panel")
        with st.expander("➕ Add New User"):
            new_u = st.text_input("New Username")
            new_p = st.text_input("New Password")
            if st.button("Save to Sheet"):
                if new_u and new_p:
                    add_user_to_db(new_u, new_p)
                    st.success(f"Added {new_u}!")
                    st.rerun()
        
        with st.expander("🗑️ Delete User"):
            df_users = conn.read(ttl=0)
            other_users = df_users[df_users['username'] != 'admin01']['username'].tolist()
            if other_users:
                user_to_delete = st.selectbox("Select user", options=other_users)
                if st.button("Confirm Delete", type="primary"):
                    updated_df = df_users[df_users['username'] != user_to_delete]
                    conn.update(data=updated_df)
                    st.cache_data.clear()
                    st.rerun()

# --- MAIN APP INTERFACE ---
st.markdown('<div class="main-container">', unsafe_allow_html=True)
st.title("✈️ Itinerary Builder")

if 'itinerary' not in st.session_state:
    st.session_state.itinerary = []
if 'tour_title' not in st.session_state:
    st.session_state.tour_title = ""

# Input Section
st.session_state.tour_title = st.text_input("📍 Tour Title", value=st.session_state.tour_title)

c1, c2, c3 = st.columns([2, 1, 1])
route = c1.text_input("Route")
dist = c2.text_input("Distance")
tm = c3.text_input("Time")
desc = st.text_area("Description")

if st.button("➕ Add Day"):
    if route:
        st.session_state.itinerary.append({"Route": route, "Distance": dist, "Time": tm, "Description": desc})
        st.rerun()

# Preview & Export
for i, item in enumerate(st.session_state.itinerary):
    st.markdown(f'<div class="itinerary-card"><b>Day {i+1}: {item["Route"]}</b><br>{item["Description"]}</div>', unsafe_allow_html=True)

if st.session_state.itinerary:
    if st.button("🗑️ Reset All"):
        st.session_state.itinerary = []
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
