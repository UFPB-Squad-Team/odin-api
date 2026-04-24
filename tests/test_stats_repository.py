import pytest
from src.infrastructure.database.repository.mongo_stats_repository import MongoStatsRepository
from src.infrastructure.database.config.connect_db import mongodb # Importa a conexão
from src.domain.entities.stats import SummaryStats
from src.infrastructure.database.mapper.school_mapper import MongoSchoolMapper
import pytest_asyncio

# Isso garante que o loop de eventos não feche entre um teste e outro
@pytest.fixture(scope="module")
def event_loop():
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.mark.asyncio
async def test_get_summary_stats_should_return_summary_stats_entity():
    # 1. Garante a conexão manual no teste
    if not mongodb.is_connected:
        await mongodb.connect()

    # 2. Pega a coleção real
    schools_collection = mongodb.get_collection("schools")

    # 3. Instancia o repo com o objeto de coleção real
    repo = MongoStatsRepository(
        collection=schools_collection,
        mapper_to_domain=MongoSchoolMapper.to_domain,
        field_map={},
        default_sort_field="municipioNome"
    )

    result = await repo.get_summary_stats()
    assert isinstance(result, SummaryStats)
    assert result.total_escolas >= 0

@pytest.mark.asyncio
async def test_get_summary_stats_grouping_keys():
    if not mongodb.is_connected:
        await mongodb.connect()
        
    schools_collection = mongodb.get_collection("schools")

    repo = MongoStatsRepository(
        collection=schools_collection,
        mapper_to_domain=MongoSchoolMapper.to_domain,
        field_map={},
        default_sort_field="municipioNome"
    )
    
    result = await repo.get_summary_stats()
    assert isinstance(result.por_dependencia, dict)