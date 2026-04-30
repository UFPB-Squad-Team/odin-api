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
        self.last_find_one_query = None
        self.last_find_one_projection = None
        self.last_aggregate_pipeline = None

    def find(self, query=None, projection=None):
        self.last_find_query = query or {}
        matched = [doc for doc in self.documents if _matches(doc, query)]
        return Cursor(matched)

    async def find_one(self, query, projection=None):
        self.last_find_one_query = query
        self.last_find_one_projection = projection
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
                "total_bairros": 64,
                "educacao": {
                    "totalEscolas": 412,
                    "totalMatriculas": 98000,
                    "pctComBiblioteca": 62.3,
                    "pctComInternet": 88.1,
                    "pctComLabInformatica": 45.2,
                    "pctSemAcessibilidade": 31.0,
                    "mediaIdebAnosIniciais": 5.12,
                    "mediaIdebAnosFinals": 4.87,
                },
                "socioeconomico": {
                    "anoReferencia": 2022,
                    "fonte": "IBGE Censo Demográfico 2022",
                    "populacao": {
                        "total": 833932,
                        "totalDomiciliosParticulares": 318000,
                        "mediaMoradoresPorDomicilio": 2.62,
                    },
                    "estruturaEtaria": {
                        "pctCriancas0a9": 12.4,
                        "pctIdosos60Mais": 15.1,
                        "razaoDependencia": 63.0,
                    },
                    "raca": {
                        "pctPretaParda": 66.2,
                    },
                    "saneamento": {
                        "pctAguaRedeGeral": 91.8,
                        "pctAguaInadequada": 8.2,
                        "pctEsgotoRedeGeral": 74.6,
                        "pctEsgotoInadequado": 25.4,
                        "pctLixoColetado": 98.1,
                        "pctLixoInadequado": 1.9,
                    },
                    "educacaoPopulacao": {
                        "taxaAnalfabetismo15Mais": 8.1,
                    },
                    "familia": {
                        "pctResponsavelFeminino": 41.7,
                    },
                    "mortalidade": {
                        "totalObitosDomicilios": 136,
                        "obitosInfantis0a4": 9,
                    },
                    "habitacao": {
                        "pctDomImprovisado": 1.2,
                        "pctDomSuperlotado": 3.4,
                    },
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
    assert resumo.mediaIdebAnosFinals == 4.87
    assert resumo.educacao.totalEscolas == 412
    assert resumo.educacao.pctComInternet == 88.1
    assert resumo.socioeconomico.anoReferencia == 2022
    assert resumo.socioeconomico.fonte == "IBGE Censo Demográfico 2022"
    assert resumo.socioeconomico.populacao.total == 833932
    assert resumo.socioeconomico.populacao.totalDomiciliosParticulares == 318000
    assert resumo.socioeconomico.estruturaEtaria.razaoDependencia == 63.0
    assert resumo.socioeconomico.saneamento.pctAguaInadequada == 8.2
    assert resumo.socioeconomico.saneamento.pctEsgotoInadequado == 25.4
    assert resumo.socioeconomico.saneamento.pctLixoInadequado == 1.9
    assert resumo.socioeconomico.educacaoPopulacao.taxaAnalfabetismo15Mais == 8.1
    assert municipio_collection.last_find_one_projection is not None
    assert "educacao.mediaIdebAnosFinals" in municipio_collection.last_find_one_projection


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
                "educacao": {
                    "totalEscolas": 80,
                    "totalMatriculas": 42000,
                    "pctComBiblioteca": 51.2,
                    "pctComInternet": 91.7,
                    "mediaIdebAnosIniciais": 4.9,
                    "mediaIdebAnosFinals": 4.2,
                },
                "socioeconomico": {
                    "anoReferencia": 2022,
                    "fonte": "IBGE Censo Demográfico 2022",
                    "saneamento": {
                        "pctAguaRedeGeral": 72.5,
                        "pctEsgotoRedeGeral": 51.2,
                    },
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
    assert resumo.mediaIdebAnosFinals == 4.2
    assert resumo.socioeconomico.saneamento.pctAguaRedeGeral == 72.5
    assert resumo.socioeconomico.saneamento.pctEsgotoRedeGeral == 51.2
    assert resumo.educacao.pctComBiblioteca == 51.2
    assert resumo.socioeconomico.anoReferencia == 2022
    assert resumo.socioeconomico.saneamento.pctAguaRedeGeral == 72.5
