from pydantic import BaseModel

class CityEducacao(BaseModel):
    total_escolas: int
    total_alunos: int
    pct_com_biblioteca: float
    pct_com_internet: float
    pct_com_lab_informatica: float
    pct_sem_acessibilidade: float
    ideb_iniciais: float
    ideb_finais: float

class CitySocioeconomico(BaseModel):
    populacao: int
    taxa_desemprego: float

class CityAggregation(BaseModel):
    educacao: CityEducacao
    socioeconomico: CitySocioeconomico