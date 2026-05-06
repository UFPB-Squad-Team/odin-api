from fastapi import APIRouter, Depends, HTTPException, Path, status
from src.domain.entities.bairro import BairroResumo
from src.application.bairro.get_bairro_resumo.get_bairro_resumo import GetBairroResumo
from src.application.bairro.get_bairro_resumo.get_bairro_resumo_dto import GetBairroResumoDTO
from .callable.bairro_callable import get_bairro_resumo_use_case

router = APIRouter()

@router.get(
    "/bairros/{bairro_id}/resumo",
    response_model=BairroResumo,
    tags=["bairros"],
    summary="Resumo de bairro",
    description="Retorna indicadores de bairro com fallback para agregação de setores."
)
async def get_bairro_resumo(
    bairro_id: str = Path(..., min_length=10, max_length=10, description="ID de 10 dígitos"),
    use_case: GetBairroResumo = Depends(get_bairro_resumo_use_case)
):
    dto = GetBairroResumoDTO(bairro_id=bairro_id)
    resumo = await use_case.execute(dto)

    if not resumo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bairro não encontrado."
        )

    return resumo