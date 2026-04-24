from src.infrastructure.database.repository.base_mongo_repository import BaseMongoRepository

class MongoStatsRepository(BaseMongoRepository):
    def __init__(self, collection):
        # Bypass arquitetural
        super().__init__(
            collection=collection,
            mapper_to_domain=lambda x: x,
            field_map={},
            default_sort_field="_id"
        )

    async def get_summary_stats(self):
        # Usamos $facet para buscar TODOS os dados do SummaryStats de uma só vez
        pipeline = [
            {
                "$facet": {
                    "totais": [
                        {
                            "$group": {
                                "_id": None,
                                "total_escolas": {"$sum": 1},
                                # Conta 1 se for True, 0 se for False/Null
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
        
        if not result_list:
            return {}
            
        data = result_list[0]
        
        # Extrai os totais e evita divisão por zero
        totais = data.get("totais", [{}])[0] if data.get("totais") else {}
        total_escolas = totais.get("total_escolas", 0)
        
        def calc_pct(qtd, total):
            return round((qtd / total * 100), 2) if total > 0 else 0.0

        indicadores_infra = {
            "Internet (%)": calc_pct(totais.get("qtd_internet", 0), total_escolas),
            "Biblioteca (%)": calc_pct(totais.get("qtd_biblioteca", 0), total_escolas),
            "Lab. Informática (%)": calc_pct(totais.get("qtd_informatica", 0), total_escolas)
        }

        # Constrói os dicionários de dependência e zona ignorando valores vazios
        por_dependencia = {
            item["_id"]: item["count"] for item in data.get("dependencia", []) if item.get("_id")
        }
        
        por_zona = {
            item["_id"]: item["count"] for item in data.get("zona", []) if item.get("_id")
        }
        
        total_municipios = len(data.get("municipios", []))
        
        # Retorna o dicionário perfeitamente alinhado com o SummaryStats
        return {
            "total_escolas": total_escolas,
            "total_municipios": total_municipios,
            "indicadores_infra": indicadores_infra,
            "por_dependencia": por_dependencia,
            "por_zona": por_zona
        }