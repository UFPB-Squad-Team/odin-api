from typing import Any, Dict

from src.domain.repository.school_repository import ISchoolRepository


class GetBairrosGeoJson:
    def __init__(self, school_repository: ISchoolRepository):
        self.school_repository = school_repository

    async def execute(self, municipio: str) -> Dict[str, Any]:
        return await self.school_repository.get_bairros_geojson(municipio)
