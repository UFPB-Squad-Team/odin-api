from contextlib import aclosing
from typing import Any, Dict

from src.domain.repository.school_repository import ISchoolRepository


class GetParaibaGeoJson:
    def __init__(self, school_repository: ISchoolRepository):
        self.school_repository = school_repository

    async def execute(self, municipio_id: str | None = None) -> Dict[str, Any]:
        return await self.school_repository.get_paraiba_geojson(
            municipio_id=municipio_id
        )

    async def iter_items(self, municipio_id=None):
        async with aclosing(
            self.school_repository.iter_geojson_features(municipio_id=municipio_id)
        ) as items:
            async for item in items:
                yield item
