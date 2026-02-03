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
        # Robust encoding fix for your binary data errors
        safe_text = day['Description'].replace('✓', '-').encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 7, safe_text)
        pdf.ln(5)
    return pdf.output(dest='S')

def create_word(title, itinerary):
    doc = Document()
    doc.add_heading("EXCLUSIVE HOLIDAYS SRI LANKA", 0)
    doc.add_paragraph("Unforgettable Island Adventures Awaits").italic = True
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
/* Faint placeholders */
input::placeholder, textarea::placeholder {{
    color: #cccccc !important; opacity: 0.3 !important;
}}
.stTextInput input, .stTextArea textarea {{ background-color: white !important; color: black !important; }}
</style>
""", unsafe_allow_html=True)

# ================= BRANDING (MANDATORY DISPLAY) =================
# This section now runs BEFORE login check
if st.session_state.uploaded_logo:
    _, logocol, _ = st.columns([2, 1, 2])
    logocol.image(st.session_state.uploaded_logo, use_container_width=True)

st.markdown("<h1 style='text-align:center; color:white; text-shadow:3px 3px 6px black; margin-bottom:0;'>EXCLUSIVE HOLIDAYS SRI LANKA</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#FFD700; font-style:italic; font-size:1.3rem; margin-top:0;'>\"Unforgettable Island Adventures Awaits\"</p>", unsafe_allow_html=True)

# ================= LOGIN SYSTEM =================
if not st.session_state.authenticated:
    st.write("---")
    _, lbox, _ = st.columns([1, 1.5, 1])
    with lbox:
        with st.form("login_form"):
            st.subheader("🔑 Staff Access")
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                db = load_user_db()
                match = db[(db["username"] == u) & (db["password"].astype(str) == p)]
                if not match.empty:
                    st.session_state.authenticated = True
                    st.session_state.user_role = "Admin" if u.lower() in ["admin", "admin01"] else "Staff"
                    st.rerun()
                else: st.error("Invalid Credentials")
    st.stop()

# ================= USER BAR (LOGOUT) =================
c_user, c_logout = st.columns([8, 2])
c_user.write(f"Logged in as: **{st.session_state.user_role}**")
if c_logout.button("Logout & Exit"):
    st.session_state.clear()
    st.rerun()

# ================= ADMIN TOOLS =================
if st.session_state.user_role == "Admin":
    st.markdown("---")
    st.header("🛠️ Admin Control Panel")
    db = load_user_db()

    with st.sidebar:
        st.subheader("🖼️ Branding Settings")
        new_logo = st.file_uploader("Upload Company Logo", type=["png", "jpg"])
        if new_logo: st.session_state.uploaded_logo = new_logo

    t1, t2, t3 = st.tabs(["Add/Remove User", "Password Management", "User Database"])
    
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            st.write("#### Add Staff")
            nu = st.text_input("New Username", placeholder="e.g. kamil.c")
            np = st.text_input("New Password", type="password")
            if st.button("Save Account"):
                upd = pd.concat([db, pd.DataFrame([{"username": nu, "password": np, "status": "Active"}])], ignore_index=True)
                conn.update(worksheet="Sheet1", data=upd)
                st.success("User added!"); st.rerun()
        with c2:
            st.write("#### Remove Staff")
            du = st.selectbox("Select User", db["username"].tolist())
            if st.button("Delete Permanent", type="primary"):
                conn.update(worksheet="Sheet1", data=db[db["username"] != du])
                st.warning("Deleted!"); st.rerun()

    with t2:
        st.write("#### Change Password")
        su = st.selectbox("Target User", db["username"].tolist(), key="su")
        sp = st.text_input("New Password", type="password", key="sp")
        if st.button("Update"):
            db.loc[db["username"] == su, "password"] = sp
            conn.update(worksheet="Sheet1", data=db)
            st.success("Updated!")

    with t3: st.dataframe(db, use_container_width=True)

# ================= STAFF BUILDER =================
else:
    st.markdown("---")
    st.header("✈️ Itinerary Builder")
    title = st.text_input("Itinerary Name", placeholder="e.g. 7 Days Tour")
    
    col_r = st.columns([2, 1, 1])
    route = col_r[0].text_input("Route", placeholder="From - To", key=f"r_{st.session_state.form_reset}")
    dist = col_r[1].text_input("Distance", placeholder="KM", key=f"d_{st.session_state.form_reset}")
    dur = col_r[2].text_input("Duration", placeholder="Time", key=f"t_{st.session_state.form_reset}")
    
    num_a = st.selectbox("Activities", range(0, 11))
    acts = [st.text_input(f"Activity {i+1}", key=f"a_{i}_{st.session_state.form_reset}") for i in range(num_a)]
    desc = st.text_area("Description", key=f"desc_{st.session_state.form_reset}")
    
    if st.button("➕ Add Day"):
        if route:
            act_text = "\n".join([f"✓ {a}" for a in acts if a]) + "\n\n" if any(acts) else ""
            st.session_state.itinerary.append({"Route": route, "Description": f"{dist} | {dur}\n{act_text}{desc}"})
            st.session_state.form_reset += 1; st.rerun()

    if st.session_state.itinerary:
        st.write("---")
        # Export Buttons
        b1, b2, b3 = st.columns(3)
        b1.download_button("📊 Excel Export", pd.DataFrame(st.session_state.itinerary).to_csv(index=False).encode('utf-8'), "trip.csv")
        b2.download_button("📝 Word Export", create_word(title, st.session_state.itinerary), "trip.docx")
        b3.download_button("📄 PDF Export", create_pdf(title, st.session_state.itinerary), "trip.pdf", mime="application/pdf")

        for i, item in enumerate(st.session_state.itinerary):
            with st.expander(f"Day {i+1}: {item['Route']}", expanded=True):
                st.write(item['Description'])
                if st.button(f"Remove Day {i+1}", key=f"rm_{i}"):
                    st.session_state.itinerary.pop(i); st.rerun()
