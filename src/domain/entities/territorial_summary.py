from pydantic import BaseModel, ConfigDict, Field


class CitySummary(BaseModel):
    """Consolidated territorial aggregation for a city."""

    model_config = ConfigDict(from_attributes=True)

    mongoId: str | None = Field(default=None, description="MongoDB document ID")
    co_municipio: str = Field(..., description="IBGE city code")
    municipio: str = Field(default="", description="City name")
    uf: str | None = Field(default=None, description="State code")
    total_escolas: int = 0
    total_alunos: int = 0
    avg_ideb: float | None = None
    pct_com_biblioteca: float | None = None
    pct_com_internet: float | None = None
    pct_com_lab_informatica: float | None = None
    pct_sem_acessibilidade: float | None = None
    socioeconomico: dict | None = None
    educacao: dict | None = None
    full_geometry: dict | None = Field(
        default=None,
        description="Full geometry (Polygon/MultiPolygon/Point) when available",
    )
    coordinates: tuple[float, float] | None = Field(
        default=None,
        description="Centroid in [longitude, latitude]",
    )
    source: str = Field(
        default="municipio_indicadores",
        description="Data source used to build this summary",
    )


class NeighborhoodSummary(BaseModel):
    """Consolidated territorial aggregation for a neighborhood."""

    model_config = ConfigDict(from_attributes=True)

    mongoId: str | None = Field(default=None, description="MongoDB document ID")
    co_municipio: str = Field(..., description="IBGE city code")
    bairro: str = Field(default="", description="Neighborhood display name")
    municipio: str = Field(default="", description="City name")
    uf: str | None = Field(default=None, description="State code")
    total_escolas: int = 0
    total_alunos: int = 0
    avg_ideb: float | None = None
    pct_com_biblioteca: float | None = None
    pct_com_internet: float | None = None
    pct_com_lab_informatica: float | None = None
    pct_sem_acessibilidade: float | None = None
    tem_bairro_official: bool = True
    coordinates: tuple[float, float] | None = Field(
        default=None,
        description="Centroid in [longitude, latitude]",
    )
    source: str = Field(
        default="bairro_indicadores",
        description="Data source used to build this summary",
    )
