import pytest
from tests.factories import FakeCollection 
from src.infrastructure.database.repository.mongo_stats_repository import MongoStatsRepository

@pytest.mark.asyncio
async def test_get_summary_stats_should_call_aggregate_with_correct_pipeline():
    # 1. ARRANGE (Preparação)
    # Simulamos o retorno exato que o MongoDB daria após o $facet
    fake_data = [{
        "totais": [{"total_escolas": 5, "qtd_internet": 3, "qtd_biblioteca": 2, "qtd_informatica": 1}],
        "dependencia": [{"_id": "Estadual", "count": 5}],
        "zona": [{"_id": "Urbana", "count": 5}],
        "municipios": [{"_id": "2507507"}]
    }]
    
    # Usamos a fábrica do projeto como o Samuel sugeriu
    fake_collection = FakeCollection(documents=fake_data)
    
    # O repositório agora recebe apenas a collection (sem herança da Base)
    repository = MongoStatsRepository(collection=fake_collection)

    # 2. ACT (Ação)
    result = await repository.get_summary_stats()

    # 3. ASSERT (Verificação)
    # Prova real: O pipeline foi montado?
    assert fake_collection.aggregate_pipeline is not None
    
    # Prova real: O primeiro estágio é o $match por PB (Eficiência pedida pelo Brenno)
    assert fake_collection.aggregate_pipeline[0]["$match"]["estadoSigla"] == "PB"
    
    # Prova real: O segundo estágio é o $facet (Consolidação de dados)
    assert "$facet" in fake_collection.aggregate_pipeline[1]
    
    # Verifica se os dados retornados batem com o "fake"
    assert result["totais"][0]["total_escolas"] == 5
    assert len(result["municipios"]) == 1   