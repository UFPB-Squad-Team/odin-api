from typing import Any

from src.domain.repository.territorial_aggregation_repository import (
    ITerritorialAggregationRepository,
)
from src.domain.validators.neighborhood_validation import NeighborhoodValidator
from src.infrastructure.cache.aggregation_cache import (
    AggregationCache,
    uf_cache_key,
)


class GetNeighborhoodAggregations:
    def __init__(
        self,
        repository: ITerritorialAggregationRepository,
        cache: AggregationCache | None = None,
    ):
        self.repository = repository
        self.cache = cache

    async def execute(
        self,
        municipio_id_ibge: str,
        bairro: str | None = None,
        include_geometria: bool = False,
        sg_uf: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        NeighborhoodValidator(municipio_id_ibge)
        if self.cache is None:
            return await self.repository.get_by_municipio(
                municipio_id_ibge=municipio_id_ibge,
                bairro=bairro,
                sg_uf=sg_uf,
                include_geometria=include_geometria,
            )

        key = self._build_cache_key(
            municipio_id_ibge=municipio_id_ibge,
            bairro=bairro,
            ufs=uf_cache_key(sg_uf),
            include_geometria=include_geometria,
        )

        cached = await self.cache.get(key)
        if cached is not None:
            return cached

        result = await self.repository.get_by_municipio(
            municipio_id_ibge=municipio_id_ibge,
            bairro=bairro,
            sg_uf=sg_uf,
            include_geometria=include_geometria,
        )
        await self.cache.set(key, result)
        return result

    @staticmethod
    def _build_cache_key(
        *,
        municipio_id_ibge: str,
        bairro: str | None,
        ufs: tuple[str, ...] | None,
        include_geometria: bool,
    ) -> str:
        uf_part = ",".join(ufs) if ufs else "__all_ufs__"
        return (
            f"neighborhood:{municipio_id_ibge}:{bairro or '__all__'}:{uf_part}:"
            f"geom={1 if include_geometria else 0}"
        )
