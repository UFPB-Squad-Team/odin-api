from src.domain.repository.school_repository import ISchoolRepository
from src.domain.entities.school import School
from src.domain.value_objects.pagination import PaginatedResponse
from .list_all_schools_dto import ListSchoolsDTO


class ListAllSchools:
    def __init__(self, school_repository: ISchoolRepository):
        self.school_repository = school_repository

    async def execute(self, dto: ListSchoolsDTO) -> PaginatedResponse[School]:
        return await self.school_repository.list_all(
            page=dto.page, page_size=dto.page_size
        )
