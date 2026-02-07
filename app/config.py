import os
import sys
from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    TEST_DATABASE_URL: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    PGADMIN_EMAIL: str
    PGADMIN_PASSWORD: str
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    EMAIL_ADDRESS: str
    EMAIL_SENDER: str
    EMAIL_PASSWORD: str
    FE_PW_RESET_URL: str
    # AI / GenAI settings
    class AIProviderEnum(StrEnum):
        OPENAI = "OPENAI"
        HUGGINGFACE = "HUGGINGFACE"
        MOCK = "MOCK"

    AI_PROVIDER: AIProviderEnum | None = None
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str | None = None
    # HuggingFace (free tier supported)
    HUGGINGFACE_API_KEY: str | None = None
    HUGGINGFACE_MODEL: str | None = None
    ALGORITHM: str = "HS256"
    app_name: str = "FlightsHub"
    model_config = SettingsConfigDict(env_file=str(Path(__file__).parent / "local.env"))


@lru_cache
def get_settings():
    settings = Settings()  # type: ignore
    # Force AI provider to MOCK during tests to avoid external calls
    try:
        if "PYTEST_CURRENT_TEST" in os.environ or "pytest" in sys.modules:
            settings.AI_PROVIDER = Settings.AIProviderEnum.MOCK
    except Exception:
        # If detection fails, keep existing value
        pass
    return settings


# Helper to allow tests to reload settings after changing environment vars
def reset_settings_cache():
    get_settings.cache_clear()