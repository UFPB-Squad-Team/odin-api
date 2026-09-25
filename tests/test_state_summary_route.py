import httpx
import pytest

from src.domain.entities.state_summary import (
    EducacaoStateStats,
    SocioeconomicoStateStats,
    StateSummary,
)
from src.main import app
from src.presentation.http.controller.state.get_state_summary_controller import (
    get_use_case,
)


class FakeGetStateSummaryUseCase:
    def __init__(self, result: StateSummary | None):
        self.result = result
        self.received_sg_uf: str | None = None

    async def execute(self, sg_uf: str) -> StateSummary | None:
        self.received_sg_uf = sg_uf
        return self.result


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_state_summary_route_returns_paraiba_aggregates():
    summary = StateSummary(
        sg_uf="PB",
        estado="Paraíba",
        total_municipios=223,
        educacao=EducacaoStateStats(
            total_escolas=3200,
            total_alunos=650000,
            avg_ideb_iniciais=5.1,
        ),
        socioeconomico=SocioeconomicoStateStats(
            populacao_total=3974495,
            indicadores={"taxa_desemprego_media": 8.4},
        ),
    )
    fake_use_case = FakeGetStateSummaryUseCase(summary)
    app.dependency_overrides[get_use_case] = lambda: fake_use_case

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/estados/PB/resumo")

    assert response.status_code == 200
    assert fake_use_case.received_sg_uf == "PB"
    assert response.json() == {
        "sg_uf": "PB",
        "estado": "Paraíba",
        "total_municipios": 223,
        "educacao": {
            "metodo_agregacao": "soma_absoluta",
            "total_escolas": 3200,
            "total_alunos": 650000,
            "pct_com_biblioteca": None,
            "pct_com_internet": None,
            "pct_com_internet_alunos": None,
            "pct_com_lab_informatica": None,
            "pct_com_lab_ciencias": None,
            "pct_sem_acessibilidade": None,
            "pct_com_agua_potavel": None,
            "pct_com_energia_publica": None,
            "pct_com_esgoto_rede_publica": None,
            "pct_com_coleta_lixo": None,
            "pct_com_quadra_esportes": None,
            "pct_com_cozinha": None,
            "pct_com_refeitorio": None,
            "avg_ideb_iniciais": 5.1,
            "avg_ideb_finais": None,
            "avg_ideb_ensino_medio": None,
            "avg_afd_anos_iniciais": None,
            "avg_afd_anos_finais": None,
            "avg_afd_ensino_medio": None,
            "avg_tdi_anos_iniciais": None,
            "avg_tdi_anos_finais": None,
            "avg_tdi_ensino_medio": None,
            "avg_taxa_aprovacao_ai": None,
            "avg_taxa_aprovacao_af": None,
            "avg_taxa_aprovacao_em": None,
            "avg_taxa_abandono_ai": None,
            "avg_taxa_abandono_af": None,
            "avg_taxa_abandono_em": None,
            "avg_docentes_superior_ai": None,
            "avg_docentes_superior_af": None,
            "avg_docentes_superior_em": None,
            "avg_horas_aula_ai": None,
            "avg_horas_aula_af": None,
            "avg_horas_aula_em": None,
            "avg_alunos_turma_ai": None,
            "avg_alunos_turma_af": None,
            "avg_alunos_turma_em": None,
        },
        "socioeconomico": {
            "metodo_agregacao": "media_ponderada",
            "populacao_total": 3974495,
            "indicadores": {"taxa_desemprego_media": 8.4},
        },
    }


@pytest.mark.asyncio
async def test_state_summary_route_returns_404_when_state_has_no_data():
    app.dependency_overrides[get_use_case] = lambda: FakeGetStateSummaryUseCase(None)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/estados/ZZ/resumo")

    assert response.status_code == 404
    assert response.json() == {
        "error": "NOT_FOUND",
        "message": "Dados não encontrados para o estado: ZZ",
    }


@pytest.mark.asyncio
async def test_state_summary_route_rejects_invalid_uf_length():
    app.dependency_overrides[get_use_case] = lambda: FakeGetStateSummaryUseCase(None)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/estados/P/resumo")

    assert response.status_code == 422
