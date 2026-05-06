from src.infrastructure.database.repository.base_mongo_repository import BaseMongoRepository

class MongoStatsRepository:
    def __init__(self, collection):
    
        self.collection = collection

    async def get_summary_stats(self) -> dict:
        pipeline = [
            {
                "$match": {
                    "estadoSigla": "PB" 
                }
            },
            {
                "$facet": {
                    "totais": [
                        {
                            "$group": {
                                "_id": None,
                                "total_escolas": {"$sum": 1},
                                "qtd_internet": {"$sum": {"$cond": [{"$eq": ["$infraestrutura.internet.possuiInternet", True]}, 1, 0]}},
                                "qtd_biblioteca": {"$sum": {"$cond": [{"$eq": ["$infraestrutura.possuiBiblioteca", True]}, 1, 0]}},
                                "qtd_informatica": {"$sum": {"$cond": [{"$eq": ["$infraestrutura.possuiLaboratorioInformatica", True]}, 1, 0]}}
                            }
                        }
                    ],
                    "dependencia": [
                        {"$group": {"_id": "$dependenciaAdm", "count": {"$sum": 1}}}
                    ],
                    "zona": [
                        {"$group": {"_id": "$tipoLocalizacao", "count": {"$sum": 1}}}
                    ],
                    "municipios": [
                        {"$group": {"_id": "$municipioIdIbge"}}
                    ]
                }
            }
        ]
        
        cursor = self.collection.aggregate(pipeline)
        result_list = await cursor.to_list(length=1)
        
        return result_list[0] if result_list else {}