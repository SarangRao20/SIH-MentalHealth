import streamlit as st
import pandas as pd
import os
from datetime import datetime
import csv

# Updated imports for Gemini
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain_core.output_parsers import StrOutputParser

# Audio features
from st_audiorec import st_audiorec
import whisper
from TTS.api import TTS
from pydub import AudioSegment

# --- Global File ---
MOOD_FILE = "mood_log.csv"
REFERENCE_WAV_PATH = "reference_clean.wav"

# --- App Title ---
st.title("My Empathetic Wellness Chatbot 🧠")
st.markdown("Your mood is automatically tracked. Based on your mood, the bot may suggest resources in the sidebar.")

# --- Sidebar ---
st.sidebar.header("Settings")

# API Key input
api_key = st.sidebar.text_input("Enter your Gemini API Key:", type="password", help="Get your API key from https://makersuite.google.com/app/apikey")
if not api_key:
    st.sidebar.warning("⚠️ Please enter your Gemini API key to use the chatbot")
    st.stop()

enable_voice = st.sidebar.checkbox("Enable Voice Features", value=True)
enable_mood_tracking = st.sidebar.checkbox("Enable Automatic Mood Tracking", value=True)

# File uploader for reference voice
st.sidebar.subheader("Upload Reference Voice File (WAV/MP3/OPUS)")
uploaded_file = st.sidebar.file_uploader("Choose a voice file", type=["wav", "mp3", "opus"])

# --- Function to Clean Audio ---
def clean_audio(uploaded_file, output_file="reference_clean.wav"):
    try:
        temp_path = "temp_uploaded.wav"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.read())

        # Convert to 16kHz, mono WAV
        audio = AudioSegment.from_file(temp_path)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(output_file, format="wav")

        os.remove(temp_path)
        return output_file
    except Exception as e:
        st.error(f"Error cleaning audio: {e}")
        return None

# If file uploaded, clean and save it
if uploaded_file:
    cleaned_path = clean_audio(uploaded_file, REFERENCE_WAV_PATH)
    if cleaned_path:
        st.sidebar.success(f"✅ Reference voice saved at {cleaned_path}")

# --- Function to Suggest a Test Based on Mood ---
def get_test_suggestion(mood_emoji):
    suggestions = {
        '😔': {"name": "PHQ-9 Questionnaire", "description": "Helps understand symptoms of depression. Not a diagnosis.", "link": "https://www.mdcalc.com/calc/1725/phq-9-patient-health-questionnaire-9"},
        '😥': {"name": "GAD-7 Questionnaire", "description": "Helps understand symptoms of anxiety. Not a diagnosis.", "link": "https://www.mdcalc.com/calc/1727/gad-7-general-anxiety-disorder-7"},
        '😊': {"name": "WHO-5 Well-Being Index", "description": "A quick measure of your current mental well-being.", "link": "https://www.psycom.net/self-assessments/who-5-well-being-index"}
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
    try:
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
    except Exception as e:
        st.error(f"Error in mood detection: {e}")
        return None

# --- Whisper Model ---
@st.cache_resource
def load_whisper_model():
    return whisper.load_model("base")

whisper_model = load_whisper_model()

# --- TTS Model ---
@st.cache_resource
def load_tts_model():
    return TTS("tts_models/multilingual/multi-dataset/xtts_v2")

tts_model = load_tts_model()

# --- Conversation Chain Setup ---
@st.cache_resource
def get_conversation_chain(_api_key):
    try:
        # Initialize Gemini model
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=_api_key,
            temperature=0.7,
            convert_system_message_to_human=True  # Gemini doesn't support system messages directly
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("human", "You are a warm, empathetic and friendly companion. Give answers point-wise. The user may use (hindi/english/) strictly give response in the same language. Keep responses human-like. User is based in India. Suggest small steps if situation is very bad.\n\nConversation history:\n{chat_history}\n\nCurrent message: {input}"),
        ])
        
        memory = ConversationBufferMemory(
            memory_key="chat_history", 
            return_messages=False,  # Return as string for better compatibility
            input_key="input",
            output_key="response"
        )
        
        conversation_chain = ConversationChain(
            llm=llm, 
            prompt=prompt, 
            memory=memory, 
            verbose=False, 
            output_key="response"
        )
        
        return conversation_chain, llm
    except Exception as e:
        st.error(f"Error initializing Gemini model: {e}")
        st.stop()

conversation_chain, llm = get_conversation_chain(api_key)

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "suggestion" not in st.session_state:
    st.session_state.suggestion = None

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- TTS ---
def speak_text(text, tts_model, reference_wav_path):
    try:
        output_audio_path = "temp_chatbot_audio.wav"
        tts_model.tts_to_file(
            text=text,
            speaker_wav=reference_wav_path,
            language="en", 
            file_path=output_audio_path
        )
        with open(output_audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
        st.audio(audio_bytes, format='audio/wav', autoplay=True)
    except Exception as e:
        st.error(f"Error generating audio: {e}")
    finally:
        if os.path.exists(output_audio_path):
            os.remove(output_audio_path)

# --- Process & Respond ---
def process_and_respond(user_input):
    try:
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
                
                if enable_voice and os.path.exists(REFERENCE_WAV_PATH):
                    speak_text(response, tts_model, REFERENCE_WAV_PATH)

        st.session_state.messages.append({"role": "assistant", "content": response})
    except Exception as e:
        st.error(f"Error processing response: {e}")

# --- Sidebar Suggestion & Mood Visualization ---
if st.session_state.suggestion:
    with st.sidebar.expander("Based on your recent chat, you might find this helpful:", expanded=True):
        suggestion = st.session_state.suggestion
        st.subheader(suggestion["name"])
        st.write(suggestion["description"])
        st.markdown(f"[Learn More Here]({suggestion['link']})")
        st.warning("**Disclaimer:** This is not a diagnosis. Please consult a healthcare professional.")

if enable_mood_tracking:
    st.sidebar.header("Your Mood History")
    if os.path.exists(MOOD_FILE):
        try:
            df = pd.read_csv(MOOD_FILE)
            if not df.empty:
                mood_map = {'😊': 2, '😐': 1, '😔': -1, '😠': -2, '😥': -1.5}
                df['mood_value'] = df['mood'].map(mood_map)
                st.sidebar.line_chart(df.set_index('timestamp')['mood_value'])
            else:
                st.sidebar.write("No moods logged yet.")
        except Exception as e:
            st.sidebar.error(f"Error loading mood data: {e}")
    else:
        st.sidebar.write("No moods logged yet.")

# --- Voice and Text Input ---
if enable_voice:
    st.sidebar.header("Voice Input")
    audio_bytes = st_audiorec()
    if audio_bytes:
        temp_file = "temp_audio.wav"
        with open(temp_file, "wb") as f:
            f.write(audio_bytes)
        try:
            with st.spinner("Transcribing..."):
                result = whisper_model.transcribe(temp_file)
                transcript = result["text"]
                if transcript.strip():  # Only process if transcript is not empty
                    process_and_respond(transcript)
        except Exception as e:
            st.sidebar.error(f"Error transcribing audio: {e}")
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

# Text input
if prompt := st.chat_input("How are you feeling today?"):
    process_and_respond(prompt)
