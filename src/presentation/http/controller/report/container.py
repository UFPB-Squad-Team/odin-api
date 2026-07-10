from dependency_injector import containers, providers

from src.infrastructure.database.config.connect_db import mongodb
from src.infrastructure.report.dossier_builder import MunicipioDossierBuilder
from src.infrastructure.report.report_data_service import ReportDataService


class Container(containers.DeclarativeContainer):
    """DI container for the report/dossier module."""

    escolas_collection = providers.Callable(
        mongodb.get_collection,
        "escolas",
    )
    municipio_collection = providers.Callable(
        mongodb.get_collection,
        "municipio_indicadores",
    )
    bairro_collection = providers.Callable(
        mongodb.get_collection,
        "bairro_indicadores",
    )

    report_data_service = providers.Singleton(
        ReportDataService,
        escolas_collection=escolas_collection,
        municipio_collection=municipio_collection,
        bairro_collection=bairro_collection,
    )

    municipio_dossier_builder = providers.Singleton(
        MunicipioDossierBuilder,
        data_service=report_data_service,
    )


container = Container()