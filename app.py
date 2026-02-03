import streamlit as st
import os
import base64
import pandas as pd
from io import BytesIO
from docx import Document
from streamlit_gsheets import GSheetsConnection

# 1. Page Config (Must be first)
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

# 2. Global Styling (Background + Glassmorphism + Header Fix)
bg_img = "https://images.unsplash.com/photo-1586500036706-41963de24d8b?q=80&w=2574&auto=format&fit=crop"

st.markdown(f"""
    <style>
    /* Force background and remove white header space */
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3)), 
                    url("{bg_img}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    [data-testid="stHeader"] {{
        background-color: rgba(0,0,0,0) !important;
    }}

    [data-testid="stDecoration"] {{
        display: none;
    }}

    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    .main-card {{
        background: rgba(255, 255, 255, 0.88);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        padding: 40px; 
        border-radius: 25px; 
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.2);
        max-width: 900px; 
        margin: auto;
        margin-top: 30px;
        color: #1e1e1e;
    }}
    
    .stButton > button, .stForm submit_button > button {{
        background-color: #6495ED !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        height: 48px;
        width: 100%;
        border: none !important;
        transition: 0.3s;
    }}

    .stButton > button:hover {{
        background-color: #4169E1 !important;
        transform: translateY(-1px);
    }}

    .itinerary-card {{
        background: rgba(255, 255, 255, 0.6);
        padding: 20px; 
        border-radius: 15px; 
        margin-bottom: 15px; 
        border-left: 10px solid #6495ED; 
    }}
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<div class="main-card" style="max-width: 450px;">', unsafe_allow_html=True)
        logo_base64 = get_base64("logo.png")
        if logo_base64:
            st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_base64}" width="200"></div>', unsafe_allow_html=True)
        
        st.markdown('<h2 style="text-align: center;">Welcome Back</h2>', unsafe_allow_html=True)
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
                        if u_input != "admin01":
                            st.session_state.needs_password_change = True
                        st.rerun()
                    else:
                        st.error("Invalid Username or Password")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- PASSWORD CHANGE ---
if st.session_state.needs_password_change:
    st.markdown('<div class="main-card" style="max-width: 500px;">', unsafe_allow_html=True)
    st.subheader("🔒 Security: Update Password")
    with st.form("change_pass_form"):
        new_p = st.text_input("New Password", type="password")
        conf_p = st.text_input("Confirm Password", type="password")
        if st.form_submit_button("Update & Enter"):
            if new_p == conf_p and len(new_p) >= 4:
                update_password_in_db(st.session_state.current_user, new_p)
                st.session_state.needs_password_change = False
                st.rerun()
            else:
                st.error("Passwords must match (min 4 chars).")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- APP CONTENT ---
st.markdown('<div class="main-card">', unsafe_allow_html=True)

# Top Bar inside the card
c_logo, c_space, c_logout = st.columns([2, 5, 1.5])
with c_logo:
    logo_base64 = get_base64("logo.png")
    if logo_base64:
        st.image(f"data:image/png;base64,{logo_base64}", width=120)
with c_logout:
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.needs_password_change = False
        st.rerun()

# ADMIN VIEW
if st.session_state.current_user == "admin01":
    st.title("👨‍💼 Admin Panel")
    tab1, tab2 = st.tabs(["Add Staff", "Remove Staff"])
    with tab1:
        new_u = st.text_input("New Username")
        new_p = st.text_input("Temp Password", type="password")
        if st.button("Register Account"):
            if new_u and new_p:
                add_user_to_db(new_u, new_p)
                st.success(f"Account '{new_u}' added!")
    with tab2:
        df_u = load_user_db()
        others = df_u[df_u['username'] != 'admin01']['username'].tolist() if df_u is not None else []
        if others:
            u_to_del = st.selectbox("Select user to delete", options=others)
            if st.button("Delete Forever", type="primary"):
                up_df = df_u[df_u['username'] != u_to_del]
                conn.update(worksheet="Sheet1", data=up_df)
                st.cache_data.clear()
                st.rerun()

# STAFF VIEW
else:
    st.title("✈️ Itinerary Builder")
    tour_title = st.text_input("Tour Title / Client Name")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1: r_in = st.text_input("Route")
    with col2: d_in = st.text_input("Distance")
    with col3: t_in = st.text_input("Time")
    desc_in = st.text_area("Day Description")
    
    if st.button("➕ Add Day"):
        if r_in:
            st.session_state.itinerary.append({"Route": r_in, "Distance": d_in, "Time": t_in, "Description": desc_in})
            st.rerun()

    if st.session_state.itinerary:
        st.divider()
        
        # Word Logic
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

        # Excel Logic
        df_export = pd.DataFrame(st.session_state.itinerary)
        excel_out = BytesIO()
        with pd.ExcelWriter(excel_out, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name="Itinerary")
        
        ex_col1, ex_col2 = st.columns(2)
        with ex_col1:
            st.download_button("📝 Export Word", data=create_word(st.session_state.itinerary, tour_title), file_name=f"{tour_title}.docx")
        with ex_col2:
            st.download_button("📊 Export Excel", data=excel_out.getvalue(), file_name=f"{tour_title}.xlsx")

        for i, item in enumerate(st.session_state.itinerary):
            st.markdown(f'<div class="itinerary-card"><b>Day {i+1}: {item["Route"]}</b><br>{item["Description"]}</div>', unsafe_allow_html=True)
            if st.button(f"Remove Day {i+1}", key=f"rem_{i}"):
                st.session_state.itinerary.pop(i)
                st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
