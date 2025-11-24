import pytest
from unittest.mock import AsyncMock, Mock
from src.application.school.get_school_by_id.get_school_by_id import GetSchoolById
from src.application.school.get_school_by_id.get_school_by_id_dto import GetSchoolByIdDTO
from src.domain.entities.school import School

@pytest.mark.asyncio
async def test_should_return_school_when_found():
    # Arrange (Preparação)
    mock_repository = Mock()
    
    # Simulamos uma Escola falsa retornada pelo banco
    fake_school = Mock(spec=School) 
    
    # Configura o mock para retornar a escola falsa de forma assíncrona
    mock_repository.get_by_id = AsyncMock(return_value=fake_school)

    use_case = GetSchoolById(school_repository=mock_repository)
    dto = GetSchoolByIdDTO(id="123")

    # Act (Ação)
    result = await use_case.execute(dto)

    # Assert (Verificação)
    assert result == fake_school
    mock_repository.get_by_id.assert_called_once_with("123")

@pytest.mark.asyncio
async def test_should_return_none_when_not_found():
    # Arrange
    mock_repository = Mock()
    # Configura o mock para retornar None (não achou no banco)
    mock_repository.get_by_id = AsyncMock(return_value=None)

    use_case = GetSchoolById(school_repository=mock_repository)
    dto = GetSchoolByIdDTO(id="999")

    # Act
    result = await use_case.execute(dto)

    # Assert
    assert result is None