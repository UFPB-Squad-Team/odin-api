from dataclasses import dataclass
from typing import Optional
from src.domain.value_objects.query import QueryOptions


@dataclass
class ListSchoolsDTO:
    query: QueryOptions
    search_term: Optional[str] = None
    municipio: Optional[str] = None
    municipio_id: Optional[str] = None
