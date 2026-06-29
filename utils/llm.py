from google import genai
from google.genai import types
import os
import base64
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# New Gemini client
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Groq only for vision/pest detection
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def ask_gemini(prompt: str, image_path: str = None, language: str = "hi", script: str = "native") -> str:
    
    language_map = {
        "hi": "Hindi", "en": "English", "ta": "Tamil", "te": "Telugu",
        "bn": "Bengali", "mr": "Marathi", "gu": "Gujarati", "kn": "Kannada",
        "ml": "Malayalam", "pa": "Punjabi", "or": "Odia",
    }
    language_name = language_map.get(language, "Hindi")
    
    if script == "roman" and language != "en":
        script_instruction = f"Reply in {language_name}, but write it using ROMAN/ENGLISH alphabet only (Hinglish style, like 'aapka sawaal' not 'आपका सवाल'). Do NOT use native script."
    elif language == "kn":
        script_instruction = "Reply ONLY in Kannada using Kannada script (ಕನ್ನಡ). Do NOT reply in Hindi or English."
    else:
        script_instruction = f"Reply ONLY in {language_name}, using its native script."
    
    full_prompt = prompt + f"\n\nIMPORTANT: {script_instruction} Use only real, correct words."
    
    try:
        if image_path:
            # Groq vision for pest detection
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            ext = image_path.split(".")[-1].lower()
            media_type = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"
            
            response = groq_client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": full_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_data}"}}
                    ]
                }],
                max_tokens=1000
            )
            return response.choices[0].message.content
        else:
            # New Gemini API for text
            response = gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=full_prompt
            )
            return response.text
    
    except Exception as e:
        print(f"LLM ERROR: {e}")
        error_messages = {
            "hi": "माफ करें, अभी जवाब देने में समस्या हो रही है।",
            "en": "Sorry, there was an error. Please try again.",
        }
        return error_messages.get(language, error_messages["hi"])