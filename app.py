import streamlit as st
import os
import base64
import pandas as pd
from io import BytesIO
from fpdf import FPDF
from docx import Document
from streamlit_gsheets import GSheetsConnection

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Exclusive Holidays SL", page_icon="✈️", layout="wide")

# ================= DATABASE =================
conn = st.connection("gsheets", type=GSheetsConnection)

def load_user_db():
    try:
        return conn.read(worksheet="Sheet1", ttl=0)
    except:
        return None

# ================= SESSION STATE =================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = []
if 'builder_form_key' not in st.session_state:
    st.session_state.builder_form_key = 0

# ================= HELPERS =================
def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

def clean_for_pdf(text):
    if not text:
        return ""
    return text.encode("latin-1", "replace").decode("latin-1").replace("?", "")

# ================= STYLING =================
bg_img = "https://images.unsplash.com/photo-1586500036706-41963de24d8b?q=80&w=2574&auto=format&fit=crop"

st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
    background: linear-gradient(rgba(0,0,0,0.55), rgba(0,0,0,0.55)), url("{bg_img}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{
    background-color: rgba(255,255,255,0.95) !important;
    color: #1e1e1e !important;
}}
.stButton > button {{
    color: #000 !important;
    font-weight: 800 !important;
    background-color: #fff !important;
    border-radius: 8px;
    width: 100%;
}}
h1, h2, h3, p, label {{
    color: white !important;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
}}
</style>
""", unsafe_allow_html=True)

# ================= BRANDING =================
def display_branding():
    logo = get_base64("logo.png")
    if logo:
        st.markdown(
            f'<div style="text-align:center;"><img src="data:image/png;base64,{logo}" width="80"></div>',
            unsafe_allow_html=True
        )
    st.markdown("<h1 style='text-align:center;'>EXCLUSIVE HOLIDAYS</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;font-style:italic;'>Unforgettable Island Adventures Awaits</p>",
        unsafe_allow_html=True
    )

# ================= EXPORT FUNCTIONS =================
def create_word(title, itinerary):
    doc = Document()
    doc.add_heading(f"Itinerary: {title}", 0)
    for i, day in enumerate(itinerary):
        doc.add_heading(f"Day {i+1}: {day['Route']}", level=1)
        doc.add_paragraph(f"Distance: {day['Distance']} | Duration: {day['Time']}")
        doc.add_paragraph(day['Description'])
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

def create_pdf(title, itinerary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, clean_for_pdf("EXCLUSIVE HOLIDAYS SRI LANKA"), 0, 1, "C")
    pdf.ln(8)

    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, clean_for_pdf(f"Trip Plan: {title}"), 0, 1)

    for i, day in enumerate(itinerary):
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, clean_for_pdf(f"Day {i+1}: {day['Route']}"), 1, 1)

        pdf.set_font("helvetica", "I", 10)
        pdf.cell(
            0, 7,
            clean_for_pdf(f"Distance: {day['Distance']} | Duration: {day['Time']}"),
            0, 1
        )

        pdf.set_font("helvetica", "", 11)
        pdf.multi_cell(0, 7, clean_for_pdf(day['Description']))
        pdf.ln(4)

    return pdf.output(dest="S").encode("latin-1")

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Itinerary")
    return output.getvalue()

# ================= LOGIN =================
if not st.session_state.authenticated:
    display_branding()
    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                df = load_user_db()
                if df is not None and not df[
                    (df["username"] == u) & (df["password"].astype(str) == p)
                ].empty:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    st.stop()

# ================= MAIN APP =================
display_branding()

_, logout = st.columns([9, 1])
with logout:
    if st.button("Logout & Reset"):
        st.session_state.authenticated = False
        st.session_state.itinerary = []
        st.session_state.builder_form_key = 0
        st.rerun()

tab_build, tab_set = st.tabs(["✈️ Itinerary Builder", "Settings ⚙️"])

# ================= BUILDER =================
with tab_build:
    tour_title = st.text_input("Client Name")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        r = st.text_input("Route", key=f"r{st.session_state.builder_form_key}")
    with c2:
        d = st.text_input("Distance", key=f"d{st.session_state.builder_form_key}")
    with c3:
        t = st.text_input("Duration", key=f"t{st.session_state.builder_form_key}")

    desc = st.text_area("Main Description", key=f"desc{st.session_state.builder_form_key}")

    num = st.selectbox("How many activities?", range(0, 11))
    acts = []
    for i in range(num):
        a = st.text_input(f"Activity {i+1}", key=f"a{st.session_state.builder_form_key}{i}")
        if a:
            acts.append(f"- {a}")

    full_desc = desc + ("\n\n" + "\n".join(acts) if acts else "")

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Add Day"):
            if r:
                st.session_state.itinerary.append({
                    "Route": r,
                    "Distance": d,
                    "Time": t,
                    "Description": full_desc
                })
                st.session_state.builder_form_key += 1
                st.rerun()
    with b2:
        if st.button("Clear All"):
            st.session_state.itinerary = []
            st.rerun()

    if st.session_state.itinerary:
        st.markdown("---")
        st.subheader("Download Options")

        e1, e2, e3 = st.columns(3)
        df = pd.DataFrame(st.session_state.itinerary)

        with e1:
            st.download_button("Excel", to_excel(df), f"{tour_title}.xlsx")

        with e2:
            st.download_button("Word", create_word(tour_title, st.session_state.itinerary), f"{tour_title}.docx")

        with e3:
            try:
                st.download_button(
                    "PDF",
                    create_pdf(tour_title, st.session_state.itinerary),
                    f"{tour_title}.pdf",
                    mime="application/pdf"
                )
            except:
                st.error("PDF export failed. Remove emojis or special symbols.")

        st.markdown("---")
        for i, day in enumerate(st.session_state.itinerary):
            with st.expander(f"Day {i+1}: {day['Route']}", expanded=True):
                st.write(f"Distance: {day['Distance']} | Duration: {day['Time']}")
                st.write(day["Description"])

# ================= SETTINGS =================
with tab_set:
    st.write("Settings & Password Management")
