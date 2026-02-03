import streamlit as st
import os
import base64
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Page Config
st.set_page_config(page_title="Exclusive Holidays SL", page_icon="✈️", layout="wide")

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_user_db():
    try:
        df = conn.read(worksheet="Sheet1", ttl=0) # Matches your tab name
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
    }
    .itinerary-card {
        background-color: #ffffff; padding: 20px; border-radius: 12px; 
        margin-bottom: 15px; border-left: 8px solid #6495ED; 
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
            st.markdown(f'<div style="text-align: center; margin-top: 80px;"><img src="data:image/png;base64,{logo_base64}" width="180"></div>', unsafe_allow_html=True)
        
        st.markdown('<h2 style="text-align: center; color: #444;">Sign in</h2>', unsafe_allow_html=True)
        u_input = st.text_input("Username", placeholder="Username", label_visibility="collapsed")
        p_input = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
        
        if st.button("Sign In", use_container_width=True):
            user_db = load_user_db()
            if user_db and u_input in user_db and str(user_db[u_input]) == p_input:
                st.session_state.authenticated = True
                st.session_state.current_user = u_input
                st.rerun()
            else:
                st.error("Connection error with database or invalid credentials")
        
        st.markdown(f'<div style="text-align: center; margin-top: 15px;"><a href="mailto:monsterkamil176@gmail.com" style="color: #6495ED; text-decoration: none;">Unable to sign in?</a></div>', unsafe_allow_html=True)
    st.stop()

# --- SIDEBAR (FORCED POSITION) ---
# This must be outside of any other column or container logic to appear
with st.sidebar:
    st.title("Settings")
    st.write(f"👤 User: **{st.session_state.current_user}**")
    
    if st.button("Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()
    
    if st.session_state.current_user == "admin01":
        st.divider()
        st.subheader("🛠️ User Management")
        with st.expander("➕ Add New User"):
            new_u = st.text_input("New Username")
            new_p = st.text_input("New Password")
            if st.button("Save to Sheet"):
                if new_u and new_p:
                    add_user_to_db(new_u, new_p)
                    st.success("Added!")
                    st.rerun()
        
        with st.expander("🗑️ Delete User"):
            try:
                df_users = conn.read(worksheet="Sheet1", ttl=0)
                other_users = df_users[df_users['username'] != 'admin01']['username'].tolist()
                if other_users:
                    u_to_del = st.selectbox("Select user", options=other_users)
                    if st.button("Delete Forever", type="primary"):
                        updated_df = df_users[df_users['username'] != u_to_del]
                        conn.update(worksheet="Sheet1", data=updated_df)
                        st.cache_data.clear()
                        st.rerun()
            except:
                st.write("No users found.")

# --- MAIN APP INTERFACE ---
st.markdown('<div style="max-width: 1000px; margin: auto; padding: 20px;">', unsafe_allow_html=True)

# Branding
logo_path = "logo.png"
logo_base64 = get_base64(logo_path)
if logo_base64:
    st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_base64}" width="150"></div>', unsafe_allow_html=True)

st.markdown('<h1 style="text-align: center; color: #333;">Exclusive Holidays Itinerary Builder</h1>', unsafe_allow_html=True)
st.markdown("---")

# Builder Section
st.subheader("📝 Create New Journey")
tour_title = st.text_input("Tour Title / Client Name", placeholder="e.g. 10 Days Luxury Tour")

c1, c2, c3 = st.columns([2, 1, 1])
with c1: r_in = st.text_input("Route", placeholder="Airport to Negombo")
with c2: d_in = st.text_input("Distance", placeholder="35 KM")
with c3: t_in = st.text_input("Time", placeholder="45 Mins")

desc_in = st.text_area("Description", placeholder="Enter highlights...")

if st.button("➕ Add Day to Itinerary", use_container_width=True):
    if r_in:
        st.session_state.itinerary.append({"Route": r_in, "Distance": d_in, "Time": t_in, "Description": desc_in})
        st.rerun()

# Preview Section
if st.session_state.itinerary:
    st.divider()
    for i, item in enumerate(st.session_state.itinerary):
        st.markdown(f'''
            <div class="itinerary-card">
                <h4 style="margin:0; color: #6495ED;">Day {i+1}: {item["Route"]}</h4>
                <p>📏 {item["Distance"]} | ⏱️ {item["Time"]}</p>
                <p>{item["Description"]}</p>
            </div>
        ''', unsafe_allow_html=True)
        if st.button(f"Remove Day {i+1}", key=f"rem_{i}"):
            st.session_state.itinerary.pop(i)
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
