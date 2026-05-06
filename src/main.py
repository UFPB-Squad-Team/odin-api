from fastapi import FastAPI
from src.infrastructure.database.config.app_config import config
from src.presentation.http.controller.school.container import container as school_container
from src.presentation.http.controller.school.index import (
    router as school_controller,
)
from src.presentation.http.controller.aggregation.container import (
    container as aggregation_container,
)
from src.presentation.http.controller.aggregation.index import (
    router as aggregation_controller,
)
from src.infrastructure.database.config.connect_db import mongodb
from src.presentation.http.middleware.global_exception_handler import (
    register_global_exception_handlers,
)
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from src.presentation.http.controller.school.stats.stats_controller import router as stats_router

load_dotenv()
school_container.wire(modules=[
    "src.presentation.http.controller.school.list_all_schools_controller",
    "src.presentation.http.controller.school.get_school_by_id_controller",
    "src.presentation.http.controller.school.geojson_controller",
    "src.presentation.http.controller.school.stats.stats_controller" 
])

aggregation_container.wire(modules=[
    "src.presentation.http.controller.aggregation.aggregations_controller",
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

register_global_exception_handlers(app)

app.include_router(school_controller, prefix="/api/v1", tags=["schools"])
app.include_router(aggregation_controller, prefix="/api/v1", tags=["aggregations"])
app.include_router(stats_router, prefix="/api/v1", tags=["stats"])