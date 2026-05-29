from abc import ABC, abstractmethod
from typing import Any, Optional


class IUniversalSearchRepository(ABC):
    @abstractmethod
    async def search_schools(
        self,
        q: str,
        *,
        sg_uf: Optional[str] = None,
        municipio_id: Optional[str] = None,
        limit: int = 8,
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def search_logradouros(
        self,
        q: str,
        *,
        sg_uf: Optional[str] = None,
        municipio_id: Optional[str] = None,
        limit: int = 8,
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def search_by_cep(
        self,
        q: str,
        *,
        sg_uf: Optional[str] = None,
        municipio_id: Optional[str] = None,
        limit: int = 8,
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def search_municipios(
        self,
        q: str,
        *,
        sg_uf: Optional[str] = None,
        limit: int = 8,
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def search_bairros(
        self,
        q: str,
        *,
        sg_uf: Optional[str] = None,
        municipio_id: Optional[str] = None,
        limit: int = 8,
    ) -> list[dict[str, Any]]: ...
