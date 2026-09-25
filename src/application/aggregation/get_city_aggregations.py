from typing import Any

from src.domain.repository.territorial_aggregation_repository import (
    ITerritorialAggregationRepository,
)
from src.infrastructure.cache.aggregation_cache import (
    AggregationCache,
    uf_cache_key,
)


class GetCityAggregations:
    def __init__(
        self,
        repository: ITerritorialAggregationRepository,
        cache: AggregationCache | None = None,
    ):
        self.repository = repository
        self.cache = cache

    async def execute(
        self,
        co_municipio: str | None = None,
        sg_uf: str | list[str] | None = None,
        include_geometria: bool = False,
    ) -> dict[str, Any]:
        if self.cache is None:
            return await self.repository.get_cities(
                co_municipio=co_municipio,
                sg_uf=sg_uf,
                include_geometria=include_geometria,
            )

        key = self._build_cache_key(
            co_municipio=co_municipio,
            ufs=uf_cache_key(sg_uf),
            include_geometria=include_geometria,
        )

        cached = await self.cache.get(key)
        if cached is not None:
            return cached

        result = await self.repository.get_cities(
            co_municipio=co_municipio,
            sg_uf=sg_uf,
            include_geometria=include_geometria,
        )
        await self.cache.set(key, result)
        return result

    @staticmethod
    def _build_cache_key(
        *,
        co_municipio: str | None,
        ufs: tuple[str, ...] | None,
        include_geometria: bool,
    ) -> str:
        uf_part = ",".join(ufs) if ufs else "__all_ufs__"
        return (
            f"city:{co_municipio or '__all__'}:{uf_part}:"
            f"geom={1 if include_geometria else 0}"
        )
