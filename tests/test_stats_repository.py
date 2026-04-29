import pytest
from tests.factories import FakeCollection 
from src.infrastructure.database.repository.mongo_stats_repository import MongoStatsRepository

@pytest.mark.asyncio
async def test_get_summary_stats_should_call_aggregate_with_correct_pipeline():
   
    fake_data = [{
        "totais": [{"total_escolas": 5, "qtd_internet": 3, "qtd_biblioteca": 2, "qtd_informatica": 1}],
        "dependencia": [{"_id": "Estadual", "count": 5}],
        "zona": [{"_id": "Urbana", "count": 5}],
        "municipios": [{"_id": "2507507"}]
    }]
    
    
    fake_collection = FakeCollection(documents=fake_data)
    
   
    repository = MongoStatsRepository(collection=fake_collection)

   
    result = await repository.get_summary_stats()

   
    assert fake_collection.aggregate_pipeline is not None
    
    
    assert fake_collection.aggregate_pipeline[0]["$match"]["estadoSigla"] == "PB"
    

    assert "$facet" in fake_collection.aggregate_pipeline[1]
    
    
    assert result["totais"][0]["total_escolas"] == 5
    assert len(result["municipios"]) == 1   