from src.domain.exeptions.validation_error import DomainValidationError


class NeighborhoodValidator:
    def __init__(self, municipio_id_ibge: str):
        self._municipio_id_ibge = municipio_id_ibge
        self._validate()

    def _validate(self) -> None:
        if (
            not self._municipio_id_ibge
            or len(self._municipio_id_ibge) != 7
            or not self._municipio_id_ibge.isdigit()
        ):
            raise DomainValidationError("municipio_id_ibge must be 7 digits.")