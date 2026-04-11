from typing import Generic, TypeVar

from src.domain.repository.base_repository import IBaseReadRepository
from src.domain.value_objects.pagination import PaginatedResponse
from src.domain.value_objects.query import QueryOptions

T = TypeVar("T")


class BaseListUseCase(Generic[T]):
    def __init__(self, repository: IBaseReadRepository[T]):
        self.repository = repository

    async def execute(self, query: QueryOptions) -> PaginatedResponse[T]:
        return await self.repository.find_paginated(query)
