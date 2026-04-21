from typing import Any, Dict, Optional

from src.domain.repository.school_repository import ISchoolRepository


class GetBairroBySchoolId:
    def __init__(self, school_repository: ISchoolRepository):
        self.school_repository = school_repository

    async def execute(self, school_id: str) -> Optional[Dict[str, Any]]:
        return await self.school_repository.get_bairro_by_school_id(school_id)
