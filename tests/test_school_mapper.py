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
    assert school.matriculas.totalAlunos == 270
    assert school.matriculas.educacaoInfantil == 45
    assert school.matriculas.educacaoInfantilCreche == 15
    assert school.matriculas.educacaoInfantilPreEscola == 30
    assert school.matriculas.fundamentalTotal == 120
    assert school.matriculas.fundamentalAnosIniciais == 70
    assert school.matriculas.fundamentalAnosFinais == 50
    assert school.matriculas.ensinoMedio == 80
    assert school.matriculas.eja == 25
    assert school.infraestrutura.possuiAguaPotavel is True
    assert school.infraestrutura.equipamentos.desktopAluno is True