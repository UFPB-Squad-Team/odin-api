from pydantic import BaseModel, ConfigDict, Field

class EducacaoStateStats(BaseModel):
    """Indicadores educacionais agregados por estado (Soma Absoluta)."""
    model_config = ConfigDict(from_attributes=True)

    metodo_agregacao: str = Field(default="soma_absoluta")
    total_escolas: int = 0
    total_alunos: int = 0
    pct_com_biblioteca: float | None = None
    pct_com_internet: float | None = None
    pct_com_lab_informatica: float | None = None
    pct_sem_acessibilidade: float | None = None
    avg_ideb_iniciais: float | None = None
    avg_ideb_finais: float | None = None

class SocioeconomicoStateStats(BaseModel):
    """Indicadores socioeconômicos agregados por estado - Média Ponderada."""
    model_config = ConfigDict(from_attributes=True)

    metodo_agregacao: str = Field(default="media_ponderada")
    populacao_total: int = 0
    indicadores: dict | None = Field(default_factory=dict)

class StateSummary(BaseModel):
    """Visão macro dos indicadores de um estado."""
    model_config = ConfigDict(from_attributes=True)

    sg_uf: str = Field(..., description="Sigla da Unidade Federativa (ex: PB)")
    estado: str | None = Field(default=None, description="Nome completo do estado")
    educacao: EducacaoStateStats
    socioeconomico: SocioeconomicoStateStats