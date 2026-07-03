"""
Application configuration.

Loads all environment variables from the `.env` file using
Pydantic Settings and exposes a singleton `settings`
object for use throughout the application.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    # ==========================
    # Application
    # ==========================
    APP_NAME: str = "AI Pharmacy Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ==========================
    # Database
    # ==========================
    DATABASE_URL: str = Field(...)

    # ==========================
    # LLM
    # ==========================
    GEMINI_API_KEY: str = Field(...)
    GROQ_API_KEY: str = ""

    GEMINI_MODEL: str = "gemini-3.1-pro-preview"


    LLM_TEMPERATURE: float = 0.2

    MAX_TOKENS: int = 512

    # ==========================
    # STT (Optional for now)
    # ==========================
    DEEPGRAM_API_KEY: str = ""

    # ==========================
    # TTS (Optional for now)
    # ==========================
    ELEVENLABS_API_KEY: str = ""

    # ==========================
    # Logging
    # ==========================
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    """
    return Settings()


settings = get_settings()