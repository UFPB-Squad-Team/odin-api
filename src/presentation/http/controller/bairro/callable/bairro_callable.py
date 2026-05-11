from src.application.bairro.get_bairro_resumo.get_bairro_resumo import GetBairroResumo
from ..container import bairro_container

def get_bairro_resumo_use_case() -> GetBairroResumo:
    return bairro_container.get_resumo_use_case()