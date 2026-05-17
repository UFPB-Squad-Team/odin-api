from pydantic import BaseModel, ConfigDict, Field

class EducacaoStateStats(BaseModel):
    """Indicadores educacionais agregados por estado (Soma Absoluta)."""
    model_config = ConfigDict(from_attributes=True)

    metodo_agregacao: str = Field(default="soma_absoluta")
    total_escolas: int = 0
    total_alunos: int = 0
    pct_com_biblioteca: float | None = None
    pct_com_internet: float | None = None
    pct_com_internet_alunos: float | None = None
    pct_com_lab_informatica: float | None = None
    pct_com_lab_ciencias: float | None = None
    pct_sem_acessibilidade: float | None = None
    pct_com_agua_potavel: float | None = None
    pct_com_energia_publica: float | None = None
    pct_com_esgoto_rede_publica: float | None = None
    pct_com_coleta_lixo: float | None = None
    pct_com_quadra_esportes: float | None = None
    pct_com_cozinha: float | None = None
    pct_com_refeitorio: float | None = None
    avg_ideb_iniciais: float | None = None
    avg_ideb_finais: float | None = None
    avg_ideb_ensino_medio: float | None = None
    avg_afd_anos_iniciais: float | None = None
    avg_afd_anos_finais: float | None = None
    avg_afd_ensino_medio: float | None = None
    avg_tdi_anos_iniciais: float | None = None
    avg_tdi_anos_finais: float | None = None
    avg_tdi_ensino_medio: float | None = None
    avg_taxa_aprovacao_ai: float | None = None
    avg_taxa_aprovacao_af: float | None = None
    avg_taxa_aprovacao_em: float | None = None
    avg_taxa_abandono_ai: float | None = None
    avg_taxa_abandono_af: float | None = None
    avg_taxa_abandono_em: float | None = None
    avg_docentes_superior_ai: float | None = None
    avg_docentes_superior_af: float | None = None
    avg_docentes_superior_em: float | None = None
    avg_horas_aula_ai: float | None = None
    avg_horas_aula_af: float | None = None
    avg_horas_aula_em: float | None = None
    avg_alunos_turma_ai: float | None = None
    avg_alunos_turma_af: float | None = None
    avg_alunos_turma_em: float | None = None

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