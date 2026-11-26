"""The three outside services: speech-to-text, chat, text-to-speech.

All keys and model names come from environment variables, never from code.
"""
import os
from functools import lru_cache

from .persona import FALLBACK_REPLY, SYSTEM_PROMPT

# Model names are env-configurable because OpenAI retires models over time
# (whisper-1 is scheduled to shut down on 2027-02-26).
STT_MODEL = os.getenv("STT_MODEL", "whisper-1")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-6-luna")
TTS_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_flash_v2_5")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "EfeZGaJNAkxPkAcQVffY")
# Hard cap on reply length. Replies are meant to be ~12 words; this stops a
# runaway answer from costing you money in voice characters.
MAX_REPLY_TOKENS = int(os.getenv("MAX_REPLY_TOKENS", "120"))
MAX_REPLY_CHARS = int(os.getenv("MAX_REPLY_CHARS", "160"))

CONTENT_TYPES = {
    "webm": "audio/webm",
    "m4a": "audio/mp4",
    "mp4": "audio/mp4",
    "ogg": "audio/ogg",
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
}


class MissingKey(RuntimeError):
    pass


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise MissingKey(f"{name} is not set")
    return value


@lru_cache(maxsize=1)
def _openai():
    from openai import OpenAI

    return OpenAI(api_key=_require("OPENAI_API_KEY"))


@lru_cache(maxsize=1)
def _eleven():
    from elevenlabs import ElevenLabs

    return ElevenLabs(api_key=_require("ELEVENLABS_API_KEY"))


def transcribe(audio: bytes, filename: str) -> str:
    """Turn recorded audio into text. The language is auto-detected."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "webm"
    content_type = CONTENT_TYPES.get(ext, "audio/webm")
    result = _openai().audio.transcriptions.create(
        model=STT_MODEL,
        file=(f"recording.{ext}", audio, content_type),
    )
    return (result.text or "").strip()


def chat(history: list, user_text: str) -> str:
    """Get a short in-character reply."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history]
    messages.append({"role": "user", "content": user_text})
    completion = _openai().chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        max_completion_tokens=MAX_REPLY_TOKENS,
    )
    text = (completion.choices[0].message.content or "").strip()
    if not text:
        return FALLBACK_REPLY
    return text[:MAX_REPLY_CHARS]


def speak(text: str) -> bytes:
    """Turn the reply into MP3 audio."""
    stream = _eleven().text_to_speech.convert(
        voice_id=VOICE_ID,
        text=text,
        model_id=TTS_MODEL,
        output_format="mp3_44100_64",
    )
    return b"".join(stream)
