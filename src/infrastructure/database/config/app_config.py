import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    raise ValueError(f"Missing required environment variable: {name}")


@dataclass
class AppConfig:
    port: int = int(os.getenv("PORT", "8000"))
    environment: str = os.getenv("ENVIRONMENT", "development")
    mongo_uri: str = _required_env("MONGO_URI")
    database_name: str = _required_env("DATABASE_NAME")
    max_page_size: int = int(os.getenv("MAX_PAGE_SIZE", "100"))
    max_offset_records: int = int(os.getenv("MAX_OFFSET_RECORDS", "50000"))
    use_estimated_total_for_unfiltered_lists: bool = (
        os.getenv("USE_ESTIMATED_TOTAL", "true").lower() == "true"
    )


config = AppConfig()
