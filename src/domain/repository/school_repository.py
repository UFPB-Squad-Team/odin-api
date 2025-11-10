from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from src.domain.entities.school import School
from src.domain.value_objects.pagination import PaginatedResponse
from src.domain.value_objects.school_criteria import SchoolCriteria

class ISchoolRepository(ABC):
    """
    This is the READ-ONLY interface for the School repository.
    
    It defines the contract for querying school data, using
    unique identifiers or a flexible criteria object for searching.
    """

    @abstractmethod
    def get_by_id(self, school_id: UUID) -> Optional[School]:
        """
        Retrieves a single school by its unique identifier (UUID).
        """
        ...
        
    @abstractmethod
    def get_by_inep_id(self, inep_id: int) -> Optional[School]:
        """
        Retrieves a single school by its INEP ID.
        """
        ...

    @abstractmethod
    def search(self, criteria: SchoolCriteria) -> PaginatedResponse[School]:
        """
        Retrieves a paginated list of schools based on a flexible
        set of criteria.
        
        This method REPLACES list_all, get_by_name, get_by_uf,
        get_by_municipality, and all other paginated get_by_ methods.
        
        Args:
            criteria: A SchoolCriteria object containing all
                      filter parameters and pagination info.
                      
        Returns:
            A PaginatedResponse container with the list of School
            entities for the requested page and pagination metadata.
        """
        ...