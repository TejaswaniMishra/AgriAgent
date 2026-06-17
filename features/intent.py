from utils.llm import ask_gemini

def detect_intent(text: str) -> str:
    """
    Returns one of: 'mandi', 'pest', 'scheme', 'advisory', 'unknown'
    """
    prompt = f"""
    एक किसान ने यह कहा: "{text}"
    
    नीचे दिए गए विकल्पों में से केवल एक शब्द में जवाब दो:
    - mandi (अगर वो मंडी भाव, कीमत, रेट पूछ रहे हैं)
    - pest (अगर वो फसल की बीमारी, कीड़े, या फोटो भेजी है)
    - scheme (अगर वो सरकारी योजना, सब्सिडी, पैसा पूछ रहे हैं)
    - advisory (अगर वो फसल की देखभाल, खाद, पानी, मौसम पूछ रहे हैं)
    - unknown (अगर कुछ और है)
    
    सिर्फ एक शब्द लिखो, कुछ और नहीं।
    """
    result = ask_gemini(prompt).strip().lower()
    
    # Safety check
    valid = ["mandi", "pest", "scheme", "advisory"]
    return result if result in valid else "unknown"