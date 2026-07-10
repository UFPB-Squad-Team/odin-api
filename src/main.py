import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.database.config.app_config import config
from src.infrastructure.database.config.connect_db import mongodb
from src.presentation.http.controller.aggregation.container import (
    container as aggregation_container,
)
from src.presentation.http.controller.aggregation.index import (
    router as aggregation_controller,
)
from src.presentation.http.controller.bairro.container import bairro_container
from src.presentation.http.controller.bairro.index import router as bairro_controller
from src.presentation.http.controller.health import router as health_router
from src.presentation.http.controller.municipio.container import (
    container as municipio_container,
)
from src.presentation.http.controller.municipio.index import (
    router as municipio_controller,
)
from src.presentation.http.controller.report.index import router as report_controller
from src.presentation.http.controller.school.container import (
    container as school_container,
)
from src.presentation.http.controller.school.index import router as school_controller
from src.presentation.http.controller.school.stats.stats_controller import (
    router as stats_router,
)
from src.presentation.http.controller.search.container import (
    container as search_container,
)
from src.presentation.http.controller.search.index import router as search_controller
from src.presentation.http.controller.state.container import (
    container as state_container,
)
from src.presentation.http.controller.state.index import router as state_controller
from src.presentation.http.middleware.global_exception_handler import (
    register_global_exception_handlers,
)
from src.presentation.http.middleware.request_id_middleware import (
    RequestIDMiddleware,
)


def setup_logging() -> None:
    """Configure structured logging for the application."""
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)


setup_logging()
logger = logging.getLogger(__name__)


school_container.wire(
    modules=[
        "src.presentation.http.controller.school.list_all_schools_controller",
        "src.presentation.http.controller.school.get_school_by_id_controller",
        "src.presentation.http.controller.school.geojson_controller",
        "src.presentation.http.controller.school.stats.stats_controller",
    ]
)

aggregation_container.wire(
    modules=[
        "src.presentation.http.controller.aggregation.aggregations_controller",
    ]
)

municipio_container.wire(
    modules=[
        "src.presentation.http.controller.municipio.municipios_controller",
    ]
)

bairro_container.wire(
    modules=[
        "src.presentation.http.controller.bairro.bairro_controller",
    ]
)

search_container.wire(
    modules=[
        "src.presentation.http.controller.search.universal_search_controller",
    ]
)

state_container.wire(
    modules=[
        "src.presentation.http.controller.state.get_state_summary_controller",
        "src.presentation.http.controller.state.list_states_controller",
    ]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle."""
    logger.info(
        "Starting Odin API | port=%s | env=%s",
        config.port,
        config.environment,
    )

    success = await mongodb.connect()
    if not success:
        logger.critical("Failed to connect to database — aborting startup")
        raise RuntimeError("Failed to connect to database")

    logger.info("Application ready to serve requests")
    yield

    await mongodb.disconnect()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="Odin Backend API",
    description="Backend para gerenciamento de processos de dados escolares",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if not config.is_production else None,
    redoc_url="/redoc" if not config.is_production else None,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.add_middleware(RequestIDMiddleware)

register_global_exception_handlers(app)


app.include_router(health_router)
app.include_router(state_controller, prefix="/api/v1", tags=["estados"])
app.include_router(municipio_controller, prefix="/api/v1", tags=["municipios"])
app.include_router(school_controller, prefix="/api/v1", tags=["schools"])
app.include_router(bairro_controller, prefix="/api/v1", tags=["bairros"])
app.include_router(search_controller, prefix="/api/v1", tags=["busca"])
app.include_router(aggregation_controller, prefix="/api/v1", tags=["aggregations"])
app.include_router(stats_router, prefix="/api/v1", tags=["stats"])
app.include_router(report_controller, prefix="/api/v1", tags=["relatorios"])
