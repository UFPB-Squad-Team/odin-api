import pytest
from pydantic import ValidationError

from src.domain.entities.school import School
from src.domain.enums.enum_dependencia_administrativa import (
    DependenciaAdministrativa,
)
from src.domain.enums.enum_tipo_localizacao import TipoLocalizacao
from src.domain.enums.enum_uf import UF
from src.domain.value_objects.location import Location


def test_school_builds_with_defaults():
    school = School(
        municipio_id_ibge="1234567",
        escola_id_inep=12345678,
        escola_nome="Escola A",
        municipio_nome="Joao Pessoa",
        estado_sigla=UF.PARAIBA,
        dependencia_adm=DependenciaAdministrativa.MUNICIPAL,
        tipo_localizacao=TipoLocalizacao.URBANA,
        localizacao=Location(type="Point", coordinates=(-34.86, -7.12)),
    )

    assert school.id
    assert school.indicadores.totalAlunos == 0
    assert school.infraestrutura == {}


def test_school_rejects_invalid_ibge_code():
    with pytest.raises(ValidationError):
        School(
            municipio_id_ibge="123",
            escola_id_inep=12345678,
            escola_nome="Escola A",
            municipio_nome="Joao Pessoa",
            estado_sigla=UF.PARAIBA,
            dependencia_adm=DependenciaAdministrativa.MUNICIPAL,
            tipo_localizacao=TipoLocalizacao.URBANA,
            localizacao=Location(type="Point", coordinates=(-34.86, -7.12)),
        )