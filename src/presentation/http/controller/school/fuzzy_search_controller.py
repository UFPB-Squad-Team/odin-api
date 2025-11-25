from fastapi import APIRouter, Query, Depends, HTTPException
from src.application.school.fuzzy_search.fuzzy_search import FuzzySearch
from src.application.school.fuzzy_search.fuzzy_search_dto import FuzzySearchDTO
from .callable.school_callable import get_fuzzy_search_use_case
from typing import List
from src.domain.entities.school import School
from pydantic import BaseModel

# Modelo de resposta paginada
class PaginatedSchoolResponse(BaseModel):
    schools: List[School]
    total_items: int
    page: int
    page_size: int

class FuzzySearchController:
    def __init__(self, use_case: FuzzySearch):
        self.use_case = use_case

    async def handle(self, query: str, page: int, page_size: int):
        if not query or len(query.strip()) < 1:
             raise HTTPException(status_code=400, detail="Search query cannot be empty")

        dto = FuzzySearchDTO(query=query, page=page, page_size=page_size)
        return await self.use_case.execute(dto)

router = APIRouter()

@router.get("/search", response_model=PaginatedSchoolResponse)
async def fuzzy_search_schools(
    q: str = Query(..., min_length=1, description="Busca inteligente (Nome, Cidade, Estado, etc)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    use_case: FuzzySearch = Depends(get_fuzzy_search_use_case),
):
    controller = FuzzySearchController(use_case)
    result = await controller.handle(query=q, page=page, page_size=page_size)

    return PaginatedSchoolResponse(
        schools=result.items,
        total_items=result.total_items,
        page=result.page,
        page_size=result.page_size
    )