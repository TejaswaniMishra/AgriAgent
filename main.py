from fastapi import FastAPI, Form, Request
from fastapi.staticfiles import StaticFiles
import httpx
import os
import asyncio
from dotenv import load_dotenv

from utils.voice import transcribe_audio, text_to_voice
from utils.whatsapp import send_text, send_voice
from features.intent import detect_intent

load_dotenv()

app = FastAPI()

# Serve temp audio files publicly (Twilio needs a public URL to send audio)
os.makedirs("temp", exist_ok=True)
app.mount("/temp", StaticFiles(directory="temp"), name="temp")

PUBLIC_URL = os.getenv("PUBLIC_URL", "")  # Your ngrok URL goes here

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
    
    # Step 1 — Get text from farmer (voice note or typed)
    transcribed_text = ""
    
    if has_media and MediaContentType0 and "audio" in MediaContentType0:
        # Farmer sent a voice note — download and transcribe
        send_text(farmer_number, "🎤 आपकी आवाज़ सुन रहे हैं...")
        audio_path = await download_media(MediaUrl0, "mp3")
        transcribed_text = transcribe_audio(audio_path)
        
    elif has_media and MediaContentType0 and "image" in MediaContentType0:
        # Farmer sent a photo — go directly to pest detection
        send_text(farmer_number, "📸 फोटो देख रहे हैं...")
        image_path = await download_media(MediaUrl0, "jpg")
        from features.pest import analyze_pest
        reply = analyze_pest(image_path)
        await send_reply(farmer_number, reply)
        return {"status": "ok"}
        
    else:
        # Farmer typed something
        transcribed_text = Body
    
    if not transcribed_text.strip():
        send_text(farmer_number, "माफ करें, आपकी बात समझ नहीं आई। कृपया दोबारा बोलें या लिखें।")
        return {"status": "ok"}
    
    # Step 2 — Detect what farmer wants
    intent = detect_intent(transcribed_text)
    
    # Step 3 — Route to correct feature
    reply = await route_intent(intent, transcribed_text, farmer_number)
    
    # Step 4 — Send reply (voice + text)
    await send_reply(farmer_number, reply)
    
    return {"status": "ok"}


async def route_intent(intent: str, text: str, farmer_number: str) -> str:
    if intent == "mandi":
        from features.mandi import get_mandi_prices
        return get_mandi_prices(text)
    
    elif intent == "scheme":
        from features.schemes import get_schemes
        return get_schemes(text)
    
    elif intent == "advisory":
        from features.advisory import get_advisory
        return get_advisory(text)
    
    else:
        from utils.llm import ask_gemini
        return ask_gemini(f"""
        तुम एक भारतीय कृषि सहायक हो। किसान ने कहा: "{text}"
        सरल हिंदी में मददगार जवाब दो। 2-3 वाक्य से ज्यादा नहीं।
        """)


async def send_reply(farmer_number: str, hindi_text: str):
    """Send both voice and text reply to farmer"""
    audio_path = text_to_voice(hindi_text)
    
    if audio_path and PUBLIC_URL:
        filename = os.path.basename(audio_path)
        audio_url = f"{PUBLIC_URL}/temp/{filename}"
        send_voice(farmer_number, audio_url, hindi_text)
    else:
        # Fallback to text only if audio fails
        send_text(farmer_number, hindi_text)


async def download_media(url: str, ext: str) -> str:
    """Download media file from Twilio"""
    import uuid
    os.makedirs("temp", exist_ok=True)
    filepath = f"temp/{uuid.uuid4().hex}.{ext}"
    
    # Use Twilio credentials for auth
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url, 
            auth=(account_sid, auth_token),
            follow_redirects=True,  # Important — Twilio redirects media URLs
            timeout=30.0
        )
        
        print(f"Media download status: {response.status_code}")
        print(f"Content type: {response.headers.get('content-type')}")
        print(f"Content length: {len(response.content)} bytes")
        
        with open(filepath, "wb") as f:
            f.write(response.content)
    
    return filepath