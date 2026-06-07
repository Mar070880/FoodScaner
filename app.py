import streamlit as st
import google.generativeai as genai
from PIL import Image
import re
import json
from datetime import datetime

# 1. Pulling the API key securely from your Streamlit Dashboard Secrets
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("API Key Missing! Please add GEMINI_API_KEY to your Streamlit Advanced Settings Secrets.")

st.set_page_config(page_title="AI Food Scale", page_icon="📸", layout="centered")

# Initialize Phone Storage Connection
from streamlit_local_storage import StLocalStorage
local_storage = StLocalStorage()

# ADVANCED CSS: Injects 3D Textured Green Buttons and a Soft Floral Background
st.markdown(
    """
    <head>
        <link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/512/8124/8124017.png">
        <link rel="icon" type="image/png" href="https://cdn-icons-png.flaticon.com/512/8124/8124017.png">
    </head>
    <style>
    /* Fixed aspect ratio for mobile camera video elements */
    div[data-testid="stMarkdownContainer"] video {
        object-fit: contain !important;
        height: auto !important;
    }
    iframe {
        height: 350px !important;
    }

    /* Soft Textured Light Floral Background */
    .stApp {
        background-image: linear-gradient(rgba(255, 255, 255, 0.88), rgba(255, 255, 255, 0.88)), 
                          url('https://images.unsplash.com/photo-1526047932273-341f2a7631f9?q=80&w=1200&auto=format&fit=crop');
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }

    /* 3D Green Button Styling (Targeting the action keys at the top) */
    div.stButton > button {
        background: linear-gradient(135deg, #a2d149 0%, #7cb021 100%) !important;
        color: white !important;
        font-weight: bold !important;
        font-size: 18px !important;
        border: 1px solid #6b991c !important;
        border-radius: 14px !important;
        padding: 12px 24px !important;
        box-shadow: 0px 6px 0px #537812, 0px 10px 15px rgba(0, 0, 0, 0.2) !important;
        text-shadow: 1px 2px 2px rgba(0, 0, 0, 0.3) !important;
        transition: all 0.1s ease-in-out !important;
        text-transform: none !important;
    }

    /* Active pressing effect to make it feel 3D tactile */
    div.stButton > button:active {
        box-shadow: 0px 2px 0px #537812, 0px 4px 6px rgba(0, 0, 0, 0.2) !important;
        transform: translateY(4px) !important;
    }
    
    /* Clean text styling readability overrides over the background */
    h1, h2, h3, p, label {
        color: #2e3d1d !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📸 AI Food Scale & Calorie Counter")
st.write("Analyze your meal instantly using your live camera or an image upload.")
st.write("---")

# Get today's date formatted as YYYY-MM-DD
today_str = datetime.today().strftime('%Y-%m-%d')

# --- PHONE MEMORY MANAGEMENT BLOCK ---
saved_data = local_storage.get(key="meal_history_archive")
if saved_data is not None and saved_data != "":
    try:
        history_archive = json.loads(saved_data)
    except:
        history_archive = {}
else:
    history_archive = {}

if today_str not in history_archive:
    history_archive[today_str] = {"target": 2000, "consumed": 0, "meals": []}

if "current_consumed" not in st.session_state:
    st.session_state.current_consumed = history_archive[today_str]["consumed"]

if "photo_source" not in st.session_state:
    st.session_state.photo_source = None

# =========================================================
# STEP 1: 3D CAMERA & SCANNER OPTION AT THE VERY TOP
# =========================================================
col1, col2 = st.columns(2)

with col1:
    if st.button("📷 Open Live Camera Mode", use_container_width=True):
        st.session_state.photo_source = "camera"

with col2:
    if st.button("📁 Open File Uploader Mode", use_container_width=True):
