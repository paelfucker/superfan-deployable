import openai
import os

class SpeechToTextManager:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise EnvironmentError("OPENAI_API_KEY not found in environment variables!")

    def transcribe_audio(self, file_path, language=None):
        try:
            with open(file_path, "rb") as audio_file:
                transcription = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    language=language,  # optional: "en", "es", "ja", etc.
                )
                return transcription["text"]
        except Exception as e:
            print(f"[Transcription Error] {e}")
            return ""
