from abc import ABC, abstractmethod
from typing import Any


class ITerritorialAggregationRepository(ABC):
    @abstractmethod
    async def get_cities(
        self,
        co_municipio: str | None = None,
        sg_uf: str | list[str] | None = None,
        include_geometria: bool = False,
    ) -> dict[str, Any]:
        """Returns consolidated city aggregates as GeoJSON FeatureCollection."""
        ...

    @abstractmethod
    async def get_by_municipio(
        self,
        municipio_id_ibge: str,
        bairro: str | None = None,
        include_geometria: bool = False,
        sg_uf: str | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Returns neighborhood documents for a municipality using bairro_indicadores as primary source, including cd_municipio-compatible documents."""
        ...

    async def iter_cities(self, **kwargs):
        result = await self.get_cities(**kwargs)
        for feature in result["features"]:
            yield feature

    async def iter_neighborhoods(self, **kwargs):
        for item in await self.get_by_municipio(**kwargs):
            yield item
