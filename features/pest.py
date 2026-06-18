import os
from utils.llm import ask_gemini

def analyze_pest(image_path: str, language: str = "hi") -> str:
    prompt = """
    You are an expert Indian agricultural scientist with 20 years of experience.
    
    Analyze this crop photo carefully and provide:
    
    1. PROBLEM IDENTIFICATION: What disease, pest, or deficiency is visible?
    2. SEVERITY: How serious is it? (Minor / Moderate / Severe)
    3. CAUSE: What causes this problem?
    4. TREATMENT: What specific pesticide/fungicide/fertilizer should be used?
       - Give the generic chemical name
       - Give a common brand name available in Indian markets
       - How much quantity per acre/liter of water
    5. PREVENTION: How to prevent this in future?
    6. URGENCY: Should the farmer act today, this week, or this month?
    
    IMPORTANT RULES:
    - Reply ONLY in simple Hindi (not English)
    - Use simple words a rural farmer can understand
    - Keep total response under 150 words
    - Be specific and practical, not generic
    - If the image is not a crop/plant, politely say so in Hindi
    """
    
    return ask_gemini(prompt, image_path=image_path,language=language)