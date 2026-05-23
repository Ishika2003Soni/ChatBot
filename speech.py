import streamlit as st
from groq import Groq
from dotenv import load_dotenv
load_dotenv()
import speech_recognition as sr
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import os

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="AI Voice Chatbot",
    page_icon="🎤",
    layout="wide"
)

st.title("🎤 AI Voice Chatbot")
st.write("Speak or type to chat with AI")

# ---------------- API KEY ----------------
# ---------------- API KEY ----------------
import os

api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=api_key)

# ---------------- SETTINGS ----------------
fs = 44100
seconds = 4

APP_COMMANDS = {
    "brave": r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe"
}

# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- BUTTONS ----------------
col1, col2 = st.columns(2)

with col1:
    speak = st.button("🎤 Speak")

with col2:
    clear = st.button("🗑️ Clear Chat")

if clear:
    st.session_state.messages = []
    st.rerun()

# ---------------- VOICE INPUT ----------------
if speak:
    with st.spinner("🎙️ Listening..."):

        recording = sd.rec(
            int(seconds * fs),
            samplerate=fs,
            channels=1
        )

        sd.wait()

        recording = np.int16(recording * 32767)

        write("voice.wav", fs, recording)

    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile("voice.wav") as source:
            audio = recognizer.record(source)

        command = recognizer.recognize_google(audio).lower()

        st.success(f"You said: {command}")

        app_opened = False

        # Open Apps
        for keyword, path in APP_COMMANDS.items():
            if keyword in command:
                os.startfile(path)
                st.success(f"Opening {keyword}")
                app_opened = True
                break

        # Send to AI
        if not app_opened:
            st.session_state.messages.append({
                "role": "user",
                "content": command
            })

            st.rerun()

    except Exception as e:
        st.error(f"Voice recognition failed: {e}")

st.divider()

# ---------------- CHAT HISTORY ----------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ---------------- AI RESPONSE ----------------
if (
    st.session_state.messages
    and st.session_state.messages[-1]["role"] == "user"
):

    with st.chat_message("assistant"):
        with st.spinner("🤖 Thinking..."):

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content":
                        """You are a helpful AI assistant.
                        Answer clearly and simply.
                        If user asks to open apps,
                        guide politely."""
                    },
                    *st.session_state.messages
                ]
            )

            reply = response.choices[0].message.content

            st.write(reply)

            st.session_state.messages.append({
                "role": "assistant",
                "content": reply
            })

# ---------------- TEXT CHAT ----------------
prompt = st.chat_input("Type message here...")

if prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    st.rerun()