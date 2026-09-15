from google import genai
import edge_tts
import asyncio
import os
import re
import speech_recognition as sr
from dotenv import load_dotenv
load_dotenv()
import pygame
import json
from ss import ss
from prompt import prompt
from memory import add_memory, get_memory

api_key = os.getenv("GOOGLE_API")

chat_history = []

if os.path.exists("chat_history.json"):
    with open("chat_history.json", "r", encoding="utf-8") as file:
        chat_history = json.load(file)

async def speak(response):
    voice = "en-IN-PrabhatNeural"
    tts = edge_tts.Communicate(response , voice , rate = "+17%")

    await tts.save("answer.mp3")

    pygame.mixer.init()
    pygame.mixer.music.load("answer.mp3")
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)

    pygame.mixer.music.unload()
    os.remove("answer.mp3")


def listen():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("speak...")
        listen = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(listen)

    except sr.UnknownValueError:
        print("didn't inderstand")
        return ""

    except sr.RequestError:
        print("service unavailable")
        return ""

    return text

def clean_text(text):

    text = re.sub(r"[\*\_#\`\~]", "", text)
    text = re.sub(r"\n+", ". ", text)
    text = re.sub(r"\s{2,}", " ", text)

    return text.strip()

client = genai.Client(api_key = api_key)

prompt = prompt()

def llm(text):

    global chat_history

    history = "\n".join(chat_history)
    mem = "\n".join(get_memory())

    content = [
        prompt,

        f"""
        RELEVANT CHAT HISTORY:
        {history}
        """,

        f"""
        RELEVANT LONG-TERM MEMORY:
        {mem}
        """,

        f"""
        CURRENT USER MESSAGE:
        {text}
        """
    ]

    if "check" in text or "wrong" in text:       
        screenshot , code = ss()
        content.append(screenshot)
        content.append(f"""
        CODE FROM USER'S SCREEN:
        {code}
        """)
        chat_history.append(f"User: {text}")
        chat_history.append(f"Code:\n{code}")

    response = client.models.generate_content(
        model = "gemini-3.5-flash-lite",
        contents = content
    )

    chat_history.append(f"User: {text}")
    chat_history.append(f"Jax: {response.text}")

    chat_history = chat_history[-10:]

    with open("chat_history.json", "w", encoding="utf-8") as file:
        json.dump(chat_history, file, indent=4)

    response = clean_text(response.text)

    print("Jax : ", response)
    return response

while True:
    text = listen()

    if text == "":
        continue

    if "bye" in text or ("talk" in text and "later" in text) or ("see" in text and "you" in text):
        text = "see you have a great day"
        asyncio.run(speak(text))
        with open("chat_history.json", "w", encoding="utf-8") as file:
            json.dump([], file, indent=4)
        break

    if "memory" in text or "remember" in text:
        add_memory(text)
        asyncio.run(speak(
            "Successfully Remembered"
        ))
        continue

    response = llm(text)

    asyncio.run(speak(response))

    print(chat_history)