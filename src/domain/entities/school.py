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
from src.domain.value_objects.infraestrutura import Infraestrutura
from src.domain.value_objects.endereco import Endereco


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
    endereco: Endereco = Field(default_factory=Endereco)
    indicadores: Indicadores = Field(default_factory=Indicadores)
    infraestrutura: Infraestrutura = Field(default_factory=Infraestrutura)

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
            endereco=self.endereco,
            indicadores=self.indicadores,
            infraestrutura=self.infraestrutura,
        )
        return self