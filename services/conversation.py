"""
Conversation service using LangGraph.
"""

from services.agent import agent
from services.logger import logger
from typing import Iterator
from app.config import settings

class ConversationService:
    """
    Handles conversations with the AI Pharmacy Assistant.
    """

    def chat(
        self,
        session_id: str,
        message: str,
    ) -> str:
    

    

        logger.info(
            f"[{session_id}] USER: {message}"
        )

        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "DUMMY_GEMINI_API_KEY":
            msg = (
                "Hello! I am currently unable to answer your query because the Gemini API key is not configured. "
                "Please configure a valid `GEMINI_API_KEY` in the environment variables (e.g. Railway dashboard) to activate me."
            )
            logger.warning(f"[{session_id}] ASSISTANT (API Key missing/dummy): {msg}")
            return msg

        try:

            response = agent.invoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": message,
                        }
                    ]
                },
                config={
                    "configurable": {
                        "thread_id": session_id,
                    }
                },
            )

            assistant_response = response["messages"][-1].content
          
          

            logger.info(
                f"[{session_id}] ASSISTANT: {assistant_response}"
            )

            return assistant_response

        except Exception as e:
            err_str = str(e)
            if "API key not valid" in err_str or "API_KEY_INVALID" in err_str:
                msg = (
                    "Hello! I am currently unable to answer your query because the configured Gemini API key is invalid. "
                    "Please check and update your `GEMINI_API_KEY` in the environment variables (e.g. Railway dashboard) with a valid key."
                )
                logger.error(f"[{session_id}] ASSISTANT (Invalid API Key): {msg}")
                return msg
            import traceback
            traceback.print_exc()
            raise

    def stream_chat(
        self,
        session_id: str,
        message: str,
    ):
        """
        Stream assistant response text.
        """

        logger.info(f"[{session_id}] USER: {message}")

        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "DUMMY_GEMINI_API_KEY":
            msg = (
                "Hello! I am currently unable to answer your query because the Gemini API key is not configured. "
                "Please configure a valid `GEMINI_API_KEY` in the environment variables (e.g. Railway dashboard) to activate me."
            )
            logger.warning(f"[{session_id}] ASSISTANT (API Key missing/dummy): {msg}")
            yield msg
            return

        try:

            stream = agent.stream(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": message,
                        }
                    ]
                },
                config={
                    "configurable": {
                        "thread_id": session_id,
                    }
                },
                stream_mode="messages",
            )

            for chunk, metadata in stream:

                if not chunk.content:
                    continue

                for item in chunk.content:

                    if item.get("type") == "text":

                        text = item.get("text", "")

                        if text:
                            yield text

        except Exception as e:
            err_str = str(e)
            if "API key not valid" in err_str or "API_KEY_INVALID" in err_str:
                msg = (
                    "Hello! I am currently unable to answer your query because the configured Gemini API key is invalid. "
                    "Please check and update your `GEMINI_API_KEY` in the environment variables (e.g. Railway dashboard) with a valid key."
                )
                logger.error(f"[{session_id}] ASSISTANT (Invalid API Key): {msg}")
                yield msg
                return
            logger.exception("Streaming failed.")


conversation_service = ConversationService()