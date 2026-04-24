from src.domain.entities.stats import SummaryStats
from src.domain.repository.stats_repository import IStatsRepository

class GetSummaryStatsUseCase:
    # O parâmetro TEM de se chamar "repository" para o Container injetar corretamente
    def __init__(self, repository: IStatsRepository):
        self.repository = repository

    async def execute(self) -> SummaryStats:
        """
        Coordena a obtenção das estatísticas resumidas através do repositório.
        """
        return await self.repository.get_summary_stats()