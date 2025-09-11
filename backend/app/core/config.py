"""Application settings module."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly typed runtime settings."""

    model_config = SettingsConfigDict(env_file=".env.example", case_sensitive=False)

    app_name: str = "Spatial-Temporal Risk Intelligence Engine"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_url: str
    redis_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    rate_limit_public: str = "60/minute"
    rate_limit_analyst: str = "240/minute"
    rate_limit_admin: str = "600/minute"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings object."""
    return Settings()
