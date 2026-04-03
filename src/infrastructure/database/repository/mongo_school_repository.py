from motor.motor_asyncio import AsyncIOMotorClient

from src.domain.entities.school import School
from src.domain.repository.school_repository import ISchoolRepository
from src.domain.value_objects.pagination import PaginatedResponse
from src.domain.value_objects.query import QueryOptions, QuerySort
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
        )

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
