from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    log_level: str = "INFO"
    port: int = 8000

    meta_webhook_verify_token: str = ""
    meta_app_secret: str = ""
    database_url: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
