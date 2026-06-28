from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Short Video Copywriter"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./data/app.db"
    storage_root: Path = Path("../storage")
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001", "http://localhost:3002", "http://127.0.0.1:3002"])
    download_timeout_seconds: int = 600

    whisper_model: str = "small"
    whisper_device: str = "auto"
    whisper_compute_type: str = "auto"

    # LLM API Configuration
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: int = 120

    # YouTube Cookie Configuration (optional)
    # Export cookies from browser using extension like "Get cookies.txt LOCALLY"
    # Save as Netscape format and place path here
    youtube_cookies_file: str = ""

    # Browser cookie extraction (optional)
    # Auto-extract cookies from browser for platforms that need them (Douyin, etc.)
    # Supported values: "chrome", "edge", "firefox", "brave", "chromium", "opera"
    # Leave empty to disable; requires having logged into the target site in that browser
    browser_cookies: str = ""

    # Manual cookies file (optional, fallback when browser extraction fails)
    # Export cookies using browser extension "Get cookies.txt LOCALLY" (Netscape format)
    # Works for all platforms (Douyin, Bilibili, etc.)
    cookies_file: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
