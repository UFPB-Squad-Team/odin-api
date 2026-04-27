import pytest
import httpx

from src.domain.value_objects.pagination import PaginatedResponse
from src.domain.value_objects.query import QueryFilter
from src.main import app
from src.presentation.http.controller.school.callable.school_callable import (
    get_bairro_by_school_id_use_case,
    get_bairros_geojson_use_case,
    get_paraiba_geojson_use_case,
    get_school_by_id_use_case,
    get_list_all_schools_use_case,
)
from src.application.school.get_school_by_id.get_school_by_id_dto import (
    GetSchoolByIdDTO,
)

from tests.factories import build_school


class FakeListAllSchoolsUseCase:
    def __init__(self):
        self.received_dto = None

    async def execute(self, dto):
        self.received_dto = dto
        return PaginatedResponse(
            items=[build_school()],
            total_items=1,
            page=dto.query.page,
            page_size=dto.query.page_size,
            next_cursor=dto.query.cursor,
        )


class FakeGetSchoolByIdUseCase:
    async def execute(self, dto: GetSchoolByIdDTO):
        if dto.id == "missing-id":
            return None
        school = build_school()
        school.id = dto.id
        return school


class FakeGetParaibaGeoJsonUseCase:
    async def execute(self):
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": "school-1",
                    "geometry": {"type": "Point", "coordinates": [-34.86, -7.12]},
                    "properties": {"bairro": "Centro"},
                }
            ],
        }


class FakeGetBairrosGeoJsonUseCase:
    async def execute(self, municipio: str):
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": "Centro",
                    "geometry": {"type": "Point", "coordinates": [-34.86, -7.12]},
                    "properties": {
                        "bairro": "Centro",
                        "municipio_nome": municipio,
                        "qtd_escolas": 10,
                    },
                }
            ],
        }


class FakeGetBairroBySchoolIdUseCase:
    async def execute(self, school_id: str):
        if school_id == "missing-id":
            return None
        return {
            "id": school_id,
            "escola_nome": "Escola A",
            "bairro": "Centro",
            "municipio_nome": "Joao Pessoa",
        }


@pytest.mark.asyncio
async def test_school_list_route_returns_paginated_payload(monkeypatch):
    async def fake_connect(): return True
    async def fake_disconnect(): return None

    from src.infrastructure.database.config.connect_db import mongodb
    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    
    app.dependency_overrides[get_list_all_schools_use_case] = lambda: FakeListAllSchoolsUseCase()
    app.dependency_overrides[get_school_by_id_use_case] = lambda: FakeGetSchoolByIdUseCase()
    app.dependency_overrides[get_paraiba_geojson_use_case] = lambda: FakeGetParaibaGeoJsonUseCase()
    app.dependency_overrides[get_bairros_geojson_use_case] = lambda: FakeGetBairrosGeoJsonUseCase()
    app.dependency_overrides[get_bairro_by_school_id_use_case] = lambda: FakeGetBairroBySchoolIdUseCase()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/all?page=1&page_size=1")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_items"] == 1
    assert payload["page"] == 1
    assert payload["page_size"] == 1
    assert payload["next_cursor"] is None
    assert payload["schools"][0]["escola_nome"] == "Escola A"


@pytest.mark.asyncio
async def test_school_list_route_rejects_deep_offset(monkeypatch):
    async def fake_connect(): return True
    async def fake_disconnect(): return None

    from src.infrastructure.database.config.connect_db import mongodb
    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    
    app.dependency_overrides[get_list_all_schools_use_case] = lambda: FakeListAllSchoolsUseCase()
    app.dependency_overrides[get_school_by_id_use_case] = lambda: FakeGetSchoolByIdUseCase()
    app.dependency_overrides[get_paraiba_geojson_use_case] = lambda: FakeGetParaibaGeoJsonUseCase()
    app.dependency_overrides[get_bairros_geojson_use_case] = lambda: FakeGetBairrosGeoJsonUseCase()
    app.dependency_overrides[get_bairro_by_school_id_use_case] = lambda: FakeGetBairroBySchoolIdUseCase()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/all?page=999999&page_size=100")

    app.dependency_overrides.clear()
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_school_list_route_rejects_unsupported_filter(monkeypatch):
    async def fake_connect(): return True
    async def fake_disconnect(): return None

    from src.infrastructure.database.config.connect_db import mongodb
    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    
    app.dependency_overrides[get_list_all_schools_use_case] = lambda: FakeListAllSchoolsUseCase()
    app.dependency_overrides[get_school_by_id_use_case] = lambda: FakeGetSchoolByIdUseCase()
    app.dependency_overrides[get_paraiba_geojson_use_case] = lambda: FakeGetParaibaGeoJsonUseCase()
    app.dependency_overrides[get_bairros_geojson_use_case] = lambda: FakeGetBairrosGeoJsonUseCase()
    app.dependency_overrides[get_bairro_by_school_id_use_case] = lambda: FakeGetBairroBySchoolIdUseCase()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/schools?filter[hack]=1")

    app.dependency_overrides.clear()
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_school_detail_route_returns_school_when_found(monkeypatch):
    async def fake_connect(): return True
    async def fake_disconnect(): return None

    from src.infrastructure.database.config.connect_db import mongodb
    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    
    app.dependency_overrides[get_school_by_id_use_case] = lambda: FakeGetSchoolByIdUseCase()
    app.dependency_overrides[get_paraiba_geojson_use_case] = lambda: FakeGetParaibaGeoJsonUseCase()
    app.dependency_overrides[get_bairros_geojson_use_case] = lambda: FakeGetBairrosGeoJsonUseCase()
    app.dependency_overrides[get_bairro_by_school_id_use_case] = lambda: FakeGetBairroBySchoolIdUseCase()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/68c8d9747e1b2e5af20f3cd9")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "68c8d9747e1b2e5af20f3cd9"


@pytest.mark.asyncio
async def test_school_detail_route_returns_404_when_missing(monkeypatch):
    async def fake_connect(): return True
    async def fake_disconnect(): return None

    from src.infrastructure.database.config.connect_db import mongodb
    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    
    app.dependency_overrides[get_school_by_id_use_case] = lambda: FakeGetSchoolByIdUseCase()
    app.dependency_overrides[get_paraiba_geojson_use_case] = lambda: FakeGetParaibaGeoJsonUseCase()
    app.dependency_overrides[get_bairros_geojson_use_case] = lambda: FakeGetBairrosGeoJsonUseCase()
    app.dependency_overrides[get_bairro_by_school_id_use_case] = lambda: FakeGetBairroBySchoolIdUseCase()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/missing-id")

    app.dependency_overrides.clear()
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_paraiba_geojson_route_returns_feature_collection(monkeypatch):
    async def fake_connect(): return True
    async def fake_disconnect(): return None

    from src.infrastructure.database.config.connect_db import mongodb
    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    app.dependency_overrides[get_paraiba_geojson_use_case] = lambda: FakeGetParaibaGeoJsonUseCase()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/escolas/geojson/paraiba")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "FeatureCollection"
    assert payload["features"][0]["properties"]["bairro"] == "Centro"


@pytest.mark.asyncio
async def test_get_bairros_geojson_route_returns_aggregated_geojson(monkeypatch):
    async def fake_connect(): return True
    async def fake_disconnect(): return None

    from src.infrastructure.database.config.connect_db import mongodb
    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    app.dependency_overrides[get_bairros_geojson_use_case] = lambda: FakeGetBairrosGeoJsonUseCase()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/bairros/geojson/Joao%20Pessoa")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "FeatureCollection"
    assert payload["features"][0]["properties"]["municipio_nome"] == "Joao Pessoa"


@pytest.mark.asyncio
async def test_get_bairro_by_school_id_route_returns_bairro(monkeypatch):
    async def fake_connect(): return True
    async def fake_disconnect(): return None

    from src.infrastructure.database.config.connect_db import mongodb
    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    app.dependency_overrides[get_bairro_by_school_id_use_case] = lambda: FakeGetBairroBySchoolIdUseCase()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/bairro/68c8d9747e1b2e5af20f3cd9")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    payload = response.json()
    assert payload["bairro"] == "Centro"


@pytest.mark.asyncio
async def test_get_bairro_by_school_id_route_returns_404(monkeypatch):
    async def fake_connect(): return True
    async def fake_disconnect(): return None

    from src.infrastructure.database.config.connect_db import mongodb
    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    app.dependency_overrides[get_bairro_by_school_id_use_case] = lambda: FakeGetBairroBySchoolIdUseCase()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/bairro/missing-id")

    app.dependency_overrides.clear()
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_school_list_route_accepts_name_only_search(monkeypatch):
    async def fake_connect(): return True
    async def fake_disconnect(): return None

    from src.infrastructure.database.config.connect_db import mongodb
    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    
    fake_use_case = FakeListAllSchoolsUseCase()
    app.dependency_overrides[get_list_all_schools_use_case] = lambda: fake_use_case
    app.dependency_overrides[get_school_by_id_use_case] = lambda: FakeGetSchoolByIdUseCase()
    app.dependency_overrides[get_paraiba_geojson_use_case] = lambda: FakeGetParaibaGeoJsonUseCase()
    app.dependency_overrides[get_bairros_geojson_use_case] = lambda: FakeGetBairrosGeoJsonUseCase()
    app.dependency_overrides[get_bairro_by_school_id_use_case] = lambda: FakeGetBairroBySchoolIdUseCase()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/all?search=escola")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert fake_use_case.received_dto.search_term == "escola"
    assert fake_use_case.received_dto.municipio is None


@pytest.mark.asyncio
async def test_school_list_route_accepts_municipio_only_search(monkeypatch):
    async def fake_connect(): return True
    async def fake_disconnect(): return None

    from src.infrastructure.database.config.connect_db import mongodb
    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    
    fake_use_case = FakeListAllSchoolsUseCase()
    app.dependency_overrides[get_list_all_schools_use_case] = lambda: fake_use_case
    app.dependency_overrides[get_school_by_id_use_case] = lambda: FakeGetSchoolByIdUseCase()
    app.dependency_overrides[get_paraiba_geojson_use_case] = lambda: FakeGetParaibaGeoJsonUseCase()
    app.dependency_overrides[get_bairros_geojson_use_case] = lambda: FakeGetBairrosGeoJsonUseCase()
    app.dependency_overrides[get_bairro_by_school_id_use_case] = lambda: FakeGetBairroBySchoolIdUseCase()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/all?municipio=Joao%20Pessoa")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert fake_use_case.received_dto.search_term is None
    assert fake_use_case.received_dto.municipio == "Joao Pessoa"


@pytest.mark.asyncio
async def test_school_list_route_accepts_combined_search_and_municipio(monkeypatch):
    async def fake_connect(): return True
    async def fake_disconnect(): return None

    from src.infrastructure.database.config.connect_db import mongodb
    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    
    fake_use_case = FakeListAllSchoolsUseCase()
    app.dependency_overrides[get_list_all_schools_use_case] = lambda: fake_use_case
    app.dependency_overrides[get_school_by_id_use_case] = lambda: FakeGetSchoolByIdUseCase()
    app.dependency_overrides[get_paraiba_geojson_use_case] = lambda: FakeGetParaibaGeoJsonUseCase()
    app.dependency_overrides[get_bairros_geojson_use_case] = lambda: FakeGetBairrosGeoJsonUseCase()
    app.dependency_overrides[get_bairro_by_school_id_use_case] = lambda: FakeGetBairroBySchoolIdUseCase()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/all?search=estadual&municipio=Joao%20Pessoa")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert fake_use_case.received_dto.search_term == "estadual"
    assert fake_use_case.received_dto.municipio == "Joao Pessoa"


@pytest.mark.asyncio
async def test_school_list_route_preserves_filters_and_cursor_with_search_params(monkeypatch):
    async def fake_connect(): return True
    async def fake_disconnect(): return None

    from src.infrastructure.database.config.connect_db import mongodb
    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    
    fake_use_case = FakeListAllSchoolsUseCase()
    app.dependency_overrides[get_list_all_schools_use_case] = lambda: fake_use_case
    app.dependency_overrides[get_school_by_id_use_case] = lambda: FakeGetSchoolByIdUseCase()
    app.dependency_overrides[get_paraiba_geojson_use_case] = lambda: FakeGetParaibaGeoJsonUseCase()
    app.dependency_overrides[get_bairros_geojson_use_case] = lambda: FakeGetBairrosGeoJsonUseCase()
    app.dependency_overrides[get_bairro_by_school_id_use_case] = lambda: FakeGetBairroBySchoolIdUseCase()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/all?search=centro&cursor=cursor-123&filter[bairro]=Centro&page=1&page_size=10"
        )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    payload = response.json()
    assert payload["page"] == 1
    assert payload["page_size"] == 10
    assert payload["next_cursor"] == "cursor-123"
    assert "total_items" in payload
    assert fake_use_case.received_dto.query.cursor == "cursor-123"
    assert fake_use_case.received_dto.query.filters == [
        QueryFilter(field="bairro", operator="eq", value="Centro")
    ]
