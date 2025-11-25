import pytest
from unittest.mock import AsyncMock, Mock
from src.application.school.fuzzy_search.fuzzy_search import FuzzySearch
from src.application.school.fuzzy_search.fuzzy_search_dto import FuzzySearchDTO
from src.domain.entities.school import School
from src.domain.value_objects.pagination import PaginatedResponse

@pytest.mark.asyncio
async def test_should_return_paginated_response_when_found():
    mock_repository = Mock()
    
    fake_school = Mock(spec=School)
    
    expected_response = PaginatedResponse[School](
        items=[fake_school],
        total_items=1,
        page=1,
        page_size=10
    )

    mock_repository.fuzzy_search = AsyncMock(return_value=expected_response)

    use_case = FuzzySearch(school_repository=mock_repository)

    dto = FuzzySearchDTO(query="Rio", page=1, page_size=10)

    result = await use_case.execute(dto)

    assert result == expected_response
    assert len(result.items) == 1

    mock_repository.fuzzy_search.assert_called_once_with(
        query="Rio", 
        page=1, 
        page_size=10
    )

@pytest.mark.asyncio
async def test_should_return_empty_pagination_when_nothing_found():
    mock_repository = Mock()
    
    empty_response = PaginatedResponse[School](
        items=[],
        total_items=0,
        page=1,
        page_size=10
    )
    
    mock_repository.fuzzy_search = AsyncMock(return_value=empty_response)

    use_case = FuzzySearch(school_repository=mock_repository)
    dto = FuzzySearchDTO(query="XyzWk", page=1, page_size=10)

    result = await use_case.execute(dto)

    assert result == empty_response
    assert result.items == []
    assert result.total_items == 0
    
    mock_repository.fuzzy_search.assert_called_once_with(
        query="XyzWk", 
        page=1, 
        page_size=10
    )