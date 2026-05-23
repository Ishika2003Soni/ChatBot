import streamlit as st
from groq import Groq
from dotenv import load_dotenv
import speech_recognition as sr
import numpy as np
import os

# ---------------- LOAD ENV ----------------
load_dotenv()

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="AI Voice Chatbot",
    page_icon="🎤",
    layout="wide"
)

st.title("🎤 AI Voice Chatbot")
st.caption("Speak or type to chat with AI")

# ---------------- API KEY ----------------
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("❌ GROQ_API_KEY not found.")
    st.info("Create a .env file and add:\n\nGROQ_API_KEY=your_api_key")
    st.stop()

client = Groq(api_key=api_key)

# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

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

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("⚙ Settings")
    st.write("Voice Duration:", seconds, "seconds")

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# ---------------- BUTTONS ----------------
col1, col2 = st.columns(2)

with col1:
    speak = st.button("🎤 Speak")

with col2:
    st.info("💡 Voice works locally only")

# ---------------- VOICE INPUT ----------------
if speak:

    try:
        import sounddevice as sd
        from scipy.io.wavfile import write

        with st.spinner("🎙️ Listening... Speak now"):

            recording = sd.rec(
                int(seconds * fs),
                samplerate=fs,
                channels=1
            )

            sd.wait()

            recording = np.int16(recording * 32767)

            write("voice.wav", fs, recording)

        recognizer = sr.Recognizer()

        with sr.AudioFile("voice.wav") as source:
            audio = recognizer.record(source)

        command = recognizer.recognize_google(audio).lower()

        st.success(f"🗣️ You said: {command}")

        app_opened = False

        # OPEN APPS
        for keyword, path in APP_COMMANDS.items():

            if keyword in command:

                try:
                    os.startfile(path)
                    st.success(f"🚀 Opening {keyword.title()}")
                    app_opened = True
                    break

                except Exception:
                    st.error(f"Couldn't open {keyword}")

        # SEND TO AI
        if not app_opened:
            st.session_state.messages.append({
                "role": "user",
                "content": command
            })

            st.rerun()

    except ModuleNotFoundError:
        st.error(
            "❌ Voice feature doesn't work on Streamlit Cloud.\n"
            "Use text chat or run locally."
        )

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

    already_replied = (
        len(st.session_state.messages) > 1
        and st.session_state.messages[-2]["role"] == "assistant"
    )

    if not already_replied:

        with st.chat_message("assistant"):
            with st.spinner("🤖 Thinking..."):

                try:
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "system",
                                "content":
                                """
                                You are a helpful AI assistant.
                                Answer clearly and simply.
                                If the user asks to open apps,
                                politely guide them.
                                """
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

                except Exception as e:
                    st.error(f"AI Error: {e}")

# ---------------- TEXT CHAT ----------------
prompt = st.chat_input("Type your message here...")

if prompt:

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    st.rerun()