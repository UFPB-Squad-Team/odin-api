from fastapi import APIRouter, Query, Depends, HTTPException
from src.domain.entities.school import School
from src.application.school.list_all_schools.list_all_schools import (
    ListAllSchools,
)
from .callable.school_callable import get_list_all_schools_use_case
from src.application.school.list_all_schools.list_all_schools_dto import (
    ListSchoolsDTO,
)
from typing import List
from pydantic import BaseModel
from src.infrastructure.database.config.app_config import config


class PaginatedSchoolResponse(BaseModel):
    """
    Defines the response data structure for paginated endpoints.
    """
    schools: List[School]
    total_items: int
    page: int
    page_size: int


class ListAllSchoolsController:
    def __init__(self, list_all_schools_use_case: ListAllSchools):
        self.list_all_schools_use_case = list_all_schools_use_case

    async def handle(
        self,
        page: int = 1,
        page_size: int = 10
    ):
        dto = ListSchoolsDTO(page=page, page_size=page_size)

        return await self.list_all_schools_use_case.execute(dto=dto)


router = APIRouter()


@router.get("/all", response_model=PaginatedSchoolResponse)
async def list_all_schools(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=config.max_page_size),
    list_all_schools_use_case: ListAllSchools = Depends(
        get_list_all_schools_use_case
    ),
):

    offset = (page - 1) * page_size
    if offset > config.max_offset_records:
        raise HTTPException(
            status_code=422,
            detail=(
                "Requested page is too deep for offset pagination. "
                "Use smaller page values or filters."
            ),
        )

    controller = ListAllSchoolsController(list_all_schools_use_case)

    result = await controller.handle(page=page, page_size=page_size)

    return PaginatedSchoolResponse(
        schools=result.items,
        total_items=result.total_items,
        page=result.page,
        page_size=result.page_size
    )
