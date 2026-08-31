"""Settings. Everything that differs between machines comes from the environment."""
from __future__ import annotations

import secrets
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LANGRAM_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///langram.db"
    # Generated per process when unset, which is fine for local work and would
    # log every learner out on restart in production. Set it there.
    secret_key: str = ""
    access_token_hours: int = 24 * 14
    item_token_minutes: int = 60
    cors_origins: list[str] = ["http://localhost:5173"]

    def resolved_secret(self) -> str:
        return self.secret_key or _ephemeral_secret()


@lru_cache(maxsize=1)
def _ephemeral_secret() -> str:
    return secrets.token_urlsafe(48)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
