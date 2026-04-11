from pydantic import BaseModel, Field


class InfraestruturaEquipamentos(BaseModel):
    computadorPortatilAluno: bool = False
    desktopAluno: bool = False
    impressora: bool = False
    lousaDigital: bool = False
    multimidia: bool = False
    tabletAluno: bool = False


class InfraestruturaInternet(BaseModel):
    internetAdministrativa: bool = False
    internetParaAlunos: bool = False
    possuiInternet: bool = False


class InfraestruturaSalas(BaseModel):
    acessiveis: int = 0
    climatizadas: int = 0
    utilizadas: int = 0


class Infraestrutura(BaseModel):
    possuiAcessibilidadePcd: bool = False
    possuiAguaPotavel: bool = False
    possuiBiblioteca: bool = False
    possuiColetaLixo: bool = False
    possuiCozinha: bool = False
    possuiEnergiaPublica: bool = False
    possuiEsgotoRedePublica: bool = False
    possuiLaboratorioCiencias: bool = False
    possuiLaboratorioInformatica: bool = False
    possuiPatioCoberto: bool = False
    possuiPatioDescoberto: bool = False
    possuiPiscina: bool = False
    possuiQuadraEsportes: bool = False
    possuiRefeitorio: bool = False
    equipamentos: InfraestruturaEquipamentos = Field(
        default_factory=InfraestruturaEquipamentos
    )
    internet: InfraestruturaInternet = Field(default_factory=InfraestruturaInternet)
    salas: InfraestruturaSalas = Field(default_factory=InfraestruturaSalas)
