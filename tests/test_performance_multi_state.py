"""Optional performance tests against a real MongoDB (ODIN-B08 / ODIN-B11).

These validate the acceptance criteria: queries filtered by ``estadoSigla``
must return in under 100ms with ~75k documents and use an index (IXSCAN).

Skipped by default. To run, point ``MONGO_URI`` at a local/Atlas MongoDB and
set ``RUN_PERFORMANCE_TESTS=1``:

    $env:RUN_PERFORMANCE_TESTS="1"
    $env:MONGO_URI="mongodb://localhost:27017"
    $env:DATABASE_NAME="odin_perf_test"
    uv run pytest tests/test_performance_multi_state.py -v
"""

import os
import time

import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient

from src.domain.value_objects.query import QueryFilter, QueryOptions
from src.infrastructure.database.config.connect_db import MongoDB
from src.infrastructure.database.repository.mongo_school_repository import (
    MongoSchoolRepository,
)

RUN_PERFORMANCE_TESTS = os.getenv("RUN_PERFORMANCE_TESTS") == "1"
MONGODB_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "odin_perf_test")

UFS = ["PB", "PE", "CE", "RN", "MA", "PI", "AL", "SE", "BA"]
TARGET_SCHOOLS = 75_000
BATCH_SIZE = 5_000


pytestmark = pytest.mark.skipif(
    not RUN_PERFORMANCE_TESTS,
    reason=("set RUN_PERFORMANCE_TESTS=1 to run the real-Mongo performance suite"),
)


def _school_doc(uf_index: int, uf: str, i: int) -> dict:
    return {
        "escolaIdInep": uf_index * 10_000_000 + i + 1,
        "escolaNome": f"Escola {uf} {i}",
        "municipioNome": f"Municipio {uf} {i % 200}",
        "municipioIdIbge": f"{1_000_000 + uf_index * 100_000 + (i % 200):07d}",
        "estadoSigla": uf,
        "dependenciaAdm": "Municipal",
        "tipoLocalizacao": "Urbana",
        "localizacao": {
            "type": "Point",
            "coordinates": [-34.0 + uf_index, -7.0 + uf_index * 0.1],
        },
        "endereco": {"bairro": "Centro"},
        "indicadores": {"anoReferencia": 2025, "totalAlunos": 200, "ideb": 5.5},
        "matriculas": {"totalAlunos": 200, "fundamentalTotal": 200},
        "unrelated_census_payload": "x" * 4096,
    }


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def perf_database():
    assert DATABASE_NAME.startswith(
        "odin_perf_"
    ), "Use an isolated odin_perf_* database"
    client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=10_000)
    db = client[DATABASE_NAME]
    schools = db["escolas"]
    await schools.drop()

    chunk: list[dict] = []
    per_uf = TARGET_SCHOOLS // len(UFS)
    for uf_index, uf in enumerate(UFS):
        for i in range(per_uf + (1 if uf_index < TARGET_SCHOOLS % len(UFS) else 0)):
            chunk.append(_school_doc(uf_index, uf, i))
            if len(chunk) >= BATCH_SIZE:
                await schools.insert_many(chunk)
                chunk = []
    if chunk:
        await schools.insert_many(chunk)

    mongo = MongoDB()
    mongo.client = client
    mongo.database = db
    await mongo._ensure_indexes()

    total = await schools.count_documents({})
    assert total >= TARGET_SCHOOLS, f"expected {TARGET_SCHOOLS} schools, got {total}"

    yield db

    await schools.drop()
    client.close()


def _assert_uses_index(explain: dict) -> None:
    winning_plan = explain.get("queryPlanner", {}).get("winningPlan", {})
    assert "COLLSCAN" not in str(
        winning_plan
    ), "query uses COLLSCAN — expected an index (IXSCAN)"


@pytest.mark.asyncio(loop_scope="module")
async def test_estado_sigla_query_uses_index_and_is_fast(perf_database):
    explain = await perf_database.command(
        "explain",
        {"find": "escolas", "filter": {"estadoSigla": "PB"}},
        verbosity="executionStats",
    )
    _assert_uses_index(explain)
    execution_ms = explain["executionStats"]["executionTimeMillis"]
    assert execution_ms < 100, f"executionTimeMillis={execution_ms} >= 100ms"


@pytest.mark.asyncio(loop_scope="module")
async def test_multi_uf_in_query_uses_index_and_is_fast(perf_database):
    explain = await perf_database.command(
        "explain",
        {"find": "escolas", "filter": {"estadoSigla": {"$in": ["PB", "PE"]}}},
        verbosity="executionStats",
    )
    _assert_uses_index(explain)
    execution_ms = explain["executionStats"]["executionTimeMillis"]
    assert execution_ms < 100, f"executionTimeMillis={execution_ms} >= 100ms"


@pytest.mark.asyncio(loop_scope="module")
async def test_repository_state_filter_page_size_500_is_fast(perf_database):
    collection = perf_database["escolas"]
    repository = MongoSchoolRepository(collection=collection)

    query = QueryOptions(
        page=1,
        page_size=500,
        filters=[QueryFilter(field="estado_sigla", operator="eq", value="PB")],
    )

    start = time.monotonic()
    result = await repository.find_paginated(query)
    elapsed_ms = (time.monotonic() - start) * 1000

    assert len(result.items) == 500
    assert result.total_items > 0
    assert elapsed_ms < 200, f"paginated estadoSigla query took {elapsed_ms:.1f}ms"


@pytest.mark.asyncio(loop_scope="module")
async def test_city_projection_preserves_coordinate_fallback_on_real_mongo(
    perf_database,
):
    from src.infrastructure.database.mapper.territorial_aggregation_mapper import (
        TerritorialAggregationMapper,
    )
    from src.infrastructure.database.repository.mongo_territorial_aggregation_repository import (
        MongoTerritorialAggregationRepository,
    )

    polygon = {"type": "Polygon", "coordinates": [[[1, 1], [3, 1], [3, 3], [1, 1]]]}
    documents = [
        {
            "municipioIdIbge": "2927408",
            "centroide": {"type": "Point", "coordinates": [10, 20]},
            "geometria": polygon,
        },
        {"municipioIdIbge": "2927408", "geometria": polygon},
        {
            "municipioIdIbge": "2927408",
            "centroid": {},
            "geometry": polygon,
            "lon": 12,
            "lat": 5,
        },
    ]
    collection = perf_database["municipio_indicadores"]
    inserted = await collection.insert_many(documents)
    try:
        for original in documents:
            projected = await collection.find_one(
                {"_id": original["_id"]},
                MongoTerritorialAggregationRepository._city_projection(False),
            )
            assert TerritorialAggregationMapper.city_from_doc(
                projected, source="municipio_indicadores"
            ) == TerritorialAggregationMapper.city_from_doc(
                original, source="municipio_indicadores"
            )
            if "centroide" in original or "centroid" in original:
                assert "geometria" not in projected
                assert "geometry" not in projected
    finally:
        await collection.delete_many({"_id": {"$in": inserted.inserted_ids}})


@pytest.mark.asyncio(loop_scope="module")
async def test_neighborhood_projection_keeps_geometry_needed_for_name_resolution(
    perf_database,
):
    from src.infrastructure.database.repository.mongo_territorial_aggregation_repository import (
        MongoTerritorialAggregationRepository,
    )

    polygon = {"type": "Polygon", "coordinates": [[[1, 1], [3, 1], [3, 3], [1, 1]]]}
    documents = [
        {"municipioIdIbge": "9999999", "bairro": "Centro", "geometria": polygon},
        {
            "municipioIdIbge": "9999999",
            "bairro": "  ",
            "nm_bairro": "Ignored",
            "geometria": polygon,
        },
        {"municipioIdIbge": "9999999", "nm_bairro": "Nome", "geometria": polygon},
        {
            "municipioIdIbge": "9999999",
            "bairro": 123,
            "nm_bairro": "Ignored",
            "geometria": polygon,
        },
    ]
    collection = perf_database["bairro_indicadores"]
    inserted = await collection.insert_many(documents)
    repository = MongoTerritorialAggregationRepository(
        perf_database["municipio_indicadores"],
        collection,
        perf_database["setor_indicadores"],
    )
    try:
        projected = {
            doc["_id"]: doc
            async for doc in repository._iter_neighborhood_docs(
                municipio_id_ibge="9999999"
            )
        }
        for index, document in enumerate(documents):
            assert ("geometria" in projected[document["_id"]]) == (index in (1, 3))
    finally:
        await collection.delete_many({"_id": {"$in": inserted.inserted_ids}})
