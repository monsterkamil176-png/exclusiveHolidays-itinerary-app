import streamlit as st
import pandas as pd
from io import BytesIO
from fpdf import FPDF
from docx import Document
from streamlit_gsheets import GSheetsConnection

# ================= 1. PAGE SETUP =================
st.set_page_config(page_title="Exclusive Holidays SL", layout="wide")

# ================= 2. THE BRANDING (FORCED TO TOP) =================
# This appears for EVERYONE, including on the login page.
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:white; text-shadow:3px 3px 6px black; margin-bottom:0; font-size:3rem;'>EXCLUSIVE HOLIDAYS SRI LANKA</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#FFD700; font-style:italic; font-size:1.3rem; margin-top:0;'>\"Unforgettable Island Adventures Awaits\"</p>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.2);'>", unsafe_allow_html=True)

# ================= 3. SESSION STATE =================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "itinerary" not in st.session_state:
    st.session_state.itinerary = []
if "user_role" not in st.session_state:
    st.session_state.user_role = None

# ================= 4. STYLING =================
bg_img = "https://images.unsplash.com/photo-1586500036706-41963de24d8b?q=80&w=2574&auto=format&fit=crop"
st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
    background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("{bg_img}");
    background-size: cover; background-position: center; background-attachment: fixed;
}}
input::placeholder, textarea::placeholder {{ color: #cccccc !important; opacity: 0.3 !important; }}
.stTextInput input, .stTextArea textarea {{ background-color: white !important; color: black !important; }}
</style>
""", unsafe_allow_html=True)

# ================= 5. LOGIN GATE =================
if not st.session_state.authenticated:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.form("login_gate"):
            st.subheader("🔑 Staff Access")
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
                else: st.error("Invalid credentials")
        st.markdown("<div style='text-align:center;'><a href='mailto:admin@exclusiveholidays.com' style='color:#FFD700; text-decoration:none;'>Unable to sign in? Contact Admin</a></div>", unsafe_allow_html=True)
    st.stop()

# ================= 6. POST-LOGIN (LOGOUT & CONTENT) =================
c_info, c_logout = st.columns([9, 1])
c_info.write(f"Logged in as: **{st.session_state.user_role}**")
if c_logout.button("Logout"):
    st.session_state.clear()
    st.rerun()

# --- EXPORT LOGIC ---
def create_pdf(itinerary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16); pdf.cell(0, 10, "EXCLUSIVE HOLIDAYS SRI LANKA", 0, 1, "C")
    for i, day in enumerate(itinerary):
        pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, f"Day {i+1}: {day['Route']}", 1, 1)
        pdf.set_font("Arial", "", 10); pdf.multi_cell(0, 7, day['Description'].encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S')

# --- ROLE BASED VIEWS ---
if st.session_state.user_role == "Admin":
    st.header("🛠️ Admin Panel")
    conn = st.connection("gsheets", type=GSheetsConnection)
    db = conn.read(worksheet="Sheet1", ttl=0)
    st.dataframe(db, use_container_width=True)
    st.info("Management tools are active. Update your Google Sheet to manage users.")

else:
    st.header("✈️ Itinerary Builder")
    with st.container():
        r = st.text_input("Route", placeholder="e.g. Colombo to Kandy")
        d = st.text_area("Description", placeholder="Activities for the day...")
        if st.button("➕ Add Day"):
            st.session_state.itinerary.append({"Route": r, "Description": d})
            st.rerun()

    if st.session_state.itinerary:
        st.write("---")
        b1, b2 = st.columns(2)
        b1.download_button("📊 Excel Export", pd.DataFrame(st.session_state.itinerary).to_csv(index=False).encode('utf-8'), "trip.csv")
        b2.download_button("📄 PDF Export", create_pdf(st.session_state.itinerary), "trip.pdf", mime="application/pdf")
        
        for i, item in enumerate(st.session_state.itinerary):
            with st.expander(f"Day {i+1}: {item['Route']}"):
                st.write(item['Description'])
                if st.button(f"Remove Day {i+1}", key=f"rm_{i}"):
                    st.session_state.itinerary.pop(i)
                    st.rerun()
