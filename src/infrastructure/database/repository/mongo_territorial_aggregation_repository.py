import re
import unicodedata
from collections.abc import AsyncGenerator
from contextlib import aclosing
from typing import Any

from src.domain.entities.municipio import MunicipioCatalogItem, MunicipioResumo
from src.domain.repository.municipio_repository import IMunicipioRepository
from src.domain.repository.territorial_aggregation_repository import (
    ITerritorialAggregationRepository,
)
from src.infrastructure.database.mapper.mongo_neighborhood_mapper import (
    MongoNeighborhoodMapper,
)
from src.infrastructure.database.mapper.territorial_aggregation_mapper import (
    TerritorialAggregationMapper,
)

from .cursor import iter_documents


class MongoTerritorialAggregationRepository(
    ITerritorialAggregationRepository,
    IMunicipioRepository,
):
    def __init__(
        self,
        municipio_collection: Any,
        bairro_collection: Any,
        setor_collection: Any,
    ):
        self.municipio_collection = municipio_collection
        self.bairro_collection = bairro_collection
        self.setor_collection = setor_collection

    @staticmethod
    def _normalize_uf_filter(
        sg_uf: str | list[str] | None,
    ) -> str | list[str] | None:
        if isinstance(sg_uf, str):
            normalized = sg_uf.strip().upper()
            return normalized or None

        if not sg_uf:
            return None

        normalized_ufs = list(
            dict.fromkeys(uf.strip().upper() for uf in sg_uf if uf.strip())
        )
        return normalized_ufs or None

    @staticmethod
    def _uf_clause(sg_uf: str | list[str]) -> dict[str, Any]:
        value: str | dict[str, list[str]]
        value = {"$in": sg_uf} if isinstance(sg_uf, list) else sg_uf
        return {
            "$or": [
                {"sg_uf": value},
                {"uf": value},
                {"estado_sigla": value},
            ]
        }

    async def get_cities(self, co_municipio=None, sg_uf=None, include_geometria=False):
        return {
            "type": "FeatureCollection",
            "features": [
                feature
                async for feature in self.iter_cities(
                    co_municipio, sg_uf, include_geometria
                )
            ],
        }

    async def iter_cities(self, co_municipio=None, sg_uf=None, include_geometria=False):
        normalized_uf = self._normalize_uf_filter(sg_uf)
        if co_municipio:
            query = {
                "$or": [
                    {field: co_municipio}
                    for field in (
                        "co_municipio",
                        "municipioIdIbge",
                        "municipio_id_ibge",
                        "idIbge",
                    )
                ]
            }
            if normalized_uf:
                query = {"$and": [query, self._uf_clause(normalized_uf)]}
            doc = await self.municipio_collection.find_one(
                query, self._city_projection(include_geometria)
            )
            if doc:
                city = TerritorialAggregationMapper.city_from_doc(
                    doc,
                    source="municipio_indicadores",
                    include_geometria=include_geometria,
                )
                yield TerritorialAggregationMapper.city_to_feature(city)
                return
            docs = await self._aggregate_city_from_setor(
                co_municipio=co_municipio, sg_uf=normalized_uf
            )
            for doc in docs:
                city = TerritorialAggregationMapper.city_from_doc(
                    doc, source="setor_indicadores", include_geometria=include_geometria
                )
                yield TerritorialAggregationMapper.city_to_feature(city)
            return
        query = self._uf_clause(normalized_uf) if normalized_uf else {}
        async with aclosing(
            iter_documents(
                self.municipio_collection.find(
                    query, self._city_projection(include_geometria)
                )
            )
        ) as documents:
            async for doc in documents:
                city = TerritorialAggregationMapper.city_from_doc(
                    doc,
                    source="municipio_indicadores",
                    include_geometria=include_geometria,
                )
                yield TerritorialAggregationMapper.city_to_feature(city)

    @staticmethod
    def _city_projection(include_geometria: bool = False) -> dict[str, Any]:
        # Geometry may be required by the legacy coordinate fallback. Select
        # every consumed alias, but never fetch unrelated census payloads.
        fields = (
            "_id co_municipio municipioIdIbge municipio_id_ibge idIbge nm_municipio municipio "
            "municipio_nome municipioNome sg_uf estado_sigla estadoSigla uf "
            "total_escolas qtd_escolas escolas total_alunos total_matriculas qtd_alunos alunos "
            "avg_ideb ideb_medio ideb pct_com_biblioteca pct_com_internet pct_com_internet_alunos "
            "pct_com_lab_informatica pct_com_lab_ciencias pct_sem_acessibilidade "
            "socioeconomico educacao centroide centroid geometry localizacao geometria "
            "longitude lon avg_lon latitude lat avg_lat"
        )
        projection: dict[str, Any] = dict.fromkeys(fields.split(), 1)
        if not include_geometria:
            has_centroid = {
                "$ne": [
                    {"$ifNull": ["$centroide", {"$ifNull": ["$centroid", None]}]},
                    None,
                ]
            }
            for field in ("geometry", "geometria", "localizacao"):
                projection[field] = {"$cond": [has_centroid, "$$REMOVE", "$" + field]}
        return projection

    async def get_by_municipio(
        self, municipio_id_ibge, bairro=None, include_geometria=False, sg_uf=None
    ):
        return [
            item
            async for item in self.iter_neighborhoods(
                municipio_id_ibge, bairro, include_geometria, sg_uf
            )
        ]

    async def iter_neighborhoods(
        self, municipio_id_ibge, bairro=None, include_geometria=False, sg_uf=None
    ):
        normalized_uf = self._normalize_uf_filter(sg_uf)
        found = False
        async with aclosing(
            self._iter_neighborhood_docs(
                municipio_id_ibge=municipio_id_ibge,
                bairro=bairro,
                sg_uf=normalized_uf,
                include_geometria=include_geometria,
            )
        ) as items:
            async for doc in items:
                found = True
                enriched = await self._enrich_primary_neighborhood_docs([doc])
                yield MongoNeighborhoodMapper.from_doc(
                    enriched[0],
                    source="bairros_indicadores",
                    include_geometria=include_geometria,
                )
        if found:
            return
        async with aclosing(
            self._iter_neighborhoods_from_setor(
                co_municipio=municipio_id_ibge,
                bairro=bairro,
                sg_uf=normalized_uf,
                include_geometria=include_geometria,
            )
        ) as items:
            async for doc in items:
                yield MongoNeighborhoodMapper.from_doc(
                    doc, source="setor_indicadores", include_geometria=include_geometria
                )

    async def list_municipios(
        self,
        sg_uf: str | None = None,
    ) -> list[MunicipioCatalogItem]:
        normalized_uf = sg_uf.upper() if sg_uf else None

        query: dict[str, Any] = {}
        if normalized_uf:
            query = {
                "$or": [
                    {"sg_uf": normalized_uf},
                    {"uf": normalized_uf},
                    {"estado_sigla": normalized_uf},
                    {"estadoSigla": normalized_uf},
                ]
            }

        projection = {
            "co_municipio": 1,
            "municipioIdIbge": 1,
            "municipio_id_ibge": 1,
            "idIbge": 1,
            "municipio": 1,
            "nm_municipio": 1,
            "municipio_nome": 1,
            "municipioNome": 1,
            "sg_uf": 1,
            "uf": 1,
            "estado_sigla": 1,
            "estadoSigla": 1,
        }

        items = []
        async with aclosing(
            iter_documents(self.municipio_collection.find(query, projection))
        ) as documents:
            async for doc in documents:
                item = self._map_municipio_catalog_item(doc)
                if item is not None:
                    items.append(item)

        items.sort(key=lambda item: self._sort_key(item.nome))
        return items

    async def get_resumo(
        self,
        municipio_id_ibge: str,
    ) -> Any | None:
        query: dict[str, Any] = {
            "$or": [
                {"co_municipio": municipio_id_ibge},
                {"municipioIdIbge": municipio_id_ibge},
                {"municipio_id_ibge": municipio_id_ibge},
                {"idIbge": municipio_id_ibge},
            ]
        }

        primary_doc = await self.municipio_collection.find_one(query)
        if primary_doc:
            resumo = self._build_municipio_resumo(
                primary_doc,
                source="municipio_indicadores",
            )
            total_bairros = await self._count_official_neighborhoods(municipio_id_ibge)
            return resumo.model_copy(
                update={
                    "total_bairros": total_bairros,
                    "tem_bairros_oficiais": total_bairros > 0,
                }
            )

        fallback_docs = await self._aggregate_city_from_setor(
            co_municipio=municipio_id_ibge,
            sg_uf=None,
        )
        if not fallback_docs:
            return None

        resumo = self._build_municipio_resumo(
            fallback_docs[0],
            source="setor_indicadores",
        )
        total_bairros = await self._count_official_neighborhoods(municipio_id_ibge)
        return resumo.model_copy(
            update={
                "total_bairros": total_bairros,
                "tem_bairros_oficiais": total_bairros > 0,
            }
        )

    @staticmethod
    def _sort_key(value: str | None) -> str:
        if not value:
            return ""
        normalized = unicodedata.normalize("NFKD", value)
        return "".join(
            char for char in normalized if not unicodedata.combining(char)
        ).casefold()

    def _map_municipio_catalog_item(
        self,
        doc: dict[str, Any],
    ) -> MunicipioCatalogItem | None:
        municipio_id = TerritorialAggregationMapper._pick(
            doc,
            "co_municipio",
            "municipioIdIbge",
            "municipio_id_ibge",
            "idIbge",
            default=None,
        )
        nome = TerritorialAggregationMapper._pick(
            doc,
            "municipio",
            "nm_municipio",
            "municipio_nome",
            "municipioNome",
            default=None,
        )
        uf = TerritorialAggregationMapper._pick(
            doc,
            "sg_uf",
            "uf",
            "estado_sigla",
            "estadoSigla",
            default=None,
        )

        if municipio_id is None or nome is None:
            return None

        return MunicipioCatalogItem(
            id=str(municipio_id),
            nome=str(nome),
            sg_uf=str(uf).upper() if uf else None,
        )

    def _build_municipio_resumo(
        self,
        doc: dict[str, Any],
        *,
        source: str,
    ) -> MunicipioResumo:
        city = TerritorialAggregationMapper.city_from_doc(
            doc,
            source=source,
            include_geometria=False,
        )

        total_matriculas = city.total_alunos
        total_bairros = (
            TerritorialAggregationMapper._as_int(
                TerritorialAggregationMapper._pick(
                    doc,
                    "total_bairros",
                    "totalBairros",
                    default=TerritorialAggregationMapper._pick_nested(
                        doc,
                        ("educacao", "totalBairros"),
                    ),
                )
            )
            or 0
        )

        return MunicipioResumo(
            municipioIdIbge=city.co_municipio,
            municipio=city.municipio,
            sg_uf=city.uf,
            total_escolas=city.total_escolas,
            total_matriculas=total_matriculas,
            total_bairros=total_bairros,
            pct_com_biblioteca=city.pct_com_biblioteca,
            pct_com_internet=city.pct_com_internet,
            pct_com_lab_informatica=city.pct_com_lab_informatica,
            pct_sem_acessibilidade=city.pct_sem_acessibilidade,
            avg_ideb=city.avg_ideb,
            tem_bairros_oficiais=total_bairros > 0,
            source=source,
        )

    async def _count_official_neighborhoods(
        self,
        municipio_id_ibge: str,
        municipio_nome: str | None = None,
    ) -> int:
        query: dict[str, Any] = {
            "$or": [
                {"municipioIdIbge": municipio_id_ibge},
                {"municipio_id_ibge": municipio_id_ibge},
                {"co_municipio": municipio_id_ibge},
                {"idIbge": municipio_id_ibge},
            ]
        }
        return await self.bairro_collection.count_documents(query)

    async def _enrich_primary_neighborhood_docs(
        self,
        docs: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        enriched_docs: list[dict[str, Any]] = []
        for doc in docs:
            resolved_name = await self._resolve_official_neighborhood_name(doc)
            if resolved_name:
                updated_doc = dict(doc)
                updated_doc["bairro"] = resolved_name
                updated_doc.setdefault("nm_bairro", resolved_name)
                enriched_docs.append(updated_doc)
                continue

            enriched_docs.append(doc)

        return enriched_docs

    async def _resolve_official_neighborhood_name(
        self,
        doc: dict[str, Any],
    ) -> str | None:
        current_name = TerritorialAggregationMapper._pick(
            doc,
            "bairro",
            "nm_bairro",
            "nome_area",
            "situacao",
            default=None,
        )
        if isinstance(current_name, str) and current_name.strip():
            return current_name.strip()

        municipio_id = TerritorialAggregationMapper._pick(
            doc,
            "municipioIdIbge",
            "municipio_id_ibge",
            "cd_municipio",
            "co_municipio",
            "idIbge",
            default=None,
        )
        code = TerritorialAggregationMapper._pick(
            doc,
            "cd_bairro_ibge",
            "cd_bairro",
            default=None,
        )

        municipio_clauses: list[dict[str, Any]] = []
        if municipio_id is not None:
            municipio_clauses = [
                {"municipioIdIbge": str(municipio_id)},
                {"municipio_id_ibge": str(municipio_id)},
                {"cd_municipio": str(municipio_id)},
                {"co_municipio": str(municipio_id)},
                {"idIbge": str(municipio_id)},
            ]

        name_projection = {
            "bairro": 1,
            "nm_bairro": 1,
            "nome_area": 1,
            "situacao": 1,
        }

        if code is not None:
            municipality_clause = (
                {"$or": municipio_clauses} if municipio_clauses else {}
            )
            code_query: dict[str, Any] = {
                "$and": [
                    municipality_clause,
                    {
                        "$or": [
                            {"cd_bairro_ibge": code},
                            {"cd_bairro": code},
                        ]
                    },
                    {
                        "$or": [
                            {"bairro": {"$nin": [None, ""]}},
                            {"nm_bairro": {"$nin": [None, ""]}},
                            {"nome_area": {"$nin": [None, ""]}},
                            {"situacao": {"$nin": [None, ""]}},
                        ]
                    },
                ]
            }
            code_doc = await self.bairro_collection.find_one(
                code_query, name_projection
            )
            if code_doc:
                resolved = TerritorialAggregationMapper._pick(
                    code_doc,
                    "bairro",
                    "nm_bairro",
                    "nome_area",
                    "situacao",
                    default=None,
                )
                if isinstance(resolved, str) and resolved.strip():
                    return resolved.strip()

        geometry = TerritorialAggregationMapper._pick(
            doc, "geometria", "geometry", default=None
        )
        if not isinstance(geometry, dict) or not geometry:
            return self._build_official_neighborhood_label(doc)

        municipality_clause = {"$or": municipio_clauses} if municipio_clauses else {}
        geo_query: dict[str, Any] = {
            "$and": [
                municipality_clause,
                {
                    "geometria": {
                        "$geoIntersects": {
                            "$geometry": geometry,
                        }
                    }
                },
                {
                    "$or": [
                        {"bairro": {"$nin": [None, ""]}},
                        {"nm_bairro": {"$nin": [None, ""]}},
                        {"nome_area": {"$nin": [None, ""]}},
                        {"situacao": {"$nin": [None, ""]}},
                    ]
                },
            ]
        }

        geo_doc = await self.bairro_collection.find_one(geo_query, name_projection)
        if not geo_doc:
            return self._build_official_neighborhood_label(doc)

        resolved = TerritorialAggregationMapper._pick(
            geo_doc,
            "bairro",
            "nm_bairro",
            "nome_area",
            "situacao",
            default=None,
        )
        if isinstance(resolved, str) and resolved.strip():
            return resolved.strip()

        return self._build_official_neighborhood_label(doc)

    @staticmethod
    def _build_official_neighborhood_label(doc: dict[str, Any]) -> str | None:
        code = TerritorialAggregationMapper._pick(
            doc,
            "cd_bairro_ibge",
            "cd_bairro",
            default=None,
        )
        if code is not None:
            return f"Bairro {code}"

        municipio_id = TerritorialAggregationMapper._pick(
            doc,
            "municipioIdIbge",
            "municipio_id_ibge",
            "cd_municipio",
            "co_municipio",
            "idIbge",
            default=None,
        )
        if municipio_id is not None:
            return f"Bairro sem nome {municipio_id}"

        return "Bairro sem nome"

    async def _iter_neighborhood_docs(
        self,
        *,
        municipio_id_ibge: str,
        bairro: str | None = None,
        sg_uf: str | list[str] | None = None,
        include_geometria: bool = False,
    ) -> AsyncGenerator[dict[str, Any], None]:
        query: dict[str, Any] = {
            "$and": [
                {
                    "$or": [
                        {"municipioIdIbge": municipio_id_ibge},
                        {"municipio_id_ibge": municipio_id_ibge},
                        {"cd_municipio": municipio_id_ibge},
                        {"co_municipio": municipio_id_ibge},
                        {"idIbge": municipio_id_ibge},
                    ]
                },
            ]
        }

        if sg_uf:
            query["$and"].append(self._uf_clause(sg_uf))

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

        projection: dict[str, Any] = {
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
            "cd_municipio": 1,
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
            "pct_com_internet_alunos": 1,
            "pct_com_lab_informatica": 1,
            "pct_com_lab_ciencias": 1,
            "pct_sem_acessibilidade": 1,
            "tem_bairro_official": 1,
            "tem_bairro_oficial": 1,
            "cd_setor": 1,
            "co_setor": 1,
            "id_setor": 1,
            "socioeconomico": 1,
            "educacao": 1,
        }

        if not include_geometria:
            # The name resolver only needs geometry if the first populated name
            # alias is absent, invalid or blank. Match its precedence exactly.
            resolved_name = {
                "$ifNull": [
                    "$bairro",
                    {
                        "$ifNull": [
                            "$nm_bairro",
                            {"$ifNull": ["$nome_area", "$situacao"]},
                        ]
                    },
                ]
            }
            known_name = {
                "$let": {
                    "vars": {"name": resolved_name},
                    "in": {
                        "$cond": [
                            {"$eq": [{"$type": "$$name"}, "string"]},
                            {"$ne": [{"$trim": {"input": "$$name"}}, ""]},
                            False,
                        ]
                    },
                }
            }
            for field in (
                "geometria",
                "geometry",
                "centroide",
                "centroid",
                "localizacao",
            ):
                projection[field] = {"$cond": [known_name, "$$REMOVE", "$" + field]}

        async with aclosing(
            iter_documents(self.bairro_collection.find(query, projection))
        ) as documents:
            async for doc in documents:
                yield doc

    async def _aggregate_city_from_setor(
        self,
        *,
        co_municipio: str,
        sg_uf: str | list[str] | None,
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
            match_conditions.append(self._uf_clause(sg_uf))

        pipeline: list[dict[str, Any]] = [
            {"$match": {"$and": match_conditions}},
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
                            {
                                "$ifNull": [
                                    "$total_matriculas",
                                    {"$ifNull": ["$qtd_alunos", 0]},
                                ]
                            },
                        ]
                    },
                    "avg_ideb": {"$ifNull": ["$avg_ideb", "$ideb"]},
                    "pct_com_biblioteca": "$pct_com_biblioteca",
                    "pct_com_internet": "$pct_com_internet",
                    "pct_com_internet_alunos": "$pct_com_internet_alunos",
                    "pct_com_lab_informatica": "$pct_com_lab_informatica",
                    "pct_com_lab_ciencias": "$pct_com_lab_ciencias",
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
                                            {
                                                "$arrayElemAt": [
                                                    "$centroide.coordinates",
                                                    0,
                                                ]
                                            },
                                            {
                                                "$arrayElemAt": [
                                                    "$geometria.coordinates.0.0.0",
                                                    0,
                                                ]
                                            },
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
                                            {
                                                "$arrayElemAt": [
                                                    "$centroide.coordinates",
                                                    1,
                                                ]
                                            },
                                            {
                                                "$arrayElemAt": [
                                                    "$geometria.coordinates.0.0.0",
                                                    1,
                                                ]
                                            },
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
                    "pct_com_internet_alunos": {"$avg": "$pct_com_internet_alunos"},
                    "pct_com_lab_informatica": {"$avg": "$pct_com_lab_informatica"},
                    "pct_com_lab_ciencias": {"$avg": "$pct_com_lab_ciencias"},
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
                    "pct_com_internet_alunos": 1,
                    "pct_com_lab_informatica": 1,
                    "pct_com_lab_ciencias": 1,
                    "pct_sem_acessibilidade": 1,
                    "avg_lon": 1,
                    "avg_lat": 1,
                }
            },
        ]

        return await self.setor_collection.aggregate(pipeline).to_list(length=None)

    async def _iter_neighborhoods_from_setor(
        self,
        *,
        co_municipio: str,
        bairro: str | None,
        sg_uf: str | list[str] | None = None,
        include_geometria: bool = False,
    ) -> AsyncGenerator[dict[str, Any], None]:
        municipio_match_values: list[Any] = [co_municipio]
        if co_municipio.isdigit():
            municipio_match_values.append(int(co_municipio))

        match_conditions: list[dict[str, Any]] = [
            {
                "$or": [
                    {"co_municipio": {"$in": municipio_match_values}},
                    {"municipioIdIbge": {"$in": municipio_match_values}},
                    {"municipio_id_ibge": {"$in": municipio_match_values}},
                    {"idIbge": {"$in": municipio_match_values}},
                ]
            }
        ]
        if sg_uf:
            match_conditions.append(self._uf_clause(sg_uf))

        pipeline: list[dict[str, Any]] = [
            {
                "$match": (
                    match_conditions[0]
                    if len(match_conditions) == 1
                    else {"$and": match_conditions}
                )
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
                        "$ifNull": [
                            "$tem_bairro_official",
                            {"$ifNull": ["$tem_bairro_oficial", False]},
                        ]
                    },
                    "bairro_resolvido": {
                        "$cond": {
                            "if": {
                                "$or": [
                                    {"$ne": ["$bairro", None]},
                                    {"$ne": ["$nm_bairro", None]},
                                ]
                            },
                            "then": {"$ifNull": ["$bairro", "$nm_bairro"]},
                            "else": {
                                "$ifNull": [
                                    "$nome_area",
                                    {"$ifNull": ["$situacao", "Setor sem nome"]},
                                ]
                            },
                        }
                    },
                    "cd_setor": {
                        "$ifNull": [
                            "$cd_setor",
                            {"$ifNull": ["$co_setor", "$id_setor"]},
                        ]
                    },
                    "total_escolas": {
                        "$ifNull": [
                            "$total_escolas",
                            {
                                "$ifNull": [
                                    "$qtd_escolas",
                                    {
                                        "$ifNull": [
                                            "$educacao.totalEscolas",
                                            "$educacao.total_escolas",
                                        ]
                                    },
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
                        "$ifNull": [
                            "$pct_com_biblioteca",
                            {
                                "$ifNull": [
                                    "$educacao.pctComBiblioteca",
                                    "$educacao.pct_com_biblioteca",
                                ]
                            },
                        ]
                    },
                    "pct_com_internet": {
                        "$ifNull": [
                            "$pct_com_internet",
                            {
                                "$ifNull": [
                                    "$educacao.pctComInternet",
                                    "$educacao.pct_com_internet",
                                ]
                            },
                        ]
                    },
                    "pct_com_internet_alunos": {
                        "$ifNull": [
                            "$pct_com_internet_alunos",
                            {
                                "$ifNull": [
                                    "$educacao.pctComInternetAlunos",
                                    "$educacao.pct_com_internet_alunos",
                                ]
                            },
                        ]
                    },
                    "pct_com_lab_informatica": {
                        "$ifNull": [
                            "$pct_com_lab_informatica",
                            {
                                "$ifNull": [
                                    "$educacao.pctComLaboratorioInformatica",
                                    {
                                        "$ifNull": [
                                            "$educacao.pctComLabInformatica",
                                            "$educacao.pct_com_lab_informatica",
                                        ]
                                    },
                                ]
                            },
                        ]
                    },
                    "pct_com_lab_ciencias": {
                        "$ifNull": [
                            "$pct_com_lab_ciencias",
                            {
                                "$ifNull": [
                                    "$educacao.pctComLaboratorioCiencias",
                                    "$educacao.pct_com_lab_ciencias",
                                ]
                            },
                        ]
                    },
                    "pct_sem_acessibilidade": {
                        "$ifNull": [
                            "$pct_sem_acessibilidade",
                            {
                                "$ifNull": [
                                    "$educacao.pctSemAcessibilidade",
                                    "$educacao.pct_sem_acessibilidade",
                                ]
                            },
                        ]
                    },
                    "geometria": {
                        "$ifNull": [
                            "$geometria",
                            {
                                "$ifNull": [
                                    "$geometry",
                                    {
                                        "$ifNull": [
                                            "$centroide",
                                            {"$ifNull": ["$centroid", "$localizacao"]},
                                        ]
                                    },
                                ]
                            },
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
                                            {
                                                "$arrayElemAt": [
                                                    "$centroide.coordinates",
                                                    0,
                                                ]
                                            },
                                            {
                                                "$arrayElemAt": [
                                                    "$geometria.coordinates.0.0.0",
                                                    0,
                                                ]
                                            },
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
                                            {
                                                "$arrayElemAt": [
                                                    "$centroide.coordinates",
                                                    1,
                                                ]
                                            },
                                            {
                                                "$arrayElemAt": [
                                                    "$geometria.coordinates.0.0.0",
                                                    1,
                                                ]
                                            },
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

        # NÃO agrupar por bairro - retornar cada setor censitário separadamente
        # Isso preserva a granularidade original dos dados do censo
        pipeline.extend(
            [
                {
                    "$project": {
                        "_id": 0,
                        "co_municipio": 1,
                        "bairro": "$bairro_resolvido",
                        "cd_setor": 1,
                        "municipio": 1,
                        "uf": 1,
                        "tem_bairro_official": 1,
                        "total_escolas": 1,
                        "total_alunos": 1,
                        "avg_ideb": 1,
                        "pct_com_biblioteca": 1,
                        "pct_com_internet": 1,
                        "pct_com_internet_alunos": 1,
                        "pct_com_lab_informatica": 1,
                        "pct_com_lab_ciencias": 1,
                        "pct_sem_acessibilidade": 1,
                        "geometria": 1,
                        "socioeconomico": 1,
                        "educacao": 1,
                        "lon": 1,
                        "lat": 1,
                    }
                },
                {"$sort": {"bairro": 1, "cd_setor": 1}},
            ]
        )

        pipeline.insert(
            -1,
            {
                "$addFields": {
                    "educacao": {
                        "$ifNull": [
                            "$educacao",
                            {
                                "totalEscolas": "$total_escolas",
                                "totalMatriculas": "$total_alunos",
                                "pctComInternet": "$pct_com_internet",
                                "pctComBiblioteca": "$pct_com_biblioteca",
                                "pctComLaboratorioInformatica": "$pct_com_lab_informatica",
                                "pctSemAcessibilidade": "$pct_sem_acessibilidade",
                            },
                        ]
                    },
                    "socioeconomico": {"$ifNull": ["$socioeconomico", {}]},
                }
            },
        )

        if not include_geometria:
            # Keep the has_geometria ordering key, then shed polygons before the
            # sort and transfer. Numeric coordinate fallbacks were already read.
            pipeline.insert(3, {"$unset": "geometria"})

        async with aclosing(
            iter_documents(self.setor_collection.aggregate(pipeline))
        ) as documents:
            async for doc in documents:
                yield doc
