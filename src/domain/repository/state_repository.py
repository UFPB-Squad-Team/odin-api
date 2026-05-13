from abc import ABC, abstractmethod
from typing import Any, List

class IStateRepository(ABC):
    @abstractmethod
    async def get_cities_data_by_state(self, sg_uf: str) -> List[dict[str, Any]]:
        pass