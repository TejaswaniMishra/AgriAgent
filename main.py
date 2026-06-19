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
user_conversation_history = {}

def ask_llm(prompt: str) -> str:
    from utils.llm import ask_gemini
    return ask_gemini(prompt)


def get_system_message(message_type: str, language: str) -> str:
    """Generate any system message in target language using LLM"""
    messages = {
        "listening": "Tell the user you are listening to their voice message. Very short, 1 sentence.",
        "sorry": "Tell the user you could not understand and to please try again. Very short, 1 sentence.",
        "analyzing": "Tell the user you are analyzing their crop photo. Very short, 1 sentence.",
    }
    prompt = f"""
    Generate this message in the language with ISO code "{language}":
    "{messages.get(message_type, message_type)}"
    Add a relevant emoji at the start.
    Reply with ONLY the message, nothing else.
    """
    try:
        return ask_llm(prompt)
    except:
        defaults = {
            "listening": "🎤 Listening...",
            "sorry": "Sorry, please try again.",
            "analyzing": "📸 Analyzing photo..."
        }
        return defaults.get(message_type, "Please wait...")


def get_confirmation_message(language: str) -> str:
    """Generate language change confirmation in target language"""
    prompt = f"""
    Generate a short confirmation message in the language with ISO code "{language}".
    The message should say: "Language changed successfully. How can I help you?"
    Add a ✅ emoji at the start.
    Reply with ONLY the message, nothing else.
    """
    try:
        return ask_llm(prompt)
    except:
        return "✅ Language changed. How can I help you?"


def detect_language_change_command(text: str) -> str | None:
    """Use LLM to detect if farmer wants to change language"""
    prompt = f"""
    A farmer said exactly this: "{text}"
    
    Is this farmer EXPLICITLY asking to change/switch the response language?
    Only say YES if they clearly request a language change, like:
    "Give response in Kannada", "Hindi mein btao", "switch to Tamil", "reply in English"
    
    Say NO for everything else, including:
    - Greetings like "hi", "hello", "namaste"
    - Questions about crops, schemes, weather, prices
    - Any normal farming-related question
    - Short messages that aren't clearly a language request
    
    If YES, reply with ONLY the 2-letter ISO 639-1 code of the requested language (e.g. kn, hi, ta, en).
    If NO, reply with ONLY the word: NO
    
    Examples:
    "Give response in Kannada" → kn
    "Hindi mein btao" → hi
    "hi" → NO
    "hello" → NO
    "mujhe sinchai ki yojana chahiye" → NO
    "tell me irrigation schemes for farmers" → NO
    "aaj gehu ka bhav kya hai" → NO
    "respond in odia" → or
    """
    try:
        result = ask_llm(prompt).strip().lower()
        # Clean — remove any punctuation/extra text
        result = result.replace(".", "").replace(",", "").strip()
        
        if result == "no" or "no" in result[:3]:
            return None
        
        # Extract just first 2 alphabetic characters
        result = "".join(c for c in result if c.isalpha())[:2]
        
        valid_codes = {"hi", "en", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa", "or", "ur"}
        return result if result in valid_codes else None
    except:
        return None
    
def detect_language_from_text(text: str) -> tuple[str, str]:
    """Use LLM to detect language of typed text. Returns (language_code, script) - script is 'native' or 'roman' """
    prompt = f"""
    Analyze this text: "{text}"
    
    Important: Judge by the SCRIPT and GRAMMAR structure, not individual proper nouns or place names.
    For example, "What are wheat prices in Gorakhpur mandi today" is ENGLISH (en) — 
    even though "mandi" and "Gorakhpur" are Hindi/Indian words, the sentence structure 
    and majority of words are English.
    
    1) What language is it? Reply with 2-letter ISO 639-1 code.
    2) What script/alphabet is it written in? 
       - "native" if written in the language's own script (Devanagari, Tamil script, etc.)
       - "roman" if written in English/Latin alphabet (like "mujhe sichai ki yojna chahiye")
    
    Examples:
    "What are wheat prices in Gorakhpur mandi today" → LANG: en, SCRIPT: roman
    "aaj gehu ka bhav kya hai" → LANG: hi, SCRIPT: roman
    "गेहूं का भाव क्या है" → LANG: hi, SCRIPT: native
    "tell me farming schemes" → LANG: en, SCRIPT: roman
    "mujhe sichai ki yojna chahiye" → LANG: hi, SCRIPT: roman
    "naa sahayam kavali" → LANG: te, SCRIPT: roman
    Bhojpuri/Awadhi/Maithili → LANG: hi
    
    Reply EXACTLY in this format, nothing else:
    LANG: hi
    SCRIPT: roman
    """
    try:
        result = ask_llm(prompt).strip().lower()
        lang = "hi"
        script = "native"
        for line in result.split("\n"):
            if "lang:" in line:
                lang_part = line.split("lang:")[-1].strip()
                lang = "".join(c for c in lang_part if c.isalpha())[:2]
            if "script:" in line:
                script = "roman" if "roman" in line else "native"
        valid_codes = {"hi", "en", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa", "or", "ur"}
        lang = lang if lang in valid_codes else "hi"
        return lang, script
    except:
        return "hi", "native"


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

    current_language = user_language_cache.get(farmer_number, "hi")
    transcribed_text = ""
    detected_script = "native"
    detected_language = current_language

    # --- VOICE NOTE ---
    if has_media and MediaContentType0 and "audio" in MediaContentType0:
        send_text(farmer_number, get_system_message("listening", current_language))
        audio_path = await download_media(MediaUrl0, "mp3")
        transcribed_text, detected_language = transcribe_audio(audio_path)

        lang_change = detect_language_change_command(transcribed_text)
        if lang_change:
            detected_language = lang_change
            user_language_cache[farmer_number] = detected_language
            confirm_msg = get_confirmation_message(detected_language)
            await send_reply(farmer_number, confirm_msg, detected_language)
            return {"status": "ok"}
        else:
            user_language_cache[farmer_number] = detected_language

    # --- IMAGE ---
    elif has_media and MediaContentType0 and "image" in MediaContentType0:
        caption = Body.strip() if Body else ""

        if caption:
            lang_change = detect_language_change_command(caption)
            if lang_change:
                detected_language = lang_change
                user_language_cache[farmer_number] = detected_language
            else:
                detected_language = current_language
        else:
            detected_language = current_language

        send_text(farmer_number, get_system_message("analyzing", detected_language))
        image_path = await download_media(MediaUrl0, "jpg")
        from features.pest import analyze_pest
        reply = analyze_pest(image_path, detected_language,detected_script)
        await send_reply(farmer_number, reply, detected_language)
        return {"status": "ok"}

    # --- TEXT MESSAGE ---
    else:
        transcribed_text = Body

        lang_change = detect_language_change_command(transcribed_text)
        if lang_change:
            detected_language = lang_change
            user_language_cache[farmer_number] = detected_language
            confirm_msg = get_confirmation_message(detected_language)
            await send_reply(farmer_number, confirm_msg, detected_language)
            return {"status": "ok"}

        detected_language, detected_script = detect_language_from_text(transcribed_text)
        user_language_cache[farmer_number] = detected_language

    # --- EMPTY MESSAGE CHECK ---
    if not transcribed_text.strip():
        send_text(farmer_number, get_system_message("sorry", current_language))
        return {"status": "ok"}

    # --- ROUTE TO FEATURE ---
    # --- ROUTE TO FEATURE ---
    intent = detect_intent(transcribed_text)
    reply = await route_intent(intent, transcribed_text, detected_language, farmer_number, detected_script)
    await send_reply(farmer_number, reply, detected_language)
    return {"status": "ok"}


async def route_intent(intent: str, text: str, language: str = "hi", farmer_number: str = "", script: str = "native") -> str:
    previous_context = user_conversation_history.get(farmer_number, "")
    
    if intent == "mandi":
        from features.mandi import get_mandi_prices
        return get_mandi_prices(text, language, previous_context, script)
    elif intent == "scheme":
        from features.schemes import get_schemes
        return get_schemes(text, language, previous_context, script)
    elif intent == "advisory":
        from features.advisory import get_advisory
        return get_advisory(text, language, previous_context, script)
    else:
        from utils.llm import ask_gemini
        prompt = f'The farmer said: "{text}".'
        if previous_context:
            prompt = f'Previous conversation: "{previous_context}"\n\nFarmer now said: "{text}". If this refers to the previous conversation, use that context.'
        return ask_gemini(prompt + " Reply helpfully as an Indian agricultural assistant in 2-3 sentences.", language=language, script=script)


async def send_reply(farmer_number: str, text: str, language: str = "hi"):
    """Send both voice note and text to farmer"""
    # Save this response as context for potential follow-up questions
    user_conversation_history[farmer_number] = text
    
    audio_path = text_to_voice(text, language)
    if audio_path and PUBLIC_URL:
        filename = os.path.basename(audio_path)
        audio_url = f"{PUBLIC_URL}/temp/{filename}"
        print(f"Sending voice: {audio_url}")
        send_voice(farmer_number, audio_url, text)
    else:
        print("Audio failed — sending text only")
        send_text(farmer_number, text)

async def download_media(url: str, ext: str) -> str:
    """Download media from Twilio"""
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
        print(f"Media download: {response.status_code} | {len(response.content)} bytes")
        with open(filepath, "wb") as f:
            f.write(response.content)

    return filepath