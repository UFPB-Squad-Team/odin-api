from typing import Optional

from src.domain.entities.school import School
from src.domain.repository.school_repository import ISchoolRepository

from .get_school_by_id_dto import GetSchoolByIdDTO


class GetSchoolById:
    def __init__(self, school_repository: ISchoolRepository):
        self.school_repository = school_repository

    async def execute(self, dto: GetSchoolByIdDTO) -> Optional[School]:
        return await self.school_repository.get_by_inep_id(dto.escola_id_inep)
