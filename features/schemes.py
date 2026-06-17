from utils.llm import ask_gemini

def get_schemes(text: str) -> str:
    prompt = f"""
    तुम एक सरकारी योजना सहायक हो।
    किसान ने पूछा: "{text}"
    PM-Kisan, Kisan Credit Card, PMFBY जैसी योजनाओं के बारे में
    सरल हिंदी में बताओ। 3-4 वाक्य में।
    """
    return ask_gemini(prompt)