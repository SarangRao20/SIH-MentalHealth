from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GENAI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")

st.set_page_config(page_title="MindMate 💙", page_icon="💭", layout="centered")

st.markdown(
    """
    <style>
    body {
        background-color: #f7f9fc;
    }
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("💙 MindMate - Your Friendly Companion")
st.write("Hi there 👋! I'm here to chat, listen, and cheer you up 🌸. Not a doctor, just a buddy who cares.")


# --------------------------
# 💬 Session State for Chat
# --------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# --------------------------
# 📩 Chat Input + Response
# --------------------------
user_input = st.chat_input("Type your thoughts here...")

if user_input:
    # Append user message
    st.session_state.chat_history.append(("You", user_input))

    # Gemini response
    response = model.generate_content(
            f"""
    You are MindMate 💙, a kind and caring friend who chats casually and supportively. 
    Your style: warm, gentle, slightly playful, but never judgmental. 
    Avoid sounding like a doctor or giving medical advice. 
    Use emojis sparingly to make responses feel friendly and human. 
    Keep replies short and easy to read, like talking to a close buddy. 
    
    The user says: {user_input}
    """
    )
    bot_reply = response.text

    st.session_state.chat_history.append(("MindMate", bot_reply))


# --------------------------
# 📜 Display Chat History
# --------------------------
for sender, message in st.session_state.chat_history:
    if sender == "You":
        st.chat_message("user").markdown(message)
    else:
        st.chat_message("assistant").markdown(message)