from typing import List, Dict, Any
from src.domain.entities.school import School
from src.domain.value_objects.location import Location
from src.domain.value_objects.indicators import Indicadores

MONGO_TO_DOMAIN_MAP = {
    '_id': 'id',
    'municipioIdIbge': 'municipio_id_ibge',
    'escolaIdInep': 'escola_id_inep',
    'escolaNome': 'escola_nome',
    'municipioNome': 'municipio_nome',
    'estadoSigla': 'estado_sigla',
    'dependenciaAdm': 'dependencia_adm',
    'tipoLocalizacao': 'tipo_localizacao',
    'localizacao': 'localizacao',
    'indicadores': 'indicadores',
    'infraestrutura': 'infraestrutura',
}


class MongoSchoolMapper:
    @staticmethod
    def to_domain(school_doc: Dict[str, Any]) -> School:
        domain_data: Dict[str, Any] = {}

        for mongo_key, domain_key in MONGO_TO_DOMAIN_MAP.items():
            if mongo_key in school_doc:
                domain_data[domain_key] = school_doc[mongo_key]

        if 'id' in domain_data:
            domain_data['id'] = str(domain_data['id'])

        if ('municipio_id_ibge' in domain_data
                and domain_data['municipio_id_ibge'] is not None):
            domain_data['municipio_id_ibge'] = str(
                domain_data['municipio_id_ibge']
            )

        if (
            'escola_id_inep' in domain_data
            and domain_data['escola_id_inep'] is not None
        ):
            try:
                _escola_id = domain_data['escola_id_inep']
                domain_data['escola_id_inep'] = int(_escola_id)
            except ValueError as e:
                msg = (
                    "Não foi possível converter escola_id_inep para inteiro. "
                    f"Detalhes: {e}"
                )
                raise ValueError(msg)

        if (
            'localizacao' in domain_data
            and isinstance(domain_data['localizacao'], dict)
        ):
            domain_data['localizacao'] = Location(**domain_data['localizacao'])

        if (
            'indicadores' in domain_data
            and isinstance(domain_data['indicadores'], dict)
        ):
            indicadores_data = domain_data['indicadores']
            domain_data['indicadores'] = Indicadores(**indicadores_data)

        return School(**domain_data)

    @staticmethod
    def to_domain_many(school_docs: List[Dict[str, Any]]) -> List[School]:
        return [MongoSchoolMapper.to_domain(doc.copy()) for doc in school_docs]
