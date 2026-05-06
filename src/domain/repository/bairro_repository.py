from abc import ABC, abstractmethod
from src.domain.entities.bairro import BairroResumo

class IBairroRepository(ABC):
    @abstractmethod
    async def get_resumo(self, bairro_id: str) -> BairroResumo | None:
        """Busca o resumo do bairro com lógica de fallback integrada."""
        pass