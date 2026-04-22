import httpx
import pytest

from src.main import app
from src.presentation.http.controller.aggregation.callable.aggregation_callable import (
    get_city_aggregations_use_case,
    get_neighborhood_aggregations_use_case,
)


class FakeGetCityAggregationsUseCase:
    async def execute(
        self,
        co_municipio: str | None = None,
        sg_uf: str | None = None,
    ):
        source = "setor_indicadores" if co_municipio == "2507507" else "municipio_indicadores"
        resolved_uf = sg_uf or "PB"
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": co_municipio or "2507507",
                    "geometry": {"type": "Point", "coordinates": [-34.86, -7.12]},
                    "properties": {
                        "municipioIdIbge": co_municipio or "2507507",
                        "co_municipio": co_municipio or "2507507",
                        "municipio": "Joao Pessoa",
                        "uf": resolved_uf,
                        "total_escolas": 123,
                        "total_alunos": 45678,
                        "avg_ideb": 5.1,
                        "source": source,
                    },
                }
            ],
        }


class FakeGetNeighborhoodAggregationsUseCase:
    async def execute(
        self,
        municipio_id_ibge: str,
        bairro: str | None = None,
        include_geometria: bool = False,
    ):
        resolved_bairro = bairro or "Area Urbana Integrada"
        return [
            {
                "_id": "69e211325157cf0f20312a59",
                "municipio": "Joao Pessoa",
                "bairro": resolved_bairro,
                "cd_bairro_ibge": "2507507001",
                "geometria": (
                    {"type": "Point", "coordinates": [-34.83, -7.10]}
                    if include_geometria
                    else None
                ),
                "municipioIdIbge": municipio_id_ibge,
                "pct_com_biblioteca": 50,
                "pct_com_internet": 100,
                "pct_com_lab_informatica": 25,
                "pct_sem_acessibilidade": 10,
                "sg_uf": "PB",
                "total_escolas": 10,
                "total_matriculas": 4500,
                "tem_bairro_official": bairro is not None,
                "source": "bairro_indicadores",
            }
        ]


@pytest.mark.asyncio
async def test_get_city_aggregations_route_returns_200_and_feature_collection(monkeypatch):
    async def fake_connect():
        return True

    async def fake_disconnect():
        return None

    from src.infrastructure.database.config.connect_db import mongodb

    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    app.dependency_overrides[get_city_aggregations_use_case] = (
        lambda: FakeGetCityAggregationsUseCase()
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/aggregations/cities?municipioIdIbge=2507507")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "FeatureCollection"
    assert payload["features"][0]["properties"]["source"] == "setor_indicadores"
    assert payload["features"][0]["geometry"]["coordinates"] == [-34.86, -7.12]


@pytest.mark.asyncio
async def test_get_neighborhood_aggregations_route_returns_200(monkeypatch):
    async def fake_connect():
        return True

    async def fake_disconnect():
        return None

    from src.infrastructure.database.config.connect_db import mongodb

    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    app.dependency_overrides[get_neighborhood_aggregations_use_case] = (
        lambda: FakeGetNeighborhoodAggregationsUseCase()
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/aggregations/neighborhoods?municipio_id=2507507")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload[0]["_id"] == "69e211325157cf0f20312a59"
    assert payload[0]["bairro"] == "Area Urbana Integrada"
    assert payload[0]["geometria"] is None
    assert payload[0]["source"] == "bairro_indicadores"


@pytest.mark.asyncio
async def test_get_neighborhood_aggregations_route_can_include_geometria(monkeypatch):
    async def fake_connect():
        return True

    async def fake_disconnect():
        return None

    from src.infrastructure.database.config.connect_db import mongodb

    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    app.dependency_overrides[get_neighborhood_aggregations_use_case] = (
        lambda: FakeGetNeighborhoodAggregationsUseCase()
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/aggregations/neighborhoods?municipio_id=2507507&include_geometria=true"
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["geometria"]["type"] == "Point"


@pytest.mark.asyncio
async def test_get_city_aggregations_route_accepts_sg_uf_filter(monkeypatch):
    async def fake_connect():
        return True

    async def fake_disconnect():
        return None

    from src.infrastructure.database.config.connect_db import mongodb

    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    app.dependency_overrides[get_city_aggregations_use_case] = (
        lambda: FakeGetCityAggregationsUseCase()
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/aggregations/cities?sg_uf=pb")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["features"][0]["properties"]["uf"] == "PB"


@pytest.mark.asyncio
async def test_get_neighborhood_aggregations_route_requires_city_param(monkeypatch):
    async def fake_connect():
        return True

    async def fake_disconnect():
        return None

    from src.infrastructure.database.config.connect_db import mongodb

    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    app.dependency_overrides[get_neighborhood_aggregations_use_case] = (
        lambda: FakeGetNeighborhoodAggregationsUseCase()
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/aggregations/neighborhoods")

    app.dependency_overrides.clear()

    assert response.status_code == 422
