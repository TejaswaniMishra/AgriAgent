from fastapi import FastAPI, Form, Request
from fastapi.staticfiles import StaticFiles
import httpx
import os
from dotenv import load_dotenv

from utils.voice import transcribe_audio, text_to_voice
from utils.whatsapp import send_text, send_voice
from features.intent import detect_intent

load_dotenv()

app = FastAPI()

os.makedirs("temp", exist_ok=True)
app.mount("/temp", StaticFiles(directory="temp"), name="temp")

PUBLIC_URL = os.getenv("PUBLIC_URL", "")

# Session memory — farmer number -> language
user_language_cache = {}


LANGUAGE_NAMES = {
    "hi": {"hi": "हिंदी", "en": "Hindi", "kn": "ಹಿಂದಿ", "ta": "இந்தி", "te": "హిందీ", "bn": "হিন্দি", "gu": "હિન્દી", "ml": "ഹിന്ദി"},
    "en": {"hi": "अंग्रेजी", "en": "English", "kn": "ಇಂಗ್ಲಿಷ್", "ta": "ஆங்கிலம்", "te": "ఇంగ్లీష్", "bn": "ইংরেজি", "gu": "અંગ્રેજી", "ml": "ഇംഗ്ലീഷ്"},
    "kn": {"hi": "कन्नड़", "en": "Kannada", "kn": "ಕನ್ನಡ", "ta": "கன்னடம்", "te": "కన్నడ", "bn": "কন্নড়", "gu": "કન્નડ", "ml": "കന്നഡ"},
    "ta": {"hi": "तमिल", "en": "Tamil", "kn": "ತಮಿಳು", "ta": "தமிழ்", "te": "తమిళం", "bn": "তামিল", "gu": "તમિળ", "ml": "തമിഴ്"},
    "te": {"hi": "तेलुगु", "en": "Telugu", "kn": "ತೆಲುಗು", "ta": "తెలుగు", "te": "తెలుగు", "bn": "তেলুগু", "gu": "તેલુગુ", "ml": "തെലുങ്ക്"},
    "bn": {"hi": "बंगाली", "en": "Bengali", "kn": "ಬೆಂಗಾಳಿ", "ta": "வங்காளம்", "te": "బెంగాలీ", "bn": "বাংলা", "gu": "બંગાળી", "ml": "ബംഗാളി"},
    "mr": {"hi": "मराठी", "en": "Marathi", "kn": "ಮರಾಠಿ", "ta": "மராத்தி", "te": "మరాఠీ", "bn": "মারাঠি", "gu": "મરાઠી", "ml": "മറാത്തി"},
    "gu": {"hi": "गुजराती", "en": "Gujarati", "kn": "ಗುಜರಾತಿ", "ta": "குஜராத்தி", "te": "గుజరాతీ", "bn": "গুজরাটি", "gu": "ગુજરાતી", "ml": "ഗുജറാത്തി"},
    "ml": {"hi": "मलयालम", "en": "Malayalam", "kn": "ಮಲಯಾಳಂ", "ta": "மலையாளம்", "te": "మలయాళం", "bn": "মালায়ালাম", "gu": "મલયાલમ", "ml": "മലയാളം"},
    "pa": {"hi": "पंजाबी", "en": "Punjabi", "kn": "ಪಂಜಾಬಿ", "ta": "பஞ்சாபி", "te": "పంజాబీ", "bn": "পাঞ্জাবি", "gu": "પંજાબી", "ml": "പഞ്ചാബി"},
}

def get_confirmation_message(language: str) -> str:
    prompt = f"""
    Generate a short confirmation message in the language with code "{language}".
    The message should say: "Language changed successfully. How can I help you?"
    Add a ✅ emoji at the start.
    Reply with ONLY the message, nothing else.
    """
    try:
        from utils.llm import ask_gemini
        return ask_gemini(prompt)
    except:
        return "✅ Language changed. How can I help you?"

def detect_language_change_command(text: str) -> str | None:
    prompt = f"""
    A farmer said: "{text}"
    Is the farmer requesting to change the response language?
    If YES, reply with ONLY the 2-letter ISO 639-1 code of requested language.
    If NO, reply with ONLY the word: NO
    
    Examples:
    "Give response in Kannada" → kn
    "Hindi mein btao" → hi
    "Tamil mein bolo" → ta
    "aaj gehu ka bhav kya hai" → NO
    "respond in odia" → or
    "ಕನ್ನಡದಲ್ಲಿ ಹೇಳಿ" → kn
    """
    try:
        from utils.llm import ask_gemini
        result = ask_gemini(prompt).strip().lower()
        if result == "no":
            return None
        if len(result) == 2:
            return result
        return None
    except:
        return None

def detect_language_from_text(text: str) -> str:
    prompt = f"""
    What language is this text written in: "{text}"
    Reply with ONLY the 2-letter ISO 639-1 code.
    Examples: Hindi=hi, English=en, Kannada=kn, Tamil=ta,
    Telugu=te, Bengali=bn, Gujarati=gu, Malayalam=ml,
    Punjabi=pa, Odia=or, Marathi=mr
    Bhojpuri/Awadhi → hi
    Reply ONLY the 2-letter code, nothing else.
    """
    try:
        from utils.llm import ask_gemini
        result = ask_gemini(prompt).strip().lower()[:2]
        return result if len(result) == 2 else "hi"
    except:
        return "hi"

@app.get("/")
def root():
    return {"status": "AgriAgent is running 🌾"}


@app.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(default=""),
    MediaUrl0: str = Form(default=None),
    MediaContentType0: str = Form(default=None),
    NumMedia: str = Form(default="0")
):
    farmer_number = From
    has_media = int(NumMedia) > 0

    # Get farmer's last known language, default Hindi
    current_language = user_language_cache.get(farmer_number, "hi")
    transcribed_text = ""
    detected_language = current_language

    if has_media and MediaContentType0 and "audio" in MediaContentType0:
        send_text(farmer_number, "🎤 Listening...")
        audio_path = await download_media(MediaUrl0, "mp3")
        transcribed_text, detected_language = transcribe_audio(audio_path)

        # Check if farmer is requesting language change via voice
        lang_change = detect_language_change_command(transcribed_text)
        if lang_change:
            detected_language = lang_change
            user_language_cache[farmer_number] = detected_language
            lang_names = {
                "hi": "Hindi", "en": "English", "kn": "Kannada",
                "ta": "Tamil", "te": "Telugu", "bn": "Bengali",
                "mr": "Marathi", "gu": "Gujarati", "ml": "Malayalam"
            }
            confirm_msg = get_confirmation_message(detected_language)  
            await send_reply(farmer_number, confirm_msg, detected_language)
            return {"status": "ok"}
        else:
            # Auto update language based on what farmer spoke
            user_language_cache[farmer_number] = detected_language

    elif has_media and MediaContentType0 and "image" in MediaContentType0:
        # Check if caption has language command
        caption = Body.strip() if Body else ""
        
        if caption:
            lang_change = detect_language_change_command(caption)
            if lang_change:
                detected_language = lang_change
                user_language_cache[farmer_number] = detected_language
            else:
                detected_language = user_language_cache.get(farmer_number, "hi")
        else:
            detected_language = user_language_cache.get(farmer_number, "hi")
        
        send_text(farmer_number, "📸 Analyzing your crop photo...")
        image_path = await download_media(MediaUrl0, "jpg")
        from features.pest import analyze_pest
        reply = analyze_pest(image_path, detected_language)
        await send_reply(farmer_number, reply, detected_language)
        return {"status": "ok"}

    else:
        transcribed_text = Body

        # Check if farmer is requesting language change via text
        lang_change = detect_language_change_command(transcribed_text)
        if lang_change:
            detected_language = lang_change
            user_language_cache[farmer_number] = detected_language
            lang_names = {
                "hi": "Hindi", "en": "English", "kn": "Kannada",
                "ta": "Tamil", "te": "Telugu", "bn": "Bengali",
                "mr": "Marathi", "gu": "Gujarati", "ml": "Malayalam"
            }
            confirm_msg = get_confirmation_message(detected_language)
            await send_reply(farmer_number, confirm_msg, detected_language)
            return {"status": "ok"}

        # Auto detect from script
        script_lang = detect_language_from_text(transcribed_text)
        if script_lang != "en":
            detected_language = script_lang
        else:
            detected_language = current_language

        user_language_cache[farmer_number] = detected_language

    if not transcribed_text.strip():
        send_text(farmer_number, "Sorry, I could not understand. Please try again.")
        return {"status": "ok"}

    intent = detect_intent(transcribed_text)
    reply = await route_intent(intent, transcribed_text, detected_language)
    await send_reply(farmer_number, reply, detected_language)

    return {"status": "ok"}


async def route_intent(intent: str, text: str, language: str = "hi") -> str:
    if intent == "mandi":
        from features.mandi import get_mandi_prices
        return get_mandi_prices(text, language)
    elif intent == "scheme":
        from features.schemes import get_schemes
        return get_schemes(text, language)
    elif intent == "advisory":
        from features.advisory import get_advisory
        return get_advisory(text, language)
    else:
        from utils.llm import ask_gemini
        return ask_gemini(
            f'The farmer said: "{text}". Reply helpfully as an agricultural assistant in 2-3 sentences.',
            language=language
        )


async def send_reply(farmer_number: str, text: str, language: str = "hi"):
    audio_path = text_to_voice(text, language)
    if audio_path and PUBLIC_URL:
        filename = os.path.basename(audio_path)
        audio_url = f"{PUBLIC_URL}/temp/{filename}"
        send_voice(farmer_number, audio_url, text)
    else:
        send_text(farmer_number, text)


async def download_media(url: str, ext: str) -> str:
    import uuid
    os.makedirs("temp", exist_ok=True)
    filepath = f"temp/{uuid.uuid4().hex}.{ext}"

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            auth=(account_sid, auth_token),
            follow_redirects=True,
            timeout=30.0
        )
        with open(filepath, "wb") as f:
            f.write(response.content)

    return filepath