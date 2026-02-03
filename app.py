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
if "form_reset" not in st.session_state:
    st.session_state.form_reset = 0

# ================= STYLING & BACKGROUND =================
bg_img = "https://images.unsplash.com/photo-1586500036706-41963de24d8b?q=80&w=2574&auto=format&fit=crop"
st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
    background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("{bg_img}");
    background-size: cover; background-position: center; background-attachment: fixed;
}}
/* Faint placeholders to look clean */
input::placeholder, textarea::placeholder {{
    color: #cccccc !important; opacity: 0.3 !important;
}}
.stTextInput input, .stTextArea textarea {{ background-color: white !important; color: black !important; }}
</style>
""", unsafe_allow_html=True)

# ================= 1. COMPANY IDENTITY (ALWAYS VISIBLE) =================
# This is placed OUTSIDE the login check so it appears on the login page.
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:white; text-shadow:3px 3px 6px black; margin-bottom:0; font-size:3.5rem;'>EXCLUSIVE HOLIDAYS SRI LANKA</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#FFD700; font-style:italic; font-size:1.5rem; margin-top:0;'>\"Unforgettable Island Adventures Awaits\"</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ================= 2. LOGIN SYSTEM =================
if not st.session_state.authenticated:
    _, lbox, _ = st.columns([1, 1.2, 1])
    with lbox:
        with st.form("login_form"):
            st.subheader("🔐 Staff Access")
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    db = conn.read(worksheet="Sheet1", ttl=0)
                    match = db[(db["username"] == u) & (db["password"].astype(str) == p)]
                    if not match.empty:
                        st.session_state.authenticated = True
                        st.session_state.user_role = "Admin" if u.lower() in ["admin", "admin01"] else "Staff"
                        st.rerun()
                    else:
                        st.error("Invalid Credentials. Please try again.")
                except Exception:
                    st.error("Database connection error. Please contact Admin.")
        
        # Unable to sign in help
        st.markdown("<div style='text-align:center;'><a href='#' style='color:#FFD700; text-decoration:none; font-size:0.9rem;'>Unable to sign in? Contact Management</a></div>", unsafe_allow_html=True)
    st.stop()

# ================= 3. USER BAR (LOGOUT) =================
# This appears only after login
c_user, c_logout = st.columns([9, 1])
c_user.write(f"👤 Logged in as: **{st.session_state.user_role}**")
if c_logout.button("Logout"):
    st.session_state.clear()
    st.rerun()

# ================= 4. PDF ENGINE (BINARY ERROR FIX) =================
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
        # Replacing special characters that cause the binary byte error
        clean_desc = day['Description'].replace('✓', '-').encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 7, clean_desc)
        pdf.ln(5)
    return pdf.output(dest='S')

# ================= 5. APP CONTENT =================
if st.session_state.user_role == "Admin":
    st.header("🛠️ Admin Panel")
    st.info("Account Management tools are active. You can manage staff from the Google Sheet connected.")
else:
    st.header("✈️ Itinerary Builder")
    title = st.text_input("Itinerary Name", placeholder="e.g. 10 Day Paradise Tour")
    
    col = st.columns([2, 1, 1])
    route = col[0].text_input("Route", key=f"r_{st.session_state.form_reset}")
    dist = col[1].text_input("Distance", key=f"d_{st.session_state.form_reset}")
    dur = col[2].text_input("Duration", key=f"t_{st.session_state.form_reset}")
    desc = st.text_area("Daily Details", key=f"desc_{st.session_state.form_reset}")
    
    if st.button("➕ Add Day"):
        if route:
            st.session_state.itinerary.append({"Route": route, "Description": f"{dist} | {dur}\n{desc}"})
            st.session_state.form_reset += 1
            st.rerun()

    if st.session_state.itinerary:
        st.write("---")
        # Export Buttons
        b1, b2, b3 = st.columns(3)
        b1.download_button("📊 Excel Export", pd.DataFrame(st.session_state.itinerary).to_csv(index=False).encode('utf-8'), "trip.csv")
        b3.download_button("📄 PDF Export", create_pdf(title, st.session_state.itinerary), "trip.pdf", mime="application/pdf")
