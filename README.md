# 🌾 AgriAgent

**A WhatsApp-based voice AI agent that gives Indian farmers instant access to mandi prices, crop disease diagnosis, government schemes, and crop advisory — in their own language, for free, with no app download required.**

Built for HackBharat — Theme: AI Automation & Agentic Systems

---

## Problem Statement

India has 140+ million small and marginal farmers who make critical decisions every day — when to sell their crop, what to spray on a diseased plant, which government scheme to apply for. But their information sources are broken:

- **Mandi prices** — farmers rely on local middlemen (aadatiyas) who have an incentive to quote low prices
- **Pest & disease** — farmers ask the local pesticide shop owner, who often upsells the most expensive product
- **Government schemes** — most farmers don't know relevant schemes exist or miss application deadlines
- **Crop advisory** — farmers follow inherited practices regardless of current soil, weather, or season

This information asymmetry costs the average small farmer thousands of rupees every season — in wrong selling decisions, wrong pesticide use, and missed subsidies. Existing solutions either require literacy in English, app downloads, or long call-center wait times — none of which fit how a rural farmer actually communicates.

## Solution

AgriAgent works entirely on **WhatsApp** — an app 500+ million Indians already use daily. A farmer sends a voice note, a text message, or a photo, and gets a spoken + written reply in their own language. No new app to install, no English required, no literacy barrier.

### Why WhatsApp, not just "ask an AI chatbot"

- **Hyper-local, real-time data** — live-style mandi price lookups and government scheme matching, not generic chatbot guesses
- **Zero learning curve** — farmers already use WhatsApp; there's nothing new to learn
- **Truly agentic** — a single conversation can move from "what pest is this" to "what should I spray" to "is there a subsidy for that" without the farmer repeating context
- **Voice-first** — every response comes back as both a voice note and text, so literacy is never a barrier

---

## Features

### 1. 🎙️ Voice + Text Input in Multiple Indian Languages
Farmers can speak or type in Hindi, English, or several regional languages. The agent auto-detects the language used and replies in the same language — both as text and as a voice note. Farmers can also explicitly switch languages mid-conversation (e.g. "reply in Kannada").

### 2. 📸 AI-Powered Pest & Disease Diagnosis
Farmers send a photo of an affected crop. The agent identifies the likely disease/pest, severity, recommended treatment (generic + common Indian brand names), dosage, and urgency — entirely from a photo, no typing required.

### 3. 💰 Mandi Price Assistant
Farmers ask for today's price of a crop in their district. The agent extracts the crop and location from natural conversation and responds with price context and selling guidance.

### 4. 🏛️ Government Scheme Finder
A curated database of 24+ central and state government schemes (PM-Kisan, KCC, PMFBY, PM-KUSUM, livestock and fisheries schemes, women-farmer schemes, UP state schemes, and more). The agent matches a farmer's question to the most relevant schemes and explains benefits and how to apply in simple language.

### 5. 🌦️ Weather-Aware Crop Advisory
Combines live weather data for the farmer's district with crop-stage knowledge to give specific, actionable advice — irrigation timing, fertilizer dosage, pest risk from current humidity/rain, and harvesting windows.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Messaging interface | Twilio WhatsApp API |
| LLM (reasoning, advisory, scheme matching) | Groq (Llama 3.1) |
| Vision (pest detection) | Groq Vision (Llama 4 Scout) |
| Speech-to-text | OpenAI Whisper |
| Text-to-speech | Google Text-to-Speech (gTTS) |
| Weather data | OpenWeatherMap API |
| Scheme database | Curated JSON dataset |
| Tunneling (dev) | ngrok |

---

## Architecture

```
Farmer sends voice/text/photo on WhatsApp
            │
            ▼
   Twilio Webhook → FastAPI Backend
            │
   ┌────────┼────────────────────┐
   ▼        ▼                    ▼
 Voice    Image                Text
 note    (photo)              message
   │        │                    │
Whisper   Groq Vision      Language detect
(speech     │                    │
 to text)   │                    │
   │        ▼                    ▼
   └──> Intent Detection (mandi / pest / scheme / advisory)
            │
            ▼
   Route to relevant feature module
            │
            ▼
   Groq LLM generates response in farmer's language
            │
            ▼
   Google TTS converts to voice note
            │
            ▼
   Twilio sends BOTH voice note + text back to farmer
```

---

## Project Structure

```
agriagent/
├── main.py                  # FastAPI app + WhatsApp webhook + routing
├── requirements.txt
├── .env.example              # Environment variable template
│
├── features/
│   ├── mandi.py              # Mandi price lookup
│   ├── pest.py                # Pest/disease detection from photo
│   ├── schemes.py            # Government scheme finder (RAG-style)
│   ├── advisory.py           # Weather-based crop advisory
│   └── intent.py             # Intent classification
│
├── utils/
│   ├── voice.py               # Whisper transcription + gTTS voice generation
│   ├── whatsapp.py           # Twilio send (text + voice)
│   └── llm.py                 # Groq LLM wrapper
│
└── data/
    └── schemes.json          # Government schemes database (24+ schemes)
```

---

## Setup & Run Locally

### Prerequisites
- Python 3.10+
- A Twilio account (free WhatsApp Sandbox)
- API keys: Groq, OpenWeatherMap

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/AgriAgent.git
cd AgriAgent/agriagent

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

### Environment Variables

Copy `.env.example` to `.env` and fill in your keys:

```env
GROQ_API_KEY=your_key_here
TWILIO_ACCOUNT_SID=your_key_here
TWILIO_AUTH_TOKEN=your_key_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
DATAGOV_API_KEY=your_key_here
OPENWEATHER_API_KEY=your_key_here
PUBLIC_URL=your_ngrok_or_deployed_url
```

### Run

```bash
uvicorn main:app --reload --port 8000
```

In a separate terminal, expose the server publicly (for local dev):
```bash
ngrok http 8000
```

Set the resulting URL + `/webhook` as your Twilio WhatsApp Sandbox webhook under **Messaging → Try it out → WhatsApp Sandbox Settings**.

---

## Team

| Name | Role |
|---|---|
| Tejaswani Mishra | Full-stack Development, AI/ML Integration, Product Design |

---

## Roadmap (Post Round 1)

- Integrate **Sarvam AI** (India-optimized speech-to-text and text-to-speech) for significantly better regional language and Hinglish accuracy
- Live mandi price integration via data.gov.in / Agmarknet (currently uses AI-estimated price ranges as a reliable fallback)
- Expand scheme database from 24 to the full myScheme government dataset (4,180+ schemes)
- Conversational memory for natural follow-up questions ("tell me more about the first one")
- WhatsApp Business API for production-scale messaging (beyond sandbox limits)

---

## Why This Matters

AgriAgent isn't trying to be a smarter chatbot — it's trying to remove every barrier between a farmer and the information they're entitled to: no app to download, no English to type, no literacy required, no helpline number to remember. It meets farmers exactly where they already are.