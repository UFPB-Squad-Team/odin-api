from typing import Any

from src.domain.repository.territorial_aggregation_repository import (
    ITerritorialAggregationRepository,
)


class GetCityAggregations:
    def __init__(self, repository: ITerritorialAggregationRepository):
        self.repository = repository

    async def execute(
        self,
        co_municipio: str | None = None,
        sg_uf: str | None = None,
        include_geometria: bool = False,
    ) -> dict[str, Any]:
        return await self.repository.get_cities(
            co_municipio=co_municipio,
            sg_uf=sg_uf,
            include_geometria=include_geometria,
        )
