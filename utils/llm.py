from groq import Groq
import os
import base64
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def ask_gemini(prompt: str, image_path: str = None) -> str:
    try:
        if image_path:
            # Read and encode image
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            # Detect image type
            ext = image_path.split(".")[-1].lower()
            if ext == "jpg" or ext == "jpeg":
                media_type = "image/jpeg"
            elif ext == "png":
                media_type = "image/png"
            else:
                media_type = "image/jpeg"  # default
            
            response = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
        else:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000
            )
        
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"GROQ ERROR: {e}")
        return "माफ करें, अभी जवाब देने में समस्या हो रही है। कृपया दोबारा कोशिश करें।"