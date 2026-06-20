# AgriAgent — Project Log

This document tracks what has been built, what changed and why, what's still pending, and what's planned next. Keep this updated as the project evolves — it's the single source of truth for project history.

---

## Project Status: Core MVP Complete (Pre-Hackathon-2 Phase)

**Original context:** Built for HackBharat (Open Innovation / AI Automation & Agentic Systems theme). That specific hackathon was called off before participation. Project continues independently — now has more time to mature before applying to the next hackathon.

---

## 1. Core Concept

**Problem:** Indian farmers lack real-time, trustworthy, accessible information (mandi prices, crop disease, govt schemes, crop advisory) in their own language — leading to income loss every season.

**Solution:** AgriAgent — a WhatsApp-based voice AI agent. Farmer sends voice/text/photo, gets a reply in their own language as both voice note and text. No app download, no literacy barrier.

**Key differentiation decided early on:**
- Not "just ChatGPT" — purpose-built workflow (diagnose → recommend → locate → check subsidy) in one conversation, not generic Q&A
- Lives on WhatsApp, not a new app or a phone helpline (differentiates from govt's Bharat-VISTAAR platform, which is call-based and Hindi/English only)
- Voice-first for low-literacy users

---

## 2. Architecture (Current State)

```
Farmer (WhatsApp) → Twilio Webhook → FastAPI (main.py)
        │
        ├── Voice note → Whisper (transcribe) → language detected
        ├── Photo → Groq Vision → pest analysis directly
        └── Text → language detected from script
        │
        ▼
   Intent detection (mandi / pest / scheme / advisory / unknown)
        │
        ▼
   Routed to feature module → Groq LLM generates response in farmer's language
        │
        ▼
   gTTS → voice note generated → Twilio sends voice + text back
```

**Session memory:** `user_language_cache` (in-memory dict, farmer_number → last used language). Resets if server restarts. Not persistent storage yet.

---

## 3. Features Built (Status: Working)

| # | Feature | File | Status | Notes |
|---|---|---|---|---|
| 1 | WhatsApp voice/text/image pipeline | `main.py` | ✅ Working | Twilio webhook → FastAPI → response |
| 2 | Pest/disease detection from photo | `features/pest.py` | ✅ Working | Groq Vision (Llama 4 Scout), no database needed — pure vision model |
| 3 | Mandi price lookup | `features/mandi.py` | ✅ Working (estimate-based) | Live data.gov.in API confirmed unreliable even with official sample key — see Decision 4.5. Fallback is now the realistic default, with explicit "this is an estimate" disclaimer built into the response |
| 4 | Government scheme finder | `features/schemes.py` | ✅ Working | RAG-style: JSON database (45 schemes — expanded from initial 24) + LLM matches relevant ones to farmer's question |
| 5 | Weather-based crop advisory | `features/advisory.py` | ✅ Working | OpenWeatherMap live weather + crop/season context → LLM advisory |
| 6 | Multi-language auto-detect + switching | `main.py` | ✅ Working | LLM-based detection (not rule-based dictionaries) — detects both language AND script (native vs Roman/Hinglish), matches farmer's input style |
| 7 | Conversational memory (follow-ups) | `main.py` + all feature modules | ✅ Working | `user_conversation_history` cache — farmer can say "tell me more about the first one" and it resolves correctly against the prior response |

---

## 4. Decision Log — Key Choices & Why

### 4.1 LLM-based language detection over rule-based dictionaries
**What changed:** Initially built `LANGUAGE_COMMANDS`, `LANGUAGE_NAMES`, `CONFIRMATION_MESSAGES` as large hardcoded Python dictionaries (manually mapping "kannada"/"ಕನ್ನಡ"/typos → language codes).

**Why it changed:** This doesn't scale — every new language, typo, or phrasing ("kannad mein btao" vs "respond in kannada" vs "ಕನ್ನಡದಲ್ಲಿ ಹೇಳಿ") needed a manual entry. Missed entries silently failed (e.g. Odia wasn't detected until explicitly added).

**Decision:** Replaced with LLM-prompted detection — `detect_language_change_command()`, `detect_language_from_text()`, `get_confirmation_message()` all ask Groq directly. No dictionaries to maintain; any language/phrasing/typo is handled automatically since the LLM understands intent, not just keywords.

**Tradeoff accepted:** 1-2 extra LLM calls per message. Acceptable since Groq is free and fast.

### 4.2 Scheme database stays manual JSON (not LLM-generated)
**Why:** Government scheme details (benefit amounts, eligibility, application URLs) are **factual data**. Letting the LLM "guess" or generate this would risk hallucination — giving a farmer wrong subsidy amounts or wrong application steps is actively harmful, not just inaccurate.

**Rule established:** 
- Factual/accuracy-critical data (scheme details, prices) → must come from a verified database, not LLM generation.
- Flexible/creative tasks (language detection, formatting, conversational responses) → LLM is appropriate.

**Current state:** 24 schemes manually curated and verified (real scheme names, real benefit structures) in `data/schemes.json`. Expanded once from an initial 10 to cover more categories (livestock, fisheries, women farmers, equipment, solar/PM-KUSUM, dairy, FPOs, 2 UP state-specific schemes).

**Known limitation:** A full government dataset (myScheme platform has 4,180+ schemes; a Hugging Face dataset `shrijayan/gov_myscheme` has 723 schemes as PDFs) exists but requires a PDF-extraction pipeline to use — deferred as a Round 2+ task.

### 4.3 Voice transcription quality (Whisper) — known weak point
**Issue found:** Whisper `base` model transcription accuracy on real WhatsApp voice notes (compressed, accented, noisy) has been poor — at least one test produced a completely unrelated transcription ("Boost the billionaire" instead of the farmer's actual Hindi question).

**Root causes addressed:**
- ffmpeg wasn't installed/wasn't on PATH → fixed by installing ffmpeg and adding its `bin` folder to `os.environ["PATH"]` in `voice.py`
- Folder structure issues (venv accidentally containing the whole project) caused multiple cascading errors — fixed by restructuring

**Still unresolved:** Even with ffmpeg working, transcription accuracy on Indian languages/accents remains weak with Whisper `base`.

**Decision:** Do not fix this now. Documented as a planned Round 2 swap to **Sarvam AI** (Indian-government-backed, trained specifically on Indian language audio — see section 6).

### 4.4 Gemini → Groq switch
**Why:** Gemini free tier (`gemini-2.0-flash`, then `gemini-1.5-flash`) hit quota/model-availability errors (429 quota exhausted, then 404 model not found under the new `google-genai` SDK). 

**Decision:** Switched entirely to Groq (`llama-3.1-8b-instant` for text, `meta-llama/llama-4-scout-17b-16e-instruct` for vision). Free tier is generous (14,400 req/day) and has had no quota issues since.

**Note:** Function is still named `ask_gemini()` in `utils/llm.py` for historical/compatibility reasons — it actually calls Groq. Consider renaming to `ask_llm()` for clarity in a future cleanup pass.

### 4.5 Mandi prices — live API confirmed unreliable, fallback finalized as the working solution
**Issue:** `api.data.gov.in` mandi price endpoint consistently times out (`ReadTimeoutError`) regardless of correct API key/filters.

**Investigation (root cause confirmed):** Verified the resource ID in use (`9ef84268-d588-465a-a308-a864a43d0070`) is correct by cross-checking against the official data.gov.in API docs page. Tested directly with data.gov.in's own official **sample/demo API key** (not just our own key) using a generous 15-second timeout — still timed out (`ReadTimeoutError` on `api.data.gov.in:443`). This confirms the issue is the government server's reliability itself, not our API key, resource ID, or request format. This is a known, widely-reported issue with this particular government API.

**Decision:** Stopped pursuing a fix to the live endpoint. `fetch_from_data_gov()` is kept in the code as-is (harmless — if the government API ever stabilizes, it will automatically start working again with zero code changes needed), but the **fallback path is now the realistic default**, not a backup.

The fallback prompt was deliberately restructured to:
1. Explicitly tell the farmer this is an **estimated** range, not live/confirmed data — never presented as if it were today's real price
2. Give a realistic seasonal price range with 1-2 context factors (arrivals, demand)
3. Point to agmarknet.gov.in / local mandi samiti / mandi gate for exact verification before a selling decision
4. Stay warm and practical in tone rather than reading like a corporate disclaimer

**Why this is the right call, not a compromise:** Showing stale/cached "live" data and labeling it as current would be actively misleading for a farmer making a real selling decision — worse than an honest, clearly-labeled estimate. This also gives a clean, honest story for the pitch: *"Real-time government API integration attempted and verified non-viable (confirmed via testing with data.gov.in's own sample key); AI-estimated pricing with clear disclaimers used as the interim solution, with live integration to resume if/when the government API stabilizes."*

**Considered alternatives (not pursued):**
- Static Kaggle dataset (`ishankat/daily-wholesale-commodity-prices-india-mandis`) — rejected because it would present non-live data as if current, same honesty problem as the original issue, just with better-looking but still stale numbers
- Third-party sites scraping data.gov.in (mandipulse.com, kisanbridge.com) — not pursued; adds a fragile dependency on an undocumented third party for a problem we'd still inherit

---

## 5. Bugs Fixed (Chronological, for reference)

1. **Folder structure error** — entire project (`features/`, `utils/`, `main.py`, `.env`) accidentally created inside `venv/` folder instead of alongside it. Fixed by moving all files out; later required a full venv rebuild (`rmdir /s /q venv` → recreate) after `pyvenv.cfg` got corrupted/misplaced.
2. **ngrok "endpoint already online"** — stale ngrok process running in background. Fixed with `taskkill /F /IM ngrok.exe` before restarting.
3. **Gemini 429 quota exhausted** → tried `gemini-1.5-flash` → 404 not found → ultimately abandoned Gemini for Groq (see Decision 4.4).
4. **Twilio image download `invalid image data`** — `download_media()` wasn't passing Twilio auth credentials correctly and wasn't following redirects. Fixed by adding `auth=(account_sid, auth_token)` and `follow_redirects=True`.
5. **Image caption language command ignored** — when a farmer sent a photo with a caption like "give response in malayalam," the code only checked `user_language_cache`, never the caption text (`Body`). Fixed by checking caption for a language-change command before falling back to cached language.
6. **Confirmation message always in English** — language-change confirmation ("✅ Language changed to...") was hardcoded in English regardless of target language. Fixed by generating the confirmation via LLM in the target language.
7. **Odia not detected** — both keyword-matching and Unicode-range detection missed Odia ("ଓଡ଼ିଆ", script range `0x0B00–0x0B7F`). Root issue: manual rule-based detection inherently misses entries. Permanently fixed by moving to LLM-based detection (Decision 4.1).
8. **Voice transcription totally failing** — root cause was `ffmpeg` not installed / not on system PATH, so the wav-conversion step in `transcribe_audio()` silently failed and Whisper got no usable audio. Fixed by installing ffmpeg and explicitly adding its `bin` directory to `PATH` in `voice.py`.
9. **Twilio sandbox 50 messages/day limit hit** — free sandbox cap. No permanent fix yet; documented as a constraint, not a bug. Resets ~5:30 AM IST (UTC midnight).

---

## 6. Explicitly Deferred (Not Forgotten — Planned for Later)

These were identified as real product gaps during development but consciously deprioritized to keep momentum. Listed here so they aren't lost:

| Item | What's the gap | Planned fix |
|---|---|---|
| Voice transcription accuracy | Whisper `base` model weak on Indian accents/languages — upgraded to `small` model (better, but still not India-specific) | Switch to **Sarvam AI** (STT model "Saaras v3" — trained on 1M+ hours of real Indian audio, supports 22 languages, code-mixing/Hinglish). Paused for now — free credits (₹100) reserved, will revisit. |
| Voice output naturalness | gTTS sounds robotic, limited language support | Switch to **Sarvam AI Bulbul V3** TTS — 35+ natural voices, native Hinglish code-switching. Paused alongside STT swap above. |
| Scheme database size | 45 schemes (curated manually, expanded from initial 24) | Build proper extraction pipeline from myScheme government dataset (4,180+ schemes) or a structured Q&A dataset (e.g. `bharatschemes-v1`) if/when time allows |
| Deployment | Currently only runs locally via ngrok — not a permanent, shareable link | Deploy to Railway/Render for a permanent public URL |
| Twilio message limit | Free WhatsApp Sandbox caps at 50 messages/day, repeatedly interrupts testing | Create a fresh Twilio account, or move to WhatsApp Business API for real demo/production use |
| Persistent storage | `user_language_cache` and `user_conversation_history` are in-memory dicts — wiped on every server restart | Move to SQLite (lightweight) or Postgres for persistence across restarts |
| Robustness/error handling | No rate limiting, minimal logging, no handling for oversized files or concurrent request edge cases | Add structured logging, basic rate limiting, and graceful handling for malformed/oversized media before any real-world use |

---

## 7. Tech Stack (Current)

| Layer | Technology | Why |
|---|---|---|
| Backend | FastAPI (Python) | Async support, good for webhook-driven I/O |
| Messaging | Twilio WhatsApp Sandbox | Free for development, real WhatsApp delivery |
| LLM (text) | Groq — `llama-3.1-8b-instant` | Free, fast, generous quota (14,400 req/day) |
| LLM (vision) | Groq — `meta-llama/llama-4-scout-17b-16e-instruct` | Free, handles image+text prompts well |
| Speech-to-text | OpenAI Whisper (`base`, local) | Free, offline, but weak on Indian accents (known limitation) |
| Text-to-speech | gTTS | Free, simple, but limited voice naturalness |
| Weather | OpenWeatherMap | Free tier, district-level current weather |
| Scheme data | Static JSON | Accuracy-critical, manually curated (see Decision 4.2) |
| Tunneling (dev only) | ngrok | Free, makes localhost reachable by Twilio webhook |
| Version control | Git + GitHub | Public repo for hackathon submission |

---

## 8. How to Use This Log Going Forward

When you make a meaningful change, add an entry under the relevant section:
- **New feature working?** → Add to Section 3 table.
- **Changed approach mid-stream?** → Add to Section 4 (Decision Log) with *what changed* and *why*.
- **Fixed a confusing bug?** → Add to Section 5, one line, root cause + fix.
- **Identified a gap but not fixing now?** → Add to Section 6 so it doesn't get lost.

This keeps the project narratable — useful for your own understanding, for a teammate joining later, and for writing pitch/PPT content without having to reconstruct the journey from memory.