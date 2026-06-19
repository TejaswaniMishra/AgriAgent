from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
TWILIO_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

def send_text(to: str, message: str):
    """Send text message to farmer"""
    try:
        client.messages.create(
            from_=TWILIO_NUMBER,
            to=to,
            body=message
        )
    except Exception as e:
        print(f"Text send error: {e}")

def send_voice(to: str, audio_url: str, message: str):
    try:
        print(f"Sending voice to {to}")
        print(f"Audio URL: {audio_url}")
        client.messages.create(
            from_=TWILIO_NUMBER,
            to=to,
            media_url=[audio_url],
            body=""
        )
        send_text(to, message)
        print("✅ Voice sent successfully")
    except Exception as e:
        print(f"VOICE SEND ERROR: {e}")