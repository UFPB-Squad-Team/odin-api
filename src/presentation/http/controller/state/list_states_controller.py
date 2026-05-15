from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from src.application.state.list_states.list_states import ListStatesUseCase
from src.domain.entities.state import State
from src.presentation.http.controller.state.container import container 

router = APIRouter()
def get_use_case() -> ListStatesUseCase:
    return container.list_states_use_case()

@router.get("/estados", response_model=List[State], description="Lista os estados únicos que possuem dados carregados.")
async def list_states(
    q: Optional[str] = Query(None, description="Busca aproximada (fuzzy search) pelo nome ou sigla do estado"),
    use_case: ListStatesUseCase = Depends(get_use_case) 
):
    return await use_case.execute(q=q)