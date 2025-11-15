from typing import Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, ConfigDict
from ..enums.enum_dependencia_administrativa import DependenciaAdministrativa
from ..enums.enum_uf import UF
from ..enums.enum_tipo_localizacao import TipoLocalizacao
from ..validators.school_validation import (
    SchoolValidator,
    DomainValidationError,
)
from src.domain.value_objects.location import Location
from src.domain.value_objects.indicators import Indicadores


class School(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, 
        arbitrary_types_allowed=True
    )

    id: str 
    municipio_id_ibge: str
    escola_id_inep: int
    escola_nome: str
    municipio_nome: str
    estado_sigla: UF
    dependencia_adm: DependenciaAdministrativa
    tipo_localizacao: TipoLocalizacao
    localizacao: Location
    indicadores: Indicadores
    infraestrutura: Dict[str, bool]

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
        indicadores: Optional[Indicadores] = None,
        infraestrutura: Optional[Dict[str, bool]] = None,
        id: Optional[str] = None,
        **data: Any
    ):
        try:
            self._validator = SchoolValidator(
                municipio_id_ibge=municipio_id_ibge,
                escola_id_inep=escola_id_inep,
                escola_nome=escola_nome,
                municipio_nome=municipio_nome,
                estado_sigla=estado_sigla,
                dependencia_adm=dependencia_adm,
                tipo_localizacao=tipo_localizacao,
                localizacao=localizacao,
                indicadores=indicadores,
            )
        except DomainValidationError as e:
            raise e

        self._id = id or str(uuid4())
        self._municipio_id_ibge = municipio_id_ibge
        self._escola_id_inep = escola_id_inep
        self._escola_nome = escola_nome
        self._municipio_nome = municipio_nome
        self._estado_sigla = estado_sigla
        self._dependencia_adm = dependencia_adm
        self._tipo_localizacao = tipo_localizacao
        self._localizacao = localizacao
        self._indicadores = indicadores or Indicadores()
        self._infraestrutura = infraestrutura or {}
        super().__init__(
            id=self._id,
            municipio_id_ibge=self._municipio_id_ibge,
            escola_id_inep=self._escola_id_inep,
            escola_nome=self._escola_nome,
            municipio_nome=self._municipio_nome,
            estado_sigla=self._estado_sigla,
            dependencia_adm=self._dependencia_adm,
            tipo_localizacao=self._tipo_localizacao,
            localizacao=self._localizacao,
            indicadores=self._indicadores,
            infraestrutura=self._infraestrutura,
            **data
        )

    @property
    def id(self) -> str:
        return self._id

    @property
    def municipio_id_ibge(self) -> str:
        return self._municipio_id_ibge

    @property
    def escola_id_inep(self) -> int:
        return self._escola_id_inep

    @property
    def escola_nome(self) -> str:
        return self._escola_nome
    
    @property
    def municipio_nome(self) -> str:
        return self._municipio_nome

    @property
    def estado_sigla(self) -> UF:
        return self._estado_sigla
    
    @property
    def dependencia_adm(self) -> DependenciaAdministrativa:
        return self._dependencia_adm

    @property
    def tipo_localizacao(self) -> TipoLocalizacao:
        return self._tipo_localizacao

    @property
    def localizacao(self) -> Location:
        return self._localizacao

    @property
    def indicadores(self) -> Indicadores:
        return self._indicadores

    @property
    def infraestrutura(self) -> Dict[str, bool]:
        return self._infraestrutura.copy()