from dependency_injector import containers, providers

from src.application.municipio.get_municipio_resumo.get_municipio_resumo import (
    GetMunicipioResumo,
)
from src.application.municipio.list_municipios.list_municipios import ListMunicipios
from src.infrastructure.database.config.connect_db import mongodb
from src.infrastructure.database.repository.mongo_municipio_repository import (
    MongoMunicipioRepository,
)


class Container(containers.DeclarativeContainer):
    municipio_repository = providers.Factory(
        MongoMunicipioRepository,
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

    list_municipios_use_case = providers.Singleton(
        ListMunicipios,
        municipio_repository=municipio_repository,
    )

    get_municipio_resumo_use_case = providers.Singleton(
        GetMunicipioResumo,
        municipio_repository=municipio_repository,
    )


container = Container()
