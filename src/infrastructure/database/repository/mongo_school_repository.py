from motor.motor_asyncio import AsyncIOMotorClient
from src.domain.entities.school import School
from src.domain.repository.school_repository import ISchoolRepository
from src.domain.value_objects.pagination import PaginatedResponse
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

        cursor = (
            self.collection.find()
            .skip((page - 1) * page_size)
            .limit(page_size)
        )
        schools_docs = await cursor.to_list(length=page_size)

        schools = MongoSchoolMapper.to_domain_many(schools_docs)

        total = await self.collection.count_documents({})

        return PaginatedResponse[School](
            items=schools,
            total_items=total,
            page=page,
            page_size=page_size,
        )
