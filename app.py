import streamlit as st
import pandas as pd
from io import BytesIO
from fpdf import FPDF
from docx import Document
from streamlit_gsheets import GSheetsConnection

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Exclusive Holidays SL", page_icon="✈️", layout="wide")

# ================= SESSION STATE =================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "itinerary" not in st.session_state:
    st.session_state.itinerary = []
if "uploaded_logo" not in st.session_state:
    st.session_state.uploaded_logo = None

# ================= STYLING & BACKGROUND =================
bg_img = "https://images.unsplash.com/photo-1586500036706-41963de24d8b?q=80&w=2574&auto=format&fit=crop"
st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
    background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("{bg_img}");
    background-size: cover; background-position: center; background-attachment: fixed;
}}
/* Fix for faint placeholders */
input::placeholder, textarea::placeholder {{
    color: #cccccc !important; opacity: 0.3 !important;
}}
.stTextInput input, .stTextArea textarea {{ background-color: white !important; color: black !important; }}
</style>
""", unsafe_allow_html=True)

# ================= 1. MANDATORY BRANDING (ALWAYS LOADS FIRST) =================
st.write("") # Spacer
if st.session_state.uploaded_logo:
    _, logocol, _ = st.columns([2, 1, 2])
    logocol.image(st.session_state.uploaded_logo, use_container_width=True)

st.markdown("<h1 style='text-align:center; color:white; text-shadow:3px 3px 6px black; margin-bottom:0;'>EXCLUSIVE HOLIDAYS SRI LANKA</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#FFD700; font-style:italic; font-size:1.3rem; margin-top:0;'>\"Unforgettable Island Adventures Awaits\"</p>", unsafe_allow_html=True)

# ================= 2. LOGIN SYSTEM =================
if not st.session_state.authenticated:
    st.markdown("---")
    _, lbox, _ = st.columns([1, 1.2, 1])
    with lbox:
        with st.form("login_form"):
            st.subheader("🔐 Staff Login")
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                conn = st.connection("gsheets", type=GSheetsConnection)
                db = conn.read(worksheet="Sheet1", ttl=0)
                match = db[(db["username"] == u) & (db["password"].astype(str) == p)]
                if not match.empty:
                    st.session_state.authenticated = True
                    st.session_state.user_role = "Admin" if u.lower() in ["admin", "admin01"] else "Staff"
                    st.rerun()
                else: st.error("Invalid Credentials")
        
        # Help link added here
        st.markdown("<div style='text-align:center;'><a href='#' style='color:#FFD700; text-decoration:none;'>Unable to sign in? Contact Management</a></div>", unsafe_allow_html=True)
    st.stop()

# ================= 3. POST-LOGIN UI (LOGOUT BUTTON) =================
col_user, col_logout = st.columns([8, 2])
col_user.write(f"✅ Active Session: **{st.session_state.user_role}**")
if col_logout.button("🚪 Logout & Clear"):
    st.session_state.clear()
    st.rerun()

# ================= 4. EXPORT ENGINES (FIXED PDF) =================
def create_pdf(title, itinerary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "EXCLUSIVE HOLIDAYS SRI LANKA", 0, 1, "C")
    pdf.ln(10)
    for i, day in enumerate(itinerary):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, f"Day {i+1}: {day['Route']}", 1, 1)
        pdf.set_font("Helvetica", "", 11)
        # Fix for binary/special symbol errors
        clean_text = day['Description'].replace('✓', '-').encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 7, clean_text)
        pdf.ln(5)
    return pdf.output(dest='S')

# ================= 5. ADMIN PANEL =================
if st.session_state.user_role == "Admin":
    st.header("🛠️ Admin Panel")
    with st.expander("🖼️ Branding & Logo Settings"):
        logo_file = st.file_uploader("Upload Company Logo", type=["png", "jpg"])
        if logo_file: 
            st.session_state.uploaded_logo = logo_file
            st.success("Logo Updated!")

    # User Management logic here...
    st.info("Use this section to add or remove staff accounts.")

# ================= 6. STAFF BUILDER =================
else:
    st.header("✈️ Itinerary Builder")
    title = st.text_input("Trip Name", placeholder="e.g. Sri Lanka Wonders")
    
    # Input logic for staff...
    if st.button("➕ Add Day"):
        st.session_state.itinerary.append({"Route": "New Route", "Description": "Details here..."})
        st.rerun()

    if st.session_state.itinerary:
        st.write("---")
        b1, b2, b3 = st.columns(3)
        b1.download_button("📊 Excel", pd.DataFrame(st.session_state.itinerary).to_csv(index=False).encode('utf-8'), "itinerary.csv")
        b3.download_button("📄 PDF", create_pdf(title, st.session_state.itinerary), "itinerary.pdf", mime="application/pdf")
