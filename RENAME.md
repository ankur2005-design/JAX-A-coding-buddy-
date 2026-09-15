# JAX — Jason AI eXpert 🤖

JAX (Jason AI eXpert) is a Python-based personal AI assistant designed to provide natural voice conversations, analyze code, understand screenshots, and remember important information across conversations.

The project combines Google's Gemini API with speech recognition, text-to-speech, screenshot capture, and a simple persistent memory system.

## ✨ Features

- 🎙️ Voice input using speech recognition
- 🔊 Natural voice responses using Edge TTS
- 🧠 Gemini-powered AI conversations
- 💻 Code error detection and explanation
- 📸 Screenshot capture for code analysis
- 🧾 Persistent chat history
- 🧠 Persistent memory system
- 💬 Context-aware conversations
- ⚡ Fully Python-based
- 🔐 API key stored using environment variables

## 🛠️ Tech Stack

- Python 3.10
- Google Gemini API
- `google-genai`
- Edge TTS
- Pygame
- SpeechRecognition
- PyAutoGUI
- Pyperclip
- python-dotenv

## 📁 Project Structure

```text
JAX/
│
├── codeview.py          # Main JAX program
├── prompt.py            # AI personality and behavior
├── memory.py            # Persistent memory system
├── ss.py                # Screenshot and code capture
│
├── memory.json          # Stored memories
├── chat_history.json    # Conversation history
├── .env                 # API key (not uploaded)
├── .gitignore
└── README.md