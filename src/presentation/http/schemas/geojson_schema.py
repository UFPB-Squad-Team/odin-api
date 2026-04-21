from typing import Literal

from pydantic import BaseModel


class GeoJsonPointGeometry(BaseModel):
    type: Literal["Point"]
    coordinates: tuple[float, float]


class ParaibaSchoolProperties(BaseModel):
    escola_nome: str | None = None
    escola_id_inep: int | None = None
    municipio_nome: str | None = None
    bairro: str | None = None
    dependencia_adm: str | None = None
    tipo_localizacao: str | None = None
    ideb: float | int | None = None


class ParaibaSchoolFeature(BaseModel):
    type: Literal["Feature"]
    id: str
    geometry: GeoJsonPointGeometry
    properties: ParaibaSchoolProperties


class ParaibaSchoolFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"]
    features: list[ParaibaSchoolFeature]


class BairroGeoJsonProperties(BaseModel):
    bairro: str
    municipio_nome: str
    qtd_escolas: int
    avg_ideb: float | int | None = None


class BairroGeoJsonFeature(BaseModel):
    type: Literal["Feature"]
    id: str
    geometry: GeoJsonPointGeometry
    properties: BairroGeoJsonProperties


class BairroGeoJsonFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"]
    features: list[BairroGeoJsonFeature]


class BairroBySchoolResponse(BaseModel):
    id: str
    escola_id_inep: int | None = None
    escola_nome: str | None = None
    municipio_nome: str | None = None
    estado_sigla: str | None = None
    bairro: str = ""
