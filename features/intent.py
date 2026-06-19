from utils.llm import ask_gemini

def detect_intent(text: str) -> str:
    """
    Returns one of: 'mandi', 'pest', 'scheme', 'advisory', 'unknown'
    """
    prompt = f"""
    A farmer said: "{text}"
    
    Based on the text above, respond with exactly ONE word from the options below:
    - mandi (If they are asking about market prices, crop rates, or costs [मंडी भाव, कीमत, रेट])
    - pest (If they are asking about crop diseases, insects, pests, or have sent a photo [फसल की बीमारी, कीड़े, फोटो])
    - scheme (If they are asking about government schemes, subsidies, or financial aid [सरकारी योजना, सब्सिडी, पैसा])
    - advisory (If they are asking about crop care, fertilizers, watering, or weather [फसल की देखभाल, खाद, पानी, मौसम])
    - unknown (If it is anything else)
    
    Respond with ONLY the single classification word. Do not write any other text.
    """
    result = ask_gemini(prompt).strip().lower()
    print(f"INTENT DETECTED: {result}")
    # Safety check
    valid = ["mandi", "pest", "scheme", "advisory"]
    return result if result in valid else "unknown"