from utils.llm import ask_gemini

def get_advisory(text: str, language: str = "hi") -> str:
    prompt = f"""
    A farmer asked: "{text}"
    You are an Indian agricultural expert.
    Give practical crop advisory — irrigation, fertilizer, pest prevention, harvesting tips.
    Be specific and practical for Indian farming conditions.
    Keep it to 4-5 sentences.
    """
    return ask_gemini(prompt, language=language)