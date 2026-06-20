import requests
import os
from utils.llm import ask_gemini
from dotenv import load_dotenv

load_dotenv()

def get_mandi_prices(text: str, language: str = "hi", previous_context: str = "", script: str = "native") -> str:
    # Step 1 — Extract commodity and location
    extract_prompt = f"""
    The farmer said: "{text}"
    Extract only two things:
    1) Crop name in English (like Wheat, Rice, Onion, Potato)
    2) District name in English (like Gorakhpur, Lucknow, Varanasi)
    
    Reply ONLY in this exact format, nothing else:
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

    # Step 2 — Try fetching live prices (kept as primary path in case data.gov.in becomes reliable later)
    prices = fetch_from_data_gov(commodity, district)
    history_note = ""
    if previous_context:
        history_note = f"""
    
    IMPORTANT CONTEXT — Your previous reply to this farmer was:
    "{previous_context}"
    
    If the farmer's new question refers back to this (e.g. "what about tomorrow", 
    "and for rice","and for any other crop", "ispe aur batao"), use the previous reply to understand the context.
    """
    
    # Step 3 — Format response
    if prices:
        price_text = "\n".join(prices)
        response_prompt = f"""
        These are today's LIVE mandi prices for {commodity} in {district}:
        {price_text}
        {history_note}
        
        Tell this to a farmer in simple language.
        Mention market name, min price, max price, modal price per quintal.
        End with one advice on whether to sell now or wait.
        """
        return ask_gemini(response_prompt, language=language, script=script)
    else:
        # Fallback — government live API unavailable, give a clearly-labeled estimate instead
        fallback_prompt = f"""
        A farmer asked about {commodity} mandi price in {district}, Uttar Pradesh.
        {history_note}
        
        You are an experienced agricultural market expert. The live government price feed 
        is temporarily unavailable, so give a helpful estimate instead.
        
        Structure your answer like this:
        1) Clearly state this is an ESTIMATED price range (not live data) — be upfront about this, 
           do not present it as confirmed today's price.
        2) Give a realistic price range per quintal for {commodity} in {district}/Uttar Pradesh 
           based on typical seasonal patterns.
        3) Mention 1-2 factors that affect the price right now (arrivals, season, demand).
        4) Tell them to verify the exact price by checking agmarknet.gov.in, calling the local 
           mandi samiti, or asking at the mandi gate before making a selling decision.
        
        Keep it warm and practical, like a knowledgeable person helping a friend — not a disclaimer-heavy 
        corporate message. 4-5 sentences total.
        """
        return ask_gemini(fallback_prompt, language=language, script=script)

def fetch_from_data_gov(commodity: str, district: str) -> list:
    """Try data.gov.in API with short timeout. 
    Note: This government API has proven unreliable (consistent timeouts even with the 
    official sample key) — kept as a primary attempt in case it stabilizes, but the 
    fallback path is the realistic default for now."""
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
        response = requests.get(url, params=params, timeout=5)
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