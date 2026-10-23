import asyncio
import io
import os
import re
import httpx
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()

# Default configuration
KEY = os.getenv("ELEVENLABS_API_KEY", "")
TTS_MODEL = os.getenv("ELEVEN_TTS_MODEL", "eleven_flash_v2_5")
STT_MODEL = os.getenv("ELEVEN_STT_MODEL", "scribe_v1")
VOICES = {
    "en": os.getenv("ELEVEN_VOICE_EN", "21m00Tcm4TlvDq8ikWAM"),
    "hi": os.getenv("ELEVEN_VOICE_HI", "21m00Tcm4TlvDq8ikWAM"),
}
# Scribe takes ISO-639-3 codes; omit for auto-detect (better for code-mixed speech)
SCRIBE_LANG = {"en": "eng", "hi": "hin"}

_client = httpx.AsyncClient(timeout=60)

# Track usage metadata for the dashboard (from ElevenLabs response headers)
usage_stats = {
    "tts_calls": 0,
    "stt_calls": 0,
    "total_characters": 0,
    "last_request_id": None,
    "last_trace_id": None,
}


def get_config():
    """Reload .env dynamically to pick up any key updates without server restart."""
    global KEY, TTS_MODEL, STT_MODEL, VOICES
    load_dotenv(override=True)
    KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()
    TTS_MODEL = os.getenv("ELEVEN_TTS_MODEL", "eleven_flash_v2_5").strip()
    STT_MODEL = os.getenv("ELEVEN_STT_MODEL", "scribe_v1").strip()
    VOICES = {
        "en": os.getenv("ELEVEN_VOICE_EN", "21m00Tcm4TlvDq8ikWAM").strip(),
        "hi": os.getenv("ELEVEN_VOICE_HI", "21m00Tcm4TlvDq8ikWAM").strip(),
    }
    return KEY, TTS_MODEL, STT_MODEL, VOICES


def get_usage_stats():
    """Return current usage stats gathered from ElevenLabs response headers."""
    return dict(usage_stats)


async def tts(text: str, lang: str) -> bytes:
    """Text-to-speech using ElevenLabs SDK with with_raw_response to capture
    character-cost, request-id, and x-trace-id from response headers.
    Falls back to direct REST API with xi-api-key if needed."""
    key, tts_model, _, voices = get_config()
    if not key:
        raise ValueError("ELEVENLABS_API_KEY is not set. Please add it to backend/.env")

    voice_id = voices.get(lang, voices["en"])

    # 1. Primary: Official ElevenLabs SDK with with_raw_response
    try:
        client = ElevenLabs(api_key=key)

        # Get raw response with headers
        with client.text_to_speech.with_raw_response.convert(
            text=text,
            voice_id=voice_id,
            model_id=tts_model,
            output_format="mp3_44100_128",
        ) as response:
            # Access character cost from headers
            char_cost = response.headers.get("character-cost")

            # Store these for debugging / dashboard
            request_id = response.headers.get("request-id")
            trace_id = response.headers.get("x-trace-id")

            # Read audio data from response stream
            if hasattr(response.data, "__iter__") and not isinstance(response.data, (bytes, bytearray)):
                audio_data = b"".join(response.data)
            else:
                audio_data = response.data

        # Update telemetry stats
        usage_stats["tts_calls"] += 1
        usage_stats["last_request_id"] = request_id
        usage_stats["last_trace_id"] = trace_id
        if char_cost:
            usage_stats["total_characters"] += int(char_cost)

        return audio_data

    except Exception:
        # 2. Fallback: Direct REST API with xi-api-key header
        r = await _client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            params={"output_format": "mp3_44100_128"},
            headers={"xi-api-key": key, "Content-Type": "application/json"},
            json={"text": text, "model_id": tts_model},
        )
        if r.status_code != 200:
            raise RuntimeError(f"ElevenLabs TTS error ({r.status_code}): {r.text}")

        char_cost = r.headers.get("character-cost")
        request_id = r.headers.get("request-id")
        trace_id = r.headers.get("x-trace-id")

        usage_stats["tts_calls"] += 1
        usage_stats["last_request_id"] = request_id
        usage_stats["last_trace_id"] = trace_id
        if char_cost:
            usage_stats["total_characters"] += int(char_cost)

        return r.content


def sanitize_audio_meta(filename: str, content_type: str) -> tuple[str, str]:
    """Strip codec parameters (e.g. '; codecs=mp4a.40.2') and normalize for ElevenLabs."""
    clean_ct = (content_type or "").split(";")[0].strip().lower()
    fn = filename or "audio.mp4"
    if "mp4" in clean_ct or "m4a" in clean_ct or fn.endswith((".mp4", ".m4a")):
        return "audio.mp4", "audio/mp4"
    if "webm" in clean_ct or fn.endswith(".webm"):
        return "audio.webm", "audio/webm"
    if "wav" in clean_ct or fn.endswith(".wav"):
        return "audio.wav", "audio/wav"
    if "mpeg" in clean_ct or "mp3" in clean_ct or fn.endswith(".mp3"):
        return "audio.mp3", "audio/mpeg"
    if "ogg" in clean_ct or fn.endswith(".ogg"):
        return "audio.ogg", "audio/ogg"
    return "audio.mp4", "audio/mp4"


async def stt(audio: bytes, filename: str, content_type: str, lang: str | None = None) -> str:
    """Speech-to-text using ElevenLabs Scribe API with xi-api-key header."""
    key, _, stt_model, _ = get_config()
    if not key:
        raise ValueError("ELEVENLABS_API_KEY is not set. Please add it to backend/.env")

    clean_fn, clean_ct = sanitize_audio_meta(filename, content_type)

    # 1. Primary: Official ElevenLabs SDK
    try:
        client = ElevenLabs(api_key=key)
        # Wrap audio as (filename, BytesIO, content_type) tuple for proper format detection
        file_tuple = (clean_fn, io.BytesIO(audio), clean_ct)
        res = client.speech_to_text.convert(
            file=file_tuple,
            model_id=stt_model,
            language_code=SCRIBE_LANG.get(lang) if lang else None,
        )
        usage_stats["stt_calls"] += 1
        return (res.text or "").strip()

    except Exception:
        # 2. Fallback: Direct REST API with xi-api-key header
        data = {"model_id": stt_model}
        if lang in SCRIBE_LANG:
            data["language_code"] = SCRIBE_LANG[lang]
        r = await _client.post(
            "https://api.elevenlabs.io/v1/speech-to-text",
            headers={"xi-api-key": key},
            data=data,
            files={"file": (filename, audio, content_type)},
        )
        if r.status_code != 200:
            raise RuntimeError(f"ElevenLabs STT error ({r.status_code}): {r.text}")
        usage_stats["stt_calls"] += 1
        return r.json().get("text", "").strip()


async def translate_audio(
    audio: bytes,
    filename: str,
    content_type: str,
    src_lang: str,
    tgt_lang: str,
) -> tuple[str, str, bytes]:
    """
    Live Translation using ONLY ElevenLabs:
    1. Transcribes source voice via ElevenLabs Scribe.
    2. Translates speech and generates dubbed voice via ElevenLabs Dubbing API.
    3. Retrieves translated transcript and dubbed audio directly from ElevenLabs.
    """
    key, _, _, _ = get_config()
    if not key:
        raise ValueError("ELEVENLABS_API_KEY is not set. Please add it to backend/.env")

    clean_fn, clean_ct = sanitize_audio_meta(filename, content_type)

    # 1. Get heard text using ElevenLabs STT
    heard_text = await stt(audio, clean_fn, clean_ct, src_lang)

    if src_lang == tgt_lang:
        return heard_text, heard_text, audio

    # 2. Translate and dub using ElevenLabs Dubbing API
    client = ElevenLabs(api_key=key)
    file_tuple = (clean_fn, io.BytesIO(audio), clean_ct)

    dub = client.dubbing.create(
        file=file_tuple,
        source_lang=src_lang,
        target_lang=tgt_lang,
    )
    dub_id = dub.dubbing_id

    # Poll status (Dubbing short spoken phrases takes 2-4 seconds)
    status = "dubbing"
    for _ in range(15):
        await asyncio.sleep(1.5)
        res = client.dubbing.get(dubbing_id=dub_id)
        status = res.status
        if status == "dubbed":
            break

    if status != "dubbed":
        # Graceful fallback: synthesize TTS in target language if dubbing times out
        fallback_audio = await tts(heard_text, tgt_lang)
        return heard_text, heard_text, fallback_audio

    # 3. Retrieve dubbed audio bytes from ElevenLabs
    audio_gen = client.dubbing.audio.get(dubbing_id=dub_id, language_code=tgt_lang)
    dubbed_audio = b"".join(audio_gen) if hasattr(audio_gen, "__iter__") else audio_gen

    # 4. Retrieve translated text transcript from ElevenLabs
    r = await _client.get(
        f"https://api.elevenlabs.io/v1/dubbing/{dub_id}/transcript/{tgt_lang}",
        headers={"xi-api-key": key},
    )
    translated_text = ""
    if r.status_code == 200:
        lines = [
            re.sub(r"<[^>]+>", "", line.strip())
            for line in r.text.splitlines()
            if line.strip() and not line.strip().isdigit() and "-->" not in line
        ]
        translated_text = " ".join(lines).strip()

    # Clean up dubbing job on ElevenLabs
    try:
        client.dubbing.delete(dubbing_id=dub_id)
    except Exception:
        pass

    return heard_text, translated_text or heard_text, dubbed_audio
