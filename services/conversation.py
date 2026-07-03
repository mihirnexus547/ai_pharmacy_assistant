"""
Conversation service using LangGraph.
"""

from services.agent import agent
from services.logger import logger
from typing import Iterator

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

        except Exception:
            logger.exception("Streaming failed.")


conversation_service = ConversationService()