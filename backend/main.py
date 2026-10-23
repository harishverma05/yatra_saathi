import hashlib
import json
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import eleven
import llm

ROOT = Path(__file__).parent
KB_DIR = ROOT / "kb"
CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)

app = FastAPI(title="Yatra Saathi")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/audio", StaticFiles(directory=CACHE), name="audio")

# Landmark metadata for the dashboard (images, descriptions, categories)
LANDMARK_META = {
    "bara_imambara": {
        "image": "/images/bara_imambara.jpg",
        "category": "Monument",
        "era": "1784",
        "rating": 4.8,
        "visitors": "~5000/day",
        "description": "One of the grandest monuments of Lucknow, featuring the famous Bhul Bhulaiya labyrinth.",
    },
    "rumi_darwaza": {
        "image": "/images/rumi_darwaza.jpg",
        "category": "Gateway",
        "era": "1784",
        "rating": 4.7,
        "visitors": "~8000/day",
        "description": "The iconic 60-foot gateway that has become the symbol of Lucknow.",
    },
    "tunday_kababi": {
        "image": "/images/tunday_kababi.jpg",
        "category": "Cuisine",
        "era": "1905",
        "rating": 4.6,
        "visitors": "~3000/day",
        "description": "Home of the legendary Galouti Kebab — so soft it melts in your mouth.",
    },
}


# ---------- helpers ----------
def load_kb(landmark: str) -> tuple[str, str, str]:
    """Returns (title, narration, full_text). KB format: '# Title', '## Narration', '## Facts'."""
    path = KB_DIR / f"{landmark}.md"
    if not path.exists():
        raise HTTPException(404, f"Unknown landmark: {landmark}")
    full = path.read_text(encoding="utf-8")
    title = full.splitlines()[0].lstrip("# ").strip()
    narration = full.split("## Narration", 1)[1].split("## Facts", 1)[0].strip()
    return title, narration, full


def save_audio(data: bytes, name: str | None = None) -> str:
    name = name or hashlib.sha1(data).hexdigest()[:16]
    (CACHE / f"{name}.mp3").write_bytes(data)
    return f"/audio/{name}.mp3"


async def read_upload(audio: UploadFile) -> tuple[bytes, str, str]:
    data = await audio.read()
    raw_ct = (audio.content_type or "audio/mp4").split(";")[0].strip().lower()
    fn = audio.filename or "audio.mp4"
    if "mp4" in raw_ct or "m4a" in raw_ct or fn.endswith((".mp4", ".m4a")):
        clean_ct = "audio/mp4"
        clean_fn = "audio.mp4"
    elif "webm" in raw_ct or fn.endswith(".webm"):
        clean_ct = "audio/webm"
        clean_fn = "audio.webm"
    elif "wav" in raw_ct or fn.endswith(".wav"):
        clean_ct = "audio/wav"
        clean_fn = "audio.wav"
    elif "mpeg" in raw_ct or "mp3" in raw_ct or fn.endswith(".mp3"):
        clean_ct = "audio/mpeg"
        clean_fn = "audio.mp3"
    else:
        clean_ct = "audio/mp4"
        clean_fn = "audio.mp4"
    return data, clean_fn, clean_ct


@app.get("/api/health")
@app.get("/")
def health():
    eleven_key, _, _, _ = eleven.get_config()
    llm_key = llm.get_config()["key"]
    return {
        "status": "online",
        "service": "Yatra Saathi API",
        "elevenlabs_configured": bool(eleven_key),
        "llm_configured": bool(llm_key),
    }


@app.get("/api/landmarks")
def landmarks():
    results = []
    for p in sorted(KB_DIR.glob("*.md")):
        lid = p.stem
        title = load_kb(lid)[0]
        meta = LANDMARK_META.get(lid, {})
        results.append({"id": lid, "title": title, **meta})
    return results


@app.get("/api/narrate/{landmark}")
async def narrate(landmark: str, lang: str = "en"):
    meta = CACHE / f"narr_{landmark}_{lang}.json"
    if meta.exists():  # pre-cached -> instant demo
        try:
            return json.loads(meta.read_text(encoding="utf-8"))
        except Exception:
            pass
    try:
        _, narration, _ = load_kb(landmark)
        text = await llm.translate(narration, "en", lang, landmark_id=landmark)
        audio_bytes = await eleven.tts(text, lang)
        url = save_audio(audio_bytes, f"narr_{landmark}_{lang}")
        out = {"text": text, "audio_url": url}
        meta.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
        return out
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/ask")
async def ask(audio: UploadFile = File(...), landmark: str = Form(...), lang: str = Form("en")):
    try:
        data, fn, ct = await read_upload(audio)
        question = await eleven.stt(data, fn, ct)  # auto-detect language
        if not question:
            raise HTTPException(422, "Could not hear anything. Please try speaking again.")
        _, _, kb = load_kb(landmark)
        reply = await llm.answer(question, kb, lang)
        audio_bytes = await eleven.tts(reply, lang)
        return {
            "question": question,
            "text": reply,
            "audio_url": save_audio(audio_bytes),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/interpret")
async def interpret(audio: UploadFile = File(...), src: str = Form("en"), tgt: str = Form("hi")):
    try:
        data, fn, ct = await read_upload(audio)
        heard, translated, audio_bytes = await eleven.translate_audio(data, fn, ct, src, tgt)
        return {
            "text": heard,
            "translation": translated,
            "audio_url": save_audio(audio_bytes),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/stats")
def stats():
    """Dashboard usage stats from ElevenLabs SDK headers."""
    return eleven.get_usage_stats()
