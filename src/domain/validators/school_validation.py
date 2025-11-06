from typing import Optional, Dict
from src.domain.validators.school_validation import DomainValidationError
from ..entities.school import Location, Indicadores
from ..enums.enum_uf import UF
from ..enums.enum_dependencia_administrativa import DependenciaAdministrativa
from ..enums.enum_tipo_localizacao import TipoLocalizacao


class SchoolValidator:
    def __init__(
        self,
        municipio_id_ibge: str,
        escola_id_inep: int,
        escola_nome: str,
        municipio_nome: str,
        estado_sigla: UF,
        dependencia_adm: DependenciaAdministrativa,
        tipo_localizacao: TipoLocalizacao,
        localizacao: Location,
        indicadores: Optional[Indicadores],
        infraestrutura: Optional[Dict[str, bool]] = None
    ):
        
        self._municipio_id_ibge = municipio_id_ibge
        self._escola_id_inep = escola_id_inep
        self._escola_nome = escola_nome
        self._municipio_nome = municipio_nome
        self._estado_sigla = estado_sigla
        self._dependencia_adm = dependencia_adm
        self._tipo_localizacao = tipo_localizacao
        self._localizacao = localizacao
        self._indicadores = indicadores
        
        self._validate()

    def _validate(self):
        """
        Orchestrator method that calls all individual validation checks.
        """
        self._validate_ibge()
        self._validate_inep()
        self._validate_nome()
        self._validate_municipio_nome()
        self._validate_location()
        self._validate_indicadores()

    def _validate_ibge(self):
        """ Validates the 7-digit IBGE municipality code. """
        if not self._municipio_id_ibge or len(self._municipio_id_ibge) != 7 or not self._municipio_id_ibge.isdigit():
            raise DomainValidationError("municipio_id_ibge must be 7 digits.")

    def _validate_inep(self):
        """ Validates the 8-digit INEP school code. """
        if not (10000000 <= self._escola_id_inep <= 99999999):
            raise DomainValidationError(f"escola_id_inep is invalid, must be 8 digits: {self._escola_id_inep}.")

    def _validate_nome(self):
        """ Validates the school name. """
        if not self._escola_nome or len(self._escola_nome.strip()) == 0:
            raise DomainValidationError("escola_nome is required.")
        if len(self._escola_nome) > 255:
            raise DomainValidationError("escola_nome must not exceed 255 characters.")

    def _validate_municipio_nome(self):
        """ Validates the municipality name. """
        if not self._municipio_nome or len(self._municipio_nome.strip()) == 0:
            raise DomainValidationError("municipio_nome is required.")
            
    def _validate_location(self):
        """ Validates the Location dataclass. """
        if self._localizacao is None:
            raise DomainValidationError("localizacao is required.")
        if self._localizacao.type != "Point":
            raise DomainValidationError("localizacao.type must be 'Point'.")
        
        lat, lon = self._localizacao.coordinates
        if not (-90.0 <= lat <= 90.0):
            raise DomainValidationError(f"Invalid latitude: {lat}. Must be between -90 and 90.")
        if not (-180.0 <= lon <= 180.0):
            raise DomainValidationError(f"Invalid longitude: {lon}. Must be between -180 and 180.")

    def _validate_indicadores(self):
        """ Validates the optional Indicadores dataclass. """
        if self._indicadores:
            for i in self.Indicadores:
                if not i:
                    raise DomainValidationError(f"Indicadores fields must be valid. Indicador {i} is invalid.")
    
    def _validate_infraestrutura(self):
        """ Validates the optional infraestrutura dictionary. """
        if self._infraestrutura:
            for key, value in self._infraestrutura.items():
                if value is None or key is None:
                    raise DomainValidationError(f"Infraestructure data cannot have null keys or values.")
                if not isinstance(value, bool):
                    raise DomainValidationError(f"The value to infrastructure key '{key}' must be a boolean. Actually is '{type(value)}'.")