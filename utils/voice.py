import whisper
from gtts import gTTS
import os
import uuid

# Fix ffmpeg PATH — sirf bin folder ka path, file ka nahi
os.environ["PATH"] += r";C:\Users\tejas\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-essentials_build\bin"

# Load model with error handling
try:
    whisper_model = whisper.load_model("base")
    print("✅ Whisper model loaded successfully")
except Exception as e:
    print(f"❌ Whisper load failed: {e}")
    whisper_model = None

GTTS_SUPPORTED = {
    "hi", "en", "ta", "te", "bn", "mr",
    "gu", "kn", "ml", "pa", "ur", "or"
}

def transcribe_audio(audio_path: str) -> tuple[str, str]:
    try:
        if whisper_model is None:
            print("Whisper model not loaded")
            return "", "hi"

        print(f"Transcribing: {audio_path}")
        print(f"File size: {os.path.getsize(audio_path)} bytes")

        wav_path = audio_path.replace(".mp3", ".wav")
        result = os.system(f'ffmpeg -i "{audio_path}" -ar 16000 -ac 1 "{wav_path}" -y -loglevel quiet')
        print(f"FFmpeg conversion result: {result}")

        transcribe_path = wav_path if os.path.exists(wav_path) else audio_path
        print(f"Transcribing from: {transcribe_path}")

        whisper_result = whisper_model.transcribe(transcribe_path, language=None)
        text = whisper_result["text"].strip()
        language = whisper_result.get("language", "hi")

        print(f"Transcribed: '{text}' | Language: {language}")
        return text, language

    except Exception as e:
        print(f"WHISPER ERROR: {e}")
        return "", "hi"


def text_to_voice(text: str, language: str = "hi") -> str:
    try:
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