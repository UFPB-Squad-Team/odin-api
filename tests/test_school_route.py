import pytest
import httpx

from src.domain.value_objects.pagination import PaginatedResponse
from src.main import app
from src.presentation.http.controller.school.callable.school_callable import (
    get_school_by_id_use_case,
    get_list_all_schools_use_case,
)
from src.application.school.get_school_by_id.get_school_by_id_dto import (
    GetSchoolByIdDTO,
)

from tests.factories import build_school


class FakeListAllSchoolsUseCase:
    async def execute(self, dto):
        return PaginatedResponse(
            items=[build_school()],
            total_items=1,
            page=dto.page,
            page_size=dto.page_size,
        )


class FakeGetSchoolByIdUseCase:
    async def execute(self, dto: GetSchoolByIdDTO):
        if dto.id == "missing-id":
            return None
        school = build_school()
        school.id = dto.id
        return school


@pytest.mark.asyncio
async def test_school_list_route_returns_paginated_payload(monkeypatch):
    async def fake_connect():
        return True

    async def fake_disconnect():
        return None

    from src.infrastructure.database.config.connect_db import mongodb

    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    app.dependency_overrides[get_list_all_schools_use_case] = lambda: FakeListAllSchoolsUseCase()
    app.dependency_overrides[get_school_by_id_use_case] = lambda: FakeGetSchoolByIdUseCase()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/all?page=1&page_size=1")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_items"] == 1
    assert payload["page"] == 1
    assert payload["page_size"] == 1
    assert payload["schools"][0]["escola_nome"] == "Escola A"


@pytest.mark.asyncio
async def test_school_list_route_rejects_deep_offset(monkeypatch):
    async def fake_connect():
        return True

    async def fake_disconnect():
        return None

    from src.infrastructure.database.config.connect_db import mongodb

    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    app.dependency_overrides[get_list_all_schools_use_case] = lambda: FakeListAllSchoolsUseCase()
    app.dependency_overrides[get_school_by_id_use_case] = lambda: FakeGetSchoolByIdUseCase()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/all?page=999999&page_size=100")

    app.dependency_overrides.clear()

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_school_detail_route_returns_school_when_found(monkeypatch):
    async def fake_connect():
        return True

    async def fake_disconnect():
        return None

    from src.infrastructure.database.config.connect_db import mongodb

    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    app.dependency_overrides[get_school_by_id_use_case] = lambda: FakeGetSchoolByIdUseCase()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/68c8d9747e1b2e5af20f3cd9")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "68c8d9747e1b2e5af20f3cd9"


@pytest.mark.asyncio
async def test_school_detail_route_returns_404_when_missing(monkeypatch):
    async def fake_connect():
        return True

    async def fake_disconnect():
        return None

    from src.infrastructure.database.config.connect_db import mongodb

    monkeypatch.setattr(mongodb, "connect", fake_connect)
    monkeypatch.setattr(mongodb, "disconnect", fake_disconnect)
    app.dependency_overrides[get_school_by_id_use_case] = lambda: FakeGetSchoolByIdUseCase()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/missing-id")

    app.dependency_overrides.clear()

    assert response.status_code == 404