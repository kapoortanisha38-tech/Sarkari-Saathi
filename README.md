# Sarkari Saathi

Voice-first assistant that helps Indian citizens find government schemes by speaking in Hindi or English.

**Built with Gnani AI:** Prisma (speech-to-text) hears the user, Timbre (text-to-speech) answers in voice.
Scheme matching uses Google Gemini over `schemes.json` (10 sample central schemes; verify details on official sites).

## Run
```
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # Windows: copy .env.example .env  -> add your keys
uvicorn main:app --reload
```
Open http://localhost:8000 and tap the mic.

## Flow
mic (browser, WAV) -> `/api/ask` -> Gnani Prisma STT -> Gemini picks schemes -> Gnani Timbre TTS -> audio + scheme cards

Hashtags: #GnaniAI #GreatIndianAIInternshipChallenge
