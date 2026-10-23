import os
import httpx
from dotenv import load_dotenv

LANGS = {"en": "English", "hi": "Hindi"}

_client = httpx.AsyncClient(timeout=60)

# Pre-translated landmark narrations in natural spoken Hindi
LANDMARK_HINDI_NARRATION = {
    "rumi_darwaza": (
        "यह रूमी दरवाज़ा है, वह भव्य द्वार जो लखनऊ का ऐतिहासिक प्रतीक बन चुका है। "
        "इसे 1784 में नवाब आसफ़-उद-दौला ने बनवाया था, जिन्होंने बड़ा इमामबाड़ा भी तामीर कराया था। "
        "लगभग साठ फीट ऊंचा, इसका भव्य मेहराब और नाज़ुक नक्काशी इसे शहर का सबसे गौरवशाली स्थल बनाती है। "
        "कहा जाता है कि इसकी रूपरेखा इस्तांबुल के ऐतिहासिक द्वार जैसी है, और वहीं से इसका नाम रूमी पड़ा। "
        "इसके नीचे खड़े होकर नवाबों की शाही सवारियों और नवाबी तहज़ीब की कल्पना कीजिए।"
    ),
    "bara_imambara": (
        "यह लखनऊ का विश्व प्रसिद्ध बड़ा इमामबाड़ा है, जिसे 1784 में नवाब आसफ़-उद-दौला ने अकाल राहत कार्य के दौरान बनवाया था। "
        "इस विशाल ऐतिहासिक परिसर में मशहूर भुलभुलैया, भव्य आसफ़ी मस्जिद और शाही बावली शामिल हैं। "
        "इसके मुख्य हॉल की विशाल छत बिना किसी बीम या खंभे के सहारे टिकी है, जो वास्तुकला का एक अद्भुत करिश्मा है।"
    ),
    "tunday_kababi": (
        "यह है लखनऊ का मशहूर टुंडे कबाबी, जिसकी शुरुआत 1905 में चौक बाज़ार से हुई थी। "
        "इसके संस्थापक हाजी मुराद अली एक हाथ से दिव्यांग थे, इसलिए उन्हें प्यार से टुंडे कबाबी कहा जाता था। "
        "उनके बनाए गलौटी कबाब 160 से अधिक गुप्त मसालों के साथ इतने नर्म बनते हैं कि मुंह में रखते ही घुल जाते हैं। "
        "यह लखनवी ज़ायके और नवाबी मेहमाननवाज़ी की सबसे खास पहचान है।"
    ),
}


def get_config():
    load_dotenv(override=True)
    return {
        "base": os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
        "key": os.getenv("LLM_API_KEY", ""),
        "model": os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
    }


async def chat(system: str, user: str, temperature: float = 0.3) -> str:
    cfg = get_config()
    if not cfg["key"]:
        raise ValueError("LLM_API_KEY is not set in backend/.env. Please configure your Groq or OpenAI API key.")

    r = await _client.post(
        f"{cfg['base']}/chat/completions",
        headers={"Authorization": f"Bearer {cfg['key']}"},
        json={
            "model": cfg["model"],
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


async def translate(text: str, src: str, tgt: str, landmark_id: str | None = None) -> str:
    if src == tgt or not text:
        return text

    # Check for curated landmark Hindi narration
    if tgt == "hi" and landmark_id and landmark_id in LANDMARK_HINDI_NARRATION:
        return LANDMARK_HINDI_NARRATION[landmark_id]

    # Check by text match
    for lid, hindi_text in LANDMARK_HINDI_NARRATION.items():
        if landmark_id == lid or lid.replace("_", " ") in text.lower():
            if tgt == "hi":
                return hindi_text

    cfg = get_config()
    if not cfg["key"]:
        # If no LLM key yet, return original text or known phrase rather than crashing
        if tgt == "hi" and "rumi" in text.lower():
            return LANDMARK_HINDI_NARRATION["rumi_darwaza"]
        if tgt == "hi" and "imambara" in text.lower():
            return LANDMARK_HINDI_NARRATION["bara_imambara"]
        if tgt == "hi" and "tunday" in text.lower():
            return LANDMARK_HINDI_NARRATION["tunday_kababi"]
        return text

    system = (
        f"You are a live interpreter. Translate from {LANGS[src]} to {LANGS[tgt]}. "
        "Keep the tone polite and natural for spoken conversation. "
        "Use Devanagari script for Hindi. Output ONLY the translation."
    )
    return await chat(system, text, temperature=0.1)


async def answer(question: str, kb: str, lang: str) -> str:
    cfg = get_config()
    if not cfg["key"]:
        # Fallback when LLM key is not yet set: extract informative summary from kb
        facts = [line.strip("- *# ") for line in kb.splitlines() if line.strip().startswith("-")]
        summary = " ".join(facts[:3]) if facts else "Welcome to Lucknow! This is a historic heritage landmark."
        if lang == "hi":
            return f"लखनऊ के इतिहास में आपका स्वागत है। {summary}। विस्तृत जानकारी के लिए backend/.env में LLM_API_KEY जोड़ें।"
        return f"{summary} (For custom interactive AI answers, please configure LLM_API_KEY in backend/.env)."

    system = (
        "You are Yatra Saathi, a warm storyteller guide for tourists in Lucknow. "
        "Answer ONLY using the facts below. If the answer is not in the facts, "
        "say you are not sure and suggest asking a local guide. "
        f"Reply in {LANGS[lang]} in 2-3 short spoken sentences, no lists.\n\n"
        f"FACTS:\n{kb}"
    )
    return await chat(system, question)
