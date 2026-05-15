import pytest
from unittest.mock import AsyncMock
from src.application.state.get_state_summary.get_state_summary import GetStateSummaryUseCase
from src.domain.entities.city_aggregation import CityAggregation, CityEducacao, CitySocioeconomico

@pytest.mark.asyncio
async def test_get_state_summary_success():
  
    mock_repo = AsyncMock()
    
    mock_repo.get_cities_data_by_state.return_value = [
        CityAggregation(
            educacao=CityEducacao(total_escolas=10, total_alunos=100, pct_com_biblioteca=50.0, pct_com_internet=100.0, pct_com_lab_informatica=0.0, pct_sem_acessibilidade=0.0, ideb_iniciais=5.0, ideb_finais=0.0),
            socioeconomico=CitySocioeconomico(populacao=1000, taxa_desemprego=10.0)
        ),
        CityAggregation(
            educacao=CityEducacao(total_escolas=10, total_alunos=100, pct_com_biblioteca=50.0, pct_com_internet=0.0, pct_com_lab_informatica=0.0, pct_sem_acessibilidade=0.0, ideb_iniciais=6.0, ideb_finais=0.0),
            socioeconomico=CitySocioeconomico(populacao=3000, taxa_desemprego=2.0)
        )
    ]

    use_case = GetStateSummaryUseCase(mock_repo)
    result = await use_case.execute("PB")

  
    assert result is not None
    assert result.sg_uf == "PB"
    assert result.educacao.total_escolas == 20
    assert result.educacao.pct_com_biblioteca == 50.0 
    assert result.educacao.avg_ideb_iniciais == 5.5
    assert result.socioeconomico.indicadores is not None
    assert result.socioeconomico.indicadores["taxa_desemprego_media"] == 4.0