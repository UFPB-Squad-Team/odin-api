import pytest
import httpx

from src.application.search.universal_search.universal_search_dto import (
    SearchResultItem,
    UniversalSearchOutputDTO,
)
from src.main import app
from src.presentation.http.controller.search.callable.search_callable import (
    get_universal_search_use_case,
)


class FakeUniversalSearchUseCase:
    async def execute(self, dto):
        return UniversalSearchOutputDTO(
            results=[
                SearchResultItem(
                    id="1",
                    kind="escola",
                    label="Escola A",
                    subtitle="Joao Pessoa • Centro",
                    coordinates=(-34.86, -7.12),
                    municipio_id_ibge="2507507",
                    metadata={"source": "fake"},
                )
            ],
            total=1,
            query=dto.q,
        )


@pytest.mark.asyncio
async def test_universal_search_route_returns_typed_results(monkeypatch):
    async def fake_connect():
        return True

    async def fake_disconnect():
        return None

    from src.infrastructure.database.config.connect_db import mongodb

    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)

    app.dependency_overrides[get_universal_search_use_case] = lambda: FakeUniversalSearchUseCase()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/busca/universal?q=Epitacio&limit=2")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["query"] == "Epitacio"
    assert payload["results"][0]["kind"] == "escola"
    assert payload["results"][0]["coordinates"] == [-34.86, -7.12]


@pytest.mark.asyncio
async def test_universal_search_route_rejects_short_queries(monkeypatch):
    async def fake_connect():
        return True

    async def fake_disconnect():
        return None

    from src.infrastructure.database.config.connect_db import mongodb

    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)

    app.dependency_overrides[get_universal_search_use_case] = lambda: FakeUniversalSearchUseCase()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/busca/universal?q=a")

    app.dependency_overrides.clear()

    assert response.status_code == 422