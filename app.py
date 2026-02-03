mport streamlit as st
import pandas as pd
import re
from io import BytesIO
from fpdf import FPDF
from streamlit_gsheets import GSheetsConnection

# ================= 1. PAGE CONFIG =================
st.set_page_config(page_title="Exclusive Holidays SL", page_icon="✈️", layout="wide")

# ================= 2. MANDATORY BRANDING (FORCED TO TOP) =================
# This section MUST stay above the login logic to appear on the login screen.
st.markdown("""
    <div style='text-align:center; padding:20px;'>
        <h1 style='color:white; text-shadow: 3px 3px 6px #000000; margin-bottom:0; font-size:3rem;'>
            EXCLUSIVE HOLIDAYS SRI LANKA
        </h1>
        <p style='color:#FFD700; font-style:italic; font-size:1.4rem; margin-top:0;'>
            "Unforgettable Island Adventures Awaits"
        </p>
    </div>
    <hr style='border: 1px solid rgba(255,255,255,0.2); margin-top:0;'>
    """, unsafe_allow_html=True)

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
.stTextInput input, .stTextArea textarea {{ background-color: white !important; color: black !important; }}
::placeholder {{ color: #888888 !important; opacity: 0.5 !important; }}
</style>
""", unsafe_allow_html=True)

# ================= 5. LOGIN GATE =================
if not st.session_state.authenticated:
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        with st.form("login_gate"):
            st.subheader("🔐 Staff Login")
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                # Connect to Google Sheets
                conn = st.connection("gsheets", type=GSheetsConnection)
                db = conn.read(worksheet="Sheet1", ttl=0)
                match = db[(db["username"] == u) & (db["password"].astype(str) == p)]
                if not match.empty:
                    st.session_state.authenticated = True
                    st.session_state.user_role = "Admin" if u.lower() in ["admin", "admin01"] else "Staff"
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        
        # HELP LINK FOR LOGIN ISSUES
        st.markdown("<div style='text-align:center;'><a href='#' style='color:#FFD700; text-decoration:none;'>Unable to sign in? Contact Admin</a></div>", unsafe_allow_html=True)
    st.stop() # Prevents further execution until logged in

# ================= 6. POST-LOGIN UI =================

# LOGOUT BUTTON - Visible at the top right
top_c1, top_c2 = st.columns([9, 1])
top_c1.write(f"Logged in as: **{st.session_state.user_role}**")
if top_c2.button("Logout"):
    st.session_state.clear()
    st.rerun()

# --- ADMIN PANEL ---
if st.session_state.user_role == "Admin":
    st.header("🛠️ Admin Panel")
    conn = st.connection("gsheets", type=GSheetsConnection)
    db = conn.read(worksheet="Sheet1", ttl=0)
    st.dataframe(db, use_container_width=True)

# --- STAFF ITINERARY BUILDER ---
else:
    st.header("✈️ Itinerary Builder")
    it_title = st.text_input("Itinerary Name", placeholder="e.g. 10 Days in Paradise")
    
    cA, cB, cC = st.columns([2, 1, 1])
    route = cA.text_input("Route", placeholder="Colombo to Kandy")
    dist = cB.text_input("Distance", placeholder="115KM")
    time = cC.text_input("Time", placeholder="3 Hours")
    desc = st.text_area("Details", placeholder="Describe the day's activities...")

    if st.button("➕ Add Day"):
        if route:
            st.session_state.itinerary.append({
                "Route": route, "Distance": dist, "Time": time, "Description": desc
            })
            st.rerun()

    if st.session_state.itinerary:
        st.write("---")
        # Export Buttons
        ex1, ex2 = st.columns(2)
        ex1.download_button("📊 Excel Export", pd.DataFrame(st.session_state.itinerary).to_csv(index=False).encode('utf-8'), "trip.csv")
        
        # PDF Generation Logic
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16); pdf.cell(0, 10, "EXCLUSIVE HOLIDAYS", 0, 1, "C")
        for i, day in enumerate(st.session_state.itinerary):
            pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, f"Day {i+1}: {day['Route']}", 1, 1)
            pdf.set_font("Arial", "", 10); pdf.multi_cell(0, 7, day['Description'])
        
        ex2.download_button("📄 PDF Export", pdf.output(dest='S'), "trip.pdf", mime="application/pdf")

        for i, item in enumerate(st.session_state.itinerary):
            with st.expander(f"Day {i+1}: {item['Route']}"):
                st.write(item['Description'])
                if st.button(f"Remove Day {i+1}", key=f"rm_{i}"):
                    st.session_state.itinerary.pop(i)
                    st.rerun()
