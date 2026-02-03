import streamlit as st
import pandas as pd
import re
from io import BytesIO
from fpdf import FPDF
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

# ================= PDF ENGINE (FIXES BINARY ERROR) =================
def create_pdf(title, itinerary):
    pdf = FPDF()
    pdf.add_page()
    # Using 'Arial' or 'Helvetica' (standard core fonts) to avoid encoding crashes
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
        # Clean text for PDF to prevent binary byte errors
        clean_desc = day['Description'].replace('✓', '-').encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 7, clean_desc)
        pdf.ln(5)
    return pdf.output(dest='S')

# ================= STYLING =================
bg_img = "https://images.unsplash.com/photo-1586500036706-41963de24d8b?q=80&w=2574&auto=format&fit=crop"
st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
    background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url("{bg_img}");
    background-size: cover; background-position: center; background-attachment: fixed;
}}
/* Toned down placeholders */
input::placeholder, textarea::placeholder {{
    color: #cccccc !important; opacity: 0.5 !important;
}}
.stTextInput input, .stTextArea textarea {{ background-color: white !important; color: black !important; }}
</style>
""", unsafe_allow_html=True)

# ================= BRANDING DISPLAY (Always Visible) =================
def show_branding():
    if st.session_state.uploaded_logo:
        st.image(st.session_state.uploaded_logo, width=120)
    st.markdown("<h1 style='text-align:center; color:white; text-shadow:2px 2px 4px black; margin-bottom:0;'>EXCLUSIVE HOLIDAYS SRI LANKA</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#FFD700; font-style:italic; font-size:1.2rem; margin-top:0;'>\"Unforgettable Island Adventures Awaits\"</p>", unsafe_allow_html=True)

# ================= LOGIN SCREEN =================
if not st.session_state.authenticated:
    show_branding()
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
show_branding()

with st.sidebar:
    st.write(f"User: **{st.session_state.user_role}**")
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()
    st.write("---")
    # Logo Settings ONLY here
    st.subheader("⚙️ Logo Settings")
    logo_file = st.file_uploader("Update Company Logo", type=["png", "jpg"])
    if logo_file:
        st.session_state.uploaded_logo = logo_file

# --- 🛠️ ADMIN PANEL (Full Control) ---
if st.session_state.user_role == "Admin":
    st.header("🛠️ Admin Control Panel")
    db = load_user_db()
    
    t1, t2, t3 = st.tabs(["Add / Remove User", "Change Password", "User List"])
    
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Add User")
            nu = st.text_input("New Username", placeholder="username")
            np = st.text_input("New Password", type="password", placeholder="password")
            if st.button("Save User"):
                new_row = pd.DataFrame([{"username": nu, "password": np, "status": "Active"}])
                conn.update(worksheet="Sheet1", data=pd.concat([db, new_row], ignore_index=True))
                st.success("User added!"); st.rerun()
        with c2:
            st.subheader("Remove User")
            target_del = st.selectbox("Select User to Delete", db["username"].tolist())
            if st.button("Delete User", type="primary"):
                conn.update(worksheet="Sheet1", data=db[db["username"] != target_del])
                st.warning("User Deleted"); st.rerun()

    with t2:
        st.subheader("Change User Password")
        target_u = st.selectbox("Select User", db["username"].tolist(), key="cp")
        new_p = st.text_input("New Password", type="password", key="np")
        if st.button("Update Password"):
            db.loc[db["username"] == target_u, "password"] = new_p
            conn.update(worksheet="Sheet1", data=db)
            st.success("Password Updated")

    with t3:
        st.dataframe(db, use_container_width=True)

# --- ✈️ STAFF BUILDER ---
else:
    st.header("✈️ Itinerary Builder")
    it_name = st.text_input("Itinerary Name", placeholder="Trip Name")
    
    row1 = st.columns([2, 1, 1])
    r = row1[0].text_input("Route", placeholder="From - To", key=f"r_{st.session_state.form_reset}")
    d = row1[1].text_input("Distance", placeholder="KM", key=f"d_{st.session_state.form_reset}")
    t = row1[2].text_input("Duration", placeholder="Time", key=f"t_{st.session_state.form_reset}")
    
    num_a = st.selectbox("Activities", range(0, 11))
    acts = []
    for i in range(num_a):
        av = st.text_input(f"Activity {i+1}", key=f"a_{i}_{st.session_state.form_reset}")
        if av: acts.append(f"✓ {av}")
    
    desc = st.text_area("Description", key=f"desc_{st.session_state.form_reset}")
    
    if st.button("➕ Add Day"):
        if r:
            act_text = "\n".join(acts) + "\n\n" if acts else ""
            st.session_state.itinerary.append({"Route": r, "Description": f"{d} | {t}\n{act_text}{desc}"})
            st.session_state.form_reset += 1
            st.rerun()

    if st.session_state.itinerary:
        st.write("---")
        # Export Buttons
        cex, cpd = st.columns(2)
        cex.download_button("📊 Excel", pd.DataFrame(st.session_state.itinerary).to_csv(index=False).encode('utf-8'), "trip.csv")
        
        pdf_bytes = create_pdf(it_name, st.session_state.itinerary)
        cpd.download_button("📄 PDF", pdf_bytes, "trip.pdf", mime="application/pdf")

        for i, item in enumerate(st.session_state.itinerary):
            with st.expander(f"Day {i+1}: {item['Route']}", expanded=True):
                st.write(item['Description'])
                if st.button(f"Remove Day {i+1}", key=f"del_{i}"):
                    st.session_state.itinerary.pop(i)
                    st.rerun()
