from utils.llm import ask_gemini

def get_schemes(text: str, language: str = "hi") -> str:
    prompt = f"""
    A farmer asked: "{text}"
    You are a government scheme expert for Indian farmers.
    Tell them about relevant schemes like PM-Kisan, Kisan Credit Card, PMFBY crop insurance.
    Give practical info — eligibility, benefit amount, how to apply.
    Keep it to 4-5 sentences.
    """
    return ask_gemini(prompt, language=language)