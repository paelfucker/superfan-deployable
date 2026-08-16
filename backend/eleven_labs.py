import os
from io import BytesIO
from elevenlabs import ElevenLabs


class ElevenLabsManager:
    def __init__(self):
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise EnvironmentError("ELEVENLABS_API_KEY not found in environment variables!")

        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID")
        if not self.voice_id:
            raise EnvironmentError("ELEVENLABS_VOICE_ID not found in environment variables!")

        self.client = ElevenLabs(api_key=api_key)

    def text_to_audio_stream(self, input_text):
        audio_stream = self.client.text_to_speech.convert(
            text=input_text,
            voice_id=self.voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )
        audio_data = b"".join(audio_stream)
        return BytesIO(audio_data)

    def text_to_audio(self, input_text, save_as_wave=False, subdirectory=""):
        audio_stream = self.client.text_to_speech.convert(
            text=input_text,
            voice_id=self.voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )
        audio_data = b"".join(audio_stream)
        file_name = f"___Msg{str(hash(input_text))}.mp3"
        tts_file = os.path.join(os.path.abspath(os.curdir), subdirectory, file_name)
        with open(tts_file, "wb") as f:
            f.write(audio_data)
        return tts_file
