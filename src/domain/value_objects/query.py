from dataclasses import dataclass, field
from typing import Any, Generic, List, Optional, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class QueryFilter:
    field: str
    operator: str
    value: Any


@dataclass(frozen=True)
class QuerySort:
    field: str
    direction: int = 1


@dataclass
class QueryOptions:
    page: int = 1
    page_size: int = 10
    cursor: Optional[str] = None
    filters: List[QueryFilter] = field(default_factory=list)
    sort: Optional[QuerySort] = None
    fields: Optional[List[str]] = None


@dataclass
class CursorPage(Generic[T]):
    items: List[T]
    total_items: int
    page: int
    page_size: int
    next_cursor: Optional[str] = None
