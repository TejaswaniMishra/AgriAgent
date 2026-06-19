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


def get_schemes(text: str, language: str = "hi") -> str:
    schemes = load_schemes()
    
    if not schemes:
        return ask_gemini(
            f'A farmer asked about government schemes: "{text}". Give general info about PM-Kisan, KCC, PMFBY schemes.',
            language=language
        )
    
    # Format all schemes as context for the LLM
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
    
    prompt = f"""
    You are a government scheme expert for Indian farmers.
    
    Here is a database of government schemes:
    {schemes_context}
    
    A farmer asked: "{text}"
    
    Based on the database above, identify the 1-3 MOST RELEVANT schemes for this farmer's question.
    Explain in simple language:
    1) Name of the scheme
    2) What benefit they get
    3) How to apply (be specific)
    
    Keep it practical and actionable. Maximum 5-6 sentences total.
    If the farmer's question is general (like "what schemes are there"), give a brief overview of 2-3 most useful schemes.
    """
    
    return ask_gemini(prompt, language=language)