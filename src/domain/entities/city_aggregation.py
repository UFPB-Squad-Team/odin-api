from pydantic import BaseModel

class CityEducacao(BaseModel):
    total_escolas: int
    total_alunos: int
    pct_com_biblioteca: float = 0.0
    pct_com_internet: float = 0.0
    pct_com_internet_alunos: float = 0.0
    pct_com_lab_informatica: float = 0.0
    pct_com_lab_ciencias: float = 0.0
    pct_sem_acessibilidade: float = 0.0
    pct_com_agua_potavel: float = 0.0
    pct_com_energia_publica: float = 0.0
    pct_com_esgoto_rede_publica: float = 0.0
    pct_com_coleta_lixo: float = 0.0
    pct_com_quadra_esportes: float = 0.0
    pct_com_cozinha: float = 0.0
    pct_com_refeitorio: float = 0.0
    ideb_iniciais: float = 0.0
    ideb_finais: float = 0.0
    ideb_ensino_medio: float = 0.0
    media_afd_anos_iniciais: float = 0.0
    media_afd_anos_finais: float = 0.0
    media_afd_ensino_medio: float = 0.0
    media_tdi_anos_iniciais: float = 0.0
    media_tdi_anos_finais: float = 0.0
    media_tdi_ensino_medio: float = 0.0
    media_taxa_aprovacao_ai: float = 0.0
    media_taxa_aprovacao_af: float = 0.0
    media_taxa_aprovacao_em: float = 0.0
    media_taxa_abandono_ai: float = 0.0
    media_taxa_abandono_af: float = 0.0
    media_taxa_abandono_em: float = 0.0
    media_docentes_superior_ai: float = 0.0
    media_docentes_superior_af: float = 0.0
    media_docentes_superior_em: float = 0.0
    media_horas_aula_ai: float = 0.0
    media_horas_aula_af: float = 0.0
    media_horas_aula_em: float = 0.0
    media_alunos_turma_ai: float = 0.0
    media_alunos_turma_af: float = 0.0
    media_alunos_turma_em: float = 0.0

class CitySocioeconomico(BaseModel):
    populacao: int
    taxa_desemprego: float

class CityAggregation(BaseModel):
    educacao: CityEducacao
    socioeconomico: CitySocioeconomico