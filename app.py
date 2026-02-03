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
if "display_name" not in st.session_state:
    st.session_state.display_name = ""
if "itinerary" not in st.session_state:
    st.session_state.itinerary = []
if "form_reset" not in st.session_state:
    st.session_state.form_reset = 0

# ================= HELPERS =================
def clean_strict(text):
    """Prevents PDF crashes by removing emojis and non-standard symbols."""
    if not text: return ""
    return re.sub(r'[^a-zA-Z0-9\s\.,\-\(\):/!\?]', '', str(text))

def clean_filename(text):
    if not text: return "itinerary"
    return re.sub(r"[^A-Za-z0-9_-]+", "_", text).strip("_")

# ================= EXPORT LOGIC =================
def create_pdf(title, itinerary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", "B", 16)
    pdf.cell(0, 10, "EXCLUSIVE HOLIDAYS SRI LANKA", 0, 1, "C")
    pdf.set_font("Courier", "I", 10)
    pdf.cell(0, 5, "Unforgettable Island Adventures Awaits", 0, 1, "C")
    pdf.ln(10)
    pdf.set_font("Courier", "B", 14)
    pdf.cell(0, 10, f"Itinerary: {clean_strict(title)}", 0, 1)
    for i, day in enumerate(itinerary):
        pdf.set_font("Courier", "B", 12)
        pdf.cell(0, 10, clean_strict(f"Day {i+1}: {day['Route']}"), 1, 1)
        pdf.set_font("Courier", "I", 10)
        pdf.cell(0, 7, clean_strict(f"{day['Distance']} | {day['Time']}"), 0, 1)
        pdf.set_font("Courier", "", 11)
        pdf.multi_cell(0, 7, clean_strict(day['Description']))
        pdf.ln(5)
    return bytes(pdf.output(dest='S'))

def create_word(title, itinerary):
    doc = Document()
    doc.add_heading("EXCLUSIVE HOLIDAYS SRI LANKA", 0)
    doc.add_paragraph("Unforgettable Island Adventures Awaits").italic = True
    doc.add_heading(f"Itinerary: {title}", level=1)
    for i, day in enumerate(itinerary):
        doc.add_heading(f"Day {i+1}: {day['Route']}", level=2)
        doc.add_paragraph(f"{day['Distance']} | {day['Time']}")
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
    color: #000000 !important; opacity: 1 !important; font-weight: bold !important;
}}
.stTextInput input, .stTextArea textarea {{ background-color: #ffffff !important; color: #000000 !important; }}
.branding-container {{ text-align: center; color: white; padding: 20px; text-shadow: 2px 2px 4px black; }}
</style>
""", unsafe_allow_html=True)

# ================= BRANDING HEADER =================
def render_header():
    st.markdown("<div class='branding-container'><h1>EXCLUSIVE HOLIDAYS SRI LANKA</h1>"
                "<h3 style='color: #FFD700; font-style: italic;'>\"Unforgettable Island Adventures Awaits\"</h3></div>", 
                unsafe_allow_html=True)

# ================= LOGIN =================
if not st.session_state.authenticated:
    render_header()
    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.form("login_form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                db = load_user_db()
                user_match = db[(db["username"] == u) & (db["password"].astype(str) == p)]
                if not user_match.empty:
                    st.session_state.authenticated = True
                    st.session_state.user_role = "Admin" if u.lower() in ["admin", "admin01"] else "Staff"
                    st.session_state.display_name = u.split('.')[0].capitalize()
                    st.rerun()
                else: st.error("Invalid credentials")
    st.stop()

# ================= APP CONTENT =================
render_header()
c1, c2 = st.columns([8, 2])
with c1: st.write(f"### Hello, {st.session_state.display_name}!")
with c2: 
    if st.button("Logout & Reset"):
        st.session_state.clear()
        st.rerun()

# --- GLOBAL LOGO UPLOADER ---
with st.sidebar:
    st.write("### 📁 Global Settings")
    logo = st.file_uploader("Upload Company Logo", type=["png", "jpg"])
    if logo: st.image(logo, width=150)

# --- ADMIN VIEW ---
if st.session_state.user_role == "Admin":
    st.markdown("---")
    st.subheader("🛠️ Admin Panel")
    
    with st.container(border=True):
        st.write("#### Register New Staff Member")
        new_u = st.text_input("Username", placeholder="e.g. kamil.c")
        new_p = st.text_input("Password", type="password")
        if st.button("Save User"):
            if new_u and new_p:
                df = load_user_db()
                new_row = pd.DataFrame([{"username": new_u, "password": new_p, "status": "New"}])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                st.success("User added successfully!")
                st.rerun()
    
    st.write("#### User Database")
    st.dataframe(load_user_db(), use_container_width=True)

# --- STAFF VIEW ---
else:
    st.markdown("---")
    st.subheader("✈️ Itinerary Builder")
    
    it_name = st.text_input("Itinerary Name", placeholder="Relax on Beach – 10 Days")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1: r = st.text_input("Route", placeholder="Airport - Negombo", key=f"r_{st.session_state.form_reset}")
    with col2: d = st.text_input("Distance", placeholder="10KM", key=f"d_{st.session_state.form_reset}")
    with col3: t = st.text_input("Duration", placeholder="30 Minutes", key=f"t_{st.session_state.form_reset}")
    
    num_a = st.selectbox("How many activities?", range(0, 11))
    acts = []
    for i in range(num_a):
        a_val = st.text_input(f"Activity {i+1}", placeholder="Relaxing on beach", key=f"a_{st.session_state.form_reset}_{i}")
        if a_val: acts.append(f"✓ {a_val}") # Added Checkmark
    
    desc = st.text_area("Description", placeholder="Negombo is a bustling city...", key=f"desc_{st.session_state.form_reset}")
    
    if st.button("➕ Add Day"):
        if r:
            full_d = ("Activities: " + " • ".join(acts) + "\n\n" if acts else "") + desc
            st.session_state.itinerary.append({"Route": r, "Distance": d, "Time": t, "Description": full_d})
            st.session_state.form_reset += 1
            st.rerun()

    if st.session_state.itinerary:
        st.markdown("---")
        fn = clean_filename(it_name)
        b1, b2, b3 = st.columns(3)
        with b1:
            csv = pd.DataFrame(st.session_state.itinerary).to_csv(index=False).encode('utf-8')
            st.download_button("📊 Excel", csv, f"{fn}.csv")
        with b2:
            word_file = create_word(it_name, st.session_state.itinerary)
            st.download_button("📝 Word", word_file, f"{fn}.docx")
        with b3:
            try:
                pdf_file = create_pdf(it_name, st.session_state.itinerary)
                st.download_button("📄 PDF", pdf_file, f"{fn}.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"Error: {e}")

        for i, item in enumerate(st.session_state.itinerary):
            with st.expander(f"Day {i+1}: {item['Route']}", expanded=True):
                st.write(f"**{item['Distance']} | {item['Time']}**")
                st.write(item['Description'])
                if st.button(f"Remove Day {i+1}", key=f"rem_{i}"):
                    st.session_state.itinerary.pop(i)
                    st.rerun()
