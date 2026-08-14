import httpx
import pytest

from src.main import app
from src.presentation.http.controller.aggregation.callable.aggregation_callable import (
    get_city_aggregations_use_case,
    get_neighborhood_aggregations_use_case,
)


class FakeGetCityAggregationsUseCase:
    def __init__(self):
        self.received_sg_uf: list[str] | None = None

    async def execute(
        self,
        co_municipio: str | None = None,
        sg_uf: list[str] | None = None,
        include_geometria: bool = False,
    ):
        self.received_sg_uf = sg_uf
        source = (
            "setor_indicadores"
            if co_municipio == "2507507"
            else "municipio_indicadores"
        )
        resolved_ufs = sg_uf or ["PB"]
        geometry = {"type": "Point", "coordinates": [-34.86, -7.12]}
        if include_geometria:
            geometry = {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-34.9, -7.2],
                        [-34.8, -7.2],
                        [-34.8, -7.1],
                        [-34.9, -7.1],
                        [-34.9, -7.2],
                    ]
                ],
            }
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": co_municipio or str(2507507 + index),
                    "geometry": geometry,
                    "properties": {
                        "municipioIdIbge": co_municipio or str(2507507 + index),
                        "co_municipio": co_municipio or str(2507507 + index),
                        "municipio": "Joao Pessoa",
                        "uf": resolved_uf,
                        "total_escolas": 123,
                        "total_alunos": 45678,
                        "avg_ideb": 5.1,
                        "socioeconomico": {
                            "anoReferencia": 2022,
                            "fonte": "IBGE Censo Demografico 2022",
                            "populacao": {"total": 817511},
                        },
                        "source": source,
                    },
                }
                for index, resolved_uf in enumerate(resolved_ufs)
            ],
        }


class FakeGetNeighborhoodAggregationsUseCase:
    def __init__(self):
        self.received_sg_uf: list[str] | None = None

    async def execute(
        self,
        municipio_id_ibge: str,
        bairro: str | None = None,
        include_geometria: bool = False,
        sg_uf: list[str] | None = None,
    ):
        self.received_sg_uf = sg_uf
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
                "tem_bairro_oficial": bairro is not None,
                "nivel": "bairro",
                "socioeconomico": {
                    "anoReferencia": 2022,
                    "fonte": "IBGE",
                    "populacao": {"total": 14000},
                },
                "educacao": {
                    "totalEscolas": 10,
                    "totalMatriculas": 4500,
                    "pctComInternet": 100,
                },
                "source": "bairros_indicadores",
            }
        ]


@pytest.mark.asyncio
async def test_get_city_aggregations_route_returns_200_and_feature_collection(
    monkeypatch,
):
    async def fake_connect():
        return True

    async def fake_disconnect():
        return None

    from src.infrastructure.database.config.connect_db import mongodb

    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    fake_use_case = FakeGetCityAggregationsUseCase()
    app.dependency_overrides[get_city_aggregations_use_case] = lambda: fake_use_case

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/aggregations/cities?municipioIdIbge=2507507"
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "FeatureCollection"
    assert payload["features"][0]["properties"]["source"] == "setor_indicadores"
    assert payload["features"][0]["geometry"]["coordinates"] == [-34.86, -7.12]
    assert (
        payload["features"][0]["properties"]["socioeconomico"]["anoReferencia"] == 2022
    )
    assert fake_use_case.received_sg_uf is None


@pytest.mark.asyncio
async def test_get_neighborhood_aggregations_route_returns_200(monkeypatch):
    async def fake_connect():
        return True

    async def fake_disconnect():
        return None

    from src.infrastructure.database.config.connect_db import mongodb

    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    fake_use_case = FakeGetNeighborhoodAggregationsUseCase()
    app.dependency_overrides[get_neighborhood_aggregations_use_case] = (
        lambda: fake_use_case
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/aggregations/neighborhoods?municipio_id=2507507"
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload[0]["_id"] == "69e211325157cf0f20312a59"
    assert payload[0]["bairro"] == "Area Urbana Integrada"
    assert payload[0]["geometria"] is None
    assert payload[0]["tem_bairro_oficial"] is False
    assert payload[0]["nivel"] == "bairro"
    assert payload[0]["socioeconomico"]["anoReferencia"] == 2022
    assert payload[0]["educacao"]["totalMatriculas"] == 4500
    assert payload[0]["source"] == "bairros_indicadores"
    assert fake_use_case.received_sg_uf is None


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
    assert payload["type"] == "FeatureCollection"
    assert payload["features"][0]["geometry"]["type"] == "Point"
    assert payload["features"][0]["properties"]["tem_bairro_oficial"] is False
    assert payload["features"][0]["properties"]["nivel"] == "bairro"
    assert (
        payload["features"][0]["properties"]["socioeconomico"]["anoReferencia"] == 2022
    )
    assert payload["features"][0]["properties"]["educacao"]["totalMatriculas"] == 4500


@pytest.mark.asyncio
async def test_get_city_aggregations_route_accepts_sg_uf_filter(monkeypatch):
    async def fake_connect():
        return True

    async def fake_disconnect():
        return None

    from src.infrastructure.database.config.connect_db import mongodb

    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    fake_use_case = FakeGetCityAggregationsUseCase()
    app.dependency_overrides[get_city_aggregations_use_case] = lambda: fake_use_case

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/aggregations/cities?sg_uf=pb")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["features"][0]["properties"]["uf"] == "PB"
    assert fake_use_case.received_sg_uf == ["PB"]


@pytest.mark.asyncio
async def test_get_city_aggregations_route_accepts_multiple_sg_uf_filters(monkeypatch):
    async def fake_connect():
        return True

    async def fake_disconnect():
        return None

    from src.infrastructure.database.config.connect_db import mongodb

    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    fake_use_case = FakeGetCityAggregationsUseCase()
    app.dependency_overrides[get_city_aggregations_use_case] = lambda: fake_use_case

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/aggregations/cities?sg_uf=pb&sg_uf=PE")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert fake_use_case.received_sg_uf == ["PB", "PE"]
    payload = response.json()
    assert {feature["properties"]["uf"] for feature in payload["features"]} == {
        "PB",
        "PE",
    }


@pytest.mark.asyncio
async def test_get_neighborhood_aggregations_route_accepts_multiple_sg_uf_filters(
    monkeypatch,
):
    async def fake_connect():
        return True

    async def fake_disconnect():
        return None

    from src.infrastructure.database.config.connect_db import mongodb

    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    fake_use_case = FakeGetNeighborhoodAggregationsUseCase()
    app.dependency_overrides[get_neighborhood_aggregations_use_case] = (
        lambda: fake_use_case
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/aggregations/neighborhoods"
            "?municipio_id=2507507&sg_uf=pb&sg_uf=PE"
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert fake_use_case.received_sg_uf == ["PB", "PE"]


@pytest.mark.asyncio
async def test_aggregation_routes_reject_invalid_sg_uf_length(monkeypatch):
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
    app.dependency_overrides[get_neighborhood_aggregations_use_case] = (
        lambda: FakeGetNeighborhoodAggregationsUseCase()
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        city_response = await client.get("/api/v1/aggregations/cities?sg_uf=P")
        neighborhood_response = await client.get(
            "/api/v1/aggregations/neighborhoods?municipio_id=2507507&sg_uf=PER"
        )

    app.dependency_overrides.clear()

    assert city_response.status_code == 422
    assert neighborhood_response.status_code == 422


def test_aggregation_sg_uf_filters_are_documented_as_arrays_in_openapi():
    schema = app.openapi()

    for path in (
        "/api/v1/aggregations/cities",
        "/api/v1/aggregations/neighborhoods",
    ):
        parameters = schema["paths"][path]["get"]["parameters"]
        sg_uf = next(
            parameter for parameter in parameters if parameter["name"] == "sg_uf"
        )

        assert sg_uf["schema"]["anyOf"][0]["type"] == "array"
        assert "?sg_uf=PB&sg_uf=PE" in sg_uf["description"]


@pytest.mark.asyncio
async def test_get_city_aggregations_route_can_include_full_geometry(monkeypatch):
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
        response = await client.get(
            "/api/v1/aggregations/cities?include_geometria=true"
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["features"][0]["geometry"]["type"] == "Polygon"


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
