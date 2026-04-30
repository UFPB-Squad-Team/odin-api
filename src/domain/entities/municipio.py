from pydantic import BaseModel, ConfigDict, Field


class MunicipioCatalogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="IBGE municipality code as a 7-digit string")
    nome: str = Field(..., description="Municipality name")
    sg_uf: str | None = Field(default=None, description="State code")


class EducacaoStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    totalEscolas: int | None = None
    totalMatriculas: int | None = None
    totalBairros: int | None = None
    pctComBiblioteca: float | int | None = None
    pctComInternet: float | int | None = None
    pctComLabInformatica: float | int | None = None
    pctSemAcessibilidade: float | int | None = None
    mediaIdebAnosIniciais: float | None = None
    mediaIdebAnosFinals: float | None = None


class SocioeconomicoPopulacao(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total: int | None = None
    totalDomiciliosParticulares: int | None = None
    mediaMoradoresPorDomicilio: float | int | None = None


class SocioeconomicoEstruturaEtaria(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pctCriancas0a9: float | int | None = None
    pctIdosos60Mais: float | int | None = None
    razaoDependencia: float | int | None = None


class SocioeconomicoRaca(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pctPretaParda: float | int | None = None


class SocioeconomicoSaneamento(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pctAguaRedeGeral: float | int | None = None
    pctAguaInadequada: float | int | None = None
    pctEsgotoRedeGeral: float | int | None = None
    pctEsgotoInadequado: float | int | None = None
    pctLixoColetado: float | int | None = None
    pctLixoInadequado: float | int | None = None


class SocioeconomicoEducacaoPopulacao(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    taxaAnalfabetismo15Mais: float | int | None = None


class SocioeconomicoFamilia(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pctResponsavelFeminino: float | int | None = None


class SocioeconomicoMortalidade(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    totalObitosDomicilios: float | int | None = None
    obitosInfantis0a4: float | int | None = None


class SocioeconomicoHabitacao(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pctDomImprovisado: float | int | None = None
    pctDomSuperlotado: float | int | None = None


class SocioeconomicoStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    anoReferencia: int | None = None
    fonte: str | None = None
    populacao: SocioeconomicoPopulacao | None = None
    estruturaEtaria: SocioeconomicoEstruturaEtaria | None = None
    raca: SocioeconomicoRaca | None = None
    saneamento: SocioeconomicoSaneamento | None = None
    educacaoPopulacao: SocioeconomicoEducacaoPopulacao | None = None
    familia: SocioeconomicoFamilia | None = None
    mortalidade: SocioeconomicoMortalidade | None = None
    habitacao: SocioeconomicoHabitacao | None = None


class MunicipioResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    municipioIdIbge: str = Field(..., description="IBGE municipality code as a 7-digit string")
    municipio: str = Field(default="", description="Municipality name")
    sg_uf: str | None = Field(default=None, description="State code")
    total_bairros: int = 0
    tem_bairros_oficiais: bool = False
    educacao: EducacaoStats = Field(default_factory=EducacaoStats)
    socioeconomico: SocioeconomicoStats = Field(default_factory=SocioeconomicoStats)
    source: str = Field(
        default="municipio_indicadores",
        description="Data source used to build this summary",
    )

    @property
    def total_escolas(self) -> int:
        return int(self.educacao.totalEscolas or 0)

    @property
    def total_matriculas(self) -> int:
        return int(self.educacao.totalMatriculas or 0)

    @property
    def total_alunos(self) -> int:
        return int(self.educacao.totalMatriculas or 0)

    @property
    def pct_com_biblioteca(self) -> float | None:
        return self.educacao.pctComBiblioteca

    @property
    def pct_com_internet(self) -> float | None:
        return self.educacao.pctComInternet

    @property
    def pct_com_lab_informatica(self) -> float | None:
        return self.educacao.pctComLabInformatica

    @property
    def pct_sem_acessibilidade(self) -> float | None:
        return self.educacao.pctSemAcessibilidade

    @property
    def mediaIdebAnosIniciais(self) -> float | None:
        return self.educacao.mediaIdebAnosIniciais

    @property
    def mediaIdebAnosFinals(self) -> float | None:
        return self.educacao.mediaIdebAnosFinals
