import streamlit as st
import pandas as pd
import os
from datetime import datetime
import subprocess  # To run Piper
import re        # To clean text for Piper

from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain_core.output_parsers import StrOutputParser

# Imports for audio features
from st_audiorec import st_audiorec
import whisper

# --- App Title ---
st.title("My Empathetic Wellness Chatbot 🧠")
st.markdown("Your mood is automatically tracked. Based on mood patterns, the bot may suggest resources.")

# --- Sidebar ---
st.sidebar.header("Settings")
enable_voice = st.sidebar.checkbox("Enable Voice Features", value=True)
enable_mood_tracking = st.sidebar.checkbox("Enable Automatic Mood Tracking", value=True)

# --- Piper TTS Setup ---
PIPER_EXE = "./piper.exe"
VOICE_MODEL = "./en_US-lessac-medium.onnx"

def play_audio_with_piper(text_to_speak):
    # Clean text to remove emojis for better TTS performance
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               "]+", flags=re.UNICODE)
    clean_text = emoji_pattern.sub(r'', text_to_speak)
    
    output_audio_file = "output_audio.wav"
    command = f'echo "{clean_text}" | "{PIPER_EXE}" --model "{VOICE_MODEL}" --output_file "{output_audio_file}"'
    
    try:
        subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(output_audio_file):
            st.audio(output_audio_file, autoplay=True)
    except subprocess.CalledProcessError as e:
        st.error(f"Error generating audio with Piper: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

# --- Function to Suggest a Test Based on Mood ---
def get_test_suggestion(mood_emoji):
    suggestions = {
        '😔': {"name": "PHQ-9 Questionnaire", "description": "A common tool to help understand symptoms of depression.", "link": "https://www.mdcalc.com/calc/1725/phq-9-patient-health-questionnaire-9"},
        '😥': {"name": "GAD-7 Questionnaire", "description": "A common tool to help understand symptoms of anxiety.", "link": "https://www.mdcalc.com/calc/1727/gad-7-general-anxiety-disorder-7"}
    }
    return suggestions.get(mood_emoji)

# --- Mood Tracking & Other Setups ---
mood_file = "mood_log.csv"
SUGGESTION_THRESHOLD = 3

def save_mood(mood_entry):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = pd.DataFrame([{"timestamp": timestamp, "mood": mood_entry}])
    if os.path.exists(mood_file):
        new_entry.to_csv(mood_file, mode='a', header=False, index=False)
    else:
        new_entry.to_csv(mood_file, mode='w', header=True, index=False)

def get_mood_from_text(llm, user_text):
    mood_prompt = ChatPromptTemplate.from_messages([
        ("system", "Analyze the user's text and classify the primary mood as one of these emojis: 😊, 😐, 😔, 😠, 😥. Respond with ONLY the single emoji."),
        ("human", "{text_input}")
    ])
    mood_chain = mood_prompt | llm | StrOutputParser()
    mood = mood_chain.invoke({"text_input": user_text})
    valid_emojis = ['😊', '😐', '😔', '😠', '😥']
    for emoji in valid_emojis:
        if emoji in mood: return emoji
    return None

# --- Main App Logic (Whisper, LLM Setup) ---
@st.cache_resource
def load_whisper_model():
    model = whisper.load_model("base"); return model
whisper_model = load_whisper_model()

@st.cache_resource
def get_conversation_chain():
    llm = ChatOllama(model="llama3.1:latest")
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a warm, empathetic, and friendly companion. Your primary goal is to listen and offer supportive, non-judgmental responses. Respond in the same language (English or Hinglish) as the user's input. Do not give medical advice. Focus on making the user feel heard and understood."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])
    memory = ConversationBufferMemory(key="chat_history", return_messages=True)
    conversation_chain = ConversationChain(llm=llm, prompt=prompt, memory=memory, verbose=False,memory_key="chat_history",input_key="input")
    return conversation_chain, llm
conversation_chain, llm = get_conversation_chain()

# --- Initialize Session State ---
if "messages" not in st.session_state: st.session_state.messages = []
if "suggestion" not in st.session_state: st.session_state.suggestion = None
if "mood_counts" not in st.session_state: st.session_state.mood_counts = {'😔': 0, '😥': 0}

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def process_and_respond(user_input):
    st.session_state.suggestion = None
    if enable_mood_tracking:
        detected_mood = get_mood_from_text(llm, user_input)
        if detected_mood:
            save_mood(detected_mood)
            if detected_mood in st.session_state.mood_counts:
                st.session_state.mood_counts[detected_mood] += 1
                if st.session_state.mood_counts[detected_mood] >= SUGGESTION_THRESHOLD:
                    st.session_state.suggestion = get_test_suggestion(detected_mood)
                    st.session_state.mood_counts[detected_mood] = 0

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = conversation_chain.invoke({"input": user_input})
            response = result['response']
            st.markdown(response)
            if enable_voice:
                play_audio_with_piper(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

# --- Display Suggestion in Sidebar ---
if st.session_state.suggestion:
    with st.sidebar.expander("Based on our recent chats, you might find this helpful:", expanded=True):
        suggestion = st.session_state.suggestion
        st.subheader(suggestion["name"])
        st.write(suggestion["description"])
        st.markdown(f"[Learn More Here]({suggestion['link']})")
        st.warning("**Disclaimer:** This is not a diagnosis. Please consult a healthcare professional.")

# --- Mood Visualization ---
if enable_mood_tracking:
    st.sidebar.header("Your Mood History")
    if os.path.exists(mood_file):
        df = pd.read_csv(mood_file)
        if not df.empty: st.sidebar.line_chart(df.set_index('timestamp')['mood'])
        else: st.sidebar.write("No moods logged yet.")
    else: st.sidebar.write("No moods logged yet.")

# --- Voice & Text Input ---
if enable_voice:
    st.sidebar.header("Voice Input")
    audio_bytes = st_audiorec()
    if audio_bytes:
        with open("temp_audio.wav", "wb") as f: f.write(audio_bytes)
        with st.spinner("Transcribing..."):
            try:
                result = whisper_model.transcribe("temp_audio.wav"); transcript = result["text"]
                process_and_respond(transcript)
            except Exception as e: st.sidebar.error(f"Error: {e}")
        os.remove("temp_audio.wav")

if prompt := st.chat_input("How are you feeling today?"):
    process_and_respond(prompt)
