from src.domain.repository.school_repository import ISchoolRepository
from src.domain.entities.school import School
from src.domain.value_objects.pagination import PaginatedResponse
from src.application.common.base_list_use_case import BaseListUseCase
from .list_all_schools_dto import ListSchoolsDTO


class ListAllSchools(BaseListUseCase[School]):
    def __init__(self, school_repository: ISchoolRepository):
        super().__init__(school_repository)

    async def execute(self, dto: ListSchoolsDTO) -> PaginatedResponse[School]:
        return await super().execute(dto.query)
