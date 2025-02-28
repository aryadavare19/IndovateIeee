import streamlit as st
import google.generativeai as genai
import os

# Set page config first
st.set_page_config(page_title="Healthcare AI Chatbot", layout="wide")

# Configure Gemini API
genai.configure(api_key="AIzaSyAL6aVguGx_Ta60pnYWXdMbKIhorNBqgqU")  # Replace with your actual API key

@st.cache_resource
def load_model():
    return genai.GenerativeModel("gemini-1.5-pro-latest")

model = load_model()

@st.cache_data
def get_gemini_response(prompt):
    response = model.generate_content(prompt)
    return response.text

st.markdown(
     """
    <style>
    body {
        background-color: #ffebee;
    }
    .main-title {
        text-align: center;
        color: #b71c1c;
    }
    .chat-container {
        background-color: #ffcdd2;
        padding: 20px;
        border-radius: 10px;
    }
    .button-container {
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Home Page
if "page" not in st.session_state:
    st.session_state.page = "home"

if st.session_state.page == "home":
    st.markdown("<h1 class='main-title'>🏥 Healthcare AI Chatbot</h1>", unsafe_allow_html=True)
    # st.image(os.path.join(os.getcwd(),"static","SBQ-Hard-Work.jpg"))
    st.write("Welcome to the AI-powered healthcare assistant. Click the chatbot icon below to start chatting.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🤖 Open Chatbot", key="chatbot_btn", use_container_width=True):
            st.session_state.page = "chatbot"
            st.rerun()

elif st.session_state.page == "chatbot":
    st.markdown("<h1 class='main-title'>🤖 Gemini AI Chatbot</h1>", unsafe_allow_html=True)
    st.write("Chat with Gemini-powered AI")
    
    # Initialize chat history if not already present
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Chat interface
    chat_container = st.container()
    with chat_container:
        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
        for role, message in st.session_state.chat_history:
            with st.chat_message(role):
                st.markdown(message)
        st.markdown("</div>", unsafe_allow_html=True)

    # User Input
    user_input = st.chat_input("Type your message...")

    if user_input:
        with st.chat_message("You"):
            st.markdown(user_input)
        
        response = get_gemini_response(user_input)
        
        with st.chat_message("AI"):
            st.markdown(response)
        
        # Store chat history
        st.session_state.chat_history.append(("You", user_input))
        st.session_state.chat_history.append(("AI", response))
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🏠 Back to Home", key="home_btn", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
