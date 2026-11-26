# Superfan

Tap the mic, ask The #1 Super Fan a question, and it answers out loud like a Magic 8-Ball.

Flow: your voice -> OpenAI speech-to-text -> short in-character reply -> ElevenLabs voice -> played back in the browser.

## Run locally

```bash
pip install -r requirements.txt
cd frontend && npm ci && npm run build && cd ..
export OPENAI_API_KEY=...        # see .env.example
export ELEVENLABS_API_KEY=...
uvicorn backend.main:app --port 8000
```

Open http://localhost:8000. Browsers only allow the microphone on `localhost` or HTTPS.

## Deploy to Google Cloud Run

```bash
gcloud run deploy superfan --source . --region us-central1 \
  --allow-unauthenticated --max-instances 2 --memory 512Mi \
  --set-env-vars OPENAI_API_KEY=...,ELEVENLABS_API_KEY=...
```

Cloud Run builds the `Dockerfile`, gives you an HTTPS URL, and scales to zero when idle.
`--max-instances 2` keeps a traffic spike from running up your API bill.

## Keeping the bill small

- Replies are capped at about 12 words (see `backend/persona.py`) plus a hard limit in `backend/services.py`.
- Each visitor is limited to 20 questions per 10 minutes, and the whole app to 1,000 per day. Change with `RATE_LIMIT_PER_10_MIN` and `DAILY_REQUEST_CAP`.
- Set a budget alert in the Google Cloud, OpenAI and ElevenLabs dashboards too.

## Model names

OpenAI retires models over time, so they are settings, not code: `CHAT_MODEL` (default `gpt-6-luna`) and `STT_MODEL` (default `whisper-1`, which OpenAI plans to shut down on 2027-02-26). Change them without touching the code.
