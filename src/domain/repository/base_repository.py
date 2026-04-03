from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

from src.domain.value_objects.pagination import PaginatedResponse
from src.domain.value_objects.query import QueryOptions

T = TypeVar("T")


class IBaseReadRepository(ABC, Generic[T]):
    @abstractmethod
    async def find_paginated(self, query: QueryOptions) -> PaginatedResponse[T]:
        ...

    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        ...

    @abstractmethod
    async def exists(self, entity_id: str) -> bool:
        ...
