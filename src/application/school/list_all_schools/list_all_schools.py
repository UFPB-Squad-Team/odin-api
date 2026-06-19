import re

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
            if dto.fuzzy_search:
                search_pattern = self._build_fuzzy_pattern(dto.search_term)
                filters.append(
                    QueryFilter(
                        field="escola_nome",
                        operator="regex",
                        value=search_pattern,
                    )
                )
            else:
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

        if dto.municipio_id:
            filters.append(
                QueryFilter(
                    field="municipio_id_ibge",
                    operator="eq",
                    value=dto.municipio_id,
                )
            )

        if dto.dependencia_adm:
            filters.append(
                QueryFilter(
                    field="dependencia_adm",
                    operator="in",
                    value=dto.dependencia_adm,
                )
            )

        if dto.tipo_localizacao:
            filters.append(
                QueryFilter(
                    field="tipo_localizacao",
                    operator="in",
                    value=dto.tipo_localizacao,
                )
            )

        dto.query.filters = filters
        return await self.school_repository.find_paginated(dto.query)

    def _build_fuzzy_pattern(self, search_term: str) -> str:
        
        import unicodedata
        normalized = unicodedata.normalize('NFKD', search_term)
        normalized = ''.join(c for c in normalized if not unicodedata.combining(c))
        
        words = normalized.strip().split()
        if len(words) == 1:
            return f".*{re.escape(words[0])}.*"
        else:
            pattern = ".*".join([re.escape(word) for word in words])
            return f".*{pattern}.*"
