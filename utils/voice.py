import os
import uuid
from groq import Groq
from gtts import gTTS
import platform
from dotenv import load_dotenv

load_dotenv()

# Groq client — same jo LLM ke liye use kar rahe ho
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

print("✅ Groq Whisper API ready (no local model needed)")


def transcribe_audio(audio_path: str) -> tuple[str, str]:
    """Transcribe audio using Groq Whisper API — zero RAM, large-v3 model"""
    try:
        print(f"Transcribing via Groq: {audio_path}")
        print(f"File size: {os.path.getsize(audio_path)} bytes")

        with open(audio_path, "rb") as audio_file:
            response = groq_client.audio.transcriptions.create(
                file=(os.path.basename(audio_path), audio_file),
                model="whisper-large-v3",
                response_format="verbose_json",  # gives us language detection too
            )

        text = response.text.strip()
        language = response.language if hasattr(response, 'language') else "hi"

        # Groq returns full language name sometimes (e.g. "hindi") — normalize to ISO code
        language_name_to_code = {
            "hindi": "hi", "english": "en", "tamil": "ta", "telugu": "te",
            "bengali": "bn", "marathi": "mr", "gujarati": "gu", "kannada": "kn",
            "malayalam": "ml", "punjabi": "pa", "odia": "or", "urdu": "ur",
        }
        if len(language) > 2:
            language = language_name_to_code.get(language.lower(), "hi")

        print(f"Transcribed: '{text}' | Language: {language}")
        return text, language

    except Exception as e:
        print(f"GROQ TRANSCRIPTION ERROR: {e}")
        return "", "hi"


def text_to_voice(text: str, language: str = "hi") -> str:
    """Convert text to audio using gTTS"""
    try:
        GTTS_SUPPORTED = {
            "hi", "en", "ta", "te", "bn", "mr",
            "gu", "kn", "ml", "pa", "or", "ur"
        }
        lang_code = language if language in GTTS_SUPPORTED else "hi"

        filename = f"reply_{uuid.uuid4().hex}.mp3"
        output_path = f"temp/{filename}"
        os.makedirs("temp", exist_ok=True)

        tts = gTTS(text=text, lang=lang_code, slow=False)
        tts.save(output_path)
        print(f"✅ TTS generated: {output_path}")
        return output_path

    except Exception as e:
        print(f"TTS ERROR: {e}")
        return None