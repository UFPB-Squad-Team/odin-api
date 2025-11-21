from src.domain.repository.school_repository import ISchoolRepository
from src.domain.entities.school import School
from .get_school_by_id_dto import GetSchoolByIdDTO
from typing import Optional

class GetSchoolById:
    def __init__(self, school_repository: ISchoolRepository):
        self.school_repository = school_repository

    async def execute(self, dto: GetSchoolByIdDTO) -> Optional[School]:
        return await self.school_repository.get_by_id(dto.id)