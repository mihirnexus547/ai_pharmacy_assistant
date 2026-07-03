"""
WebSocket endpoint for browser voice chat.
"""

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from providers.deepgram import DeepgramClient
from services.voice import voice_service

router = APIRouter()


@router.websocket("/ws/audio")
async def websocket_audio(websocket: WebSocket, session_id: str = "browser"):

    await websocket.accept()

    print("Browser connected")

    dg = DeepgramClient()
    await dg.connect()

    async def transcript_worker():
        accumulated_transcript = []
        while True:
            try:
                message = await dg.get_message()
                if "channel" not in message:
                    continue

                alternatives = message["channel"]["alternatives"]
                if not alternatives:
                    continue

                transcript = alternatives[0]["transcript"]
                is_final = message.get("is_final", False)
                speech_final = message.get("speech_final", False)

                # Append finalized fragments
                if transcript and is_final:
                    accumulated_transcript.append(transcript)

                print(f"STT segment: '{transcript}' | is_final: {is_final} | speech_final: {speech_final}")

                # If Deepgram signals silence/endpointing is reached
                if speech_final:
                    full_transcript = " ".join(accumulated_transcript).strip()
                    accumulated_transcript = []  # Reset for next sentence

                    if not full_transcript:
                        continue

                    print(f"Processing final voice transcript: '{full_transcript}'")

                    # User finished speaking
                    response = await voice_service.process_transcript(
                        session_id=session_id,
                        transcript=full_transcript,
                    )

                    if not response:
                        continue

                    # Send assistant text
                    await websocket.send_json(
                        {
                            "type": "assistant",
                            "text": response,
                        }
                    )

                    # Generate ONE MP3
                    audio = voice_service.generate_speech(response)

                    print(
                        "Generated audio:",
                        len(audio),
                        "bytes",
                    )

                    # Send ONE MP3
                    await websocket.send_bytes(audio)
                    continue

                # Send intermediate preview to browser
                preview_parts = list(accumulated_transcript)
                if transcript and not is_final:
                    preview_parts.append(transcript)
                preview_text = " ".join(preview_parts).strip()
                if preview_text:
                    await websocket.send_json(
                        {
                            "type": "transcript",
                            "text": preview_text,
                        }
                    )

            except Exception as e:
                print("Error in transcript_worker:", e)
                try:
                    await websocket.close()
                except Exception:
                    pass
                break

    worker = asyncio.create_task(
        transcript_worker()
    )



    try:

        while True:

            audio = await websocket.receive_bytes()

            await dg.send_audio(audio)

    except WebSocketDisconnect:

        print("Browser disconnected")

    finally:

        worker.cancel()

        await dg.close()