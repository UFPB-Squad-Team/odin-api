from src.domain.entities.municipio import MunicipioResumo
from src.domain.repository.municipio_repository import IMunicipioRepository

from .get_municipio_resumo_dto import GetMunicipioResumoDTO


class GetMunicipioResumo:
    def __init__(self, municipio_repository: IMunicipioRepository):
        self.municipio_repository = municipio_repository

    async def execute(self, dto: GetMunicipioResumoDTO) -> MunicipioResumo | None:
        return await self.municipio_repository.get_resumo(dto.municipio_id)
