from unittest.mock import AsyncMock

import pytest

from src.application.aggregation.get_city_aggregations import GetCityAggregations
from src.application.aggregation.get_neighborhood_aggregations import (
    GetNeighborhoodAggregations,
)


@pytest.mark.asyncio
async def test_city_use_case_passes_multiple_ufs_to_repository():
    repository = AsyncMock()
    repository.get_cities.return_value = {"type": "FeatureCollection", "features": []}
    use_case = GetCityAggregations(repository)

    await use_case.execute(sg_uf=["PB", "PE"])

    repository.get_cities.assert_awaited_once_with(
        co_municipio=None,
        sg_uf=["PB", "PE"],
        include_geometria=False,
    )


@pytest.mark.asyncio
async def test_neighborhood_use_case_passes_multiple_ufs_to_repository():
    repository = AsyncMock()
    repository.get_by_municipio.return_value = []
    use_case = GetNeighborhoodAggregations(repository)

    await use_case.execute(
        municipio_id_ibge="2507507",
        sg_uf=["PB", "PE"],
    )

    repository.get_by_municipio.assert_awaited_once_with(
        municipio_id_ibge="2507507",
        bairro=None,
        sg_uf=["PB", "PE"],
        include_geometria=False,
    )
