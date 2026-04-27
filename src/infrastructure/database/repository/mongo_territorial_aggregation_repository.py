import re
from typing import Any

from src.domain.repository.territorial_aggregation_repository import (
    ITerritorialAggregationRepository,
)
from src.infrastructure.database.mapper.mongo_neighborhood_mapper import (
    MongoNeighborhoodMapper,
)
from src.infrastructure.database.mapper.territorial_aggregation_mapper import (
    TerritorialAggregationMapper,
)


class MongoTerritorialAggregationRepository(ITerritorialAggregationRepository):
    def __init__(
        self,
        municipio_collection: Any,
        bairro_collection: Any,
        setor_collection: Any,
    ):
        self.municipio_collection = municipio_collection
        self.bairro_collection = bairro_collection
        self.setor_collection = setor_collection

    async def get_cities(
        self,
        co_municipio: str | None = None,
        sg_uf: str | None = None,
        include_geometria: bool = False,
    ) -> dict[str, Any]:
        normalized_uf = sg_uf.upper() if sg_uf else None

        if co_municipio:
            query: dict[str, Any] = {
                "$or": [
                    {"co_municipio": co_municipio},
                    {"municipioIdIbge": co_municipio},
                    {"municipio_id_ibge": co_municipio},
                    {"idIbge": co_municipio},
                ]
            }
            if normalized_uf:
                query = {
                    "$and": [
                        query,
                        {
                            "$or": [
                                {"sg_uf": normalized_uf},
                                {"uf": normalized_uf},
                                {"estado_sigla": normalized_uf},
                            ]
                        },
                    ]
                }

            primary_doc = await self.municipio_collection.find_one(query)

            if primary_doc:
                city = TerritorialAggregationMapper.city_from_doc(
                    primary_doc,
                    source="municipio_indicadores",
                    include_geometria=include_geometria,
                )
                return {
                    "type": "FeatureCollection",
                    "features": [TerritorialAggregationMapper.city_to_feature(city)],
                }

            fallback_docs = await self._aggregate_city_from_setor(
                co_municipio=co_municipio,
                sg_uf=normalized_uf,
            )
            cities = [
                TerritorialAggregationMapper.city_from_doc(
                    doc,
                    source="setor_indicadores",
                    include_geometria=include_geometria,
                )
                for doc in fallback_docs
            ]

            return {
                "type": "FeatureCollection",
                "features": [
                    TerritorialAggregationMapper.city_to_feature(city) for city in cities
                ],
            }

        list_query: dict[str, Any] = {}
        if normalized_uf:
            list_query = {
                "$or": [
                    {"sg_uf": normalized_uf},
                    {"uf": normalized_uf},
                    {"estado_sigla": normalized_uf},
                ]
            }

        docs = await self.municipio_collection.find(list_query).to_list(length=None)
        cities = [
            TerritorialAggregationMapper.city_from_doc(
                doc,
                source="municipio_indicadores",
                include_geometria=include_geometria,
            )
            for doc in docs
        ]

        return {
            "type": "FeatureCollection",
            "features": [TerritorialAggregationMapper.city_to_feature(city) for city in cities],
        }

    async def get_by_municipio(
        self,
        municipio_id_ibge: str,
        bairro: str | None = None,
        include_geometria: bool = False,
    ) -> list[dict[str, Any]]:
        primary_docs = await self._find_neighborhood_docs(
            municipio_id_ibge=municipio_id_ibge,
            bairro=bairro,
        )

        if primary_docs:
            return [
                MongoNeighborhoodMapper.from_doc(
                    doc,
                    source="bairros_indicadores",
                    include_geometria=include_geometria,
                )
                for doc in primary_docs
            ]

        fallback_docs = await self._aggregate_neighborhoods_from_setor(
            co_municipio=municipio_id_ibge,
            bairro=bairro,
        )
        return [
            MongoNeighborhoodMapper.from_doc(
                doc,
                source="setor_indicadores",
                include_geometria=include_geometria,
            )
            for doc in fallback_docs
        ]

    async def _find_neighborhood_docs(
        self,
        *,
        municipio_id_ibge: str,
        bairro: str | None = None,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {
            "$and": [
                {
                    "$or": [
                        {"municipioIdIbge": municipio_id_ibge},
                        {"municipio_id_ibge": municipio_id_ibge},
                        {"co_municipio": municipio_id_ibge},
                        {"idIbge": municipio_id_ibge},
                    ]
                },
            ]
        }

        if bairro:
            query = {
                "$and": [
                    query,
                    {
                        "$or": [
                            {"bairro": {"$regex": bairro, "$options": "i"}},
                            {"nm_bairro": {"$regex": bairro, "$options": "i"}},
                            {"nome_area": {"$regex": bairro, "$options": "i"}},
                        ]
                    },
                ]
            }

        projection = {
            "_id": 1,
            "municipio": 1,
            "nm_municipio": 1,
            "bairro": 1,
            "nm_bairro": 1,
            "nome_area": 1,
            "situacao": 1,
            "cd_bairro_ibge": 1,
            "cd_bairro": 1,
            "geometria": 1,
            "geometry": 1,
            "centroide": 1,
            "centroid": 1,
            "localizacao": 1,
            "municipioIdIbge": 1,
            "municipio_id_ibge": 1,
            "co_municipio": 1,
            "idIbge": 1,
            "sg_uf": 1,
            "uf": 1,
            "total_escolas": 1,
            "qtd_escolas": 1,
            "total_matriculas": 1,
            "total_alunos": 1,
            "qtd_alunos": 1,
            "pct_com_biblioteca": 1,
            "pct_com_internet": 1,
            "pct_com_lab_informatica": 1,
            "pct_sem_acessibilidade": 1,
            "tem_bairro_official": 1,
            "tem_bairro_oficial": 1,
            "cd_setor": 1,
            "co_setor": 1,
            "id_setor": 1,
            "socioeconomico": 1,
            "educacao": 1,
        }

        return await self.bairro_collection.find(query, projection).to_list(length=None)

    async def _aggregate_city_from_setor(
        self,
        *,
        co_municipio: str,
        sg_uf: str | None,
    ) -> list[dict[str, Any]]:
        match_conditions: list[dict[str, Any]] = [
            {
                "$or": [
                    {"co_municipio": co_municipio},
                    {"municipioIdIbge": co_municipio},
                ]
            }
        ]
        if sg_uf:
            match_conditions.append(
                {
                    "$or": [
                        {"sg_uf": sg_uf},
                        {"uf": sg_uf},
                        {"estado_sigla": sg_uf},
                    ]
                }
            )

        pipeline = [
            {
                "$match": {"$and": match_conditions}
            },
            {
                "$project": {
                    "co_municipio": {"$ifNull": ["$co_municipio", "$municipioIdIbge"]},
                    "municipio": {"$ifNull": ["$nm_municipio", "$municipio"]},
                    "uf": {"$ifNull": ["$sg_uf", "$uf"]},
                    "total_escolas": {
                        "$ifNull": ["$total_escolas", {"$ifNull": ["$qtd_escolas", 0]}]
                    },
                    "total_alunos": {
                        "$ifNull": [
                            "$total_alunos",
                            {"$ifNull": ["$total_matriculas", {"$ifNull": ["$qtd_alunos", 0]}]},
                        ]
                    },
                    "avg_ideb": {"$ifNull": ["$avg_ideb", "$ideb"]},
                    "pct_com_biblioteca": "$pct_com_biblioteca",
                    "pct_com_internet": "$pct_com_internet",
                    "pct_com_lab_informatica": "$pct_com_lab_informatica",
                    "pct_sem_acessibilidade": "$pct_sem_acessibilidade",
                    "socioeconomico": "$socioeconomico",
                    "educacao": "$educacao",
                    "lon": {
                        "$ifNull": [
                            "$longitude",
                            {
                                "$ifNull": [
                                    "$lon",
                                    {
                                        "$ifNull": [
                                            {"$arrayElemAt": ["$centroide.coordinates", 0]},
                                            {"$arrayElemAt": ["$geometria.coordinates.0.0.0", 0]},
                                        ]
                                    },
                                ]
                            },
                        ]
                    },
                    "lat": {
                        "$ifNull": [
                            "$latitude",
                            {
                                "$ifNull": [
                                    "$lat",
                                    {
                                        "$ifNull": [
                                            {"$arrayElemAt": ["$centroide.coordinates", 1]},
                                            {"$arrayElemAt": ["$geometria.coordinates.0.0.0", 1]},
                                        ]
                                    },
                                ]
                            },
                        ]
                    },
                }
            },
            {
                "$group": {
                    "_id": "$co_municipio",
                    "co_municipio": {"$first": "$co_municipio"},
                    "municipio": {"$first": "$municipio"},
                    "uf": {"$first": "$uf"},
                    "total_escolas": {"$sum": "$total_escolas"},
                    "total_alunos": {"$sum": "$total_alunos"},
                    "avg_ideb": {"$avg": "$avg_ideb"},
                    "pct_com_biblioteca": {"$avg": "$pct_com_biblioteca"},
                    "pct_com_internet": {"$avg": "$pct_com_internet"},
                    "pct_com_lab_informatica": {"$avg": "$pct_com_lab_informatica"},
                    "pct_sem_acessibilidade": {"$avg": "$pct_sem_acessibilidade"},
                    "avg_lon": {"$avg": "$lon"},
                    "avg_lat": {"$avg": "$lat"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "co_municipio": 1,
                    "municipio": 1,
                    "uf": 1,
                    "total_escolas": 1,
                    "total_alunos": 1,
                    "avg_ideb": 1,
                    "pct_com_biblioteca": 1,
                    "pct_com_internet": 1,
                    "pct_com_lab_informatica": 1,
                    "pct_sem_acessibilidade": 1,
                    "avg_lon": 1,
                    "avg_lat": 1,
                }
            },
        ]

        return await self.setor_collection.aggregate(pipeline).to_list(length=None)

    async def _aggregate_neighborhoods_from_setor(
        self,
        *,
        co_municipio: str,
        bairro: str | None,
    ) -> list[dict[str, Any]]:
        municipio_match_values: list[Any] = [co_municipio]
        if co_municipio.isdigit():
            municipio_match_values.append(int(co_municipio))

        pipeline = [
            {
                "$match": {
                    "$or": [
                        {"co_municipio": {"$in": municipio_match_values}},
                        {"municipioIdIbge": {"$in": municipio_match_values}},
                        {"municipio_id_ibge": {"$in": municipio_match_values}},
                        {"idIbge": {"$in": municipio_match_values}},
                    ]
                }
            },
            {
                "$project": {
                    "co_municipio": {
                        "$ifNull": [
                            "$co_municipio",
                            {
                                "$ifNull": [
                                    "$municipioIdIbge",
                                    {"$ifNull": ["$municipio_id_ibge", "$idIbge"]},
                                ]
                            },
                        ]
                    },
                    "municipio": {"$ifNull": ["$nm_municipio", "$municipio"]},
                    "uf": {
                        "$ifNull": [
                            "$sg_uf",
                            {"$ifNull": ["$uf", "$estado_sigla"]},
                        ]
                    },
                    "tem_bairro_official": {
                        "$ifNull": ["$tem_bairro_official", {"$ifNull": ["$tem_bairro_oficial", True]}]
                    },
                    "bairro_oficial": {"$ifNull": ["$bairro", "$nm_bairro"]},
                    "cd_setor": {
                        "$ifNull": [
                            "$cd_setor",
                            {"$ifNull": ["$co_setor", "$id_setor"]},
                        ]
                    },
                    "nome_area": 1,
                    "situacao": 1,
                    "total_escolas": {
                        "$ifNull": [
                            "$total_escolas",
                            {
                                "$ifNull": [
                                    "$qtd_escolas",
                                    {"$ifNull": ["$educacao.totalEscolas", "$educacao.total_escolas"]},
                                ]
                            },
                        ]
                    },
                    "total_alunos": {
                        "$ifNull": [
                            "$total_alunos",
                            {
                                "$ifNull": [
                                    "$total_matriculas",
                                    {
                                        "$ifNull": [
                                            "$qtd_alunos",
                                            {
                                                "$ifNull": [
                                                    "$educacao.totalMatriculas",
                                                    "$educacao.total_matriculas",
                                                ]
                                            },
                                        ]
                                    },
                                ]
                            },
                        ]
                    },
                    "avg_ideb": {"$ifNull": ["$avg_ideb", "$ideb"]},
                    "pct_com_biblioteca": {
                        "$ifNull": ["$pct_com_biblioteca", {"$ifNull": ["$educacao.pctComBiblioteca", "$educacao.pct_com_biblioteca"]}]
                    },
                    "pct_com_internet": {
                        "$ifNull": ["$pct_com_internet", {"$ifNull": ["$educacao.pctComInternet", "$educacao.pct_com_internet"]}]
                    },
                    "pct_com_lab_informatica": {
                        "$ifNull": ["$pct_com_lab_informatica", {"$ifNull": ["$educacao.pctComLabInformatica", "$educacao.pct_com_lab_informatica"]}]
                    },
                    "pct_sem_acessibilidade": {
                        "$ifNull": ["$pct_sem_acessibilidade", {"$ifNull": ["$educacao.pctSemAcessibilidade", "$educacao.pct_sem_acessibilidade"]}]
                    },
                    "geometria": {
                        "$ifNull": [
                            "$geometria",
                            {"$ifNull": ["$geometry", {"$ifNull": ["$centroide", {"$ifNull": ["$centroid", "$localizacao"]}]}]},
                        ]
                    },
                    "socioeconomico": "$socioeconomico",
                    "educacao": "$educacao",
                    "lon": {
                        "$ifNull": [
                            "$longitude",
                            {
                                "$ifNull": [
                                    "$lon",
                                    {
                                        "$ifNull": [
                                            {"$arrayElemAt": ["$centroide.coordinates", 0]},
                                            {"$arrayElemAt": ["$geometria.coordinates.0.0.0", 0]},
                                        ]
                                    },
                                ]
                            },
                        ]
                    },
                    "lat": {
                        "$ifNull": [
                            "$latitude",
                            {
                                "$ifNull": [
                                    "$lat",
                                    {
                                        "$ifNull": [
                                            {"$arrayElemAt": ["$centroide.coordinates", 1]},
                                            {"$arrayElemAt": ["$geometria.coordinates.0.0.0", 1]},
                                        ]
                                    },
                                ]
                            },
                        ]
                    },
                }
            },
            {
                "$addFields": {
                    "bairro_resolvido": {
                        "$cond": {
                            "if": "$tem_bairro_official",
                            "then": "$bairro_oficial",
                            "else": {
                                "$ifNull": [
                                    "$nome_area",
                                    {"$ifNull": ["$situacao", "$bairro_oficial"]},
                                ]
                            },
                        }
                    }
                }
            },
            {
                "$match": {
                    "$expr": {
                        "$and": [
                            {"$ne": ["$bairro_resolvido", None]},
                            {"$ne": ["$bairro_resolvido", ""]},
                        ]
                    }
                }
            },
            {
                "$addFields": {
                    "has_geometria": {
                        "$cond": {
                            "if": {"$ne": ["$geometria", None]},
                            "then": 1,
                            "else": 0,
                        }
                    }
                }
            },
            {
                "$sort": {
                    "bairro_resolvido": 1,
                    "has_geometria": -1,
                }
            },
        ]

        if bairro:
            pipeline.append(
                {
                    "$match": {
                        "bairro_resolvido": {
                            "$regex": re.escape(bairro),
                            "$options": "i",
                        }
                    }
                }
            )

        pipeline.extend(
            [
                {
                    "$group": {
                        "_id": "$bairro_resolvido",
                        "co_municipio": {"$first": "$co_municipio"},
                        "bairro": {"$first": "$bairro_resolvido"},
                        "cd_setor": {"$first": "$cd_setor"},
                        "municipio": {"$first": "$municipio"},
                        "uf": {"$first": "$uf"},
                        "tem_bairro_official": {"$first": "$tem_bairro_official"},
                        "total_escolas": {"$sum": "$total_escolas"},
                        "total_alunos": {"$sum": "$total_alunos"},
                        "avg_ideb": {"$avg": "$avg_ideb"},
                        "pct_com_biblioteca": {"$avg": "$pct_com_biblioteca"},
                        "pct_com_internet": {"$avg": "$pct_com_internet"},
                        "pct_com_lab_informatica": {"$avg": "$pct_com_lab_informatica"},
                        "pct_sem_acessibilidade": {"$avg": "$pct_sem_acessibilidade"},
                        "geometria": {"$first": "$geometria"},
                        "socioeconomico": {"$first": "$socioeconomico"},
                        "educacao": {"$first": "$educacao"},
                        "avg_lon": {"$avg": "$lon"},
                        "avg_lat": {"$avg": "$lat"},
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "co_municipio": 1,
                        "bairro": 1,
                        "cd_setor": 1,
                        "municipio": 1,
                        "uf": 1,
                        "tem_bairro_official": 1,
                        "total_escolas": 1,
                        "total_alunos": 1,
                        "avg_ideb": 1,
                        "pct_com_biblioteca": 1,
                        "pct_com_internet": 1,
                        "pct_com_lab_informatica": 1,
                        "pct_sem_acessibilidade": 1,
                        "geometria": 1,
                        "socioeconomico": 1,
                        "educacao": 1,
                        "avg_lon": 1,
                        "avg_lat": 1,
                    }
                },
                {"$sort": {"total_escolas": -1, "bairro": 1}},
            ]
        )

        return await self.setor_collection.aggregate(pipeline).to_list(length=None)
