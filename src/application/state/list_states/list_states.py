from typing import List, Optional
from src.domain.entities.state import State
from src.domain.repository.state_repository import IStateRepository

class ListStatesUseCase:
    def __init__(self, state_repository: IStateRepository):
        self.state_repository = state_repository

    async def execute(self, q: Optional[str] = None) -> List[State]:
        return await self.state_repository.list_distinct_states(query=q)