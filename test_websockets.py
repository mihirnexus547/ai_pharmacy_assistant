import asyncio
import json

import websockets


async def main():

    uri = "ws://127.0.0.1:8000/ws"

    async with websockets.connect(uri) as websocket:

        while True:

            message = input("You: ")

            if message.lower() == "exit":
                break

            await websocket.send(
                json.dumps(
                    {
                        "session_id": "mihir",
                        "message": message,
                    }
                )
            )

            response = await websocket.recv()

            print("Assistant:", response)


asyncio.run(main())