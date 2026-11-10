# Sarkari Saathi

Voice-first assistant that helps Indian citizens find government schemes by speaking in Hindi or English.

**Built with Gnani AI:** Prisma (speech-to-text) hears the user, Timbre (text-to-speech) answers in voice.
Scheme matching uses Google Gemini over `schemes.json` (10 sample central schemes; verify details on official sites).

## Run
   ```
   pip install -r requirements.txt
   copy .env.example .env      (Mac/Linux: cp .env.example .env)
   ```
   Add your Gnani and Gemini keys to `.env`, then run:
   ```
   python -m uvicorn main:app --reload
   ```
   Open http://localhost:8000 and tap the mic.

   Built by Tanisha Kapoor for The Great Indian AI Internship Challenge.

## Flow
mic (browser, WAV) -> `/api/ask` -> Gnani Prisma STT -> Gemini picks schemes -> Gnani Timbre TTS -> audio + scheme cards

Hashtags: #GnaniAI #GreatIndianAIInternshipChallenge
