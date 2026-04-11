from typing import Dict
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field, model_validator
from ..enums.enum_dependencia_administrativa import DependenciaAdministrativa
from ..enums.enum_uf import UF
from ..enums.enum_tipo_localizacao import TipoLocalizacao
from ..validators.school_validation import (
    SchoolValidator,
)
from src.domain.value_objects.location import Location
from src.domain.value_objects.indicators import Indicadores


class School(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, 
        arbitrary_types_allowed=True
    )

    id: str = Field(default_factory=lambda: str(uuid4()))
    municipio_id_ibge: str
    escola_id_inep: int
    escola_nome: str
    municipio_nome: str
    estado_sigla: UF
    dependencia_adm: DependenciaAdministrativa
    tipo_localizacao: TipoLocalizacao
    localizacao: Location
    indicadores: Indicadores = Field(default_factory=Indicadores)
    infraestrutura: Dict[str, bool] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_domain(self):
        SchoolValidator(
            municipio_id_ibge=self.municipio_id_ibge,
            escola_id_inep=self.escola_id_inep,
            escola_nome=self.escola_nome,
            municipio_nome=self.municipio_nome,
            estado_sigla=self.estado_sigla,
            dependencia_adm=self.dependencia_adm,
            tipo_localizacao=self.tipo_localizacao,
            localizacao=self.localizacao,
            indicadores=self.indicadores,
            infraestrutura=self.infraestrutura,
        )
        return self