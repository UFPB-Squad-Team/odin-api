from dependency_injector import containers, providers

from src.application.aggregation.get_city_aggregations import GetCityAggregations
from src.application.aggregation.get_neighborhood_aggregations import (
    GetNeighborhoodAggregations,
)
from src.infrastructure.database.config.connect_db import mongodb
from src.infrastructure.database.repository.mongo_territorial_aggregation_repository import (
    MongoTerritorialAggregationRepository,
)


class Container(containers.DeclarativeContainer):
    territorial_repository = providers.Factory(
        MongoTerritorialAggregationRepository,
        municipio_collection=providers.Callable(
            mongodb.get_collection,
            "municipio_indicadores",
        ),
        bairro_collection=providers.Callable(
            mongodb.get_collection,
            "bairro_indicadores",
        ),
        setor_collection=providers.Callable(
            mongodb.get_collection,
            "setor_indicadores",
        ),
    )

    get_city_aggregations_use_case = providers.Singleton(
        GetCityAggregations,
        repository=territorial_repository,
    )

    get_neighborhood_aggregations_use_case = providers.Singleton(
        GetNeighborhoodAggregations,
        repository=territorial_repository,
    )


container = Container()
