import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore
import speech_recognition as sr
import pyttsx3

# Set up Streamlit UI
st.set_page_config(page_title="Medical AI Assistant", layout="wide")

# Configure Gemini AI (Medical Assistant Mode)
genai.configure(api_key="YOUR_API_KEY")  # Replace with your actual API key

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

# Initialize Text-to-Speech Engine
tts_engine = pyttsx3.init()
def speak(text):
    tts_engine.say(text)
    tts_engine.runAndWait()

# Speech-to-Text Function
def speech_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening...")
        try:
            audio = recognizer.listen(source, timeout=5)
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return "Could not understand audio. Please try again."
        except sr.RequestError:
            return "Speech recognition service is unavailable."

# Generate Medical Response
def get_medical_response(user_input, chat_history):
    context = "You are a professional medical assistant. Answer questions related to health and medicine with accurate, reliable information. If a query is outside medical knowledge, state that you cannot provide advice."
    past_chats = "\n".join([f"User: {msg}\nAI: {resp}" for msg, resp in chat_history[-5:]])  # Use last 5 messages for context
    prompt = f"{context}\n{past_chats}\nUser: {user_input}\nAI:"
    
    response = model.generate_content(prompt)
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

    col1, col2 = st.columns([3, 1])
    with col1:
        user_input = st.chat_input("Ask me anything about health...")
    with col2:
        if st.button("🎤 Speak", key="voice_input_btn", use_container_width=True):
            user_input = speech_to_text()
            st.write(f"You said: {user_input}")

    if user_input:
        with st.chat_message("You"):
            st.markdown(user_input)

        response = get_medical_response(user_input, st.session_state.chat_history)

        with st.chat_message("AI"):
            st.markdown(response)
            speak(response)  # Convert AI response to speech

        st.session_state.chat_history.append((user_input, response))

    if st.button("🏠 Back to Home", key="home_btn", use_container_width=True):
        st.session_state.page = "home"
        st.session_state.chat_history = []  # Clear chat history when returning home
        st.rerun()
