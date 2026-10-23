# ⚙️ Yatra Saathi Backend
### *High-Performance FastAPI Audio Engine & ElevenLabs Multimodal Pipeline*

The **Yatra Saathi Backend** serves as the intelligence and audio processing layer of the travel companion. Built on **FastAPI** and **Uvicorn**, it coordinates speech synthesis, speech recognition, real-time cross-language audio dubbing, and telemetry tracking.

---

## 🏛️ Architecture Overview

The backend is intentionally architected around simplicity, speed, and resilient voice processing:

1. **Native ElevenLabs SDK (`elevenlabs.client.ElevenLabs`)**:
   - Integrates the modern ElevenLabs Python SDK.
   - Employs `with_raw_response` context managers to intercept HTTP response headers directly from ElevenLabs edge servers.
2. **Audio MIME Normalization (`sanitize_audio_meta`)**:
   - Solves cross-browser recording incompatibilities (such as Safari's `audio/mp4; codecs=mp4a.40.2` and Chromium's `audio/webm; codecs=opus`) by sanitizing multipart payloads before forwarding them to downstream neural models.
3. **Pure ElevenLabs Audio Translation Pipeline**:
   - Uses **ElevenLabs Scribe (`scribe_v1`)** for high-accuracy source audio transcription.
   - Uses **ElevenLabs Dubbing v2** for automated speech-to-speech translation into target accents while preserving the original speaker's vocal characteristics and cadence.
4. **Low-Latency Disk Cache**:
   - Caches synthesized landmark narratives by landmark ID and language code (`/audio/narr_<landmark>_<lang>.mp3`). Repeated requests for stories resolve in under 2ms.

---

## 📂 Backend File Organization

```
backend/
├── kb/                       # Domain Knowledge Bases (Markdown)
│   ├── bara_imambara.md      # Historical facts on Bara Imambara & Bhul Bhulaiya
│   ├── rumi_darwaza.md       # Architectural history of Rumi Darwaza
│   └── tunday_kababi.md      # Culinary origin of Nawabi Galouti kebabs
├── cache/                    # Local storage for synthesized MP3 files
├── eleven.py                 # Core ElevenLabs SDK wrapper, Dubbing, and Telemetry
├── llm.py                    # Curated heritage narrations & Grounded Q&A engine
├── main.py                   # FastAPI server, endpoints, and static audio mounts
├── pregen.py                 # CLI utility to pre-synthesize landmark audio
├── requirements.txt          # Python package requirements
├── .env.example              # Sample environment configuration
└── README.md                 # This backend guide
```

---

## 🔑 Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

| Variable | Default Value | Description |
|---|---|---|
| `ELEVENLABS_API_KEY` | *(Required)* | Your ElevenLabs API key. |
| `ELEVEN_TTS_MODEL` | `eleven_flash_v2_5` | High-speed, multilingual low-latency model. |
| `ELEVEN_STT_MODEL` | `scribe_v1` | ElevenLabs Scribe speech-to-text model. |
| `ELEVEN_VOICE_EN` | `21m00Tcm4TlvDq8ikWAM` | Voice ID used for English speech synthesis. |
| `ELEVEN_VOICE_HI` | `21m00Tcm4TlvDq8ikWAM` | Voice ID used for Hindi speech synthesis. |
| `LLM_BASE_URL` | `https://api.groq.com/openai/v1` | Optional OpenAI-compatible inference base URL. |
| `LLM_API_KEY` | *(Optional)* | Optional API key for freeform LLM answering. |
| `LLM_MODEL` | `llama-3.3-70b-versatile` | Model name for conversational grounding. |

> [!NOTE]
> Environment variables are loaded dynamically using `load_dotenv(override=True)`. Changes to `.env` take effect immediately on subsequent requests without requiring server reboots.

---

## 📡 API Specification

### 1. Healthcheck
- **Endpoint**: `GET /api/health`
- **Response**:
```json
{
  "status": "online",
  "service": "Yatra Saathi API",
  "elevenlabs_configured": true,
  "llm_configured": false
}
```

### 2. List Landmarks
- **Endpoint**: `GET /api/landmarks`
- **Response**: Returns an array of landmarks with rich metadata (name, era, visitor rating, descriptions, images).

### 3. Landmark Narration
- **Endpoint**: `GET /api/narrate/{landmark_id}?lang={en|hi}`
- **Parameters**:
  - `landmark_id`: e.g. `rumi_darwaza`, `bara_imambara`, `tunday_kababi`
  - `lang`: `en` or `hi` (default: `en`)
- **Response**:
```json
{
  "text": "This is the Rumi Darwaza, the great gateway...",
  "audio_url": "/audio/narr_rumi_darwaza_en.mp3"
}
```

### 4. Live Speech Interpreter (Pure ElevenLabs)
- **Endpoint**: `POST /api/interpret`
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `audio`: Recorded audio file (`audio/webm` or `audio/mp4`)
  - `src`: Source language code (e.g. `en`, `hi`)
  - `tgt`: Target language code (e.g. `hi`, `en`)
- **Response**:
```json
{
  "text": "Where is the Bara Imambara entrance?",
  "translation": "बड़ा इमामबाड़ा का मुख्य प्रवेश द्वार कहाँ है?",
  "audio_url": "/audio/84eb05dd29d39d7b.mp3"
}
```

### 5. Grounded Voice Q&A
- **Endpoint**: `POST /api/ask`
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `audio`: Recorded voice query
  - `landmark`: Landmark ID (`rumi_darwaza`, etc.)
  - `lang`: Language code (`en` or `hi`)
- **Response**:
```json
{
  "question": "Who built this gate?",
  "text": "Rumi Darwaza was built in 1784 by Nawab Asaf-ud-Daula as part of famine-relief works.",
  "audio_url": "/audio/a39bc019284f.mp3"
}
```

### 6. Observability & Telemetry Stats
- **Endpoint**: `GET /api/stats`
- **Response**:
```json
{
  "tts_calls": 5,
  "stt_calls": 3,
  "total_characters": 250,
  "last_request_id": "yXikHA1tTzzlJ43Vh6f8",
  "last_trace_id": "3b2f326ea056d6af4d5d3e68df440b96"
}
```

---

## 🧪 Local Testing & Verification

Run the test suite directly to verify your ElevenLabs credentials and audio generation:

```bash
python3 -c "
import asyncio, eleven

async def test():
    print('Testing TTS...')
    audio = await eleven.tts('Testing Yatra Saathi', 'en')
    print('Generated audio bytes:', len(audio))
    
    print('Testing STT...')
    text = await eleven.stt(audio, 'test.mp3', 'audio/mp3', 'en')
    print('Transcribed text:', text)
    
    print('Stats:', eleven.get_usage_stats())

asyncio.run(test())
"
```
