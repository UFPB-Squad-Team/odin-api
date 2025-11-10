from src.domain.repository.school_repository import ISchoolRepository
from src.domain.value_objects.pagination import PaginatedResponse
from src.domain.value_objects.school_criteria import SchoolCriteria
from src.domain.entities.school import School

class ListSchoolsUseCase:
    """
    This is the SINGLE Use Case for listing/searching schools.
    
    It decouples the API layer from the persistence layer.
    Its job is to receive the search criteria and pass it
    to the repository.
    """
    
    def __init__(self, school_repo: ISchoolRepository):
        """
        Initializes the use case with its dependencies.
        It depends on the ISchoolRepository *abstraction*,
        not on a concrete implementation.
        
        Args:
            school_repo: An instance of a class that implements
                         the ISchoolRepository interface.
        """
        self.school_repo = school_repo

    def execute(self, criteria: SchoolCriteria) -> PaginatedResponse[School]:
        """
        Executes the search.
        
        The API Layer is responsible for building the SchoolCriteria
        object from the HTTP query parameters. This Use Case
        simply passes it along to the repository.
        
        Args:
            criteria: A SchoolCriteria object with all filters and
                      pagination info.
            
        Returns:
            A PaginatedResponse DTO containing the result.
            
        Raises:
            DomainValidationError: If the criteria itself is invalid
                                   (though most is checked in the VO).
            Exception: Any database or infrastructure-level exception.
        """

        paginated_result = self.school_repo.search(criteria)
        
        return paginated_result