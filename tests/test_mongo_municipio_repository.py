import pytest

from src.infrastructure.database.repository.mongo_territorial_aggregation_repository import (
    MongoTerritorialAggregationRepository,
)
from src.infrastructure.database.repository.mongo_municipio_repository import (
    MongoMunicipioRepository,
)


def _matches(document: dict, query: dict | None) -> bool:
    if not query:
        return True

    if "$or" in query:
        return any(_matches(document, item) for item in query["$or"])

    if "$and" in query:
        return all(_matches(document, item) for item in query["$and"])

    for key, value in query.items():
        if document.get(key) != value:
            return False

    return True


class Cursor:
    def __init__(self, documents):
        self.documents = list(documents)

    async def to_list(self, length):
        if length is None:
            return list(self.documents)
        return self.documents[:length]


class Collection:
    def __init__(self, documents):
        self.documents = list(documents)
        self.last_find_query = None
        self.last_aggregate_pipeline = None

    def find(self, query=None, projection=None):
        self.last_find_query = query or {}
        matched = [doc for doc in self.documents if _matches(doc, query)]
        return Cursor(matched)

    async def find_one(self, query):
        for document in self.documents:
            if _matches(document, query):
                return document
        return None

    async def count_documents(self, query):
        return sum(1 for document in self.documents if _matches(document, query))

    def aggregate(self, pipeline, **kwargs):
        self.last_aggregate_pipeline = pipeline

        if pipeline and "$match" in pipeline[0]:
            matched = [doc for doc in self.documents if _matches(doc, pipeline[0]["$match"])]
        else:
            matched = list(self.documents)

        return Cursor(matched)


@pytest.mark.asyncio
async def test_list_municipios_filters_and_sorts_by_name():
    municipio_collection = Collection(
        [
            {
                "co_municipio": "2507507",
                "municipio": "João Pessoa",
                "sg_uf": "PB",
            },
            {
                "municipioIdIbge": "2504009",
                "municipioNome": "Campina Grande",
                "estadoSigla": "PB",
            },
        ]
    )
    bairro_collection = Collection([])
    setor_collection = Collection([])

    repository = MongoMunicipioRepository(
        municipio_collection=municipio_collection,
        bairro_collection=bairro_collection,
        setor_collection=setor_collection,
    )

    items = await repository.list_municipios(sg_uf="pb")

    assert [item.nome for item in items] == ["Campina Grande", "João Pessoa"]
    assert [item.sg_uf for item in items] == ["PB", "PB"]


@pytest.mark.asyncio
async def test_get_resumo_uses_primary_document_and_counts_bairros():
    municipio_collection = Collection(
        [
            {
                "co_municipio": "2507507",
                "municipio": "João Pessoa",
                "sg_uf": "PB",
                "total_escolas": 412,
                "total_matriculas": 98000,
                "pct_com_biblioteca": 62.3,
                "pct_com_internet": 88.1,
                "pct_com_lab_informatica": 45.2,
                "pct_sem_acessibilidade": 31.0,
                "educacao": {
                    "totalBairros": 64,
                    "mediaIdebAnosIniciais": 5.12,
                },
            }
        ]
    )
    bairro_collection = Collection(
        [
            {"municipio": "João Pessoa"},
            {"municipio": "João Pessoa"},
        ]
    )
    setor_collection = Collection([])

    repository = MongoMunicipioRepository(
        municipio_collection=municipio_collection,
        bairro_collection=bairro_collection,
        setor_collection=setor_collection,
    )

    resumo = await repository.get_resumo("2507507")

    assert resumo is not None
    assert resumo.source == "municipio_indicadores"
    assert resumo.total_escolas == 412
    assert resumo.total_matriculas == 98000
    assert resumo.total_bairros == 64
    assert resumo.tem_bairros_oficiais is True
    assert resumo.mediaIdebAnosIniciais == 5.12


@pytest.mark.asyncio
async def test_get_resumo_falls_back_to_setor_when_primary_missing():
    municipio_collection = Collection([])
    bairro_collection = Collection([])
    setor_collection = Collection(
        [
            {
                "co_municipio": "2507507",
                "municipio": "João Pessoa",
                "uf": "PB",
                "total_escolas": 80,
                "total_alunos": 42000,
                "educacao": {
                    "mediaIdebAnosIniciais": 4.9,
                },
            }
        ]
    )

    repository = MongoMunicipioRepository(
        municipio_collection=municipio_collection,
        bairro_collection=bairro_collection,
        setor_collection=setor_collection,
    )

    resumo = await repository.get_resumo("2507507")

    assert resumo is not None
    assert resumo.source == "setor_indicadores"
    assert resumo.total_escolas == 80
    assert resumo.total_matriculas == 42000
    assert resumo.total_bairros == 0
    assert resumo.tem_bairros_oficiais is False
    assert resumo.mediaIdebAnosIniciais == 4.9
