import os
import json
import asyncio
import websockets

from dotenv import load_dotenv
import base64

load_dotenv()


class ElevenLabsStreaming:

    def __init__(self):

        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID")

    async def stream(
        self,
        text_stream,
    ):
        """
        Streams audio chunks from ElevenLabs.
        """

        uri = (
            f"wss://api.elevenlabs.io/v1/text-to-speech/"
            f"{self.voice_id}/stream-input"
            "?model_id=eleven_flash_v2_5"
        )

        async with websockets.connect(uri) as ws:

            await ws.send(
                json.dumps(
                    {
                        "xi_api_key": self.api_key,
                        "voice_settings": {
                            "stability": 0.4,
                            "similarity_boost": 0.8,
                        },
                    }
                )
            )

            async def sender():

                async for text in text_stream:

                    if text.strip():

                        await ws.send(
                            json.dumps(
                                {
                                    "text": text,
                                    "try_trigger_generation": True,
                                }
                            )
                        )

                await ws.send(
                    json.dumps({"text": ""})
                )

            async def receiver():

                while True:

                    message = json.loads(
                        await ws.recv()
                    )
                    print(message)

                    if "audio" in message:

                        yield base64.b64decode(message["audio"])

                    if message.get("isFinal"):

                        break

            sender_task = asyncio.create_task(
                sender()
            )

            async for audio in receiver():

                yield audio

            await sender_task


tts_stream = ElevenLabsStreaming()