from src.application.search.universal_search.universal_search_use_case import (
    UniversalSearchUseCase,
)

from ..container import container


def get_universal_search_use_case() -> UniversalSearchUseCase:
    return container.universal_search_use_case()