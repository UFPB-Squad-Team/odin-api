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


class GeoAwareFakeCollection(FakeCollection):
    def __init__(self, find_one_responses=None, **kwargs):
        super().__init__(**kwargs)
        self.find_one_responses = list(find_one_responses or [])
        self.find_one_queries = []

    async def find_one(self, query, projection=None):
        self.last_find_one_query = query
        self.find_one_queries.append(query)

        if not self.find_one_responses:
            return None

        if len(self.find_one_responses) == 1:
            return self.find_one_responses[0]

        if "$geoIntersects" in str(query):
            return self.find_one_responses[-1]

        return self.find_one_responses[0]


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
async def test_get_cities_filters_by_multiple_ufs():
    municipio_collection = FakeCollection(find_docs=[])
    repository = MongoTerritorialAggregationRepository(
        municipio_collection=municipio_collection,
        bairro_collection=FakeCollection(),
        setor_collection=FakeCollection(),
    )

    await repository.get_cities(sg_uf=["pb", " PE ", "pb"])

    assert municipio_collection.last_find_query == {
        "$or": [
            {"sg_uf": {"$in": ["PB", "PE"]}},
            {"uf": {"$in": ["PB", "PE"]}},
            {"estado_sigla": {"$in": ["PB", "PE"]}},
        ]
    }


@pytest.mark.asyncio
async def test_get_by_municipio_filters_primary_and_fallback_by_multiple_ufs():
    bairro_collection = FakeCollection(find_docs=[])
    setor_collection = FakeCollection()
    repository = MongoTerritorialAggregationRepository(
        municipio_collection=FakeCollection(),
        bairro_collection=bairro_collection,
        setor_collection=setor_collection,
    )

    await repository.get_by_municipio(
        municipio_id_ibge="2507507",
        sg_uf=["pb", "pe"],
    )

    uf_clause = {
        "$or": [
            {"sg_uf": {"$in": ["PB", "PE"]}},
            {"uf": {"$in": ["PB", "PE"]}},
            {"estado_sigla": {"$in": ["PB", "PE"]}},
        ]
    }
    assert uf_clause in bairro_collection.last_find_query["$and"]
    assert uf_clause in setor_collection.last_aggregate_pipeline[0]["$match"]["$and"]


@pytest.mark.asyncio
async def test_get_by_municipio_returns_primary_bairro_collection():
    municipio_collection = FakeCollection()
    bairro_collection = FakeCollection(
        find_docs=[
            {
                "_id": "69e211325157cf0f20312a59",
                "cd_municipio": "2507507",
                "municipio": "Joao Pessoa",
                "nm_bairro": "Alto do Mateus",
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
                "socioeconomico": {
                    "anoReferencia": 2022,
                    "fonte": "IBGE",
                    "populacao": {"total": 10000},
                },
                "educacao": {
                    "totalEscolas": 2,
                    "totalMatriculas": 2182,
                    "pctComInternet": 100,
                },
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
    assert item["municipioIdIbge"] == "2507507"
    assert item["socioeconomico"]["anoReferencia"] == 2022
    assert item["educacao"]["totalMatriculas"] == 2182
    assert item["source"] == "bairros_indicadores"
    assert setor_collection.last_aggregate_pipeline is None
    assert {"$or": [
        {"municipioIdIbge": "2507507"},
        {"municipio_id_ibge": "2507507"},
        {"cd_municipio": "2507507"},
        {"co_municipio": "2507507"},
        {"idIbge": "2507507"},
    ]} in bairro_collection.last_find_query["$and"]


@pytest.mark.asyncio
async def test_get_by_municipio_matches_cd_municipio_in_primary_collection():
    municipio_collection = FakeCollection()
    bairro_collection = FakeCollection(
        find_docs=[
            {
                "_id": "69ee979682c705ca26d13187",
                "cd_bairro": "2507507039",
                "cd_municipio": "2507507",
                "nm_municipio": "João Pessoa",
                "nm_bairro": "Mangabeira",
                "uf": "PB",
                "socioeconomico": {
                    "anoReferencia": 2022,
                    "fonte": "IBGE Censo Demográfico 2022",
                },
                "educacao": {
                    "totalEscolas": 1,
                    "totalMatriculas": 314,
                },
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
    assert item["bairro"] == "Mangabeira"
    assert item["municipioIdIbge"] == "2507507"
    assert item["source"] == "bairros_indicadores"
    assert item["nivel"] == "bairro"
    assert setor_collection.last_aggregate_pipeline is None
    assert bairro_collection.last_find_query is not None
    assert {"cd_municipio": "2507507"} in bairro_collection.last_find_query["$and"][0]["$or"]


@pytest.mark.asyncio
async def test_get_by_municipio_enriches_blank_bairro_from_bairro_code():
    municipio_collection = FakeCollection()
    bairro_collection = GeoAwareFakeCollection(
        find_docs=[
            {
                "_id": "69ee979682c705ca26d1316b",
                "cd_bairro_ibge": "2507507011",
                "cd_municipio": "2507507",
                "municipio": "João Pessoa",
                "bairro": "",
                "nm_bairro": "",
                "geometria": None,
                "sg_uf": "PB",
                "total_escolas": 0,
                "total_matriculas": 0,
                "tem_bairro_official": True,
                "socioeconomico": {"anoReferencia": 2022, "fonte": "IBGE Censo Demográfico 2022"},
                "educacao": None,
            }
        ],
        find_one_responses=[
            {
                "bairro": "Área 51",
                "nm_bairro": "Área 51",
            }
        ],
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
    assert item["bairro"] == "Área 51"
    assert item["source"] == "bairros_indicadores"
    assert bairro_collection.find_one_queries
    assert "cd_bairro_ibge" in str(bairro_collection.find_one_queries[0])


@pytest.mark.asyncio
async def test_get_by_municipio_uses_geo_fallback_when_code_lookup_fails_and_geometry_exists():
    municipio_collection = FakeCollection()
    bairro_collection = GeoAwareFakeCollection(
        find_docs=[
            {
                "_id": "69ee979682c705ca26d1316c",
                "cd_bairro_ibge": "2507507012",
                "cd_municipio": "2507507",
                "municipio": "João Pessoa",
                "bairro": "",
                "nm_bairro": "",
                "geometria": {
                    "type": "MultiPolygon",
                    "coordinates": [[[[ -34.86, -7.12 ], [ -34.85, -7.12 ], [ -34.85, -7.13 ], [ -34.86, -7.13 ], [ -34.86, -7.12 ]]]],
                },
                "sg_uf": "PB",
                "total_escolas": 0,
                "total_matriculas": 0,
                "tem_bairro_official": True,
                "socioeconomico": {"anoReferencia": 2022, "fonte": "IBGE Censo Demográfico 2022"},
                "educacao": None,
            }
        ],
        find_one_responses=[
            None,
            {
                "bairro": "Mangabeira",
                "nm_bairro": "Mangabeira",
            },
        ],
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
    assert item["bairro"] == "Mangabeira"
    assert item["source"] == "bairros_indicadores"
    assert any("$geoIntersects" in str(query) for query in bairro_collection.find_one_queries)


@pytest.mark.asyncio
async def test_get_by_municipio_uses_readable_label_when_official_bairro_has_no_name():
    municipio_collection = FakeCollection()
    bairro_collection = GeoAwareFakeCollection(
        find_docs=[
            {
                "_id": "69ee979682c705ca26d1316d",
                "cd_bairro_ibge": "2507507011",
                "cd_municipio": "2507507",
                "municipio": "João Pessoa",
                "bairro": "",
                "nm_bairro": "",
                "geometria": None,
                "sg_uf": "PB",
                "total_escolas": 0,
                "total_matriculas": 0,
                "tem_bairro_official": True,
                "socioeconomico": {"anoReferencia": 2022, "fonte": "IBGE Censo Demográfico 2022"},
                "educacao": None,
            }
        ],
        find_one_responses=[],
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
    assert item["bairro"] == "Bairro 2507507011"
    assert item["source"] == "bairros_indicadores"
    assert item["nivel"] == "bairro"


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
                "socioeconomico": {
                    "anoReferencia": 2022,
                    "fonte": "IBGE",
                    "populacao": {"total": 5000},
                },
                "educacao": {
                    "totalEscolas": 10,
                    "totalMatriculas": 4500,
                    "pctComInternet": 100,
                },
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
    assert item["socioeconomico"]["anoReferencia"] == 2022
    assert item["educacao"]["totalMatriculas"] == 4500
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
