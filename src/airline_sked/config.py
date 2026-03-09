"""애플리케이션 설정."""

from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = f"sqlite+aiosqlite:///{DATA_DIR / 'airline_sked.db'}"
    telegram_bot_token: str = ""
    telegram_admin_chat_id: str = ""
    discord_bot_token: str = ""
    discord_channel_id: str = ""
    scrape_interval_hours: int = 24
    scrape_user_agent: str = "airline-sked/0.1 (schedule-monitor)"
    scrape_request_delay_sec: float = 2.0
    scrape_browser_headless: bool = True
    scrape_browser_timeout_ms: int = 60000
    scrape_browser_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"


settings = Settings()
