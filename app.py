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
        # Connects to the worksheet named Sheet1
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

# HELPER: Image to base64 for branding
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
    .stButton > button, .stForm submit_button > button {
        background-color: #6495ED !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        height: 45px;
        width: 100%;
    }
    .main-card {
        background-color: #ffffff; padding: 40px; border-radius: 15px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); max-width: 900px; margin: auto;
    }
    .itinerary-card {
        background-color: #f8f9fa; padding: 20px; border-radius: 12px; 
        margin-bottom: 15px; border-left: 8px solid #6495ED; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN LOGIC (Enter Key Enabled) ---
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        logo_path = "logo.png"
        logo_base64 = get_base64(logo_path)
        if logo_base64:
            st.markdown(f'<div style="text-align: center; margin-top: 80px;"><img src="data:image/png;base64,{logo_base64}" width="180"></div>', unsafe_allow_html=True)
        
        st.markdown('<h2 style="text-align: center; color: #444;">Sign in</h2>', unsafe_allow_html=True)
        
        # Using st.form allows the "Enter" key to trigger the login
        with st.form("login_form", clear_on_submit=False):
            u_input = st.text_input("Username", placeholder="Username", label_visibility="collapsed")
            p_input = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
            submit_login = st.form_submit_button("Sign In")
            
            if submit_login:
                user_db = load_user_db()
                if user_db and u_input in user_db and str(user_db[u_input]) == p_input:
                    st.session_state.authenticated = True
                    st.session_state.current_user = u_input
                    st.rerun()
                else:
                    st.error("Invalid Credentials")
    st.stop()

# --- APP HEADER ---
top_l, top_r = st.columns([9, 1])
with top_r:
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

logo_path = "logo.png"
logo_base64 = get_base64(logo_path)
if logo_base64:
    st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_base64}" width="150"></div>', unsafe_allow_html=True)

# --- ADMIN VIEW ---
if st.session_state.current_user == "admin01":
    st.markdown('<h1 style="text-align: center; color: #333;">Staff Management</h1>', unsafe_allow_html=True)
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["➕ Create Account", "🗑️ Remove Account"])
    with tab1:
        new_u = st.text_input("Staff Username")
        new_p = st.text_input("Staff Password", type="password")
        if st.button("Save Account"):
            if new_u and new_p:
                add_user_to_db(new_u, new_p)
                st.success(f"Account for {new_u} added!")
    with tab2:
        df_u = conn.read(worksheet="Sheet1", ttl=0)
        others = df_u[df_u['username'] != 'admin01']['username'].tolist()
        if others:
            u_to_del = st.selectbox("Select account", options=others)
            if st.button("Delete Permanent", type="primary"):
                up_df = df_u[df_u['username'] != u_to_del]
                conn.update(worksheet="Sheet1", data=up_df)
                st.cache_data.clear()
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- STAFF VIEW (Itinerary Builder) ---
else:
    st.markdown('<h1 style="text-align: center; color: #333;">Exclusive Holidays Itinerary Builder</h1>', unsafe_allow_html=True)
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    
    st.subheader("📝 Journey Details")
    tour_title = st.text_input("Tour Title / Client Name", placeholder="e.g. Luxury Tour")
    
    # Builder Inputs
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: r_in = st.text_input("Route", placeholder="Airport to Negombo")
    with c2: d_in = st.text_input("Distance", placeholder="35 KM")
    with c3: t_in = st.text_input("Time", placeholder="45 Mins")
    desc_in = st.text_area("Description", placeholder="Daily highlights...")
    
    if st.button("➕ Add Day"):
        if r_in:
            st.session_state.itinerary.append({"Route": r_in, "Distance": d_in, "Time": t_in, "Description": desc_in})
            st.rerun()

    # EXPORT BUTTONS
    if st.session_state.itinerary:
        st.divider()
        st.markdown("### 📥 Export Itinerary")
        
        def create_word(data, title):
            doc = Document()
            doc.add_heading(title or "Itinerary", 0)
            for i, day in enumerate(data):
                doc.add_heading(f"Day {i+1}: {day['Route']}", level=1)
                doc.add_paragraph(f"Distance: {day['Distance']} | Time: {day['Time']}")
                doc.add_paragraph(day['Description'])
            out = BytesIO()
            doc.save(out)
            return out.getvalue()

        df_export = pd.DataFrame(st.session_state.itinerary)
        excel_out = BytesIO()
        with pd.ExcelWriter(excel_out, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name="Itinerary")
        
        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            st.download_button("📝 Download Word", data=create_word(st.session_state.itinerary, tour_title), file_name=f"{tour_title or 'Tour'}.docx")
        with col_ex2:
            st.download_button("📊 Download Excel", data=excel_out.getvalue(), file_name=f"{tour_title or 'Tour'}.xlsx")

    # PREVIEW CARDS
    if st.session_state.itinerary:
        st.divider()
        for i, item in enumerate(st.session_state.itinerary):
            st.markdown(f'<div class="itinerary-card"><b>Day {i+1}: {item["Route"]}</b><br>{item["Distance"]} | {item["Time"]}<br>{item["Description"]}</div>', unsafe_allow_html=True)
            if st.button(f"Remove Day {i+1}", key=f"rem_{i}"):
                st.session_state.itinerary.pop(i)
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
