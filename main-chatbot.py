import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore

# Set up Streamlit UI
st.set_page_config(page_title="Healthcare AI Chatbot", layout="wide")

# Configure Gemini API
genai.configure(api_key="IzaSyAL6aVguGx_Ta60pnYWXdMbKIhorNBqgqU")  # Replace with your actual API key

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("C:\\Users\\User\\Downloads\\indovateieee-firebase-adminsdk-fbsvc-3a690188cc.json")  # Replace with your file path
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Load Gemini Model
@st.cache_resource
def load_model():
    return genai.GenerativeModel("gemini-1.5-pro-latest")

model = load_model()

# Retrieve chat history for a specific user
def load_chat_history():
    chats = db.collection("chats").order_by("timestamp").stream()
    return [(chat.get("user_message"), chat.get("ai_response")) for chat in chats]

# Generate response with chat history for context
def get_gemini_response(user_input, chat_history):
    # Format past chats to provide context
    context = "\n".join([f"User: {msg}\nAI: {resp}" for msg, resp in chat_history[-5:]])  # Use last 5 messages for context
    prompt = f"{context}\nUser: {user_input}\nAI:"
    
    # Get response from Gemini
    response = model.generate_content(prompt)
    return response.text

# Store chat in Firestore
def save_chat_to_firebase(user_input, response):
    chat_data = {
        "user_message": user_input,
        "ai_response": response,
        "timestamp": firestore.SERVER_TIMESTAMP
    }
    db.collection("chats").add(chat_data)

# Home Page
if "page" not in st.session_state:
    st.session_state.page = "home"

if st.session_state.page == "home":
    st.markdown("<h1 style='text-align:center;'>🏥 Healthcare AI Chatbot</h1>", unsafe_allow_html=True)
    st.write("Welcome to the AI-powered healthcare assistant. Click below to start chatting.")

    if st.button("🤖 Open Chatbot", key="chatbot_btn", use_container_width=True):
        st.session_state.page = "chatbot"
        st.session_state.chat_history = load_chat_history()  # Load previous chats
        st.rerun()

elif st.session_state.page == "chatbot":
    st.markdown("<h1 style='text-align:center;'>🤖 Gemini AI Chatbot</h1>", unsafe_allow_html=True)
    st.write("Chat with Gemini-powered AI")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = load_chat_history()

    chat_container = st.container()
    with chat_container:
        for user_msg, ai_msg in st.session_state.chat_history:
            with st.chat_message("You"):
                st.markdown(user_msg)
            with st.chat_message("AI"):
                st.markdown(ai_msg)

    user_input = st.chat_input("Type your message...")

    if user_input:
        with st.chat_message("You"):
            st.markdown(user_input)

        response = get_gemini_response(user_input, st.session_state.chat_history)

        with st.chat_message("AI"):
            st.markdown(response)

        st.session_state.chat_history.append((user_input, response))
        save_chat_to_firebase(user_input, response)  # Store chat in Firestore

    if st.button("🏠 Back to Home", key="home_btn", use_container_width=True):
        st.session_state.page = "home"
        st.rerun()
