from src.domain.entities.school import School
from src.domain.repository.school_repository import ISchoolRepository
from src.domain.value_objects.pagination import PaginatedResponse
from src.domain.value_objects.query import QueryFilter

from .list_all_schools_dto import ListSchoolsDTO


class ListAllSchools:
    def __init__(self, school_repository: ISchoolRepository):
        self.school_repository = school_repository

    async def execute(self, dto: ListSchoolsDTO) -> PaginatedResponse[School]:
        filters = list(dto.query.filters or [])

        if dto.search_term:
            filters.append(
                QueryFilter(
                    field="escola_nome",
                    operator="contains",
                    value=dto.search_term,
                )
            )

        if dto.municipio:
            filters.append(
                QueryFilter(
                    field="municipio_nome",
                    operator="contains",
                    value=dto.municipio,
                )
            )

        dto.query.filters = filters
        return await self.school_repository.find_paginated(dto.query)
