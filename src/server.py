import uvicorn
from src.infrastructure.database.config.app_config import config

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=config.port,
        reload=config.environment == "development"
    )
