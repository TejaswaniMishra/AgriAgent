import whisper
from gtts import gTTS
import os
import uuid

# Load whisper model once (do this at startup, not per request)
whisper_model = whisper.load_model("base")  # 'base' is fast and good enough

def transcribe_audio(audio_path: str) -> tuple[str, str]:
    """Returns (transcribed_text, detected_language)"""
    try:
        result = whisper_model.transcribe(audio_path, language=None)
        text = result["text"]
        language = result.get("language", "hi")  # default Hindi
        return text, language
    except Exception as e:
        return "", "hi"

def text_to_voice(text: str, language: str = "hi") -> str:
    """Convert text to audio in detected language"""
    try:
        # gTTS language codes
        gtts_lang_map = {
            "hi": "hi",
            "en": "en",
            "ta": "ta",
            "te": "te",
            "bn": "bn",
            "mr": "mr",
            "gu": "gu",
            "kn": "kn",
            "ml": "ml",
            "pa": "pa",
            "or": "or",
        }
        lang_code = gtts_lang_map.get(language, "hi")
        
        filename = f"reply_{uuid.uuid4().hex}.mp3"
        output_path = f"temp/{filename}"
        os.makedirs("temp", exist_ok=True)
        
        tts = gTTS(text=text, lang=lang_code, slow=False)
        tts.save(output_path)
        return output_path
    except Exception as e:
        print(f"TTS ERROR: {e}")
        return None