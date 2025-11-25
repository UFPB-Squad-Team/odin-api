from src.domain.repository.school_repository import ISchoolRepository
from src.domain.value_objects.pagination import PaginatedResponse
from src.domain.entities.school import School
from .fuzzy_search_dto import FuzzySearchDTO

class FuzzySearch:
    def __init__(self, school_repository: ISchoolRepository):
        self.school_repository = school_repository

    async def execute(self, dto: FuzzySearchDTO) -> PaginatedResponse[School]:
        return await self.school_repository.fuzzy_search(
            query=dto.query,
            page=dto.page,
            page_size=dto.page_size
        )