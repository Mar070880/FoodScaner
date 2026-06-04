import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Directly apply your API key here
genai.configure(api_key="AQ.Ab8RN6IzREH7_Hvv6XemVIAq6tzM_h6AhPXy22982mJRxzjfVQ")

st.set_page_config(page_title="AI Food Scale", page_icon="📸", layout="centered")

st.title("📸 AI Food Scale & Calorie Counter")
st.write("Analyze your meal instantly using your live camera or an image upload.")
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
    
    # FIXED: Reverted to standard camera_input to completely fix the crash
    final_image = st.camera_input("Line up your food scale display and snap a picture")
    
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
                
                prompt = (
                    "You are a nutritional expert and automated food scale assistant. "
                    "Analyze the provided image carefully. Your task is to:\n"
                    "1. Read the exact number display on the digital food scale if visible.\n"
                    "2. Identify all visible ingredients or meals.\n"
                    "3. Provide a clear Markdown table detailing the ingredients, estimated or read weights, "
                    "and a precise calorie breakdown.\n"
                    "4. Give a final total calorie calculation.\n"
                    "Keep your tone helpful, supportive, and direct."
                )
                
                response = model.generate_content([prompt, img])
                st.success("Analysis Complete!")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Something went wrong during analysis: {e}")
