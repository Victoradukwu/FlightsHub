from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    app_name: str = "FlightsHub"
    model_config = SettingsConfigDict(env_file="local.env")


@lru_cache
def get_settings():
    return Settings()