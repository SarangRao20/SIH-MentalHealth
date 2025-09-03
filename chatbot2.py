import streamlit as st
import pandas as pd
import os
from datetime import datetime

from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain_core.output_parsers import StrOutputParser

# Imports for audio features
from st_audiorec import st_audiorec
import whisper
import pyttsx3
import threading

# --- App Title ---
st.title("My Empathetic Wellness Chatbot 🧠")
st.markdown("Your mood is automatically tracked. Based on your mood, the bot may suggest resources in the sidebar.")

# --- Sidebar ---
st.sidebar.header("Settings")
enable_voice = st.sidebar.checkbox("Enable Voice Features", value=True)
enable_mood_tracking = st.sidebar.checkbox("Enable Automatic Mood Tracking", value=True)

# --- (NEW) Function to Suggest a Test Based on Mood ---
def get_test_suggestion(mood_emoji):
    suggestions = {
        '😔': {
            "name": "PHQ-9 Questionnaire",
            "description": "This is a common screening tool that helps in understanding symptoms of depression. It is not a diagnosis.",
            "link": "https://www.mdcalc.com/calc/1725/phq-9-patient-health-questionnaire-9"
        },
        '😥': {
            "name": "GAD-7 Questionnaire",
            "description": "This is a common screening tool used to help understand symptoms of anxiety. It is not a diagnosis.",
            "link": "https://www.mdcalc.com/calc/1727/gad-7-general-anxiety-disorder-7"
        },
        '😊': {
            "name": "WHO-5 Well-Being Index",
            "description": "This is a quick way to measure your current mental well-being.",
            "link": "https://www.psycom.net/self-assessments/who-5-well-being-index"
        }
    }
    return suggestions.get(mood_emoji)

# --- Mood Tracking & Other Setups ---
mood_file = "mood_log.csv"

def save_mood(mood_entry):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = pd.DataFrame([{"timestamp": timestamp, "mood": mood_entry}])
    if os.path.exists(mood_file):
        new_entry.to_csv(mood_file, mode='a', header=False, index=False)
    else:
        new_entry.to_csv(mood_file, mode='w', header=True, index=False)

def get_mood_from_text(llm, user_text):
    mood_prompt = ChatPromptTemplate.from_messages([
        ("system", "Analyze the user's text and classify the primary mood as one of the following emojis: 😊, 😐, 😔, 😠, 😥. Respond with ONLY the single emoji."),
        ("human", "{text_input}")
    ])
    mood_chain = mood_prompt | llm | StrOutputParser()
    mood = mood_chain.invoke({"text_input": user_text})
    valid_emojis = ['😊', '😐', '😔', '😠', '😥']
    for emoji in valid_emojis:
        if emoji in mood: return emoji
    return None

# --- Whisper Model ---
@st.cache_resource
def load_whisper_model():
    model = whisper.load_model("base"); return model
whisper_model = load_whisper_model()

# --- Conversation Chain Setup ---
@st.cache_resource
def get_conversation_chain():
    llm = ChatOllama(model="llama3.1:latest")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a warm, empathetic, and friendly companion."
        "give the answer point wise."
        "the user can use hindi or english language give the result in the same language as the user"
        "highlight the main keywords in the response"
        "keep the response more humanly "),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    conversation_chain = ConversationChain(llm=llm, prompt=prompt, memory=memory, verbose=False)
    return conversation_chain, llm
conversation_chain, llm = get_conversation_chain()

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "suggestion" not in st.session_state:
    st.session_state.suggestion = None

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Threaded TTS Function ---
def speak_text(text):
    def _speak():
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    threading.Thread(target=_speak, daemon=True).start()

# --- Process & Respond Function ---
def process_and_respond(user_input):
    if enable_mood_tracking:
        detected_mood = get_mood_from_text(llm, user_input)
        if detected_mood:
            save_mood(detected_mood)
            st.session_state.suggestion = get_test_suggestion(detected_mood)

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = conversation_chain.invoke({"input": user_input})
            response = result['response']
            st.markdown(response)

            if enable_voice:
                try:
                    speak_text(response)  # ✅ now non-blocking, no run loop error
                except Exception as e:
                    st.error(f"Couldn't generate audio: {e}")

    st.session_state.messages.append({"role": "assistant", "content": response})

# --- Display Suggestion in Sidebar ---
if st.session_state.suggestion:
    with st.sidebar.expander("Based on your recent chat, you might find this helpful:", expanded=True):
        suggestion = st.session_state.suggestion
        st.subheader(suggestion["name"])
        st.write(suggestion["description"])
        st.markdown(f"[Learn More Here]({suggestion['link']})")
        st.warning("**Disclaimer:** This is not a diagnosis. Please consult a healthcare professional for any concerns.")

# --- Mood Visualization ---
if enable_mood_tracking:
    st.sidebar.header("Your Mood History")
    if os.path.exists(mood_file):
        df = pd.read_csv(mood_file)
        if not df.empty:
            st.sidebar.line_chart(df.set_index('timestamp')['mood'])
        else:
            st.sidebar.write("No moods logged yet.")
    else:
        st.sidebar.write("No moods logged yet.")

# --- Voice & Text Input ---
if enable_voice:
    st.sidebar.header("Voice Input")
    audio_bytes = st_audiorec()
    if audio_bytes:
        with open("temp_audio.wav", "wb") as f:
            f.write(audio_bytes)
        try:
            with st.spinner("Transcribing..."):
                result = whisper_model.transcribe("temp_audio.wav")
                transcript = result["text"]
                process_and_respond(transcript)
        except Exception as e:
            st.sidebar.error(f"Error: {e}")
        finally:
            if os.path.exists("temp_audio.wav"):
                os.remove("temp_audio.wav")  # ✅ safe cleanup

# --- Text Input ---
if prompt := st.chat_input("How are you feeling today?"):
    process_and_respond(prompt)
