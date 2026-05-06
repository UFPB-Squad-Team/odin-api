from typing import Any
from src.domain.entities.bairro import BairroResumo, BairroEducacaoStats
from src.domain.entities.municipio import SocioeconomicoStats
from src.domain.repository.bairro_repository import IBairroRepository
from src.infrastructure.database.mapper.mongo_neighborhood_mapper import MongoNeighborhoodMapper
from .mongo_territorial_aggregation_repository import MongoTerritorialAggregationRepository

class MongoBairroRepository(MongoTerritorialAggregationRepository, IBairroRepository):
    def __init__(self, bairro_collection: Any, setor_collection: Any):
        # Reutilizamos a base que lida com agregações complexas
        super().__init__(None, bairro_collection, setor_collection)

    async def get_resumo(self, bairro_id: str) -> BairroResumo | None:
        # 1. Tenta buscar documento oficial (com flexibilidade no nome do campo)
        query = {
            "$or": [
                {"cd_bairro": bairro_id},
                {"cd_bairro_ibge": bairro_id}
            ]
        }
        doc = await self.bairro_collection.find_one(query)
        
        if doc:
            return self._map_to_resumo(doc, source="bairros_indicadores", oficial=True)

        # 2. Fallback: Agregação por setores
        fallback_docs = await self.setor_collection.aggregate([
            {"$match": query}, # Usamos a mesma query flexível aqui!
            {"$group": {
                "_id": "$cd_bairro_ibge", # O _id do group pode ficar assim mesmo
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
        
        # Construção manual para garantir a separação correta sugerida pelo líder
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