import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore
from PIL import Image
import io
import speech_recognition as sr  # Import Speech Recognition

# Set up Streamlit UI with dark mode
st.set_page_config(page_title="Medical AI Assistant", layout="wide")
st.markdown("""
    <style>
    body {
        background-color: #121212;
        color: white;
    }
    .stChatInput input {
        background-color: #1e1e1e;
        color: white;
        border-radius: 10px;
        padding: 10px;
    }
    .stChatMessage {
        background-color: #1e1e1e;
        color: white;
        border-radius: 10px;
        padding: 10px;
        margin: 5px 0;
    }
    .stButton button {
        background-color: #00b4d8;
        color: white;
        border-radius: 10px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Configure Gemini AI (Medical Assistant Mode)
genai.configure(api_key="AIzaSyD99tI0dl5hpKSery1FwZNUceSQeHrPyPY")  # Replace with your actual API key

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
    context = "You are a professional medical assistant. Answer questions related to health and medicine with accurate, reliable information. Format your responses as follows:\n\n"
    
    #context += "**<IDENTIFY IMAGE/DISEASE/PROBLEM>**\n**<SYMPTOMS>**\n**<PRECAUTIONS>**\n**<DIET OR EXERCISE IF NECESSARY>**\n**<WHEN TO SEE DOCTOR>**\n"
    context += "**<IDENTIFY IMAGE/DISEASE/PROBLEM>**\n"
    context += "**<SYMPTOMS>**\n"
    context += "**<PRECAUTIONS>**\n"
    context += "**<DIET OR EXERCISE IF NECESSARY>**\n"
    context += "**<WHEN TO SEE DOCTOR>**\n"
  
    context += "If a query is outside medical knowledge, state that you cannot provide advice."
    
    past_chats = "\n".join([f"User: {msg}\nAI: {resp}" for msg, resp in chat_history[-5:]])  # Use last 5 messages for context
    prompt = f"{context}\n{past_chats}\nUser: {user_input}\nAI:"
    
    response = model.generate_content(prompt)
    return response.text

# Analyze Medical Image and Store in Firebase & Session State
def analyze_medical_image(image):
    if st.session_state.get("last_uploaded_image") == image:
        return st.session_state.image_analysis_result
    response = model.generate_content([
    "Analyze the given medical image and provide insights in the required format:\n\n"
    "**<IDENTIFY IMAGE/DISEASE/PROBLEM>**\n"
    "**<SYMPTOMS>**\n"
    "**<PRECAUTIONS>**\n"
    "**<DIET OR EXERCISE IF NECESSARY>**\n"
    "**<WHEN TO SEE DOCTOR>**",
    image
    ])

    # response = model.generate_content([
    #     "Analyze the given medical image and provide insights in the required format:\n\n"
    #     "**<IDENTIFY IMAGE/DISEASE/PROBLEM>**\n**<SYMPTOMS>**\n**<PRECAUTIONS>**\n**<DIET OR EXERCISE IF NECESSARY>**\n**<WHEN TO SEE DOCTOR>**",
    #     image  # Directly passing the PIL image instead of raw bytes
    # ])
    
    analysis_result = response.text
    
    # Store in Firebase
    db.collection("image_analysis").add({
        "analysis_result": analysis_result
    })
    
    # Store in session state to remember response
    st.session_state.image_analysis_result = analysis_result
    st.session_state.last_uploaded_image = image
    
    return analysis_result

# Speech Recognition Function
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("🎙️ Listening... Speak now!")
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return "Could not understand the audio. Please try again."
        except sr.RequestError:
            return "Could not request results. Please check your internet connection."

# Home Page
if "page" not in st.session_state:
    st.session_state.page = "home"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # Reset chat history on restart
if "image_analysis_result" not in st.session_state:
    st.session_state.image_analysis_result = None  # Store last image analysis result
if "last_uploaded_image" not in st.session_state:
    st.session_state.last_uploaded_image = None

if st.session_state.page == "home":
    st.markdown("<h1 style='text-align:center;'>&#127973; Medical AI Assistant</h1>", unsafe_allow_html=True)
    st.write("Welcome to the AI-powered medical assistant. Click below to start chatting.")

    if st.button("🩺 Open Assistant", key="assistant_btn", use_container_width=True):
        st.session_state.page = "chatbot"
        st.rerun()

elif st.session_state.page == "chatbot":
    st.markdown("<h1 style='text-align:center;'>&#129657; AI Medical Chatbot</h1>", unsafe_allow_html=True)
    st.write("Chat with our AI-powered medical assistant.")

    chat_container = st.container()
    with chat_container:
        for user_msg, ai_msg in st.session_state.chat_history:
            with st.chat_message("You"):
                st.markdown(user_msg)
            with st.chat_message("AI"):
                st.markdown(ai_msg)

    user_input = st.chat_input("Ask anything...", key="chat_input")
    
    if st.button("🎤 Speak", key="voice_input_btn"):
        user_input = recognize_speech()
        st.write(f"🗣️ You said: {user_input}")
    
    if user_input:
        with st.chat_message("You"):
            st.markdown(user_input)

        response = get_medical_response(user_input, st.session_state.chat_history)

        with st.chat_message("AI"):
            st.markdown(response)

        st.session_state.chat_history.append((user_input, response))
