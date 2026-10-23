import json
import os
from pathlib import Path

MEMORY_FILE = Path(__file__).resolve().parent / "memory.json"
MAX_MEMORIES = 100


def load_memory():
    if not MEMORY_FILE.exists():
        return []

    try:
        with MEMORY_FILE.open("r", encoding="utf-8") as file:
            memory = json.load(file)

        if not isinstance(memory, list):
            return []

        return [
            item for item in memory
            if isinstance(item, str) and item.strip()
        ][-MAX_MEMORIES:]

    except (json.JSONDecodeError, OSError) as exc:
        print("Could not load memory:", exc)
        return []


def save_memory(memory):
    if not isinstance(memory, list):
        raise TypeError("Memory must be a list.")

    clean_memory = [
        item.strip()
        for item in memory
        if isinstance(item, str) and item.strip()
    ][-MAX_MEMORIES:]

    temp_file = MEMORY_FILE.with_suffix(".tmp")

    try:
        with temp_file.open("w", encoding="utf-8") as file:
            json.dump(
                clean_memory,
                file,
                indent=4,
                ensure_ascii=False,
            )

        os.replace(temp_file, MEMORY_FILE)

    finally:
        if temp_file.exists():
            temp_file.unlink()


def add_memory(text):
    if not isinstance(text, str) or not text.strip():
        return

    memory = load_memory()
    text = text.strip()

    if text not in memory:
        memory.append(text)

    save_memory(memory)


def get_memory():
    return load_memory()