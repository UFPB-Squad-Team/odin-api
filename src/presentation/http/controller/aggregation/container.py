from dependency_injector import containers, providers

from src.application.aggregation.get_city_aggregations import GetCityAggregations
from src.application.aggregation.get_neighborhood_aggregations import (
    GetNeighborhoodAggregations,
)
from src.infrastructure.cache.aggregation_cache import AggregationCache
from src.infrastructure.database.config.app_config import config
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

    # Shared in-memory cache (per worker process). Both use cases are
    # Singletons, so a single cache instance serves all aggregation calls.
    aggregation_cache = providers.Singleton(
        AggregationCache,
        ttl_seconds=config.aggregation_cache_ttl_seconds,
        max_keys=config.aggregation_cache_max_keys,
    )

    get_city_aggregations_use_case = providers.Singleton(
        GetCityAggregations,
        repository=territorial_repository,
        cache=aggregation_cache,
    )

    get_neighborhood_aggregations_use_case = providers.Singleton(
        GetNeighborhoodAggregations,
        repository=territorial_repository,
        cache=aggregation_cache,
    )


container = Container()
