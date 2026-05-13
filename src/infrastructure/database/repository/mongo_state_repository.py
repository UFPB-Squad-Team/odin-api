from typing import Any, List
from src.domain.repository.state_repository import IStateRepository
from src.infrastructure.database.mapper.state_summary_mapper import StateSummaryMapper
from src.domain.entities.city_aggregation import CityAggregation

class MongoStateRepository(IStateRepository):
    def __init__(self, municipio_collection: Any):
        self.municipio_collection = municipio_collection

    async def get_cities_data_by_state(self, sg_uf: str) -> List[CityAggregation]:
        """
        Busca os dados no MongoDB e realiza a tradução imediata para a 
        estrutura de domínio usando o Mapper.
        """
        # Query otimizada conforme a sugestão 5
        query = {"sg_uf": sg_uf.upper()}
        
        # Projection para buscar apenas o necessário
        projection = {
            "_id": 0, 
            "educacao": 1, 
            "socioeconomico": 1
        }
        
        cursor = self.municipio_collection.find(query, projection)
        raw_documents = await cursor.to_list(length=None)
        
        # Aqui acontece a 'mágica' da tradução que o seu colega sugeriu:
        # Transformamos a lista de dicts em uma lista de objetos CityAggregation
        return [StateSummaryMapper.to_entity(doc) for doc in raw_documents]