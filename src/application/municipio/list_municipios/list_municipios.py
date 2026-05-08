from src.domain.entities.municipio import MunicipioCatalogItem
from src.domain.repository.municipio_repository import IMunicipioRepository

from .list_municipios_dto import ListMunicipiosDTO


class ListMunicipios:
    def __init__(self, municipio_repository: IMunicipioRepository):
        self.municipio_repository = municipio_repository

    async def execute(self, dto: ListMunicipiosDTO) -> list[MunicipioCatalogItem]:
        return await self.municipio_repository.list_municipios(sg_uf=dto.sg_uf)
