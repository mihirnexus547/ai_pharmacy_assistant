"""
Deepgram Live Speech-to-Text Provider.
"""

from database import database
import asyncio
import json
import os

import websockets
from dotenv import load_dotenv

load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")


class DeepgramClient:

    def __init__(self):

        self.websocket = None

        self.transcript_queue = asyncio.Queue()

    async def connect(self):

        url = (
            "wss://api.deepgram.com/v1/listen"
            "?encoding=linear16"
            "&sample_rate=16000"
            "&channels=1"
            "&interim_results=true"
            "&punctuate=true"
            "&smart_format=true"
            "&endpointing=200"
        )


        self.websocket = await websockets.connect(
            url,
            additional_headers={
                "Authorization": f"Token {DEEPGRAM_API_KEY}",
            },
        )

        asyncio.create_task(
            self._receive_loop()
        )

    async def send_audio(
        self,
        audio: bytes,
    ):

        if self.websocket:

            await self.websocket.send(audio)

    async def _receive_loop(self):
        try:
            async for message in self.websocket:
                data = json.loads(message)
                try:
                    if "channel" in data:
                        await self.transcript_queue.put(data)
                except Exception:
                    pass
        finally:
            await self.transcript_queue.put(None)

    async def get_message(self):
        msg = await self.transcript_queue.get()
        if msg is None:
            raise Exception("Deepgram connection closed")
        return msg


    async def close(self):

        if self.websocket:

            await self.websocket.close()