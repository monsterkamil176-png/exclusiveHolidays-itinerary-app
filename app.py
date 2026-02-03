import streamlit as st
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
    except Exception:
        return pd.DataFrame(columns=["username", "password", "status"])

# ================= SESSION STATE =================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "itinerary" not in st.session_state:
    st.session_state.itinerary = []
if "form_reset" not in st.session_state:
    st.session_state.form_reset = 0
if "uploaded_logo" not in st.session_state:
    st.session_state.uploaded_logo = None

# ================= EXPORT ENGINES =================
def create_pdf(title, itinerary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "EXCLUSIVE HOLIDAYS SRI LANKA", 0, 1, "C")
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 5, "Unforgettable Island Adventures Awaits", 0, 1, "C")
    pdf.ln(10)
    for i, day in enumerate(itinerary):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, f"Day {i+1}: {day['Route']}", 1, 1)
        pdf.set_font("Helvetica", "", 11)
        safe_text = day['Description'].replace('✓', '-').encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 7, safe_text)
        pdf.ln(5)
    return pdf.output(dest='S')

def create_word(title, itinerary):
    doc = Document()
    doc.add_heading("EXCLUSIVE HOLIDAYS SRI LANKA", 0)
    for i, day in enumerate(itinerary):
        doc.add_heading(f"Day {i+1}: {day['Route']}", level=2)
        doc.add_paragraph(day['Description'])
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# ================= STYLING =================
bg_img = "https://images.unsplash.com/photo-1586500036706-41963de24d8b?q=80&w=2574&auto=format&fit=crop"
st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
    background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url("{bg_img}");
    background-size: cover; background-position: center; background-attachment: fixed;
}}
input::placeholder, textarea::placeholder {{
    color: #cccccc !important; opacity: 0.3 !important;
}}
.stTextInput input, .stTextArea textarea {{ background-color: white !important; color: black !important; }}
</style>
""", unsafe_allow_html=True)

# ================= 1. BRANDING (ALWAYS AT TOP) =================
if st.session_state.uploaded_logo:
    _, logocol, _ = st.columns([2, 1, 2])
    logocol.image(st.session_state.uploaded_logo, use_container_width=True)

st.markdown("<h1 style='text-align:center; color:white; text-shadow:3px 3px 6px black; margin-bottom:0;'>EXCLUSIVE HOLIDAYS SRI LANKA</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#FFD700; font-style:italic; font-size:1.3rem; margin-top:0;'>\"Unforgettable Island Adventures Awaits\"</p>", unsafe_allow_html=True)

# ================= 2. LOGIN & HELP LINK =================
if not st.session_state.authenticated:
    st.write("---")
    _, lbox, _ = st.columns([1, 1.5, 1])
    with lbox:
        with st.form("login_form"):
            st.subheader("🔑 Login")
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                db = load_user_db()
                match = db[(db["username"] == u) & (db["password"].astype(str) == p)]
                if not match.empty:
                    st.session_state.authenticated = True
                    st.session_state.user_role = "Admin" if u.lower() in ["admin", "admin01"] else "Staff"
                    st.rerun()
                else: st.error("Invalid Login")
        
        # Help link
        st.markdown("<div style='text-align:center;'><a href='mailto:admin@exclusiveholidays.com' style='color:#FFD700;'>Unable to sign in? Contact Admin</a></div>", unsafe_allow_html=True)
    st.stop()

# ================= 3. LOGOUT & CONTENT =================
c_info, c_logout = st.columns([9, 1])
c_info.write(f"Logged in: **{st.session_state.user_role}**")
if c_logout.button("Logout"):
    st.session_state.clear()
    st.rerun()

# --- ADMIN PANEL ---
if st.session_state.user_role == "Admin":
    st.markdown("---")
    st.header("🛠️ Admin Tools")
    db = load_user_db()
    with st.sidebar:
        st.subheader("Settings")
        new_logo = st.file_uploader("Upload Logo", type=["png", "jpg"])
        if new_logo: st.session_state.uploaded_logo = new_logo

    t1, t2 = st.tabs(["Users", "Passwords"])
    with t1:
        ca, cr = st.columns(2)
        with ca:
            nu = st.text_input("New User")
            np = st.text_input("New Password", type="password")
            if st.button("Add"):
                upd = pd.concat([db, pd.DataFrame([{"username": nu, "password": np, "status": "Active"}])], ignore_index=True)
                conn.update(worksheet="Sheet1", data=upd); st.rerun()
        with cr:
            du = st.selectbox("Delete", db["username"].tolist())
            if st.button("Confirm Delete"):
                conn.update(worksheet="Sheet1", data=db[db["username"] != du]); st.rerun()
    with t2:
        st.dataframe(db)

# --- STAFF BUILDER ---
else:
    st.markdown("---")
    st.header("✈️ Itinerary Builder")
    title = st.text_input("Trip Name")
    col = st.columns([2, 1, 1])
    route = col[0].text_input("Route", key=f"r_{st.session_state.form_reset}")
    dist = col[1].text_input("KM", key=f"d_{st.session_state.form_reset}")
    dur = col[2].text_input("Time", key=f"t_{st.session_state.form_reset}")
    desc = st.text_area("Description", key=f"desc_{st.session_state.form_reset}")
    
    if st.button("Add Day"):
        st.session_state.itinerary.append({"Route": route, "Description": f"{dist} | {dur}\n{desc}"})
        st.session_state.form_reset += 1; st.rerun()

    if st.session_state.itinerary:
        st.write("---")
        b1, b2, b3 = st.columns(3)
        b1.download_button("Excel", pd.DataFrame(st.session_state.itinerary).to_csv(index=False).encode('utf-8'), "trip.csv")
        b2.download_button("Word", create_word(title, st.session_state.itinerary), "trip.docx")
        b3.download_button("PDF", create_pdf(title, st.session_state.itinerary), "trip.pdf", mime="application/pdf")
