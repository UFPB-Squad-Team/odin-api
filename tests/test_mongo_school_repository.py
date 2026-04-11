import pytest
from bson import ObjectId

from src.infrastructure.database.repository.mongo_school_repository import (
    MongoSchoolRepository,
)

from tests.factories import FakeCollection, build_school_document


@pytest.mark.asyncio
async def test_repository_lists_paginated_schools_with_stable_sort():
    collection = FakeCollection([build_school_document("school-1")])
    repository = MongoSchoolRepository(collection=collection)

    result = await repository.list_all(page=2, page_size=5)

    assert collection.find_args == ({}, None)
    assert collection.cursor.sort_args == [("escolaIdInep", 1), ("_id", 1)]
    assert collection.cursor.skip_value == 5
    assert collection.cursor.limit_value == 5
    assert collection.count_query == {}
    assert collection.estimated_count_called is False
    assert result.total_items == 1
    assert result.page == 2
    assert result.page_size == 5
    assert len(result.items) == 1
    assert result.items[0].escola_nome == "Escola A"


@pytest.mark.asyncio
async def test_repository_get_by_id_uses_object_id_when_possible():
    object_id = ObjectId("68c8d9747e1b2e5af20f3cd6")
    collection = FakeCollection([build_school_document(object_id)])
    repository = MongoSchoolRepository(collection=collection)

    result = await repository.get_by_id("68c8d9747e1b2e5af20f3cd6")

    assert result is not None
    assert result.id == "68c8d9747e1b2e5af20f3cd6"
    assert collection.find_one_queries[0] == {"_id": object_id}


@pytest.mark.asyncio
async def test_repository_get_by_id_falls_back_to_string_id():
    collection = FakeCollection([build_school_document("school-str-id")])
    repository = MongoSchoolRepository(collection=collection)

    result = await repository.get_by_id("school-str-id")

    assert result is not None
    assert result.id == "school-str-id"
    assert collection.find_one_queries[-1] == {"_id": "school-str-id"}