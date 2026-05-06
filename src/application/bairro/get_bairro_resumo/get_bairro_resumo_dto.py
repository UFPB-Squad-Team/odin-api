from pydantic import BaseModel, Field

class GetBairroResumoDTO(BaseModel):
    bairro_id: str = Field(..., min_length=10, max_length=10)