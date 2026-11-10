import asyncio
import base64, json, os
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()
GNANI_KEY = os.getenv("GNANI_API_KEY", "")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
VOICE = "Shivani"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
SCHEMES = json.load(open("schemes.json", encoding="utf-8"))
H = {"X-API-Key-ID": GNANI_KEY}

app = FastAPI()


async def stt(audio: bytes, lang: str) -> str:
    """Gnani Prisma speech-to-text (REST, clips up to 60s)."""
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(
            "https://api.vachana.ai/stt/v3",
            headers=H,
            files={"audio_file": ("speech.wav", audio, "audio/wav")},
            data={"language_code": lang},
        )
    if r.status_code != 200:
        raise HTTPException(502, f"Gnani STT error {r.status_code}: {r.text[:200]}")
    return r.json().get("transcript", "").strip()


async def ask_llm(question: str, reply_lang: str) -> dict:
    """Pick matching schemes with Gemini; return short spoken answer + schemes."""
    prompt = f"""You help Indian citizens find government schemes.
Schemes (JSON): {json.dumps(SCHEMES, ensure_ascii=False)}

User said: "{question}"

Pick the 1-3 best matching schemes from the list only. If the user gave too little
information, give the most likely ones and ask one short follow-up question.
Reply language: {reply_lang}. The spoken answer must be 2-4 simple sentences,
plain words, no markdown, no emojis, numbers written naturally.
Return ONLY JSON: {{"answer": "...", "schemes": ["exact scheme name", ...]}}"""
    models = [GEMINI_MODEL, "gemini-flash-latest", "gemini-flash-lite-latest"]
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    last = ""
    async with httpx.AsyncClient(timeout=30) as c:
        for model in models * 2:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            try:
                r = await c.post(url, params={"key": GEMINI_KEY}, json=body)
            except httpx.HTTPError as e:
                last = str(e)
                continue
            if r.status_code == 200:
                text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
            last = f"{r.status_code}: {r.text[:150]}"
            await asyncio.sleep(1)
    raise HTTPException(502, f"LLM error {last}")

async def tts(text: str):
    """Gnani Timbre text-to-speech (REST, returns audio bytes)."""
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(
            "https://api.vachana.ai/api/v1/tts/inference",
            headers={**H, "Content-Type": "application/json"},
                  json={
       "text": text,
       "voice": VOICE,
       "model": "timbre-v3.0",
       "audio_config": {
           "sample_rate": 24000,
           "num_channels": 1,
           "sample_width": 2,
           "encoding": "linear_pcm",
           "container": "wav",
       },
   },
        )
    if r.status_code != 200:
        raise HTTPException(502, f"Gnani TTS error {r.status_code}: {r.text[:200]}")
    print("TTS:", r.headers.get("content-type"), len(r.content), r.content[:12])
    return r.content, r.headers.get("content-type", "audio/wav")


@app.post("/api/ask")
async def ask(audio: UploadFile = File(...), lang: str = Form("hi-IN")):
    if not GNANI_KEY or not GEMINI_KEY:
        raise HTTPException(500, "Set GNANI_API_KEY and GEMINI_API_KEY in .env")
    transcript = await stt(await audio.read(), lang)
    if not transcript:
        raise HTTPException(422, "Could not hear anything. Please try again.")
    reply_lang = "Hindi (Devanagari)" if lang.startswith("hi") else "English"
    result = await ask_llm(transcript, reply_lang)
    audio_bytes, mime = await tts(result["answer"])
    matched = [s for s in SCHEMES if s["name"] in result.get("schemes", [])]
    return {
        "transcript": transcript,
        "answer": result["answer"],
        "schemes": matched,
        "audio": base64.b64encode(audio_bytes).decode(),
        "mime": mime,
    }


@app.get("/")
def home():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")
