from utils.llm import ask_gemini

def get_advisory(text: str) -> str:
    prompt = f"""
    तुम एक भारतीय कृषि विशेषज्ञ हो।
    किसान ने पूछा: "{text}"
    सरल हिंदी में फसल सलाह दो। 3-4 वाक्य में।
    """
    return ask_gemini(prompt)