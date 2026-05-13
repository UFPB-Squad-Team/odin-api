from .get_bairro_resumo_dto import GetBairroResumoDTO
from src.domain.entities.bairro import BairroResumo
from src.domain.repository.bairro_repository import IBairroRepository

class GetBairroResumo:
    def __init__(self, bairro_repository: IBairroRepository):
        self.bairro_repository = bairro_repository

    async def execute(self, dto: GetBairroResumoDTO) -> BairroResumo | None:
        return await self.bairro_repository.get_resumo(dto.bairro_id)