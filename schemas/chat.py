"""
Request and response schemas.
"""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """
    Incoming chat request.
    """

    session_id: str
    message: str


class ChatResponse(BaseModel):
    """
    Outgoing chat response.
    """

    response: str