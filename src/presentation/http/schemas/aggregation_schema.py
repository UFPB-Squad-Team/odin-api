from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class AggregationPointGeometry(BaseModel):
    type: Literal["Point"]
    coordinates: tuple[float, float]


class AggregationGeometry(BaseModel):
    type: str
    coordinates: Any


class CityAggregationProperties(BaseModel):
    municipioIdIbge: str
    co_municipio: str
    municipio: str
    uf: str | None = None
    total_escolas: int
    total_alunos: int
    avg_ideb: float | int | None = None
    pct_com_biblioteca: float | int | None = None
    pct_com_internet: float | int | None = None
    pct_com_lab_informatica: float | int | None = None
    pct_sem_acessibilidade: float | int | None = None
    source: str


class CityAggregationFeature(BaseModel):
    type: Literal["Feature"]
    mongoId: str | None = None
    id: str
    geometry: AggregationGeometry
    properties: CityAggregationProperties


class CityAggregationFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"]
    features: list[CityAggregationFeature]


class MongoNeighborhoodGeometry(BaseModel):
    type: str
    coordinates: Any


class MongoNeighborhoodAggregation(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    mongo_id: str | None = Field(
        default=None,
        validation_alias="_id",
        serialization_alias="_id",
    )
    municipio: str
    bairro: str
    cd_bairro_ibge: str | None = None
    geometria: MongoNeighborhoodGeometry | None = None
    municipio_id_ibge: str = Field(
        validation_alias="municipioIdIbge",
        serialization_alias="municipioIdIbge",
    )
    pct_com_biblioteca: float | int | None = None
    pct_com_internet: float | int | None = None
    pct_com_lab_informatica: float | int | None = None
    pct_sem_acessibilidade: float | int | None = None
    sg_uf: str | None = None
    total_escolas: int
    total_matriculas: int
    tem_bairro_oficial: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("tem_bairro_oficial", "tem_bairro_official"),
    )
    nivel: Literal["bairro", "setor"] = "bairro"
    cd_setor: str | None = None
    source: str


class NeighborhoodAggregationProperties(BaseModel):
    id: str
    municipioIdIbge: str
    co_municipio: str
    bairro: str
    municipio: str
    uf: str | None = None
    total_escolas: int
    total_alunos: int
    avg_ideb: float | int | None = None
    pct_com_biblioteca: float | int | None = None
    pct_com_internet: float | int | None = None
    pct_com_lab_informatica: float | int | None = None
    pct_sem_acessibilidade: float | int | None = None
    tem_bairro_oficial: bool = Field(serialization_alias="tem_bairro_oficial")
    nivel: Literal["bairro", "setor"] = "bairro"
    cd_setor: str | None = None
    source: str


class NeighborhoodAggregationFeature(BaseModel):
    type: Literal["Feature"]
    mongoId: str | None = None
    id: str
    geometry: AggregationGeometry
    properties: NeighborhoodAggregationProperties


class NeighborhoodAggregationFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"]
    features: list[NeighborhoodAggregationFeature]
