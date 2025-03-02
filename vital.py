import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore
from PIL import Image
import io
import speech_recognition as sr  # Import Speech Recognition

# Set up Streamlit UI with dark mode
st.set_page_config(page_title="HealBot", layout="wide")
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
genai.configure(api_key="AIzaSyCjYIyf12JbZbXO4GLUg4k-dX3y8E6Ieak")  # Replace with your actual API key

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

def get_medical_response(user_input, chat_history):
    context = ("You are a professional medical assistant. "
               "Answer questions related to health and medicine with accurate, reliable information. "
               "Follow this response format strictly:\n"
               "\n**<IDENTIFY IMAGE/DISEASE/PROBLEM>**\n"
               "\n**<SYMPTOMS>**\n"
               "\n**<POSSIBLE CAUSES>**\n"
               "\n**<PRECAUTIONS>**\n"
               "\n**<DIET OR EXERCISE IF NECESSARY>**\n"
               "\n**<WHEN TO SEE DOCTOR>**\n"
               "If a query is outside medical knowledge, state that you cannot provide advice.")
    
    past_chats = "\n".join([f"User: {msg}\nAI: {resp}" for msg, resp in chat_history[-5:]])  # Use last 5 messages for context
    prompt = f"{context}\n{past_chats}\nUser: {user_input}\nAI:"
    
    response = model.generate_content(prompt)
    return response.text

    
    analysis_result = response.text

def analyze_medical_image(image):
    # Check if the image has already been analyzed
    if "last_uploaded_image" in st.session_state and st.session_state.last_uploaded_image == image:
        return st.session_state.image_analysis_result  # Return the existing result

    response = model.generate_content([
        "Analyze the given medical image and provide insights in the following format:\n"
        "\n**<IDENTIFY IMAGE/DISEASE/PROBLEM>**\n"
        "\n**<SYMPTOMS>**\n"
        "\n**<POSSIBLE CAUSES>**\n"
        "\n**<PRECAUTIONS>**\n"
        "\n**<DIET OR EXERCISE IF NECESSARY>**\n"
        "\n**<WHEN TO SEE DOCTOR>**\n",
        image
    ])
    
    # Ensure a valid response is assigned
    analysis_result = response.text if response and hasattr(response, "text") else "No analysis available."

    # Store in Firebase
    db.collection("image_analysis").add({
        "analysis_result": analysis_result
    })
    
    # Store in session state to prevent reanalysis
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

if st.session_state.page == "home":
    st.markdown("<h1 style='text-align:center;'>&#127973; HealBot</h1>", unsafe_allow_html=True)
    st.write("Welcome to the AI-powered medical assistant. Click below to start chatting.")

    if st.button("🩺 Open Assistant", key="assistant_btn", use_container_width=True):
        st.session_state.page = "chatbot"
        st.rerun()

elif st.session_state.page == "chatbot":
    st.markdown("<h1 style='text-align:center;'>&#129657; HealBot</h1>", unsafe_allow_html=True)
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
    
    # Image Upload and Analysis
    uploaded_image = st.file_uploader("➕ Upload a medical image (X-ray, skin rash, etc.) for AI analysis:", type=["png", "jpg", "jpeg"])

    if uploaded_image is not None:
        image = Image.open(uploaded_image)
        st.image(image, caption="📷 Uploaded Image", use_column_width=True)
        
        if "last_uploaded_image" not in st.session_state or st.session_state.last_uploaded_image != image:
            with st.spinner("🔍 Analyzing Image..."):
                analysis_result = analyze_medical_image(image)
                st.session_state.image_analysis_result = analysis_result
        else:
            st.write("✅ This image has already been analyzed.")
                
# Display last analyzed image response
if st.session_state.image_analysis_result:
    st.subheader("🩺 AI Analysis Result:")
    st.write(st.session_state.image_analysis_result)
    
    if st.button("🏠 Back to Home", key="home_btn", use_container_width=True):
        st.session_state.page = "home"
        st.session_state.chat_history = []  # Clear chat history when returning home
        st.session_state.image_analysis_result = None  # Reset stored image analysis result
        st.rerun()
