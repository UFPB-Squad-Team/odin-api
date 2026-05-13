from fastapi import APIRouter, Depends
from src.domain.entities.stats import SummaryStats
from src.presentation.http.controller.school.callable.school_callable import get_summary_stats_use_case

router = APIRouter(prefix="/school/stats", tags=["Estatísticas"])

@router.get("/summary", response_model=SummaryStats)
async def get_summary(
   
    use_case = Depends(get_summary_stats_use_case)
):
    return await use_case.execute()