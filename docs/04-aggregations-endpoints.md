# Documentação dos Endpoints de Agregações

## Visão Geral

O endpoint de cidades retorna **GeoJSON FeatureCollection**. O endpoint de bairros retorna o **contrato bruto do documento Mongo**, com `_id` e `geometria`. Existem dois níveis de agregação:

### 1. **Cities** - Agregação por Município
### 2. **Neighborhoods** - Agregação por Bairro

---

## 📍 Endpoint: `GET /api/v1/aggregations/cities`

### Descrição
Retorna indicadores agregados **por município** em formato GeoJSON.

### Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-----------|-----------|
| `municipioIdIbge` | string | ❌ Não | Código IBGE de 7 dígitos. Se informado, retorna dados apenas daquele município. Se omitido, retorna todos os municípios. |

### Comportamento

#### Sem `municipioIdIbge`:
- Retorna **TODOS os municípios** da collection `municipio_indicadores`
- Resposta pode ser grande (centenas de cidades)

#### Com `municipioIdIbge`:
- Primeiro tenta buscar em `municipio_indicadores` (fonte primária)
- Se não encontrado, agregra dados de `setor_indicadores` (fallback)

### Exemplo de Requisição
```bash
# Todos os municípios
GET /api/v1/aggregations/cities

# Município específico
GET /api/v1/aggregations/cities?municipioIdIbge=2504009
```

### Exemplo de Resposta
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "mongoId": "669e211325157cf0f20312a59",
      "id": "2504009",
      "geometry": {
        "type": "Point",
        "coordinates": [-35.8811, -7.2263]
      },
      "properties": {
        "municipioIdIbge": "2504009",
        "co_municipio": "2504009",
        "municipio": "Campina Grande",
        "uf": "PB",
        "total_escolas": 152,
        "total_alunos": 42530,
        "avg_ideb": 4.8,
        "pct_com_biblioteca": 45.3,
        "pct_com_internet": 98.5,
        "pct_com_lab_informatica": 67.2,
        "pct_sem_acessibilidade": 12.5,
        "source": "municipio_indicadores"
      }
    }
  ]
}
```

### Campos Explicados

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `mongoId` | string\|null | ID do documento no MongoDB (se existir em bairros_indicadores) |
| `id` | string | Identificador GeoJSON (código IBGE do município) |
| `geometry` | GeoJSON | Centróide do município em [longitude, latitude] |
| `properties.municipioIdIbge` | string | Código IBGE do município |
| `properties.total_escolas` | int | Número total de escolas |
| `properties.total_alunos` | int | Número total de alunos matriculados |
| `properties.avg_ideb` | float\|null | Índice de Desenvolvimento da Educação Básica (média) |
| `properties.pct_com_biblioteca` | float | Percentual de escolas com biblioteca |
| `properties.pct_com_internet` | float | Percentual de escolas com internet |
| `properties.pct_com_lab_informatica` | float | Percentual de escolas com lab de informática |
| `properties.pct_sem_acessibilidade` | float | Percentual de escolas SEM acessibilidade |
| `properties.source` | string | Fonte dos dados: `municipio_indicadores` ou `setor_indicadores` |

---

## 📍 Endpoint: `GET /api/v1/aggregations/neighborhoods`

### Descrição
Retorna indicadores agregados **por bairro** de um município específico seguindo o contrato do documento Mongo.

### Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-----------|-----------|
| `municipio_id` | string | ✅ **Sim** | Código IBGE do município (7 dígitos). OBRIGATÓRIO. |
| `bairro` | string | ❌ Não | Nome do bairro para filtrar. Busca case-insensitive em: `bairro`, `nm_bairro`, `nome_area`. |

### Comportamento

#### Busca em Cascata (Fallback):

1. **Primeiro:** Tenta buscar em `bairros_indicadores` (fonte primária)
  - Procura por `municipioIdIbge` / `municipio_id_ibge` / `co_municipio` / `idIbge`
  - Se `bairro` for informado, filtra também por nome

2. **Se não encontrar:** Agrega dados de `setor_indicadores` (fallback)
   - Agrupa setores censitários por bairro
   - Consolida métricas (somas, médias)

### Exemplo de Requisição
```bash
# Todos os bairros de um município
GET /api/v1/aggregations/neighborhoods?municipio_id=2504009

# Bairro específico (case-insensitive)
GET /api/v1/aggregations/neighborhoods?municipio_id=2504009&bairro=Malvinas

# Busca parcial
GET /api/v1/aggregations/neighborhoods?municipio_id=2504009&bairro=centro
```

### Exemplo de Resposta
```json
[
  {
    "_id": "69e211325157cf0f20312a59",
    "municipio": "Campina Grande",
    "bairro": "Acácio Figueiredo",
    "cd_bairro_ibge": "2504009049",
    "geometria": {
      "type": "MultiPolygon",
      "coordinates": [[[[-35.87, -7.22], [-35.86, -7.22], [-35.86, -7.23], [-35.87, -7.23], [-35.87, -7.22]]]]
    },
    "municipioIdIbge": "2504009",
    "pct_com_biblioteca": 50,
    "pct_com_internet": 100,
    "pct_com_lab_informatica": 0,
    "pct_sem_acessibilidade": 0,
    "sg_uf": "PB",
    "total_escolas": 2,
    "total_matriculas": 1651,
    "tem_bairro_official": true
  }
]
```

### Campos Explicados

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `_id` | string\|null | ID do documento no MongoDB |
| `geometria` | object | Geometria original do bairro ou ponto agregado do setor |
| `municipioIdIbge` | string | Código IBGE do município |
| `bairro` | string | Nome do bairro |
| `cd_bairro_ibge` | string\|null | Código IBGE do bairro, quando existir |
| `total_matriculas` | int | Total de matrículas agregadas |
| `tem_bairro_official` | bool\|null | Indica se o bairro veio da collection oficial ou do fallback |
| Demais campos | - | Indicadores percentuais do documento original |

---

## 🔄 Fluxo de Dados

```
GET /api/v1/aggregations/neighborhoods?municipioIdIbge=2504009
        ↓
   ┌────────────────────────────────────────┐
   │ Controller (validação de params)      │
   └────────────────────┬───────────────────┘
                        ↓
   ┌────────────────────────────────────────┐
  │ Use Case (GetNeighborhoodAggregations) │
   └────────────────────┬───────────────────┘
                        ↓
   ┌────────────────────────────────────────┐
   │ Repository (MongoDB query)             │
   │ 1. Try: bairro_collection              │
   │ 2. Fallback: setor aggregation         │
   └────────────────────┬───────────────────┘
                        ↓
   ┌────────────────────────────────────────┐
  │ Mapper (Doc → Response contract)       │
   └────────────────────┬───────────────────┘
                        ↓
   ┌────────────────────────────────────────┐
  │ List of neighborhood documents         │
   └────────────────────────────────────────┘
```

---

## 📊 Estrutura das Collections MongoDB

### `municipio_indicadores`
```javascript
{
  "_id": ObjectId(),
  "municipioIdIbge": "2504009",
  "co_municipio": "2504009",
  "nm_municipio": "Campina Grande",
  "sg_uf": "PB",
  "total_escolas": 152,
  "total_alunos": 42530,
  "avg_ideb": 4.8,
  // ... mais campos
  "geometria" ou "centroide": { "coordinates": [lon, lat] }
}
```

### `bairros_indicadores`
```javascript
{
  "_id": ObjectId(),
  "municipioIdIbge": "2504009",
  "bairro": "Malvinas",
  "nm_bairro": "Malvinas",
  "municipio": "Campina Grande",
  "sg_uf": "PB",
  "total_escolas": 13,
  "total_matriculas": 4124,
  "pct_com_biblioteca": 66.67,
  "tem_bairro_official": true,
  // ... mais campos
  "geometria": { "coordinates": [[...]] }
}
```

### `setor_indicadores` (Setores Censitários)
```javascript
{
  "_id": ObjectId(),
  "co_municipio": "2504009",
  "bairro" ou "nome_area": "Malvinas",
  "total_escolas": 2,
  "total_alunos": 340,
  // ... agregado por setores
  "centroide": { "coordinates": [lon, lat] }
}
```

---

## ⚠️ Casos Especiais

### 1. Coordinates `[0.0, 0.0]`
Se o documento não tiver geometria/centróide, retorna coordenadas `[0.0, 0.0]`. Isso indica **dados incompletos** naquela collection.

### 2. `mongoId: null`
Quando dados vêm de `setor_indicadores` (fallback), `mongoId` é `null` porque não existe documento único consolidado em `bairros_indicadores`.

### 3. `tem_bairro_official: false`
Indica que é um agrupamento de setores censitários, **não um bairro oficial** da prefeitura. Use com cautela para análises administrativas.

---

## 🧪 Teste Rápido

```bash
# Teste 1: Todos os municípios
curl -s "http://localhost:8000/api/v1/aggregations/cities" | jq '.features | length'

# Teste 2: Município específico
curl -s "http://localhost:8000/api/v1/aggregations/cities?municipioIdIbge=2504009" | jq '.features[0].properties'

# Teste 3: Bairros de um município
curl -s "http://localhost:8000/api/v1/aggregations/neighborhoods?municipioIdIbge=2504009" | jq '.features | length'

# Teste 4: Filtro por bairro
curl -s "http://localhost:8000/api/v1/aggregations/neighborhoods?municipioIdIbge=2504009&bairro=Malvinas" | jq '.features[0].properties.bairro'
```
