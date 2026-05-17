from pydantic import BaseModel, ConfigDict, Field
from .municipio import SocioeconomicoStats

class BairroEducacaoStats(BaseModel):
    """Estatísticas educacionais para granularidade de Bairro."""
    model_config = ConfigDict(from_attributes=True)

    totalEscolas: int | None = None
    totalMatriculas: int | None = None
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

class BairroResumo(BaseModel):
    """Entidade consolidada para o painel lateral de bairros."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="ID de 10 dígitos (7 mun + 3 bairro)")
    bairro: str = Field(..., description="Nome do bairro")
    municipio: str = Field(..., description="Nome do município")
    municipioIdIbge: str = Field(..., description="Código IBGE 7 dígitos")
    sg_uf: str | None = Field(default=None)
    
    tem_bairro_oficial: bool = Field(default=True)
    source: str = Field(default="bairros_indicadores")

    educacao: BairroEducacaoStats = Field(default_factory=BairroEducacaoStats)
    socioeconomico: SocioeconomicoStats = Field(default_factory=SocioeconomicoStats)