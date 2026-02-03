import streamlit as st
import pandas as pd
import re
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

# ================= HELPERS (PDF SAFETY) =================
def make_pdf_safe(text):
    if not text: return ""
    # Standardizes characters to avoid binary data errors
    return text.encode('latin-1', 'replace').decode('latin-1')

def create_pdf(title, itinerary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "EXCLUSIVE HOLIDAYS SRI LANKA", 0, 1, "C")
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 5, "Unforgettable Island Adventures Awaits", 0, 1, "C")
    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, make_pdf_safe(f"Itinerary: {title}"), 0, 1)
    for i, day in enumerate(itinerary):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, make_pdf_safe(f"Day {i+1}: {day['Route']}"), 1, 1)
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 7, make_pdf_safe(day['Description']))
        pdf.ln(5)
    return pdf.output(dest='S').encode('latin-1')

# ================= STYLING =================
bg_img = "https://images.unsplash.com/photo-1586500036706-41963de24d8b?q=80&w=2574&auto=format&fit=crop"
st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
    background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url("{bg_img}");
    background-size: cover; background-position: center; background-attachment: fixed;
}}
/* Toned down placeholder intensity */
input::placeholder, textarea::placeholder {{
    color: #888888 !important; opacity: 0.7 !important; font-weight: normal !important;
}}
.stTextInput input, .stTextArea textarea {{ background-color: white !important; color: black !important; }}
</style>
""", unsafe_allow_html=True)

# ================= LOGIN LOGIC (STRICT SEPARATION) =================
if not st.session_state.authenticated:
    # Minimalist login without branding settings
    st.markdown("<h1 style='text-align:center; color:white;'>LOGIN</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                db = load_user_db()
                user = db[(db["username"] == u) & (db["password"].astype(str) == p)]
                if not user.empty:
                    st.session_state.authenticated = True
                    st.session_state.user_role = "Admin" if u.lower() in ["admin", "admin01"] else "Staff"
                    st.rerun()
                else: st.error("Invalid Login")
    st.stop()

# ================= POST-LOGIN CONTENT =================
# ONLY appears after login
st.markdown("<h1 style='text-align:center; color:white; margin-bottom:0;'>EXCLUSIVE HOLIDAYS SRI LANKA</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#FFD700; font-style:italic; font-size:1.2rem; margin-top:0;'>\"Unforgettable Island Adventures Awaits\"</p>", unsafe_allow_html=True)

with st.sidebar:
    st.write(f"Logged in as: **{st.session_state.user_role}**")
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()
    st.write("---")
    # Logo Settings moved here, hidden from Login
    st.subheader("🖼️ Company Logo Settings")
    logo = st.file_uploader("Upload Logo", type=["png", "jpg"])
    if logo: st.image(logo, width=150)

# --- 🛠️ ADMIN PANEL ---
if st.session_state.user_role == "Admin":
    st.header("🛠️ Admin Panel")
    db = load_user_db()
    t1, t2, t3 = st.tabs(["Add/Remove User", "Password Management", "Database View"])
    
    with t1:
        c_a, c_r = st.columns(2)
        with c_a:
            st.write("#### Add Staff")
            nu = st.text_input("New Username", placeholder="e.g. kamil.c")
            np = st.text_input("New Password", type="password")
            if st.button("Create User"):
                new_data = pd.DataFrame([{"username": nu, "password": np, "status": "Active"}])
                conn.update(worksheet="Sheet1", data=pd.concat([db, new_data], ignore_index=True))
                st.success("User added!"); st.rerun()
        with c_r:
            st.write("#### Remove Staff")
            ud = st.selectbox("Select User to Remove", db["username"].tolist())
            if st.button("Delete User", type="primary"):
                conn.update(worksheet="Sheet1", data=db[db["username"] != ud])
                st.warning("User deleted!"); st.rerun()

    with t2:
        st.write("#### Reset Password")
        tu = st.selectbox("User", db["username"].tolist(), key="reset_u")
        tp = st.text_input("New Password", type="password", key="reset_p")
        if st.button("Update"):
            db.loc[db["username"] == tu, "password"] = tp
            conn.update(worksheet="Sheet1", data=db)
            st.success("Updated!")

    with t3:
        st.dataframe(db, use_container_width=True)

# --- ✈️ STAFF BUILDER ---
else:
    st.header("✈️ Itinerary Builder")
    it_name = st.text_input("Itinerary Name", placeholder="e.g. Beach Holiday")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1: r = st.text_input("Route", placeholder="e.g. Airport - Negombo", key=f"r_{st.session_state.form_reset}")
    with col2: d = st.text_input("Distance", placeholder="e.g. 10KM", key=f"d_{st.session_state.form_reset}")
    with col3: t = st.text_input("Duration", placeholder="e.g. 30 Mins", key=f"t_{st.session_state.form_reset}")
    
    # Check Mark Activities
    num_a = st.selectbox("How many activities?", range(0, 11))
    acts = []
    for i in range(num_a):
        av = st.text_input(f"Activity {i+1}", key=f"act_{i}_{st.session_state.form_reset}")
        if av: acts.append(f"✓ {av}")
    
    desc = st.text_area("Description", key=f"desc_{st.session_state.form_reset}")
    
    if st.button("➕ Add Day"):
        if r:
            activity_str = "\n".join(acts) + "\n\n" if acts else ""
            st.session_state.itinerary.append({"Route": r, "Description": f"{d} | {t}\n{activity_str}{desc}"})
            st.session_state.form_reset += 1; st.rerun()

    if st.session_state.itinerary:
        st.write("---")
        # Export Buttons
        c_ex, c_pd = st.columns(2)
        c_ex.download_button("📊 Excel", pd.DataFrame(st.session_state.itinerary).to_csv(index=False).encode('utf-8'), "itinerary.csv")
        try:
            pdf_b = create_pdf(it_name, st.session_state.itinerary)
            c_pd.download_button("📄 PDF", pdf_b, "itinerary.pdf", mime="application/pdf")
        except: st.error("PDF format error. Avoid emojis.")

        for i, item in enumerate(st.session_state.itinerary):
            with st.expander(f"Day {i+1}: {item['Route']}", expanded=True):
                st.write(item['Description'])
                if st.button(f"Remove Day {i+1}", key=f"del_{i}"):
                    st.session_state.itinerary.pop(i); st.rerun()
