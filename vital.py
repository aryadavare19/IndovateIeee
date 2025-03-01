import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore
from PIL import Image
import io

# Set up Streamlit UI
st.set_page_config(page_title="Medical AI Assistant", layout="wide")

# Configure Gemini AI (Medical Assistant Mode)
genai.configure(api_key="AIzaSyArJov7xa3ARwH9YcqkSdb9GlzhPnj5uII")  # Replace with your actual API key

# Initialize Firebase (Ensure New Sessions Don't Load Old Chats)
if not firebase_admin._apps:
    cred = credentials.Certificate("C:\\Users\\User\\Downloads\\indovateieee-firebase-adminsdk-fbsvc-3a690188cc.json")  # Replace with your file path
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Load Gemini Model
@st.cache_resource
def load_model():
    return genai.GenerativeModel("gemini-1.5-pro-latest")

model = load_model()

# Generate Medical Response
def get_medical_response(user_input, chat_history):
    context = "You are a professional medical assistant. Answer questions related to health and medicine with accurate, reliable information. If a query is outside medical knowledge, state that you cannot provide advice."
    past_chats = "\n".join([f"User: {msg}\nAI: {resp}" for msg, resp in chat_history[-5:]])  # Use last 5 messages for context
    prompt = f"{context}\n{past_chats}\nUser: {user_input}\nAI:"
    
    response = model.generate_content(prompt)
    return response.text

# analyze_medical_image
def analyze_medical_image(image):
    """Convert PIL image to Gemini-compatible format and analyze it."""
    response = model.generate_content([
        "Analyze the given medical image and provide insights:",
        image  # Directly passing the PIL image instead of raw bytes
    ])
    return response.text


# Home Page
if "page" not in st.session_state:
    st.session_state.page = "home"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # Reset chat history on restart

if st.session_state.page == "home":
    st.markdown("<h1 style='text-align:center;'>🏥 Medical AI Assistant</h1>", unsafe_allow_html=True)
    st.write("Welcome to the AI-powered medical assistant. Click below to start chatting.")

    if st.button("🩺 Open Assistant", key="assistant_btn", use_container_width=True):
        st.session_state.page = "chatbot"
        st.rerun()

elif st.session_state.page == "chatbot":
    st.markdown("<h1 style='text-align:center;'>🩺 AI Medical Chatbot</h1>", unsafe_allow_html=True)
    st.write("Chat with our AI-powered medical assistant.")

    chat_container = st.container()
    with chat_container:
        for user_msg, ai_msg in st.session_state.chat_history:
            with st.chat_message("You"):
                st.markdown(user_msg)
            with st.chat_message("AI"):
                st.markdown(ai_msg)

    user_input = st.chat_input("Ask me anything about health...")

    if user_input:
        with st.chat_message("You"):
            st.markdown(user_input)

        response = get_medical_response(user_input, st.session_state.chat_history)

        with st.chat_message("AI"):
            st.markdown(response)

        st.session_state.chat_history.append((user_input, response))
    
    # Image Upload and Analysis
    uploaded_image = st.file_uploader("Upload a medical image (X-ray, skin rash, etc.) for AI analysis:", type=["png", "jpg", "jpeg"])
    if uploaded_image is not None:
        image = Image.open(uploaded_image)
        st.image(image, caption="Uploaded Image", use_column_width=True)
        
        with st.spinner("Analyzing Image..."):
            analysis_result = analyze_medical_image(image)
            st.subheader("🔍 AI Analysis Result:")
            st.write(analysis_result)
    
    if st.button("🏠 Back to Home", key="home_btn", use_container_width=True):
        st.session_state.page = "home"
        st.session_state.chat_history = []  # Clear chat history when returning home
        st.rerun()
