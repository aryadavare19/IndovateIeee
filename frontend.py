from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication

# Configure Gemini AI
genai.configure(api_key="IzaSyAL6aVguGx_Ta60pnYWXdMbKIhorNBqgqU")  # Replace with your actual API key
model = genai.GenerativeModel("gemini-1.5-pro-latest")

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("C:\\Users\\User\\Downloads\\indovateieee-firebase-adminsdk-fbsvc-3a690188cc.json")  # Replace with your file path
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Fetch chat history
@app.route('/api/chats', methods=['GET'])
def load_chat_history():
    chats = db.collection("chats").order_by("timestamp").stream()
    chat_data = [{"user_message": chat.get("user_message"), "ai_response": chat.get("ai_response")} for chat in chats]
    return jsonify(chat_data)

# Generate AI response
@app.route('/api/generate', methods=['POST'])
def get_gemini_response():
    data = request.json
    user_input = data.get("user_input", "")
    chat_history = data.get("chat_history", [])

    # Format chat history for context
    context = "\n".join([f"User: {msg['user_message']}\nAI: {msg['ai_response']}" for msg in chat_history[-5:]])  
    prompt = f"{context}\nUser: {user_input}\nAI:"
    
    # Get response from Gemini
    response = model.generate_content(prompt)
    ai_response = response.text.strip()

    # Store in Firebase
    chat_data = {
        "user_message": user_input,
        "ai_response": ai_response,
        "timestamp": firestore.SERVER_TIMESTAMP
    }
    db.collection("chats").add(chat_data)

    return jsonify({"ai_response": ai_response})

if __name__ == '__main__':
    app.run(port=5000, debug=True)  # Run Flask on port 5000
