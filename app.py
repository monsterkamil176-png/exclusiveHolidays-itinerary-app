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
        df = conn.read(worksheet="Sheet1", ttl=0)
        return df
    except:
        return None

def update_password_in_db(username, new_password):
    df = conn.read(worksheet="Sheet1", ttl=0)
    df.loc[df['username'] == username, 'password'] = str(new_password)
    conn.update(worksheet="Sheet1", data=df)
    st.cache_data.clear()

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
if 'needs_password_change' not in st.session_state:
    st.session_state.needs_password_change = False

def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

# 2. Global Styling with Custom Background
bg_image_url = "https://wowiwalkers.com/wp-content/uploads/2023/05/Sigiriya-Rock-Sri-Lanka-1.jpg"

st.markdown(f"""
    <style>
    /* Background Image Styling */
    .stApp {{
        background: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), 
                    url("{bg_image_url}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    header {{visibility: hidden;}}
    
    /* Center Card Styling */
    .main-card {{
        background-color: rgba(255, 255, 255, 0.95); 
        padding: 40px; 
        border-radius: 20px; 
        box-shadow: 0 10px 30px rgba(0,0,0,0.3); 
        max-width: 900px; 
        margin: auto;
    }}
    
    .stButton > button {{
        background-color: #6495ED !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        height: 48px;
        width: 100%;
        border: none !important;
    }}

    .itinerary-card {{
        background-color: #f8f9fa; padding: 20px; border-radius: 12px; 
        margin-bottom: 15px; border-left: 8px solid #6495ED; 
    }}
    
    /* Input field adjustments */
    .stTextInput input, .stTextArea textarea {{
        border-radius: 8px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- PHASE 1: LOGIN (ENTER KEY ENABLED) ---
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<div class="main-card" style="margin-top: 50px; max-width: 450px;">', unsafe_allow_html=True)
        logo_base64 = get_base64("logo.png")
        if logo_base64:
            st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_base64}" width="180"></div>', unsafe_allow_html=True)
        else:
            st.markdown('<h1 style="text-align: center; color: #333;">Exclusive Holidays</h1>', unsafe_allow_html=True)
            
        st.markdown('<h3 style="text-align: center; color: #444; margin-bottom: 20px;">Welcome Back</h3>', unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=False):
            u_input = st.text_input("Username", placeholder="Username", label_visibility="collapsed")
            p_input = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
            if st.form_submit_button("Sign In"):
                df = load_user_db()
                if df is not None:
                    user_row = df[df['username'] == u_input]
                    if not user_row.empty and str(user_row.iloc[0]['password']) == p_input:
                        st.session_state.authenticated = True
                        st.session_state.current_user = u_input
                        if u_input != "admin01":
                            st.session_state.needs_password_change = True
                        st.rerun()
                    else:
                        st.error("Invalid Credentials")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- PHASE 2: FORCE PASSWORD CHANGE ---
if st.session_state.needs_password_change:
    st.markdown('<div class="main-card" style="margin-top: 100px; max-width: 500px;">', unsafe_allow_html=True)
    st.subheader("🔒 Update Your Password")
    st.info("First-time login: please update your password.")
    with st.form("change_pass_form"):
        new_p = st.text_input("New Password", type="password")
        conf_p = st.text_input("Confirm New Password", type="password")
        if st.form_submit_button("Save & Continue"):
            if new_p == conf_p and len(new_p) >= 4:
                update_password_in_db(st.session_state.current_user, new_p)
                st.session_state.needs_password_change = False
                st.rerun()
            else:
                st.error("Passwords must match and be at least 4 characters.")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- PHASE 3: MAIN APP CONTENT ---
# Header Area
top_l, top_r = st.columns([8, 1.5])
with top_r:
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.needs_password_change = False
        st.rerun()

# --- ADMIN PANEL ---
if st.session_state.current_user == "admin01":
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown('<h1 style="text-align: center; color: #333;">Staff Management</h1>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["➕ Create Account", "🗑️ Remove Account"])
    with tab1:
        new_u = st.text_input("New Staff Username")
        new_p = st.text_input("Temporary Password", type="password")
        if st.button("Register Staff"):
            if new_u and new_p:
                add_user_to_db(new_u, new_p)
                st.success(f"Account '{new_u}' added!")
    with tab2:
        df_u = load_user_db()
        others = df_u[df_u['username'] != 'admin01']['username'].tolist() if df_u is not None else []
        if others:
            u_to_del = st.selectbox("Select account to remove", options=others)
            if st.button("Delete Permanently", type="primary"):
                up_df = df_u[df_u['username'] != u_to_del]
                conn.update(worksheet="Sheet1", data=up_df)
                st.cache_data.clear()
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- STAFF BUILDER ---
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown('<h1 style="text-align: center; color: #333;">Itinerary Builder</h1>', unsafe_allow_html=True)
    
    st.subheader("📝 Journey Details")
    tour_title = st.text_input("Tour Title / Client Name")
    
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: r_in = st.text_input("Route")
    with c2: d_in = st.text_input("Distance")
    with c3: t_in = st.text_input("Time")
    desc_in = st.text_area("Description")
    
    if st.button("➕ Add Day"):
        if r_in:
            st.session_state.itinerary.append({"Route": r_in, "Distance": d_in, "Time": t_in, "Description": desc_in})
            st.rerun()

    # Preview/Export logic remains the same...
    if st.session_state.itinerary:
        st.divider()
        st.write("### Review & Export")
        for i, item in enumerate(st.session_state.itinerary):
            st.markdown(f'<div class="itinerary-card"><b>Day {i+1}: {item["Route"]}</b><br>{item["Description"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
