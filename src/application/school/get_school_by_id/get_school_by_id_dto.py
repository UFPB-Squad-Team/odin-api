from pydantic import BaseModel, Field


class GetSchoolByIdDTO(BaseModel):
    escola_id_inep: str = Field(..., description="Identificador INEP da escola")