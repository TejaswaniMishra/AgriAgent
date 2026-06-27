import google.generativeai as genai
from groq import Groq
import os
import base64
from dotenv import load_dotenv

load_dotenv()

# Gemini for text
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# Groq for image/vision only
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
    
    full_prompt = prompt + f"\n\nIMPORTANT: {script_instruction} Use only real correct words."
    
    try:
        if image_path:
            # Use Groq Vision for images
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
            # Use Gemini for text
            response = gemini_model.generate_content(full_prompt)
            return response.text
    
    except Exception as e:
        print(f"LLM ERROR: {e}")
        error_messages = {
            "hi": "माफ करें, अभी जवाब देने में समस्या हो रही है।",
            "en": "Sorry, there was an error. Please try again.",
            "ta": "மன்னிக்கவும், தற்போது பதில் சொல்ல இயலவில்லை.",
            "te": "క్షమించండి, ప్రస్తుతం సమాధానం ఇవ్వడంలో సమస్య ఉంది.",
        }
        return error_messages.get(language, error_messages["hi"])