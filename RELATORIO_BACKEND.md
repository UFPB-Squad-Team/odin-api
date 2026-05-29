# Relatório Completo — Backend ODIN API

**Data de geração:** 28 de maio de 2026  
**Versão do projeto:** 0.1.0

---

## 1. Resumo Executivo

### Stack Tecnológica

| Componente | Tecnologia | Versão |
|---|---|---|
| Linguagem | Python | ^3.12 |
| Framework Web | FastAPI | ^0.104.1 |
| Servidor ASGI | Uvicorn | ^0.24.0 |
| Banco de Dados | MongoDB (Atlas) | — |
| Driver Async | Motor | ^3.3.2 |
| Driver Sync | PyMongo | ^4.6.0 |
| Validação/Schemas | Pydantic | ^2.5.0 |
| Injeção de Dependência | dependency-injector | ^4.41.0 |
| Gerenciador de Deps | Poetry | — |
| Variáveis de Ambiente | python-dotenv | ^1.0.0 |

### Estado Geral

O **ODIN (Observatório de Dados Integrados do Nordeste)** é uma API REST que expõe dados educacionais e socioeconômicos processados por um ETL.
O foco atual é o estado da Paraíba (PB), com dados de escolas, municípios, bairros e setores censitários. A API está **funcional e operacional**, com 12+ endpoints implementados cobrindo listagem paginada, busca universal, agregações territoriais e GeoJSON para mapas.

**Projeto construído por:** LEMA/UFPB  
**Objetivo:** Fortalecer infraestrutura de dados abertos e de qualidade para o Nordeste do Brasil.

---

## 2. Arquitetura da API

### 2.1 Padrão Arquitetural

Clean Architecture com 4 camadas bem definidas:

```
src/
├── domain/              → Núcleo de negócio (entidades, enums, value objects, validadores, contratos)
├── application/         → Casos de uso (orquestração fina, sem regras de framework)
├── infrastructure/      → Implementações concretas (MongoDB, mappers, config)
└── presentation/        → Camada HTTP (controllers, middleware, schemas, query parsing)
```

### 2.2 Estrutura de Pastas Detalhada

```
src/
├── main.py                          → Bootstrap da aplicação FastAPI
├── server.py                        → Runner Uvicorn
├── domain/
│   ├── entities/
│   │   ├── school.py                → Entidade School (principal)
│   │   ├── municipio.py             → MunicipioResumo, MunicipioCatalogItem, EducacaoStats, SocioeconomicoStats
│   │   ├── bairro.py                → BairroResumo, BairroEducacaoStats
│   │   ├── state_summary.py         → StateSummary, EducacaoStateStats, SocioeconomicoStateStats
│   │   ├── city_aggregation.py      → CityAggregation, CityEducacao, CitySocioeconomico
│   │   ├── territorial_summary.py   → CitySummary, NeighborhoodSummary
│   │   └── stats.py                 → SummaryStats
│   ├── enums/
│   │   ├── enum_uf.py               → UF (estados do Nordeste)
│   │   ├── enum_dependencia_administrativa.py → Federal/Estadual/Municipal/Privada
│   │   └── enum_tipo_localizacao.py → Urbana/Rural
│   ├── value_objects/
│   │   ├── location.py              → Location (GeoJSON Point)
│   │   ├── endereco.py              → Endereco
│   │   ├── indicators.py            → Indicadores, Matriculas, DetalheEtapaEnsino
│   │   ├── infraestrutura.py        → Infraestrutura (equipamentos, internet, salas)
│   │   ├── pagination.py            → PaginatedResponse[T]
│   │   └── query.py                 → QueryOptions, QueryFilter, QuerySort, CursorPage
│   ├── validators/
│   │   ├── school_validation.py     → SchoolValidator (validação completa de domínio)
│   │   └── neighborhood_validation.py → NeighborhoodValidator
│   ├── factories/
│   │   └── state_summary_factory.py → StateSummaryFactory (agregação estadual)
│   ├── repository/                  → Interfaces abstratas (ABC)
│   │   ├── base_repository.py       → IBaseReadRepository[T]
│   │   ├── school_repository.py     → ISchoolRepository
│   │   ├── municipio_repository.py  → IMunicipioRepository
│   │   ├── bairro_repository.py     → IBairroRepository
│   │   ├── state_repository.py      → IStateRepository
│   │   ├── stats_repository.py      → IStatsRepository
│   │   ├── territorial_aggregation_repository.py → ITerritorialAggregationRepository
│   │   └── universal_search_repository.py → IUniversalSearchRepository
│   └── exeptions/
│       └── validation_error.py      → DomainValidationError
├── application/
│   ├── common/
│   │   └── base_list_use_case.py    → BaseListUseCase[T] genérico
│   ├── school/
│   │   ├── list_all_schools/        → ListAllSchools + DTO
│   │   ├── get_school_by_id/        → GetSchoolById + DTO
│   │   └── geojson/                 → GetParaibaGeoJson, GetBairrosGeoJson, GetBairroBySchoolId
│   ├── municipio/
│   │   ├── list_municipios/         → ListMunicipios + DTO
│   │   └── get_municipio_resumo/    → GetMunicipioResumo + DTO
│   ├── bairro/
│   │   └── get_bairro_resumo/       → GetBairroResumo + DTO
│   ├── aggregation/
│   │   ├── get_city_aggregations.py
│   │   └── get_neighborhood_aggregations.py
│   ├── search/
│   │   └── universal_search/        → UniversalSearchUseCase + DTOs
│   ├── state/
│   │   └── get_state_summary/       → GetStateSummaryUseCase
│   └── stats/
│       └── get_summary_stats_use_case.py
├── infrastructure/
│   └── database/
│       ├── config/
│       │   ├── app_config.py        → AppConfig (dataclass com env vars)
│       │   └── connect_db.py        → MongoDB singleton + índices
│       ├── mapper/
│       │   ├── school_mapper.py     → MongoSchoolMapper
│       │   ├── territorial_aggregation_mapper.py → TerritorialAggregationMapper
│       │   ├── mongo_neighborhood_mapper.py → MongoNeighborhoodMapper
│       │   └── state_summary_mapper.py → StateSummaryMapper
│       └── repository/
│           ├── base_mongo_repository.py → BaseMongoRepository[T] (genérico)
│           ├── pagination.py        → fetch_paginated_documents (helper)
│           ├── mongo_school_repository.py
│           ├── mongo_municipio_repository.py
│           ├── mongo_bairro_repository.py
│           ├── mongo_territorial_aggregation_repository.py
│           ├── mongo_state_repository.py
│           ├── mongo_stats_repository.py
│           └── mongo_universal_search_repository.py
└── presentation/
    └── http/
        ├── middleware/
        │   └── global_exception_handler.py
        ├── query/
        │   └── query_param_parser.py → QueryParamParser (filtros via query string)
        ├── schemas/
        │   ├── school_search_schema.py
        │   ├── paginated_response.py
        │   ├── geojson_schema.py
        │   └── aggregation_schema.py
        └── controller/
            ├── school/              → list, get_by_id, geojson, stats
            ├── municipio/           → list, resumo
            ├── bairro/              → resumo
            ├── aggregation/         → cities, neighborhoods
            ├── search/              → universal search
            └── state/               → resumo estadual
```

### 2.3 Padrões de Design Utilizados

| Padrão | Onde |
|---|---|
| Repository Pattern | Interfaces em `domain/repository/`, implementações em `infrastructure/` |
| Use Case / Interactor | Cada operação em `application/` é um use case fino |
| DTO (Data Transfer Object) | Input/Output DTOs para cada use case |
| Mapper | Conversão documento MongoDB ↔ entidade de domínio |
| Factory | `StateSummaryFactory` para agregação estadual |
| Dependency Injection | Containers `dependency-injector` por módulo |
| Fallback Strategy | Busca primária → agregação de setores censitários |
| Cursor-based Pagination | Base64 encoded cursor para paginação profunda |

---

## 3. Endpoints Implementados

Todos os endpoints estão sob o prefixo **`/api/v1`**.

### 3.1 Escolas (Schools)

#### `GET /api/v1/schools`

| Item | Detalhe |
|---|---|
| **Método** | GET |
| **Rota** | `/api/v1/schools` (alias: `/api/v1/all`) |
| **Descrição** | Listagem paginada de escolas com filtros dinâmicos, ordenação e projeção de campos |
| **Collection** | `escolas` |
| **Parâmetros Query** | `page` (int, default 1), `page_size` (int, default 10, max 100), `search` (busca por nome), `municipio` (filtro por nome de município), `municipio_id` (filtro por código IBGE), `cursor` (paginação cursor-based), `sort` (campo com prefixo `-` para desc), `fields` (projeção CSV), `filter[campo__operador]` (filtros dinâmicos) |
| **Filtros permitidos** | `escola_id_inep`, `escola_nome`, `municipio_nome`, `estado_sigla`, `dependencia_adm`, `tipo_localizacao`, `municipio_id_ibge`, `bairro` |
| **Operadores** | `eq`, `ne`, `in`, `nin`, `gt`, `gte`, `lt`, `lte`, `contains`, `startswith`, `endswith` |
| **Resposta** | `{ schools: School[], total_items: int, page: int, page_size: int, next_cursor: str\|null }` |
| **Proteção** | Offset máximo de 50.000 registros (retorna 422 se exceder) |

#### `GET /api/v1/{escola_id_inep}`

| Item | Detalhe |
|---|---|
| **Método** | GET |
| **Rota** | `/api/v1/{escola_id_inep}` |
| **Descrição** | Retorna uma escola pelo identificador INEP |
| **Collection** | `escolas` |
| **Parâmetros Path** | `escola_id_inep` (string) |
| **Resposta** | Objeto `School` completo |
| **Erro** | 404 se não encontrada |

#### `GET /api/v1/escolas/geojson/paraiba`

| Item | Detalhe |
|---|---|
| **Método** | GET |
| **Rota** | `/api/v1/escolas/geojson/paraiba` |
| **Descrição** | Retorna todas as escolas da Paraíba como GeoJSON FeatureCollection |
| **Collection** | `escolas` |
| **Parâmetros Query** | `municipio_id` (opcional, 7 dígitos — filtra por município) |
| **Resposta** | GeoJSON FeatureCollection com properties: `escola_nome`, `escola_id_inep`, `estado_sigla`, `indicadores`, `matriculas`, `municipio_nome`, `municipioIdIbge`, `bairro`, `dependencia_adm`, `tipo_localizacao`, `ideb` |
| **Cache** | In-memory com TTL de 60s e máximo de 512 chaves |
| **Filtro base** | `estadoSigla: "PB"` + coordenadas válidas |

#### `GET /api/v1/bairros/geojson/{municipio}`

| Item | Detalhe |
|---|---|
| **Método** | GET |
| **Rota** | `/api/v1/bairros/geojson/{municipio}` |
| **Descrição** | Retorna bairros de um município como GeoJSON, agregados a partir das escolas |
| **Collection** | `escolas` |
| **Parâmetros Path** | `municipio` (nome do município) |
| **Resposta** | GeoJSON FeatureCollection com centróide médio por bairro, `qtd_escolas`, `avg_ideb` |
| **Pipeline** | Aggregation: match por municipio + group por `endereco.bairro` |

#### `GET /api/v1/bairro/{school_id}`

| Item | Detalhe |
|---|---|
| **Método** | GET |
| **Rota** | `/api/v1/bairro/{school_id}` |
| **Descrição** | Retorna informação do bairro de uma escola específica |
| **Collection** | `escolas` |
| **Parâmetros Path** | `school_id` (_id Mongo ou escolaIdInep) |
| **Resposta** | `{ id, escola_id_inep, escola_nome, municipio_nome, estado_sigla, bairro }` |
| **Erro** | 404 se escola não encontrada |

### 3.2 Estatísticas

#### `GET /api/v1/school/stats/summary`

| Item | Detalhe |
|---|---|
| **Método** | GET |
| **Rota** | `/api/v1/school/stats/summary` |
| **Descrição** | Retorna estatísticas agregadas de infraestrutura das escolas da Paraíba |
| **Collection** | `escolas` |
| **Parâmetros** | Nenhum |
| **Pipeline** | `$facet` com: totais (internet, biblioteca, informática), por dependência administrativa, por zona (urbana/rural), municípios distintos |
| **Resposta** | `{ total_escolas: int, total_municipios: int, indicadores_infra: { "Internet (%)": float, "Biblioteca (%)": float, "Lab. Informática (%)": float }, por_dependencia: { "Municipal": int, ... }, por_zona: { "Urbana": int, "Rural": int } }` |
| **Filtro base** | `estadoSigla: "PB"` |

---

### 3.3 Municípios

#### `GET /api/v1/municipios`

| Item | Detalhe |
|---|---|
| **Método** | GET |
| **Rota** | `/api/v1/municipios` |
| **Descrição** | Lista municípios para popular seletores e filtros em cascata |
| **Collection** | `municipio_indicadores` |
| **Parâmetros Query** | `sg_uf` (opcional, 2 caracteres — ex: PB) |
| **Resposta** | `[ { id: "2504009", nome: "Campina Grande", sg_uf: "PB" }, ... ]` |
| **Ordenação** | Alfabética (accent-insensitive) |

#### `GET /api/v1/municipios/{municipio_id}/resumo`

| Item | Detalhe |
|---|---|
| **Método** | GET |
| **Rota** | `/api/v1/municipios/{municipio_id}/resumo` |
| **Descrição** | Resumo consolidado do município com indicadores educacionais e socioeconômicos |
| **Collections** | `municipio_indicadores` (primária), `setor_indicadores` (fallback), `bairro_indicadores` (contagem de bairros) |
| **Parâmetros Path** | `municipio_id` (7 dígitos IBGE) |
| **Resposta** | `MunicipioResumo` com: `municipioIdIbge`, `municipio`, `sg_uf`, `total_bairros`, `tem_bairros_oficiais`, `educacao` (30+ indicadores), `socioeconomico` (população, estrutura etária, gênero, raça, saneamento, educação, família, mortalidade, habitação), `source` |
| **Fallback** | Se não encontrar em `municipio_indicadores`, agrega de `setor_indicadores` |
| **Erro** | 404 se município não encontrado |

---

### 3.4 Bairros

#### `GET /api/v1/bairros/{bairro_id}/resumo`

| Item | Detalhe |
|---|---|
| **Método** | GET |
| **Rota** | `/api/v1/bairros/{bairro_id}/resumo` |
| **Descrição** | Resumo de bairro com indicadores educacionais e socioeconômicos |
| **Collections** | `bairro_indicadores` (primária), `setor_indicadores` (fallback via aggregation) |
| **Parâmetros Path** | `bairro_id` (exatamente 10 dígitos: 7 município + 3 bairro) |
| **Resposta** | `BairroResumo` com: `id`, `bairro`, `municipio`, `municipioIdIbge`, `sg_uf`, `tem_bairro_oficial`, `source`, `educacao` (mesmos indicadores do município), `socioeconomico` |
| **Fallback** | Se não encontrar por `cd_bairro_ibge`, agrega setores com `$group` |
| **Erro** | 404 se bairro não encontrado |

---

### 3.5 Agregações Territoriais

#### `GET /api/v1/aggregations/cities`

| Item | Detalhe |
|---|---|
| **Método** | GET |
| **Rota** | `/api/v1/aggregations/cities` |
| **Descrição** | Retorna indicadores agregados por município em formato GeoJSON FeatureCollection |
| **Collections** | `municipio_indicadores` (primária), `setor_indicadores` (fallback) |
| **Parâmetros Query** | `municipioIdIbge` (opcional, 7 dígitos), `sg_uf` (opcional, 2 chars), `include_geometria` (bool, default false) |
| **Comportamento sem municipioIdIbge** | Retorna TODOS os municípios da collection |
| **Comportamento com municipioIdIbge** | Busca específica com fallback para setor_indicadores |
| **Resposta** | `{ type: "FeatureCollection", features: [ { type: "Feature", id: "2504009", mongoId: "...", geometry: { type: "Point", coordinates: [lon, lat] }, properties: { municipioIdIbge, co_municipio, municipio, uf, total_escolas, total_alunos, avg_ideb, pct_com_biblioteca, pct_com_internet, pct_com_internet_alunos, pct_com_lab_informatica, pct_com_lab_ciencias, pct_sem_acessibilidade, socioeconomico, educacao, source } } ] }` |

#### `GET /api/v1/aggregations/neighborhoods`

| Item | Detalhe |
|---|---|
| **Método** | GET |
| **Rota** | `/api/v1/aggregations/neighborhoods` |
| **Descrição** | Retorna indicadores por bairro de um município |
| **Collections** | `bairro_indicadores` (primária), `setor_indicadores` (fallback) |
| **Parâmetros Query** | `municipio_id` (obrigatório, 7 dígitos), `municipioIdIbge` (alias deprecated), `bairro` (opcional, filtro case-insensitive), `include_geometria` (bool, default false) |
| **Resposta sem geometria** | Lista de `MongoNeighborhoodAggregation`: `{ _id, municipio, bairro, cd_bairro_ibge, geometria, municipioIdIbge, pct_com_*, sg_uf, total_escolas, total_matriculas, tem_bairro_oficial, nivel, cd_setor, socioeconomico, educacao, source }` |
| **Resposta com geometria** | GeoJSON FeatureCollection |
| **Validação** | `municipio_id_ibge` deve ter exatamente 7 dígitos (DomainValidationError) |
| **Erro** | 422 se nenhum dos parâmetros de município for informado |

---

### 3.6 Busca Universal

#### `GET /api/v1/busca/universal`

| Item | Detalhe |
|---|---|
| **Método** | GET |
| **Rota** | `/api/v1/busca/universal` |
| **Descrição** | Busca unificada que retorna sugestões tipadas com coordenadas para centralização no mapa |
| **Collections** | `escolas`, `municipio_indicadores`, `bairro_indicadores` |
| **Parâmetros Query** | `q` (obrigatório, min 2 chars), `sg_uf` (opcional), `municipio_id` (opcional), `limit` (1-20, default 20) |
| **Tipos de resultado** | `escola`, `logradouro`, `cep`, `municipio`, `bairro` |
| **Resposta** | `{ results: [ { id, kind, label, subtitle, coordinates: [lon, lat], municipioIdIbge, metadata: {} } ], total: int, query: str }` |
| **Estratégia de busca** | `asyncio.gather` paralelo em todas as fontes |
| **Detecção de CEP** | Se query tem 8 dígitos, busca apenas por CEP |
| **Busca accent-insensitive** | Regex com classes de caracteres acentuados + collation `pt` strength 1 |
| **Fallback** | Busca por prefixo → busca por substring (se prefixo não retornar resultados) |
| **Ranking** | Match exato > prefixo > substring > subtitle; prioridade: escola > logradouro > bairro > município > cep |

---

### 3.7 Estados

#### `GET /api/v1/estados/{sg_uf}/resumo`

| Item | Detalhe |
|---|---|
| **Método** | GET |
| **Rota** | `/api/v1/estados/{sg_uf}/resumo` |
| **Descrição** | Resumo estadual com indicadores educacionais e socioeconômicos agregados de todos os municípios |
| **Collection** | `municipio_indicadores` |
| **Parâmetros Path** | `sg_uf` (2 chars, ex: PB) |
| **Resposta** | `StateSummary` com: `sg_uf`, `estado`, `educacao` (30+ indicadores com médias ponderadas), `socioeconomico` (população total, taxa desemprego média) |
| **Cálculo educação** | Infraestrutura: média ponderada por nº de escolas. Indicadores acadêmicos: média ponderada por nº de alunos |
| **Cálculo socioeconômico** | Média ponderada por população |
| **Erro** | 404 se não houver dados para o estado |

---

## 4. Models/Schemas Definidos

### 4.1 Entidade Principal — School

```python
class School(BaseModel):
    id: str
    municipio_id_ibge: str          # 7 dígitos IBGE
    escola_id_inep: int             # 8 dígitos INEP
    escola_nome: str
    municipio_nome: str
    estado_sigla: UF                # Enum: AL, BA, CE, MA, PB, PE, PI, RN, SE
    dependencia_adm: DependenciaAdministrativa  # Federal/Estadual/Municipal/Privada
    tipo_localizacao: TipoLocalizacao           # Urbana/Rural
    localizacao: Location           # { type: "Point", coordinates: [lon, lat] }
    endereco: Endereco              # { bairro, cep, logradouro, municipio, numero, uf }
    indicadores: Indicadores        # Métricas por etapa de ensino
    matriculas: Matriculas          # Totais por nível
    infraestrutura: Infraestrutura  # Equipamentos, internet, salas, acessibilidade
```

### 4.2 Value Objects

| Value Object | Campos principais |
|---|---|
| `Location` | `type` ("Point"), `coordinates` (lon, lat) |
| `Endereco` | `bairro`, `cep`, `logradouro`, `municipio`, `numero`, `uf` |
| `Indicadores` | `anoReferencia`, `totalAlunos`, `educacaoInfantil`, `fundamentalAnosIniciais`, `fundamentalAnosFinais`, `ensinoMedio` (cada um com `alunosPorTurma`, `taxaAprovacao`, `taxaReprovacao`, `horasAulaDiarias`, `tnr`) |
| `Matriculas` | `totalAlunos`, `educacaoInfantil`, `educacaoInfantilCreche`, `educacaoInfantilPreEscola`, `fundamentalTotal`, `fundamentalAnosIniciais`, `fundamentalAnosFinais`, `ensinoMedio`, `eja` |
| `Infraestrutura` | `possuiBiblioteca`, `possuiInternet`, `possuiLabInformatica`, `possuiQuadraEsportes`, `possuiAcessibilidadePcd`, `possuiAguaPotavel`, etc. + sub-objetos `equipamentos`, `internet`, `salas` |
| `PaginatedResponse[T]` | `items`, `total_items`, `page`, `page_size`, `next_cursor` |
| `QueryOptions` | `page`, `page_size`, `cursor`, `filters[]`, `sort`, `fields[]` |

### 4.3 Entidades Territoriais

| Entidade | Uso |
|---|---|
| `MunicipioResumo` | Resumo completo com educação (30+ campos) + socioeconômico (11 sub-objetos) |
| `MunicipioCatalogItem` | Item leve para seletores: `{ id, nome, sg_uf }` |
| `BairroResumo` | Resumo de bairro com mesma estrutura de indicadores |
| `StateSummary` | Agregação estadual com `EducacaoStateStats` + `SocioeconomicoStateStats` |
| `CityAggregation` | Estrutura intermediária para cálculo de agregação estadual |
| `CitySummary` | Resumo territorial de cidade para GeoJSON |
| `NeighborhoodSummary` | Resumo territorial de bairro para GeoJSON |
| `SummaryStats` | Estatísticas gerais: totais, percentuais de infra, distribuição por dependência/zona |

---

## 5. Conexão com Banco de Dados

### 5.1 Configuração

- **Driver**: Motor (async) + PyMongo
- **Conexão**: MongoDB Atlas via URI em variável de ambiente `MONGO_URI`
- **Database**: Configurado via `DATABASE_NAME`
- **Singleton**: Classe `MongoDB` em `connect_db.py` com lifecycle gerenciado pelo lifespan do FastAPI
- **Health check**: `ping` no admin ao conectar

### 5.2 Collections Utilizadas

| Collection | Descrição | Uso principal |
|---|---|---|
| `escolas` | Dados individuais de cada escola | Listagem, busca, GeoJSON, stats |
| `municipio_indicadores` | Indicadores agregados por município | Agregações de cidade, resumo municipal, resumo estadual, busca |
| `bairro_indicadores` | Indicadores agregados por bairro | Agregações de bairro, resumo de bairro, busca |
| `setor_indicadores` | Indicadores por setor censitário | Fallback quando dados primários não existem |

### 5.3 Índices Criados Automaticamente

Os índices são criados no startup via `_ensure_indexes()`:

**Collection `escolas`:**
| Índice | Campos | Tipo | Observação |
|---|---|---|---|
| `idx_escolas_estado_municipio_bairro` | `estadoSigla` + `municipioNome` + `endereco.bairro` | Compound | Filtros combinados |
| `idx_escolas_inep` | `escolaIdInep` | Single | Busca por INEP |
| `idx_escolas_localizacao_2dsphere_valid_only` | `localizacao` | 2dsphere | Partial filter (coordenadas válidas) |
| `idx_escolas_nome_busca` | `escolaNome` | Single | Collation `pt` strength 1 |
| `idx_escolas_logradouro_busca` | `endereco.logradouro` | Single | Collation `pt` strength 1 |
| `idx_escolas_cep_busca` | `endereco.cep` | Single | Busca por CEP |
| `idx_geojson_paraiba_municipio` | `estadoSigla` + `municipioIdIbge` + `escolaIdInep` | Compound | GeoJSON endpoint |

**Collection `municipio_indicadores`:**
| Índice | Campos |
|---|---|
| `idx_municipio_indicadores_co_municipio` | `co_municipio` |
| `idx_municipio_indicadores_municipioIdIbge` | `municipioIdIbge` |
| `idx_municipio_indicadores_municipio_id_ibge` | `municipio_id_ibge` |
| `idx_municipio_indicadores_idIbge` | `idIbge` |
| `idx_municipio_nome_busca` | `municipio` (collation pt) |

**Collection `bairro_indicadores`:**
| Índice | Campos |
|---|---|
| Compound indexes | `{municipio_field}` + `{bairro_field}` para cada combinação |
| `idx_bairro_nome_busca` | `bairro` (collation pt) |

**Collection `setor_indicadores`:**
| Índice | Campos |
|---|---|
| `idx_setor_indicadores_*` | Mesmos campos de município (`co_municipio`, `municipioIdIbge`, etc.) |

---

## 6. Middlewares, Validações e Tratamento de Erros

### 6.1 CORS

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,  # Configurável via CORS_ALLOWED_ORIGINS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 6.2 Global Exception Handlers

| Exceção | Status | Código de erro |
|---|---|---|
| `HTTPException` | Variável (404, 422, 5xx) | `NOT_FOUND`, `VALIDATION_ERROR`, `INTERNAL_SERVER_ERROR` |
| `RequestValidationError` | 422 | `VALIDATION_ERROR` + detalhes dos erros |
| `DomainValidationError` | 422 | `DOMAIN_VALIDATION_ERROR` |
| `PyMongoError` | 503 | `DATABASE_ERROR` ("The database is temporarily unavailable") |
| `ValueError` | 500 | `MAPPER_ERROR` |
| `Exception` (genérica) | 500 | `INTERNAL_SERVER_ERROR` |

**Formato padrão de erro:**
```json
{
  "error": "CODIGO_ERRO",
  "message": "Descrição legível",
  "detail": "..." // opcional
}
```

### 6.3 Validações

**Camada de Apresentação (borda HTTP):**
- `QueryParamParser`: Valida filtros, sort, fields e paginação via query string
- `SchoolSearchSchema`: Valida campos permitidos, operadores e valores
- FastAPI `Query()` com `min_length`, `max_length`, `ge`, `le`, `pattern`
- Proteção contra deep pagination: offset > 50.000 retorna 422

**Camada de Domínio:**
- `SchoolValidator`: Valida IBGE (7 dígitos), INEP (8 dígitos), nome, localização, coordenadas, indicadores, infraestrutura
- `NeighborhoodValidator`: Valida `municipio_id_ibge` (7 dígitos)

---

## 7. Configuração

### 7.1 Variáveis de Ambiente (`.env.example`)

```env
# Database
MONGO_URI="mongodb+srv://<user>:<password>@<cluster>.mongodb.net/<dbname>?retryWrites=true&w=majority"
DATABASE_NAME="odin_db"

# Server
PORT=8000
ENVIRONMENT=development   # development | staging | production

# CORS
CORS_ALLOWED_ORIGINS="http://localhost:3000"

# Pagination
MAX_PAGE_SIZE=100
MAX_OFFSET_RECORDS=50000
USE_ESTIMATED_TOTAL=true
```

### 7.2 AppConfig (Dataclass)

```python
@dataclass
class AppConfig:
    port: int                                    # default 8000
    environment: str                             # default "development"
    mongo_uri: str                               # OBRIGATÓRIO
    database_name: str                           # OBRIGATÓRIO
    max_page_size: int                           # default 100
    max_offset_records: int                      # default 50000
    use_estimated_total_for_unfiltered_lists: bool  # default true
    cors_origins: list[str]                      # parsed de CSV
```

### 7.3 Docker

**Dockerfile:**
- Base: `python:3.12-slim`
- Instala Poetry, copia deps, instala apenas produção
- Não define CMD (provavelmente definido no compose ou externamente)

**docker-compose.yml:**
- Serviço `api` na porta 5000:5000
- Usa `.env` para variáveis

### 7.4 Makefile

Comandos disponíveis:
- `make dev` — Servidor com hot reload
- `make prod` — Servidor produção
- `make lint` — flake8
- `make format` — black
- `make typecheck` — mypy
- `make test` — pytest
- `make docker-build/up/down/logs/shell/clean`

---

## 8. Dependências Principais e Versões

### Produção

| Pacote | Versão | Função |
|---|---|---|
| `fastapi` | ^0.104.1 | Framework web assíncrono |
| `uvicorn[standard]` | ^0.24.0 | Servidor ASGI |
| `pydantic` | ^2.5.0 | Validação e serialização |
| `motor` | ^3.3.2 | Driver MongoDB assíncrono |
| `pymongo` | ^4.6.0 | Driver MongoDB (base do Motor) |
| `python-multipart` | ^0.0.6 | Upload de arquivos (FastAPI) |
| `python-dotenv` | ^1.0.0 | Carregamento de .env |
| `dependency-injector` | ^4.41.0 | Container de injeção de dependência |

### Desenvolvimento

| Pacote | Versão | Função |
|---|---|---|
| `pytest` | ^7.4.3 | Framework de testes |
| `pytest-asyncio` | ^0.21.1 | Suporte async para pytest |
| `black` | ^23.11.0 | Formatador de código |
| `flake8` | ^6.1.0 | Linter |
| `mypy` | ^1.7.1 | Type checker |
| `httpx` | ^0.27.0 | Cliente HTTP para testes |

---

## 9. Status: Funcional vs. Parcial vs. Pendente

### ✅ Funcional (Implementado e Operacional)

| Feature | Status | Observação |
|---|---|---|
| Listagem paginada de escolas | ✅ Completo | Filtros, sort, projeção, cursor, search |
| Busca por ID INEP | ✅ Completo | — |
| GeoJSON Paraíba (escolas) | ✅ Completo | Com cache in-memory |
| GeoJSON bairros por município | ✅ Completo | Aggregation pipeline |
| Bairro por escola | ✅ Completo | — |
| Estatísticas gerais (PB) | ✅ Completo | Infra, dependência, zona |
| Lista de municípios | ✅ Completo | Filtro por UF |
| Resumo de município | ✅ Completo | Com fallback para setores |
| Resumo de bairro | ✅ Completo | Com fallback para setores |
| Agregação por cidade (GeoJSON) | ✅ Completo | Com fallback |
| Agregação por bairro | ✅ Completo | Com fallback + filtro por nome |
| Busca universal | ✅ Completo | 5 tipos, paralela, ranking |
| Resumo estadual | ✅ Completo | Médias ponderadas |
| Tratamento global de erros | ✅ Completo | 6 handlers |
| Índices MongoDB automáticos | ✅ Completo | Criados no startup |
| CORS configurável | ✅ Completo | Via env var |
| Paginação cursor-based | ✅ Completo | Base64 encoded |
| Validação de domínio | ✅ Completo | School + Neighborhood |
| Injeção de dependência | ✅ Completo | Container por módulo |
| Docker + Compose | ✅ Completo | — |

### ⚠️ Parcial / Limitações Conhecidas

| Item | Status | Detalhe |
|---|---|---|
| Cobertura de testes | ⚠️ Parcial | Estrutura de testes existe (`tests/`) mas sem cobertura visível no código |
| Escopo geográfico | ⚠️ Limitado | Stats hardcoded para PB; GeoJSON hardcoded para PB; Enum UF apenas Nordeste |
| Autenticação/Autorização | ⚠️ Ausente | Nenhum middleware de auth implementado |
| Rate limiting | ⚠️ Ausente | Sem proteção contra abuso |
| Logging estruturado | ⚠️ Básico | Apenas `logging` padrão, sem correlação de requests |
| Documentação OpenAPI | ⚠️ Parcial | FastAPI gera automaticamente, mas nem todos os endpoints têm `summary`/`description` completos |
| Cache distribuído | ⚠️ Ausente | Apenas cache in-memory (não persiste entre instâncias) |

### 🔲 Pendente / Planejado (baseado na documentação)

| Item | Evidência |
|---|---|
| Novos módulos (Hospitals, Companies) | Documentado em `docs/03-module-pattern.md` |
| Busca fuzzy avançada | Mencionado como trade-off em `docs/05-busca-universal-modelagem.md` |
| Cache Redis | Considerado e descartado na v1 (doc de busca) |
| Atlas Search | Alternativa considerada para busca |
| Endpoints de escrita (CRUD completo) | Repository interface tem apenas leitura |
| Testes automatizados robustos | Deps de teste existem mas sem suíte visível |
| CI/CD completo | Workflows GitHub existem (Docker build check, Discord notifier) |

---

## 10. Cruzamento com Documentação de Planejamento

### Documentos encontrados em `docs/`:

| Documento | Conteúdo | Status de Implementação |
|---|---|---|
| `01-resumo-e-introducao.md` | Visão geral, stack, fluxo de requisição | ✅ Implementado conforme descrito |
| `03-module-pattern.md` | Padrão repetível para novos módulos | ✅ Padrão seguido em school, municipio, bairro, search, state, aggregation |
| `04-aggregations-endpoints.md` | Spec dos endpoints de agregação (cities + neighborhoods) | ✅ Implementado com todas as features descritas (fallback, GeoJSON, filtros) |
| `05-busca-universal-modelagem.md` | Modelagem completa da busca universal | ✅ Implementado seguindo a spec (módulo isolado, asyncio.gather, ranking, collation, índices) |

### Progresso vs. Planejamento

A documentação de planejamento foi **integralmente implementada**. Todos os endpoints, estratégias de fallback, índices e padrões arquiteturais descritos nos docs estão presentes no código. O projeto está além do que a documentação inicial (`01-resumo-e-introducao.md`) descrevia como "enxuto em endpoints" — cresceu significativamente com módulos de agregação, busca universal e resumos territoriais.

---

## 11. Resumo de Rotas (Quick Reference)

```
GET  /api/v1/schools                              → Lista escolas (paginada + filtros)
GET  /api/v1/all                                  → Alias para /schools
GET  /api/v1/{escola_id_inep}                     → Escola por INEP
GET  /api/v1/escolas/geojson/paraiba              → GeoJSON escolas PB
GET  /api/v1/bairros/geojson/{municipio}          → GeoJSON bairros (por nome)
GET  /api/v1/bairro/{school_id}                   → Bairro de uma escola
GET  /api/v1/school/stats/summary                 → Stats gerais PB
GET  /api/v1/municipios                           → Lista municípios
GET  /api/v1/municipios/{municipio_id}/resumo     → Resumo município
GET  /api/v1/bairros/{bairro_id}/resumo           → Resumo bairro
GET  /api/v1/aggregations/cities                  → Agregação por cidade (GeoJSON)
GET  /api/v1/aggregations/neighborhoods           → Agregação por bairro
GET  /api/v1/busca/universal                      → Busca universal
GET  /api/v1/estados/{sg_uf}/resumo               → Resumo estadual
```

**Total: 14 rotas (12 endpoints únicos + 2 aliases)**

---