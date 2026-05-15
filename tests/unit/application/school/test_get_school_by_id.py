import pytest
from unittest.mock import AsyncMock, Mock

from src.application.school.get_school_by_id.get_school_by_id import GetSchoolById
from src.application.school.get_school_by_id.get_school_by_id_dto import GetSchoolByIdDTO
from src.domain.entities.school import School


@pytest.mark.asyncio
async def test_should_return_school_when_found():
    mock_repository = Mock()
    fake_school = Mock(spec=School)
    mock_repository.get_by_inep_id = AsyncMock(return_value=fake_school)

    use_case = GetSchoolById(school_repository=mock_repository)
    dto = GetSchoolByIdDTO(escola_id_inep="123")

    result = await use_case.execute(dto)

    assert result == fake_school
    mock_repository.get_by_inep_id.assert_called_once_with("123")


@pytest.mark.asyncio
async def test_should_return_none_when_not_found():
    mock_repository = Mock()
    mock_repository.get_by_inep_id = AsyncMock(return_value=None)

    use_case = GetSchoolById(school_repository=mock_repository)
    dto = GetSchoolByIdDTO(escola_id_inep="999")

    result = await use_case.execute(dto)

    assert result is None
