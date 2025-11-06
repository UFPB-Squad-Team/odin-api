from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from src.domain.entities.school import School
from src.domain.value_objects.pagination import PaginatedResponse
from src.domain.enums.enum_uf import UF
from src.domain.enums.enum_dependencia_administrativa import DependenciaAdministrativa
from src.domain.enums.enum_tipo_localizacao import TipoLocalizacao

class ISchoolRepository(ABC):
    """
    This is the READ-ONLY interface for the School repository.
    
    It defines the contract for querying school data, with a focus
    on paginated listing and retrieval by unique identifiers.
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
    def get_by_name(
        self, 
        name: str, 
        page: int, 
        page_size: int
    ) -> PaginatedResponse[School]:
        """
        Retrieves a paginated list of schools matching a name.
        """
        ...

    @abstractmethod
    def get_by_uf(
        self, 
        uf: UF,
        page: int, 
        page_size: int
    ) -> PaginatedResponse[School]:
        """
        Retrieves a paginated list of schools by its UF.
        """
        ...

    @abstractmethod
    def get_by_municipality(
        self, 
        municipality: str, 
        page: int, 
        page_size: int
    ) -> PaginatedResponse[School]:
        """
        Retrieves a paginated list of schools by its municipality.
        """
        ...

    @abstractmethod
    def get_by_street(
        self, 
        street: str, 
        page: int, 
        page_size: int
    ) -> PaginatedResponse[School]:
        """
        Retrieves a paginated list of schools by its street.
        """
        ...
    
    @abstractmethod
    def get_by_neighbourhood(
        self, 
        neighbourhood: str, 
        page: int, 
        page_size: int
    ) -> PaginatedResponse[School]:
        """
        Retrieves a paginated list of schools by its neighbourhood.
        """
        ...

    @abstractmethod
    def get_by_administrative_dependency(
        self, 
        administrative_dependency: DependenciaAdministrativa, 
        page: int, 
        page_size: int
    ) -> PaginatedResponse[School]:
        """
        Retrieves a paginated list of schools by its administrative dependency (municipal, state, federal, private).
        """
        ...

    @abstractmethod
    def get_by_location(
        self, 
        location_type: TipoLocalizacao, 
        page: int, 
        page_size: int
    ) -> PaginatedResponse[School]:
        """
        Retrieves a paginated list of schools by its location type (urban, rural).
        """
        ...

    @abstractmethod
    def list_all(
        self, 
        page: int, 
        page_size: int
    ) -> PaginatedResponse[School]:
        """
        Retrieves a paginated list of all schools.
        """
        ...