from pydantic import BaseModel, Field

class DetalheEtapaEnsino(BaseModel):
    alunosPorTurma: float = 0.0
    taxaAprovacao: float = 0.0
    taxaReprovacao: float = 0.0
    horasAulaDiarias: float = 0.0
    tnr: float = 0.0 

class Indicadores(BaseModel):
    anoReferencia: int = 2024
    totalAlunos: int = 0
    
    educacaoInfantil: DetalheEtapaEnsino = Field(default_factory=DetalheEtapaEnsino)
    fundamentalAnosIniciais: DetalheEtapaEnsino = Field(default_factory=DetalheEtapaEnsino)
    fundamentalAnosFinais: DetalheEtapaEnsino = Field(default_factory=DetalheEtapaEnsino)
    ensinoMedio: DetalheEtapaEnsino = Field(default_factory=DetalheEtapaEnsino)