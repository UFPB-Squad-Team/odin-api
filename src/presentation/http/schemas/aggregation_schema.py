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
    totalDomicilios: int | None = None
    mediaMoradoresPorDomicilio: float | int | None = None


class SocioeconomicoEstruturaEtaria(BaseModel):
    pctCriancas0a9: float | int | None = None
    pctIdosos60Mais: float | int | None = None
    pctJovens15a29: float | int | None = None
    pctAdultos30a59: float | int | None = None


class SocioeconomicoRaca(BaseModel):
    pctPretaParda: float | int | None = None
    pctBranca: float | int | None = None
    pctIndigena: float | int | None = None


class SocioeconomicoGenero(BaseModel):
    pctPopMasculina: float | int | None = None
    pctPopFeminina: float | int | None = None


class SocioeconomicoSaneamento(BaseModel):
    pctAguaRedeGeral: float | int | None = None
    pctAguaInadequada: float | int | None = None
    pctAguaNaoEncanada: float | int | None = None
    pctEsgotoRedeGeral: float | int | None = None
    pctEsgotoInadequado: float | int | None = None
    pctLixoColetado: float | int | None = None
    pctLixoInadequado: float | int | None = None
    pctDomSemBanheiro: float | int | None = None


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
    pctDomUnipessoal: float | int | None = None
    pctDomTipoCasa: float | int | None = None
    pctDomTipoApto: float | int | None = None
    pctDomDegradado: float | int | None = None


class Socioeconomico(BaseModel):
    anoReferencia: int | None = None
    fonte: str | None = None
    populacao: SocioeconomicoPopulacao | None = None
    estruturaEtaria: SocioeconomicoEstruturaEtaria | None = None
    genero: SocioeconomicoGenero | None = None
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
    # Infraestrutura
    pctComAguaPotavel: float | int | None = None
    pctComEnergiaPublica: float | int | None = None
    pctComEsgotoRedePublica: float | int | None = None
    pctComColetaLixo: float | int | None = None
    pctComInternet: float | int | None = None
    pctComInternetAlunos: float | int | None = None
    pctComBiblioteca: float | int | None = None
    pctComLaboratorioInformatica: float | int | None = None
    pctComLaboratorioCiencias: float | int | None = None
    pctComQuadraEsportes: float | int | None = None
    pctComCozinha: float | int | None = None
    pctComRefeitorio: float | int | None = None
    pctSemAcessibilidade: float | int | None = None
    # IDEB
    mediaIdebAnosIniciais: float | None = None
    mediaIdebAnosFinals: float | None = None
    mediaIdebEnsinoMedio: float | None = None
    # AFD
    mediaAfdAnosIniciais: float | None = None
    mediaAfdAnosFinais: float | None = None
    mediaAfdEnsinoMedio: float | None = None
    # TDI
    mediaTdiAnosIniciais: float | None = None
    mediaTdiAnosFinais: float | None = None
    mediaTdiEnsinoMedio: float | None = None
    # Taxas de Aprovação
    mediaTaxaAprovacaoAi: float | None = None
    mediaTaxaAprovacaoAf: float | None = None
    mediaTaxaAprovacaoEm: float | None = None
    # Taxas de Abandono
    mediaTaxaAbandonoAi: float | None = None
    mediaTaxaAbandonoAf: float | None = None
    mediaTaxaAbandonoEm: float | None = None
    # Docentes com Ensino Superior
    mediaDocentesSuperiorAi: float | None = None
    mediaDocentesSuperiorAf: float | None = None
    mediaDocentesSuperiorEm: float | None = None
    # Horas Aula Diárias
    mediaHorasAulaAi: float | None = None
    mediaHorasAulaAf: float | None = None
    mediaHorasAulaEm: float | None = None
    # Alunos por Turma
    mediaAlunosTurmaAi: float | None = None
    mediaAlunosTurmaAf: float | None = None
    mediaAlunosTurmaEm: float | None = None


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
    pct_com_internet_alunos: float | int | None = None
    pct_com_lab_informatica: float | int | None = None
    pct_com_lab_ciencias: float | int | None = None
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
    pct_com_internet_alunos: float | int | None = None
    pct_com_lab_informatica: float | int | None = None
    pct_com_lab_ciencias: float | int | None = None
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
    pct_com_internet_alunos: float | int | None = None
    pct_com_lab_informatica: float | int | None = None
    pct_com_lab_ciencias: float | int | None = None
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
