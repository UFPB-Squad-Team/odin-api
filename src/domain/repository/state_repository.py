from abc import ABC, abstractmethod
from typing import List
from src.domain.entities.city_aggregation import CityAggregation
from typing import List, Optional
from src.domain.entities.state import State

class IStateRepository(ABC):
    @abstractmethod
    async def get_cities_data_by_state(self, sg_uf: str) -> List[CityAggregation]:
        pass
    @abstractmethod
    async def list_distinct_states(self, query: Optional[str] = None) -> List[State]:
        pass