from dataclasses import dataclass
from typing import List, Optional

from src.domain.value_objects.query import QueryOptions


@dataclass
class ListSchoolsDTO:
    query: QueryOptions
    search_term: Optional[str] = None
    municipio: Optional[str] = None
    municipio_id: Optional[str] = None
    dependencia_adm: Optional[List[str]] = None
    tipo_localizacao: Optional[List[str]] = None
    fuzzy_search: bool = False
