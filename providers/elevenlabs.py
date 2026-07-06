"""
ElevenLabs Text-to-Speech provider.
"""

import os

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()


class ElevenLabsProvider:

    def __init__(self):

        self.client = ElevenLabs(
            api_key=os.getenv("ELEVENLABS_API_KEY")
        )

        self.voice_id = os.getenv(
            "ELEVENLABS_VOICE_ID"
        )

    def text_to_speech(
        self,
        text: str,
        output_format: str = "mp3_44100_128",
    ) -> bytes:
        """
        Generate complete speech.
        """

        audio = self.client.text_to_speech.convert(

            voice_id=self.voice_id,

            model_id="eleven_flash_v2_5",

            text=text,

            output_format=output_format,

        )

        return b"".join(audio)

    def stream_text_to_speech(
        self,
        text: str,
        output_format: str = "mp3_44100_128",
    ):
        """
        Stream speech chunks.
        """

        audio_stream = self.client.text_to_speech.convert(

            voice_id=self.voice_id,

            model_id="eleven_flash_v2_5",

            text=text,

            output_format=output_format,

        )

        for chunk in audio_stream:

            if chunk:

                yield chunk


tts = ElevenLabsProvider()