import pytest
from bson import ObjectId

from src.infrastructure.database.config.app_config import config
from src.infrastructure.database.repository.mongo_school_repository import (
    MongoSchoolRepository,
)
from src.domain.value_objects.query import QueryFilter, QueryOptions

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
    if config.use_estimated_total_for_unfiltered_lists:
        assert collection.estimated_count_called is True
        assert collection.count_query is None
    else:
        assert collection.count_query == {}
        assert collection.estimated_count_called is False
    assert result.total_items == 1
    assert result.page == 2
    assert result.page_size == 5
    assert len(result.items) == 1
    assert result.items[0].escola_nome == "Escola A"


@pytest.mark.asyncio
async def test_repository_uses_count_documents_when_filters_exist():
    collection = FakeCollection([build_school_document("school-1")])
    repository = MongoSchoolRepository(collection=collection)

    query = QueryOptions(
        page=1,
        page_size=10,
        filters=[QueryFilter(field="bairro", operator="eq", value="Centro")],
    )

    result = await repository.find_paginated(query)

    assert collection.estimated_count_called is False
    assert collection.count_query is not None
    assert result.total_items == 1


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


@pytest.mark.asyncio
async def test_get_bairros_geojson_builds_expected_match_and_feature_collection():
    aggregate_docs = [
        {
            "_id": "Centro",
            "municipio_nome": "Joao Pessoa",
            "qtd_escolas": 2,
            "avg_ideb": 5.4,
            "avg_lon": -34.86,
            "avg_lat": -7.12,
        }
    ]
    collection = FakeCollection([])
    collection.aggregate_documents = aggregate_docs
    repository = MongoSchoolRepository(collection=collection)

    result = await repository.get_bairros_geojson("João Pessoa")

    assert collection.aggregate_pipeline is not None
    match_stage = collection.aggregate_pipeline[0]["$match"]
    assert match_stage["estadoSigla"] == "PB"
    assert "Joao Pessoa" in match_stage["municipioNome"]["$in"]
    assert "João Pessoa" in match_stage["municipioNome"]["$in"]

    assert result["type"] == "FeatureCollection"
    assert len(result["features"]) == 1
    feature = result["features"][0]
    assert feature["id"] == "Centro"
    assert feature["geometry"] == {
        "type": "Point",
        "coordinates": [-34.86, -7.12],
    }
    assert feature["properties"]["municipio_nome"] == "Joao Pessoa"
    assert feature["properties"]["qtd_escolas"] == 2
    assert feature["properties"]["avg_ideb"] == 5.4


@pytest.mark.asyncio
async def test_get_bairros_geojson_ignores_docs_without_coordinates():
    aggregate_docs = [
        {
            "_id": "Centro",
            "municipio_nome": "Joao Pessoa",
            "qtd_escolas": 1,
            "avg_ideb": 4.8,
            "avg_lon": None,
            "avg_lat": -7.12,
        }
    ]
    collection = FakeCollection([])
    collection.aggregate_documents = aggregate_docs
    repository = MongoSchoolRepository(collection=collection)

    result = await repository.get_bairros_geojson("Joao Pessoa")

    assert result == {"type": "FeatureCollection", "features": []}


@pytest.mark.asyncio
async def test_get_paraiba_geojson_uses_escola_id_inep_as_feature_id():
    collection = FakeCollection([])
    collection.aggregate_documents = [
        {
            "_id": "mongo-id-1",
            "escolaNome": "Escola A",
            "escolaIdInep": 25033158,
            "municipioNome": "Agua Branca",
            "municipioIdIbge": "2500106",
            "bairro": "Centro",
            "dependenciaAdm": "Municipal",
            "tipoLocalizacao": "Urbana",
            "ideb": 4.2,
            "geometry": {"type": "Point", "coordinates": [-34.86, -7.12]},
        }
    ]
    repository = MongoSchoolRepository(collection=collection)

    result = await repository.get_paraiba_geojson()

    assert collection.aggregate_pipeline is not None
    match_stage = collection.aggregate_pipeline[0]["$match"]
    assert match_stage["estadoSigla"] == "PB"
    assert "$or" not in match_stage

    feature = result["features"][0]
    assert feature["id"] == "25033158"
    assert feature["properties"]["id"] == "25033158"
    assert feature["properties"]["escola_id_inep"] == 25033158
    assert feature["properties"]["municipioIdIbge"] == "2500106"


@pytest.mark.asyncio
async def test_get_paraiba_geojson_adds_municipio_id_filter_when_informed():
    collection = FakeCollection([])
    collection.aggregate_documents = []
    repository = MongoSchoolRepository(collection=collection)

    await repository.get_paraiba_geojson(municipio_id="2507507")

    assert collection.aggregate_pipeline is not None
    match_stage = collection.aggregate_pipeline[0]["$match"]
    assert "$or" in match_stage
    assert {"municipioIdIbge": {"$in": ["2507507", 2507507]}} in match_stage["$or"]