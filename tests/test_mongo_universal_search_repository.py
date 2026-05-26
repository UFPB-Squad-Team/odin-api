import pytest

from src.infrastructure.database.repository.mongo_universal_search_repository import (
    MongoUniversalSearchRepository,
)


class FakeCursor:
    def __init__(self, docs):
        self.docs = list(docs)
        self.last_collation = None
        self.last_sort = None
        self.last_limit = None

    def collation(self, value):
        self.last_collation = value
        return self

    def sort(self, value):
        self.last_sort = value
        return self

    def limit(self, value):
        self.last_limit = value
        return self

    async def to_list(self, length=None):
        if length is None:
            return list(self.docs)
        return list(self.docs)[:length]


class FakeCollection:
    def __init__(self, find_responses=None, aggregate_responses=None):
        self.find_responses = [list(items) for items in (find_responses or [[]])]
        self.aggregate_responses = [list(items) for items in (aggregate_responses or [[]])]
        self.find_calls = []
        self.aggregate_calls = []
        self.last_find_query = None
        self.last_find_projection = None
        self.last_aggregate_pipeline = None

    def find(self, query, projection=None):
        self.find_calls.append((query, projection))
        self.last_find_query = query
        self.last_find_projection = projection
        docs = self.find_responses.pop(0) if self.find_responses else []
        return FakeCursor(docs)

    def aggregate(self, pipeline):
        self.aggregate_calls.append(pipeline)
        self.last_aggregate_pipeline = pipeline
        docs = self.aggregate_responses.pop(0) if self.aggregate_responses else []
        return FakeCursor(docs)


@pytest.mark.asyncio
async def test_search_schools_uses_prefix_query_and_falls_back_to_contains():
    escolas = FakeCollection(
        find_responses=[
            [],
            [
                {
                    "escolaIdInep": "1",
                    "escolaNome": "Escola Epitacio",
                    "municipioNome": "Joao Pessoa",
                    "municipioIdIbge": "2507507",
                    "endereco": {"bairro": "Centro"},
                    "localizacao": {"coordinates": [-34.86, -7.12]},
                }
            ],
        ]
    )
    repository = MongoUniversalSearchRepository(escolas, FakeCollection(), FakeCollection())

    docs = await repository.search_schools("Epitacio", sg_uf="pb", municipio_id="2507507", limit=4)

    assert len(docs) == 1
    regex_pattern = escolas.find_calls[0][0]["$and"][0]["$and"][0]["escolaNome"]["$regex"]
    assert regex_pattern.startswith("^")
    assert "[eEéÉèÈêÊëË]" in regex_pattern
    assert escolas.find_calls[0][0]["$and"][0]["$and"][1]["$or"][0]["sg_uf"] == "PB"
    assert len(escolas.find_calls) == 2
    assert escolas.last_find_projection["escolaNome"] == 1


@pytest.mark.asyncio
async def test_search_schools_builds_accent_insensitive_regex():
    escolas = FakeCollection(
        find_responses=[
            [
                {
                    "escolaIdInep": "1",
                    "escolaNome": "Escola João",
                    "municipioNome": "Joao Pessoa",
                    "municipioIdIbge": "2507507",
                    "endereco": {"bairro": "Centro"},
                    "localizacao": {"coordinates": [-34.86, -7.12]},
                }
            ]
        ]
    )
    repository = MongoUniversalSearchRepository(escolas, FakeCollection(), FakeCollection())

    docs = await repository.search_schools("João", limit=2)

    assert len(docs) == 1
    regex_pattern = escolas.find_calls[0][0]["escolaNome"]["$regex"]
    assert regex_pattern.startswith("^")
    assert "[oOóÓòÒôÔõÕöÖ]" in regex_pattern


@pytest.mark.asyncio
async def test_search_logradouros_builds_group_pipeline():
    escolas = FakeCollection(
        aggregate_responses=[
            [
                {
                    "logradouro": "Avenida Epitacio Pessoa",
                    "municipioNome": "Joao Pessoa",
                    "municipioIdIbge": "2507507",
                    "bairros": ["Tambau"],
                    "count": 4,
                    "avg_lon": -34.84,
                    "avg_lat": -7.10,
                }
            ]
        ]
    )
    repository = MongoUniversalSearchRepository(escolas, FakeCollection(), FakeCollection())

    docs = await repository.search_logradouros("Epitacio", municipio_id="2507507", limit=3)

    assert len(docs) == 1
    match_stage = escolas.last_aggregate_pipeline[0]["$match"]
    assert match_stage["$and"][0]["endereco.logradouro"]["$regex"].startswith("^")
    assert "[eEéÉèÈêÊëË]" in match_stage["$and"][0]["endereco.logradouro"]["$regex"]
    assert escolas.last_aggregate_pipeline[-1]["$limit"] == 3
