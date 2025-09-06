import os
import logging
import csv
from datetime import datetime
import threading
import io
from flask import Flask, render_template, request, jsonify, send_file
from markupsafe import Markup
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy.orm import DeclarativeBase
import matplotlib.pyplot as plt
import pandas as pd
from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain_core.output_parsers import StrOutputParser
import pyttsx3

logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///mental_health.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {'pool_pre_ping': True, "pool_recycle": 300}
db = SQLAlchemy(model_class=Base)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

with app.app_context():
    import models
    db.create_all()
    logging.info("Database tables created")

def nl2br(value):
    if value is None:
        return ''
    if not isinstance(value, str):
        value = str(value)
    return Markup(value.replace('\n', '<br>'))

app.jinja_env.filters['nl2br'] = nl2br

MOOD_FILE = "mood_log.csv"

llm = ChatOllama(model="llama3.1:latest")
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a warm, empathetic coach and companion. Answer point-wise, in Hinglish/English. Suggest small steps."),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
conversation_chain = ConversationChain(llm=llm, prompt=prompt, memory=memory, output_key="response")

mood_prompt = ChatPromptTemplate.from_messages([
    ("system", "Classify the user's text into one emoji: 😊, 😐, 😔, 😠, 😥. Respond ONLY with the emoji."),
    ("human", "{text_input}")
])
mood_chain = mood_prompt | llm | StrOutputParser()

def save_mood_csv(mood_entry, mood_file=MOOD_FILE):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_exists = os.path.exists(mood_file) and os.path.getsize(mood_file) > 0
    with open(mood_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'mood'])
        if not file_exists:
            writer.writeheader()
        writer.writerow({'timestamp': timestamp, 'mood': mood_entry})

def speak_text(text):
    def _speak():
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    threading.Thread(target=_speak, daemon=True).start()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"error": "No input provided"}), 400
    mood = mood_chain.invoke({"text_input": user_input})
    valid_emojis = ['😊', '😐', '😔', '😠', '😥']
    detected_mood = mood if mood in valid_emojis else None
    if detected_mood:
        save_mood_csv(detected_mood)
    result = conversation_chain.invoke({"input": user_input})
    response = result["response"]
    speak_text(response)
    return jsonify({"response": response, "mood": detected_mood})

@app.route("/mood")
def mood_chart():
    if not os.path.exists(MOOD_FILE):
        return "No mood history yet."
    df = pd.read_csv(MOOD_FILE)
    if df.empty:
        return "No mood history yet."
    mood_map = {'😊': 2, '😐': 1, '😔': -1, '😠': -2, '😥': -1.5}
    df['mood_value'] = df['mood'].map(mood_map)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(df['timestamp'], df['mood_value'], marker="o", linestyle="-")
    ax.set_title("Mood History Over Time")
    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Mood Level")
    ax.tick_params(axis='x', rotation=45)
    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format="png")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

if __name__ == "__main__":
    app.run(debug=True)
