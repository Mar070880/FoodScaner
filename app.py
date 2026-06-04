import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Configure the AI Brain
genai.configure(api_key="AQ.Ab8RN6IzREH7_Hvv6XemVIAq6tzM_h6AhPXy22982mJRxzjfVQ")

st.set_page_config(page_title="AI Food Scale", page_icon="📸", layout="centered")

# 2. App Interface
st.title("📸 AI Food Scale & Calorie Counter")
st.write("Scan your food via camera or upload an image from your device!")
st.write("---")

input_method = st.radio("Choose how you want to add your photo:", ("Use Camera 📷", "Upload from Device 📁"))

uploaded_file = None
if input_method == "Use Camera 📷":
    uploaded_file = st.camera_input("Take a picture of your food scale")
else:
    uploaded_file = st.file_uploader("Choose a food photo from your gallery...", type=["jpg", "jpeg", "png"])

# 3. Processing the Food Scan
if uploaded_file is not None:
    if input_method == "Upload from Device 📁":
        st.image(uploaded_file, caption='Your Uploaded Food Scan', use_container_width=True)
    
    st.write("---")
    
    if st.button("Calculate Calories 🧮"):
        with st.spinner("🧠 AI is analyzing the scale display and ingredients..."):
            try:
                # Convert the file format for the AI
                img = Image.open(uploaded_file)
                
                # Using the working model version
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # Instructions telling the AI exactly what to return to your screen
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
