from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    ALGORITHM: str = "HS256"
    app_name: str = "FlightsHub"
    model_config = SettingsConfigDict(env_file=str(Path(__file__).parent / "local.env"))


@lru_cache
def get_settings():
    return Settings() # type: ignore