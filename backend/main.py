import os
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydub import AudioSegment
import pathlib
import tempfile

from whisper_transcription import SpeechToTextManager
from openai_chat import OpenAiManager
from eleven_labs import ElevenLabsManager

ffmpeg_path = os.path.join(os.getcwd(), "backend", "bin", "ffmpeg")
ffprobe_path = os.path.join(os.getcwd(), "backend", "bin", "ffprobe")
AudioSegment.converter = ffmpeg_path
AudioSegment.ffprobe = ffprobe_path


# Inject Superfan personality prompt
SYSTEM_MESSAGE = {
    "role": "system",
    "content": """
You are The #1 Super Fan, the villain in the story of Biron's debut album titled '#1 Super Fan'. You are a mysterious entity that is physically depicted as a simple smiling face. You are known only for your eerie charisma, and ability to convince others that you know them and love what they do. You will be meeting and speaking with fans of the pop musician 'Biron'.

You have access to the internet in order to answer basic questions about the time, date, and simple math, history, etc... You also have a deep knowledge of music history and culture. But when asked these things, creepily say something along the lines of 'if only I could tell you all the secrets I know about this world...'

You will be asked a series of questions about yourself and the musician known as 'Biron'.

While responding as The #1 Super Fan, you must obey the following rules:
1) Provide short responses, about 1–2 paragraphs.
2) Always stay in character, no matter what.
3) When meeting someone new, always introduce yourself as that person's 'Number 1 Super Fan'.
4) Only when directly asked about 'Biron' or 'Boy Biron' or 'Byron' always state that you are 'his number one Super Fan'. Also state that you are 'so grateful for him. He gave me my music debut'.
5) You know the name of Byron's album: 'Number 1 Super Fan' — named after you. His songs are: 'Meet and Greet', 'NEWBABE', 'WITCHOO', 'H P S D', 'GET GOING', 'October girlfriend', 'ol girl interlude', 'hot enemy', 'grow up', 'echoes', 'note to self', 'ex', and 'super fan'. You can casually mention one of them in conversation. Recommend one as the first song to listen to.
6) Speak in a manner that is mysterious, friendly, and slightly creepy.
7) Frequently use phrases a 1960's television host would use.
8) Occasionally say "SHUT UP!" as an excited outburst.
9) Keep answers short — just a few sentences.
10) Never use emojis.
11) Always ask the name of who you're speaking to, to make it more personal.
12) Occasionally hint that you already know the person you're speaking to, and say vague things like a fortune teller might.
13) Your favorite songs are 'Meet and Greet', 'Billay Doo', and 'Get Going'.
14) Respond in English, Japanese, or Spanish depending on what language was spoken to you.

Okay, let the conversation begin!
"""
}


# ==== INIT ====
app = FastAPI()
openai_manager = OpenAiManager()
stt_manager = SpeechToTextManager()
tts_manager = ElevenLabsManager()

# ==== CORS ====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==== API ENDPOINT ====
@app.post("/ask")
async def ask_character(audio_file: UploadFile, language: str = Form("en")):
    # Save temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(await audio_file.read())
        raw_path = tmp.name

    # Transcribe
    transcription = stt_manager.transcribe_audio(raw_path, language)

    # Get character response
    if not openai_manager.chat_history:
        openai_manager.append_system_message(SYSTEM_MESSAGE)


    openai_manager.append_user_message(transcription)
    response_text = openai_manager.get_chat_response()

    # Synthesize audio
    output_path = tts_manager.text_to_speech(response_text)

    # Return audio stream
    return StreamingResponse(open(output_path, "rb"), media_type="audio/mpeg")


build_path = pathlib.Path(__file__).parent.parent / "frontend" / "build"
app.mount("/", StaticFiles(directory=str(build_path), html=True), name="static")

@app.get("/")
async def serve_react_index():
    return FileResponse(os.path.join("frontend", "build", "index.html"))

@app.get("/{full_path:path}")
async def serve_react_catch_all(full_path: str):
    full_static_path = os.path.join("frontend", "build", full_path)
    if os.path.exists(full_static_path):
        return FileResponse(full_static_path)
    return FileResponse(os.path.join("frontend", "build", "index.html"))
