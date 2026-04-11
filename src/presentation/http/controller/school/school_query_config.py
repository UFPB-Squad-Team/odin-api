from src.presentation.http.query.query_param_parser import AllowedFilter, to_int, to_str

SCHOOL_QUERY_FIELDS = [
    "id",
    "escola_id_inep",
    "escola_nome",
    "municipio_nome",
    "estado_sigla",
    "dependencia_adm",
    "tipo_localizacao",
    "municipio_id_ibge",
    "bairro",
]

SCHOOL_ALLOWED_FILTERS = {
    "id": AllowedFilter(caster=to_str, operators=["eq", "in"]),
    "escola_id_inep": AllowedFilter(caster=to_int, operators=["eq", "gt", "gte", "lt", "lte", "in"]),
    "escola_nome": AllowedFilter(caster=to_str, operators=["eq", "contains", "startswith", "endswith"]),
    "municipio_nome": AllowedFilter(caster=to_str, operators=["eq", "contains", "startswith", "endswith"]),
    "estado_sigla": AllowedFilter(caster=to_str, operators=["eq", "in"]),
    "dependencia_adm": AllowedFilter(caster=to_str, operators=["eq", "in"]),
    "tipo_localizacao": AllowedFilter(caster=to_str, operators=["eq", "in"]),
    "municipio_id_ibge": AllowedFilter(caster=to_str, operators=["eq", "in"]),
    "bairro": AllowedFilter(caster=to_str, operators=["eq", "contains", "startswith", "endswith"]),
}
