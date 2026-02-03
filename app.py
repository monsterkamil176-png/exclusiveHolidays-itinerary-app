import streamlit as st
import os
import base64
import pandas as pd
from io import BytesIO
from fpdf import FPDF
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
    except: return None

def update_user_password(username, new_password):
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

def remove_user_from_db(username):
    df = conn.read(worksheet="Sheet1", ttl=0)
    updated_df = df[df['username'] != username]
    conn.update(worksheet="Sheet1", data=updated_df)
    st.cache_data.clear()

# Initialize Session States
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'itinerary' not in st.session_state: st.session_state.itinerary = []
if 'builder_form_key' not in st.session_state: st.session_state.builder_form_key = 0

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
        background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url("{bg_img}");
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    .stTextInput input, .stTextArea textarea {{ background-color: rgba(255, 255, 255, 0.95) !important; color: #1e1e1e !important; }}
    ::placeholder {{ color: #777777 !important; opacity: 1; }}
    .stButton > button {{ color: #000000 !important; font-weight: 800 !important; background-color: #ffffff !important; }}
    h1, h2, h3, p, label {{ color: white !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.8); }}
    header, footer {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

def display_branding(logo_size=80):
    logo_base64 = get_base64("logo.png")
    if logo_base64:
        st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_base64}" width="{logo_size}"></div>', unsafe_allow_html=True)
    st.markdown('<h1 style="text-align: center; font-size: 28px;">EXCLUSIVE HOLIDAYS</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-style: italic;">"Unforgettable Island Adventures Awaits"</p>', unsafe_allow_html=True)

# --- EXPORT LOGIC ---
class ITINERARY_PDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 16)
        self.set_text_color(0, 51, 102)
        self.cell(0, 10, 'EXCLUSIVE HOLIDAYS SRI LANKA', 0, 1, 'C')
        self.ln(5)

def create_pdf(title, itinerary):
    pdf = ITINERARY_PDF()
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 10, f'Trip Plan: {title}', 0, 1, 'L')
    for i, day in enumerate(itinerary):
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 10, f'Day {i+1}: {day["Route"]}', 1, 1, 'L', fill=True)
        pdf.set_font('helvetica', '', 11)
        pdf.multi_cell(0, 7, day['Description'])
        pdf.ln(5)
    return pdf.output()

def to_word(title, itinerary):
    doc = Document()
    doc.add_heading(f'Itinerary: {title}', 0)
    for i, item in enumerate(itinerary):
        doc.add_heading(f'Day {i+1}: {item["Route"]}', level=1)
        doc.add_paragraph(item['Description'])
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- AUTH LOGIC (Omitted for brevity, keep your existing login blocks here) ---
# [Assuming st.session_state.authenticated check happens here]

if not st.session_state.get('authenticated', False):
    # (Your Login code goes here)
    st.write("Please Log In") # Placeholder
    st.stop()

display_branding()

# --- THE BUILDER ---
tab_build, tab_set = st.tabs(["✈️ Itinerary Builder", "Settings ⚙️"])

with tab_build:
    tour_title = st.text_input("Client Name", placeholder="e.g. John Doe", key="title_main")
    
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: r_in = st.text_input("Route", placeholder="Airport -> Colombo", key=f"r_{st.session_state.builder_form_key}")
    with c2: d_in = st.text_input("Distance", placeholder="30 KM", key=f"d_{st.session_state.builder_form_key}")
    with c3: t_in = st.text_input("Time", placeholder="1 Hr", key=f"t_{st.session_state.builder_form_key}")
    
    # --- DYNAMIC ACTIVITIES START ---
    st.markdown("### Activities")
    num_activities = st.selectbox("How many activities for this day?", range(1, 11), index=0)
    
    activity_list = []
    for j in range(num_activities):
        act = st.text_input(f"Activity {j+1}", placeholder=f"Enter activity {j+1} details...", key=f"act_{st.session_state.builder_form_key}_{j}")
        if act: activity_list.append(f"• {act}")
    
    # Combine activities into a description
    desc_in = "\n".join(activity_list)
    # --- DYNAMIC ACTIVITIES END ---
    
    if st.button("➕ Add Day to Itinerary"):
        if r_in:
            st.session_state.itinerary.append({
                "Route": r_in, 
                "Distance": d_in, 
                "Time": t_in, 
                "Description": desc_in
            })
            st.session_state.builder_form_key += 1
            st.rerun()

    if st.session_state.itinerary:
        st.markdown("---")
        # Export Buttons
        e1, e2, e3 = st.columns(3)
        with e1: st.button("📥 Excel (Logic Here)")
        with e2: st.download_button("📥 Word", data=to_word(tour_title, st.session_state.itinerary), file_name=f"{tour_title}.docx")
        with e3:
            pdf_data = create_pdf(tour_title, st.session_state.itinerary)
            st.download_button("📥 PDF", data=pdf_data, file_name=f"{tour_title}.pdf")

        # Display Added Days
        for i, item in enumerate(st.session_state.itinerary):
            st.markdown(f"**Day {i+1}: {item['Route']}**")
            st.write(item['Description'])
            if st.button("❌ Remove", key=f"rem_{i}"):
                st.session_state.itinerary.pop(i)
                st.rerun()

with tab_set:
    # (Settings Password change code goes here)
    pass
