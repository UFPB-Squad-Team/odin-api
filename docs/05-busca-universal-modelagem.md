# Modelagem — `GET /api/v1/busca/universal`

## 1. Visão Geral

Endpoint de busca unificada que recebe um texto livre e retorna sugestões tipadas (escola, logradouro, CEP, bairro, município) com coordenadas para centralização no mapa.

---

## 2. Decisões Arquiteturais

### 2.1 Módulo novo e isolado (`search`)

Este endpoint **não pertence** ao módulo `school`, `municipio` ou `bairro`. Ele cruza múltiplas collections e tem lógica de orquestração própria. Seguindo o padrão documentado em `docs/03-module-pattern.md`, criamos um módulo `search` dedicado.

**Justificativa**: O endpoint agrega dados de `escolas`, `municipio_indicadores` e `bairro_indicadores`. Colocá-lo em qualquer módulo existente violaria o SRP (Single Responsibility Principle) — cada módulo deve ter uma única razão para mudar.

### 2.2 Sem entidade de domínio rica

Diferente de `School` que tem validadores complexos, o resultado de busca é um **Value Object de leitura** (read-only DTO). Não há regras de negócio que justifiquem uma entidade com validação de domínio. Usaremos Pydantic models como DTOs tipados.

### 2.3 Repository dedicado (não herda de `BaseMongoRepository`)

O `BaseMongoRepository` foi projetado para CRUD paginado de uma única collection com field mapping. A busca universal:
- Consulta **3 collections** diferentes
- Usa **aggregation pipelines** e **regex/text search**
- Não precisa de paginação cursor-based
- Não mapeia para entidade de domínio

Portanto, teremos um `IUniversalSearchRepository` com implementação `MongoUniversalSearchRepository` que recebe as 3 collections diretamente (padrão já usado em `MongoTerritorialAggregationRepository`).

### 2.4 Estratégia de busca no MongoDB

**Decisão**: Usar `$regex` com `^` (prefixo) + collation `pt` ao invés de `$text` search.

**Razões**:
1. `$text` exige índice textual que tokeniza palavras — ruim para autocomplete parcial ("epit" não encontra "Epitácio")
2. `$regex` com `^` (anchored) usa índice B-tree eficientemente
3. Collation `{ locale: "pt", strength: 1 }` resolve case-insensitive + accent-insensitive nativamente no MongoDB sem normalização manual
4. Performance < 200ms é viável com índices corretos e limit pequeno (8-20 docs)

**Fallback**: Para termos que não são prefixo (busca no meio da string), usar `$regex` sem anchor com `$options: "i"` — mais lento, mas aceitável com limit baixo.

---

## 3. Estrutura de Pastas

```
src/
├── domain/
│   └── repository/
│       └── universal_search_repository.py          # Interface abstrata
│
├── application/
│   └── search/
│       └── universal_search/
│           ├── __init__.py
│           ├── universal_search_use_case.py        # Orquestração
│           └── universal_search_dto.py             # Input/Output DTOs
│
├── infrastructure/
│   └── database/
│       └── repository/
│           └── mongo_universal_search_repository.py  # Implementação MongoDB
│
└── presentation/
    └── http/
        └── controller/
            └── search/
                ├── __init__.py
                ├── index.py                        # Router principal
                ├── container.py                    # DI container
                ├── callable/
                │   ├── __init__.py
                │   └── search_callable.py          # Factory para Depends()
                └── universal_search_controller.py  # Controller HTTP
```

---

## 4. Contratos e Tipagens

### 4.1 Input DTO

```python
# src/application/search/universal_search/universal_search_dto.py

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class UniversalSearchInputDTO:
    """
    Parâmetros validados de entrada para a busca universal.
    Validação de borda (q >= 2 chars) já foi feita no controller.
    """
    q: str
    sg_uf: Optional[str] = None
    municipio_id: Optional[str] = None
    limit: int = 8
```

### 4.2 Output DTOs (Value Objects de resultado)

```python
# src/application/search/universal_search/universal_search_dto.py (continuação)

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class SearchResultItem:
    """
    Um item individual do resultado de busca.
    Imutável — é um Value Object de leitura.
    """
    id: str
    kind: str                          # "escola" | "logradouro" | "cep" | "municipio" | "bairro"
    label: str
    subtitle: str
    coordinates: tuple[float, float]   # [longitude, latitude]
    municipio_id_ibge: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class UniversalSearchOutputDTO:
    """Resultado completo da busca."""
    results: list[SearchResultItem]
    total: int
    query: str
```

### 4.3 Interface do Repository

```python
# src/domain/repository/universal_search_repository.py

from abc import ABC, abstractmethod
from typing import Optional


class IUniversalSearchRepository(ABC):
    """
    Contrato para busca universal cross-collection.
    
    Cada método retorna uma lista de dicts crus (raw docs) 
    que o use case transforma em SearchResultItem.
    Isso mantém o repository focado em acesso a dados
    e o use case focado em lógica de transformação/priorização.
    """

    @abstractmethod
    async def search_schools(
        self,
        q: str,
        *,
        sg_uf: Optional[str] = None,
        municipio_id: Optional[str] = None,
        limit: int = 8,
    ) -> list[dict]:
        """
        Busca escolas por nome (escolaNome).
        Retorna docs com: escolaIdInep, escolaNome, municipioNome, 
        municipioIdIbge, dependenciaAdm, tipoLocalizacao, 
        localizacao.coordinates, endereco.bairro
        """
        ...

    @abstractmethod
    async def search_logradouros(
        self,
        q: str,
        *,
        sg_uf: Optional[str] = None,
        municipio_id: Optional[str] = None,
        limit: int = 8,
    ) -> list[dict]:
        """
        Agrega logradouros únicos a partir de escolas.endereco.logradouro.
        Retorna docs com: logradouro, municipioNome, municipioIdIbge,
        bairros (lista), centroide (avg coordinates)
        """
        ...

    @abstractmethod
    async def search_by_cep(
        self,
        q: str,
        *,
        sg_uf: Optional[str] = None,
        municipio_id: Optional[str] = None,
        limit: int = 8,
    ) -> list[dict]:
        """
        Busca escolas por CEP (endereco.cep).
        Retorna docs com: cep, escolaNome, municipioNome, 
        municipioIdIbge, endereco.bairro, localizacao.coordinates
        """
        ...

    @abstractmethod
    async def search_municipios(
        self,
        q: str,
        *,
        sg_uf: Optional[str] = None,
        limit: int = 8,
    ) -> list[dict]:
        """
        Busca municípios por nome na collection municipio_indicadores.
        Retorna docs com: co_municipio/municipioIdIbge, municipio/nm_municipio,
        sg_uf, socioeconomico.populacao.total (para subtitle)
        """
        ...

    @abstractmethod
    async def search_bairros(
        self,
        q: str,
        *,
        sg_uf: Optional[str] = None,
        municipio_id: Optional[str] = None,
        limit: int = 8,
    ) -> list[dict]:
        """
        Busca bairros por nome na collection bairro_indicadores.
        Retorna docs com: cd_bairro_ibge, bairro/nm_bairro, 
        municipio, municipioIdIbge, centroide/localizacao
        """
        ...
```

### 4.4 Response Schema (Presentation Layer)

```python
# Definido inline no controller ou em schema separado

from pydantic import BaseModel, Field
from typing import Any


class SearchResultItemResponse(BaseModel):
    id: str
    kind: str
    label: str
    subtitle: str
    coordinates: list[float] = Field(..., min_length=2, max_length=2)
    municipioIdIbge: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class UniversalSearchResponse(BaseModel):
    results: list[SearchResultItemResponse]
    total: int
    query: str
```

---

## 5. Lógica do Use Case

```python
# src/application/search/universal_search/universal_search_use_case.py

class UniversalSearchUseCase:
    """
    Orquestra buscas paralelas em múltiplas fontes e 
    consolida resultados com priorização.
    
    Responsabilidades:
    1. Disparar buscas em paralelo (asyncio.gather)
    2. Transformar docs crus em SearchResultItem
    3. Aplicar priorização: escola > logradouro > bairro > município > CEP
    4. Respeitar o limit total
    """

    def __init__(self, repository: IUniversalSearchRepository):
        self._repository = repository

    async def execute(self, dto: UniversalSearchInputDTO) -> UniversalSearchOutputDTO:
        # 1. Detectar se a query parece um CEP (só dígitos, 8 chars)
        is_cep_query = dto.q.replace("-", "").isdigit()

        # 2. Disparar buscas em paralelo
        # Cada busca individual já respeita um limit interno
        # para não sobrecarregar o banco
        import asyncio

        tasks = []
        
        if is_cep_query:
            tasks.append(self._search_cep(dto))
        else:
            tasks.append(self._search_schools(dto))
            tasks.append(self._search_logradouros(dto))
            tasks.append(self._search_bairros(dto))
            tasks.append(self._search_municipios(dto))
            # CEP também se tiver dígitos misturados
            if any(c.isdigit() for c in dto.q):
                tasks.append(self._search_cep(dto))

        all_results = await asyncio.gather(*tasks)

        # 3. Flatten e deduplicar por id
        merged: list[SearchResultItem] = []
        seen_ids: set[str] = set()
        
        for result_list in all_results:
            for item in result_list:
                if item.id not in seen_ids:
                    seen_ids.add(item.id)
                    merged.append(item)

        # 4. Aplicar limit final
        final = merged[:dto.limit]

        return UniversalSearchOutputDTO(
            results=final,
            total=len(final),
            query=dto.q,
        )
```

### 5.1 Priorização implícita

A ordem dos `tasks` define a prioridade. Como fazemos `gather` e iteramos na ordem, os resultados de escola vêm primeiro, depois logradouro, bairro, município, CEP. Isso garante que ao aplicar o `limit`, escolas têm prioridade natural.

**Alternativa considerada**: Score-based ranking. Descartada por complexidade desnecessária neste momento — a prioridade por tipo já atende o requisito do frontend.

---

## 6. Implementação do Repository (MongoDB)

### 6.1 Queries principais

```python
# src/infrastructure/database/repository/mongo_universal_search_repository.py

class MongoUniversalSearchRepository(IUniversalSearchRepository):
    def __init__(
        self,
        escolas_collection,
        municipio_collection,
        bairro_collection,
    ):
        self._escolas = escolas_collection
        self._municipios = municipio_collection
        self._bairros = bairro_collection

    # --- Collation para busca accent/case insensitive ---
    _PT_COLLATION = {"locale": "pt", "strength": 1}
```

#### 6.1.1 Busca de Escolas

```python
async def search_schools(self, q, *, sg_uf=None, municipio_id=None, limit=8):
    query = {"escolaNome": {"$regex": f"^{re.escape(q)}", "$options": "i"}}
    
    if sg_uf:
        query["estadoSigla"] = sg_uf.upper()
    if municipio_id:
        query["$or"] = [
            {"municipioIdIbge": municipio_id},
            {"municipioIdIbge": int(municipio_id)} if municipio_id.isdigit() else {},
        ]

    projection = {
        "escolaIdInep": 1,
        "escolaNome": 1,
        "municipioNome": 1,
        "municipioIdIbge": 1,
        "dependenciaAdm": 1,
        "tipoLocalizacao": 1,
        "localizacao.coordinates": 1,
        "endereco.bairro": 1,
    }

    cursor = self._escolas.find(query, projection).collation(self._PT_COLLATION).limit(limit)
    return await cursor.to_list(length=limit)
```

#### 6.1.2 Busca de Logradouros (Aggregation)

```python
async def search_logradouros(self, q, *, sg_uf=None, municipio_id=None, limit=8):
    match_stage = {
        "endereco.logradouro": {"$regex": f"^{re.escape(q)}", "$options": "i"},
        "localizacao.type": "Point",
    }
    if sg_uf:
        match_stage["estadoSigla"] = sg_uf.upper()
    if municipio_id:
        match_stage["municipioIdIbge"] = municipio_id

    pipeline = [
        {"$match": match_stage},
        {"$group": {
            "_id": {
                "logradouro": "$endereco.logradouro",
                "municipio": "$municipioNome",
                "municipioIdIbge": "$municipioIdIbge",
            },
            "bairros": {"$addToSet": "$endereco.bairro"},
            "avg_lon": {"$avg": {"$arrayElemAt": ["$localizacao.coordinates", 0]}},
            "avg_lat": {"$avg": {"$arrayElemAt": ["$localizacao.coordinates", 1]}},
            "count": {"$sum": 1},
        }},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ]

    return await self._escolas.aggregate(pipeline).to_list(length=limit)
```

#### 6.1.3 Busca por CEP

```python
async def search_by_cep(self, q, *, sg_uf=None, municipio_id=None, limit=8):
    cep_clean = q.replace("-", "").strip()
    query = {"endereco.cep": {"$regex": f"^{re.escape(cep_clean)}"}}
    
    if sg_uf:
        query["estadoSigla"] = sg_uf.upper()
    if municipio_id:
        query["municipioIdIbge"] = municipio_id

    projection = {
        "endereco.cep": 1,
        "endereco.bairro": 1,
        "endereco.logradouro": 1,
        "municipioNome": 1,
        "municipioIdIbge": 1,
        "localizacao.coordinates": 1,
    }

    # Agrupar por CEP para deduplicar
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": "$endereco.cep",
            "bairro": {"$first": "$endereco.bairro"},
            "logradouro": {"$first": "$endereco.logradouro"},
            "municipioNome": {"$first": "$municipioNome"},
            "municipioIdIbge": {"$first": "$municipioIdIbge"},
            "coordinates": {"$first": "$localizacao.coordinates"},
        }},
        {"$limit": limit},
    ]

    return await self._escolas.aggregate(pipeline).to_list(length=limit)
```

#### 6.1.4 Busca de Municípios

```python
async def search_municipios(self, q, *, sg_uf=None, limit=8):
    # Tenta múltiplos campos de nome
    name_regex = {"$regex": f"^{re.escape(q)}", "$options": "i"}
    query = {
        "$or": [
            {"municipio": name_regex},
            {"nm_municipio": name_regex},
            {"municipioNome": name_regex},
        ]
    }
    if sg_uf:
        query = {"$and": [
            query,
            {"$or": [
                {"sg_uf": sg_uf.upper()},
                {"uf": sg_uf.upper()},
                {"estadoSigla": sg_uf.upper()},
            ]}
        ]}

    projection = {
        "co_municipio": 1,
        "municipioIdIbge": 1,
        "municipio_id_ibge": 1,
        "idIbge": 1,
        "municipio": 1,
        "nm_municipio": 1,
        "municipioNome": 1,
        "sg_uf": 1,
        "uf": 1,
        "estadoSigla": 1,
        "socioeconomico.populacao.total": 1,
    }

    return await self._municipios.find(query, projection).limit(limit).to_list(length=limit)
```

#### 6.1.5 Busca de Bairros

```python
async def search_bairros(self, q, *, sg_uf=None, municipio_id=None, limit=8):
    name_regex = {"$regex": f"^{re.escape(q)}", "$options": "i"}
    query = {
        "$or": [
            {"bairro": name_regex},
            {"nm_bairro": name_regex},
            {"nome_area": name_regex},
        ]
    }
    if municipio_id:
        query = {"$and": [
            query,
            {"$or": [
                {"municipioIdIbge": municipio_id},
                {"municipio_id_ibge": municipio_id},
                {"co_municipio": municipio_id},
            ]}
        ]}

    projection = {
        "cd_bairro_ibge": 1,
        "cd_bairro": 1,
        "bairro": 1,
        "nm_bairro": 1,
        "nome_area": 1,
        "municipio": 1,
        "nm_municipio": 1,
        "municipioIdIbge": 1,
        "municipio_id_ibge": 1,
        "co_municipio": 1,
        "centroide": 1,
        "localizacao": 1,
    }

    return await self._bairros.find(query, projection).limit(limit).to_list(length=limit)
```

---

## 7. Índices Necessários

Adicionar em `connect_db.py` → `_ensure_indexes()`:

```python
# --- Índices para busca universal ---

# Prefixo em escolaNome (já coberto parcialmente pelo idx existente)
await schools.create_index(
    [("escolaNome", ASCENDING)],
    name="idx_escolas_nome_busca",
    collation={"locale": "pt", "strength": 1},
    background=True,
)

# Prefixo em endereco.logradouro
await schools.create_index(
    [("endereco.logradouro", ASCENDING)],
    name="idx_escolas_logradouro_busca",
    collation={"locale": "pt", "strength": 1},
    background=True,
)

# CEP para busca por prefixo
await schools.create_index(
    [("endereco.cep", ASCENDING)],
    name="idx_escolas_cep_busca",
    background=True,
)

# Municípios - busca por nome
await municipios.create_index(
    [("municipio", ASCENDING)],
    name="idx_municipio_nome_busca",
    collation={"locale": "pt", "strength": 1},
    background=True,
)

# Bairros - busca por nome
await bairros.create_index(
    [("bairro", ASCENDING)],
    name="idx_bairro_nome_busca",
    collation={"locale": "pt", "strength": 1},
    background=True,
)
```

**Nota sobre collation**: Índices com collation `strength: 1` permitem queries case+accent insensitive usando o índice diretamente (sem scan). A query **deve** usar `.collation()` com os mesmos parâmetros para que o MongoDB use o índice.

---

## 8. Controller e Rota

```python
# src/presentation/http/controller/search/universal_search_controller.py

from fastapi import APIRouter, Query, HTTPException, Depends

router = APIRouter()

@router.get("/busca/universal", response_model=UniversalSearchResponse)
async def universal_search(
    q: str = Query(..., min_length=2, description="Texto de busca (mínimo 2 caracteres)"),
    sg_uf: str | None = Query(None, description="Filtrar por UF"),
    municipio_id: str | None = Query(None, description="Restringir a um município"),
    limit: int = Query(8, ge=1, le=20, description="Máximo de resultados"),
    use_case: UniversalSearchUseCase = Depends(get_universal_search_use_case),
):
    """
    Busca universal — retorna sugestões tipadas com coordenadas.
    
    O parâmetro `q` com min_length=2 já garante HTTP 422 automático
    do FastAPI se < 2 caracteres (equivalente ao 400 solicitado).
    """
    dto = UniversalSearchInputDTO(
        q=q.strip(),
        sg_uf=sg_uf,
        municipio_id=municipio_id,
        limit=limit,
    )

    result = await use_case.execute(dto)

    return UniversalSearchResponse(
        results=[
            SearchResultItemResponse(
                id=item.id,
                kind=item.kind,
                label=item.label,
                subtitle=item.subtitle,
                coordinates=list(item.coordinates),
                municipioIdIbge=item.municipio_id_ibge,
                metadata=item.metadata,
            )
            for item in result.results
        ],
        total=result.total,
        query=result.query,
    )
```

### 8.1 Registro no `main.py`

```python
from src.presentation.http.controller.search.container import container as search_container
from src.presentation.http.controller.search.index import router as search_controller

search_container.wire(modules=[
    "src.presentation.http.controller.search.universal_search_controller",
])

app.include_router(search_controller, prefix="/api/v1", tags=["busca"])
```

---

## 9. DI Container

```python
# src/presentation/http/controller/search/container.py

from dependency_injector import containers, providers
from src.infrastructure.database.config.connect_db import mongodb
from src.infrastructure.database.repository.mongo_universal_search_repository import (
    MongoUniversalSearchRepository,
)
from src.application.search.universal_search.universal_search_use_case import (
    UniversalSearchUseCase,
)


class Container(containers.DeclarativeContainer):

    search_repository = providers.Factory(
        MongoUniversalSearchRepository,
        escolas_collection=providers.Callable(mongodb.get_collection, "escolas"),
        municipio_collection=providers.Callable(mongodb.get_collection, "municipio_indicadores"),
        bairro_collection=providers.Callable(mongodb.get_collection, "bairro_indicadores"),
    )

    universal_search_use_case = providers.Singleton(
        UniversalSearchUseCase,
        repository=search_repository,
    )


container = Container()
```

---

## 10. Questões em Aberto / Trade-offs

| # | Questão | Decisão proposta | Alternativa |
|---|---------|-----------------|-------------|
| 1 | **HTTP 400 vs 422** para `q < 2 chars` | Usar 422 (padrão FastAPI com `Query(min_length=2)`) — semanticamente correto para validação de input | Override manual para retornar 400 se frontend exigir |
| 2 | **Coordenadas de município** | Usar centróide calculado a partir de `setor_indicadores` (avg lat/lon) | Adicionar campo `centroide` na collection `municipio_indicadores` |
| 3 | **Coordenadas de bairro** | Usar campo `centroide` da collection `bairro_indicadores` se existir, senão calcular avg das escolas | Pré-calcular e persistir |
| 4 | **Logradouro ID** | Gerar ID determinístico: `logradouro:{slug}-{municipio_id}` | UUID aleatório (perde idempotência) |
| 5 | **CEP ID** | Usar `cep:{valor_limpo}` | Usar ObjectId da escola |
| 6 | **Bairro ID** | Usar `bairro:{cd_bairro_ibge}` se disponível, senão `bairro:{municipio_id}{hash}` | Apenas nome |
| 7 | **Busca fuzzy** | Não implementar na v1 — prefixo + collation já cobre 90% dos casos | Implementar com `$text` + score ou Atlas Search |
| 8 | **Cache** | Não cachear no backend (resultados dependem de contexto, frontend faz debounce) | Redis com TTL curto (30s) por query+params |
| 9 | **Paralelismo** | `asyncio.gather` para todas as buscas simultâneas | Sequencial com early-return se limit atingido |
| 10 | **Collation nos índices** | Criar índices com collation `pt` strength 1 | Normalizar strings no application layer (como já feito em `_remove_accents`) |

---

## 11. Fluxo de Dados Completo

```
[Frontend]
    │
    ▼ GET /api/v1/busca/universal?q=epitacio&municipio_id=2507507&limit=8
    │
[Controller] ─── valida params (FastAPI Query) ─── monta DTO
    │
    ▼
[UniversalSearchUseCase.execute(dto)]
    │
    ├── asyncio.gather(
    │       repo.search_schools(q, ...),
    │       repo.search_logradouros(q, ...),
    │       repo.search_bairros(q, ...),
    │       repo.search_municipios(q, ...),
    │   )
    │
    ▼
[MongoUniversalSearchRepository]
    │
    ├── escolas.find({escolaNome: /^epitacio/i}).collation(pt).limit(8)
    ├── escolas.aggregate([match logradouro, group, limit])
    ├── bairro_indicadores.find({bairro: /^epitacio/i}).limit(8)
    └── municipio_indicadores.find({municipio: /^epitacio/i}).limit(8)
    │
    ▼
[Use Case] ─── transforma docs → SearchResultItem ─── deduplica ─── aplica limit
    │
    ▼
[Controller] ─── serializa → UniversalSearchResponse (JSON)
    │
    ▼
[Frontend] ─── renderiza dropdown com ícones por kind
```

---

## 12. Checklist de Implementação

- [ ] Criar `src/domain/repository/universal_search_repository.py`
- [ ] Criar `src/application/search/__init__.py`
- [ ] Criar `src/application/search/universal_search/__init__.py`
- [ ] Criar `src/application/search/universal_search/universal_search_dto.py`
- [ ] Criar `src/application/search/universal_search/universal_search_use_case.py`
- [ ] Criar `src/infrastructure/database/repository/mongo_universal_search_repository.py`
- [ ] Criar `src/presentation/http/controller/search/__init__.py`
- [ ] Criar `src/presentation/http/controller/search/index.py`
- [ ] Criar `src/presentation/http/controller/search/container.py`
- [ ] Criar `src/presentation/http/controller/search/callable/__init__.py`
- [ ] Criar `src/presentation/http/controller/search/callable/search_callable.py`
- [ ] Criar `src/presentation/http/controller/search/universal_search_controller.py`
- [ ] Adicionar índices em `connect_db.py`
- [ ] Registrar router em `main.py`
- [ ] Testar com dados reais (performance < 200ms)
