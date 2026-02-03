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

# 2. THE CSS FIX: Restores EVERYTHING and kills the ghost boxes
bg_img = "https://images.unsplash.com/photo-1586500036706-41963de24d8b?q=80&w=2574&auto=format&fit=crop"

st.markdown(f"""
    <style>
    /* Background setup */
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3)), 
                    url("{bg_img}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    /* FIX: This specifically targets that white ghost box without hiding your content */
    div[data-testid="stVerticalBlock"] > div:has(> div:empty) {{
        display: none !important;
    }}
    
    [data-testid="stVerticalBlock"] {{
        background-color: transparent !important;
    }}

    /* Input Field Styling & Placeholders */
    .stTextInput input, .stTextArea textarea {{
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: #1e1e1e !important;
    }}
    
    /* Make example text (placeholders) dark enough to see */
    ::placeholder {{
        color: #555555 !important;
        opacity: 1;
    }}

    /* Button Styling: Solid white with dark bold text */
    .stButton > button {{
        color: #000000 !important;
        font-weight: 800 !important;
        background-color: #ffffff !important;
        border: 2px solid #ffffff !important;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
    }}

    /* Text Colors for Headings */
    h1, h2, h3, p, label {{
        color: white !important;
        text-shadow: 2px 2px 8px rgba(0,0,0,0.8);
    }}

    [data-testid="stHeader"], [data-testid="stDecoration"] {{
        background-color: rgba(0,0,0,0) !important;
    }}
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# --- PHASE 1: LOGIN ---
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        # LOGO RESTORED
        logo_base64 = get_base64("logo.png")
        if logo_base64:
            st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_base64}" width="220"></div>', unsafe_allow_html=True)
        
        # COMPANY NAME & MOTTO RESTORED
        st.markdown('<h1 style="text-align: center; font-size: 42px; margin-bottom: 0;">EXCLUSIVE HOLIDAYS</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align: center; font-size: 18px; font-style: italic; margin-top: 0;">"Crafting Unforgettable Sri Lankan Journeys"</p>', unsafe_allow_html=True)
        
        st.markdown('<h2 style="text-align: center; margin-top: 30px;">Welcome Back</h2>', unsafe_allow_html=True)
        with st.form("login_form"):
            u_input = st.text_input("Username", placeholder="Enter username here...")
            p_input = st.text_input("Password", type="password", placeholder="Enter password here...")
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
    st.stop()

# --- PHASE 2: PASSWORD CHANGE ---
if st.session_state.needs_password_change:
    st.markdown("## 🔒 Security Update")
    with st.form("pw_form"):
        new_p = st.text_input("New Password", type="password", placeholder="Min 4 characters")
        conf_p = st.text_input("Confirm New Password", type="password")
        if st.form_submit_button("Update Password"):
            if new_p == conf_p and len(new_p) >= 4:
                update_password_in_db(st.session_state.current_user, new_p)
                st.session_state.needs_password_change = False
                st.rerun()
    st.stop()

# --- PHASE 3: MAIN APP ---
t_col1, t_col2 = st.columns([8, 2])
with t_col2:
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

if st.session_state.current_user == "admin01":
    st.markdown("# 👨‍💼 Admin Panel")
    # Admin Tabs and logic...
    tab1, tab2 = st.tabs(["Add Staff", "Remove Staff"])
    with tab1:
        new_u = st.text_input("New Staff Username", placeholder="e.g. tour_guide_01")
        new_p = st.text_input("Temp Password", type="password")
        if st.button("Register Account"):
            if new_u and new_p:
                add_user_to_db(new_u, new_p)
                st.success("Account Created!")
else:
    st.markdown("# ✈️ Itinerary Builder")
    tour_title = st.text_input("Tour Title / Client Name", placeholder="e.g. Mr. John Doe - 10 Days Sri Lanka")
    
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: r_in = st.text_input("Route", placeholder="e.g. Airport -> Negombo")
    with c2: d_in = st.text_input("Distance", placeholder="e.g. 30 KM")
    with c3: t_in = st.text_input("Time", placeholder="e.g. 1 Hour")
    desc_in = st.text_area("Description", placeholder="Describe the day's activities here...")
    
    if st.button("➕ Add Day"):
        if r_in:
            st.session_state.itinerary.append({"Route": r_in, "Distance": d_in, "Time": t_in, "Description": desc_in})
            st.rerun()

    if st.session_state.itinerary:
        st.markdown("---")
        for i, item in enumerate(st.session_state.itinerary):
            st.markdown(f"### Day {i+1}: {item['Route']}")
            if st.button(f"Remove Day {i+1}", key=f"rem_{i}"):
                st.session_state.itinerary.pop(i)
                st.rerun()
