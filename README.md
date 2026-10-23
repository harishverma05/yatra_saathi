# Yatra Saathi

Voice-first travel companion for Lucknow. ElevenLabs Scribe (STT) + TTS, open-weight LLM for translation and grounded Q&A.

## Run

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add ELEVENLABS_API_KEY and LLM_API_KEY
python pregen.py            # pre-cache all narrations (en + hi)
uvicorn main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173
```

Phones need HTTPS for the mic. Easiest: `ngrok http 5173` (or `cloudflared tunnel --url http://localhost:5173`).

## API
| Endpoint | Purpose |
|---|---|
| `GET /api/landmarks` | list landmarks |
| `GET /api/narrate/{id}?lang=en\|hi` | `{text, audio_url}`, cached on disk |
| `POST /api/ask` | form: `audio`, `landmark`, `lang` → Scribe → grounded LLM → TTS |
| `POST /api/interpret` | form: `audio`, `src`, `tgt` → Scribe → translate → TTS |

## Add a landmark
Create `backend/kb/<id>.md` with `# Title`, `## Narration`, `## Facts`. Verify every fact by hand.

## License
MIT
