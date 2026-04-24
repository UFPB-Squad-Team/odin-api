from src.domain.repository.school_repository import ISchoolRepository
from src.domain.entities.school import School
from src.domain.value_objects.pagination import PaginatedResponse
from src.application.common.base_list_use_case import BaseListUseCase
from .list_all_schools_dto import ListSchoolsDTO

class ListAllSchools(BaseListUseCase[School]):
    def __init__(self, school_repository: ISchoolRepository):
        super().__init__(school_repository)
        self.school_repository = school_repository # Salvando a referência do repositório

    async def execute(self, dto: ListSchoolsDTO) -> PaginatedResponse[School]:
        # Aqui a mágica acontece: repassando os dados do DTO direto pra sua função do banco!
        return await self.school_repository.list_all(
            page=dto.query.page,
            page_size=dto.query.page_size,
            search_term=dto.search_term,
            municipio=dto.municipio
        )