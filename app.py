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
        # Fallback if sheet is unreachable
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

# ================= EXPORT ENGINES (FIXED PDF) =================

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
        # Clean text for PDF to prevent binary format errors shown in your screenshots
        safe_desc = day['Description'].replace('✓', '-').encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 7, safe_desc)
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
/* Faint placeholders as requested */
input::placeholder, textarea::placeholder {{
    color: #cccccc !important; opacity: 0.3 !important; font-weight: normal !important;
}}
.stTextInput input, .stTextArea textarea {{ background-color: white !important; color: black !important; }}
/* Logout placement */
.stButton button[kind="secondary"] {{ border-radius: 20px; }}
</style>
""", unsafe_allow_html=True)

# ================= BRANDING HEADER =================
def render_branding_section():
    # Logo Display
    if st.session_state.uploaded_logo:
        _, logocol, _ = st.columns([2, 1, 2])
        logocol.image(st.session_state.uploaded_logo, use_container_width=True)
    
    # Title and Motto
    st.markdown("<h1 style='text-align:center; color:white; text-shadow:3px 3px 6px black; margin-bottom:0;'>EXCLUSIVE HOLIDAYS SRI LANKA</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#FFD700; font-style:italic; font-size:1.3rem; margin-top:0;'>\"Unforgettable Island Adventures Awaits\"</p>", unsafe_allow_html=True)

# ================= APP LOGIC =================

# 1. Show Branding on Login Screen
if not st.session_state.authenticated:
    render_branding_section()
    st.write("---")
    _, lbox, _ = st.columns([1, 1.5, 1])
    with lbox:
        with st.form("login_form"):
            st.subheader("🔐 Staff Login")
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                db = load_user_db()
                match = db[(db["username"] == u) & (db["password"].astype(str) == p)]
                if not match.empty:
                    st.session_state.authenticated = True
                    st.session_state.user_role = "Admin" if u.lower() in ["admin", "admin01"] else "Staff"
                    st.rerun()
                else: st.error("Access Denied: Invalid Credentials")
    st.stop()

# 2. Show Branding + Logout after Login
render_branding_section()
col_spacer, col_logout = st.columns([9, 1])
if col_logout.button("Logout"):
    st.session_state.clear()
    st.rerun()

# ================= ADMIN TOOLS =================
if st.session_state.user_role == "Admin":
    st.markdown("---")
    st.header("🛠️ Administrator Control Panel")
    db = load_user_db()

    with st.sidebar:
        st.subheader("🖼️ Branding Settings")
        new_logo = st.file_uploader("Update Company Logo", type=["png", "jpg", "jpeg"])
        if new_logo:
            st.session_state.uploaded_logo = new_logo
            st.success("Logo Updated!")

    t1, t2, t3 = st.tabs(["User Management", "Security Settings", "Database View"])
    
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            st.write("#### Add User")
            add_u = st.text_input("Username", key="au")
            add_p = st.text_input("Password", type="password", key="ap")
            if st.button("Add New Staff"):
                upd = pd.concat([db, pd.DataFrame([{"username": add_u, "password": add_p, "status": "Active"}])], ignore_index=True)
                conn.update(worksheet="Sheet1", data=upd)
                st.success("User Registered!"); st.rerun()
        with c2:
            st.write("#### Remove User")
            del_u = st.selectbox("Select Account", db["username"].tolist(), key="du")
            if st.button("Delete User Account", type="primary"):
                conn.update(worksheet="Sheet1", data=db[db["username"] != del_u])
                st.warning("User Deleted!"); st.rerun()

    with t2:
        st.write("#### Password Reset")
        pu = st.selectbox("Target User", db["username"].tolist(), key="pu")
        pp = st.text_input("New Password", type="password", key="pp")
        if st.button("Update Password"):
            db.loc[db["username"] == pu, "password"] = pp
            conn.update(worksheet="Sheet1", data=db)
            st.success("Password updated!")

    with t3:
        st.dataframe(db, use_container_width=True)

# ================= STAFF ITINERARY BUILDER =================
else:
    st.markdown("---")
    st.header("✈️ Itinerary Builder")
    
    name = st.text_input("Itinerary Name", placeholder="e.g. 10 Days Culture Tour")
    
    r_col = st.columns([2, 1, 1])
    route = r_col[0].text_input("Route", placeholder="From - To", key=f"r_{st.session_state.form_reset}")
    dist = r_col[1].text_input("Distance", placeholder="KM", key=f"d_{st.session_state.form_reset}")
    dur = r_col[2].text_input("Time", placeholder="Hours/Mins", key=f"t_{st.session_state.form_reset}")
    
    num_act = st.selectbox("Number of Activities", range(0, 11))
    acts_input = [st.text_input(f"Activity {i+1}", key=f"a_{i}_{st.session_state.form_reset}") for i in range(num_act)]
    
    desc_input = st.text_area("Daily Description", key=f"desc_{st.session_state.form_reset}")
    
    if st.button("➕ Add Day to Itinerary"):
        if route:
            # Format activities with checkmarks
            act_str = "\n".join([f"✓ {a}" for a in acts_input if a]) + "\n\n" if any(acts_input) else ""
            st.session_state.itinerary.append({
                "Route": route, 
                "Description": f"{dist} | {dur}\n{act_str}{desc_input}"
            })
            st.session_state.form_reset += 1
            st.rerun()

    if st.session_state.itinerary:
        st.write("---")
        # THE EXPORT BUTTONS
        ex_col, wd_col, pd_col = st.columns(3)
        
        # Excel
        df_it = pd.DataFrame(st.session_state.itinerary)
        ex_col.download_button("📊 Excel Export", df_it.to_csv(index=False).encode('utf-8'), "itinerary.csv")
        
        # Word
        wd_col.download_button("📝 Word Export", create_word(name, st.session_state.itinerary), "itinerary.docx")
        
        # PDF
        pdf_data = create_pdf(name, st.session_state.itinerary)
        pd_col.download_button("📄 PDF Export", pdf_data, "itinerary.pdf", mime="application/pdf")

        # Display and Edit Days
        for i, item in enumerate(st.session_state.itinerary):
            with st.expander(f"Day {i+1}: {item['Route']}", expanded=True):
                st.write(item['Description'])
                if st.button(f"Remove Day {i+1}", key=f"rem_{i}"):
                    st.session_state.itinerary.pop(i)
                    st.rerun()
