from fastapi import APIRouter, HTTPException, Query, Depends
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

        result = await self.list_all_schools_use_case.execute(dto=dto)

        if not result.items:
            raise HTTPException(status_code=404, detail="Schools not found")

        return result


router = APIRouter()


@router.get("/all", response_model=PaginatedSchoolResponse)
async def list_all_schools(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    list_all_schools_use_case: ListAllSchools = Depends(
        get_list_all_schools_use_case
    ),
):

    controller = ListAllSchoolsController(list_all_schools_use_case)

    result = await controller.handle(page=page, page_size=page_size)

    return PaginatedSchoolResponse(
        schools=result.items,
        total_items=result.total_items,
        page=result.page,
        page_size=result.page_size
    )
