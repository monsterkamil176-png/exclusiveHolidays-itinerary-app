import streamlit as st
import os
import base64
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
        return pd.DataFrame(columns=["username", "password"])

# ================= SESSION STATE =================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "first_name" not in st.session_state:
    st.session_state.first_name = ""
if "itinerary" not in st.session_state:
    st.session_state.itinerary = []
if "form_reset" not in st.session_state:
    st.session_state.form_reset = 0

# ================= HELPERS =================
def clean_strict(text):
    if not text: return ""
    # Strips symbols like 🔗 or emojis that crash FPDF
    return re.sub(r'[^a-zA-Z0-9\s\.,\-\(\):/!\?]', '', str(text))

def clean_filename(text):
    if not text: return "itinerary"
    return re.sub(r"[^A-Za-z0-9_-]+", "_", text).strip("_")

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
        pdf.multi_cell(0, 7, clean_strict(day["Description"]))
        pdf.ln(5)
    return bytes(pdf.output(dest='S'))

# ================= STYLING =================
bg_img = "https://images.unsplash.com/photo-1586500036706-41963de24d8b?q=80&w=2574&auto=format&fit=crop"
st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
    background: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url("{bg_img}");
    background-size: cover; background-position: center; background-attachment: fixed;
}}
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{
    background-color: rgba(255,255,255,0.95) !important; color: #1e1e1e !important;
}}
::placeholder {{ color: #444444 !important; opacity: 1 !important; }}
h1, h2, h3, p, label {{ color: white !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.8); }}
</style>
""", unsafe_allow_html=True)

# ================= LOGIN =================
if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align:center;'>EXCLUSIVE HOLIDAYS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;font-style:italic;'>Unforgettable Island Adventures Awaits</p>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.form("login_form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                db = load_user_db()
                user_row = db[(db["username"] == u) & (db["password"].astype(str) == p)]
                if not user_row.empty:
                    st.session_state.authenticated = True
                    st.session_state.user_role = "Admin" if u.lower() in ["admin", "admin01"] else "Staff"
                    st.session_state.first_name = u.split('_')[0].split('.')[0].capitalize()
                    st.rerun()
                else: st.error("Invalid credentials")
    st.stop()

# ================= HEADER =================
top1, top2 = st.columns([8, 2])
with top1:
    st.markdown(f"## Hello, {st.session_state.first_name}!")
    st.markdown("*Unforgettable Island Adventures Awaits*")
with top2:
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# ================= ADMIN PANEL =================
if st.session_state.user_role == "Admin":
    st.subheader("🛠️ Admin Panel: User Management")
    
    with st.container(border=True):
        st.write("### Register New Staff Member")
        new_u = st.text_input("New Username", placeholder="e.g. amal_perera")
        new_p = st.text_input("New Password", type="password", placeholder="••••••••")
        
        if st.button("Register User"):
            if new_u and new_p:
                current_db = load_user_db()
                if new_u in current_db["username"].values:
                    st.error("This username already exists.")
                else:
                    new_row = pd.DataFrame([{"username": new_u, "password": new_p}])
                    updated_db = pd.concat([current_db, new_row], ignore_index=True)
                    conn.update(worksheet="Sheet1", data=updated_db)
                    st.success(f"Successfully added {new_u}!")
                    st.rerun()
            else:
                st.warning("Please enter both username and password.")

    st.write("---")
    st.write("### Current System Users")
    st.dataframe(load_user_db(), use_container_width=True)

# ================= STAFF PANEL =================
else:
    st.subheader("✈️ Itinerary Builder")
    
    with st.expander("📸 Company Branding"):
        uploaded_logo = st.file_uploader("Upload Company Logo", type=["png", "jpg", "jpeg"])
        if uploaded_logo: st.image(uploaded_logo, width=150)
        st.info("Motto: Unforgettable Island Adventures Awaits")

    it_name = st.text_input("Itinerary Name", placeholder="Relax on Beach – 10 Days")
    
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: r = st.text_input("Route", placeholder="Airport - Negombo", key=f"r_{st.session_state.form_reset}")
    with c2: d = st.text_input("Distance", placeholder="9.5KM", key=f"d_{st.session_state.form_reset}")
    with c3: t = st.text_input("Duration", placeholder="30 Minutes", key=f"t_{st.session_state.form_reset}")
    
    num_a = st.selectbox("How many activities?", range(0, 11))
    act_list = []
    for i in range(num_a):
        a_val = st.text_input(f"Activity {i+1}", placeholder="Relaxing on the beach", key=f"a_{st.session_state.form_reset}_{i}")
        if a_val: act_list.append(f"✓ {a_val}") 
    
    desc = st.text_area("Description", placeholder="Negombo is a bustling,, historic coastal city.......", key=f"desc_{st.session_state.form_reset}")
    
    if st.button("➕ Add Day"):
        if r:
            full_desc = ("Activities:\n" + "\n".join(act_list) + "\n\n" if act_list else "") + desc
            st.session_state.itinerary.append({"Route": r, "Distance": d, "Time": t, "Description": full_desc})
            st.session_state.form_reset += 1
            st.rerun()

    if st.session_state.itinerary:
        st.markdown("---")
        fn = clean_filename(it_name)
        b1, b2, b3 = st.columns(3)
        with b1:
            csv = pd.DataFrame(st.session_state.itinerary).to_csv(index=False).encode('utf-8')
            st.download_button("📊 Excel (CSV)", csv, f"{fn}.csv")
        with b3:
            try:
                pdf_data = create_pdf(it_name, st.session_state.itinerary)
                st.download_button("📄 PDF", pdf_data, f"{fn}.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"PDF Error: {e}")

        for i, item in enumerate(st.session_state.itinerary):
            with st.expander(f"Day {i+1}: {item['Route']}", expanded=True):
                st.write(item['Description'])
                if st.button(f"Remove Day {i+1}", key=f"rem_{i}"):
                    st.session_state.itinerary.pop(i)
                    st.rerun()
