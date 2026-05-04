from pydantic import BaseModel, Field


class GetMunicipioResumoDTO(BaseModel):
    municipio_id: str = Field(..., description="IBGE municipality code")
