import os
from dataclasses import dataclass


@dataclass
class AppConfig:
    port: int = int(os.getenv("PORT", "8000"))
    environment: str = os.getenv("ENVIRONMENT", "development")
    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:5000")
    database_name: str = os.getenv("DATABASE_NAME", "alpargatas_insight_db")


config = AppConfig()
