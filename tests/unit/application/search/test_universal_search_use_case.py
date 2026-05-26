import pytest

from src.application.search.universal_search.universal_search_dto import (
    SearchResultItem,
    UniversalSearchInputDTO,
)
from src.application.search.universal_search.universal_search_use_case import (
    UniversalSearchUseCase,
)


class FakeRepository:
    def __init__(self):
        self.calls: list[tuple[str, dict]] = []

    async def search_schools(self, q, *, sg_uf=None, municipio_id=None, limit=8):
        self.calls.append(("search_schools", {"q": q, "sg_uf": sg_uf, "municipio_id": municipio_id, "limit": limit}))
        return [
            {
                "escolaIdInep": "1",
                "escolaNome": "Escola Epitacio A",
                "municipioNome": "Joao Pessoa",
                "municipioIdIbge": "2507507",
                "endereco": {"bairro": "Centro"},
                "localizacao": {"coordinates": [-34.86, -7.12]},
            },
            {
                "escolaIdInep": "1",
                "escolaNome": "Escola A duplicada",
                "municipioNome": "Joao Pessoa",
                "municipioIdIbge": "2507507",
                "endereco": {"bairro": "Centro"},
                "localizacao": {"coordinates": [-34.86, -7.12]},
            },
        ]

    async def search_logradouros(self, q, *, sg_uf=None, municipio_id=None, limit=8):
        self.calls.append(("search_logradouros", {"q": q, "sg_uf": sg_uf, "municipio_id": municipio_id, "limit": limit}))
        return [
            {
                "logradouro": "Avenida Epitacio Pessoa",
                "municipioNome": "Joao Pessoa",
                "municipioIdIbge": "2507507",
                "bairros": ["Tambau"],
                "count": 5,
                "avg_lon": -34.84,
                "avg_lat": -7.10,
            },
        ]

    async def search_by_cep(self, q, *, sg_uf=None, municipio_id=None, limit=8):
        self.calls.append(("search_by_cep", {"q": q, "sg_uf": sg_uf, "municipio_id": municipio_id, "limit": limit}))
        return [
            {
                "cep": "58000000",
                "logradouro": "Avenida Epitacio Pessoa",
                "bairro": "Tambau",
                "municipioNome": "Joao Pessoa",
                "municipioIdIbge": "2507507",
                "count": 3,
                "avg_lon": -34.84,
                "avg_lat": -7.10,
            }
        ]

    async def search_municipios(self, q, *, sg_uf=None, limit=8):
        self.calls.append(("search_municipios", {"q": q, "sg_uf": sg_uf, "limit": limit}))
        return [
            {
                "co_municipio": "2507507",
                "municipio": "Joao Pessoa",
                "sg_uf": "PB",
                "socioeconomico": {"populacao": {"total": 833932}},
                "centroide": {"coordinates": [-34.86, -7.12]},
            },
            {
                "co_municipio": "shared-id",
                "municipio": "Municipio Duplicado",
                "sg_uf": "PB",
                "socioeconomico": {"populacao": {"total": 1000}},
                "centroide": {"coordinates": [-35.00, -7.00]},
            },
        ]

    async def search_bairros(self, q, *, sg_uf=None, municipio_id=None, limit=8):
        self.calls.append(("search_bairros", {"q": q, "sg_uf": sg_uf, "municipio_id": municipio_id, "limit": limit}))
        return [
            {
                "bairro": "Tambau",
                "municipio": "Joao Pessoa",
                "municipioIdIbge": "2507507",
                "cd_bairro_ibge": "2507507005",
                "centroide": {"coordinates": [-34.83, -7.10]},
            }
        ]


@pytest.mark.asyncio
async def test_universal_search_prioritizes_categories_and_deduplicates():
    repository = FakeRepository()
    use_case = UniversalSearchUseCase(repository)

    result = await use_case.execute(
        UniversalSearchInputDTO(q="Epitacio", municipio_id="2507507", limit=3)
    )

    assert [item.kind for item in result.results] == ["escola", "logradouro", "bairro"]
    assert result.results[0].id == "1"
    assert result.results[1].id.startswith("logradouro:")
    assert result.results[2].kind == "bairro"
    assert result.total == 3
    assert result.query == "Epitacio"
    assert [call[0] for call in repository.calls] == [
        "search_schools",
        "search_logradouros",
        "search_bairros",
        "search_municipios",
    ]


@pytest.mark.asyncio
async def test_universal_search_detects_cep_queries():
    repository = FakeRepository()
    use_case = UniversalSearchUseCase(repository)

    result = await use_case.execute(UniversalSearchInputDTO(q="58000000", limit=5))

    assert [item.kind for item in result.results] == ["cep"]
    assert repository.calls == [
        ("search_by_cep", {"q": "58000000", "sg_uf": None, "municipio_id": None, "limit": 20})
    ]


@pytest.mark.asyncio
async def test_universal_search_surfaces_municipio_for_strong_match():
    class EmptyStrongMatchesRepository(FakeRepository):
        async def search_schools(self, q, *, sg_uf=None, municipio_id=None, limit=8):
            self.calls.append(("search_schools", {"q": q, "sg_uf": sg_uf, "municipio_id": municipio_id, "limit": limit}))
            return []

        async def search_logradouros(self, q, *, sg_uf=None, municipio_id=None, limit=8):
            self.calls.append(("search_logradouros", {"q": q, "sg_uf": sg_uf, "municipio_id": municipio_id, "limit": limit}))
            return []

        async def search_bairros(self, q, *, sg_uf=None, municipio_id=None, limit=8):
            self.calls.append(("search_bairros", {"q": q, "sg_uf": sg_uf, "municipio_id": municipio_id, "limit": limit}))
            return []

    repository = EmptyStrongMatchesRepository()
    use_case = UniversalSearchUseCase(repository)

    result = await use_case.execute(UniversalSearchInputDTO(q="Joao", limit=5))

    assert [item.kind for item in result.results] == ["municipio", "municipio"]
    assert [call[0] for call in repository.calls] == [
        "search_schools",
        "search_logradouros",
        "search_bairros",
        "search_municipios",
    ]


@pytest.mark.asyncio
async def test_universal_search_prefers_bairro_over_ambiguous_municipio():
    class PrataRepository:
        def __init__(self):
            self.calls: list[tuple[str, dict]] = []

        async def search_schools(self, q, *, sg_uf=None, municipio_id=None, limit=8):
            self.calls.append(("search_schools", {"q": q, "sg_uf": sg_uf, "municipio_id": municipio_id, "limit": limit}))
            return []

        async def search_logradouros(self, q, *, sg_uf=None, municipio_id=None, limit=8):
            self.calls.append(("search_logradouros", {"q": q, "sg_uf": sg_uf, "municipio_id": municipio_id, "limit": limit}))
            return []

        async def search_by_cep(self, q, *, sg_uf=None, municipio_id=None, limit=8):
            self.calls.append(("search_by_cep", {"q": q, "sg_uf": sg_uf, "municipio_id": municipio_id, "limit": limit}))
            return []

        async def search_municipios(self, q, *, sg_uf=None, limit=8):
            self.calls.append(("search_municipios", {"q": q, "sg_uf": sg_uf, "limit": limit}))
            return [
                {
                    "co_municipio": "2512200",
                    "municipio": "Prata",
                    "sg_uf": "PB",
                    "socioeconomico": {"populacao": {"total": 3915}},
                    "centroide": {"coordinates": [-37.08, -7.69]},
                }
            ]

        async def search_bairros(self, q, *, sg_uf=None, municipio_id=None, limit=8):
            self.calls.append(("search_bairros", {"q": q, "sg_uf": sg_uf, "municipio_id": municipio_id, "limit": limit}))
            return [
                {
                    "bairro": "Prata",
                    "municipio": "Campina Grande",
                    "municipioIdIbge": "2504009",
                    "cd_bairro_ibge": "2504009001",
                    "centroide": {"coordinates": [-35.88, -7.23]},
                }
            ]

    repository = PrataRepository()
    use_case = UniversalSearchUseCase(repository)

    result = await use_case.execute(UniversalSearchInputDTO(q="Prata", limit=5))

    assert [item.kind for item in result.results][:2] == ["bairro", "municipio"]
    assert [call[0] for call in repository.calls] == [
        "search_schools",
        "search_logradouros",
        "search_bairros",
        "search_municipios",
    ]