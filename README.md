# Roxstar AI Voice Room Assistant

A real-time Voice AI prototype built for LiveKit rooms featuring two bilingual AI participants: **Roxstar AI Dost** (Male) and **Roxstar AI Sathi** (Female). The agents understand multi-user spoken and typed conversations, handle code-mixed Hindi/Hinglish and English, and reply with natural conversational pacing and Indian accents.

---

## 1. Architecture Overview

### Pipeline Architecture

```text
[User Mic Audio / Text Chat]
│
▼
[LiveKit SFU / WebRTC Transport]
│
▼
[Silero VAD] ──> Detects speech boundaries and turn completion
│
▼
[Deepgram STT (Nova-2)] ──> Real-time transcription (English + Hindi/Hinglish)
│
▼
[Bot Turn & Routing Guard] ──> Addressee detection (Dost vs Sathi turn gating)
│
▼
[Groq LLM (Llama 3.1 8B Instant)] ──> Conversational Hinglish persona response
│
▼
[TTS Engine]
├─ Dost: ElevenLabs (eleven_multilingual_v2 - Adam) / Deepgram Aura-2
└─ Sathi: OpenAI TTS (tts-1 - Nova, Devanagari phonetics) / ElevenLabs (Rachel)
│
▼
[LiveKit Audio Publication / Text Track Reply]
```

### Sequence Flow

```text
User                      LiveKit Room Worker (Dost/Sathi)            Providers (STT/LLM/TTS)
 │                               │                                           │
 ├─ Speaks / Sends Text ────────>│                                           │
 │                               ├─ Audio / Data Packet ────────────────────>│
 │                               │                                           ├─ Deepgram STT
 │                               │<── Transcript text ───────────────────────┤
 │                               ├─ Route check (addressed?)                 │
 │                               ├─ Prompt + Room Context ──────────────────>│
 │                               │                                           ├─ Groq LLM
 │                               │<── Hinglish completion ───────────────────┤
 │                               ├─ Stream text ────────────────────────────>│
 │                               │                                           ├─ TTS Provider
 │                               │<── Audio frames ──────────────────────────┤
 │                               │                                           │
 │<── Hears / Sees Reply ────────┤                                           │
```

---

## 2. Technology Stack & Design Decisions

## Technology Stack & Design Decisions

| Component | Selected Technology | Rationale & Alternatives Evaluated |
|---|---|---|
| Transport | LiveKit Cloud / Agents SDK (Python) | WebRTC rooms, participant lifecycle events, and per-bot agent workers with explicit `agent_name`. |
| VAD | Silero VAD | Detects speech boundaries for turn handling. |
| STT | Deepgram (plugin default model) | Streaming transcription that worked from the start with no issues. |
| LLM | Groq, `openai/gpt-oss-120b` (via the OpenAI-compatible endpoint) | Fast inference for low turn latency; Hinglish persona set by prompt engineering. Gemini and `llama-3.3-70b-versatile` (deprecated) were tried and dropped. |
| TTS (Dost) | ElevenLabs (`eleven_multilingual_v2`) | Multilingual model that handles Hinglish text. Fallback: Deepgram Aura-2 (`orion`). |
| TTS (Sathi) | Cartesia (`sonic-3`, `language="hi"`) | Hindi-capable female voice with a free tier. Earlier attempts: Deepgram Aura-2 (`thalia`) and OpenAI `tts-1` (English accent), Sarvam `bulbul:v3` (blocked by a 403), ElevenLabs (key loading problem). |
| Turn routing | Name-based, in code | Each bot skips its turn when the other is named. See Known Limitations. |

---

## 3. Bot Personas & Language Policy

Both bots are instructed to avoid pure/bookish Hindi (*"Dhwanigrahak sakriya karein"*) and instead speak everyday conversational Hinglish (*"Mic unmute karo"*):

* **Roxstar AI Dost (Male):** Warm, energetic, peer-like tone. Answers technical and casual queries with relatable Indian analogies.
* **Roxstar AI Sathi (Female):** Thoughtful, clear, empathetic tone. Focuses on structured explanations and real-world examples.

---

## 4. Bot Routing Strategy

To avoid overlapping bot chatter and duplicate responses:

1. **Explicit Targeting:** When an utterance or text mentions `"Dost"` or `"AI Dost"`, Sathi drops the turn. When `"Sathi"` is addressed, Dost drops the turn.
2. **Open Room Queries:** If no bot is explicitly named, the primary respondent handles the prompt or both yield based on turn probability thresholds.
3. **Multi-Bot Orchestration:** In staged dual-turn scenarios (`"Dost answer karo, Sathi example do"`), bots respond sequentially based on task assignment in system context.

---

## 5. Prerequisites & Environment Setup

### Prerequisites

* Python 3.10+ (tested on Python 3.14 on Windows)
* LiveKit Cloud account & project credentials
* Deepgram API Key
* Groq API Key
* OpenAI API Key / ElevenLabs API Key

### Environment Variables (`.env`)

Create a `.env` file in the root directory (never commit this file):

```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
DEEPGRAM_API_KEY=your_deepgram_key
GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key
```

### Installation

```bash
# Clone the repository
git clone https://github.com/divergence-in-space/rockstar_voicebots.git
cd rockstar_voicebots

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate   # Windows
# source venv/bin/activate # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

---

## 6. Running the Agents

### Running Roxstar AI Dost (Male Bot)

In Terminal 1:
```bash
python agent.py dev
```

### Running Roxstar AI Sathi (Female Bot)

In Terminal 2:
```bash
python agent_sathi.py dev
```

### Testing via LiveKit Console

1. Log in to [LiveKit Cloud Console](https://cloud.livekit.io/).
2. Navigate to **Agents** → **Console**.
3. Select the registered worker (`roxstar-voice-agent` or `roxstar-voice-agent-sathi`).
4. Click **Save and start session** to test voice and chat streams.

---

## 7. Demonstration Scenarios Tested

| Scenario | Input (Voice / Chat) | Agent Output | Status |
| :--- | :--- | :--- | :--- |
| **1. Natural Hinglish** | *"AI kya hota hai?"* | Natural Hinglish explanation avoiding formal Hindi. | Verified |
| **2. English Understanding** | *"Can you explain cloud computing?"* | Understood in English, answered in clear Hinglish. | Verified |
| **3. Follow-up Context** | *"Shah Rukh Khan ke baare mein batao"* → *"Unki famous movie batao"* | Context maintained across consecutive turns. | Verified |
| **4. Multi-User Context** | User 1 asks concept → User 2 asks *"Simple batao"* | Simplified response referencing earlier turn. | Verified |
| **5. Session Memory** | *"Mera naam Rahul hai..."* → *"Maine kya bataya tha?"* | Retained user fact and recalled upon query. | Verified |
| **6. Interruption (Barge-in)** | Interrupted mid-response with *"Ruko, simple batao"* | Silero VAD cancels playback and pivots. | Verified |
| **7. Two-Bot Routing** | Directed prompts using bot names | Addressed agent answers; idle agent drops turn. | Verified |

---

## 8. Known Limitations & Next Steps

* **Testing Tool Single-Agent Scope:** LiveKit Cloud's built-in Agent Console UI binds to a single worker target per test session, requiring sequential validation in the console tool rather than dual-worker simultaneous presence in the test sandbox.
* * **Two-bot integration not completed:** Dost (`agent.py`) and Sathi (`agent_sathi.py`) were each built and verified separately, but they have **not been run together in one room**. LiveKit's Agent Console starts one named agent per test session, and running both in the same room needs explicit dispatch of both agents, which was not set up in time. As a result, the name-based turn routing (each bot skips a turn when the other is named) is implemented but **has not been tested live**, and overlapping greetings or replies between the bots have not been ruled out
* **Provider Upstream Latency:** Using multilingual TTS models incurs an additional ~200-400ms TTFB compared to single-language streaming engines. Future iterations will leverage custom fine-tuned edge models.
* **Accent Tuning (Sarvam AI Fallback):** Sarvam AI (`bulbul:v2`) was evaluated for regional Indic pronunciation but hit upstream 403 authorization restrictions during build. Fallback was successfully deployed using ElevenLabs and OpenAI Devanagari script routing.
* **Next Steps:** Implement shared Redis-backed session memory across distributed worker processes and implement a unified LiveKit agent dispatcher for multi-agent room dispatching.
