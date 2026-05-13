from dependency_injector import containers, providers
from src.infrastructure.database.config.connect_db import mongodb
from src.infrastructure.database.repository.mongo_bairro_repository import MongoBairroRepository
from src.application.bairro.get_bairro_resumo.get_bairro_resumo import GetBairroResumo

class BairroContainer(containers.DeclarativeContainer):
    repository = providers.Factory(
        MongoBairroRepository,
        bairro_collection=providers.Callable(mongodb.get_collection, "bairro_indicadores"),
        setor_collection=providers.Callable(mongodb.get_collection, "setor_indicadores"),
    )

    get_resumo_use_case = providers.Singleton(
        GetBairroResumo,
        bairro_repository=repository,
    )

bairro_container = BairroContainer()