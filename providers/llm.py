"""
Groq LLM provider.
"""

from langchain_groq import ChatGroq

from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings


def get_llm() -> ChatGoogleGenerativeAI:
    """
    Returns the configured Gemini chat model.
    """
    api_key = settings.GEMINI_API_KEY or "DUMMY_GEMINI_API_KEY"
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        api_key=api_key,
        temperature=settings.LLM_TEMPERATURE,
        max_output_tokens=settings.MAX_TOKENS,
    )