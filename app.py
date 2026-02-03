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

def update_user_in_db(username, new_password):
    df = conn.read(worksheet="Sheet1", ttl=0)
    df.loc[df['username'] == username, ['password', 'status']] = [str(new_password), "Active"]
    conn.update(worksheet="Sheet1", data=df)
    st.cache_data.clear()

def add_user_to_db(new_u, new_p):
    df = conn.read(worksheet="Sheet1", ttl=0)
    new_row = pd.DataFrame([{"username": str(new_u), "password": str(new_p), "status": "New"}])
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

# 2. CSS Styling
bg_img = "https://images.unsplash.com/photo-1586500036706-41963de24d8b?q=80&w=2574&auto=format&fit=crop"

st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), url("{bg_img}");
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    div[data-testid="stVerticalBlock"] > div:has(> div:empty) {{ display: none !important; }}
    [data-testid="stVerticalBlock"] {{ background-color: transparent !important; }}
    
    .stTextInput input, .stTextArea textarea {{
        background-color: rgba(255, 255, 255, 0.95) !important;
        color: #1e1e1e !important;
    }}
    ::placeholder {{ color: #555555 !important; opacity: 1; }}
    .stButton > button {{
        color: #000000 !important; font-weight: 800 !important; background-color: #ffffff !important;
    }}
    h1, h2, h3, p, label {{ color: white !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.8); }}
    header {{visibility: hidden;}} footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

def display_branding(logo_size=100, title_size=28, motto_size=14):
    logo_base64 = get_base64("logo.png")
    if logo_base64:
        st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_base64}" width="{logo_size}"></div>', unsafe_allow_html=True)
    st.markdown(f'<h1 style="text-align: center; font-size: {title_size}px; margin-bottom: 0;">EXCLUSIVE HOLIDAYS</h1>', unsafe_allow_html=True)
    st.markdown(f'<p style="text-align: center; font-size: {motto_size}px; font-style: italic; margin-top: 0;">"Unforgettable Island Adventures Awaits"</p>', unsafe_allow_html=True)

# --- EXPORT LOGIC ---
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.index = df.index + 1
        df.to_excel(writer, sheet_name='Itinerary', index_label='Day')
    return output.getvalue()

def to_word(title, itinerary):
    doc = Document()
    doc.add_heading(f'Itinerary: {title}', 0)
    for i, item in enumerate(itinerary):
        doc.add_heading(f'Day {i+1}: {item["Route"]}', level=1)
        doc.add_paragraph(f'Distance: {item["Distance"]} | Time: {item["Time"]}')
        doc.add_paragraph(item['Description'])
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- PHASE 1: LOGIN ---
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        display_branding(logo_size=200, title_size=42, motto_size=18)
        with st.form("login_form"):
            u_input = st.text_input("Username")
            p_input = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
                df = load_user_db()
                if df is not None:
                    user_row = df[df['username'] == u_input]
                    if not user_row.empty and str(user_row.iloc[0]['password']) == p_input:
                        st.session_state.authenticated = True
                        st.session_state.current_user = u_input
                        if u_input != "admin01" and user_row.iloc[0]['status'] == "New":
                            st.session_state.needs_password_change = True
                        st.rerun()
                    else: st.error("Invalid Credentials")
    st.stop()

# --- PHASE 2: PASSWORD CHANGE ---
if st.session_state.needs_password_change:
    display_branding(logo_size=120)
    st.markdown("## 🔒 Set Your Permanent Password")
    with st.form("pw_form"):
        new_p = st.text_input("New Password", type="password")
        conf_p = st.text_input("Confirm New Password", type="password")
        if st.form_submit_button("Update & Continue"):
            if new_p == conf_p and len(new_p) >= 4:
                update_user_in_db(st.session_state.current_user, new_p)
                st.session_state.needs_password_change = False
                st.rerun()
            else: st.error("Passwords must match (min 4 chars).")
    st.stop()

# --- PHASE 3: MAIN APP ---
display_branding(logo_size=80, title_size=24, motto_size=12)

t_col1, t_col2 = st.columns([9, 1])
with t_col2:
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

if st.session_state.current_user == "admin01":
    st.markdown("### 👨‍💼 Admin Panel")
    tab1, tab2 = st.tabs(["Add Staff", "Remove Staff"])
    with tab1:
        # We use keys here so we can reset them
        new_u = st.text_input("New Username", key="new_user_input")
        new_p = st.text_input("Temp Password", type="password", key="new_pass_input")
        if st.button("Register Account"):
            if new_u and new_p:
                add_user_to_db(new_u, new_p)
                st.success(f"Added {new_u}!")
                # CLEAR FIELDS: This resets the inputs
                st.session_state.new_user_input = ""
                st.session_state.new_pass_input = ""
                st.rerun()

else:
    st.markdown("### ✈️ Itinerary Builder")
    # Added "key" to allow clearing
    tour_title = st.text_input("Tour Title / Client Name", placeholder="e.g. Smith Family - 7 Days", key="tour_title_input")
    
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: r_in = st.text_input("Route", placeholder="e.g. Airport -> Negombo", key="route_input")
    with c2: d_in = st.text_input("Distance", placeholder="e.g. 30 KM", key="dist_input")
    with c3: t_in = st.text_input("Time", placeholder="e.g. 1 Hr", key="time_input")
    desc_in = st.text_area("Description", key="desc_input")
    
    col_add, col_clear = st.columns([1, 1])
    with col_add:
        if st.button("➕ Add Day"):
            if r_in:
                st.session_state.itinerary.append({"Route": r_in, "Distance": d_in, "Time": t_in, "Description": desc_in})
                # Optional: Clear day-specific fields after adding
                st.session_state.route_input = ""
                st.session_state.dist_input = ""
                st.session_state.time_input = ""
                st.session_state.desc_input = ""
                st.rerun()
    
    with col_clear:
        if st.button("🗑️ Clear All"):
            st.session_state.itinerary = []
            st.session_state.tour_title_input = ""
            st.rerun()

    if st.session_state.itinerary:
        st.markdown("---")
        df_itin = pd.DataFrame(st.session_state.itinerary)
        
        ex1, ex2 = st.columns(2)
        with ex1:
            st.download_button("📥 Export to Excel", data=to_excel(df_itin), file_name=f"{tour_title}.xlsx")
        with ex2:
            st.download_button("📥 Export to Word", data=to_word(tour_title, st.session_state.itinerary), file_name=f"{tour_title}.docx")
        
        for i, item in enumerate(st.session_state.itinerary):
            st.markdown(f"**Day {i+1}: {item['Route']}**")
            if st.button(f"Remove Day {i+1}", key=f"rem_{i}"):
                st.session_state.itinerary.pop(i)
                st.rerun()
