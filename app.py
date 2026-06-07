import streamlit as st
import google.generativeai as genai
from PIL import Image
import re

# Safely pulling the API key from your Streamlit App Secrets
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("API Key Missing! Please add GEMINI_API_KEY to your Streamlit Advanced Settings Secrets.")

st.set_page_config(page_title="AI Food Scale", page_icon="📸", layout="centered")

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

# Initialize Native Session State Tracking Variables
if "calories_consumed" not in st.session_state:
    st.session_state.calories_consumed = 0

if "photo_source" not in st.session_state:
    st.session_state.photo_source = None

# =========================================================
# STEP 1: CAMERA & SCANNER CONTROLS AT THE ABSOLUTE TOP
# =========================================================
col1, col2 = st.columns(2)

with col1:
    if st.button("📷 Open Live Camera Mode", use_container_width=True):
        st.session_state.photo_source = "camera"

with col2:
    if st.button("📁 Open File Uploader Mode", use_container_width=True):
        st.session_state.photo_source = "upload"

final_image = None

if st.session_state.photo_source == "camera":
    st.subheader("Live Camera Capture")
    from streamlit_back_camera_input import back_camera_input
    final_image = back_camera_input("Point at your food scale display and snap a picture")
    
    if st.button("🔄 Clear / Reset Camera", use_container_width=True):
        st.session_state.photo_source = None
        st.rerun()

elif st.session_state.photo_source == "upload":
    st.subheader("Image File Upload")
    final_image = st.file_uploader("Drop your food photo here...", type=["jpg", "jpeg", "png"])
    if final_image:
        st.image(final_image, caption="Uploaded Image Preview", use_container_width=True)
    if st.button("🔄 Clear / Reset Uploaded File", use_container_width=True):
        st.session_state.photo_source = None
        st.rerun()

# =========================================================
# STEP 2: DIETARY GOALS AND ANALYSIS BLOCK
# =========================================================
st.write("---")
st.subheader("🎯 Set Your Current Nutritional Goal")
diet_goal = st.selectbox(
    "Choose a filter to customize the AI analysis:",
    [
        "Standard (General Calorie Counting)", 
        "Keto / Low Carb (Track Net Carbs)", 
        "Vegan / Plant-Based (Flag Animal Products)", 
        "Calorie Deficit / Weight Loss (Highlight Low-Calorie Volumes)", 
        "Muscle Building / High Protein (Highlight Protein Sources)"
    ]
)

if final_image is not None:
    st.write("---")
    if st.button("🔥 Calculate Total Calories 🧮", use_container_width=True):
        with st.spinner("🧠 AI is analyzing the scale display and ingredients..."):
            try:
                img = Image.open(final_image)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                base_prompt = (
                    "You are a nutritional expert and automated food scale assistant. "
                    "Analyze the provided image carefully. Your task is to:\n"
                    "1. Read the exact number display on the digital food scale if visible.\n"
                    "2. Identify all visible ingredients or meals.\n"
                    "3. Provide a clear Markdown table detailing the ingredients, estimated or read weights, "
                    "and a precise calorie breakdown.\n"
                    "4. Give a final total calorie calculation.\n"
                    "CRITICAL OUTPUT FORMAT rule: At the very end of your response, output the final total numeric calorie value "
                    "exactly inside brackets like this: TOTAL_CALORIES:[XYZ] where XYZ is the total integer number alone. Do not omit this."
                )
                
                goal_instructions = ""
                if "Keto" in diet_goal:
                    goal_instructions = "\n5. DIETARY GOAL CRITICAL INSTRUCTION: The user is on KETO. Explicitly calculate Net Carbs."
                elif "Vegan" in diet_goal:
                    goal_instructions = "\n5. DIETARY GOAL CRITICAL INSTRUCTION: The user is VEGAN. Flag animal products."
                elif "Calorie Deficit" in diet_goal:
                    goal_instructions = "\n5. DIETARY GOAL CRITICAL INSTRUCTION: The user is in a DEFICIT. Suggest low-calorie volume swaps."
                elif "Muscle Building" in diet_goal:
                    goal_instructions = "\n5. DIETARY GOAL CRITICAL INSTRUCTION: The user wants to BUILD MUSCLE. Highlight proteins."
                else:
                    goal_instructions = "\n5. Keep your tone helpful, supportive, and direct."

                full_prompt = base_prompt + goal_instructions
                response = model.generate_content([full_prompt, img])
                ai_text = response.text
                
                try:
                    match = re.search(r"TOTAL_CALORIES:\[(\d+)\]", ai_text)
                    if match:
                        extracted_calories = int(match.group(1))
                        st.session_state.calories_consumed += extracted_calories
                except:
                    pass 
                
                st.success("Analysis Complete!")
                clean_display_text = ai_text.split("TOTAL_CALORIES:[")[0]
                st.markdown(clean_display_text)
                
            except Exception as e:
                st.error(f"Something went wrong during analysis: {e}")

# =========================================================
# STEP 3: CALORIE TRACKER DASHBOARD SITUATED DOWN THE PAGE
# =========================================================
st.write("---")
st.subheader("📊 Your Daily Calorie Dashboard")

daily_target = st.number_input("Set your daily calorie target:", min_value=1000, max_value=10000, value=2000, step=50)

calories_left = max(0, daily_target - st.session_state.calories_consumed)
progress_percentage = min(1.0, float(st.session_state.calories_consumed) / float(daily_target))

st.progress(progress_percentage)

col_metric1, col_metric2, col_metric3 = st.columns(3)
with col_metric1:
    st.metric("Target", f"{daily_target} kcal")
with col_metric2:
    st.metric("Consumed", f"{st.session_state.calories_consumed} kcal")
with col_metric3:
    st.metric("Remaining", f"{calories_left} kcal")

if st.button("🔄 Reset Today's Consumed Counter", use_container_width=True):
    st.session_state.calories_consumed = 0
    st.rerun()
