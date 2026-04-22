from fastapi import APIRouter, Depends, HTTPException, Query, status

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
)


router = APIRouter()


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
    sg_uf: str | None = Query(
        default=None,
        min_length=2,
        max_length=2,
        description="Optional UF filter (e.g., PB). Applied when listing cities and combined with municipioIdIbge when provided.",
    ),
    use_case: GetCityAggregations = Depends(get_city_aggregations_use_case),
):
    return await use_case.execute(
        co_municipio=municipioIdIbge,
        sg_uf=sg_uf.upper() if sg_uf else None,
    )


@router.get(
    "/aggregations/neighborhoods",
    response_model=list[MongoNeighborhoodAggregation],
    tags=["aggregations"],
    summary="List neighborhoods by city",
    description=(
        "Returns neighborhood documents for a municipality using bairros_indicadores as the primary source. "
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

    return await use_case.execute(
        municipio_id_ibge=resolved_municipio_id,
        bairro=bairro,
        include_geometria=include_geometria,
    )
