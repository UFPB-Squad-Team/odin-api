from src.infrastructure.report.dossier_builder import MunicipioDossierBuilder
from src.infrastructure.report.report_data_service import ReportDataService
from src.presentation.http.controller.report.container import container


def get_municipio_dossier_builder() -> MunicipioDossierBuilder:
    return container.municipio_dossier_builder()


def get_report_data_service() -> ReportDataService:
    return container.report_data_service()
