from src.domain.entities.state_summary import StateSummary
from src.domain.repository.state_repository import IStateRepository
from src.domain.factories.state_summary_factory import StateSummaryFactory

class GetStateSummaryUseCase:
    def __init__(self, state_repository: IStateRepository):
        self.state_repository = state_repository

    async def execute(self, sg_uf: str) -> StateSummary | None:
     
        cities = await self.state_repository.get_cities_data_by_state(sg_uf)
        if not cities:
            return None 
        return StateSummaryFactory.create_from_cities(sg_uf, cities)