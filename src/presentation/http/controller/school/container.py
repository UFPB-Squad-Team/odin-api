from dependency_injector import containers, providers
from src.infrastructure.database.config.connect_db import mongodb
from src.infrastructure.database.repository.mongo_stats_repository import MongoStatsRepository
from src.application.stats.get_summary_stats_use_case import GetSummaryStatsUseCase

class Container(containers.DeclarativeContainer):
    # 1. Instancia o repositório entregando a coleção (verifique se no Atlas é 'escola' ou 'escolas')
    stats_repository = providers.Factory(
        MongoStatsRepository,
        collection=providers.Callable(mongodb.get_collection, "escolas") 
    )

    # 2. Injeta o repositório no Use Case usando EXATAMENTE o mesmo nome
    get_summary_stats_use_case = providers.Singleton(
        GetSummaryStatsUseCase,
        repository=stats_repository
    )

container = Container()