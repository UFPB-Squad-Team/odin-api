from dependency_injector import containers, providers

from src.application.search.universal_search.universal_search_use_case import (
    UniversalSearchUseCase,
)
from src.infrastructure.database.config.connect_db import mongodb
from src.infrastructure.database.repository.mongo_universal_search_repository import (
    MongoUniversalSearchRepository,
)


class Container(containers.DeclarativeContainer):
    search_repository = providers.Factory(
        MongoUniversalSearchRepository,
        escolas_collection=providers.Callable(mongodb.get_collection, "escolas"),
        municipio_collection=providers.Callable(
            mongodb.get_collection,
            "municipio_indicadores",
        ),
        bairro_collection=providers.Callable(
            mongodb.get_collection,
            "bairro_indicadores",
        ),
    )

    universal_search_use_case = providers.Singleton(
        UniversalSearchUseCase,
        repository=search_repository,
    )


container = Container()
