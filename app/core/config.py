from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    app_name: str = "Guide Cluster API"
    database_url: str = "postgresql+psycopg://guide:guide_dev_password@localhost:5432/guide_cluster"
    sql_echo: bool = False
    bilibili_api_base_url: str = "https://api.bilibili.com"
    bilibili_request_timeout_seconds: float = Field(default=15.0, gt=0, le=60)
    bilibili_trust_env: bool = True
    bilibili_cookie: str | None = Field(default=None, repr=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
