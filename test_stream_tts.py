import asyncio
from providers.elevenlabs_stream import tts_stream


async def text_generator():
    yield "Hello!"
    yield " I am your pharmacy assistant."
    yield " How can I help you today?"


async def main():
    i = 0

    async for audio in tts_stream.stream(text_generator()):
        i += 1
        print(f"Chunk {i}: {len(audio)} bytes")


asyncio.run(main())