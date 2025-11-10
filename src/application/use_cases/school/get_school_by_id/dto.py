from dataclasses import dataclass
from uuid import UUID

@dataclass
class GetSchoolByIdRequest:
    """
    Data Transfer Object (DTO) for the GetSchoolByIdUseCase input.
    
    It carries the unique identifier of the school to be retrieved.
    """
    school_id: UUID