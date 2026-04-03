from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from bson.errors import InvalidId
from typing import Optional

from src.domain.entities.school import School
from src.domain.repository.school_repository import ISchoolRepository
from src.domain.value_objects.pagination import PaginatedResponse
from src.infrastructure.database.config.app_config import config
from .pagination import fetch_paginated_documents
from ..mapper.school_mapper import MongoSchoolMapper


class MongoSchoolRepository(ISchoolRepository):
    """
    MongoDB implementation of the School repository using Motor.

    Implements:
    - list_all: Get all schools with pagination

    """

    def __init__(self, collection: AsyncIOMotorClient):
        self.collection = collection

    async def list_all(
        self,
        page: int,
        page_size: int,
    ) -> PaginatedResponse[School]:

        schools_docs, total = await fetch_paginated_documents(
            self.collection,
            page=page,
            page_size=page_size,
            sort_field="escolaIdInep",
            use_estimated_total_for_unfiltered=(
                config.use_estimated_total_for_unfiltered_lists
            ),
        )

        schools = MongoSchoolMapper.to_domain_many(schools_docs)

        return PaginatedResponse[School](
            items=schools,
            total_items=total,
            page=page,
            page_size=page_size,
        )

    async def get_by_id(self, school_id: str) -> Optional[School]:
        document = None

        try:
            document = await self.collection.find_one({"_id": ObjectId(school_id)})
        except InvalidId:
            document = None

        if document is None:
            document = await self.collection.find_one({"_id": school_id})

        if document is None:
            return None

        return MongoSchoolMapper.to_domain(document)
