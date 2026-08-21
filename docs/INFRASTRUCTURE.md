# Guia de Infraestrutura — Odin API

> Documento de referência para setup, deploy, operação e manutenção do backend Odin.
> Última atualização: Maio 2026

---

## Índice

1. [Visão Geral da Arquitetura](#1-visão-geral-da-arquitetura)
2. [Stack Tecnológica](#2-stack-tecnológica)
3. [Setup Local (Desenvolvimento)](#3-setup-local-desenvolvimento)
4. [Variáveis de Ambiente](#4-variáveis-de-ambiente)
5. [Docker — Build e Runtime](#5-docker--build-e-runtime)
6. [Deploy em Produção](#6-deploy-em-produção)
7. [Gunicorn — Process Manager](#7-gunicorn--process-manager)
8. [Health Checks e Monitoramento](#8-health-checks-e-monitoramento)
9. [Logging e Observabilidade](#9-logging-e-observabilidade)
10. [CI/CD Pipeline](#10-cicd-pipeline)
11. [Segurança](#11-segurança)
12. [Troubleshooting](#12-troubleshooting)
13. [Comandos de Referência Rápida](#13-comandos-de-referência-rápida)

---

## 1. Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Reverse    │  Nginx / Caddy / Cloud LB
                    │  Proxy/LB   │  (TLS termination)
                    └──────┬──────┘
                           │
              ┌────────────▼────────────────┐
              │     Docker Container         │
              │  ┌────────────────────────┐  │
              │  │      Gunicorn          │  │
              │  │  (Process Manager)     │  │
              │  │                        │  │
              │  │  ┌──────┐ ┌──────┐    │  │
              │  │  │Worker│ │Worker│... │  │
              │  │  │(Uvi) │ │(Uvi) │    │  │
              │  │  └──┬───┘ └──┬───┘    │  │
              │  └─────┼────────┼────────┘  │
              └────────┼────────┼───────────┘
                       │        │
              ┌────────▼────────▼───────────┐
              │     MongoDB Atlas            │
              │     (Database)               │
              └─────────────────────────────┘
```


### Fluxo de Request

1. Request chega no reverse proxy (TLS termination, rate limiting)
2. Proxy encaminha para o container Docker na porta configurada
3. Gunicorn distribui entre os workers Uvicorn (round-robin)
4. FastAPI processa o request (validação, DI, use case, repository)
5. Motor/PyMongo executa query assíncrona no MongoDB
6. Response retorna pelo mesmo caminho

---

## 2. Stack Tecnológica

| Componente | Tecnologia | Versão | Propósito |
|---|---|---|---|
| Runtime | Python | 3.12+ | Linguagem principal |
| Framework | FastAPI | 0.115.x | API REST assíncrona |
| ASGI Server | Uvicorn | 0.34.x | Servidor ASGI (workers) |
| Process Manager | Gunicorn | 23.x | Gerenciamento de processos |
| Database Driver | Motor | 3.7.x | MongoDB async driver |
| Validation | Pydantic | 2.10.x | Validação e serialização |
| Config | pydantic-settings | 2.7.x | Configuração via env vars |
| DI | dependency-injector | 4.45.x | Injeção de dependências |
| Package Manager | uv | latest | Gerenciamento de deps (substitui Poetry) |
| Linter/Formatter | Ruff | 0.8.x | Lint + format (substitui black+flake8) |
| Container | Docker | 24+ | Containerização |
| CI/CD | GitHub Actions | — | Integração e deploy contínuo |

---

## 3. Setup Local (Desenvolvimento)

### Pré-requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (package manager)
- Docker e Docker Compose (opcional, para rodar containerizado)
- Acesso a uma instância MongoDB (Atlas ou local)


### Instalação do uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Ou via Homebrew
brew install uv
```

### Setup do Projeto

```bash
# 1. Clone o repositório
git clone <repo-url> && cd odin-api

# 2. Instale as dependências (cria .venv automaticamente)
make install-dev

# 3. Configure as variáveis de ambiente
make env
# Edite o .env com suas credenciais do MongoDB

# 4. Inicie o servidor de desenvolvimento
make dev
```

O servidor estará disponível em `http://localhost:8000` com hot reload ativado.

### Desenvolvimento com Docker

```bash
# Sobe o container com hot reload (monta src/ como volume)
make docker-dev-up

# Para o container
make docker-dev-down
```

---

## 4. Variáveis de Ambiente

Todas as variáveis são carregadas via `pydantic-settings` com validação automática de tipos.

### Variáveis Obrigatórias

| Variável | Tipo | Descrição |
|---|---|---|
| `MONGO_URI` | string | Connection string do MongoDB |
| `DATABASE_NAME` | string | Nome do banco de dados |

### Variáveis Opcionais (com defaults)

| Variável | Tipo | Default | Descrição |
|---|---|---|---|
| `PORT` | int | `8000` | Porta do servidor |
| `ENVIRONMENT` | string | `development` | Ambiente (`development`, `staging`, `production`) |
| `LOG_LEVEL` | string | `info` | Nível de log (`debug`, `info`, `warning`, `error`) |
| `CORS_ALLOWED_ORIGINS` | string | `http://localhost:3000` | Origens CORS (separadas por vírgula) |
| `MAX_PAGE_SIZE` | int | `500` | Tamanho máximo de página na paginação |
| `MAX_OFFSET_RECORDS` | int | `50000` | Offset máximo permitido |
| `USE_ESTIMATED_TOTAL` | bool | `true` | Usar contagem estimada para listas sem filtro |
| `AGGREGATION_CACHE_TTL_SECONDS` | int | `300` | TTL (segundos) do cache em memória de agregações |
| `AGGREGATION_CACHE_MAX_KEYS` | int | `512` | Máximo de chaves no cache em memória de agregações |
| `WEB_CONCURRENCY` | int | `4` | Número de workers Gunicorn |
| `GUNICORN_TIMEOUT` | int | `120` | Timeout dos workers (segundos) |
| `MAX_REQUESTS` | int | `1000` | Requests antes de reciclar worker |


### Configuração por Ambiente

```bash
# ─── Desenvolvimento ─────────────────────────────────────────
ENVIRONMENT=development
LOG_LEVEL=debug
CORS_ALLOWED_ORIGINS="http://localhost:3000"
WEB_CONCURRENCY=1

# ─── Staging ─────────────────────────────────────────────────
ENVIRONMENT=staging
LOG_LEVEL=info
CORS_ALLOWED_ORIGINS="https://staging.odin.app"
WEB_CONCURRENCY=2

# ─── Produção ────────────────────────────────────────────────
ENVIRONMENT=production
LOG_LEVEL=warning
CORS_ALLOWED_ORIGINS="https://odin.app,https://www.odin.app"
WEB_CONCURRENCY=4
```

> **Importante:** Em produção, a documentação Swagger (`/docs` e `/redoc`) é automaticamente desabilitada.

---

## 5. Docker — Build e Runtime

### Estratégia Multi-stage

O Dockerfile usa **2 stages** para minimizar o tamanho da imagem final:

```
┌─────────────────────────────────────┐
│  Stage 1: builder                   │
│  - Instala uv                       │
│  - Resolve e instala dependências   │
│  - Compila bytecode (.pyc)          │
│  - Resultado: .venv completo        │
└──────────────────┬──────────────────┘
                   │ COPY .venv
┌──────────────────▼──────────────────┐
│  Stage 2: runtime                   │
│  - python:3.12-slim (mínimo)        │
│  - Sem uv, sem pip, sem build tools │
│  - Usuário não-root (odin)          │
│  - Apenas .venv + src + gunicorn    │
└─────────────────────────────────────┘
```

### Build da Imagem

```bash
# Build padrão
docker build -t odin-api:latest .

# Build com cache (recomendado em CI)
docker buildx build \
  --cache-from type=gha \
  --cache-to type=gha,mode=max \
  -t odin-api:latest .

# Build multi-plataforma (para deploy em ARM e x86)
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t odin-api:latest .
```

### Tamanho Esperado da Imagem

| Stage | Tamanho Aproximado |
|---|---|
| python:3.12-slim base | ~150MB |
| + dependências Python | ~80MB |
| **Total (runtime)** | **~230MB** |

### Executar o Container

```bash
# Execução direta
docker run -d \
  --name odin-api \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  odin-api:latest

# Via Docker Compose (recomendado)
make docker-up
```


---

## 6. Deploy em Produção

### Opção A: VPS / VM (DigitalOcean, AWS EC2, Hetzner)

#### 1. Preparar o servidor

```bash
# Instalar Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Instalar Docker Compose plugin
sudo apt-get install docker-compose-plugin
```

#### 2. Configurar a aplicação

```bash
# Clone o repositório
git clone <repo-url> /opt/odin-api
cd /opt/odin-api

# Configurar variáveis de ambiente
cp .env.example .env
nano .env  # Preencher com valores de produção
```

#### 3. Deploy

```bash
# Build e start
docker compose up -d --build

# Verificar status
docker compose ps
docker compose logs -f
```

#### 4. Reverse Proxy (Caddy — recomendado)

```bash
# /etc/caddy/Caddyfile
api.odin.app {
    reverse_proxy localhost:8000
    
    # Headers de segurança
    header {
        X-Content-Type-Options nosniff
        X-Frame-Options DENY
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
    }
    
    # Rate limiting (requer plugin)
    # rate_limit {remote.ip} 100r/m
}
```

Caddy gerencia TLS automaticamente via Let's Encrypt.

#### 5. Systemd Service (alternativa sem Docker)

```ini
# /etc/systemd/system/odin-api.service
[Unit]
Description=Odin API
After=network.target

[Service]
Type=notify
User=odin
Group=odin
WorkingDirectory=/opt/odin-api
Environment="PATH=/opt/odin-api/.venv/bin"
EnvironmentFile=/opt/odin-api/.env
ExecStart=/opt/odin-api/.venv/bin/gunicorn src.main:app -c gunicorn.conf.py
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5
KillMode=mixed
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable odin-api
sudo systemctl start odin-api
sudo systemctl status odin-api
```


### Opção B: Platform as a Service (Railway, Render, Fly.io)

#### Railway

```bash
# Instalar CLI
npm install -g @railway/cli

# Login e deploy
railway login
railway init
railway up
```

Railway detecta automaticamente o Dockerfile e faz deploy.

#### Fly.io

```bash
# Instalar CLI
curl -L https://fly.io/install.sh | sh

# Criar app
fly launch --name odin-api --region gru

# Deploy
fly deploy
```

### Opção C: Kubernetes (para escala)

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: odin-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: odin-api
  template:
    metadata:
      labels:
        app: odin-api
    spec:
      containers:
        - name: odin-api
          image: ghcr.io/<org>/odin-api:latest
          ports:
            - containerPort: 8000
          envFrom:
            - secretRef:
                name: odin-api-secrets
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "1000m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
```

---

## 7. Gunicorn — Process Manager

### Por que Gunicorn?

Uvicorn sozinho é single-process. Em produção, precisamos:
- **Múltiplos workers** para utilizar todos os CPU cores
- **Graceful restart** sem downtime
- **Reciclagem de workers** para prevenir memory leaks
- **Supervisão de processos** (reinicia workers que morrem)

### Configuração (`gunicorn.conf.py`)

| Parâmetro | Valor | Explicação |
|---|---|---|
| `workers` | `min(2*CPU+1, WEB_CONCURRENCY)` | Workers por CPU, limitado pelo env var |
| `worker_class` | `uvicorn.workers.UvicornWorker` | Workers ASGI assíncronos |
| `worker_tmp_dir` | `/dev/shm` | Heartbeat via shared memory (rápido em containers) |
| `timeout` | `120s` | Tempo máximo para processar um request |
| `graceful_timeout` | `30s` | Tempo para worker finalizar requests em andamento |
| `keepalive` | `5s` | Keep-alive de conexões HTTP |
| `max_requests` | `1000` | Recicla worker após N requests |
| `max_requests_jitter` | `50` | Randomiza reciclagem (evita thundering herd) |
| `preload_app` | `true` | Carrega app antes de fork (economiza memória via COW) |


### Tuning de Workers

```
┌─────────────────────────────────────────────────────────────┐
│  Regra geral para apps I/O bound (como esta API):           │
│                                                             │
│  workers = (2 × CPU cores) + 1                              │
│                                                             │
│  Exemplos:                                                  │
│  - 1 vCPU  → 2-3 workers                                   │
│  - 2 vCPU  → 4-5 workers                                   │
│  - 4 vCPU  → 8-9 workers (cap em 8 para containers)        │
│                                                             │
│  ⚠ Cada worker consome ~80-120MB de RAM                     │
│  ⚠ Em containers com limite de memória, reduza workers      │
└─────────────────────────────────────────────────────────────┘
```

### Sinais do Gunicorn

| Sinal | Efeito |
|---|---|
| `SIGHUP` | Graceful reload (recarrega config e workers) |
| `SIGTERM` | Graceful shutdown (finaliza requests em andamento) |
| `SIGINT` | Quick shutdown |
| `SIGUSR2` | Upgrade in-place (zero-downtime deploy) |
| `SIGTTIN` | Incrementa 1 worker |
| `SIGTTOU` | Decrementa 1 worker |

```bash
# Reload graceful (dentro do container)
docker compose exec api kill -HUP 1

# Adicionar worker dinamicamente
docker compose exec api kill -TTIN 1
```

---

## 8. Health Checks e Monitoramento

### Endpoints

| Endpoint | Propósito | Uso |
|---|---|---|
| `GET /health` | **Liveness probe** — processo está vivo | Docker HEALTHCHECK, Load Balancer |
| `GET /health/ready` | **Readiness probe** — pode receber tráfego | Kubernetes readiness, deploy verification |

### Respostas

```json
// GET /health → 200
{ "status": "healthy" }

// GET /health/ready → 200 (tudo ok)
{
  "status": "ready",
  "checks": {
    "database": "ok"
  }
}

// GET /health/ready → 503 (problema)
{
  "status": "not_ready",
  "checks": {
    "database": "failing"
  }
}
```

### Docker HEALTHCHECK

O container tem health check nativo configurado:
- **Intervalo:** 30 segundos
- **Timeout:** 10 segundos
- **Start period:** 15 segundos (tempo para startup)
- **Retries:** 3 falhas antes de marcar como unhealthy

```bash
# Verificar status de saúde do container
docker inspect --format='{{.State.Health.Status}}' odin-api
# Resultado: healthy | unhealthy | starting
```

### Monitoramento Externo

Recomendações para monitoramento em produção:

| Ferramenta | Propósito | Integração |
|---|---|---|
| **UptimeRobot** / **Better Uptime** | Uptime monitoring | Pinga `/health` a cada 60s |
| **Sentry** | Error tracking | SDK Python (adicionar como dependência) |
| **Datadog** / **New Relic** | APM + Métricas | Agent no container |
| **Grafana + Prometheus** | Métricas custom | Exportar via `/metrics` endpoint |


---

## 9. Logging e Observabilidade

### Formato de Log

A aplicação usa logging estruturado com o formato:

```
2026-05-29 12:30:45 | INFO     | src.main | Starting Odin API | port=8000 | env=production
2026-05-29 12:30:46 | INFO     | src.infrastructure.database.config.connect_db | MongoDB connected successfully
2026-05-29 12:30:46 | INFO     | src.main | Application ready to serve requests
```

### Níveis de Log

| Nível | Quando usar | Env recomendado |
|---|---|---|
| `DEBUG` | Detalhes de execução, queries, payloads | Desenvolvimento |
| `INFO` | Eventos normais (startup, connections) | Staging |
| `WARNING` | Situações inesperadas mas recuperáveis | Produção |
| `ERROR` | Falhas que precisam de atenção | Todos |
| `CRITICAL` | Falhas que impedem o funcionamento | Todos |

### Configuração por Ambiente

```bash
# Desenvolvimento — ver tudo
LOG_LEVEL=debug

# Staging — eventos normais
LOG_LEVEL=info

# Produção — apenas problemas
LOG_LEVEL=warning
```

### Gunicorn Access Log

O Gunicorn registra cada request com o formato:

```
192.168.1.1 - - [29/May/2026:12:30:45 +0000] "GET /api/v1/schools HTTP/1.1" 200 1234 "-" "Mozilla/5.0" 45000
```

Campos: `IP - - [timestamp] "method path protocol" status bytes "referer" "user-agent" duration_microseconds`

### Rotação de Logs (Docker)

O `docker-compose.yml` configura rotação automática:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"   # Máximo 10MB por arquivo
    max-file: "3"     # Mantém 3 arquivos (30MB total)
```

### Acessar Logs

```bash
# Logs em tempo real
docker compose logs -f api

# Últimas 100 linhas
docker compose logs --tail=100 api

# Filtrar por nível (grep)
docker compose logs api | grep "ERROR"

# Logs com timestamp
docker compose logs -t api
```

### Integração com Serviços de Log

#### Opção 1: Docker log driver para CloudWatch

```yaml
# docker-compose.yml (override para AWS)
services:
  api:
    logging:
      driver: awslogs
      options:
        awslogs-group: /odin/api
        awslogs-region: sa-east-1
        awslogs-stream-prefix: odin-api
```

#### Opção 2: Fluentd / Fluent Bit (sidecar)

```yaml
services:
  api:
    logging:
      driver: fluentd
      options:
        fluentd-address: localhost:24224
        tag: odin.api

  fluentbit:
    image: fluent/fluent-bit:latest
    volumes:
      - ./fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf
    ports:
      - "24224:24224"
```

#### Opção 3: Loki + Grafana (self-hosted)

```yaml
services:
  api:
    logging:
      driver: loki
      options:
        loki-url: "http://loki:3100/loki/api/v1/push"
        loki-batch-size: "400"
```


---

## 10. CI/CD Pipeline

### Visão Geral

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Push /  │────▶│  Quality │────▶│  Tests   │────▶│  Docker  │
│  PR      │     │  Check   │     │          │     │  Build   │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                       │                                  │
                       │ ruff check                       │ build + push
                       │ ruff format --check              │ (apenas main)
                       │ mypy                             │
                       ▼                                  ▼
                  ┌──────────┐                     ┌──────────┐
                  │  Fail?   │                     │  GHCR    │
                  │  Block   │                     │  Registry│
                  │  PR      │                     └──────────┘
                  └──────────┘
```

### Workflow: CI (`ci.yml`)

**Trigger:** Push ou PR para `main` ou `development`

| Job | Dependência | O que faz |
|---|---|---|
| `quality` | — | Lint, format check, type check |
| `test` | `quality` | Roda pytest |
| `docker` | `quality` | Build da imagem (valida Dockerfile) |

### Workflow: Deploy (`deploy.yml`)

**Trigger:** Push para `main` ou tag `v*`

1. Build multi-arch (amd64 + arm64)
2. Push para GitHub Container Registry (`ghcr.io`)
3. Tags automáticas: branch name, semver, SHA

### Tags de Imagem

| Evento | Tags geradas |
|---|---|
| Push para `main` | `main`, `sha-abc1234` |
| Tag `v1.2.3` | `1.2.3`, `1.2`, `sha-abc1234` |

### Usar a Imagem do Registry

```bash
# Pull da imagem
docker pull ghcr.io/<org>/odin-api:main

# Rodar
docker run -d \
  --name odin-api \
  -p 8000:8000 \
  --env-file .env \
  ghcr.io/<org>/odin-api:main
```

### Secrets Necessários no GitHub

| Secret | Propósito |
|---|---|
| `GITHUB_TOKEN` | Automático — push para GHCR |
| `DISCORD_WEBHOOK_URL` | Notificações de PR no Discord |

---

## 11. Segurança

### Práticas Implementadas

| Prática | Implementação |
|---|---|
| Usuário não-root | Container roda como `odin:odin` |
| Imagem mínima | `python:3.12-slim` sem ferramentas extras |
| Sem shell de build | Stage final não tem `uv`, `pip`, `gcc` |
| CORS restritivo | Apenas origens explícitas, métodos específicos |
| Docs desabilitados em prod | `/docs` e `/redoc` retornam 404 |
| Dependências pinadas | Versões exatas no `pyproject.toml` |
| Validação de input | Pydantic valida todos os payloads |
| Health check sem info sensível | Não expõe detalhes internos |

### Checklist de Deploy

```
□ CORS_ALLOWED_ORIGINS configurado com domínios reais (sem wildcard)
□ ENVIRONMENT=production
□ LOG_LEVEL=warning (não expor debug info)
□ MONGO_URI usa TLS (mongodb+srv://)
□ Reverse proxy com TLS (HTTPS)
□ Rate limiting configurado no proxy
□ Firewall permite apenas portas 80/443
□ Secrets não estão no código (usar env vars ou secret manager)
□ Imagem Docker vem do registry (não build local em prod)
```


### Hardening Adicional (Recomendado)

```bash
# 1. Limitar capabilities do container
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE odin-api

# 2. Read-only filesystem
docker run --read-only --tmpfs /tmp odin-api

# 3. Sem privilege escalation
docker run --security-opt=no-new-privileges odin-api
```

### MongoDB Security

- Usar MongoDB Atlas com IP whitelist
- Habilitar autenticação (SCRAM-SHA-256)
- Usar connection string com TLS (`mongodb+srv://`)
- Criar usuário com permissões mínimas (readWrite no database específico)
- Habilitar audit log no Atlas

---

## 12. Troubleshooting

### Container não inicia

```bash
# Ver logs de startup
docker compose logs api

# Verificar se .env está correto
docker compose config

# Entrar no container para debug
docker compose run --rm api bash
```

### Erros comuns

| Erro | Causa | Solução |
|---|---|---|
| `Failed to connect to database` | MONGO_URI inválida ou rede bloqueada | Verificar connection string e IP whitelist |
| `Missing required environment variable` | Variável obrigatória não definida | Verificar `.env` tem MONGO_URI e DATABASE_NAME |
| `Worker timeout` | Request demorou mais que GUNICORN_TIMEOUT | Aumentar timeout ou otimizar query |
| `[ERROR] Connection pool exhausted` | Muitas conexões simultâneas | Aumentar pool size no Motor ou reduzir workers |
| Container `unhealthy` | Health check falhando | Verificar se app está respondendo em `/health` |

### Performance

```bash
# Ver uso de recursos do container
docker stats odin-api

# Ver quantos workers estão ativos
docker compose exec api ps aux | grep gunicorn

# Testar latência do health check
curl -w "\nTime: %{time_total}s\n" http://localhost:8000/health
```

### Restart de Emergência

```bash
# Restart graceful (sem downtime se tiver múltiplos workers)
docker compose exec api kill -HUP 1

# Restart completo do container
docker compose restart api

# Nuclear option — rebuild e restart
docker compose down && docker compose up -d --build
```

---

## 13. Comandos de Referência Rápida

### Desenvolvimento

```bash
make install-dev          # Instalar dependências
make dev                  # Servidor com hot reload
make lint                 # Verificar código
make format               # Formatar código
make check                # Lint + format + typecheck
make test                 # Rodar testes
make clean                # Limpar cache
```

### Docker

```bash
make docker-build         # Build da imagem
make docker-up            # Subir em produção
make docker-down          # Parar containers
make docker-logs          # Ver logs (follow)
make docker-shell         # Shell no container
make docker-clean         # Remover tudo (volumes + imagens)
make docker-dev-up        # Dev com Docker (hot reload)
make docker-dev-down      # Parar dev Docker
```

### Operações em Produção

```bash
# Deploy (pull nova imagem e restart)
docker compose pull && docker compose up -d

# Rollback (voltar para versão anterior)
docker compose down
docker compose up -d --no-build  # usa imagem em cache

# Scale (se não usar deploy.resources)
docker compose up -d --scale api=3

# Ver health status
docker inspect --format='{{.State.Health.Status}}' odin-api

# Backup de logs antes de limpar
docker compose logs api > backup-$(date +%Y%m%d).log
```

### uv (Package Manager)

```bash
uv sync                   # Instalar deps do lockfile
uv sync --no-dev          # Apenas produção
uv lock                   # Atualizar lockfile
uv add <package>          # Adicionar dependência
uv add --dev <package>    # Adicionar dep de desenvolvimento
uv remove <package>       # Remover dependência
uv run <command>          # Executar no venv
```

---

## Apêndice: Diagrama de Arquivos de Infraestrutura

```
odin-api/
├── .github/
│   └── workflows/
│       ├── ci.yml                 # Pipeline de CI (lint, test, docker build)
│       ├── deploy.yml             # Pipeline de deploy (build + push GHCR)
│       └── discord_notifier.yml   # Notificações de PR
├── src/
│   ├── main.py                    # Entrypoint FastAPI
│   └── presentation/
│       └── http/
│           └── controller/
│               └── health.py      # Health check endpoints
├── .dockerignore                  # Exclusões do Docker build context
├── .env.example                   # Template de variáveis de ambiente
├── .gitignore                     # Exclusões do Git
├── docker-compose.yml             # Compose de produção
├── docker-compose.dev.yml         # Compose de desenvolvimento
├── Dockerfile                     # Multi-stage production build
├── gunicorn.conf.py               # Configuração do Gunicorn
├── Makefile                       # Comandos de automação
├── pyproject.toml                 # Configuração do projeto e dependências
└── uv.lock                        # Lockfile para builds reproduzíveis
```
