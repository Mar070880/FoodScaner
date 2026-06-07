import streamlit as st
import google.generativeai as genai
from PIL import Image
import re
import json
from datetime import datetime
# Import the custom camera and phone storage plug-ins
from streamlit_back_camera_input import back_camera_input
from streamlit_local_storage import StLocalStorage

# FIXED: Safely pulling the API key from Secrets so GitHub cannot revoke it
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("API Key missing! Please add GEMINI_API_KEY to your Streamlit App Secrets.")

st.set_page_config(page_title="AI Food Scale", page_icon="📸", layout="centered")

# Initialize Phone Storage Connection
local_storage = StLocalStorage()

# Custom CSS Injection to fix the aspect ratio AND add a mobile home screen icon link
st.markdown(
    """
    <head>
        <link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/512/8124/8124017.png">
        <link rel="icon" type="image/png" href="https://cdn-icons-png.flaticon.com/512/8124/8124017.png">
    </head>
    <style>
    div[data-testid="stMarkdownContainer"] video {
        object-fit: contain !important;
        height: auto !important;
    }
    iframe {
        height: 350px !important;
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
# Load existing log history saved on the phone's local storage
saved_data = local_storage.get(key="meal_history_archive")
if saved_data is not None and saved_data != "":
    try:
        history_archive = json.loads(saved_data)
    except:
        history_archive = {}
else:
    history_archive = {}

# Ensure today exists in our archive structure
if today_str not in history_archive:
    history_archive[today_str] = {"target": 2000, "consumed": 0, "meals": []}

# Initialize temporary variables from our phone data
if "current_consumed" not in st.session_state:
    st.session_state.current_consumed = history_archive[today_str]["consumed"]

# --- DAILY CALORIE TRACKER DASHBOARD ---
st.subheader("📊 Your Daily Calorie Dashboard")

# Let user pick their exact target
daily_target = st.number_input("Set your daily calorie target:", min_value=1000, max_value=10000, value=int(history_archive[today_str].get("target", 2000)), step=50)
history_archive[today_str]["target"] = daily_target

# Calculate tracking equations
calories_consumed = st.session_state.current_consumed
calories_left = max(0, daily_target - calories_consumed)
progress_percentage = min(1.0, float(calories_consumed) / float(daily_target))

# Render visual interfaces
st.progress(progress_percentage)

col_metric1, col_metric2, col_metric3 = st.columns(3)
with col_metric1:
    st.metric("Target", f"{daily_target} kcal")
with col_metric2:
    st.metric("Consumed", f"{calories_consumed} kcal")
with col_metric3:
    st.metric("Remaining", f"{calories_left} kcal")

if st.button("🔄 Reset Today's Consumed Counter"):
    st.session_state.current_consumed = 0
    history_archive[today_str]["consumed"] = 0
    history_archive[today_str]["meals"] = []
    local_storage.set(key="meal_history_archive", value=json.dumps(history_archive))
    st.rerun()

st.write("---")

# Dietary Goal Dropdown Selection Menu
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

st.write("---")

# Initialize session state tracking to handle camera clearing cleanly
if "photo_source" not in st.session_state:
    st.session_state.photo_source = None

col1, col2 = st.columns(2)
with col1:
    if st.button("📷 Open Live Camera Mode", use_container_width=True):
        st.session_state.photo_source = "camera"
with col2:
    if st.button("📁 Open File Uploader Mode", use_container_width=True):
        st.session_state.photo_source = "upload"

st.write("---")

final_image = None

if st.session_state.photo_source == "camera":
    st.subheader("Live Camera Capture")
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

# 3. AI Processing block
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
                    goal_instructions = "5. DIETARY GOAL CRITICAL INSTRUCTION: The user is on KETO. Explicitly calculate Net Carbs."
                elif "Vegan" in diet_goal:
                    goal_instructions = "5. DIETARY GOAL CRITICAL INSTRUCTION: The user is VEGAN. Flag animal products."
                elif "Calorie Deficit" in diet_goal:
                    goal_instructions = "5. DIETARY GOAL CRITICAL INSTRUCTION: The user is in a DEFICIT. Suggest low-calorie volume swaps."
                elif "Muscle Building" in diet_goal:
                    goal_instructions = "5. DIETARY GOAL CRITICAL INSTRUCTION: The user wants to BUILD MUSCLE. Highlight proteins."
                else:
                    goal_instructions = "5. Keep your tone helpful, supportive, and direct."

                full_prompt = base_prompt + goal_instructions
                response = model.generate_content([full_prompt, img])
                ai_text = response.text
                
                extracted_calories = 0
                try:
                    match = re.search(r"TOTAL_CALORIES:\[(\d+)\]", ai_text)
                    if match:
                        extracted_calories = int(match.group(1))
                        
                        # Save directly into history log metrics
                        st.session_state.current_consumed += extracted_calories
                        history_archive[today_str]["consumed"] = st.session_state.current_consumed
                        history_archive[today_str]["meals"].append({"time": datetime.now().strftime("%H:%M"), "calories": extracted_calories})
                        
                        # Push the updated data string right into the phone's memory
                        local_storage.set(key="meal_history_archive", value=json.dumps(history_archive))
                except:
                    pass
                
                st.success("Analysis Complete!")
                clean_display_text = ai_text.split("TOTAL_CALORIES:[")[0]
                st.markdown(clean_display_text)
                st.info("💾 Meal saved automatically to your device's log archive!")
                
            except Exception as e:
                st.error(f"Something went wrong during analysis: {e}")

st.write("---")

# --- MONTHLY HISTORY ARCHIVE SECTION ---
st.subheader("📅 Your Month History Archive")
with st.expander("📋 View Past Saved Days (This Month)"):
    if len(history_archive) <= 1 and history_archive.get(today_str, {}).get("consumed", 0) == 0:
        st.write("No meals tracked yet. Your logs will appear here day by day!")
    else:
        for date_key in sorted(history_archive.keys(), reverse=True):
            day_data = history_archive[date_key]
            total_day_calories = day_data.get("consumed", 0)
            target_day_calories = day_data.get("target", 2000)
            
            st.markdown(f"**📅 Date: {date_key}**")
            st.write(f"👉 Total Eaten: **{total_day_calories}** / {target_day_calories} kcal")
            
            mini_percentage = min(1.0, float(total_day_calories) / float(target_day_calories))
            st.progress(mini_percentage)
            st.write("---")
