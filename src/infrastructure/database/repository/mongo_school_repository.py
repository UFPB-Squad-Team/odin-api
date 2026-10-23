import re
import unicodedata
from collections.abc import AsyncGenerator
from contextlib import aclosing
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorClient

from src.domain.entities.school import School
from src.domain.repository.school_repository import ISchoolRepository
from src.domain.value_objects.pagination import PaginatedResponse
from src.domain.value_objects.query import QueryFilter, QueryOptions, QuerySort
from src.infrastructure.database.config.app_config import config

from ..mapper.school_mapper import MongoSchoolMapper
from .base_mongo_repository import BaseMongoRepository
from .cursor import iter_documents

SCHOOL_FIELD_MAP = {
    "id": "_id",
    "municipio_id_ibge": "municipioIdIbge",
    "escola_id_inep": "escolaIdInep",
    "escola_nome": "escolaNome",
    "municipio_nome": "municipioNome",
    "estado_sigla": "estadoSigla",
    "dependencia_adm": "dependenciaAdm",
    "tipo_localizacao": "tipoLocalizacao",
    "bairro": "endereco.bairro",
}


class MongoSchoolRepository(BaseMongoRepository[School], ISchoolRepository):
    """
    MongoDB implementation of the School repository using Motor.

    Implements:
    - list_all: Backward-compatible offset pagination
    - find_paginated: Dynamic filters/sort/fields with cursor support

    """

    def __init__(self, collection: AsyncIOMotorClient):
        super().__init__(
            collection,
            mapper_to_domain=MongoSchoolMapper.to_domain,
            field_map=SCHOOL_FIELD_MAP,
            required_projection_fields=[
                "municipio_id_ibge",
                "escola_id_inep",
                "escola_nome",
                "municipio_nome",
                "estado_sigla",
                "dependencia_adm",
                "tipo_localizacao",
            ],
            default_sort_field="escolaIdInep",
            use_estimated_total_for_unfiltered=config.use_estimated_total_for_unfiltered_lists,
        )

    @staticmethod
    def _normalize_municipio_input(value: str) -> str:
        collapsed_spaces = " ".join(value.split())
        return collapsed_spaces.strip()

    @staticmethod
    def _remove_accents(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value)
        return "".join(ch for ch in normalized if not unicodedata.combining(ch))

    @classmethod
    def _build_municipio_candidates(cls, municipio: str) -> list[str]:
        normalized = cls._normalize_municipio_input(municipio)
        normalized_without_accents = cls._remove_accents(normalized)

        candidates: list[str] = []
        for base in (normalized, normalized_without_accents):
            for variant in (base, base.title(), base.upper(), base.lower()):
                if variant and variant not in candidates:
                    candidates.append(variant)

        return candidates

    @staticmethod
    def _build_municipio_id_values(municipio_id: str) -> list[str | int]:
        values: list[str | int] = [municipio_id]
        if municipio_id.isdigit():
            values.append(int(municipio_id))
        return values

    @staticmethod
    def _resolve_municipio_id_ibge(doc: dict) -> str | None:
        for key in ("municipioIdIbge", "municipio_id_ibge", "co_municipio", "idIbge"):
            value = doc.get(key)
            if value is not None:
                return str(value)
        return None

    async def list_all(
        self,
        page: int,
        page_size: int,
    ) -> PaginatedResponse[School]:
        query = QueryOptions(
            page=page,
            page_size=page_size,
            sort=QuerySort(field="escola_id_inep", direction=1),
        )
        return await self.find_paginated(query)

    async def find_paginated(self, query: QueryOptions) -> PaginatedResponse[School]:
        return await super().find_paginated(query)

    def _build_filters(self, filters: list[QueryFilter]) -> dict:
        if not filters:
            return {}

        clauses: list[dict] = []
        regular_filters: list[QueryFilter] = []

        for item in filters:
            if item.field == "municipio_id_ibge":
                if item.operator == "eq":
                    municipio_values = self._build_municipio_id_values(str(item.value))
                elif item.operator == "in":
                    municipio_values = []
                    for value in item.value:
                        municipio_values.extend(
                            self._build_municipio_id_values(str(value))
                        )
                else:
                    regular_filters.append(item)
                    continue

                unique_values: list[str | int] = []
                for value in municipio_values:
                    if value not in unique_values:
                        unique_values.append(value)

                clauses.append(
                    {
                        "$or": [
                            {"municipioIdIbge": {"$in": unique_values}},
                            {"municipio_id_ibge": {"$in": unique_values}},
                            {"co_municipio": {"$in": unique_values}},
                            {"idIbge": {"$in": unique_values}},
                        ]
                    }
                )
                continue

            if item.operator == "regex":
                field = self.field_map.get(item.field, item.field)
                clauses.append({field: {"$regex": item.value, "$options": "i"}})
                continue

            if item.operator == "contains":
                field = self.field_map.get(item.field, item.field)
                clauses.append(
                    {field: {"$regex": re.escape(str(item.value)), "$options": "i"}}
                )
                continue

            regular_filters.append(item)

        regular_clause = super()._build_filters(regular_filters)
        if regular_clause:
            clauses.append(regular_clause)

        if not clauses:
            return {}
        if len(clauses) == 1:
            return clauses[0]
        return {"$and": clauses}

    async def get_geojson(self, sg_uf=None, municipio_id=None) -> dict:
        return {
            "type": "FeatureCollection",
            "features": [
                feature
                async for feature in self.iter_geojson_features(sg_uf, municipio_id)
            ],
        }

    async def iter_geojson_features(
        self, sg_uf: list[str] | None = None, municipio_id: str | None = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        normalized_ufs = sorted(
            {uf.strip().upper() for uf in sg_uf or [] if uf.strip()}
        )
        match_query: dict[str, Any] = {
            "localizacao.type": "Point",
            "localizacao.coordinates.0": {"$type": "number"},
            "localizacao.coordinates.1": {"$type": "number"},
        }
        if normalized_ufs:
            match_query["estadoSigla"] = {"$in": normalized_ufs}

        if municipio_id is not None:
            municipio_id_values = self._build_municipio_id_values(municipio_id)
            match_query["$or"] = [
                {"municipioIdIbge": {"$in": municipio_id_values}},
                {"municipio_id_ibge": {"$in": municipio_id_values}},
                {"co_municipio": {"$in": municipio_id_values}},
                {"idIbge": {"$in": municipio_id_values}},
            ]

        projection = {
            "_id": 1,
            "escolaNome": 1,
            "escolaIdInep": 1,
            "municipioNome": 1,
            "municipioIdIbge": 1,
            "municipio_id_ibge": 1,
            "co_municipio": 1,
            "idIbge": 1,
            "estadoSigla": 1,
            "inep": 1,
            "inse": 1,
            "endereco.bairro": 1,
            "dependenciaAdm": 1,
            "tipoLocalizacao": 1,
            "indicadores": 1,
            "matriculas": 1,
            "localizacao": 1,
        }

        async with aclosing(
            iter_documents(self.collection.find(match_query, projection))
        ) as documents:
            async for doc in documents:
                escola_id_inep = doc.get("escolaIdInep")
                if escola_id_inep is None:
                    continue

                feature_id = str(escola_id_inep)
                municipio_id_ibge = self._resolve_municipio_id_ibge(doc)
                indicadores = dict(doc.get("indicadores") or {})
                ano_referencia = indicadores.get("anoReferencia", 2025)
                total_alunos = indicadores.get("totalAlunos", 0)
                inse = indicadores.get("inse", doc.get("inse"))
                indicadores["anoReferencia"] = ano_referencia
                indicadores["totalAlunos"] = total_alunos
                if inse is not None:
                    indicadores["inse"] = inse

                matriculas = doc.get("matriculas") or {}

                yield {
                    "type": "Feature",
                    "id": feature_id,
                    "geometry": doc.get("localizacao"),
                    "properties": {
                        "id": feature_id,
                        "escola_nome": doc.get("escolaNome"),
                        "escola_id_inep": escola_id_inep,
                        "estado_sigla": doc.get("estadoSigla"),
                        "inep": doc.get("inep"),
                        "inse": inse,
                        "indicadores": indicadores,
                        "anoReferencia": ano_referencia,
                        "totalAlunos": total_alunos,
                        "matriculas": matriculas if matriculas else None,
                        "municipio_nome": doc.get("municipioNome"),
                        "municipioIdIbge": (
                            str(municipio_id_ibge)
                            if municipio_id_ibge is not None
                            else None
                        ),
                        "bairro": (doc.get("endereco") or {}).get("bairro"),
                        "dependencia_adm": doc.get("dependenciaAdm"),
                        "tipo_localizacao": doc.get("tipoLocalizacao"),
                        "ideb": (doc.get("indicadores") or {}).get("ideb"),
                    },
                }

    async def get_paraiba_geojson(self, municipio_id: str | None = None) -> dict:
        return await self.get_geojson(municipio_id=municipio_id)

    async def get_bairros_geojson(self, municipio: str) -> dict:
        return {
            "type": "FeatureCollection",
            "features": [
                feature async for feature in self.iter_bairros_features(municipio)
            ],
        }

    async def iter_bairros_features(self, municipio: str):
        municipio_candidates = self._build_municipio_candidates(municipio)
        pipeline = [
            {
                "$match": {
                    "municipioNome": {"$in": municipio_candidates},
                    "endereco.bairro": {"$type": "string", "$ne": ""},
                    "localizacao.type": "Point",
                    "localizacao.coordinates.0": {"$type": "number"},
                    "localizacao.coordinates.1": {"$type": "number"},
                }
            },
            {
                "$group": {
                    "_id": "$endereco.bairro",
                    "municipio_nome": {"$first": "$municipioNome"},
                    "qtd_escolas": {"$sum": 1},
                    "avg_ideb": {"$avg": "$indicadores.ideb"},
                    "avg_lon": {
                        "$avg": {"$arrayElemAt": ["$localizacao.coordinates", 0]}
                    },
                    "avg_lat": {
                        "$avg": {"$arrayElemAt": ["$localizacao.coordinates", 1]}
                    },
                }
            },
            {"$sort": {"qtd_escolas": -1, "_id": 1}},
        ]

        async with aclosing(
            iter_documents(self.collection.aggregate(pipeline))
        ) as documents:
            async for doc in documents:
                if doc.get("avg_lon") is None or doc.get("avg_lat") is None:
                    continue

                yield {
                    "type": "Feature",
                    "id": doc.get("_id"),
                    "geometry": {
                        "type": "Point",
                        "coordinates": [doc.get("avg_lon"), doc.get("avg_lat")],
                    },
                    "properties": {
                        "bairro": doc.get("_id"),
                        "municipio_nome": doc.get("municipio_nome")
                        or " ".join(municipio.split()),
                        "qtd_escolas": doc.get("qtd_escolas", 0),
                        "avg_ideb": doc.get("avg_ideb"),
                    },
                }

    async def get_by_inep_id(self, inep_id: str | int) -> School | None:
        """
        Return a School domain object by its INEP identifier (`escolaIdInep`).
        """
        candidates: list[dict[str, Any]] = []

        if isinstance(inep_id, int):
            candidates.append({"escolaIdInep": inep_id})
            candidates.append({"escola_id_inep": inep_id})
        else:
            candidates.append({"escolaIdInep": inep_id})
            candidates.append({"escola_id_inep": inep_id})
            if str(inep_id).isdigit():
                candidates.append({"escolaIdInep": int(inep_id)})
                candidates.append({"escola_id_inep": int(inep_id)})

        query = {"$or": candidates}

        doc = await self.collection.find_one(query)
        if not doc:
            return None

        return self.mapper_to_domain(doc)

    async def get_bairro_by_school_id(self, school_id: str) -> dict | None:
        candidates: list[dict[str, Any]] = [{"_id": school_id}]

        try:
            candidates.append({"_id": ObjectId(school_id)})
        except InvalidId:
            pass

        if school_id.isdigit():
            candidates.append({"escolaIdInep": int(school_id)})

        query: dict[str, Any] = {"$or": candidates}
        projection = {
            "_id": 1,
            "escolaIdInep": 1,
            "escolaNome": 1,
            "municipioNome": 1,
            "estadoSigla": 1,
            "endereco.bairro": 1,
        }

        doc = await self.collection.find_one(query, projection)
        if not doc:
            return None

        return {
            "id": str(doc.get("_id")),
            "escola_id_inep": doc.get("escolaIdInep"),
            "escola_nome": doc.get("escolaNome"),
            "municipio_nome": doc.get("municipioNome"),
            "estado_sigla": doc.get("estadoSigla"),
            "bairro": (doc.get("endereco") or {}).get("bairro", ""),
        }
