from typing import List, Optional

from src.domain.entities.state import State
from src.domain.repository.state_repository import IStateRepository


class ListStatesUseCase:
    def __init__(self, state_repository: IStateRepository):
        self.state_repository = state_repository
        self.nordeste_siglas = {"AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"}

    async def execute(self, q: Optional[str] = None) -> List[State]:
        all_states = await self.state_repository.list_distinct_states(query=q)
        return [
            state for state in all_states if state.sigla.upper() in self.nordeste_siglas
        ]
