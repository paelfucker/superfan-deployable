import logging
import os
import pathlib
from urllib.parse import quote

from fastapi import FastAPI, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from . import services
from .guards import RateLimiter, SessionStore

log = logging.getLogger("superfan")

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # a few seconds of speech is well under 1 MB
MIN_UPLOAD_BYTES = 1000

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Chat-Response"],
)

limiter = RateLimiter(
    per_client=int(os.getenv("RATE_LIMIT_PER_10_MIN", "20")),
    window_seconds=600,
    daily_cap=int(os.getenv("DAILY_REQUEST_CAP", "1000")),
)
sessions = SessionStore()


def _client_ip(request: Request) -> str:
    # Cloud Run puts the real client first in X-Forwarded-For.
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.post("/ask")
def ask(
    request: Request,
    audio_file: UploadFile,
    x_session_id: str | None = Header(default=None),
):
    reason = limiter.check(_client_ip(request))
    if reason == "daily_cap":
        raise HTTPException(429, "The Super Fan needs rest. Come back tomorrow.")
    if reason:
        raise HTTPException(429, "Slow down, friend. Try again in a few minutes.")

    audio = audio_file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(audio) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Recording too long.")
    if len(audio) < MIN_UPLOAD_BYTES:
        raise HTTPException(422, "Recording too short.")

    session_id = (x_session_id or _client_ip(request))[:64]

    try:
        question = services.transcribe(audio, audio_file.filename or "recording.webm")
        if not question:
            raise HTTPException(422, "Couldn't hear anything. Try again.")

        reply = services.chat(sessions.get(session_id), question)
        speech = services.speak(reply)
    except HTTPException:
        raise
    except services.MissingKey as err:
        log.error("Server is missing configuration: %s", err)
        raise HTTPException(500, "Server is not configured.")
    except Exception:
        log.exception("Upstream failure")
        raise HTTPException(502, "The Super Fan is unreachable. Try again.")

    sessions.add_turn(session_id, question, reply)
    return Response(
        content=speech,
        media_type="audio/mpeg",
        headers={"X-Chat-Response": quote(reply, safe=""), "Cache-Control": "no-store"},
    )


# Serve the built React app. Mounted last so it never shadows the API routes.
build_dir = pathlib.Path(__file__).resolve().parent.parent / "frontend" / "build"
if build_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(build_dir), html=True), name="static")
