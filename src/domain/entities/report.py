from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ReportType(str, Enum):
    """Tipos de relatório disponíveis no sistema."""

    MUNICIPIO_DOSSIER = "municipio_dossier"
    STATE_DOSSIER = "state_dossier"
    SCHOOL_DOSSIER = "school_dossier"


class ReportStatus(str, Enum):
    """Status do processo de geração do relatório."""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportMetadata(BaseModel):
    """Metadados do relatório gerado."""

    report_type: ReportType
    title: str
    subtitle: str | None = None
    generated_at: datetime = Field(default_factory=datetime.now)
    entity_id: str
    entity_name: str
    uf: str | None = None
    total_pages: int | None = None
    file_size_bytes: int | None = None


class DossierSection(BaseModel):
    """Representa uma seção do dossiê com título e conteúdo."""

    title: str
    content: str
    order: int = 0
    has_chart: bool = False
    chart_type: str | None = None  # bar, pie, line


class MunicipioDossierData(BaseModel):
    """Dados completos para geração do dossiê de um município.

    Os indicadores educacionais por etapa (Anos Iniciais, Anos Finais,
    Ensino Médio) são agrupados em dicionários chaveados pelo nome da
    etapa, espelhando a granularidade real disponível na coleção
    `municipio_indicadores` sem exigir um campo Pydantic por combinação
    de indicador x etapa. Isso também permite ao PDF renderizar tabelas
    e gráficos comparativos genericamente.
    """

    municipio_id: str
    municipio_nome: str
    uf: str

    # Totais
    total_escolas: int = 0
    total_alunos: int = 0
    total_bairros: int = 0
    populacao_total: int | None = None

    # Desempenho educacional, por etapa: "Anos Iniciais" | "Anos Finais" | "Ensino Médio"
    ideb_por_etapa: dict[str, float] = Field(default_factory=dict)
    aprovacao_por_etapa: dict[str, float] = Field(default_factory=dict)
    abandono_por_etapa: dict[str, float] = Field(default_factory=dict)
    distorcao_idade_serie_por_etapa: dict[str, float] = Field(default_factory=dict)

    # Corpo docente e condições de ensino, por etapa
    adequacao_docente_por_etapa: dict[str, float] = Field(default_factory=dict)
    docentes_superior_por_etapa: dict[str, float] = Field(default_factory=dict)
    horas_aula_por_etapa: dict[str, float] = Field(default_factory=dict)
    alunos_por_turma_etapa: dict[str, float] = Field(default_factory=dict)

    # Infraestrutura escolar: {"Internet": 100.0, "Biblioteca": 28.6, ...}
    infraestrutura: dict[str, float] = Field(default_factory=dict)

    # Distribuição das escolas (depende da coleção `escolas`; pode vir vazio)
    escolas_por_dependencia: dict[str, int] = Field(default_factory=dict)
    escolas_por_zona: dict[str, int] = Field(default_factory=dict)
    matriculas_por_etapa: dict[str, int] = Field(default_factory=dict)
    top_escolas: list[dict] = Field(default_factory=list)

    # Demografia
    estrutura_etaria: dict[str, float] = Field(default_factory=dict)
    raca: dict[str, float] = Field(default_factory=dict)
    genero: dict[str, float] = Field(default_factory=dict)
    razao_dependencia: float | None = None

    # Saneamento e moradia
    saneamento: dict[str, float] = Field(default_factory=dict)
    habitacao: dict[str, float] = Field(default_factory=dict)
    total_domicilios: int | None = None
    media_moradores_domicilio: float | None = None

    # Outros indicadores socioeconômicos
    taxa_analfabetismo: float | None = None
    pct_responsavel_feminino: float | None = None
    obitos_domicilios: int | None = None
    obitos_infantis_0a4: int | None = None

    # Transparência / rastreabilidade dos dados
    ano_referencia_socioeconomico: int | None = None
    fonte_socioeconomico: str | None = None
    indicadores_indisponiveis: list[str] = Field(default_factory=list)

    class Config:
        frozen = False


class StateDossierData(BaseModel):
    """Dados completos para geração do dossiê de um estado.

    Os indicadores educacionais por etapa seguem a mesma convenção de
    dicionário usada em MunicipioDossierData (médias calculadas entre
    os municípios do estado com dado disponível para cada indicador).
    """

    uf: str
    estado_nome: str
    total_municipios: int
    total_escolas: int = 0
    total_alunos: int = 0
    populacao_total: int | None = None

    ideb_por_etapa: dict[str, float] = Field(default_factory=dict)
    aprovacao_por_etapa: dict[str, float] = Field(default_factory=dict)
    abandono_por_etapa: dict[str, float] = Field(default_factory=dict)

    infraestrutura: dict[str, float] = Field(default_factory=dict)

    taxa_aprovacao_media: float | None = None
    taxa_reprovacao_media: float | None = None
    ideb_medio: float | None = None
    pct_internet: float | None = None
    pct_biblioteca: float | None = None
    pct_lab_informatica: float | None = None
    pct_acessibilidade: float | None = None

    escolas_por_dependencia: dict[str, int] = Field(default_factory=dict)
    escolas_por_zona: dict[str, int] = Field(default_factory=dict)

    top_municipios: list[dict] = Field(default_factory=list)
    indicadores_indisponiveis: list[str] = Field(default_factory=list)

    class Config:
        frozen = False
