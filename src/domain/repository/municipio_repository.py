from abc import ABC, abstractmethod

from src.domain.entities.municipio import MunicipioCatalogItem, MunicipioResumo


class IMunicipioRepository(ABC):
    @abstractmethod
    async def list_municipios(
        self,
        sg_uf: str | None = None,
    ) -> list[MunicipioCatalogItem]:
        ...

    @abstractmethod
    async def get_resumo(
        self,
        municipio_id_ibge: str,
    ) -> MunicipioResumo | None:
        ...
