from motor.motor_asyncio import AsyncIOMotorClient
import unicodedata
import asyncio
import time
from bson import ObjectId
from bson.errors import InvalidId

from src.domain.entities.school import School
from src.domain.repository.school_repository import ISchoolRepository
from src.domain.value_objects.pagination import PaginatedResponse
from src.domain.value_objects.query import QueryOptions, QuerySort
from src.infrastructure.database.config.app_config import config

from ..mapper.school_mapper import MongoSchoolMapper
from .base_mongo_repository import BaseMongoRepository


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
        self._paraiba_geojson_cache: dict[str, tuple[float, dict]] = {}
        self._paraiba_geojson_ttl_seconds = 60.0
        self._paraiba_geojson_cache_lock = asyncio.Lock()
        self._paraiba_geojson_cache_max_keys = 512
        self._geojson_indexes_ready = False
        self._geojson_index_lock = asyncio.Lock()

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

    async def _ensure_geojson_indexes(self) -> None:
        if self._geojson_indexes_ready or not hasattr(self.collection, "create_index"):
            return

        async with self._geojson_index_lock:
            if self._geojson_indexes_ready:
                return

            try:
                await self.collection.create_index(
                    [
                        ("estadoSigla", 1),
                        ("municipioIdIbge", 1),
                        ("escolaIdInep", 1),
                    ],
                    background=True,
                    name="idx_geojson_paraiba_municipio",
                )
                await self.collection.create_index(
                    [
                        ("estadoSigla", 1),
                        ("municipio_id_ibge", 1),
                        ("escolaIdInep", 1),
                    ],
                    background=True,
                    name="idx_geojson_paraiba_municipio_legacy",
                )
            except Exception:
                pass

            self._geojson_indexes_ready = True

    def _cleanup_paraiba_geojson_cache(self, now: float) -> None:
        expired_keys = [
            key
            for key, (cached_at, _) in self._paraiba_geojson_cache.items()
            if (now - cached_at) >= self._paraiba_geojson_ttl_seconds
        ]
        for key in expired_keys:
            self._paraiba_geojson_cache.pop(key, None)

        if len(self._paraiba_geojson_cache) <= self._paraiba_geojson_cache_max_keys:
            return

        oldest_keys = sorted(
            self._paraiba_geojson_cache.items(),
            key=lambda item: item[1][0],
        )
        to_remove = len(self._paraiba_geojson_cache) - self._paraiba_geojson_cache_max_keys
        for key, _ in oldest_keys[:to_remove]:
            self._paraiba_geojson_cache.pop(key, None)

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

    async def get_paraiba_geojson(self, municipio_id: str | None = None) -> dict:
        await self._ensure_geojson_indexes()

        cache_key = municipio_id or "__all__"
        now = time.monotonic()
        self._cleanup_paraiba_geojson_cache(now)
        cached = self._paraiba_geojson_cache.get(cache_key)
        if cached and (now - cached[0]) < self._paraiba_geojson_ttl_seconds:
            return cached[1]

        match_query = {
            "estadoSigla": "PB",
            "localizacao.type": "Point",
            "localizacao.coordinates.0": {"$type": "number"},
            "localizacao.coordinates.1": {"$type": "number"},
        }

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
            "endereco.bairro": 1,
            "dependenciaAdm": 1,
            "tipoLocalizacao": 1,
            "indicadores.ideb": 1,
            "localizacao": 1,
        }

        docs = await self.collection.find(match_query, projection).to_list(length=None)

        features = []
        for doc in docs:
            escola_id_inep = doc.get("escolaIdInep")
            if escola_id_inep is None:
                continue

            feature_id = str(escola_id_inep)
            municipio_id_ibge = self._resolve_municipio_id_ibge(doc)

            features.append(
                {
                    "type": "Feature",
                    "id": feature_id,
                    "geometry": doc.get("localizacao"),
                    "properties": {
                        "id": feature_id,
                        "escola_nome": doc.get("escolaNome"),
                        "escola_id_inep": escola_id_inep,
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
            )

        result = {"type": "FeatureCollection", "features": features}
        async with self._paraiba_geojson_cache_lock:
            write_now = time.monotonic()
            self._cleanup_paraiba_geojson_cache(write_now)
            self._paraiba_geojson_cache[cache_key] = (write_now, result)
        return result

    async def get_bairros_geojson(self, municipio: str) -> dict:
        municipio_candidates = self._build_municipio_candidates(municipio)
        pipeline = [
            {
                "$match": {
                    "estadoSigla": "PB",
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
                    "avg_lon": {"$avg": {"$arrayElemAt": ["$localizacao.coordinates", 0]}},
                    "avg_lat": {"$avg": {"$arrayElemAt": ["$localizacao.coordinates", 1]}},
                }
            },
            {"$sort": {"qtd_escolas": -1, "_id": 1}},
        ]

        docs = await self.collection.aggregate(pipeline).to_list(length=None)

        features = []
        for doc in docs:
            if doc.get("avg_lon") is None or doc.get("avg_lat") is None:
                continue

            features.append(
                {
                    "type": "Feature",
                    "id": doc.get("_id"),
                    "geometry": {
                        "type": "Point",
                        "coordinates": [doc.get("avg_lon"), doc.get("avg_lat")],
                    },
                    "properties": {
                        "bairro": doc.get("_id"),
                        "municipio_nome": doc.get("municipio_nome") or " ".join(municipio.split()),
                        "qtd_escolas": doc.get("qtd_escolas", 0),
                        "avg_ideb": doc.get("avg_ideb"),
                    },
                }
            )

        return {"type": "FeatureCollection", "features": features}

    async def get_bairro_by_school_id(self, school_id: str) -> dict | None:
        candidates = [{"_id": school_id}]

        try:
            candidates.append({"_id": ObjectId(school_id)})
        except InvalidId:
            pass

        if school_id.isdigit():
            candidates.append({"escolaIdInep": int(school_id)})

        query = {"$or": candidates}
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
