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

def display_branding():
    logo_base64 = get_base64("logo.png")
    if logo_base64:
        st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_base64}" width="80"></div>', unsafe_allow_html=True)
    st.markdown('<h1 style="text-align: center; font-size: 28px; margin-bottom:0;">EXCLUSIVE HOLIDAYS</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-style: italic; margin-top:0;">"Unforgettable Island Adventures Awaits"</p>', unsafe_allow_html=True)

# --- EXPORTS ---
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Itinerary')
    return output.getvalue()

def to_word(title, itinerary):
    doc = Document()
    doc.add_heading(f'Itinerary: {title}', 0)
    for i, item in enumerate(itinerary):
        doc.add_heading(f'Day {i+1}: {item["Route"]}', level=1)
        doc.add_paragraph(item['Description'])
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

def create_pdf(title, itinerary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 16)
    pdf.cell(0, 10, 'EXCLUSIVE HOLIDAYS SRI LANKA', 0, 1, 'C')
    pdf.ln(10)
    
    # Cleaning the title and description of non-latin characters to prevent crash
    clean_title = title.encode('latin-1', 'replace').decode('latin-1')
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 10, f'Trip Plan: {clean_title}', 0, 1, 'L')
    
    for i, day in enumerate(itinerary):
        pdf.set_font('helvetica', 'B', 12)
        clean_route = day["Route"].encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(0, 10, f'Day {i+1}: {clean_route}', 1, 1, 'L')
        
        pdf.set_font('helvetica', '', 11)
        clean_desc = day['Description'].encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 7, clean_desc)
        pdf.ln(5)
    return pdf.output()

# --- MAIN APP UI ---
if not st.session_state.authenticated:
    # (Put your login logic here - for now assuming authenticated)
    st.session_state.authenticated = True 

display_branding()

# --- LOGOUT BUTTON (TOP RIGHT) ---
col_main, col_logout = st.columns([9, 1])
with col_logout:
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

tab_build, tab_set = st.tabs(["✈️ Itinerary Builder", "Settings ⚙️"])

with tab_build:
    tour_title = st.text_input("Client Name", placeholder="e.g. Smith Family", key="title_main")
    
    colA, colB, colC = st.columns([2, 1, 1])
    with colA: r_in = st.text_input("Route", placeholder="Negombo -> Kandy", key=f"r_{st.session_state.builder_form_key}")
    with colB: d_in = st.text_input("Distance", placeholder="120 KM", key=f"d_{st.session_state.builder_form_key}")
    with colC: t_in = st.text_input("Time", placeholder="3 Hrs", key=f"t_{st.session_state.builder_form_key}")
    
    desc_box = st.text_area("General Description", placeholder="Enter highlights...", key=f"desc_{st.session_state.builder_form_key}")
    
    num_activities = st.selectbox("Number of specific activities", range(0, 11), index=0)
    activity_list = []
    for j in range(num_activities):
        act = st.text_input(f"Activity {j+1}", key=f"act_{st.session_state.builder_form_key}_{j}")
        if act: activity_list.append(f"• {act}")
    
    full_description = desc_box + "\n" + "\n".join(activity_list)
    
    btn_col1, btn_col2 = st.columns([1, 1])
    with btn_col1:
        if st.button("➕ Add Day"):
            if r_in:
                st.session_state.itinerary.append({"Route": r_in, "Distance": d_in, "Time": t_in, "Description": full_description})
                st.session_state.builder_form_key += 1
                st.rerun()
    with btn_col2:
        if st.button("🗑️ Clear All Itinerary"):
            st.session_state.itinerary = []
            st.rerun()

    if st.session_state.itinerary:
        st.markdown("---")
        # --- EXPORT BUTTONS ---
        e1, e2, e3 = st.columns(3)
        with e1:
            df_export = pd.DataFrame(st.session_state.itinerary)
            st.download_button("📥 Excel", data=to_excel(df_export), file_name=f"{tour_title}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with e2:
            st.download_button("📥 Word", data=to_word(tour_title, st.session_state.itinerary), file_name=f"{tour_title}.docx")
        with e3:
            try:
                pdf_data = create_pdf(tour_title, st.session_state.itinerary)
                st.download_button("📥 PDF", data=pdf_data, file_name=f"{tour_title}.pdf", mime="application/pdf")
            except Exception as e:
                st.error("Encoding error in PDF. Please remove any emojis or symbols.")

        for i, item in enumerate(st.session_state.itinerary):
            st.markdown(f"### Day {i+1}: {item['Route']}")
            st.write(item['Description'])
            if st.button(f"Remove Day {i+1}", key=f"rem_{i}"):
                st.session_state.itinerary.pop(i)
                st.rerun()
