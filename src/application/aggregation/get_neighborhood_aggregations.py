from typing import Any

from src.domain.repository.territorial_aggregation_repository import (
    ITerritorialAggregationRepository,
)
from src.domain.validators.neighborhood_validation import NeighborhoodValidator


class GetNeighborhoodAggregations:
    def __init__(self, repository: ITerritorialAggregationRepository):
        self.repository = repository

    async def execute(
        self,
        municipio_id_ibge: str,
        bairro: str | None = None,
        include_geometria: bool = False,
    ) -> list[dict[str, Any]]:
        NeighborhoodValidator(municipio_id_ibge)
        return await self.repository.get_by_municipio(
            municipio_id_ibge=municipio_id_ibge,
            bairro=bairro,
            include_geometria=include_geometria,
        )
