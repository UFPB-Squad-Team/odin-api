from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import StringConstraints

from src.application.aggregation.get_city_aggregations import GetCityAggregations
from src.application.aggregation.get_neighborhood_aggregations import (
    GetNeighborhoodAggregations,
)
from src.presentation.http.controller.aggregation.callable.aggregation_callable import (
    get_city_aggregations_use_case,
    get_neighborhood_aggregations_use_case,
)
from src.presentation.http.schemas.aggregation_schema import (
    CityAggregationFeatureCollection,
    MongoNeighborhoodAggregation,
    NeighborhoodAggregationFeatureCollection,
)

router = APIRouter()

UFCode = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_upper=True,
        min_length=2,
        max_length=2,
    ),
]


def _to_neighborhood_feature_collection(
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    features: list[dict[str, Any]] = []

    for item in items:
        geometry = item.get("geometria") or {
            "type": "Point",
            "coordinates": [0.0, 0.0],
        }

        resolved_id = (
            item.get("cd_setor")
            or item.get("cd_bairro_ibge")
            or item.get("_id")
            or f"{item.get('municipioIdIbge', '')}:{item.get('bairro', '')}"
        )
        nivel = item.get("nivel") or (
            "setor" if item.get("source") == "setor_indicadores" else "bairro"
        )

        if nivel == "setor":
            cd_setor = item.get("cd_setor")
            if cd_setor:
                data_quality_label = f"Setor censitário {cd_setor} (agregação IBGE)"
            else:
                data_quality_label = "Setor censitário (agregação IBGE)"
        else:
            data_quality_label = "Dados de bairro oficial"

        properties: dict[str, Any] = {
            "id": str(resolved_id),
            "municipioIdIbge": str(item.get("municipioIdIbge", "")),
            "co_municipio": str(item.get("municipioIdIbge", "")),
            "bairro": str(item.get("bairro", "")),
            "municipio": str(item.get("municipio", "")),
            "uf": item.get("sg_uf"),
            "total_escolas": int(item.get("total_escolas", 0) or 0),
            "total_alunos": int(item.get("total_matriculas", 0) or 0),
            "pct_com_biblioteca": item.get("pct_com_biblioteca"),
            "pct_com_internet": item.get("pct_com_internet"),
            "pct_com_internet_alunos": item.get("pct_com_internet_alunos"),
            "pct_com_lab_informatica": item.get("pct_com_lab_informatica"),
            "pct_com_lab_ciencias": item.get("pct_com_lab_ciencias"),
            "pct_sem_acessibilidade": item.get("pct_sem_acessibilidade"),
            "tem_bairro_oficial": bool(item.get("tem_bairro_oficial", True)),
            "nivel": nivel,
            "data_quality_label": data_quality_label,
            "socioeconomico": item.get("socioeconomico"),
            "educacao": item.get("educacao"),
            "source": str(item.get("source", "")),
        }

        if nivel == "setor" and item.get("cd_setor"):
            properties["cd_setor"] = str(item["cd_setor"])

        feature: dict[str, Any] = {
            "type": "Feature",
            "id": str(resolved_id),
            "geometry": geometry,
            "properties": properties,
        }
        if item.get("_id"):
            feature["mongoId"] = str(item["_id"])

        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
    }


@router.get(
    "/aggregations/cities",
    response_model=CityAggregationFeatureCollection,
    tags=["aggregations"],
    summary="List or fetch city aggregations",
    description="Returns GeoJSON FeatureCollection with city-level aggregated indicators. "
    "If municipioIdIbge is provided, returns data for that specific city with fallback to setor_indicadores. "
    "If not provided, returns all cities from municipio_indicadores collection.",
)
async def get_city_aggregations(
    municipioIdIbge: str | None = Query(
        default=None,
        min_length=7,
        max_length=7,
        description="IBGE municipality code (7 digits). Primary data source: municipio_indicadores. Fallback to setor_indicadores if not found.",
    ),
    sg_uf: list[UFCode] | None = Query(
        default=None,
        description=(
            "Optional UF filter. Repeat the query parameter to filter multiple "
            "states (for example, `?sg_uf=PB&sg_uf=PE`). When omitted, "
            "aggregations from all states are returned."
        ),
    ),
    include_geometria: bool = Query(
        default=False,
        description="If true, returns full geometry (Polygon/MultiPolygon) when available; otherwise returns centroid Point.",
    ),
    use_case: GetCityAggregations = Depends(get_city_aggregations_use_case),
):
    return await use_case.execute(
        co_municipio=municipioIdIbge,
        sg_uf=sg_uf,
        include_geometria=include_geometria,
    )


@router.get(
    "/aggregations/neighborhoods",
    response_model=list[MongoNeighborhoodAggregation]
    | NeighborhoodAggregationFeatureCollection,
    tags=["aggregations"],
    summary="List neighborhoods by city",
    description=(
        "Returns neighborhood documents for a municipality using bairros_indicadores as the primary source, including docs keyed by cd_municipio. "
        "If no neighborhood document exists, falls back to setor_indicadores aggregation. "
        "The response keeps the database contract, including _id and geometria."
    ),
)
async def get_neighborhood_aggregations(
    municipio_id: str | None = Query(
        default=None,
        min_length=7,
        max_length=7,
        description="IBGE municipality code (7 digits). Validated before any database access.",
    ),
    municipioIdIbge: str | None = Query(
        default=None,
        min_length=7,
        max_length=7,
        description="Legacy alias for municipio_id.",
        deprecated=True,
    ),
    bairro: str | None = Query(
        default=None,
        min_length=1,
        description="Optional neighborhood filter. Matches bairro, nm_bairro and nome_area.",
    ),
    sg_uf: list[UFCode] | None = Query(
        default=None,
        description=(
            "Optional UF filter. Repeat the query parameter to filter multiple "
            "states (for example, `?sg_uf=PB&sg_uf=PE`). When omitted, no UF "
            "filter is applied."
        ),
    ),
    include_geometria: bool = Query(
        default=False,
        description="If true, returns full geometria (MultiPolygon/Point). Default false to reduce payload size.",
    ),
    use_case: GetNeighborhoodAggregations = Depends(
        get_neighborhood_aggregations_use_case
    ),
):
    resolved_municipio_id = municipio_id or municipioIdIbge
    if not resolved_municipio_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="One of municipio_id or municipioIdIbge is required.",
        )

    result = await use_case.execute(
        municipio_id_ibge=resolved_municipio_id,
        bairro=bairro,
        sg_uf=sg_uf,
        include_geometria=include_geometria,
    )

    if include_geometria:
        return _to_neighborhood_feature_collection(result)

    return result
