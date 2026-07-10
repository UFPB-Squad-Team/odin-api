from __future__ import annotations

import io
import logging

from src.domain.entities.report import MunicipioDossierData, StateDossierData
from src.infrastructure.report.pdf_generator import DossierPDF as MunicipioDossierPDF
from src.infrastructure.report.pdf_generator import StateDossierPDF
from src.infrastructure.report.report_data_service import ReportDataService

logger = logging.getLogger(__name__)


class MunicipioDossierBuilder:
    def __init__(self, data_service: ReportDataService) -> None:
        self._data_service = data_service

    async def build(self, municipio_id: str) -> io.BytesIO | None:
        logger.info("Building dossier for municipio %s", municipio_id)
        data = await self._data_service.get_municipio_dossier_data(municipio_id)
        if data is None:
            return None

        pdf = MunicipioDossierPDF(data)
        return pdf.render()


class StateDossierBuilder:
    def __init__(self, data_service: ReportDataService) -> None:
        self._data_service = data_service

    async def build(self, uf: str) -> io.BytesIO | None:
        logger.info("Building dossier for state %s", uf)
        data = await self._data_service.get_state_dossier_data(uf)
        if data is None:
            return None

        pdf = StateDossierPDF(data)
        return pdf.render()
