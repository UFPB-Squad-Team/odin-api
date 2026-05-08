import httpx
import pytest

from src.domain.entities.municipio import MunicipioCatalogItem, MunicipioResumo
from src.main import app
from src.presentation.http.controller.aggregation.callable.aggregation_callable import (
    get_city_aggregations_use_case,
    get_neighborhood_aggregations_use_case,
)
from src.presentation.http.controller.school.callable.school_callable import (
    get_bairro_by_school_id_use_case,
    get_bairros_geojson_use_case,
    get_list_all_schools_use_case,
    get_paraiba_geojson_use_case,
    get_school_by_id_use_case,
)
from src.presentation.http.controller.municipio.callable.municipio_callable import (
    get_list_municipios_use_case,
    get_municipio_resumo_use_case,
)


class FakeListMunicipiosUseCase:
    def __init__(self):
        self.received_dto = None

    async def execute(self, dto):
        self.received_dto = dto
        return [
            MunicipioCatalogItem(id="2504009", nome="Campina Grande", sg_uf="PB"),
            MunicipioCatalogItem(id="2507507", nome="João Pessoa", sg_uf="PB"),
        ]


class FakeGetMunicipioResumoUseCase:
    _missing = object()

    def __init__(self, resumo: MunicipioResumo | None | object = _missing):
        if resumo is self._missing:
            resumo = MunicipioResumo(
                municipioIdIbge="2507507",
                municipio="João Pessoa",
                sg_uf="PB",
                total_escolas=412,
                total_matriculas=98000,
                total_bairros=64,
                pct_com_biblioteca=62.3,
                pct_com_internet=88.1,
                pct_com_lab_informatica=45.2,
                pct_sem_acessibilidade=31.0,
                mediaIdebAnosIniciais=5.12,
                tem_bairros_oficiais=True,
                source="municipio_indicadores",
            )

        self.resumo = resumo

    async def execute(self, dto):
        return self.resumo


def _override_global_use_cases():
    app.dependency_overrides[get_list_all_schools_use_case] = lambda: object()
    app.dependency_overrides[get_school_by_id_use_case] = lambda: object()
    app.dependency_overrides[get_paraiba_geojson_use_case] = lambda: object()
    app.dependency_overrides[get_bairros_geojson_use_case] = lambda: object()
    app.dependency_overrides[get_bairro_by_school_id_use_case] = lambda: object()
    app.dependency_overrides[get_city_aggregations_use_case] = lambda: object()
    app.dependency_overrides[get_neighborhood_aggregations_use_case] = lambda: object()


@pytest.mark.asyncio
async def test_municipios_route_returns_light_catalog(monkeypatch):
    async def fake_connect():
        return True

    async def fake_disconnect():
        return None

    from src.infrastructure.database.config.connect_db import mongodb

    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)

    _override_global_use_cases()
    app.dependency_overrides[get_list_municipios_use_case] = lambda: FakeListMunicipiosUseCase()
    app.dependency_overrides[get_municipio_resumo_use_case] = lambda: FakeGetMunicipioResumoUseCase()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/municipios?sg_uf=pb")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload == [
        {"id": "2504009", "nome": "Campina Grande", "sg_uf": "PB"},
        {"id": "2507507", "nome": "João Pessoa", "sg_uf": "PB"},
    ]


@pytest.mark.asyncio
async def test_municipio_resumo_route_returns_summary(monkeypatch):
    async def fake_connect():
        return True

    async def fake_disconnect():
        return None

    from src.infrastructure.database.config.connect_db import mongodb

    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)

    _override_global_use_cases()
    app.dependency_overrides[get_list_municipios_use_case] = lambda: FakeListMunicipiosUseCase()
    app.dependency_overrides[get_municipio_resumo_use_case] = lambda: FakeGetMunicipioResumoUseCase()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/municipios/2507507/resumo")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["municipioIdIbge"] == "2507507"
    assert payload["source"] == "municipio_indicadores"
    assert payload["tem_bairros_oficiais"] is True
    assert payload["total_bairros"] == 64
    assert payload["mediaIdebAnosIniciais"] == 5.12


@pytest.mark.asyncio
async def test_municipio_resumo_route_returns_404_when_missing(monkeypatch):
    async def fake_connect():
        return True

    async def fake_disconnect():
        return None

    from src.infrastructure.database.config.connect_db import mongodb

    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)

    _override_global_use_cases()
    app.dependency_overrides[get_list_municipios_use_case] = lambda: FakeListMunicipiosUseCase()
    app.dependency_overrides[get_municipio_resumo_use_case] = lambda: FakeGetMunicipioResumoUseCase(resumo=None)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/municipios/9999999/resumo")

    app.dependency_overrides.clear()

    assert response.status_code == 404
