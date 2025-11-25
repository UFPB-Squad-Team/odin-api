from pydantic import BaseModel, Field

class FuzzySearchDTO(BaseModel):
    query: str = Field(..., min_length=1, description="Texto para busca (nome, cidade, estado, etc)")
    page: int = Field(default=1, ge=1, description="Número da página")
    page_size: int = Field(default=10, ge=1, description="Quantidade de itens por página")