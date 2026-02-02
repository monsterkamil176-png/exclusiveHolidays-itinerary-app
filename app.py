import streamlit as st
import os
import base64
import pandas as pd
from io import BytesIO
from docx import Document 

# 1. Page Config
st.set_page_config(page_title="Exclusive Holidays SL", layout="wide")

# HELPER: Converts image to base64
def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

# 2. Styling (Optimized for Mobile)
st.markdown("""
    <style>
    header {visibility: hidden;}
    .main .block-container {padding-top: 1rem; padding-bottom: 2rem;}
    
    .stApp {
        background: linear-gradient(rgba(255,255,255,0.85), rgba(255,255,255,0.85)), 
                    url("https://images.unsplash.com/photo-1528127269322-539801943592?q=80&w=2070&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
    }
    
    .main-container {
        background-color: rgba(255, 255, 255, 0.95); 
        padding: 25px; 
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.05);
        max-width: 900px;
        margin: auto;
    }

    /* BOLD WHITE TEXT FOR BUTTONS */
    button, .stButton > button {
        background-color: #0056b3 !important;
        border: 2px solid #0056b3 !important;
        border-radius: 10px !important;
        height: 50px;
    }

    button p, button span, .stButton p, .stButton span {
        color: #FFFFFF !important;
        font-weight: 800 !important;
        font-size: 16px !important;
    }

    .itinerary-card {
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 15px; 
        margin-bottom: 15px;
        border-left: 6px solid #0056b3; 
        box-shadow: 0px 4px 15px rgba(0,0,0,0.05);
    }

    /* MOBILE ADJUSTMENTS */
    @media (max-width: 768px) {
        .main-container { padding: 15px; }
        .logo-img { width: 180px !important; }
        h1 { font-size: 22px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Initialize Session States
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = []
if 'tour_title' not in st.session_state:
    st.session_state.tour_title = ""

def add_day_callback():
    if st.session_state.route_input:
        activities_list = []
        for i in range(st.session_state.num_act_selector):
            act_key = f"act_input_{i}"
            if act_key in st.session_state:
                activities_list.append(st.session_state[act_key])
        
        all_activities = ", ".join([a for a in activities_list if a.strip()])
        
        st.session_state.itinerary.append({
            "Route": st.session_state.route_input, 
            "Distance": st.session_state.dist_input, 
            "Time": st.session_state.tm_input, 
            "Activities": all_activities, 
            "Description": st.session_state.desc_input
        })
        
        # Clear fields
        st.session_state.route_input = ""
        st.session_state.dist_input = ""
        st.session_state.tm_input = ""
        st.session_state.desc_input = ""
        for i in range(10):
            if f"act_input_{i}" in st.session_state:
                st.session_state[f"act_input_{i}"] = ""

# 4. Logo (Top Middle - Unfrozen)
logo_path = "logo.png"
logo_base64 = get_base64(logo_path)
if logo_base64:
    st.markdown(f"""
        <div style="text-align: center; padding: 20px 0;">
            <img class="logo-img" src="data:image/png;base64,{logo_base64}" 
                 style="width: 250px; opacity: 0.7; transition: 0.3s;"
                 onmouseover="this.style.opacity='1'" onmouseout="this.style.opacity='0.7'">
        </div>
    """, unsafe_allow_html=True)

# 5. Content Wrapper
st.markdown('<div class="main-container">', unsafe_allow_html=True)

st.title("✈️ Exclusive Holidays SL")

# Summary Section
if st.session_state.itinerary:
    total_days = len(st.session_state.itinerary)
    st.info(f"📅 Current Plan: {total_days} Days / {total_days - 1 if total_days > 0 else 0} Nights")

# 6. Input Section
st.markdown("### 📝 Build Your Journey")
st.session_state.tour_title = st.text_input("📍 Tour Title / Client Name", value=st.session_state.tour_title, placeholder="e.g. Johnson Family")

c1, c2, c3 = st.columns([2, 1, 1])
c1.text_input("Route", placeholder="Airport to Negombo", key="route_input")
c2.text_input("Distance", placeholder="32 KM", key="dist_input")
c3.text_input("Time", placeholder="30 mins", key="tm_input")

num_activities = st.selectbox("Number of activities for this day", options=[1, 2, 3, 4, 5, 6], key="num_act_selector")

for i in range(num_activities):
    st.text_input(f"Activity {i+1}", key=f"act_input_{i}", placeholder=f"Activity {i+1} details...")

st.text_area("Place Description", key="desc_input", placeholder="Describe the destination...")

st.button("➕ Add Day to Tour", use_container_width=True, on_click=add_day_callback)

# 7. Exports
if st.session_state.itinerary:
    st.divider()
    st.markdown("### 📥 Download Documents")
    display_title = st.session_state.tour_title if st.session_state.tour_title else "Itinerary"
    
    # Word Export Logic
    def create_word(data, title):
        doc = Document()
        doc.add_heading(title, 0) 
        for i, item in enumerate(data):
            doc.add_heading(f"Day {i+1}: {item['Route']}", level=1)
            doc.add_paragraph(f"Distance: {item['Distance']} | Time: {item['Time']}")
            doc.add_paragraph(f"Activities: {item['Activities']}")
            doc.add_paragraph(item['Description'])
        word_out = BytesIO()
        doc.save(word_out)
        return word_out.getvalue()
    
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button("📝 Word Document", data=create_word(st.session_state.itinerary, display_title), file_name=f"{display_title}.docx", use_container_width=True)
    with col_dl2:
        # Excel Logic
        df = pd.DataFrame(st.session_state.itinerary)
        df.insert(0, 'Day', range(1, 1 + len(df)))
        excel_out = BytesIO()
        with pd.ExcelWriter(excel_out, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name="Itinerary") 
        st.download_button("📊 Excel Sheet", data=excel_out.getvalue(), file_name=f"{display_title}.xlsx", use_container_width=True)

# 8. Itinerary Display
st.divider()
for i, item in enumerate(st.session_state.itinerary):
    with st.container():
        st.markdown(f"""
        <div class="itinerary-card">
            <h3 style="margin:0; color: #0056b3;">Day {i+1}: {item['Route']}</h3>
            <p><b>📏 {item['Distance']} | ⏱️ {item['Time']}</b></p>
            <p><b>✨ Activities:</b> {item['Activities']}</p>
            <p>{item['Description']}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("❌ Remove Day", key=f"del_{i}", use_container_width=True):
            st.session_state.itinerary.pop(i)
            st.rerun()

# Global Reset
if st.session_state.itinerary:
    if st.button("🗑️ Reset All Data", key="global_reset", use_container_width=True):
        st.session_state.itinerary = []
        st.session_state.tour_title = ""
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)


