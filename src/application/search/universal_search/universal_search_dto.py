from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class UniversalSearchInputDTO:
    q: str
    sg_uf: str | None = None
    municipio_id: str | None = None
    limit: int = 20


@dataclass(frozen=True)
class SearchResultItem:
    id: str
    kind: str
    label: str
    subtitle: str
    coordinates: tuple[float, float]
    municipio_id_ibge: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class UniversalSearchOutputDTO:
    results: list[SearchResultItem]
    total: int
    query: str