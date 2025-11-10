from dataclasses import dataclass
from typing import Optional
from ..enums.enum_uf import UF
from ..enums.enum_dependencia_administrativa import DependenciaAdministrativa
from ..enums.enum_tipo_localizacao import TipoLocalizacao

@dataclass
class SchoolCriteria:
    """
    A Value Object that encapsulates all possible search
    parameters for a School query.
    
    All filter fields are optional. If a field is None,
    it will not be used in the filter.
    """

    name: Optional[str] = None
    uf: Optional[UF] = None
    municipality: Optional[str] = None
    street: Optional[str] = None
    neighbourhood: Optional[str] = None
    administrative_dependency: Optional[DependenciaAdministrativa] = None
    location_type: Optional[TipoLocalizacao] = None

    page: int = 1
    page_size: int = 10
    
    def __post_init__(self):
        """
        Ensures pagination values are always valid.
        """
        if self.page < 1:
            self.page = 1
        
        if self.page_size < 1 or self.page_size > 100:
            self.page_size = 10