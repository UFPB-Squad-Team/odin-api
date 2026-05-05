import pytest
from unittest.mock import AsyncMock, Mock

from src.application.school.list_all_schools.list_all_schools import ListAllSchools
from src.application.school.list_all_schools.list_all_schools_dto import ListSchoolsDTO
from src.domain.value_objects.pagination import PaginatedResponse
from src.domain.value_objects.query import QueryFilter, QueryOptions, QuerySort


@pytest.mark.asyncio
async def test_execute_appends_fuzzy_filters_and_preserves_query_options():
    repository = Mock()
    repository.find_paginated = AsyncMock(
        return_value=PaginatedResponse(
            page=1,
            page_size=10,
            total_items=0,
            items=[],
            next_cursor="next-token",
        )
    )
    use_case = ListAllSchools(school_repository=repository)
    dto = ListSchoolsDTO(
        query=QueryOptions(
            page=2,
            page_size=5,
            cursor="cursor-token",
            sort=QuerySort(field="municipio_nome", direction=-1),
            fields=["escola_nome", "municipio_nome"],
            filters=[QueryFilter(field="bairro", operator="eq", value="Centro")],
        ),
        search_term="estadual",
        municipio="Joao Pessoa",
    )

    result = await use_case.execute(dto)

    repository.find_paginated.assert_called_once()
    forwarded_query = repository.find_paginated.await_args.args[0]
    assert forwarded_query.page == 2
    assert forwarded_query.page_size == 5
    assert forwarded_query.cursor == "cursor-token"
    assert forwarded_query.sort == QuerySort(field="municipio_nome", direction=-1)
    assert forwarded_query.fields == ["escola_nome", "municipio_nome"]
    assert forwarded_query.filters == [
        QueryFilter(field="bairro", operator="eq", value="Centro"),
        QueryFilter(field="escola_nome", operator="contains", value="estadual"),
        QueryFilter(field="municipio_nome", operator="contains", value="Joao Pessoa"),
    ]
    assert result.next_cursor == "next-token"


@pytest.mark.asyncio
async def test_execute_keeps_existing_filters_when_optional_search_params_are_missing():
    repository = Mock()
    repository.find_paginated = AsyncMock(
        return_value=PaginatedResponse(
            page=1,
            page_size=10,
            total_items=0,
            items=[],
        )
    )
    use_case = ListAllSchools(school_repository=repository)
    dto = ListSchoolsDTO(
        query=QueryOptions(
            filters=[QueryFilter(field="estado_sigla", operator="eq", value="PB")]
        )
    )

    await use_case.execute(dto)

    forwarded_query = repository.find_paginated.await_args.args[0]
    assert forwarded_query.filters == [
        QueryFilter(field="estado_sigla", operator="eq", value="PB")
    ]
