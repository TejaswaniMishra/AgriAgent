import json
import os
from utils.llm import ask_gemini

def load_schemes():
    """Load schemes database from JSON file"""
    try:
        schemes_path = os.path.join(os.path.dirname(__file__), "..", "data", "schemes.json")
        with open(schemes_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"SCHEMES LOAD ERROR: {e}")
        return []


def get_schemes(text: str, language: str = "hi", previous_context: str = "") -> str:
    schemes = load_schemes()
    
    if not schemes:
        return ask_gemini(
            f'A farmer asked about government schemes: "{text}". Give general info about PM-Kisan, KCC, PMFBY schemes.',
            language=language
        )
    
    schemes_context = ""
    for s in schemes:
        schemes_context += f"""
Scheme: {s['name']} ({s['name_hindi']})
Benefit: {s['benefit']}
Eligibility: {s['eligibility']}
How to apply: {s['how_to_apply']}
Category: {s['category']}
---
"""
    
    history_note = ""
    if previous_context:
        history_note = f"""
    
    IMPORTANT CONTEXT — Your previous reply to this farmer was:
    "{previous_context}"
    
    If the farmer's new question refers back to this (e.g. "tell me more about the first one", 
    "details about that scheme", "pehli wali"), use the previous reply to understand which 
    scheme they mean, then give full details about that specific scheme from the database above.
    """
    
    prompt = f"""
    You are a government scheme expert for Indian farmers.
    
    Here is a database of government schemes:
    {schemes_context}
    {history_note}
    
    A farmer asked: "{text}"
    
    Based on the database above, identify the most relevant scheme(s) for this farmer's question.
    Explain in simple language:
    1) Name of the scheme
    2) What benefit they get
    3) How to apply (be specific)
    
    Keep it practical and actionable. Maximum 5-6 sentences total.
    """
    
    return ask_gemini(prompt, language=language)