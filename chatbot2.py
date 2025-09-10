import streamlit as st
import pandas as pd
import os
from datetime import datetime
import csv 

# from langchain_community.chat_models import ChatOllama
from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain_core.output_parsers import StrOutputParser

# Audio features
from audiorecorder import audiorecorder
import whisper
import pyttsx3
import threading


engine = pyttsx3.init()
voices = engine.getProperty('voices')
for idx, v in enumerate(voices):
    print(idx, v.name, v.id)

# --- Global File ---
MOOD_FILE = "mood_log.csv"

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
            "description": "Helps understand symptoms of depression. Not a diagnosis.",
            "link": "https://www.mdcalc.com/calc/1725/phq-9-patient-health-questionnaire-9"
        },
        '😥': {
            "name": "GAD-7 Questionnaire",
            "description": "Helps understand symptoms of anxiety. Not a diagnosis.",
            "link": "https://www.mdcalc.com/calc/1727/gad-7-general-anxiety-disorder-7"
        },
        '😊': {
            "name": "WHO-5 Well-Being Index",
            "description": "A quick measure of your current mental well-being.",
            "link": "https://www.psycom.net/self-assessments/who-5-well-being-index"
        }
    }
    return suggestions.get(mood_emoji)

# --- Mood Tracking ---
def save_mood_csv(mood_entry, mood_file=MOOD_FILE):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_exists = os.path.exists(mood_file) and os.path.getsize(mood_file) > 0
    with open(mood_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp','mood'])
        if not file_exists:
            writer.writeheader()
        writer.writerow({'timestamp': timestamp, 'mood': mood_entry})

def get_mood_from_text(llm, user_text):
    mood_prompt = ChatPromptTemplate.from_messages([
        ("system", "Classify the user's text into one mood emoji: 😊, 😐, 😔, 😠, 😥. Respond ONLY with the emoji."),
        ("human", "{text_input}")
    ])
    mood_chain = mood_prompt | llm | StrOutputParser()
    mood = mood_chain.invoke({"text_input": user_text})
    valid_emojis = ['😊', '😐', '😔', '😠', '😥']
    for emoji in valid_emojis:
        if emoji in mood: 
            return emoji
    return None

# --- Whisper Model ---
@st.cache_resource
def load_whisper_model():
    return whisper.load_model("base")
whisper_model = load_whisper_model()

# --- Conversation Chain Setup ---
@st.cache_resource
def get_conversation_chain():
    llm = ChatOllama(model="llama3.1:latest")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a warm, empathetic coach and friendly companion."
         " Give answers point-wise."
         " Use same language as user (Hindi/English/Hinglish)."
         " Keep responses human-like."
         " User is based in India."
         " Suggest small steps if situation is very bad."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    conversation_chain = ConversationChain(
        llm=llm, 
        prompt=prompt, 
        memory=memory, 
        verbose=False,
        output_key="response"  # ✅ ensures dict has "response"
    )
    return conversation_chain, llm

conversation_chain, llm = get_conversation_chain()

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "suggestion" not in st.session_state:
    st.session_state.suggestion = None

# Replay old messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- TTS ---
import queue

# put this near your other globals
tts_queue = queue.Queue()

def speak_worker():
    while True:
        text = tts_queue.get()
        if text is None:
            break
        engine.say(text)
        engine.runAndWait()
        tts_queue.task_done()

# start the worker thread once
threading.Thread(target=speak_worker, daemon=True).start()

def speak_text(text):
    tts_queue.put(text)


# --- Process & Respond ---
def process_and_respond(user_input):
    if enable_mood_tracking:
        detected_mood = get_mood_from_text(llm, user_input)
        if detected_mood:
            save_mood_csv(detected_mood)
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
                    speak_text(response)
                except Exception as e:
                    st.error(f"Couldn't generate audio: {e}")

    st.session_state.messages.append({"role": "assistant", "content": response})

# --- Sidebar Suggestion ---
if st.session_state.suggestion:
    with st.sidebar.expander("Based on your recent chat, you might find this helpful:", expanded=True):
        suggestion = st.session_state.suggestion
        st.subheader(suggestion["name"])
        st.write(suggestion["description"])
        st.markdown(f"[Learn More Here]({suggestion['link']})")
        st.warning("**Disclaimer:** This is not a diagnosis. Please consult a healthcare professional.")

# --- Mood Visualization ---
if enable_mood_tracking:
    st.sidebar.header("Your Mood History")
    if os.path.exists(MOOD_FILE):
        df = pd.read_csv(MOOD_FILE)
        if not df.empty:
            # Map moods to numeric values for chart
            mood_map = {'😊': 2, '😐': 1, '😔': -1, '😠': -2, '😥': -1.5}
            df['mood_value'] = df['mood'].map(mood_map)
            st.sidebar.line_chart(df.set_index('timestamp')['mood_value'])
        else:
            st.sidebar.write("No moods logged yet.")
    else:
        st.sidebar.write("No moods logged yet.")

# --- Voice Input ---
if enable_voice:
    st.sidebar.header("Voice Input")
    audio = audiorecorder("🎤 Start recording", "Recording...")
    if len(audio) > 0:
        temp_file = "temp_audio.wav"
        audio.export(temp_file, format="wav")
        try:
            with st.spinner("Transcribing..."):
                result = whisper_model.transcribe(temp_file)
                transcript = result["text"]
                process_and_respond(transcript)
        except Exception as e:
            st.sidebar.error(f"Error: {e}")
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

# --- Text Input ---
if prompt := st.chat_input("How are you feeling today?"):
    process_and_respond(prompt)


