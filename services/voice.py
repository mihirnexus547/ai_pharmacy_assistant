"""
Voice service.
"""

from services.conversation import conversation_service
from services.logger import logger

from providers.elevenlabs import tts


class VoiceService:

    async def process_transcript(
        self,
        session_id: str,
        transcript: str,
    ) -> str:

        transcript = transcript.strip()

        if not transcript:
            return ""

        logger.info(
            f"[VOICE] USER: {transcript}"
        )

        response = conversation_service.chat(
            session_id=session_id,
            message=transcript,
        )

        if isinstance(response, list):
            response = response[0]["text"]

        logger.info(
            f"[VOICE] ASSISTANT: {response}"
        )

        return response

    def generate_speech(
        self,
        text: str,
    ) -> bytes:

        return tts.text_to_speech(text)


voice_service = VoiceService()