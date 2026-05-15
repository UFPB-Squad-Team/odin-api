from dependency_injector import containers, providers

from src.application.state.get_state_summary.get_state_summary import GetStateSummaryUseCase
from src.infrastructure.database.config.connect_db import mongodb
from src.infrastructure.database.repository.mongo_state_repository import MongoStateRepository

class Container(containers.DeclarativeContainer):
    
    
    state_repository = providers.Factory(
        MongoStateRepository,
        municipio_collection=providers.Callable(
            mongodb.get_collection,
            "municipio_indicadores",
        )
    )

    
    get_state_summary_use_case = providers.Singleton(
        GetStateSummaryUseCase,
        state_repository=state_repository,
    )

container = Container()