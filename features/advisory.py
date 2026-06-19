import requests
import os
from datetime import datetime
from utils.llm import ask_gemini
from dotenv import load_dotenv

load_dotenv()

def get_advisory(text: str, language: str = "hi") -> str:
    # Step 1 — Extract crop and location from farmer's message
    extract_prompt = f"""
    The farmer said: "{text}"
    Extract only two things:
    1) Crop name in English (like Wheat, Rice, Sugarcane, Potato) — if not mentioned, say "general"
    2) District/city name in English (like Gorakhpur, Lucknow) — if not mentioned, say "Lucknow"
    
    Reply ONLY in this exact format, nothing else:
    CROP: Wheat
    DISTRICT: Gorakhpur
    """
    extracted = ask_gemini(extract_prompt)
    
    crop = "general"
    district = "Lucknow"
    
    for line in extracted.split("\n"):
        if "CROP:" in line:
            crop = line.split("CROP:")[-1].strip()
        if "DISTRICT:" in line:
            district = line.split("DISTRICT:")[-1].strip()
    
    # Step 2 — Get current weather
    weather_info = get_weather(district)
    
    # Step 3 — Get current month for seasonal context
    current_month = datetime.now().strftime("%B")
    
    # Step 4 — Generate advisory using LLM with weather + crop + season context
    prompt = f"""
    You are an experienced Indian agricultural advisor.
    
    Farmer's question: "{text}"
    Crop: {crop}
    Location: {district}, India
    Current month: {current_month}
    Current weather: {weather_info}
    
    Give practical crop advisory considering:
    1) Current weather conditions (irrigation needed or not, disease risk from humidity/rain)
    2) This time of year — what stage the crop would typically be at
    3) Specific actionable advice — fertilizer, irrigation, pest watch, harvesting timing
    
    Keep it practical and specific to Indian farming conditions. 4-5 sentences maximum.
    """
    
    return ask_gemini(prompt, language=language)


def get_weather(district: str) -> str:
    """Fetch current weather for a district using OpenWeatherMap"""
    try:
        api_key = os.getenv("OPENWEATHER_API_KEY")
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": f"{district},IN",
            "appid": api_key,
            "units": "metric"
        }
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        if response.status_code == 200:
            temp = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            condition = data["weather"][0]["description"]
            return f"Temperature: {temp}°C, Humidity: {humidity}%, Condition: {condition}"
        else:
            return "Weather data unavailable"
    
    except Exception as e:
        print(f"WEATHER API ERROR: {e}")
        return "Weather data unavailable"