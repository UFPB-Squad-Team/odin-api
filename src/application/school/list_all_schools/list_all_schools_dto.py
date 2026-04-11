from dataclasses import dataclass

from src.domain.value_objects.query import QueryOptions


@dataclass
class ListSchoolsDTO:
    query: QueryOptions
