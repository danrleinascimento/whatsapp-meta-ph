from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_role: Literal["hub", "agent"] = "hub"
    app_env: str = "development"
    log_level: str = "INFO"
    port: int = 8000
    bind_host: str = "0.0.0.0"

    meta_webhook_verify_token: str = ""
    meta_app_secret: str = ""
    database_url: str = ""

    # Agent / local
    ph_api_key: str = ""
    token_encryption_key: str = ""
    panel_ticket_secret: str = ""
    phsftw_root: str = r"C:\PHSFTW"
    graph_api_version: str = "v25.0"
    hub_base_url: str = "https://whatsapp-meta-ph-wzewk.ondigitalocean.app"
    hub_pull_secret: str = ""
    installation_id: str = "local-dev"
    poll_interval_seconds: int = 10
    batch_delay_seconds: float = 0.05
    pair_rate_min_seconds: float = 6.0

    # Seed / dev PH Softwares (nunca logar o token)
    meta_access_token: str = ""
    meta_phone_number_id: str = ""
    meta_waba_id: str = ""
    meta_display_phone: str = ""
    meta_app_id: str = ""
    meta_embedded_signup_config_id: str = ""
    diretorio_principal: str = ""
    diretorio_secundario: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
