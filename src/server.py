import uvicorn
from src.infrastructure.database.config.app_config import config


def run() -> None:
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=config.port,
        reload=config.environment == "development",
    )


if __name__ == "__main__":
    run()
