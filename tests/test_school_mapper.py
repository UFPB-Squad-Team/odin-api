from src.infrastructure.database.mapper.school_mapper import MongoSchoolMapper

from tests.factories import build_school_document


def test_mapper_converts_mongo_document_into_school():
    school = MongoSchoolMapper.to_domain(build_school_document())

    assert school.id == "school-1"
    assert school.municipio_id_ibge == "1234567"
    assert school.escola_id_inep == 12345678
    assert school.escola_nome == "Escola A"
    assert school.endereco.bairro == "Centro"
    assert school.indicadores.totalAlunos == 120
    assert school.infraestrutura.possuiAguaPotavel is True
    assert school.infraestrutura.equipamentos.desktopAluno is True