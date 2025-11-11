from fastapi import FastAPI
from src.infrastructure.database.config.app_config import config
from src.presentation.http.controller.school.container import container
from src.presentation.http.controller.school.index import (
    router as school_controller,
)
from src.infrastructure.database.config.connect_db import mongodb
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

container.wire(modules=[
        "src.presentation.http.controller.school.list_all_schools_controller"
])


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(
        f"Server is starting on port {config.port} "
        f"in {config.environment}"
    )

    print(f"Documentation: http://localhost:{config.port}/docs")

    success = await mongodb.connect()
    if not success:
        raise RuntimeError("Failed to connect to database")

    yield

    await mongodb.disconnect()
    print("Server shutdown")

app = FastAPI(
    title="Odin Backend API",
    description="Backend para gerenciamento de processos de dados escolares",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(school_controller, prefix="/api/v1", tags=["schools"])
