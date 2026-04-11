from fastapi import APIRouter, Query, Depends, HTTPException, Request
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
from src.presentation.http.query.query_param_parser import QueryParamParser
from .school_query_config import SCHOOL_ALLOWED_FILTERS, SCHOOL_QUERY_FIELDS
from src.presentation.http.schemas.school_search_schema import SchoolSearchSchema


class PaginatedSchoolResponse(BaseModel):
    """
    Defines the response data structure for paginated endpoints.
    """
    schools: List[School]
    total_items: int
    page: int
    page_size: int
    next_cursor: str | None = None


class ListAllSchoolsController:
    def __init__(self, list_all_schools_use_case: ListAllSchools):
        self.list_all_schools_use_case = list_all_schools_use_case

    async def handle(
        self,
        request: Request,
    ):
        query = QueryParamParser.parse(
            query_params=request.query_params,
            allowed_filters=SCHOOL_ALLOWED_FILTERS,
            allowed_fields=SCHOOL_QUERY_FIELDS,
            default_sort_field="escola_id_inep",
            default_page_size=10,
            max_page_size=config.max_page_size,
        )

        search_schema = SchoolSearchSchema.from_query_options(query)

        dto = ListSchoolsDTO(query=search_schema.to_query_options())

        return await self.list_all_schools_use_case.execute(dto=dto)


router = APIRouter()


@router.get("/schools", response_model=PaginatedSchoolResponse)
@router.get("/all", response_model=PaginatedSchoolResponse, include_in_schema=False)
async def list_all_schools_endpoint(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=config.max_page_size),
    list_all_schools_use_case: ListAllSchools = Depends(
        get_list_all_schools_use_case
    ),
):

    cursor = request.query_params.get("cursor")
    offset = (page - 1) * page_size
    if not cursor and offset > config.max_offset_records:
        raise HTTPException(
            status_code=422,
            detail=(
                "Requested page is too deep for offset pagination. "
                "Use smaller page values or filters."
            ),
        )

    controller = ListAllSchoolsController(list_all_schools_use_case)

    result = await controller.handle(request=request)

    return PaginatedSchoolResponse(
        schools=result.items,
        total_items=result.total_items,
        page=result.page,
        page_size=result.page_size,
        next_cursor=result.next_cursor,
    )
