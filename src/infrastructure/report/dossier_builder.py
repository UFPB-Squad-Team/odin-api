from __future__ import annotations

import io
import logging

from src.infrastructure.report.report_data_service import ReportDataService

logger = logging.getLogger(__name__)


class MunicipioDossierBuilder:
    def __init__(self, data_service: ReportDataService) -> None:
        self._data_service = data_service

    async def build(self, municipio_id: str) -> io.BytesIO | None:
        logger.info("Building dossier for municipio %s", municipio_id)
        from src.infrastructure.resources import pdf_renderer

        return await pdf_renderer.run(
            _render_municipio,
            prepare=lambda: self._data_service.get_municipio_dossier_data(municipio_id),
        )


class StateDossierBuilder:
    def __init__(self, data_service: ReportDataService) -> None:
        self._data_service = data_service

    async def build(self, uf: str) -> io.BytesIO | None:
        logger.info("Building dossier for state %s", uf)
        from src.infrastructure.resources import pdf_renderer

        return await pdf_renderer.run(
            _render_state,
            prepare=lambda: self._data_service.get_state_dossier_data(uf),
        )


def _render_municipio(data):
    from src.infrastructure.report.pdf_generator import DossierPDF

    return DossierPDF(data).render()


def _render_state(data):
    from src.infrastructure.report.pdf_generator import StateDossierPDF

    return StateDossierPDF(data).render()
