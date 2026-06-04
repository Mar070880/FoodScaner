import streamlit as st
import google.generativeai as genai
from PIL import Image
# Import the custom rear-camera plug-in
from streamlit_back_camera_input import back_camera_input

# 1. Directly apply your API key here
genai.configure(api_key="AQ.Ab8RN6IzREH7_Hvv6XemVIAq6tzM_h6AhPXy22982mJRxzjfVQ")

st.set_page_config(page_title="AI Food Scale", page_icon="📸", layout="centered")

# Custom CSS Injection for Mobile App Shortcut Icon and Camera Fixes (Background Image Removed)
st.markdown(
    """
    <head>
        <link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/512/8124/8124017.png">
        <link rel="icon" type="image/png" href="https://cdn-icons-png.flaticon.com/512/8124/8124017.png">
    </head>
    <style>
    /* Corrects camera aspect ratio bugs on mobile screens */
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

# Initialize session state tracking to handle clearing cleanly
if "photo_source" not in st.session_state:
    st.session_state.photo_source = None

# Create two big action rows instead of tiny select dots
col1, col2 = st.columns(2)

with col1:
    if st.button("📷 Open Live Camera Mode", use_container_width=True):
        st.session_state.photo_source = "camera"

with col2:
    if st.button("📁 Open File Uploader Mode", use_container_width=True):
        st.session_state.photo_source = "upload"

st.write("---")

final_image = None

# Handle the specific selections dynamically with refresh capabilities
if st.session_state.photo_source == "camera":
    st.subheader("Live Camera Capture")
    
    # Custom widget that auto-requests back-camera
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
                
                # Base instructions for the AI agent
                base_prompt = (
                    "You are a nutritional expert and automated food scale assistant. "
                    "Analyze the provided image carefully. Your task is to:\n"
                    "1. Read the exact number display on the digital food scale if visible.\n"
                    "2. Identify all visible ingredients or meals.\n"
                    "3. Provide a clear Markdown table detailing the ingredients, estimated or read weights, "
                    "and a precise calorie breakdown.\n"
                    "4. Give a final total calorie calculation.\n"
                )
                
                # Dynamic prompt customization logic based on selected user goal
                goal_instructions = ""
                if "Keto" in diet_goal:
                    goal_instructions = (
                        "5. DIETARY GOAL CRITICAL INSTRUCTION: The user is on a strict KETO diet. "
                        "In your text response below the table, explicitly calculate the estimated Net Carbs "
                        "(Total Carbs minus Fiber) and give a warning if any item is high in sugar or carbs."
                    )
                elif "Vegan" in diet_goal:
                    goal_instructions = (
                        "5. DIETARY GOAL CRITICAL INSTRUCTION: The user is VEGAN. "
                        "Carefully audit all identified ingredients. If you spot dairy, meat, eggs, honey, "
                        "or hidden animal fats, call them out immediately in a bold red warning or text bullet point."
                    )
                elif "Calorie Deficit" in diet_goal:
                    goal_instructions = (
                        "5. DIETARY GOAL CRITICAL INSTRUCTION: The user is in a CALORIE DEFICIT. "
                        "Provide a helpful tip beneath the table on how they could swap any high-calorie ingredient "
                        "visible for a lower-calorie alternative to increase meal volume."
                    )
                elif "Muscle Building" in diet_goal:
                    goal_instructions = (
                        "5. DIETARY GOAL CRITICAL INSTRUCTION: The user wants to BUILD MUSCLE. "
                        "Highlight which ingredients provide the highest protein in this meal, and evaluate if "
                        "the meal has enough total protein for a fitness athlete."
                    )
                else:
                    goal_instructions = "5. Keep your tone helpful, supportive, and direct."

                # Combine the core instructions with the custom dynamic goal instructions
                full_prompt = base_
