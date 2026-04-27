from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class AggregationPointGeometry(BaseModel):
    type: Literal["Point"]
    coordinates: tuple[float, float]


class AggregationGeometry(BaseModel):
    type: str
    coordinates: Any


class SocioeconomicoPopulacao(BaseModel):
    total: int | None = None
    totalDomiciliosParticulares: int | None = None
    mediaMoradoresPorDomicilio: float | int | None = None


class SocioeconomicoEstruturaEtaria(BaseModel):
    pctCriancas0a9: float | int | None = None
    pctIdosos60Mais: float | int | None = None


class SocioeconomicoRaca(BaseModel):
    pctPretaParda: float | int | None = None


class SocioeconomicoSaneamento(BaseModel):
    pctAguaRedeGeral: float | int | None = None
    pctEsgotoRedeGeral: float | int | None = None
    pctLixoColetado: float | int | None = None


class SocioeconomicoEducacaoPopulacao(BaseModel):
    taxaAnalfabetismo15Mais: float | int | None = None


class SocioeconomicoFamilia(BaseModel):
    pctResponsavelFeminino: float | int | None = None

class SocioeconomicoMortalidade(BaseModel):
    totalObitosDomicilios: float | int | None = None
    obitosInfantis0a4: float | int | None = None

class SocioeconomicoHabitacao(BaseModel):
    pctDomImprovisado: float | int | None = None
    pctDomSuperlotado: float | int | None = None


class Socioeconomico(BaseModel):
    anoReferencia: int | None = None
    fonte: str | None = None
    populacao: SocioeconomicoPopulacao | None = None
    estruturaEtaria: SocioeconomicoEstruturaEtaria | None = None
    raca: SocioeconomicoRaca | None = None
    saneamento: SocioeconomicoSaneamento | None = None
    educacaoPopulacao: SocioeconomicoEducacaoPopulacao | None = None
    familia: SocioeconomicoFamilia | None = None
    mortalidade: SocioeconomicoMortalidade | None = None
    habitacao: SocioeconomicoHabitacao | None = None


class EducacaoMunicipio(BaseModel):
    totalEscolas: int | None = None
    totalMatriculas: int | None = None
    totalBairros: int | None = None
    pctComInternet: float | int | None = None
    pctComBiblioteca: float | int | None = None
    pctComLabInformatica: float | int | None = None
    pctSemAcessibilidade: float | int | None = None


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
    socioeconomico: Socioeconomico | None = None
    educacao: EducacaoMunicipio | None = None
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
    socioeconomico: Socioeconomico | None = None
    educacao: EducacaoMunicipio | None = None
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
    socioeconomico: Socioeconomico | None = None
    educacao: EducacaoMunicipio | None = None
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
