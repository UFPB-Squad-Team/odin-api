from pydantic import BaseModel, Field


class ListMunicipiosDTO(BaseModel):
    sg_uf: str | None = Field(default=None, description="Optional UF filter")
    term: str | None = Field(default=None, description="Termo para busca parcial pelo nome do município")
