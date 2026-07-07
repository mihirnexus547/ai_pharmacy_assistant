import asyncio
import os
import websockets
import json

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

async def test_connect():
    url = (
        f"wss://api.deepgram.com/v1/listen"
        f"?encoding=mulaw"
        f"&sample_rate=8000"
        f"&channels=1"
        f"&interim_results=true"
        f"&punctuate=true"
        f"&smart_format=true"
        f"&endpointing=200"
        f"&utterance_end_ms=500"
    )
    try:
        ws = await websockets.connect(
            url,
            additional_headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"}
        )
        print("Connected successfully")
        await ws.close()
    except websockets.exceptions.InvalidStatus as e:
        print(f"Error {e.response.status_code}: {e.response.headers}")
        # body?
    except Exception as e:
        print(f"Other error: {e}")

asyncio.run(test_connect())
