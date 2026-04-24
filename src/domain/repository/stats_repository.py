from abc import ABC, abstractmethod
from src.domain.entities.stats import SummaryStats

class IStatsRepository(ABC):
    @abstractmethod
    async def get_summary_stats(self) -> SummaryStats:
        """
        Interface obrigatória para o padrão de módulo repetível.
        """
        pass