# Módulo de Relatórios e Dossiês (Data Storytelling)

## 1. Visão Geral

O módulo de Relatórios e Dossiês implementa a geração assíncrona de PDFs bem diagramados — **dossiês** — que contam a "história" de um território (município ou estado) com gráficos, tabelas e textos dinâmicos.

### Principais Funcionalidades

- **Dossiê do Município** (`GET /api/v1/municipios/{municipio_id}/dossie`)
- **Dossiê do Estado** (`GET /api/v1/estados/{sg_uf}/dossie`)
- Geração **100% em memória RAM** — sem escrita em disco
- Stream direto na resposta HTTP (`Content-Disposition: attachment`)
- Gráficos embutidos (matplotlib) com identidade visual ODIN
- Capa personalizada com branding LEMA/UFPB
- Indicadores com código de cores (verde/amarelo/vermelho)

### Por que Stream em Memória?

```
Usuário clica → Backend busca dados no MongoDB
         → Gera gráficos com matplotlib
         → Renderiza PDF com ReportLab
         → Stream direto na resposta HTTP
         → Navegador inicia download automático
```

**Vantagens para o Render (gratuito):**
- Sem necessidade de armazenamento em nuvem (S3, etc.)
- Sem arquivos temporários em disco
- Latência aceitável para relatórios municipais (poucos segundos)
- Escalabilidade horizontal: cada requisição é independente

**Limitação:** Para muitos usuários simultâneos, a RAM pode ser um gargalo. Nesse cenário, uma fila (Redis + Celery) seria o próximo passo.

---

## 2. Estrutura do Módulo

```
src/
├── domain/
│   └── entities/
│       └── report.py                    → Entidades: ReportType, ReportMetadata,
│                                           MunicipioDossierData, StateDossierData
├── application/
│   └── report/                          → (reservado para use cases futuros)
│       └── __init__.py
├── infrastructure/
│   └── report/
│       ├── __init__.py
│       ├── chart_generator.py           → Geração de gráficos (matplotlib)
│       ├── pdf_generator.py             → Renderização do PDF (ReportLab)
│       ├── report_data_service.py       → Consultas ao MongoDB
│       └── dossier_builder.py           → Orquestrador do pipeline completo
└── presentation/
    └── http/
        └── controller/
            └── report/
                ├── __init__.py
                ├── index.py             → Agrega as rotas
                ├── container.py         → DI container
                ├── callable/
                │   ├── __init__.py
                │   └── report_callable.py  → Provider functions
                └── report_controller.py → Rotas HTTP
```

---

## 3. Arquitetura

### 3.1 Fluxo de Requisição

```
HTTP Request
    │
    ▼
Controller (report_controller.py)
    │
    ▼
DossierBuilder (dossier_builder.py)
    │
    ├──► ReportDataService (report_data_service.py)
    │       ├── get_municipio_dossier_data()
    │       └── get_state_dossier_data()
    │
    ├──► ChartGenerator (chart_generator.py)
    │       ├── generate_bar_chart()
    │       ├── generate_horizontal_bar_chart()
    │       ├── generate_pie_chart()
    │       └── generate_grouped_bar_chart()
    │
    └──► DossierPDF (pdf_generator.py)
            └── render() → BytesIO
                │
                ▼
    StreamingResponse (application/pdf)
```

### 3.2 Modelos de Dados

**MunicipioDossierData:**
| Campo | Tipo | Descrição |
|---|---|---|
| `municipio_id` | str | Código IBGE 7 dígitos |
| `municipio_nome` | str | Nome do município |
| `uf` | str | Sigla da UF |
| `total_escolas` | int | Total de escolas |
| `total_alunos` | int | Total de matrículas |
| `total_bairros` | int | Total de bairros |
| `taxa_aprovacao_media` | float? | Média de aprovação |
| `taxa_reprovacao_media` | float? | Média de reprovação |
| `ideb_medio` | float? | IDEB médio (anos iniciais + finais) |
| `pct_internet` | float? | % escolas com internet |
| `pct_biblioteca` | float? | % escolas com biblioteca |
| `pct_lab_informatica` | float? | % escolas com lab. informática |
| `pct_lab_ciencias` | float? | % escolas com lab. ciências |
| `pct_quadra` | float? | % escolas com quadra |
| `pct_acessibilidade` | float? | % escolas com acessibilidade |
| `pct_agua_potavel` | float? | % escolas com água potável |
| `escolas_por_dependencia` | dict | Contagem por dependência adm. |
| `escolas_por_zona` | dict | Contagem por zona (urbana/rural) |
| `matriculas_por_etapa` | dict | Matrículas por etapa de ensino |
| `populacao_total` | int? | População do município |
| `idhm` | float? | IDHM |
| `top_escolas` | list[dict] | Top 5 escolas por IDEB |

**StateDossierData:**
| Campo | Tipo | Descrição |
|---|---|---|
| `uf` | str | Sigla da UF |
| `estado_nome` | str | Nome completo do estado |
| `total_municipios` | int | Total de municípios com dados |
| `total_escolas` | int | Total de escolas |
| `total_alunos` | int | Total de matrículas |
| `ideb_medio` | float? | IDEB médio estadual |
| `escolas_por_dependencia` | dict | Contagem por dependência adm. |
| `escolas_por_zona` | dict | Contagem por zona |
| `top_municipios` | list[dict] | Top 10 municípios por IDEB |

### 3.3 Geração de Gráficos

O módulo `chart_generator.py` usa **matplotlib** com backend não interativo (`Agg`):

```python
from src.infrastructure.report.chart_generator import (
    generate_bar_chart,
    generate_pie_chart,
    generate_horizontal_bar_chart,
    generate_grouped_bar_chart,
)

# Exemplo: barras verticais
chart_bytes = generate_bar_chart(
    labels=["Internet", "Biblioteca", "Lab."],
    values=[85.3, 62.1, 45.7],
    title="Infraestrutura Escolar",
    ylabel="Percentual (%)",
)
```

Paleta de cores ODIN:
- Azul escuro: `#1A5276`
- Verde: `#27AE60`
- Laranja: `#E67E22`
- Vermelho: `#C0392B`
- Roxo: `#8E44AD`
- Verde-água: `#16A085`

### 3.4 Geração de PDF

O módulo `pdf_generator.py` usa **ReportLab** com:

- **Capa:** Fundo azul escuro com detalhes em verde e laranja
- **Cabeçalho/rodapé:** Marca d'água ODIN + numeração de páginas
- **Seções:** Resumo Executivo, Indicadores Educacionais, Infraestrutura, Distribuição, Top Escolas, Contexto Socioeconômico
- **Tabelas:** Estilo alternado (zebrado) com cabeçalho azul
- **Indicadores:** Cards de KPI na página de resumo
- **Barras de progresso:** Código de cores (verde ≥ 70%, laranja ≥ 40%, vermelho < 40%)

---

## 4. Rotas da API

### 4.1 `GET /api/v1/municipios/{municipio_id}/dossie`

Gera o dossiê completo de um município.

| Parâmetro | Tipo | Validação | Descrição |
|---|---|---|---|
| `municipio_id` | path, str | `^\d{7}$` | Código IBGE de 7 dígitos |

**Resposta:** `application/pdf` com `Content-Disposition: attachment`

**Exemplo:**
```bash
curl -o dossie_campina_grande.pdf \
  http://localhost:8000/api/v1/municipios/2504009/dossie
```

### 4.2 `GET /api/v1/estados/{sg_uf}/dossie`

Gera o dossiê completo de um estado.

| Parâmetro | Tipo | Validação | Descrição |
|---|---|---|---|
| `sg_uf` | path, str | `^[A-Za-z]{2}$` | Sigla da UF (ex: PB, PE) |

**Resposta:** `application/pdf` com `Content-Disposition: attachment`

**Exemplo:**
```bash
curl -o dossie_paraiba.pdf \
  http://localhost:8000/api/v1/estados/PB/dossie
```

### 4.3 `GET /api/v1/relatorios/municipios/{municipio_id}/dossie`

Alias do endpoint anterior, sob o prefixo `/relatorios` para descoberta semântica.

---

## 5. Performance e Memória

### Estimativa de Consumo

| Operação | RAM Estimada | Tempo Estimado |
|---|---|---|
| Dossiê Município (pequeno) | ~50-80 MB | 2-5 segundos |
| Dossiê Município (grande) | ~80-120 MB | 5-10 segundos |
| Dossiê Estado (PB) | ~100-150 MB | 8-15 segundos |

> **Nota:** No Render Free, o plano tem 512 MB de RAM. Para cargas moderadas (1-5 requisições simultâneas), é suficiente. Para produção com múltiplos usuários, considere upgrade de plano ou fila assíncrona.

### Otimizações Implementadas

- **Matplotlib `Agg` backend:** Não usa GUI, apenas renderização em memória
- **BytesIO:** Todo processamento é em memória, sem I/O de disco
- **Pipeline único de agregação:** Uma única query MongoDB agrega todos os indicadores
- **Gráficos sob demanda:** Só são gerados se houver dados para exibir
- **Garbage collection:** matplotlib `plt.close(fig)` libera memória imediatamente

---

## 6. Configuração

### Dependências Adicionais

```toml
# pyproject.toml
reportlab==5.0.0       # Geração de PDF
matplotlib==3.11.0      # Geração de gráficos
```

### Variáveis de Ambiente

Nenhuma variável nova necessária. O módulo reusa as conexões MongoDB existentes.

---

## 7. Próximos Passos (Melhorias Futuras)

1. **Cache de relatórios:** Armazenar PDFs gerados no MongoDB (GridFS) para evitar regeneração
2. **Fila assíncrona:** Usar Redis + background tasks para relatórios estaduais pesados
3. **Mais tipos de relatório:** Dossiê de bairro, dossiê de escola individual
4. **Template customizável:** Permitir que o usuário escolha seções via query params
5. **Multilíngue:** Suporte a inglês/espanhol para relatórios internacionais
6. **Comparativo histórica:** Linha do tempo com dados de múltiplos anos