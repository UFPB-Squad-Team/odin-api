import logging

from fastapi import APIRouter, Depends, HTTPException, Path, status
from fastapi.responses import StreamingResponse

from src.infrastructure.report.dossier_builder import MunicipioDossierBuilder
from src.infrastructure.report.report_data_service import ReportDataService
from src.presentation.http.controller.report.callable.report_callable import (
    get_municipio_dossier_builder,
    get_report_data_service,
)

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

    return StreamingResponse(
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
    from src.infrastructure.report.chart_generator import (
        generate_bar_chart,
        generate_horizontal_bar_chart,
        generate_pie_chart,
    )
    from src.infrastructure.report.pdf_generator import DossierPDF

    uf = sg_uf.upper()
    state_data = await data_service.get_state_dossier_data(uf)

    if state_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estado {uf} não encontrado ou sem dados disponíveis.",
        )

    # Build a municipio-like data structure for the PDF generator
    # (reusing the same DossierPDF class with adapted data)
    from src.domain.entities.report import MunicipioDossierData

    adapted_data = MunicipioDossierData(
        municipio_id=uf,
        municipio_nome=state_data.estado_nome,
        uf=state_data.uf,
        total_escolas=state_data.total_escolas,
        total_alunos=state_data.total_alunos,
        total_bairros=state_data.total_municipios,
        taxa_aprovacao_media=state_data.taxa_aprovacao_media,
        taxa_reprovacao_media=state_data.taxa_reprovacao_media,
        ideb_medio=state_data.ideb_medio,
        pct_internet=state_data.pct_internet,
        pct_biblioteca=state_data.pct_biblioteca,
        pct_lab_informatica=state_data.pct_lab_informatica,
        pct_acessibilidade=state_data.pct_acessibilidade,
        escolas_por_dependencia=state_data.escolas_por_dependencia,
        escolas_por_zona=state_data.escolas_por_zona,
        top_escolas=[
            {
                "nome": m["nome"],
                "ideb": m["ideb"],
                "dependencia": "",
                "localizacao": "",
            }
            for m in state_data.top_municipios
        ],
    )

    pdf = DossierPDF(adapted_data)

    # Generate charts
    infra_labels, infra_values = [], []
    for label, val in [
        ("Internet", state_data.pct_internet),
        ("Biblioteca", state_data.pct_biblioteca),
        ("Lab. Informática", state_data.pct_lab_informatica),
        ("Acessibilidade", state_data.pct_acessibilidade),
    ]:
        if val is not None:
            infra_labels.append(label)
            infra_values.append(val)

    if infra_labels:
        chart = generate_bar_chart(
            labels=infra_labels,
            values=infra_values,
            title="Infraestrutura Escolar",
            ylabel="Percentual de Escolas (%)",
        )
        pdf.add_chart("infra_bars", chart)

    if state_data.escolas_por_dependencia:
        dep_labels = list(state_data.escolas_por_dependencia.keys())
        dep_values = [float(v) for v in state_data.escolas_por_dependencia.values()]
        chart = generate_pie_chart(
            labels=dep_labels,
            values=dep_values,
            title="Dependência Administrativa",
        )
        pdf.add_chart("dependencia_pie", chart)

    if state_data.escolas_por_zona:
        zona_labels = list(state_data.escolas_por_zona.keys())
        zona_values = [float(v) for v in state_data.escolas_por_zona.values()]
        chart = generate_pie_chart(
            labels=zona_labels,
            values=zona_values,
            title="Localização (Urbana/Rural)",
        )
        pdf.add_chart("zona_pie", chart)

    if state_data.top_municipios:
        city_names = [
            m["nome"][:25] + ("..." if len(m["nome"]) > 25 else "")
            for m in state_data.top_municipios
        ]
        city_idebs = [float(m["ideb"]) for m in state_data.top_municipios]
        chart = generate_horizontal_bar_chart(
            labels=city_names,
            values=city_idebs,
            title="Top Municípios — IDEB",
            xlabel="IDEB",
        )
        pdf.add_chart("top_schools", chart)

    pdf_stream = pdf.render()
    filename = f"dossie_estado_{uf}.pdf"

    return StreamingResponse(
        pdf_stream,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "application/pdf",
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )
