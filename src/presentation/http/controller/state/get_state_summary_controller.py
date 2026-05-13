from fastapi import APIRouter, HTTPException, Depends, Path
from dependency_injector.wiring import Provide, inject

from src.application.state.get_state_summary.get_state_summary import GetStateSummaryUseCase
from src.domain.entities.state_summary import StateSummary
from src.presentation.http.controller.state.container import Container

router = APIRouter()

@router.get("/estados/{sg_uf}/resumo", response_model=StateSummary)
@inject
async def get_state_summary(
    sg_uf: str = Path(..., description="Sigla da Unidade Federativa (ex: PB)"),
    use_case: GetStateSummaryUseCase = Depends(Provide[Container.get_state_summary_use_case])
):
    result = await use_case.execute(sg_uf)
    if not result:
        raise HTTPException(status_code=404, detail=f"Dados não encontrados para o estado: {sg_uf}")
    return result