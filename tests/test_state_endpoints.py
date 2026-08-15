"""State endpoints integration tests for the multi-state expansion (ODIN-B11)."""

import httpx
import pytest

from src.domain.entities.state import State
from src.main import app
from src.presentation.http.controller.state.list_states_controller import (
    get_use_case as get_list_states_use_case,
)

NORDESTE = [
    ("AL", "Alagoas"),
    ("BA", "Bahia"),
    ("CE", "Ceará"),
    ("MA", "Maranhão"),
    ("PB", "Paraíba"),
    ("PE", "Pernambuco"),
    ("PI", "Piauí"),
    ("RN", "Rio Grande do Norte"),
    ("SE", "Sergipe"),
]


class FakeListStatesUseCase:
    def __init__(self, states=None):
        self.states = states or [
            State(id=sigla, nome=nome, sigla=sigla) for sigla, nome in NORDESTE
        ]
        self.received_q = None

    async def execute(self, q=None):
        self.received_q = q
        if q:
            lowered = q.strip().lower()
            return [
                state
                for state in self.states
                if lowered in state.sigla.lower() or lowered in state.nome.lower()
            ]
        return self.states


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_states_returns_nine_nordeste_states():
    fake = FakeListStatesUseCase()
    app.dependency_overrides[get_list_states_use_case] = lambda: fake

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/estados")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 9
    assert {state["sigla"] for state in payload} == {sigla for sigla, _ in NORDESTE}


@pytest.mark.asyncio
async def test_list_states_fuzzy_search_by_sigla():
    fake = FakeListStatesUseCase()
    app.dependency_overrides[get_list_states_use_case] = lambda: fake

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/estados?q=pb")

    assert response.status_code == 200
    payload = response.json()
    assert [state["sigla"] for state in payload] == ["PB"]
    assert fake.received_q == "pb"


@pytest.mark.asyncio
async def test_state_summary_route_supports_multiple_states():
    from src.domain.entities.state_summary import (
        EducacaoStateStats,
        SocioeconomicoStateStats,
        StateSummary,
    )
    from src.presentation.http.controller.state.get_state_summary_controller import (
        get_use_case as get_state_summary_use_case,
    )

    class FakeGetStateSummaryUseCase:
        async def execute(self, sg_uf: str):
            if sg_uf != "PE":
                return None
            return StateSummary(
                sg_uf="PE",
                estado="Pernambuco",
                total_municipios=185,
                educacao=EducacaoStateStats(
                    total_escolas=12000,
                    total_alunos=1800000,
                    avg_ideb_iniciais=4.9,
                ),
                socioeconomico=SocioeconomicoStateStats(
                    populacao_total=9058931,
                    indicadores={},
                ),
            )

    app.dependency_overrides[get_state_summary_use_case] = (
        lambda: FakeGetStateSummaryUseCase()
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/estados/PE/resumo")

    assert response.status_code == 200
    payload = response.json()
    assert payload["sg_uf"] == "PE"
    assert payload["estado"] == "Pernambuco"
    assert payload["educacao"]["total_escolas"] == 12000
    assert payload["socioeconomico"]["populacao_total"] == 9058931
