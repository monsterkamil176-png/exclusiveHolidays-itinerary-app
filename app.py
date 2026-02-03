import streamlit as st
import pandas as pd
from io import BytesIO
from fpdf import FPDF
from streamlit_gsheets import GSheetsConnection

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Exclusive Holidays SL",
    page_icon="✈️",
    layout="wide"
)

# ================= CONSTANT BRANDING =================
DEFAULT_LOGO = "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Placeholder_logo.svg/512px-Placeholder_logo.svg.png"
COMPANY_NAME = "EXCLUSIVE HOLIDAYS SRI LANKA"
TAGLINE = "Unforgettable Island Adventures Awaits"

# ================= SESSION STATE =================
st.session_state.setdefault("authenticated", False)
st.session_state.setdefault("user_role", None)
st.session_state.setdefault("itinerary", [])
st.session_state.setdefault("brand_logo", DEFAULT_LOGO)

# ================= STYLING =================
bg_img = "https://images.unsplash.com/photo-1586500036706-41963de24d8b?q=80&w=2574&auto=format&fit=crop"

st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
    background:
      linear-gradient(rgba(0,0,0,0.65), rgba(0,0,0,0.65)),
      url("{bg_img}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}

input::placeholder {{
    color: #bbbbbb !important;
}}

.stTextInput input {{
    background: white !important;
    color: black !important;
}}
</style>
""", unsafe_allow_html=True)

# ================= BRANDING (ALWAYS VISIBLE) =================
st.write("")
_, logo_col, _ = st.columns([3, 2, 3])
logo_col.image(st.session_state.brand_logo, use_container_width=True)

st.markdown(
    f"<h1 style='text-align:center;color:white;text-shadow:3px 3px 6px black;'>{COMPANY_NAME}</h1>",
    unsafe_allow_html=True
)
st.markdown(
    f"<p style='text-align:center;color:#FFD700;font-style:italic;font-size:1.3rem;'>“{TAGLINE}”</p>",
    unsafe_allow_html=True
)

# ================= LOGIN =================
if not st.session_state.authenticated:
    st.markdown("---")
    _, box, _ = st.columns([1, 1.3, 1])

    with box:
        with st.form("login"):
            st.subheader("🔐 Staff Login")
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")

            if st.form_submit_button("Login"):
                conn = st.connection("gsheets", type=GSheetsConnection)
                db = conn.read(worksheet="Sheet1", ttl=0)

                user = db[
                    (db["username"] == u) &
                    (db["password"].astype(str) == p)
                ]

                if not user.empty:
                    st.session_state.authenticated = True
                    st.session_state.user_role = (
                        "Admin" if u.lower().startswith("admin") else "Staff"
                    )
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")

        st.markdown(
            "<div style='text-align:center;'>"
            "<a style='color:#FFD700;'>Contact Management if you cannot sign in</a>"
            "</div>",
            unsafe_allow_html=True
        )

    st.stop()

# ================= LOGOUT BAR =================
c1, c2 = st.columns([8, 2])
c1.success(f"Logged in as **{st.session_state.user_role}**")

if c2.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.session_state.itinerary.clear()
    st.rerun()

# ================= PDF ENGINE =================
def create_pdf(title, itinerary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, COMPANY_NAME, ln=1, align="C")
    pdf.ln(8)

    for i, day in enumerate(itinerary):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, f"Day {i+1}: {day['Route']}", ln=1)
        pdf.set_font("Helvetica", "", 11)
        text = day["Description"].replace("✓", "-")
        pdf.multi_cell(0, 7, text)
        pdf.ln(4)

    return pdf.output(dest="S")

# ================= ADMIN =================
if st.session_state.user_role == "Admin":
    st.header("🛠️ Admin Panel")

    with st.expander("🖼️ Branding Settings"):
        logo = st.file_uploader("Upload Logo", ["png", "jpg"])
        if logo:
            st.session_state.brand_logo = logo
            st.success("Brand logo updated!")

# ================= STAFF =================
else:
    st.header("✈️ Itinerary Builder")

    title = st.text_input(
        "Itinerary Name",
        placeholder="e.g. Sri Lanka Luxury Escape"
    )

    if st.button("➕ Add Day"):
        st.session_state.itinerary.append({
            "Route": "Colombo → Kandy",
            "Description": "Sightseeing and cultural tour"
        })

    if st.session_state.itinerary:
        st.write("---")
        c1, c2 = st.columns(2)

        c1.download_button(
            "📊 Excel",
            pd.DataFrame(st.session_state.itinerary).to_csv(index=False).encode(),
            "itinerary.csv"
        )

        c2.download_button(
            "📄 PDF",
            create_pdf(title, st.session_state.itinerary),
            "itinerary.pdf",
            mime="application/pdf"
        )
