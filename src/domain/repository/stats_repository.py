from abc import ABC, abstractmethod
from typing import Dict, Any

class IStatsRepository(ABC):
    @abstractmethod
    async def get_summary_stats(self) -> Dict[str, Any]:
        """
        Abstrai a consulta no banco de dados para agregar e contabilizar 
        os indicadores brutos de infraestrutura, dependência e zona.
        Retorna os dados agregados sem formatação de negócio.
        """
        pass