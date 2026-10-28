# JAX — Jason AI eXpert 🤖

JAX is a Python-based personal AI assistant and coding buddy. It supports voice conversations, helps review code, and can use project tools to inspect files, run tests, search code, and propose fixes.

JAX uses **NVIDIA Nemotron 3 Nano 30B A3B** through **Nebius Token Factory**. It uses an OpenAI-compatible API, so the model can be called from Python without running the model on your own computer.

## ✨ Features

- 🎙️ Voice input through speech recognition
- 🔊 Spoken responses using Edge TTS
- 🧠 AI conversations powered by NVIDIA Nemotron through Nebius Token Factory
- 💻 Code review and error explanation
- 🧰 Tool-calling workflow for supported coding tasks
- 📂 Project file listing, reading, and searching
- 🧪 Test-running support
- 🛠️ Proposed code fixes, with approval before changes are applied
- 💾 Persistent chat history and a simple memory system
- 🔐 API key loaded from an environment variable
- 🛡️ Project-file safeguards that block access to private files such as `.env`

## 🧰 Tech Stack

- Python 3.10+
- NVIDIA Nemotron 3 Nano 30B A3B
- Nebius Token Factory API
- `openai` Python package for API access
- `python-dotenv`
- `SpeechRecognition`
- `edge-tts`
- `pygame`
- `PyAutoGUI`
- `pyperclip`
- `PyGetWindow`
- `pytest` for tests

## 🚀 Setup

### 1. Clone the repository

```bash
git clone https://github.com/ankur2005-design/JAX-A-coding-buddy-.git
cd JAX-A-coding-buddy-
```

### 2. Create and activate a virtual environment

Windows:

```bash
py -3.10 -m venv .venv
.venv\Scripts\activate
```

If Python 3.10 is not installed, install a compatible Python version first.

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure the API key

Create a file named `.env` in the project root:

```env
NEBIUS_API_KEY=your_nebius_api_key_here
```

Get an API key from Nebius Token Factory. Never commit your real `.env` file or publish your API key.

### 5. Run JAX

Run the main voice assistant:

```bash
python codeview.py
```

You can also run the coding agent in text-only mode, if `jax_agent.py` is included in your checkout:

```bash
python jax_agent.py "List the project files and summarize them."
```

### 6. Run tests

```bash
python -m pytest -q tests
```

## 🧠 Model and Nebius Usage

JAX uses the model ID:

```text
nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B
```

The model is accessed through Nebius Token Factory using its OpenAI-compatible API endpoint:

```text
https://api.tokenfactory.nebius.com/v1/
```

The model handles conversation and selects tools for supported coding tasks. JAX executes those tools in Python and returns their results to the model. This lets the assistant do more than generate text: it can work with supported project files and development tasks.

I used API-based inference rather than deploying or fine-tuning the model on a local GPU. Token Factory made it possible to integrate Nemotron without managing the model-serving infrastructure myself.

## 🔐 Security Notes

- Keep your API key in `.env`.
- Do not commit `.env`, access tokens, or other secrets.
- Keep `.env` in `.gitignore`.
- Runtime files such as chat history and personal memory may contain private information; do not publish them.
- Review proposed code changes before approving them.

## 📁 Project Structure

The exact files may change as the project evolves. The main components include:

```text
JAX-A-coding-buddy-/
├── codeview.py       # Main voice assistant
├── jax_agent.py      # Coding agent and tool-calling workflow
├── memory.py         # Persistent memory helpers
├── prompt.py         # Assistant instructions/personality
├── error_python_code.py/   # A sample default program
├── tests/            # Agents testing
├── requirements.txt  # Python dependencies
├── .env.example      # Example environment configuration
├── .gitignore
├── LICENSE
└── README.md
```

## ⚠️ Notes

- An active internet connection and a valid Nebius Token Factory API key are required for model responses.
- Voice features require a working microphone and audio output.
- Some code-review features may expect a supported editor to be open.
- This project is provided for experimentation. Review AI-generated suggestions and test changes before relying on them.