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
    }


@pytest.fixture(scope="module")
async def perf_database():
    client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=10_000)
    db = client[DATABASE_NAME]
    schools = db["escolas"]
    await schools.drop()

    chunk: list[dict] = []
    per_uf = TARGET_SCHOOLS // len(UFS)
    for uf_index, uf in enumerate(UFS):
        for i in range(per_uf):
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


@pytest.mark.asyncio
async def test_estado_sigla_query_uses_index_and_is_fast(perf_database):
    schools = perf_database["escolas"]

    explain = await schools.find({"estadoSigla": "PB"}).explain("executionStats")
    _assert_uses_index(explain)
    execution_ms = explain["executionStats"]["executionTimeMillis"]
    assert execution_ms < 100, f"executionTimeMillis={execution_ms} >= 100ms"


@pytest.mark.asyncio
async def test_multi_uf_in_query_uses_index_and_is_fast(perf_database):
    schools = perf_database["escolas"]

    explain = await schools.find({"estadoSigla": {"$in": ["PB", "PE"]}}).explain(
        "executionStats"
    )
    _assert_uses_index(explain)
    execution_ms = explain["executionStats"]["executionTimeMillis"]
    assert execution_ms < 100, f"executionTimeMillis={execution_ms} >= 100ms"


@pytest.mark.asyncio
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
