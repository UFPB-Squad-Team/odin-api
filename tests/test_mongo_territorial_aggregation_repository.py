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
        self.last_aggregate_pipeline = None

    async def find_one(self, query):
        self.last_find_one_query = query
        return self.find_one_doc

    def find(self, query):
        self.last_find_query = query
        return FakeFindCursor(self.find_docs)

    def aggregate(self, pipeline):
        self.last_aggregate_pipeline = pipeline
        return FakeAggregateCursor(self.aggregate_docs)


@pytest.mark.asyncio
async def test_get_cities_returns_primary_collection_when_available():
    municipio_collection = FakeCollection(
        find_one_doc={
            "municipioIdIbge": "2507507",
            "municipio": "Joao Pessoa",
            "sg_uf": "PB",
            "total_escolas": 100,
            "total_matriculas": 50000,
            "avg_ideb": 5.2,
            "pct_com_internet": 100,
            "centroide": {"type": "Point", "coordinates": [-34.86, -7.12]},
            "socioeconomico": {
                "anoReferencia": 2022,
                "fonte": "IBGE Censo Demografico 2022",
                "populacao": {"total": 1000},
            },
            "educacao": {
                "totalEscolas": 101,
                "totalMatriculas": 51000,
                "pctComInternet": 98.5,
            },
        }
    )
    bairro_collection = FakeCollection()
    setor_collection = FakeCollection(aggregate_docs=[])

    repository = MongoTerritorialAggregationRepository(
        municipio_collection=municipio_collection,
        bairro_collection=bairro_collection,
        setor_collection=setor_collection,
    )

    result = await repository.get_cities(co_municipio="2507507")

    assert result["type"] == "FeatureCollection"
    assert len(result["features"]) == 1
    feature = result["features"][0]
    assert feature["properties"]["source"] == "municipio_indicadores"
    assert feature["geometry"]["coordinates"] == [-34.86, -7.12]
    assert feature["properties"]["total_escolas"] == 101
    assert feature["properties"]["total_alunos"] == 51000
    assert feature["properties"]["pct_com_internet"] == 98.5
    assert feature["properties"]["socioeconomico"]["anoReferencia"] == 2022
    assert feature["properties"]["educacao"]["totalMatriculas"] == 51000
    assert setor_collection.last_aggregate_pipeline is None


@pytest.mark.asyncio
async def test_get_cities_uses_setor_fallback_when_primary_missing():
    municipio_collection = FakeCollection(find_one_doc=None)
    bairro_collection = FakeCollection()
    setor_collection = FakeCollection(
        aggregate_docs=[
            {
                "co_municipio": "2507507",
                "municipio": "Joao Pessoa",
                "uf": "PB",
                "total_escolas": 80,
                "total_alunos": 42000,
                "avg_ideb": 4.9,
                "avg_lon": -34.85,
                "avg_lat": -7.11,
            }
        ]
    )

    repository = MongoTerritorialAggregationRepository(
        municipio_collection=municipio_collection,
        bairro_collection=bairro_collection,
        setor_collection=setor_collection,
    )

    result = await repository.get_cities(co_municipio="2507507")

    assert len(result["features"]) == 1
    feature = result["features"][0]
    assert feature["properties"]["source"] == "setor_indicadores"
    assert feature["geometry"]["coordinates"] == [-34.85, -7.11]
    assert setor_collection.last_aggregate_pipeline is not None
    assert {
        "$or": [
            {"co_municipio": "2507507"},
            {"municipioIdIbge": "2507507"},
        ]
    } in setor_collection.last_aggregate_pipeline[0]["$match"]["$and"]


@pytest.mark.asyncio
async def test_get_cities_filters_list_by_sg_uf():
    municipio_collection = FakeCollection(
        find_docs=[
            {
                "co_municipio": "2507507",
                "municipio": "Joao Pessoa",
                "sg_uf": "PB",
                "total_escolas": 100,
                "total_alunos": 50000,
                "centroide": {"type": "Point", "coordinates": [-34.86, -7.12]},
            }
        ]
    )
    bairro_collection = FakeCollection()
    setor_collection = FakeCollection()

    repository = MongoTerritorialAggregationRepository(
        municipio_collection=municipio_collection,
        bairro_collection=bairro_collection,
        setor_collection=setor_collection,
    )

    result = await repository.get_cities(sg_uf="pb")

    assert len(result["features"]) == 1
    assert municipio_collection.last_find_query == {
        "$or": [
            {"sg_uf": "PB"},
            {"uf": "PB"},
            {"estado_sigla": "PB"},
        ]
    }


@pytest.mark.asyncio
async def test_get_by_municipio_returns_primary_bairro_collection():
    municipio_collection = FakeCollection()
    bairro_collection = FakeCollection(
        find_docs=[
            {
                "_id": "69e211325157cf0f20312a59",
                "municipioIdIbge": "2507507",
                "municipio": "Joao Pessoa",
                "bairro": "Alto do Mateus",
                "cd_bairro_ibge": "2507507005",
                "geometria": {
                    "type": "MultiPolygon",
                    "coordinates": [[[[ -34.88, -7.11 ], [ -34.87, -7.11 ], [ -34.87, -7.12 ], [ -34.88, -7.12 ], [ -34.88, -7.11 ]]]],
                },
                "pct_com_biblioteca": 62.5,
                "pct_com_internet": 100,
                "pct_com_lab_informatica": 62.5,
                "pct_sem_acessibilidade": 12.5,
                "sg_uf": "PB",
                "total_escolas": 2,
                "total_matriculas": 2182,
            }
        ]
    )
    setor_collection = FakeCollection()

    repository = MongoTerritorialAggregationRepository(
        municipio_collection=municipio_collection,
        bairro_collection=bairro_collection,
        setor_collection=setor_collection,
    )

    result = await repository.get_by_municipio(municipio_id_ibge="2507507")

    assert len(result) == 1
    item = result[0]
    assert item["_id"] == "69e211325157cf0f20312a59"
    assert item["bairro"] == "Alto do Mateus"
    assert item["cd_bairro_ibge"] == "2507507005"
    assert item["total_matriculas"] == 2182
    assert item["geometria"] is None
    assert item["tem_bairro_oficial"] is True
    assert item["nivel"] == "bairro"
    assert item["source"] == "bairros_indicadores"
    assert setor_collection.last_aggregate_pipeline is None
    assert {"$or": [
        {"municipioIdIbge": "2507507"},
        {"municipio_id_ibge": "2507507"},
        {"co_municipio": "2507507"},
        {"idIbge": "2507507"},
    ]} in bairro_collection.last_find_query["$and"]


@pytest.mark.asyncio
async def test_get_by_municipio_uses_setor_fallback_when_bairro_collection_missing():
    municipio_collection = FakeCollection()
    bairro_collection = FakeCollection(find_docs=[])
    setor_collection = FakeCollection(
        aggregate_docs=[
            {
                "co_municipio": "2507507",
                "municipio": "Joao Pessoa",
                "bairro": "Area Urbana Integrada",
                "cd_setor": "250750705000101",
                "tem_bairro_official": False,
                "total_escolas": 10,
                "total_alunos": 4500,
                "avg_lon": -34.83,
                "avg_lat": -7.10,
                "pct_com_biblioteca": 72.21666666666667,
                "pct_com_internet": 100,
                "pct_com_lab_informatica": 61.11666666666667,
                "pct_sem_acessibilidade": 5.55,
            }
        ]
    )

    repository = MongoTerritorialAggregationRepository(
        municipio_collection=municipio_collection,
        bairro_collection=bairro_collection,
        setor_collection=setor_collection,
    )

    result = await repository.get_by_municipio(municipio_id_ibge="2507507")

    assert len(result) == 1
    item = result[0]
    assert item["bairro"] == "Area Urbana Integrada"
    assert item["total_matriculas"] == 4500
    assert item["geometria"] is None
    assert item["pct_com_biblioteca"] == 72.22
    assert item["pct_com_lab_informatica"] == 61.12
    assert item["pct_sem_acessibilidade"] == 5.55
    assert item["nivel"] == "setor"
    assert item["cd_setor"] == "250750705000101"
    assert item["source"] == "setor_indicadores"
    first_match = setor_collection.last_aggregate_pipeline[0]["$match"]["$or"]
    assert {"co_municipio": {"$in": ["2507507", 2507507]}} in first_match


@pytest.mark.asyncio
async def test_get_by_municipio_uses_regex_filter_in_setor_fallback():
    municipio_collection = FakeCollection()
    bairro_collection = FakeCollection(find_docs=[])
    setor_collection = FakeCollection(
        aggregate_docs=[
            {
                "co_municipio": "2507507",
                "municipio": "Joao Pessoa",
                "bairro": "Alto do Mateus",
                "tem_bairro_official": True,
                "total_escolas": 1,
                "total_alunos": 100,
                "avg_lon": -34.83,
                "avg_lat": -7.10,
            }
        ]
    )

    repository = MongoTerritorialAggregationRepository(
        municipio_collection=municipio_collection,
        bairro_collection=bairro_collection,
        setor_collection=setor_collection,
    )

    await repository.get_by_municipio(municipio_id_ibge="2507507", bairro="mate")

    regex_stages = [
        stage
        for stage in setor_collection.last_aggregate_pipeline
        if "$match" in stage and "bairro_resolvido" in stage["$match"]
    ]
    assert regex_stages
    assert regex_stages[0]["$match"]["bairro_resolvido"]["$regex"] == "mate"
    assert regex_stages[0]["$match"]["bairro_resolvido"]["$options"] == "i"


@pytest.mark.asyncio
async def test_setor_pipeline_does_not_drop_bairro_with_same_name_as_municipio():
    municipio_collection = FakeCollection()
    bairro_collection = FakeCollection(find_docs=[])
    setor_collection = FakeCollection(
        aggregate_docs=[
            {
                "co_municipio": "2500106",
                "municipio": "Agua Branca",
                "bairro": "Agua Branca",
                "tem_bairro_official": False,
                "total_escolas": 2,
                "total_alunos": 654,
                "pct_com_biblioteca": 50,
                "pct_com_internet": 100,
                "pct_com_lab_informatica": 50,
                "pct_sem_acessibilidade": 0,
            }
        ]
    )

    repository = MongoTerritorialAggregationRepository(
        municipio_collection=municipio_collection,
        bairro_collection=bairro_collection,
        setor_collection=setor_collection,
    )

    result = await repository.get_by_municipio(municipio_id_ibge="2500106")

    assert len(result) == 1
    assert result[0]["municipioIdIbge"] == "2500106"
    assert result[0]["source"] == "setor_indicadores"


@pytest.mark.asyncio
async def test_get_by_municipio_can_include_geometria_when_requested():
    municipio_collection = FakeCollection()
    bairro_collection = FakeCollection(
        find_docs=[
            {
                "_id": "69e211325157cf0f20312a59",
                "municipioIdIbge": "2507507",
                "municipio": "Joao Pessoa",
                "bairro": "Alto do Mateus",
                "cd_bairro_ibge": "2507507005",
                "geometria": {
                    "type": "MultiPolygon",
                    "coordinates": [[[[ -34.88, -7.11 ], [ -34.87, -7.11 ], [ -34.87, -7.12 ], [ -34.88, -7.12 ], [ -34.88, -7.11 ]]]],
                },
                "total_escolas": 2,
                "total_matriculas": 2182,
            }
        ]
    )
    setor_collection = FakeCollection()

    repository = MongoTerritorialAggregationRepository(
        municipio_collection=municipio_collection,
        bairro_collection=bairro_collection,
        setor_collection=setor_collection,
    )

    result = await repository.get_by_municipio(
        municipio_id_ibge="2507507",
        include_geometria=True,
    )

    assert result[0]["geometria"]["type"] == "MultiPolygon"
