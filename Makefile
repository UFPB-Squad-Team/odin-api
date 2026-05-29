# ─────────────────────────────────────────────────────────────────────────────
#  Odin Backend — Makefile
#  Uso: make <target>
# ─────────────────────────────────────────────────────────────────────────────

# Configurações
APP_MODULE    := src.main:app
HOST          := 0.0.0.0
PORT          := 8000

# Cores para output
RESET  := \033[0m
BOLD   := \033[1m
GREEN  := \033[32m
YELLOW := \033[33m
CYAN   := \033[36m
RED    := \033[31m

.DEFAULT_GOAL := help
.PHONY: help install install-dev env dev prod lint format typecheck test test-cov \
        clean docker-build docker-up docker-down docker-logs docker-shell \
        docker-clean check lock

# ─── Help ─────────────────────────────────────────────────────────────────────

help: ## Mostra esta mensagem de ajuda
	@echo ""
	@echo "$(BOLD)$(CYAN)⚡ Odin Backend$(RESET)"
	@echo "────────────────────────────────────────"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ \
		{ printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""

# ─── Setup ────────────────────────────────────────────────────────────────────

install: ## Instala dependências de produção
	uv sync --no-dev

install-dev: ## Instala todas as dependências (incluindo dev)
	uv sync

lock: ## Gera/atualiza o uv.lock
	uv lock

env: ## Cria .env a partir do .env.example (não sobrescreve se já existir)
	@if [ -f .env ]; then \
		echo "$(YELLOW)⚠  .env já existe, pulando.$(RESET)"; \
	else \
		cp .env.example .env; \
		echo "$(GREEN)✔  .env criado. Preencha as variáveis antes de rodar.$(RESET)"; \
	fi

# ─── Desenvolvimento ──────────────────────────────────────────────────────────

dev: ## Inicia o servidor em modo desenvolvimento (hot reload)
	uv run uvicorn $(APP_MODULE) \
		--host $(HOST) \
		--port $(PORT) \
		--reload

prod: ## Inicia o servidor em modo produção (Gunicorn + Uvicorn workers)
	uv run gunicorn $(APP_MODULE) -c gunicorn.conf.py

# ─── Qualidade de código ──────────────────────────────────────────────────────

lint: ## Verifica estilo com ruff
	uv run ruff check src/

fix: ## Corrige automaticamente formatação e lint
	uv run ruff format src/
	uv run ruff check src/ --fix

format: ## Formata o código com ruff
	uv run ruff format src/

format-check: ## Verifica formatação sem alterar arquivos
	uv run ruff format --check src/

typecheck: ## Verifica tipos com mypy
	uv run mypy src/

check: lint format-check typecheck ## Roda lint + format-check + typecheck

# ─── Testes ───────────────────────────────────────────────────────────────────

test: ## Roda os testes
	uv run pytest

test-cov: ## Roda os testes com relatório de cobertura
	uv run pytest --cov=src --cov-report=term-missing --cov-report=html

# ─── Limpeza ──────────────────────────────────────────────────────────────────

clean: ## Remove arquivos temporários e cache
	find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc"       -not -path "./.venv/*" -delete 2>/dev/null || true
	find . -type d -name ".mypy_cache" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache"                       -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov"                             -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage"                           -delete 2>/dev/null || true
	@echo "$(GREEN)✔  Limpeza concluída.$(RESET)"

# ─── Docker ───────────────────────────────────────────────────────────────────

docker-build: ## Build da imagem Docker (produção)
	docker compose build

docker-up: ## Sobe os containers em background (produção)
	docker compose up -d

docker-down: ## Para e remove os containers
	docker compose down

docker-logs: ## Exibe logs dos containers (follow)
	docker compose logs -f

docker-shell: ## Abre shell dentro do container da API
	docker compose exec api bash

docker-clean: ## Remove containers, volumes e imagens do projeto
	@echo "$(YELLOW)⚠  Isso remove containers, volumes e imagens do projeto.$(RESET)"
	docker compose down --volumes --rmi local

# ─── Docker Dev ───────────────────────────────────────────────────────────────

docker-dev-up: ## Sobe containers de desenvolvimento (com hot reload)
	docker compose -f docker-compose.dev.yml up --build

docker-dev-down: ## Para containers de desenvolvimento
	docker compose -f docker-compose.dev.yml down
