from utils.llm import ask_gemini

def analyze_pest(image_path: str) -> str:
    prompt = """
    तुम एक भारतीय कृषि विशेषज्ञ हो।
    इस फसल की फोटो में बीमारी या कीड़े पहचानो।
    सरल हिंदी में बताओ:
    1) क्या समस्या है
    2) क्या दवाई डालें
    3) कितना जरूरी है
    """
    return ask_gemini(prompt, image_path=image_path)