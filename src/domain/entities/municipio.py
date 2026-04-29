from pydantic import BaseModel, ConfigDict, Field


class MunicipioCatalogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="IBGE municipality code as a 7-digit string")
    nome: str = Field(..., description="Municipality name")
    sg_uf: str | None = Field(default=None, description="State code")


class MunicipioResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    municipioIdIbge: str = Field(..., description="IBGE municipality code as a 7-digit string")
    municipio: str = Field(default="", description="Municipality name")
    sg_uf: str | None = Field(default=None, description="State code")
    total_escolas: int = 0
    total_matriculas: int = 0
    total_bairros: int = 0
    pct_com_biblioteca: float | None = None
    pct_com_internet: float | None = None
    pct_com_lab_informatica: float | None = None
    pct_sem_acessibilidade: float | None = None
    mediaIdebAnosIniciais: float | None = None
    tem_bairros_oficiais: bool = False
    source: str = Field(
        default="municipio_indicadores",
        description="Data source used to build this summary",
    )
