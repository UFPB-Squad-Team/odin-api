from fastapi import APIRouter, Depends, HTTPException, Path

from src.application.state.get_state_summary.get_state_summary import (
    GetStateSummaryUseCase,
)
from src.domain.entities.state_summary import StateSummary
from src.presentation.http.controller.state.container import container

router = APIRouter()


def get_use_case() -> GetStateSummaryUseCase:
    return container.get_state_summary_use_case()


@router.get("/estados/{sg_uf}/resumo", response_model=StateSummary)
async def get_state_summary(
    sg_uf: str = Path(
        ...,
        min_length=2,
        max_length=2,
        description="Sigla da Unidade Federativa (ex: PB)",
        examples=["PB"],
    ),
    use_case: GetStateSummaryUseCase = Depends(get_use_case),
):
    result = await use_case.execute(sg_uf)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Dados não encontrados para o estado: {sg_uf.upper()}",
        )

    return result
