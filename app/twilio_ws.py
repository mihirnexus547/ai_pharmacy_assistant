"""
Router for handling Twilio inbound voice calls.
"""

import asyncio
import base64
import json
import urllib.parse
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Response
from providers.deepgram import DeepgramClient
from providers.elevenlabs import tts
from services.voice import voice_service
from services.logger import logger

router = APIRouter()

def normalize_phone(phone_str: str) -> str:
    """
    Extracts the last 10 digits of a phone number to match the database format.
    """
    digits = "".join(c for c in phone_str if c.isdigit())
    if len(digits) >= 10:
        return digits[-10:]
    return digits


@router.post("/twilio/inbound")
async def twilio_inbound(request: Request):
    """
    Twilio webhook endpoint for incoming calls.
    Returns TwiML instructing Twilio to open a WebSocket stream.
    """
    form_data = await request.form()
    caller_phone = form_data.get("From", "unknown")
    logger.info(f"[Twilio Webhook] Incoming call from: {caller_phone}")

    # Determine websocket protocol and host
    forwarded_proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    ws_scheme = "wss" if forwarded_proto == "https" else "ws"
    # request.url.netloc is the host (e.g. localhost:8000 or ngrok domain)
    caller_phone_encoded = urllib.parse.quote(caller_phone)
    stream_url = f"{ws_scheme}://{request.url.netloc}/ws/twilio?caller_phone={caller_phone_encoded}"

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{stream_url}" />
    </Connect>
</Response>"""

    return Response(content=twiml, media_type="application/xml")


@router.websocket("/ws/twilio")
async def websocket_twilio(websocket: WebSocket):
    """
    WebSocket endpoint for bidirectional audio streaming with Twilio.
    """
    await websocket.accept()
    logger.info("[Twilio WS] Connection established.")

    caller_phone = websocket.query_params.get("caller_phone", "unknown")
    phone = normalize_phone(caller_phone)

    stream_sid = None
    call_sid = None
    dg = DeepgramClient()
    await dg.connect(encoding="mulaw", sample_rate=8000)

    # State variables for managing response tasks and interruption
    response_task = None
    is_speaking = False

    async def send_audio(audio_bytes):
        nonlocal is_speaking
        if not stream_sid:
            return
        is_speaking = True
        try:
            chunk_size = 8000
            for i in range(0, len(audio_bytes), chunk_size):
                # Yield control to allow cancellation to be processed
                await asyncio.sleep(0.0)
                chunk = audio_bytes[i:i + chunk_size]
                payload = base64.b64encode(chunk).decode("utf-8")
                media_msg = {
                    "event": "media",
                    "streamSid": stream_sid,
                    "media": {
                        "payload": payload
                    }
                }
                await websocket.send_text(json.dumps(media_msg))
        except asyncio.CancelledError:
            logger.info("[Twilio WS] Audio playback cancelled (interrupted).")
            raise
        finally:
            is_speaking = False

    async def speak_response(text: str):
        try:
            # Generate the voice using ElevenLabs TTS in ulaw_8000 format
            logger.info(f"[Twilio WS] Generating speech for text: {text}")
            audio = tts.text_to_speech(text, output_format="ulaw_8000")
            logger.info(f"[Twilio WS] Generated {len(audio)} bytes of ulaw audio.")
            await send_audio(audio)
        except asyncio.CancelledError:
            logger.info("[Twilio WS] Speech generation task cancelled.")
            raise
        except Exception as e:
            logger.error(f"[Twilio WS] Error generating/sending speech: {e}")

    async def process_user_input(session_id: str, user_text: str, start_time: float = None):
        import time
        if start_time is None:
            start_time = time.perf_counter()
            
        try:
            logger.info(f"[Twilio WS] Processing transcript: {user_text}")
            
            # 1. Measure LLM Latency
            llm_start = time.perf_counter()
            response = await voice_service.process_transcript(
                session_id=session_id,
                transcript=user_text,
            )
            llm_end = time.perf_counter()
            logger.info(f"[Latency] LLM Inference + Tools took: {(llm_end - llm_start) * 1000:.2f} ms")
            
            if response:
                # 2. Measure TTS Latency
                tts_start = time.perf_counter()
                audio = tts.text_to_speech(response, output_format="ulaw_8000")
                tts_end = time.perf_counter()
                logger.info(f"[Latency] TTS Synthesis took: {(tts_end - tts_start) * 1000:.2f} ms")
                
                logger.info(f"[Latency] Total System E2E Latency: {(tts_end - start_time) * 1000:.2f} ms")
                
                await send_audio(audio)
        except asyncio.CancelledError:
            logger.info("[Twilio WS] Process user input cancelled.")
            raise
        except Exception as e:
            logger.error(f"[Twilio WS] Error in process_user_input: {e}")

    async def transcript_worker():
        nonlocal response_task
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

                if transcript:
                    # User is actively speaking. If we are speaking or planning to speak, interrupt!
                    if is_speaking or (response_task and not response_task.done()):
                        logger.info("[Twilio WS] User interruption detected! Clearing audio buffer.")
                        # Cancel the current task
                        if response_task:
                            response_task.cancel()
                        # Send clear message to Twilio
                        if stream_sid:
                            clear_msg = {
                                "event": "clear",
                                "streamSid": stream_sid
                            }
                            await websocket.send_text(json.dumps(clear_msg))

                # Append finalized fragments
                if transcript and is_final:
                    accumulated_transcript.append(transcript)

                logger.info(f"[Twilio WS] STT segment: '{transcript}' | is_final: {is_final} | speech_final: {speech_final}")

                if speech_final:
                    full_transcript = " ".join(accumulated_transcript).strip()
                    accumulated_transcript = []  # Reset for next sentence

                    if not full_transcript:
                        continue

                    # Cancel any existing response task
                    if response_task and not response_task.done():
                        response_task.cancel()

                    # Start processing user input as a new task
                    import time
                    stt_end_time = time.perf_counter()
                    session_id = call_sid if call_sid else "twilio_call"
                    response_task = asyncio.create_task(
                        process_user_input(session_id, full_transcript, stt_end_time)
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Twilio WS] Error in transcript_worker: {e}")
                break

    # Start the Deepgram transcript receiver task
    worker = asyncio.create_task(transcript_worker())

    try:
        while True:
            # Twilio sends events as text JSON frames
            message_text = await websocket.receive_text()
            data = json.loads(message_text)
            event = data.get("event")

            if event == "start":
                stream_sid = data.get("streamSid")
                call_sid = data.get("start", {}).get("callSid")
                logger.info(f"[Twilio WS] Stream started. StreamSid: {stream_sid}, CallSid: {call_sid}")

                # Trigger the initial greeting message proactively
                session_id = call_sid if call_sid else "twilio_call"
                init_msg = f"The caller has initiated the phone call. Their phone number is {phone}. Please welcome the caller. (Do not output markdown format)"
                response_task = asyncio.create_task(
                    process_user_input(session_id, init_msg)
                )

            elif event == "media":
                # Received audio from caller
                payload = data.get("media", {}).get("payload")
                if payload:
                    audio_bytes = base64.b64decode(payload)
                    await dg.send_audio(audio_bytes)

            elif event == "stop":
                logger.info(f"[Twilio WS] Stream stopped. StreamSid: {stream_sid}")
                break

    except WebSocketDisconnect:
        logger.info("[Twilio WS] Connection disconnected by Twilio.")
    except Exception as e:
        logger.error(f"[Twilio WS] Exception in Twilio WS main loop: {e}")
    finally:
        worker.cancel()
        if response_task and not response_task.done():
            response_task.cancel()
        await dg.close()
        logger.info("[Twilio WS] Cleaned up connections and tasks.")
