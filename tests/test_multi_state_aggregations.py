"""Multi-state aggregation integration tests (ODIN-B11).

Validates that city/neighborhood aggregations apply the UF filter clause
($or across sg_uf / uf / estado_sigla) when a list of states is provided.
"""

import pytest

from src.infrastructure.database.repository.mongo_territorial_aggregation_repository import (
    MongoTerritorialAggregationRepository,
)


class FakeAggregateCursor:
    def __init__(self, docs):
        self.docs = list(docs)

    async def to_list(self, length=None):
        if length is None:
            return list(self.docs)
        return self.docs[:length]


class FakeFindCursor:
    def __init__(self, docs):
        self.docs = list(docs)

    async def to_list(self, length=None):
        if length is None:
            return list(self.docs)
        return self.docs[:length]


class FakeCollection:
    def __init__(self, find_one_doc=None, find_docs=None, aggregate_docs=None):
        self.find_one_doc = find_one_doc
        self.find_docs = list(find_docs or [])
        self.aggregate_docs = list(aggregate_docs or [])
        self.last_find_one_query = None
        self.last_find_query = None
        self.last_find_projection = None
        self.last_aggregate_pipeline = None

    async def find_one(self, query, projection=None):
        self.last_find_one_query = query
        return self.find_one_doc

    def find(self, query, projection=None):
        self.last_find_query = query
        self.last_find_projection = projection
        return FakeFindCursor(self.find_docs)

    def aggregate(self, pipeline):
        self.last_aggregate_pipeline = pipeline
        return FakeAggregateCursor(self.aggregate_docs)


def _uf_clause(value):
    return {
        "$or": [
            {"sg_uf": value},
            {"uf": value},
            {"estado_sigla": value},
        ]
    }


def _build_repository(municipio_docs=None, bairro_docs=None, setor_docs=None):
    return MongoTerritorialAggregationRepository(
        municipio_collection=FakeCollection(
            find_one_doc=None,
            find_docs=municipio_docs or [],
            aggregate_docs=setor_docs or [],
        ),
        bairro_collection=FakeCollection(
            find_one_doc=None,
            find_docs=bairro_docs or [],
            aggregate_docs=setor_docs or [],
        ),
        setor_collection=FakeCollection(
            find_one_doc=None,
            find_docs=[],
            aggregate_docs=setor_docs or [],
        ),
    )


@pytest.mark.asyncio
async def test_get_cities_filters_by_multiple_ufs():
    municipio_collection = FakeCollection(
        find_one_doc=None,
        find_docs=[
            {
                "_id": "municipio-pb",
                "co_municipio": "2509000",
                "municipio": "Nova Olinda",
                "nm_municipio": "Nova Olinda",
                "sg_uf": "PB",
                "total_escolas": 10,
                "total_alunos": 100,
            },
            {
                "_id": "municipio-pe",
                "co_municipio": "2609000",
                "municipio": "Nova Olinda",
                "nm_municipio": "Nova Olinda",
                "sg_uf": "PE",
                "total_escolas": 20,
                "total_alunos": 200,
            },
        ],
    )
    repository = MongoTerritorialAggregationRepository(
        municipio_collection=municipio_collection,
        bairro_collection=FakeCollection(),
        setor_collection=FakeCollection(),
    )

    result = await repository.get_cities(sg_uf=["PB", "PE"])

    assert municipio_collection.last_find_query == _uf_clause({"$in": ["PB", "PE"]})
    assert len(result["features"]) == 2


@pytest.mark.asyncio
async def test_get_cities_normalizes_single_uf_lowercase():
    municipio_collection = FakeCollection(find_one_doc=None, find_docs=[])
    repository = MongoTerritorialAggregationRepository(
        municipio_collection=municipio_collection,
        bairro_collection=FakeCollection(),
        setor_collection=FakeCollection(),
    )

    await repository.get_cities(sg_uf="pb")

    assert municipio_collection.last_find_query == _uf_clause("PB")


@pytest.mark.asyncio
async def test_get_cities_disambiguates_homonymous_municipio_by_uf():
    setor_collection = FakeCollection(aggregate_docs=[])
    repository = MongoTerritorialAggregationRepository(
        municipio_collection=FakeCollection(find_one_doc=None, find_docs=[]),
        bairro_collection=FakeCollection(),
        setor_collection=setor_collection,
    )

    await repository.get_cities(co_municipio="2509000", sg_uf=["PB"])

    assert repository.municipio_collection.last_find_one_query == {
        "$and": [
            {
                "$or": [
                    {"co_municipio": "2509000"},
                    {"municipioIdIbge": "2509000"},
                    {"municipio_id_ibge": "2509000"},
                    {"idIbge": "2509000"},
                ]
            },
            _uf_clause({"$in": ["PB"]}),
        ]
    }
    assert setor_collection.last_aggregate_pipeline is not None


@pytest.mark.asyncio
async def test_get_by_municipio_applies_uf_clause_for_multiple_ufs():
    bairro_collection = FakeCollection(
        find_one_doc=None,
        find_docs=[
            {
                "_id": "bairro-1",
                "municipioIdIbge": "2507507",
                "bairro": "Centro",
                "sg_uf": "PB",
                "total_escolas": 3,
            }
        ],
    )
    repository = MongoTerritorialAggregationRepository(
        municipio_collection=FakeCollection(),
        bairro_collection=bairro_collection,
        setor_collection=FakeCollection(),
    )

    result = await repository.get_by_municipio(
        municipio_id_ibge="2507507",
        sg_uf=["PB", "CE"],
    )

    assert bairro_collection.last_find_query["$and"][-1] == _uf_clause(
        {"$in": ["PB", "CE"]}
    )
    assert len(result) == 1
