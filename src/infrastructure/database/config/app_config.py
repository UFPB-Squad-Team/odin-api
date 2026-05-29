"""
Application configuration using pydantic-settings.
Loads from environment variables with validation and type coercion.
"""

from typing import Any, cast

from pydantic import field_validator
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server
    port: int = 8000
    environment: str = "development"
    log_level: str = "info"

    # Database
    mongo_uri: str
    database_name: str

    # Pagination
    max_page_size: int = 100
    max_offset_records: int = 50000
    use_estimated_total_for_unfiltered_lists: bool = True

    # CORS
    cors_allowed_origins: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        """Parse comma-separated CORS origins."""
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}, got '{v}'")
        return v

    model_config = {
        "env_prefix": "",
        "case_sensitive": False,
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton config instance
config = cast(Any, AppConfig)()
