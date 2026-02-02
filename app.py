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

# 2. Styling
st.markdown("""
    <style>
    header {visibility: hidden;}
    .main .block-container {padding-top: 1rem;}
    .stApp {
        background: linear-gradient(rgba(255,255,255,0.85), rgba(255,255,255,0.85)), 
                    url("https://images.unsplash.com/photo-1528127269322-539801943592?q=80&w=2070&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
    }
    .main-container {
        background-color: rgba(255, 255, 255, 0.95); 
        padding: 40px; border-radius: 25px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.05);
    }
    button, .stButton > button, .stat-box {
        background-color: #0056b3 !important;
        border: 2px solid #0056b3 !important;
    }
    button p, button span, .stButton p, .stButton span, .stat-box h3, .stat-box span {
        color: #FFFFFF !important;
        font-weight: 800 !important;
        font-size: 18px !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    .reset-btn button {
        background-color: #d9534f !important;
        border-color: #d43f3a !important;
    }
    h1, h2, h3, p, label, span { color: #111111 !important; }
    .itinerary-card {
        background-color: #ffffff; padding: 25px; border-radius: 15px; 
        margin-bottom: 20px; border-left: 6px solid #0056b3; 
        box-shadow: 0px 4px 15px rgba(0,0,0,0.05);
    }
    .stat-box {
        padding: 12px 28px; border-radius: 50px;
        display: inline-block; margin-bottom: 30px; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Initialize Session States
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = []
if 'tour_title' not in st.session_state:
    st.session_state.tour_title = ""

# --- NEW: CALLBACK FUNCTION TO CLEAR FIELDS SAFELY ---
def add_day_callback():
    # Only add if Route is not empty
    if st.session_state.route_input:
        # Collect activities
        activities_list = []
        for i in range(st.session_state.num_act_selector):
            act_key = f"act_input_{i}"
            if act_key in st.session_state:
                activities_list.append(st.session_state[act_key])
        
        all_activities = ", ".join([a for a in activities_list if a.strip()])
        
        # Save to itinerary
        st.session_state.itinerary.append({
            "Route": st.session_state.route_input, 
            "Distance": st.session_state.dist_input, 
            "Time": st.session_state.tm_input, 
            "Activities": all_activities, 
            "Description": st.session_state.desc_input
        })
        
        # WIPE THE WIDGETS
        st.session_state.route_input = ""
        st.session_state.dist_input = ""
        st.session_state.tm_input = ""
        st.session_state.desc_input = ""
        for i in range(10): # Clear up to 10 potential activity keys
            if f"act_input_{i}" in st.session_state:
                st.session_state[f"act_input_{i}"] = ""

# 4. Logo (Updated for Size and Transparency)
logo_path = "logo.png"
logo_base64 = get_base64(logo_path)
if logo_base64:
    st.markdown(f"""
        <div style="
            position: fixed; 
            top: 15px; 
            right: 25px; 
            z-index: 9999;
            transition: opacity 0.3s ease;
        ">
            <img src="data:image/png;base64,{logo_base64}" 
                 style="
                    width: 220px; 
                    opacity: 0.7; 
                    filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.1));
                 "
                 onmouseover="this.style.opacity='1'" 
                 onmouseout="this.style.opacity='0.7'">
        </div>
    """, unsafe_allow_html=True)
# 5. Content Wrapper
st.markdown('<div class="main-container">', unsafe_allow_html=True)
st.title("✈️ Exclusive Holidays SL")
st.subheader("Unforgettable Island Adventures Await")

# Summary & Reset Section
if st.session_state.itinerary:
    sum_col, res_col = st.columns([4, 1.2])
    with sum_col:
        total_days = len(st.session_state.itinerary)
        total_nights = total_days - 1 if total_days > 0 else 0
        st.markdown(f'<div class="stat-box"><h3>📅 {total_days} Days / {total_nights} Nights</h3></div>', unsafe_allow_html=True)
    with res_col:
        st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
        if st.button("🗑️ Reset All Data", use_container_width=True):
            st.session_state.itinerary = []
            st.session_state.tour_title = ""
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# 6. Input Section
st.markdown("### 📝 Build Your Journey")
st.session_state.tour_title = st.text_input("📍 Tour Title / Client Name", value=st.session_state.tour_title, placeholder="e.g. Johnson Family - 10 Days")
display_title = st.session_state.tour_title if st.session_state.tour_title else "Travel Itinerary"

c1, c2, c3 = st.columns([2, 1, 1])
c1.text_input("Route (From - To)", placeholder="Airport to Negombo", key="route_input")
c2.text_input("Distance", placeholder="32 KM", key="dist_input")
c3.text_input("Travel Time", placeholder="30 mins", key="tm_input")

num_activities = st.selectbox("How many activities for this day?", options=[1, 2, 3, 4, 5, 6], key="num_act_selector")

for i in range(num_activities):
    st.text_input(f"Activity {i+1}", placeholder=f"Enter activity {i+1}...", key=f"act_input_{i}")

st.text_area("Place Description", key="desc_input")

# THE UPDATED BUTTON (Uses on_click callback)
st.button("➕ Add Day to Tour", use_container_width=True, on_click=add_day_callback)

# 7. Main Page Export Buttons
if st.session_state.itinerary:
    st.write("---")
    st.markdown(f"### 📥 Download: {display_title}")
    e_col1, e_col2 = st.columns(2)
    
    df = pd.DataFrame(st.session_state.itinerary)
    df.insert(0, 'Day', range(1, 1 + len(df)))
    excel_out = BytesIO()
    with pd.ExcelWriter(excel_out, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name=display_title[:31]) 
    e_col1.download_button("📊 Download as Excel", data=excel_out.getvalue(), file_name=f"{display_title}.xlsx", use_container_width=True)

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
    
    e_col2.download_button("📝 Download as Word", data=create_word(st.session_state.itinerary, display_title), file_name=f"{display_title}.docx", use_container_width=True)

st.divider()

# 8. List Display
if st.session_state.itinerary:
    for i, item in enumerate(st.session_state.itinerary):
        col_text, col_del = st.columns([9.2, 0.8])
        with col_text:
            st.markdown(f"""
            <div class="itinerary-card">
                <h3 style="margin-top:0; color: #0056b3 !important;">Day {i+1}: {item['Route']}</h3>
                <p><b>📏 {item['Distance']} | ⏱️ {item['Time']}</b></p>
                <p><b>✨ Activities:</b> {item['Activities']}</p>
                <p>{item['Description']}</p>
            </div>
            """, unsafe_allow_html=True)
        with col_del:
            if st.button("❌", key=f"del_{i}"):
                st.session_state.itinerary.pop(i)
                st.rerun()


st.markdown('</div>', unsafe_allow_html=True)
