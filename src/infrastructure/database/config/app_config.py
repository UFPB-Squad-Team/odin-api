import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


@dataclass
class AppConfig:
    port: int = int(os.getenv("PORT", "8000"))
    environment: str = os.getenv("ENVIRONMENT", "development")
    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    database_name: str = os.getenv("DATABASE_NAME", "alpargatas_insight_db")
    max_page_size: int = int(os.getenv("MAX_PAGE_SIZE", "100"))
    max_offset_records: int = int(os.getenv("MAX_OFFSET_RECORDS", "50000"))
    use_estimated_total_for_unfiltered_lists: bool = (
        os.getenv("USE_ESTIMATED_TOTAL", "true").lower() == "true"
    )


config = AppConfig()
