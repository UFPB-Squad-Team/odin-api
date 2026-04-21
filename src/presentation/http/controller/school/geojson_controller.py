from fastapi import APIRouter, Depends, HTTPException, Path

from src.application.school.geojson.get_bairros_geojson import GetBairrosGeoJson
from src.application.school.geojson.get_bairro_by_school_id import GetBairroBySchoolId
from src.application.school.geojson.get_paraiba_geojson import GetParaibaGeoJson
from src.presentation.http.schemas.geojson_schema import (
    BairroBySchoolResponse,
    BairroGeoJsonFeatureCollection,
    ParaibaSchoolFeatureCollection,
)
from .callable.school_callable import (
    get_bairro_by_school_id_use_case,
    get_bairros_geojson_use_case,
    get_paraiba_geojson_use_case,
)


router = APIRouter()


@router.get("/escolas/geojson/paraiba", response_model=ParaibaSchoolFeatureCollection)
async def get_paraiba_geojson_endpoint(
    use_case: GetParaibaGeoJson = Depends(get_paraiba_geojson_use_case),
):
    return await use_case.execute()


@router.get("/bairros/geojson/{municipio}", response_model=BairroGeoJsonFeatureCollection)
async def get_bairros_geojson_endpoint(
    municipio: str = Path(..., min_length=1, description="Nome do municipio"),
    use_case: GetBairrosGeoJson = Depends(get_bairros_geojson_use_case),
):
    return await use_case.execute(municipio=municipio)


@router.get("/bairro/{school_id}", response_model=BairroBySchoolResponse)
async def get_bairro_by_school_id_endpoint(
    school_id: str = Path(..., min_length=1, description="_id Mongo ou escola_id_inep"),
    use_case: GetBairroBySchoolId = Depends(get_bairro_by_school_id_use_case),
):
    result = await use_case.execute(school_id=school_id)
    if not result:
        raise HTTPException(status_code=404, detail="School not found")
    return result
