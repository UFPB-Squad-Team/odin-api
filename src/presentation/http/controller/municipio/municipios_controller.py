from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from src.application.municipio.get_municipio_resumo.get_municipio_resumo import (
    GetMunicipioResumo,
)
from src.application.municipio.get_municipio_resumo.get_municipio_resumo_dto import (
    GetMunicipioResumoDTO,
)
from src.application.municipio.list_municipios.list_municipios import ListMunicipios
from src.application.municipio.list_municipios.list_municipios_dto import (
    ListMunicipiosDTO,
)
from src.domain.entities.municipio import MunicipioCatalogItem, MunicipioResumo
from src.presentation.http.controller.municipio.callable.municipio_callable import (
    get_list_municipios_use_case,
    get_municipio_resumo_use_case,
)


router = APIRouter()


@router.get(
    "/municipios",
    response_model=list[MunicipioCatalogItem],
    tags=["municipios"],
    summary="Lista municípios",
    description="Retorna um catálogo leve de municípios para popular seletores e filtros em cascata.",
)
async def list_municipios(
    sg_uf: str | None = Query(
        default=None,
        min_length=2,
        max_length=2,
        description="Filtro opcional por UF, por exemplo PB.",
    ),
    use_case: ListMunicipios = Depends(get_list_municipios_use_case),
):
    dto = ListMunicipiosDTO(sg_uf=sg_uf.upper() if sg_uf else None)
    return await use_case.execute(dto)


@router.get(
    "/municipios/{municipio_id}/resumo",
    response_model=MunicipioResumo,
    tags=["municipios"],
    summary="Resumo de município",
    description="Retorna um resumo consolidado do município com fallback para setor_indicadores.",
)
async def get_municipio_resumo(
    municipio_id: str = Path(
        ...,
        min_length=7,
        max_length=7,
        description="Código IBGE do município com 7 dígitos.",
    ),
    use_case: GetMunicipioResumo = Depends(get_municipio_resumo_use_case),
):
    dto = GetMunicipioResumoDTO(municipio_id=municipio_id)
    resumo = await use_case.execute(dto)

    if resumo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Município não encontrado.",
        )

    return resumo
