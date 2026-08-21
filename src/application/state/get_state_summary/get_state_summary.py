from src.domain.entities.state_summary import StateSummary
from src.domain.factories.state_summary_factory import StateSummaryFactory
from src.domain.repository.state_repository import IStateRepository


class GetStateSummaryUseCase:
    def __init__(self, state_repository: IStateRepository):
        self.state_repository = state_repository

    async def execute(self, sg_uf: str) -> StateSummary | None:
        normalized_sg_uf = sg_uf.strip().upper()
        cities = await self.state_repository.get_cities_data_by_state(normalized_sg_uf)
        if not cities:
            return None
        return StateSummaryFactory.create_from_cities(normalized_sg_uf, cities)
