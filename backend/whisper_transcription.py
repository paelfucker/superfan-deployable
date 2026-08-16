import os
from openai import OpenAI


class SpeechToTextManager:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY not found in environment variables!")
        self.client = OpenAI(api_key=api_key)

    def transcribe_audio(self, file_path, language=None):
        try:
            with open(file_path, "rb") as audio_file:
                kwargs = {"model": "whisper-1", "file": audio_file}
                if language:
                    kwargs["language"] = language
                transcription = self.client.audio.transcriptions.create(**kwargs)
                return transcription.text
        except Exception as e:
            print(f"[Transcription Error] {e}")
            return ""
