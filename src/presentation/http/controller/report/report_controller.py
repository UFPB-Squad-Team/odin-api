import logging

from fastapi import APIRouter, Depends, HTTPException, Path, status

from src.infrastructure.report.dossier_builder import MunicipioDossierBuilder
from src.infrastructure.report.report_data_service import ReportDataService
from src.presentation.http.controller.report.callable.report_callable import (
    get_municipio_dossier_builder,
    get_report_data_service,
)
from src.presentation.http.owned_stream import OwnedStreamResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/municipios/{municipio_id}/dossie",
    tags=["relatorios", "municipios"],
    summary="Gera dossiê do município em PDF",
    description=(
        "Gera um dossiê completo do município em formato PDF, "
        "contendo indicadores educacionais, infraestrutura, "
        "distribuição das escolas, ranking IDEB e contexto socioeconômico. "
        "O PDF é gerado em memória e transmitido como stream (download automático)."
    ),
)
async def generate_municipio_dossier(
    municipio_id: str = Path(
        ...,
        min_length=7,
        max_length=7,
        pattern=r"^\d{7}$",
        description="Código IBGE do município com 7 dígitos.",
    ),
    builder: MunicipioDossierBuilder = Depends(get_municipio_dossier_builder),
):
    """Generate a municipio dossier PDF and stream it to the client."""
    pdf_stream = await builder.build(municipio_id)

    if pdf_stream is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Município não encontrado. Verifique o código IBGE de 7 dígitos.",
        )

    filename = f"dossie_municipio_{municipio_id}.pdf"

    return OwnedStreamResponse(
        pdf_stream,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "application/pdf",
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )


@router.get(
    "/relatorios/municipios/{municipio_id}/dossie",
    tags=["relatorios"],
    summary="Gera dossiê do município em PDF (alias)",
    description="Alias para /municipios/{municipio_id}/dossie",
    include_in_schema=True,
)
async def generate_municipio_dossier_alias(
    municipio_id: str = Path(
        ...,
        min_length=7,
        max_length=7,
        pattern=r"^\d{7}$",
        description="Código IBGE do município com 7 dígitos.",
    ),
    builder: MunicipioDossierBuilder = Depends(get_municipio_dossier_builder),
):
    """Alias route for municipio dossier generation."""
    return await generate_municipio_dossier(municipio_id, builder)


@router.get(
    "/estados/{sg_uf}/dossie",
    tags=["relatorios", "estados"],
    summary="Gera dossiê do estado em PDF",
    description=(
        "Gera um dossiê completo do estado em formato PDF, "
        "contendo indicadores educacionais agregados, infraestrutura, "
        "distribuição das escolas e ranking dos municípios por IDEB. "
        "O PDF é gerado em memória e transmitido como stream (download automático)."
    ),
)
async def generate_state_dossier(
    sg_uf: str = Path(
        ...,
        min_length=2,
        max_length=2,
        pattern=r"^[A-Za-z]{2}$",
        description="Sigla da UF (ex: PB, PE, CE).",
    ),
    data_service: ReportDataService = Depends(get_report_data_service),
):
    """Generate a state dossier PDF and stream it to the client."""
    uf = sg_uf.upper()
    from src.infrastructure.report.state_pdf import render_state_dossier
    from src.infrastructure.resources import pdf_renderer

    pdf_stream = await pdf_renderer.run(
        render_state_dossier, prepare=lambda: data_service.get_state_dossier_data(uf)
    )
    if pdf_stream is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estado {uf} não encontrado ou sem dados disponíveis.",
        )

    filename = f"dossie_estado_{uf}.pdf"

    return OwnedStreamResponse(
        pdf_stream,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "application/pdf",
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )
