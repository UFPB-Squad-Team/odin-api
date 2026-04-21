from motor.motor_asyncio import AsyncIOMotorClient
import unicodedata
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

    async def get_paraiba_geojson(self) -> dict:
        pipeline = [
            {
                "$match": {
                    "estadoSigla": "PB",
                    "localizacao.type": "Point",
                    "localizacao.coordinates.0": {"$type": "number"},
                    "localizacao.coordinates.1": {"$type": "number"},
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "escolaNome": 1,
                    "escolaIdInep": 1,
                    "municipioNome": 1,
                    "bairro": "$endereco.bairro",
                    "dependenciaAdm": 1,
                    "tipoLocalizacao": 1,
                    "ideb": "$indicadores.ideb",
                    "geometry": "$localizacao",
                }
            },
        ]

        docs = await self.collection.aggregate(pipeline, allowDiskUse=True).to_list(length=None)

        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": str(doc.get("_id")),
                    "geometry": doc.get("geometry"),
                    "properties": {
                        "escola_nome": doc.get("escolaNome"),
                        "escola_id_inep": doc.get("escolaIdInep"),
                        "municipio_nome": doc.get("municipioNome"),
                        "bairro": doc.get("bairro"),
                        "dependencia_adm": doc.get("dependenciaAdm"),
                        "tipo_localizacao": doc.get("tipoLocalizacao"),
                        "ideb": doc.get("ideb"),
                    },
                }
                for doc in docs
            ],
        }

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
