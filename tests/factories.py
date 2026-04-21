from src.domain.entities.school import School
from src.domain.enums.enum_dependencia_administrativa import (
    DependenciaAdministrativa,
)
from src.domain.enums.enum_tipo_localizacao import TipoLocalizacao
from src.domain.enums.enum_uf import UF
from src.domain.value_objects.indicators import Indicadores
from src.domain.value_objects.location import Location


def build_school() -> School:
    return School(
        id="school-1",
        municipio_id_ibge="1234567",
        escola_id_inep=12345678,
        escola_nome="Escola A",
        municipio_nome="Joao Pessoa",
        estado_sigla=UF.PARAIBA,
        dependencia_adm=DependenciaAdministrativa.MUNICIPAL,
        tipo_localizacao=TipoLocalizacao.URBANA,
        localizacao=Location(type="Point", coordinates=(-34.86, -7.12)),
        endereco={"bairro": "Centro"},
        indicadores=Indicadores(totalAlunos=120),
        infraestrutura={
            "possuiAguaPotavel": True,
            "equipamentos": {"desktopAluno": True},
            "internet": {"possuiInternet": True},
            "salas": {"acessiveis": 1, "climatizadas": 2, "utilizadas": 2},
        },
    )


def build_school_document(document_id: str = "school-1"):
    return {
        "_id": document_id,
        "municipioIdIbge": "1234567",
        "escolaIdInep": 12345678,
        "escolaNome": "Escola A",
        "municipioNome": "Joao Pessoa",
        "estadoSigla": "PB",
        "dependenciaAdm": "Municipal",
        "tipoLocalizacao": "Urbana",
        "localizacao": {"type": "Point", "coordinates": [-34.86, -7.12]},
        "endereco": {"bairro": "Centro", "municipio": "Joao Pessoa", "uf": "PB"},
        "indicadores": {"totalAlunos": 120},
        "infraestrutura": {
            "possuiAguaPotavel": True,
            "equipamentos": {"desktopAluno": True},
            "internet": {"possuiInternet": True},
            "salas": {"acessiveis": 1, "climatizadas": 2, "utilizadas": 2},
        },
    }


class FakeCursor:
    def __init__(self, documents):
        self.documents = list(documents)
        self.sort_args = None
        self.skip_value = None
        self.limit_value = None

    def sort(self, field, direction=None):
        if isinstance(field, list):
            self.sort_args = field
        else:
            self.sort_args = (field, direction)
        return self

    def skip(self, value):
        self.skip_value = value
        return self

    def limit(self, value):
        self.limit_value = value
        return self

    async def to_list(self, length):
        return self.documents[:length]


class FakeAggregateCursor:
    def __init__(self, documents):
        self.documents = list(documents)

    async def to_list(self, length):
        if length is None:
            return list(self.documents)
        return self.documents[:length]


class FakeCollection:
    def __init__(self, documents):
        self.documents = list(documents)
        self.find_args = None
        self.cursor = FakeCursor(self.documents)
        self.aggregate_documents = list(documents)
        self.aggregate_pipeline = None
        self.aggregate_kwargs = None
        self.count_query = None
        self.estimated_count_called = False
        self.find_one_queries = []

    def find(self, query=None, projection=None):
        self.find_args = (query or {}, projection)
        return self.cursor

    async def find_one(self, query):
        self.find_one_queries.append(query)

        target_id = query.get("_id")
        for document in self.documents:
            if document.get("_id") == target_id:
                return document
        return None

    async def count_documents(self, query):
        self.count_query = query
        return len(self.documents)

    async def estimated_document_count(self):
        self.estimated_count_called = True
        return len(self.documents)

    def aggregate(self, pipeline, **kwargs):
        self.aggregate_pipeline = pipeline
        self.aggregate_kwargs = kwargs
        return FakeAggregateCursor(self.aggregate_documents)