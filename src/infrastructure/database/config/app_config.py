"""
Application configuration using pydantic-settings.
Loads from environment variables with validation and type coercion.
"""

from pathlib import Path
from typing import Any, cast

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

# Load .env file explicitly from API root directory
env_file = Path(__file__).resolve().parent.parent.parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file, override=True)


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
    max_page_size: int = 500
    max_offset_records: int = 50000
    use_estimated_total_for_unfiltered_lists: bool = True

    # Aggregation cache (in-memory, TTL-based)
    aggregation_cache_ttl_seconds: int = 300
    aggregation_cache_max_keys: int = 512

    # Resource budgets for the 512 MB service
    mongo_max_pool_size: int = Field(default=10, ge=1)
    response_cache_max_bytes: int = Field(default=16 * 1024 * 1024, ge=0)
    response_cache_max_entry_bytes: int = Field(default=1024 * 1024, ge=0)
    response_max_flights: int = Field(default=32, ge=1)
    geo_concurrency: int = Field(default=2, ge=1)
    gzip_enabled: bool = False

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
