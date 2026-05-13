from abc import ABC, abstractmethod
from typing import List
from src.domain.entities.city_aggregation import CityAggregation

class IStateRepository(ABC):
    @abstractmethod
    async def get_cities_data_by_state(self, sg_uf: str) -> List[CityAggregation]:
        pass