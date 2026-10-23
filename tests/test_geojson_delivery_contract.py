import json
import os

import pytest
from pydantic import TypeAdapter

from src.application.school.geojson.get_paraiba_geojson import GetParaibaGeoJson
from src.infrastructure.database.repository.mongo_school_repository import (
    MongoSchoolRepository,
)
from src.presentation.http.large_json import LargeJSONService
from src.presentation.http.schemas.aggregation_schema import (
    CityAggregationFeature,
    CityAggregationFeatureCollection,
    MongoNeighborhoodAggregation,
    NeighborhoodAggregationFeature,
    NeighborhoodAggregationFeatureCollection,
)
from src.presentation.http.schemas.geojson_schema import (
    ParaibaSchoolFeature,
    ParaibaSchoolFeatureCollection,
)
from tests.factories import build_school_document


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "collection_schema,item_schema,collection,payload",
    [
        (
            CityAggregationFeatureCollection,
            CityAggregationFeature,
            True,
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "id": "2927408",
                        "geometry": {"type": "Point", "coordinates": [-38.5, -12.9]},
                        "properties": {
                            "municipioIdIbge": "2927408",
                            "co_municipio": "2927408",
                            "municipio": "Salvador",
                            "uf": "BA",
                            "total_escolas": "123",
                            "total_alunos": 5000,
                            "source": "municipio_indicadores",
                            "ignored": 10,
                        },
                    }
                ],
            },
        ),
        (
            list[MongoNeighborhoodAggregation],
            MongoNeighborhoodAggregation,
            False,
            [
                {
                    "_id": "mongo-id",
                    "municipioIdIbge": "2927408",
                    "municipio": "Salvador",
                    "bairro": "Centro",
                    "total_escolas": "2",
                    "total_matriculas": 30,
                    "tem_bairro_official": True,
                    "source": "bairros_indicadores",
                    "ignored": "omit",
                }
            ],
        ),
        (
            NeighborhoodAggregationFeatureCollection,
            NeighborhoodAggregationFeature,
            True,
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "id": "setor1",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[0, 0], [1, 0], [0, 0]]],
                        },
                        "properties": {
                            "id": "setor1",
                            "municipioIdIbge": "2927408",
                            "co_municipio": "2927408",
                            "municipio": "Salvador",
                            "bairro": "Setor 1",
                            "total_escolas": 1,
                            "total_alunos": 50,
                            "tem_bairro_oficial": False,
                            "nivel": "setor",
                            "source": "setor_indicadores",
                        },
                    }
                ],
            },
        ),
    ],
)
async def test_incremental_serialization_matches_entire_response_model(
    collection_schema, item_schema, collection, payload
):
    expected = TypeAdapter(collection_schema).dump_python(
        TypeAdapter(collection_schema).validate_python(payload),
        mode="json",
        by_alias=True,
    )

    async def items():
        for item in payload["features"] if collection else payload:
            yield item

    service = LargeJSONService()
    response = await service.response(
        "contract", items, item_schema, collection=collection
    )
    try:
        with open(response.path, encoding="utf-8") as source:
            assert json.load(source) == expected
    finally:
        response._release()
        await service.close()


@pytest.mark.asyncio
async def test_all_nine_states_use_streaming_path_and_close_cursor():
    class Cursor:
        batch = None
        closed = False

        def batch_size(self, value):
            self.batch = value
            return self

        async def __aiter__(self):
            for i, uf in enumerate(
                ["PB", "PE", "CE", "RN", "MA", "PI", "AL", "SE", "BA"]
            ):
                doc = build_school_document(str(i))
                doc.update(estadoSigla=uf, escolaIdInep=i + 1)
                yield doc

        async def close(self):
            self.closed = True

        async def to_list(self, *args, **kwargs):
            pytest.fail("Streaming delivery must not materialize the cursor")

    class Collection:
        def find(self, query, projection):
            assert "estadoSigla" not in query  # Preserve the legacy unfiltered URL.
            return cursor

    cursor = Cursor()
    use_case = GetParaibaGeoJson(MongoSchoolRepository(Collection()))
    service = LargeJSONService()
    response = await service.response(
        "schools", use_case.iter_items, ParaibaSchoolFeature
    )
    try:
        with open(response.path, encoding="utf-8") as source:
            payload = json.load(source)
        ParaibaSchoolFeatureCollection.model_validate(payload)
        assert len(payload["features"]) == 9
        assert payload["features"][-1]["properties"]["estado_sigla"] == "BA"
        assert cursor.batch == 100
        assert cursor.closed
    finally:
        response._release()
        assert not os.path.exists(response.path)
        await service.close()
