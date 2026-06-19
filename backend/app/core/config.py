from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Short Video Copywriter"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./data/app.db"
    storage_root: Path = Path("../storage")
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    download_timeout_seconds: int = 600

    whisper_model: str = "small"
    whisper_device: str = "auto"
    whisper_compute_type: str = "auto"

    # LLM API Configuration
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: int = 120

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
