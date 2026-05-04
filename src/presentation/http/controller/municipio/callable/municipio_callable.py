from src.application.municipio.get_municipio_resumo.get_municipio_resumo import (
    GetMunicipioResumo,
)
from src.application.municipio.list_municipios.list_municipios import ListMunicipios
from src.presentation.http.controller.municipio.container import container


def get_list_municipios_use_case() -> ListMunicipios:
    return container.list_municipios_use_case()


def get_municipio_resumo_use_case() -> GetMunicipioResumo:
    return container.get_municipio_resumo_use_case()
