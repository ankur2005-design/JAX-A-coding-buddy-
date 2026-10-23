import asyncio
import json
import logging
import os
import re
import subprocess
import time
import pygetwindow as gw

import edge_tts
import pyautogui
import pyperclip
import speech_recognition as sr
from dotenv import load_dotenv
from openai import OpenAI

from prompt import prompt
from memory import add_memory, get_memory
from jax_agent import run_agent, apply_fix, analyze_code

logging.disable(logging.WARNING)
load_dotenv()

# CONFIGURATION

MODEL = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"

if not os.getenv("NEBIUS_API_KEY"):
    raise RuntimeError(
        "NEBIUS_API_KEY is missing. Check your .env file."
    )

client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=os.getenv("NEBIUS_API_KEY"),
)

SYSTEM_PROMPT = prompt()

CHAT_HISTORY_FILE = "chat_history.json"
ERRORS_FILE = "errors.json"

# Keep your existing memory.py and its storage unchanged.
chat_history = []

if os.path.exists(CHAT_HISTORY_FILE):
    try:
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as file:
            loaded_history = json.load(file)

        if isinstance(loaded_history, list):
            chat_history = loaded_history[-10:]

    except (json.JSONDecodeError, OSError):
        chat_history = []

# CHAT HISTORY

def save_chat_history():
    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(
            chat_history[-10:],
            file,
            indent=4,
            ensure_ascii=False,
        )


# TEXT-TO-SPEECH

async def speak(response):
    response = clean_text(response)

    if not response:
        response = "I couldn't generate a response."

    voice = "en-US-RogerNeural"

    communicate = edge_tts.Communicate(
        response,
        voice,
        rate="+15%",
    )

    process = subprocess.Popen(
        ["mpv", "--no-video", "--really-quiet", "--", "fd://0"],
        stdin=subprocess.PIPE,
    )

    try:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio" and process.stdin:
                process.stdin.write(chunk["data"])
                process.stdin.flush()

    finally:
        if process.stdin:
            process.stdin.close()

        process.wait()


# SPEECH RECOGNITION

def listen():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Speak...")
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        audio = recognizer.listen(source)

    try:
        return recognizer.recognize_google(audio)

    except sr.UnknownValueError:
        print("Didn't understand.")
        return ""

    except sr.RequestError:
        print("Speech recognition service unavailable.")
        return ""


# CLEAN TEXT FOR CONSOLE AND VOICE

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F000-\U0001FAFF"   # emoticons, symbols, pictographs, flags
    "\U00002600-\U000027BF"   # misc symbols and dingbats
    "\U00002B00-\U00002BFF"   # stars, arrows
    "\U0000231A-\U000023FF"   # watch, hourglass, media symbols
    "\U0000200D\U0000FE0F\U000020E3"  # joiners and variation selectors
    "]+",
    flags=re.UNICODE,
)


def clean_text(text):
    if not isinstance(text, str):
        return ""

    # Remove emojis so the voice never reads their names aloud.
    text = EMOJI_PATTERN.sub("", text)

    # Remove fenced code blocks from spoken responses.
    text = re.sub(
        r"```.*?```",
        " code omitted ",
        text,
        flags=re.DOTALL,
    )

    text = re.sub(r"[*_#`~]", "", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# COPY CODE FROM THE ACTIVE EDITOR

def copy_editor_code():
    print("JAX is checking the active window...")

    try:
        active_window = gw.getActiveWindow()

        if active_window is None:
            return None

        title = active_window.title.lower()

        if "visual studio code" not in title:
            print("Please activate the VS Code window first.")
            return None

        print("Click inside the code editor, not the terminal.")

        # Remember the clipboard so it can be restored if copying fails.
        previous_clipboard = pyperclip.paste()

        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.2)
        pyautogui.hotkey("ctrl", "c")
        time.sleep(0.5)

        code = pyperclip.paste()

        if not isinstance(code, str) or not code.strip():
            pyperclip.copy(previous_clipboard)
            return None

        return code

    except Exception as exc:
        print("Could not copy code:", exc)
        return None


# PENDING CORRECTIONS

def load_proposed_corrections():
    try:
        with open(ERRORS_FILE, "r", encoding="utf-8") as file:
            corrections = json.load(file)

        if not isinstance(corrections, list):
            return []

        valid_corrections = []

        for correction in corrections:
            if not isinstance(correction, dict):
                continue

            old_code = (
                correction.get("old")
                or correction.get("old_code")
            )

            new_code = (
                correction.get("new")
                or correction.get("new_code")
            )

            if (
                isinstance(old_code, str)
                and isinstance(new_code, str)
                and old_code
                and new_code
            ):
                valid_corrections.append({
                    "line": correction.get("line"),
                    "path": correction.get("path"),
                    "old": old_code,
                    "new": new_code,
                })

        return valid_corrections

    except FileNotFoundError:
        return []

    except (json.JSONDecodeError, OSError) as exc:
        print("Could not read proposed corrections:", exc)
        return []

pending_fix = bool(load_proposed_corrections())
awaiting_fix_approval = False

def save_proposed_corrections(corrections):
    with open(ERRORS_FILE, "w", encoding="utf-8") as file:
        json.dump(
            corrections,
            file,
            indent=4,
            ensure_ascii=False,
        )


# ANALYZE CODE WITH THE AGENT

def check_code(text):
    global pending_fix, awaiting_fix_approval

    code = copy_editor_code()

    if not code:
        pending_fix = False
        awaiting_fix_approval = False
        return (
            "I couldn't copy any code. "
            "Click inside the code editor and try again."
        )

    # Remove stale corrections before starting a new review.
    save_proposed_corrections([])

    print("JAX agent is analyzing your code...")

    try:
        answer = run_agent(
            task=(
                "Review the supplied code for genuine errors. "
                "Use analyze_code when appropriate. "
                "Do not invent errors. "
                "For each genuine correction, call propose_fix "
                "with the exact original code and corrected code. "
                "If you know which project file the code belongs to, "
                "pass its path to propose_fix so it is verified. "
                "Do not call apply_fix. Do not modify source files. "
                "Explain the real problem clearly. "
                "If no genuine errors exist, say so."
            ),
            code=code,
        )

    except Exception as exc:
        pending_fix = False
        awaiting_fix_approval = False
        print("Agent error:", repr(exc))
        return "I couldn't finish analyzing the code. Check the console for details."

    corrections = load_proposed_corrections()

    pending_fix = bool(corrections)
    awaiting_fix_approval = False

    if corrections:
        print(
            f"JAX saved {len(corrections)} proposed correction(s)."
        )

    if not isinstance(answer, str) or not answer.strip():
        if corrections:
            answer = (
                f"I found {len(corrections)} proposed correction(s) "
                "and saved them."
            )
        else:
            # Safety net: never leave the user with silence.
            answer = (
                "The AI gave no explanation, so here is the basic check. "
                + analyze_code(code, "snippet.py")
            )

    if len(corrections) == 1:
        correction = corrections[0]
        old_preview = correction["old"].strip()
        new_preview = correction["new"].strip()
        line = correction.get("line")
        line_text = f" on line {line}" if line else ""
        answer = (
            f"{answer.rstrip()} "
            f"My proposed change{line_text} is to replace "
            f"{old_preview} with {new_preview}. "
            "Do you want me to apply this exact change? "
            "Say yes to apply it, or no to cancel."
        )
        awaiting_fix_approval = True
    elif len(corrections) > 1:
        answer = (
            f"{answer.rstrip()} I saved {len(corrections)} proposed changes, "
            "but I won't apply multiple changes automatically. "
            "We need to select one change first."
        )
        awaiting_fix_approval = False

    return answer


# APPLY A PROPOSED CORRECTION

def approve_and_apply_fix():
    global pending_fix, awaiting_fix_approval

    corrections = load_proposed_corrections()

    if not corrections:
        pending_fix = False
        awaiting_fix_approval = False
        return "There is no saved correction to apply. Check your code first."

    if len(corrections) > 1:
        return (
            f"I have {len(corrections)} proposed corrections. "
            "I won't apply multiple changes automatically. "
            "We need to select one correction first."
        )

    correction = corrections[0]

    old_code = correction["old"]
    new_code = correction["new"]

    print("\nProposed correction:")
    print("OLD:", repr(old_code))
    print("NEW:", repr(new_code))

    # Voice mode must not block waiting for terminal input.
    file_path = correction.get("path")

    if not file_path:
        return (
            "I don't have a verified project file path for this proposal. "
            "The source file was not changed. Ask me to review the project "
            "file directly so I can save a proposal with its exact path."
        )

    if not os.path.isfile(file_path):
        return (
            "That file does not exist. "
            "Your proposed correction is still saved."
        )

    print("\nJAX will now ask for explicit approval.")
    print("Review the old and new code carefully.")

    try:
        result = apply_fix(
            path=file_path,
            old_code=old_code,
            new_code=new_code,
            approved=True,
        )

        print("Apply-fix result:", result)

        if result.startswith("Approved change applied"):
            save_proposed_corrections([])
            pending_fix = False
            awaiting_fix_approval = False
            return "Done. I applied the approved fix, checked the code, and saved a backup."

        return (
            "The fix was not applied. "
            "Check the console for the reason. "
            "Your saved proposal has been kept."
        )

    except Exception as exc:
        print("Apply-fix error:", repr(exc))
        return (
            "I couldn't apply the correction. "
            "Your saved proposal has been kept. "
            "Check the console for the error."
        )


# INTENT ROUTING (understands free-form speech)

# Used only if the model call fails or gives an unclear answer.
FALLBACK_REVIEW_HINTS = (
    "code", "bug", "error", "wrong", "problem", "issue", "debug",
    "review", "check", "broken", "not working", "doesn't work",
    "crash", "happening", "this file", "this function", "screen",
)


def wants_code_review(text):
    """
    Decide whether the user is asking about the code in their editor.
    Nemotron judges the meaning, so any phrasing works:
    "what's wrong", "why is this crashing", "what is happening here"...
    """
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You route voice commands for a coding assistant that "
                        "can look at the code open in the user's editor. "
                        "Answer with exactly one word.\n"
                        "REVIEW: the user is asking about their code or "
                        "screen: errors, bugs, what is wrong, what is "
                        "happening, why something fails or crashes, what a "
                        "piece of code does, or asking to check, debug or "
                        "improve it.\n"
                        "CHAT: anything else (casual talk, general "
                        "questions, jokes, weather, memory, greetings)."
                    ),
                },
                {"role": "user", "content": text},
            ],
            max_tokens=200,
            temperature=0,
        )

        verdict = (response.choices[0].message.content or "").upper()

        if "REVIEW" in verdict:
            return True
        if "CHAT" in verdict:
            return False

    except Exception as exc:
        print("Intent routing failed, using keyword fallback:", repr(exc))

    lower_text = text.lower()
    return any(hint in lower_text for hint in FALLBACK_REVIEW_HINTS)


# MAIN LLM ROUTER

def llm(text):
    global chat_history, pending_fix, awaiting_fix_approval

    lower_text = text.lower().strip()

    # Only treat yes/no as approval when JAX has just asked about a specific fix.
    yes_words = re.search(
        r"\b(yes|yeah|yep|yup|approved|approve|go ahead|do it|"
        r"apply it|fix it|sure|okay|ok)\b",
        lower_text,
    )
    no_words = re.search(
        r"\b(no|nope|cancel|stop|don't|dont|do not|leave it|"
        r"leave it alone)\b",
        lower_text,
    )

    if awaiting_fix_approval and no_words:
        awaiting_fix_approval = False
        answer = "Okay, I won't change the file. The proposed correction is still saved."
    elif awaiting_fix_approval and yes_words:
        answer = approve_and_apply_fix()
    elif awaiting_fix_approval:
        answer = (
            "I haven't changed anything yet. "
            "Please say yes to apply the proposed change, or no to cancel."
        )
    else:
        if wants_code_review(text):
            answer = check_code(text)

        else:
            history = "\n".join(chat_history)
            long_term_memory = "\n".join(get_memory())

            content = f"""
{SYSTEM_PROMPT}

RELEVANT CHAT HISTORY:
{history}

RELEVANT LONG-TERM MEMORY:
{long_term_memory}

CURRENT USER MESSAGE:
{text}
"""

            try:
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {
                            "role": "user",
                            "content": content,
                        }
                    ],
                    max_tokens=700,
                    temperature=0.7,
                )

                answer = response.choices[0].message.content or ""

                if not answer.strip():
                    answer = (
                        "I couldn't generate a response. "
                        "Please try again."
                    )

            except Exception as exc:
                print("Nebius API error:", repr(exc))
                answer = (
                    "I couldn't contact the AI model. "
                    "Check your connection and API configuration."
                )

    chat_history.append(f"User: {text}")
    chat_history.append(f"JAX: {answer}")
    chat_history = chat_history[-10:]

    try:
        save_chat_history()
    except OSError as exc:
        print("Could not save chat history:", exc)

    print("User:", text)
    print("JAX:", answer)

    return clean_text(answer)


# VOICE ASSISTANT LOOP

def is_goodbye(text):
    text = text.lower().strip()

    goodbye_words = [
        "bye",
        "goodbye",
        "shut down jax",
        "shutdown jax",
        "exit jax",
        "close jax",
        "stop jax",
        "talk to you later",
        "see you",
        "good night",
    ]

    return any(word in text for word in goodbye_words)


def main():
    while True:
        try:
            text = listen()

            if not text:
                continue

            lower_text = text.lower().strip()

            if is_goodbye(text):
                goodbye = "See you, have a great day!"
                print("JAX:", goodbye)
                asyncio.run(speak(goodbye))

                # Keep the original behaviour of clearing
                # conversational history when saying goodbye.
                chat_history.clear()
                save_chat_history()
                break

            if (
                "remember" in lower_text
                or "remember this" in lower_text
            ):
                add_memory(text)
                answer = "I'll save that to memory."
                print("JAX:", answer)
                asyncio.run(speak(answer))
                continue

            answer = llm(text)
            asyncio.run(speak(answer))

        except KeyboardInterrupt:
            print("\nJAX stopped.")
            break

        except Exception as exc:
            print("Unexpected JAX error:", repr(exc))

            try:
                asyncio.run(
                    speak(
                        "Something went wrong. "
                        "Check the console for the error."
                    )
                )
            except Exception:
                pass


if __name__ == "__main__":
    main()