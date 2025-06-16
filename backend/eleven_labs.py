
import os

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

class ElevenLabsManager:
    def get_voice(self, text):
        return f"Simulated ElevenLabs audio for: {text}"
