from typing import Any, List
from src.domain.repository.state_repository import IStateRepository
from src.infrastructure.database.mapper.state_summary_mapper import StateSummaryMapper
from src.domain.entities.city_aggregation import CityAggregation
import unicodedata
from typing import Any, List, Optional
from src.infrastructure.database.mapper.state_mapper import StateMapper
from src.domain.entities.state import State

class MongoStateRepository(IStateRepository):
    def __init__(self, municipio_collection: Any):
        self.municipio_collection = municipio_collection

    async def get_cities_data_by_state(self, sg_uf: str) -> List[CityAggregation]:
        query = {"sg_uf": sg_uf.upper()}
        

        projection = {
            "_id": 0, 
            "educacao": 1, 
            "socioeconomico": 1
        }
        
        cursor = self.municipio_collection.find(query, projection)
        raw_documents = await cursor.to_list(length=None)
        
        return [StateSummaryMapper.to_entity(doc) for doc in raw_documents]
    
    def _remove_accents(self, text: str) -> str:
        """Helper privado para ajudar no Fuzzy Search."""
        return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    
    async def list_distinct_states(self, query: Optional[str] = None) -> List[State]:
        distinct_ufs = await self.municipio_collection.distinct("sg_uf")
        states = [StateMapper.to_entity(uf) for uf in distinct_ufs if uf]
        if query:
            q_clean = self._remove_accents(query.lower())
            states = [
                s for s in states
                if q_clean in self._remove_accents(s.nome.lower())
                or q_clean in s.sigla.lower()
            ]
        return sorted(states, key=lambda s: s.nome)