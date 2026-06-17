import whisper
from gtts import gTTS
import os
import uuid

# Load whisper model once (do this at startup, not per request)
whisper_model = whisper.load_model("base")  # 'base' is fast and good enough

def transcribe_audio(audio_path: str) -> str:
    """Convert farmer's voice note to text"""
    try:
        result = whisper_model.transcribe(audio_path, language=None)  # auto-detect language
        return result["text"]
    except Exception as e:
        return ""

def text_to_voice(hindi_text: str) -> str:
    """Convert Hindi text response to audio file, return file path"""
    try:
        filename = f"reply_{uuid.uuid4().hex}.mp3"
        output_path = f"temp/{filename}"
        os.makedirs("temp", exist_ok=True)
        
        tts = gTTS(text=hindi_text, lang="hi", slow=False)
        tts.save(output_path)
        return output_path
    except Exception as e:
        return None