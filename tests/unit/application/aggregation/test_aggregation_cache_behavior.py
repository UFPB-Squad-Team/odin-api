from unittest.mock import AsyncMock

import pytest

from src.application.aggregation.get_city_aggregations import GetCityAggregations
from src.application.aggregation.get_neighborhood_aggregations import (
    GetNeighborhoodAggregations,
)
from src.infrastructure.cache.aggregation_cache import AggregationCache


@pytest.mark.asyncio
async def test_city_aggregations_second_call_hits_cache():
    repository = AsyncMock()
    city_result = {"type": "FeatureCollection", "features": []}
    repository.get_cities.return_value = city_result

    use_case = GetCityAggregations(repository, cache=AggregationCache(ttl_seconds=300))

    first = await use_case.execute(sg_uf=["PB", "PE"])
    second = await use_case.execute(sg_uf=["PE", "PB"])

    assert first == city_result
    assert second == city_result
    assert repository.get_cities.await_count == 1


@pytest.mark.asyncio
async def test_city_aggregations_bypass_cache_when_disabled():
    repository = AsyncMock()
    repository.get_cities.return_value = {"type": "FeatureCollection", "features": []}

    use_case = GetCityAggregations(repository)

    await use_case.execute(sg_uf=["PB"])
    await use_case.execute(sg_uf=["PB"])

    assert repository.get_cities.await_count == 2


@pytest.mark.asyncio
async def test_city_cache_key_includes_co_municipio_and_geometry():
    repository = AsyncMock()
    repository.get_cities.return_value = {"type": "FeatureCollection", "features": []}

    use_case = GetCityAggregations(repository, cache=AggregationCache(ttl_seconds=300))

    await use_case.execute(sg_uf=["PB"])
    await use_case.execute(sg_uf=["PB"], co_municipio="2507507")
    await use_case.execute(sg_uf=["PB"], include_geometria=True)

    assert repository.get_cities.await_count == 3


@pytest.mark.asyncio
async def test_neighborhood_aggregations_second_call_hits_cache():
    repository = AsyncMock()
    neighborhood_result = [{"bairro": "Centro", "sg_uf": "PB"}]
    repository.get_by_municipio.return_value = neighborhood_result

    use_case = GetNeighborhoodAggregations(
        repository, cache=AggregationCache(ttl_seconds=300)
    )

    first = await use_case.execute(municipio_id_ibge="2507507", sg_uf=["PB"])
    second = await use_case.execute(municipio_id_ibge="2507507", sg_uf=["pb"])

    assert first == neighborhood_result
    assert second == neighborhood_result
    assert repository.get_by_municipio.await_count == 1


@pytest.mark.asyncio
async def test_neighborhood_aggregations_bypass_cache_when_disabled():
    repository = AsyncMock()
    repository.get_by_municipio.return_value = []

    use_case = GetNeighborhoodAggregations(repository)

    await use_case.execute(municipio_id_ibge="2507507", sg_uf=["PB"])
    await use_case.execute(municipio_id_ibge="2507507", sg_uf=["PB"])

    assert repository.get_by_municipio.await_count == 2


@pytest.mark.asyncio
async def test_neighborhood_cache_key_includes_bairro_and_geometry():
    repository = AsyncMock()
    repository.get_by_municipio.return_value = []

    use_case = GetNeighborhoodAggregations(
        repository, cache=AggregationCache(ttl_seconds=300)
    )

    await use_case.execute(municipio_id_ibge="2507507", sg_uf=["PB"])
    await use_case.execute(municipio_id_ibge="2507507", sg_uf=["PB"], bairro="centro")
    await use_case.execute(
        municipio_id_ibge="2507507", sg_uf=["PB"], include_geometria=True
    )

    assert repository.get_by_municipio.await_count == 3
