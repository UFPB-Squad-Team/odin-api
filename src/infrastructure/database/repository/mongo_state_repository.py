from typing import Any
from src.domain.repository.state_repository import IStateRepository

class MongoStateRepository(IStateRepository):
    def __init__(self, municipio_collection: Any):
        self.municipio_collection = municipio_collection

    async def get_cities_data_by_state(self, sg_uf: str) -> list[dict[str, Any]]:
        """Busca os dados agregados de todos os municípios de uma Unidade Federativa."""
        
        query = {
            "$or": [
                {"sg_uf": sg_uf.upper()},
                {"uf": sg_uf.upper()},
                {"estado_sigla": sg_uf.upper()},
                {"estadoSigla": sg_uf.upper()}
            ]
        }

        projection = {
            "_id": 0,
            "municipio": 1,
            "sg_uf": 1,
            "educacao": 1,
            "socioeconomico": 1
        }

        cursor = self.municipio_collection.find(query, projection)
        return await cursor.to_list(length=None)