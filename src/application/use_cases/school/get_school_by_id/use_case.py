from typing import Optional
from src.domain.repository.school_repository import ISchoolRepository
from src.domain.entities.school import School
from .dto import GetSchoolByIdRequest

class GetSchoolByIdUseCase:
    """
    Use Case to retrieve a single school by its unique ID.
    
    It orchestrates the retrieval by delegating the call
    to the repository layer.
    """
    
    def __init__(self, school_repo: ISchoolRepository):
        """
        Initializes the use case with the school repository abstraction.
        
        Args:
            school_repo: An implementation of ISchoolRepository.
        """
        self.school_repo = school_repo

    def execute(self, request: GetSchoolByIdRequest) -> Optional[School]:
        """
        Executes the retrieval logic.
        
        Args:
            request: A DTO containing the school_id.
            
        Returns:
            The School entity if found, otherwise None.
        
        Note:
            It returns None if the school is not found, as this is a
            valid search result, not a system error. The API layer
            will be responsible for translating this 'None' into a 404.
        """

        school = self.school_repo.get_by_id(
            school_id=request.school_id
        )

        return school