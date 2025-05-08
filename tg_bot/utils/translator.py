import json
import os


LOCALES = {}
def load_locales():
    global LOCALES
    base_path = os.path.join(os.path.dirname(__file__), '..',"")
    file_path = os.path.abspath(os.path.join(base_path, 'lang.json'))

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            LOCALES.update(json.load(f))
    except FileNotFoundError:
        print(f"⚠️ Translation file not found: {file_path}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error in lang.json: {e}")

def get_text(lang: str, key: str) -> str:
    """
    Retrieve translated text from loaded lang.json
    :param lang: 'uz', 'ru', 'en'
    :param key: translation key (e.g., 'start_message')
    """
    data = LOCALES.get(key)
    if not data:
        return f"❓ {key}"  # Key not found at all

    return data.get(lang, data.get("en", f"❓ {key}"))  # Fallback to English
