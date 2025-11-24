from pydantic import BaseModel, Field

class GetSchoolByIdDTO(BaseModel):
    id: str = Field(..., description="Unique identifier of the school")