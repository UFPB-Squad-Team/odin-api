# ODIN-Backend — Expansão para o Nordeste (ADR-002)

**Epic:** Expansão do Backend ODIN para suportar dados dos 9 estados do Nordeste
**Objetivo:** Sair de cobertura PB (223 municípios / 3.737 escolas) para NE completo (1.794 municípios / ~75.000 escolas), mantendo a arquitetura Clean Architecture e performance adequada.

Legenda de prioridade: 🔴 Bloqueadora · 🟠 Alta · 🟡 Média · 🟢 Baixa

---

## Para quem está começando no Backend

### Como os dados fluem (visão geral)

```
MongoDB (dados brutos)  →  Repositories (acesso)  →  Use Cases (regras)  →  Controllers (API)  →  Frontend
```

- **MongoDB:** coleções com dados processados pelo ETL. Schema já é state-agnostic (tem campo `estadoSigla`/`sg_uf`).
- **Repositories:** camada de acesso a dados. Implementam queries, filtros e índices.
- **Use Cases:** regras de negócio. Orquestram repositories e aplicam lógica.
- **Controllers:** endpoints HTTP. Recebem requests, validam e retornam responses.

### Glossário rápido

| Termo | O que significa aqui |
|---|---|
| **UF** | Unidade Federativa (estado). Ex: PB, PE, CE. No código, `estadoSigla` é o campo que filtra por estado. |
| **Clean Architecture** | Padrão de separação de responsabilidades: Domain (entidades) → Application (use cases) → Infrastructure (banco) → Presentation (API). |
| **Repository Pattern** | Camada de abstração para acesso a dados. Isola a lógica de banco do resto da aplicação. |
| **Use Case** | Classe que executa uma ação de negócio (ex: `ListAllSchools`, `GetCityAggregations`). |
| **DTO** | Data Transfer Object — objeto que transporta dados entre camadas. |
| **Cursor pagination** | Paginação baseada em cursor (mais eficiente para grandes volumes) ao invés de offset. |
| **State-agnostic** | Código que funciona para qualquer estado sem mudanças. Ex: filtros por `estadoSigla` já são genéricos. |
| **Hardcoded** | Valor fixo no código (ex: `"PB"`). Precisa ser parametrizado. |

### Padrão de código que se repete em quase toda task

A maioria das tasks segue este padrão. Se você entender essa mudança, entende 70% da expansão:

```python
# ANTES — funciona só para PB
match_query = {"estadoSigla": "PB"}

# DEPOIS — funciona para qualquer lista de UFs
match_query = {"estadoSigla": {"$in": ["PB", "PE", "CE", "RN", "MA", "PI", "AL", "SE", "BA"]}}
```

Cuidado com nomes de métodos e variáveis que levam "paraiba" no nome (ex: `get_paraiba_geojson`, `_paraiba_geojson_cache`). Eles precisam ser renomeados para algo genérico como `get_geojson` ou `get_estado_geojson`.

---

## Sprint 1 — Preparação e Parametrização de Filtros

### [ODIN-B01] Parametrizar filtros hardcoded de UF nos repositories
**Prioridade:** 🔴 Bloqueadora
**Descrição:**
Hoje existem filtros hardcoded para `"PB"` em vários repositories. É necessário transformar esses filtros para aceitar lista de UFs. Locais principais:
- `MongoSchoolRepository.get_paraiba_geojson()` → renomear para `get_geojson()` e aceitar parâmetro `sg_uf: list[str] | None`
- `MongoSchoolRepository.get_bairros_geojson()` → remover `"estadoSigla": "PB"` do match
- `MongoSchoolRepository._ensure_geojson_indexes()` → renomear índices de `idx_geojson_paraiba_*` para `idx_geojson_*`
- Remover variáveis de cache com nome `_paraiba_geojson_cache` → renomear para `_geojson_cache`

**Arquivos afetados:**
- `src/infrastructure/database/repository/mongo_school_repository.py`
- `src/infrastructure/database/repository/mongo_municipio_repository.py`
- `src/infrastructure/database/repository/mongo_bairro_repository.py`

**Critério de aceite:** Nenhum filtro hardcoded para `"PB"` nos repositories. Métodos aceitam lista de UFs ou usam `estadoSigla` genérico.
**Dependências:** Nenhuma — pode começar imediatamente.

---

### [ODIN-B02] Atualizar use cases de agregação para suportar multi-UF
**Prioridade:** 🟠 Alta
**Descrição:**
Os use cases de agregação (`GetCityAggregations`, `GetNeighborhoodAggregations`) já recebem `sg_uf` como parâmetro, mas precisam garantir que o filtro é aplicado corretamente quando uma lista de UFs é fornecida. Verificar se o repository repassa o filtro corretamente para o MongoDB.

**Arquivos afetados:**
- `src/application/aggregation/get_city_aggregations.py`
- `src/application/aggregation/get_neighborhood_aggregations.py`

**Critério de aceite:** Agregações retornam dados corretos quando `sg_uf` é uma lista (ex: `["PB", "PE"]`).
**Dependências:** ODIN-B01

---

### [ODIN-B03] Criar use case e controller para listar estados
**Prioridade:** 🟠 Alta
**Descrição:**
Já existe o endpoint `/api/v1/estados` (list_states_controller.py), mas é necessário garantir que:
1. O use case `ListStatesUseCase` retorna os 9 estados do NE quando todos estiverem carregados
2. O endpoint suporta busca fuzzy por nome/sigla
3. A entidade `State` já está correta (id, nome, sigla)

**Arquivos afetados:**
- `src/application/state/list_states/list_states.py`
- `src/presentation/http/controller/state/list_states_controller.py`

**Critério de aceite:** `GET /api/v1/estados` retorna lista com os 9 estados do NE após ETL completo.
**Dependências:** Nenhuma — pode começar imediatamente.

---

### [ODIN-B04] Criar use case e controller para resumo por estado
**Prioridade:** 🟡 Média
**Descrição:**
Criar endpoint `GET /api/v1/estados/{sg_uf}/resumo` que retorna agregados por estado:
- Total de municípios
- Total de escolas
- Total de alunos
- Média de IDEB
- Indicadores socioeconômicos principais

**Arquivos afetados:**
- `src/application/state/get_state_summary.py` (novo)
- `src/presentation/http/controller/state/get_state_summary_controller.py` (novo)
- `src/domain/entities/state_summary.py` (novo)

**Critério de aceite:** `GET /api/v1/estados/PB/resumo` retorna JSON com agregados da Paraíba.
**Dependências:** ODIN-B03

---

## Sprint 2 — Filtros e Endpoints Multi-Estado

### [ODIN-B05] Adicionar filtro por lista de UFs no endpoint de escolas
**Prioridade:** 🟠 Alta
**Descrição:**
Atualmente o endpoint `GET /api/v1/schools` aceita filtros por `municipio`, `dependencia_adm`, `tipo_localizacao`, mas não por `estado_sigla`. É necessário:
1. Adicionar parâmetro `estado_sigla: List[str] | None` no controller
2. Adicionar `estado_sigla` em `SCHOOL_ALLOWED_FILTERS` e `SCHOOL_QUERY_FIELDS`
3. Garantir que o use case aplica o filtro corretamente

**Arquivos afetados:**
- `src/presentation/http/controller/school/list_all_schools_controller.py`
- `src/presentation/http/controller/school/school_query_config.py`
- `src/application/school/list_all_schools/list_all_schools.py`

**Critério de aceite:** `GET /api/v1/schools?estado_sigla=PB&estado_sigla=PE` retorna escolas de ambos os estados.
**Dependências:** ODIN-B01

---

### [ODIN-B06] Adicionar filtro por estado nas agregações de cidade e bairro
**Prioridade:** 🟡 Média
**Descrição:**
Os endpoints de agregação já aceitam `sg_uf` como query param, mas precisam garantir que:
1. Quando `sg_uf` é uma lista, retorna agregações de todos os estados
2. Quando `sg_uf` não é fornecido, retorna agregações de todos os estados (comportamento atual)
3. Documentar esse comportamento no OpenAPI

**Arquivos afetados:**
- `src/presentation/http/controller/aggregation/aggregations_controller.py`
- `src/application/aggregation/get_city_aggregations.py`
- `src/application/aggregation/get_neighborhood_aggregations.py`

**Critério de aceite:** `GET /api/v1/aggregations/cities?sg_uf=PB&sg_uf=PE` retorna cidades de PB e PE.
**Dependências:** ODIN-B02

---

### [ODIN-B07] Criar endpoint de busca universal multi-estado
**Prioridade:** 🟡 Média
**Descrição:**
O endpoint de busca universal (`/api/v1/busca`) já existe, mas é necessário garantir que:
1. Busca retorna resultados de todos os estados quando não filtrado
2. Busca por `municipio_nome` retorna resultados corretos mesmo quando há municípios homônimos em estados diferentes (ex: "São José" em PB e PE)
3. Adicionar parâmetro opcional `estado_sigla` para filtrar por estado

**Arquivos afetados:**
- `src/presentation/http/controller/search/universal_search_controller.py`
- `src/application/search/universal_search.py`

**Critério de aceite:** `GET /api/v1/busca?q=João Pessoa` retorna a escola de João Pessoa/PB. `GET /api/v1/busca?q=João Pessoa&estado_sigla=PB` também retorna.
**Dependências:** ODIN-B05

---

## Sprint 3 — Performance e Escalabilidade

### [ODIN-B08] Otimizar índices MongoDB para multi-estado
**Prioridade:** 🟠 Alta
**Descrição:**
Com ~75k escolas, os índices atuais precisam ser revisados:
1. Garantir índice composto `estadoSigla + municipioIdIbge + escolaIdInep` (já existe, mas precisa ser validado)
2. Adicionar índice em `estadoSigla` para queries que filtram apenas por estado
3. Adicionar índice em `municipioNome` + `estadoSigla` para buscas por município
4. Revisar índices de agregações (`municipio_indicadores`, `bairro_indicadores`, `setor_indicadores`)

**Arquivos afetados:**
- `src/infrastructure/database/repository/mongo_school_repository.py`
- `src/infrastructure/database/repository/mongo_municipio_repository.py`
- `src/infrastructure/database/repository/mongo_territorial_aggregation_repository.py`

**Critério de aceite:** Queries com filtro por `estadoSigla` retornam em < 100ms com 75k documentos.
**Dependências:** ODIN-B01

---

### [ODIN-B09] Implementar cache por estado para agregações
**Prioridade:** 🟡 Média
**Descrição:**
Agregações de cidade e bairro são computacionalmente caras. Implementar cache em memória (TTL-based) por estado:
1. Cache de agregações de cidade por `sg_uf`
2. Cache de agregações de bairro por `municipio_id + sg_uf`
3. TTL de 5 minutos (configurável)
4. Invalidação automática após TTL

**Arquivos afetados:**
- `src/application/aggregation/get_city_aggregations.py`
- `src/application/aggregation/get_neighborhood_aggregations.py`
- `src/infrastructure/cache/aggregation_cache.py` (novo)

**Critério de aceite:** Segunda requisição para mesma agregação retorna em < 50ms (cache hit).
**Dependências:** ODIN-B06

---

### [ODIN-B10] Aumentar limite de page_size para suportar listagens grandes
**Prioridade:** 🟢 Baixa
**Descrição:**
Com 75k escolas, o `max_page_size` atual (provavelmente 100) é muito pequeno. Aumentar para 500 ou implementar cursor-based pagination como padrão.

**Arquivos afetados:**
- `src/infrastructure/database/config/app_config.py`
- `src/presentation/http/controller/school/list_all_schools_controller.py`

**Critério de aceite:** `GET /api/v1/schools?page_size=500` retorna 500 escolas por página sem erro.
**Dependências:** Nenhuma — pode começar imediatamente.

---

## Sprint 4 — Validação, Testes e Deploy

### [ODIN-B11] Criar testes de integração para multi-estado
**Prioridade:** 🟡 Média
**Descrição:**
Criar testes que validam:
1. Filtro por lista de UFs retorna dados corretos
2. Agregações retornam dados de múltiplos estados
3. Busca universal funciona com municípios homônimos
4. Performance: queries retornam em < 200ms

**Arquivos afetados:**
- `tests/test_multi_state_school_repository.py` (novo)
- `tests/test_multi_state_aggregations.py` (novo)
- `tests/test_state_endpoints.py` (novo)

**Critério de aceite:** `pytest tests/ -v` passa sem falhas.
**Dependências:** Sprints 1–3 concluídos.

---

### [ODIN-B12] Atualizar documentação da API (OpenAPI)
**Prioridade:** 🟡 Média
**Descrição:**
Atualizar descrições dos endpoints no código para refletir suporte a multi-estado:
1. Adicionar exemplos de uso com múltiplos estados
2. Documentar comportamento de filtros opcionais
3. Adicionar nota sobre performance com 75k escolas

**Arquivos afetados:**
- Todos os controllers com filtros por estado
- `README.md` do backend

**Critério de aceite:** `/docs` (Swagger) mostra exemplos corretos e descrições atualizadas.
**Dependências:** ODIN-B05, ODIN-B06

---

### [ODIN-B13] Deploy em produção da expansão Nordeste
**Prioridade:** 🔴 Bloqueadora
**Descrição:**
Merge da branch para `main`, build da imagem Docker e deploy. Validar:
1. Todos os endpoints funcionam com dados do NE completo
2. Performance: p95 de latência < 500ms
3. MongoDB não tem queries lentas (usar `explain()`)
4. Monitoramento de erros não mostra exceções

**Critério de aceite:** API em produção respondendo corretamente para os 9 estados, sem regressão nos dados da PB.
**Rollback:** Como não alteramos schema do MongoDB, rollback é seguro — basta reverter o código.
**Dependências:** ODIN-B11, ODIN-B12

---

## Resumo de ordem de execução

```
Sprint 1: ODIN-B01 → ODIN-B02 → ODIN-B03 → ODIN-B04
Sprint 2: ODIN-B05 → ODIN-B06 → ODIN-B07
Sprint 3: ODIN-B08 → ODIN-B09 → ODIN-B10
Sprint 4: ODIN-B11 → ODIN-B12 → ODIN-B13
```

---

## Referência técnica (para quem já manja de Backend)

### O que já é state-agnostic vs. o que exige migração real

| Componente | Estado atual | Ação necessária |
|---|---|---|
| Schema MongoDB (coleções, índices) | Já usa `estadoSigla` como campo — state-agnostic | Nenhuma |
| Entidades (School, State, Municipio) | Já têm campo de estado | Nenhuma |
| Use Cases (agregações, buscas) | Lógica genérica, sem filtro de UF hardcoded | Nenhuma |
| Repositories (acesso a dados) | Alguns filtros hardcoded para `"PB"` | Parametrizar para lista de UFs |
| Controllers (endpoints) | Não aceitam filtro por `estado_sigla` | Adicionar parâmetro |
| Cache (GeoJSON) | Nome e lógica específicos para PB | Renomear e generalizar |
| Validações | Não há validações de escala | Nenhuma (MongoDB aguenta 75k docs) |

### Decisões já fechadas no ADR-002 (evitar reabrir discussão)

| Alternativa | Por que foi rejeitada/aceita |
|---|---|
| Criar banco por estado | Complexidade operacional desnecessária — MongoDB suporta 75k docs no tier atual; índice por `estadoSigla` resolve queries filtradas |
| Modificar schema do MongoDB | Desnecessário — schema já é state-agnostic |
| Implementar sharding | Prematuro — 75k docs não justifica sharding; otimizar índices primeiro |
| Cache distribuído (Redis) | Overkill para escala atual — cache em memória (TTL) é suficiente |

### Padrão de migração: Hardcoded → State-Agnostic

```python
# ANTES — hardcoded para PB
match_query = {"estadoSigla": "PB"}
result = await collection.find(match_query).to_list()

# DEPOIS — state-agnostic
def get_geojson(self, sg_uf: str | list[str] | None = None) -> dict:
    match_query: dict[str, Any] = {}
    
    if sg_uf:
        if isinstance(sg_uf, str):
            match_query["estadoSigla"] = sg_uf
        else:
            match_query["estadoSigla"] = {"$in": sg_uf}
    
    match_query.update({
        "localizacao.type": "Point",
        "localizacao.coordinates.0": {"$type": "number"},
        "localizacao.coordinates.1": {"$type": "number"},
    })
    
    docs = await self.collection.find(match_query).to_list(length=None)
    # ... resto da lógica
```

### Riscos com maior probabilidade de virar bug silencioso

- **Filtro hardcoded não atualizado**: endpoint retorna apenas dados da PB mesmo com dados do NE carregados
- **Nome de método/variável com "paraiba"**: causa confusão e bugs futuros quando outro estado for adicionado
- **Índice não criado**: queries ficam lentas com 75k documentos (full collection scan)
- **Cache sem invalidação**: dados desatualizados após novo ETL

### Checklist de performance esperado

- [x] Queries com filtro por `estadoSigla` retornam em < 100ms (índice `idx_escolas_estado_inep` + teste de performance opt-in `RUN_PERFORMANCE_TESTS=1`)
- [x] Agregações de cidade retornam em < 500ms (cache TTL em memória por estado — ODIN-B09)
- [x] Listagem de escolas (page_size=100) retorna em < 200ms (max_page_size agora 500 — ODIN-B10)
- [ ] Busca universal retorna em < 300ms (fora do escopo desta sprint)
- [x] GeoJSON de escolas retorna em < 1s (com cache próprio do repository)
- [ ] Memória RAM do servidor < 512MB em idle (verificar após deploy)
- [ ] Memória RAM do servidor < 1GB sob carga normal (verificar após deploy)

### Monitoramento recomendado

Após deploy, monitorar:
1. **Latência p95** por endpoint (target: < 500ms)
2. **Taxa de erro** (target: < 0.1%)
3. **Uso de memória** (alerta se > 1.5GB)
4. **Queries lentas** no MongoDB (alerta se > 1s)
5. **Cache hit rate** (target: > 70% para agregações)