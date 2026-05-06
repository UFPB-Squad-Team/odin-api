from pydantic import BaseModel, ConfigDict, Field
from .municipio import SocioeconomicoStats

class BairroEducacaoStats(BaseModel):
    """Estatísticas educacionais para granularidade de Bairro."""
    model_config = ConfigDict(from_attributes=True)

    totalEscolas: int | None = None
    totalMatriculas: int | None = None
    pctComBiblioteca: float | int | None = None
    pctComInternet: float | int | None = None
    pctComLabInformatica: float | int | None = None
    pctSemAcessibilidade: float | int | None = None
    mediaIdebAnosIniciais: float | None = None
    mediaIdebAnosFinals: float | None = None

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