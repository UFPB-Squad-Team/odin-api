"""Multi-state school repository integration tests (ODIN-B11).

Validates that filters by list of UFs, homonymous municipality
disambiguation and cursor pagination produce the correct MongoDB queries.
"""

import pytest

from src.domain.value_objects.query import QueryFilter, QueryOptions
from src.infrastructure.database.repository.mongo_school_repository import (
    MongoSchoolRepository,
)
from tests.factories import FakeCollection, build_school_document


def _school_doc_for_state(uf: str, document_id: str) -> dict:
    doc = build_school_document(document_id)
    doc["estadoSigla"] = uf
    return doc


@pytest.mark.asyncio
async def test_find_paginated_builds_estado_sigla_in_clause_for_uf_list():
    collection = FakeCollection(
        [
            _school_doc_for_state("PB", "school-pb"),
            _school_doc_for_state("PE", "school-pe"),
            _school_doc_for_state("CE", "school-ce"),
        ]
    )
    repository = MongoSchoolRepository(collection=collection)

    query = QueryOptions(
        page=1,
        page_size=500,
        filters=[QueryFilter(field="estado_sigla", operator="in", value=["PB", "PE"])],
    )

    await repository.find_paginated(query)

    assert collection.find_args is not None
    mongo_query, _ = collection.find_args
    assert mongo_query == {"estadoSigla": {"$in": ["PB", "PE"]}}
    assert collection.cursor.sort_args == [("escolaIdInep", 1), ("_id", 1)]
    assert collection.cursor.limit_value == 500


@pytest.mark.asyncio
async def test_find_paginated_disambiguates_homonymous_municipio_by_uf():
    collection = FakeCollection([])
    repository = MongoSchoolRepository(collection=collection)

    query = QueryOptions(
        page=1,
        page_size=10,
        filters=[
            QueryFilter(field="municipio_nome", operator="eq", value="Nova Olinda"),
            QueryFilter(field="estado_sigla", operator="eq", value="PB"),
        ],
    )

    await repository.find_paginated(query)

    assert collection.find_args is not None
    mongo_query, _ = collection.find_args
    assert mongo_query == {
        "$and": [
            {"municipioNome": "Nova Olinda"},
            {"estadoSigla": "PB"},
        ]
    }


@pytest.mark.asyncio
async def test_find_paginated_combines_municipio_contains_with_uf_list():
    collection = FakeCollection([])
    repository = MongoSchoolRepository(collection=collection)

    query = QueryOptions(
        page=1,
        page_size=10,
        filters=[
            QueryFilter(field="municipio_nome", operator="contains", value="Nova"),
            QueryFilter(field="estado_sigla", operator="in", value=["PB", "CE"]),
        ],
    )

    await repository.find_paginated(query)

    assert collection.find_args is not None
    mongo_query, _ = collection.find_args
    assert mongo_query == {
        "$and": [
            {"municipioNome": {"$regex": "Nova", "$options": "i"}},
            {"estadoSigla": {"$in": ["PB", "CE"]}},
        ]
    }


@pytest.mark.asyncio
async def test_find_paginated_merges_cursor_with_estado_sigla_filter():
    collection = FakeCollection([_school_doc_for_state("PB", "school-pb")])
    repository = MongoSchoolRepository(collection=collection)

    cursor = repository._encode_cursor(
        {"_id": "school-pb", "escolaIdInep": 12345678},
        "escolaIdInep",
    )
    query = QueryOptions(
        page=1,
        page_size=10,
        cursor=cursor,
        filters=[QueryFilter(field="estado_sigla", operator="eq", value="PB")],
    )

    await repository.find_paginated(query)

    assert collection.find_args is not None
    mongo_query, _ = collection.find_args
    assert "$and" in mongo_query
    assert {"estadoSigla": "PB"} in mongo_query["$and"]
    assert mongo_query["$and"][1] == {
        "$or": [
            {"escolaIdInep": {"$gt": 12345678}},
            {"escolaIdInep": 12345678, "_id": {"$gt": "school-pb"}},
        ]
    }
