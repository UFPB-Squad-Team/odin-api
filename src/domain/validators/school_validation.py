from typing import Optional
from src.domain.exeptions.validation_error import DomainValidationError
from ..value_objects.location import Location
from ..value_objects.indicators import Indicadores
from ..value_objects.infraestrutura import Infraestrutura
from ..value_objects.endereco import Endereco
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
        endereco: Endereco,
        indicadores: Optional[Indicadores],
        infraestrutura: Optional[Infraestrutura] = None,
    ):
        self._municipio_id_ibge = municipio_id_ibge
        self._escola_id_inep = escola_id_inep
        self._escola_nome = escola_nome
        self._municipio_nome = municipio_nome
        self._estado_sigla = estado_sigla
        self._dependencia_adm = dependencia_adm
        self._tipo_localizacao = tipo_localizacao
        self._localizacao = localizacao
        self._endereco = endereco
        self._indicadores = indicadores
        self._infraestrutura = infraestrutura

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
        self._validate_endereco()
        self._validate_indicadores()
        self._validate_infraestrutura()

    def _validate_ibge(self):
        """Validates the 7-digit IBGE municipality code."""
        if (
            not self._municipio_id_ibge
            or len(self._municipio_id_ibge) != 7
            or not self._municipio_id_ibge.isdigit()
        ):
            raise DomainValidationError("municipio_id_ibge must be 7 digits.")

    def _validate_inep(self):
        """Validates the 8-digit INEP school code."""
        if not (10000000 <= self._escola_id_inep <= 99999999):
            raise DomainValidationError(
                f"escola_id_inep is invalid, must be 8 digits: {self._escola_id_inep}."
            )

    def _validate_nome(self):
        """Validates the school name."""
        if not self._escola_nome or len(self._escola_nome.strip()) == 0:
            raise DomainValidationError("escola_nome is required.")
        if len(self._escola_nome) > 255:
            raise DomainValidationError("escola_nome must not exceed 255 characters.")

    def _validate_municipio_nome(self):
        """Validates the municipality name."""
        if not self._municipio_nome or len(self._municipio_nome.strip()) == 0:
            raise DomainValidationError("municipio_nome is required.")

    def _validate_location(self):
        """Validates the Location dataclass."""
        if self._localizacao is None:
            raise DomainValidationError("localizacao is required.")
        if self._localizacao.type != "Point":
            raise DomainValidationError("localizacao.type must be 'Point'.")

        if len(self._localizacao.coordinates) != 2:
            raise DomainValidationError(
                "localizacao.coordinates must contain [longitude, latitude]."
            )

        lon, lat = self._localizacao.coordinates
        if not (-180.0 <= lon <= 180.0):
            raise DomainValidationError(
                f"Invalid longitude: {lon}. Must be between -180 and 180."
            )
        if not (-90.0 <= lat <= 90.0):
            raise DomainValidationError(
                f"Invalid latitude: {lat}. Must be between -90 and 90."
            )

    def _validate_indicadores(self):
        """Validates the updated Indicadores structure with education stages."""
        if not self._indicadores:
            return

        if self._indicadores.totalAlunos < 0:
            raise DomainValidationError("indicadores.totalAlunos cannot be negative.")

        if self._indicadores.anoReferencia < 1900:
            raise DomainValidationError("indicadores.anoReferencia is invalid.")

        etapas = [
            ("Educação Infantil", self._indicadores.educacaoInfantil),
            ("Anos Iniciais", self._indicadores.fundamentalAnosIniciais),
            ("Anos Finais", self._indicadores.fundamentalAnosFinais),
            ("Ensino Médio", self._indicadores.ensinoMedio),
        ]

        for nome_etapa, dados in etapas:
            self._validar_metricas_etapa(nome_etapa, dados)

    def _validar_metricas_etapa(self, nome: str, dados):
        """Helper para validar as taxas e médias de cada etapa de ensino."""
        if dados.alunosPorTurma < 0:
            raise DomainValidationError(f"indicadores.{nome}: alunosPorTurma cannot be negative.")
        
        taxas = [
            ("taxaAprovacao", dados.taxaAprovacao),
            ("taxaReprovacao", dados.taxaReprovacao),
            ("tnr", dados.tnr)
        ]

        for campo, valor in taxas:
            if not (0 <= valor <= 100):
                raise DomainValidationError(
                    f"indicadores.{nome}: {campo} must be between 0 and 100. Received: {valor}"
                )
        
        if dados.horasAulaDiarias < 0:
             raise DomainValidationError(f"indicadores.{nome}: horasAulaDiarias cannot be negative.")

    def _validate_endereco(self):
        if self._endereco is None:
            raise DomainValidationError("endereco is required.")

    def _validate_infraestrutura(self):
        if self._infraestrutura and self._infraestrutura.salas.utilizadas < 0:
            raise DomainValidationError(
                "infraestrutura.salas.utilizadas cannot be negative."
            )
