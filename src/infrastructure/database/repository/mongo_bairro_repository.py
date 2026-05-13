from typing import Any
from src.domain.entities.bairro import BairroResumo, BairroEducacaoStats
from src.domain.entities.municipio import SocioeconomicoStats
from src.domain.repository.bairro_repository import IBairroRepository
from src.infrastructure.database.mapper.mongo_neighborhood_mapper import MongoNeighborhoodMapper
from .mongo_territorial_aggregation_repository import MongoTerritorialAggregationRepository

class MongoBairroRepository(MongoTerritorialAggregationRepository, IBairroRepository):
    def __init__(self, bairro_collection: Any, setor_collection: Any):
        super().__init__(None, bairro_collection, setor_collection)

    async def get_resumo(self, bairro_id: str) -> BairroResumo | None:
        query = {
            "$or": [
                {"cd_bairro": bairro_id},
                {"cd_bairro_ibge": bairro_id}
            ]
        }
        doc = await self.bairro_collection.find_one(query)
        
        if doc:
            return self._map_to_resumo(doc, source="bairros_indicadores", oficial=True)

        fallback_docs = await self.setor_collection.aggregate([
            {"$match": query},
            {"$group": {
                "_id": "$cd_bairro_ibge",
                "municipioIdIbge": {"$first": "$municipioIdIbge"},
                "bairro": {"$first": "$bairro"},
                "municipio": {"$first": "$municipio"},
                "sg_uf": {"$first": "$sg_uf"},
                "totalEscolas": {"$sum": "$educacao.totalEscolas"},
                "totalMatriculas": {"$sum": "$educacao.totalMatriculas"},
                "populacaoTotal": {"$sum": "$socioeconomico.populacao.total"},
                "pctComInternet": {"$avg": "$educacao.pctComInternet"}
            }}
        ]).to_list(length=1)

        if fallback_docs:
            return self._map_to_resumo(fallback_docs[0], source="setor_indicadores", oficial=False)

        return None

    def _map_to_resumo(self, doc: dict, source: str, oficial: bool) -> BairroResumo:
        mapped = MongoNeighborhoodMapper.from_doc(doc, source=source)
        
        return BairroResumo(
            id=mapped["cd_bairro_ibge"],
            bairro=mapped["bairro"],
            municipio=mapped["municipio"],
            municipioIdIbge=mapped["municipioIdIbge"],
            sg_uf=mapped["sg_uf"],
            tem_bairro_oficial=oficial,
            source=source,
            educacao=BairroEducacaoStats.model_validate(doc.get("educacao", {})),
            socioeconomico=SocioeconomicoStats.model_validate(doc.get("socioeconomico", {}))
        )