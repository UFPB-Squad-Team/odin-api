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


class MunicipioGeoJsonProperties(BaseModel):
    municipio_nome: str
    municipio_id_ibge: str
    estado_sigla: str
    total_escolas: int
    total_alunos: int
    percentual_internet: float = 0.0
    percentual_biblioteca: float = 0.0
    percentual_laboratorio: float = 0.0
    percentual_quadra: float = 0.0
    percentual_acessibilidade_pcd: float = 0.0


class MunicipioGeoJsonFeature(BaseModel):
    type: Literal["Feature"]
    id: str
    geometry: GeoJsonPointGeometry
    properties: MunicipioGeoJsonProperties


class MunicipioGeoJsonFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"]
    features: list[MunicipioGeoJsonFeature]


class BairroBySchoolResponse(BaseModel):
    id: str
    escola_id_inep: int | None = None
    escola_nome: str | None = None
    municipio_nome: str | None = None
    estado_sigla: str | None = None
    bairro: str = ""
