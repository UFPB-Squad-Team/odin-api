from abc import ABC, abstractmethod
from typing import Any


class ITerritorialAggregationRepository(ABC):
    @abstractmethod
    async def get_cities(
        self,
        co_municipio: str | None = None,
        sg_uf: str | None = None,
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
    ) -> list[dict[str, Any]]:
        """Returns neighborhood documents for a municipality using bairro_indicadores as primary source."""
        ...
