from groq import Groq
import os
import base64
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def ask_gemini(prompt: str, image_path: str = None, language: str = "hi") -> str:
    
    language_map = {
        "hi": "Hindi",
        "en": "English", 
        "ta": "Tamil",
        "te": "Telugu",
        "bn": "Bengali",
        "mr": "Marathi",
        "gu": "Gujarati",
        "kn": "Kannada",
        "ml": "Malayalam",
        "pa": "Punjabi",
        "or": "Odia",
    }
    
    language_name = language_map.get(language, "Hindi")
    
    # Append language instruction to every prompt
    full_prompt = prompt + f"\n\nIMPORTANT: Reply ONLY in {language_name}. Do not use any other language. Use only real,correct words - do not invent or make up words. If unsure of any term, use simpler evryday word of that language instead "
    
    try:
        if image_path:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            ext = image_path.split(".")[-1].lower()
            media_type = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"
            
            response = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": full_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_data}"}}
                        ]
                    }
                ],
                max_tokens=1000
            )
        else:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": full_prompt}],
                max_tokens=1000
            )
        
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"GROQ ERROR: {e}")
        # Error message in detected language
        error_messages = {
            "hi": "माफ करें, अभी जवाब देने में समस्या हो रही है।",
            "en": "Sorry, there was an error. Please try again.",
            "ta": "மன்னிக்கவும், தற்போது பதில் சொல்ல இயலவில்லை.",
            "te": "క్షమించండి, ప్రస్తుతం సమాధానం ఇవ్వడంలో సమస్య ఉంది.",
        }
        return error_messages.get(language, error_messages["hi"])