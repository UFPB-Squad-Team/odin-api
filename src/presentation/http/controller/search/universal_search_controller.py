from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from src.application.search.universal_search.universal_search_dto import (
    UniversalSearchInputDTO,
)
from src.application.search.universal_search.universal_search_use_case import (
    UniversalSearchUseCase,
)

from .callable.search_callable import get_universal_search_use_case


class SearchResultItemResponse(BaseModel):
    id: str
    kind: str
    label: str
    subtitle: str
    coordinates: list[float] = Field(..., min_length=2, max_length=2)
    municipioIdIbge: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class UniversalSearchResponse(BaseModel):
    results: list[SearchResultItemResponse]
    total: int
    query: str


router = APIRouter()


@router.get("/busca/universal", response_model=UniversalSearchResponse)
async def universal_search(
    q: str = Query(
        ..., min_length=2, description="Texto de busca (mínimo 2 caracteres)"
    ),
    sg_uf: str | None = Query(None, description="Filtrar por UF"),
    municipio_id: str | None = Query(None, description="Restringir a um município"),
    limit: int = Query(20, ge=1, le=20, description="Máximo de sugestões retornadas"),
    use_case: UniversalSearchUseCase = Depends(get_universal_search_use_case),
):
    dto = UniversalSearchInputDTO(
        q=q.strip(),
        sg_uf=sg_uf,
        municipio_id=municipio_id,
        limit=limit,
    )

    result = await use_case.execute(dto)
    return UniversalSearchResponse(
        results=[
            SearchResultItemResponse(
                id=item.id,
                kind=item.kind,
                label=item.label,
                subtitle=item.subtitle,
                coordinates=list(item.coordinates),
                municipioIdIbge=item.municipio_id_ibge,
                metadata=item.metadata,
            )
            for item in result.results
        ],
        total=result.total,
        query=result.query,
    )
