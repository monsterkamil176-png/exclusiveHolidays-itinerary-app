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

# ================= EXPORT ENGINES =================
def create_pdf(title, itinerary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", "B", 16)
    pdf.cell(0, 10, "EXCLUSIVE HOLIDAYS SRI LANKA", 0, 1, "C")
    pdf.set_font("Courier", "I", 10)
    pdf.cell(0, 5, "Unforgettable Island Adventures Awaits", 0, 1, "C")
    pdf.ln(10)
    pdf.set_font("Courier", "B", 14)
    pdf.cell(0, 10, f"Itinerary: {title}", 0, 1)
    for i, day in enumerate(itinerary):
        pdf.set_font("Courier", "B", 12)
        pdf.cell(0, 10, f"Day {i+1}: {day['Route']}", 1, 1)
        pdf.multi_cell(0, 7, day['Description'])
        pdf.ln(5)
    return bytes(pdf.output(dest='S'))

def create_word(title, itinerary):
    doc = Document()
    doc.add_heading("EXCLUSIVE HOLIDAYS SRI LANKA", 0)
    doc.add_paragraph("Unforgettable Island Adventures Awaits").italic = True
    for i, day in enumerate(itinerary):
        doc.add_heading(f"Day {i+1}: {day['Route']}", level=1)
        doc.add_paragraph(day['Description'])
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# ================= STYLING =================
bg_img = "https://images.unsplash.com/photo-1586500036706-41963de24d8b?q=80&w=2574&auto=format&fit=crop"
st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
    background: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url("{bg_img}");
    background-size: cover; background-position: center; background-attachment: fixed;
}}
.stTextInput input, .stTextArea textarea {{ background-color: white !important; color: black !important; font-weight: bold !important; }}
input::placeholder {{ color: #222 !important; opacity: 1 !important; }}
</style>
""", unsafe_allow_html=True)

# ================= BRANDING (Motto & Logo) =================
def show_branding():
    st.markdown("<h1 style='text-align:center; color:white; text-shadow:2px 2px 4px black; margin-bottom:0;'>EXCLUSIVE HOLIDAYS SRI LANKA</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#FFD700; font-style:italic; font-size:1.3rem; margin-top:0;'>\"Unforgettable Island Adventures Awaits\"</p>", unsafe_allow_html=True)
    
    # Global Logo Upload (Visible to everyone)
    with st.expander("🖼️ COMPANY LOGO SETTINGS", expanded=False):
        logo_file = st.file_uploader("Upload your Company Logo here", type=["png", "jpg", "jpeg"])
        if logo_file:
            st.image(logo_file, width=150)

# ================= LOGIN =================
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

# ================= MAIN APP =================
show_branding()
st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())

# --- 🛠️ ADMIN PANEL (Add, Remove, Change Password) ---
if st.session_state.user_role == "Admin":
    st.header("🛠️ Admin Control Center")
    
    tabs = st.tabs(["➕ Add User", "❌ Remove User", "🔑 Change Password", "📊 User Database"])
    
    with tabs[0]:
        st.write("### Add New Staff member")
        with st.form("add_user"):
            nu = st.text_input("New Username")
            np = st.text_input("New Password", type="password")
            if st.form_submit_button("Save User"):
                db = load_user_db()
                updated = pd.concat([db, pd.DataFrame([{"username": nu, "password": np, "status": "Active"}])], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated)
                st.success(f"User {nu} added!")

    with tabs[1]:
        st.write("### Remove User")
        db = load_user_db()
        user_to_del = st.selectbox("Select user to remove", db["username"].tolist())
        if st.button("Confirm Delete"):
            updated = db[db["username"] != user_to_del]
            conn.update(worksheet="Sheet1", data=updated)
            st.warning(f"User {user_to_del} removed!")
            st.rerun()

    with tabs[2]:
        st.write("### Reset User Password")
        user_to_change = st.selectbox("Select user", db["username"].tolist(), key="pass_reset")
        new_pass = st.text_input("Enter New Password", type="password")
        if st.button("Update Password"):
            db.loc[db["username"] == user_to_change, "password"] = new_pass
            conn.update(worksheet="Sheet1", data=db)
            st.success(f"Password for {user_to_change} updated!")

    with tabs[3]:
        st.dataframe(load_user_db(), use_container_width=True)

# --- ✈️ STAFF PANEL (Itinerary Builder) ---
else:
    st.header("✈️ Itinerary Builder")
    it_name = st.text_input("Itinerary Name", placeholder="Relax on Beach – 10 Days")
    
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: r = st.text_input("Route", placeholder="Airport - Negombo", key=f"r_{st.session_state.form_reset}")
    with c2: d = st.text_input("Distance", placeholder="10KM", key=f"d_{st.session_state.form_reset}")
    with c3: t = st.text_input("Duration", placeholder="30 Minutes", key=f"t_{st.session_state.form_reset}")
    
    # Check Mark Activities
    num_a = st.selectbox("Number of Activities", range(0, 11))
    acts = []
    for i in range(num_a):
        av = st.text_input(f"Activity {i+1}", key=f"act_{i}_{st.session_state.form_reset}")
        if av: acts.append(f"✓ {av}")
    
    desc = st.text_area("Description", placeholder="Enter details here...", key=f"desc_{st.session_state.form_reset}")
    
    if st.button("➕ Add Day"):
        activity_str = "\n".join(acts) + "\n\n" if acts else ""
        st.session_state.itinerary.append({"Route": r, "Description": f"{d} | {t}\n{activity_str}{desc}"})
        st.session_state.form_reset += 1
        st.rerun()

    if st.session_state.itinerary:
        st.write("---")
        # ACTUAL DOWNLOAD BUTTONS
        col_ex, col_word, col_pdf = st.columns(3)
        with col_ex:
            st.download_button("📊 Excel", pd.DataFrame(st.session_state.itinerary).to_csv(index=False).encode('utf-8'), "itinerary.csv")
        with col_word:
            st.download_button("📝 Word", create_word(it_name, st.session_state.itinerary), "itinerary.docx")
        with col_pdf:
            st.download_button("📄 PDF", create_pdf(it_name, st.session_state.itinerary), "itinerary.pdf", mime="application/pdf")
        
        for i, day in enumerate(st.session_state.itinerary):
            with st.expander(f"Day {i+1}: {day['Route']}", expanded=True):
                st.write(day['Description'])
                if st.button(f"Remove Day {i+1}", key=f"del_{i}"):
                    st.session_state.itinerary.pop(i)
                    st.rerun()
