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
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"Itinerary: {title}", 0, 1)
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
    doc.add_paragraph("Unforgettable Island Adventures Awaits").italic = True
    doc.add_heading(f"Itinerary: {title}", level=1)
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
    color: #cccccc !important; opacity: 0.4 !important;
}}
.stTextInput input, .stTextArea textarea {{ background-color: white !important; color: black !important; }}
</style>
""", unsafe_allow_html=True)

# ================= BRANDING HEADER =================
def render_header():
    col_l, col_c, col_r = st.columns([1, 4, 1])
    with col_c:
        if st.session_state.uploaded_logo:
            st.image(st.session_state.uploaded_logo, width=100)
        st.markdown("<h1 style='text-align:center; color:white; text-shadow:2px 2px 4px black; margin-bottom:0;'>EXCLUSIVE HOLIDAYS SRI LANKA</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#FFD700; font-style:italic; font-size:1.1rem; margin-top:0;'>\"Unforgettable Island Adventures Awaits\"</p>", unsafe_allow_html=True)
    with col_r:
        if st.session_state.authenticated:
            if st.button("Logout & Reset"):
                st.session_state.clear()
                st.rerun()

# ================= APP FLOW =================
render_header()

if not st.session_state.authenticated:
    st.write("---")
    _, lcol, _ = st.columns([1, 1.5, 1])
    with lcol:
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

# ================= ADMIN TOOLS =================
if st.session_state.user_role == "Admin":
    st.markdown("---")
    st.header("🛠️ Admin Panel")
    db = load_user_db()
    
    with st.sidebar:
        st.subheader("⚙️ Company Branding")
        logo_up = st.file_uploader("Upload New Logo", type=["png", "jpg"])
        if logo_up: st.session_state.uploaded_logo = logo_up

    t1, t2, t3 = st.tabs(["Add/Remove Users", "Password Reset", "User List"])
    with t1:
        ca, cr = st.columns(2)
        with ca:
            nu = st.text_input("New User", placeholder="kamil.c")
            np = st.text_input("New Password", type="password")
            if st.button("Add User"):
                upd = pd.concat([db, pd.DataFrame([{"username": nu, "password": np, "status": "Active"}])], ignore_index=True)
                conn.update(worksheet="Sheet1", data=upd)
                st.success("Added!"); st.rerun()
        with cr:
            du = st.selectbox("Remove User", db["username"].tolist())
            if st.button("Delete Account", type="primary"):
                conn.update(worksheet="Sheet1", data=db[db["username"] != du])
                st.warning("Deleted!"); st.rerun()
    with t2:
        ru = st.selectbox("Select User", db["username"].tolist(), key="r_u")
        rp = st.text_input("Set New Password", type="password", key="r_p")
        if st.button("Update"):
            db.loc[db["username"] == ru, "password"] = rp
            conn.update(worksheet="Sheet1", data=db)
            st.success("Updated!")
    with t3: st.dataframe(db, use_container_width=True)

# ================= STAFF BUILDER =================
else:
    st.markdown("---")
    st.header("✈️ Itinerary Builder")
    it_name = st.text_input("Itinerary Name", placeholder="Beach Holiday")
    
    row = st.columns([2, 1, 1])
    r = row[0].text_input("Route", placeholder="Airport - Negombo", key=f"r_{st.session_state.form_reset}")
    d = row[1].text_input("Distance", placeholder="10KM", key=f"d_{st.session_state.form_reset}")
    t = row[2].text_input("Duration", placeholder="30 Mins", key=f"t_{st.session_state.form_reset}")
    
    num_a = st.selectbox("Activities", range(0, 11))
    acts = [st.text_input(f"Activity {i+1}", key=f"a_{i}_{st.session_state.form_reset}") for i in range(num_a)]
    desc = st.text_area("Description", key=f"desc_{st.session_state.form_reset}")
    
    if st.button("➕ Add Day"):
        if r:
            act_list = "\n".join([f"✓ {a}" for a in acts if a]) + "\n\n" if any(acts) else ""
            st.session_state.itinerary.append({"Route": r, "Description": f"{d} | {t}\n{act_list}{desc}"})
            st.session_state.form_reset += 1; st.rerun()

    if st.session_state.itinerary:
        st.write("---")
        # THE MISSING EXPORT BUTTONS
        b1, b2, b3 = st.columns(3)
        df_exp = pd.DataFrame(st.session_state.itinerary)
        
        b1.download_button("📊 Excel Export", df_exp.to_csv(index=False).encode('utf-8'), "trip.csv")
        b2.download_button("📝 Word Export", create_word(it_name, st.session_state.itinerary), "trip.docx")
        b3.download_button("📄 PDF Export", create_pdf(it_name, st.session_state.itinerary), "trip.pdf", mime="application/pdf")

        for i, item in enumerate(st.session_state.itinerary):
            with st.expander(f"Day {i+1}: {item['Route']}", expanded=True):
                st.write(item['Description'])
                if st.button(f"Remove Day {i+1}", key=f"rm_{i}"):
                    st.session_state.itinerary.pop(i); st.rerun()
