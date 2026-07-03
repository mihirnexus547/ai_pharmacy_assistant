"""
WebSocket endpoint for the AI Pharmacy Assistant.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services.conversation import conversation_service
from services.logger import logger

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint.

    Expected JSON message:

    {
        "session_id": "mihir",
        "message": "Hello"
    }
    """

    await websocket.accept()

    logger.info("WebSocket client connected.")

    try:
        while True:

            data = await websocket.receive_json()

            session_id = data.get("session_id", "default")
            message = data.get("message", "")

            logger.info(
                f"[{session_id}] USER: {message}"
            )

            response = conversation_service.chat(
                session_id=session_id,
                message=message,
            )

            await websocket.send_json(
                {
                    "response": response
                }
            )

    except WebSocketDisconnect:

        logger.info("Client disconnected.")

    except Exception as e:

        logger.exception(e)

        await websocket.send_json(
            {
                "error": str(e)
            }
        )