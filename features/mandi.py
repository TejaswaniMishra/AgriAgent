import requests
import os
from utils.llm import ask_gemini
from dotenv import load_dotenv

load_dotenv()

def get_mandi_prices(text: str) -> str:
    # Step 1 — Extract commodity and location
    extract_prompt = f"""
    किसान ने कहा: "{text}"
    इस वाक्य से सिर्फ दो चीजें निकालो:
    1) फसल का नाम English में (जैसे Wheat, Rice, Onion, Potato, Sugarcane)
    2) जिले का नाम English में (जैसे Gorakhpur, Lucknow, Varanasi)
    
    सिर्फ इस format में जवाब दो, कुछ और मत लिखो:
    COMMODITY: Wheat
    DISTRICT: Gorakhpur
    """
    extracted = ask_gemini(extract_prompt)
    
    commodity = "Wheat"
    district = "Gorakhpur"
    
    for line in extracted.split("\n"):
        if "COMMODITY:" in line:
            commodity = line.split("COMMODITY:")[-1].strip()
        if "DISTRICT:" in line:
            district = line.split("DISTRICT:")[-1].strip()

    # Step 2 — Try fetching live prices
    prices = fetch_from_data_gov(commodity, district)
    
    # Step 3 — Format response
    if prices:
        price_text = "\n".join(prices)
        response_prompt = f"""
        नीचे {district} की मंडियों में {commodity} के आज के भाव हैं:
        {price_text}
        
        इसे एक किसान को सरल हिंदी में बताओ।
        मंडी का नाम, न्यूनतम भाव, अधिकतम भाव और मॉडल भाव बताओ।
        अंत में एक सलाह दो।
        """
        return ask_gemini(response_prompt)
    else:
        # Fallback — LLM gives general price range based on training data
        fallback_prompt = f"""
        किसान ने {district}, उत्तर प्रदेश में {commodity} का मंडी भाव पूछा है।
        
        तुम एक अनुभवी कृषि विशेषज्ञ हो। इस फसल के बारे में बताओ:
        1) इस समय UP में इस फसल का अनुमानित भाव क्या है (per quintal)
        2) भाव किन बातों पर निर्भर करता है
        3) सही भाव जानने के लिए agmarknet.gov.in या नजदीकी मंडी से संपर्क करें
        
        सरल हिंदी में, 4-5 वाक्य में जवाब दो।
        """
        return ask_gemini(fallback_prompt)


def fetch_from_data_gov(commodity: str, district: str) -> list:
    """Try data.gov.in API with short timeout"""
    try:
        api_key = os.getenv("DATAGOV_API_KEY")
        url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
        params = {
            "api-key": api_key,
            "format": "json",
            "limit": 5,
            "filters[commodity]": commodity,
            "filters[district]": district
        }
        response = requests.get(url, params=params, timeout=5)  # short timeout
        data = response.json()
        records = data.get("records", [])
        
        if not records:
            return []
        
        prices = []
        for r in records:
            line = (
                f"मंडी: {r.get('market', 'N/A')} | "
                f"न्यूनतम: ₹{r.get('min_price', 'N/A')} | "
                f"अधिकतम: ₹{r.get('max_price', 'N/A')} | "
                f"मॉडल: ₹{r.get('modal_price', 'N/A')} प्रति क्विंटल"
            )
            prices.append(line)
        return prices

    except Exception as e:
        print(f"DATA.GOV API ERROR: {e}")
        return []