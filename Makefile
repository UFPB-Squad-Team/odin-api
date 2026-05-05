# ─────────────────────────────────────────────────────────────────────────────
#  Odin Backend — Makefile
#  Uso: make <target>
# ─────────────────────────────────────────────────────────────────────────────

# Configurações
PYTHON        := python3
POETRY        := poetry
APP_MODULE    := src.main:app
HOST          := 0.0.0.0
PORT          := 8000
WORKERS       := 1

# Cores para output
RESET  := \033[0m
BOLD   := \033[1m
GREEN  := \033[32m
YELLOW := \033[33m
CYAN   := \033[36m

.DEFAULT_GOAL := help
.PHONY: help install install-dev env dev prod lint format typecheck test test-cov \
        clean docker-build docker-up docker-down docker-logs docker-shell \
        docker-clean check

# ─── Help ─────────────────────────────────────────────────────────────────────

help: ## Mostra esta mensagem de ajuda
	@echo ""
	@echo "$(BOLD)$(CYAN)Odin Backend$(RESET)"
	@echo "────────────────────────────────────────"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ \
		{ printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""

# ─── Setup ────────────────────────────────────────────────────────────────────

install: ## Instala dependências de produção
	$(POETRY) install --only=main

install-dev: ## Instala todas as dependências (incluindo dev)
	$(POETRY) install

env: ## Cria .env a partir do .env.example (não sobrescreve se já existir)
	@if [ -f .env ]; then \
		echo "$(YELLOW)⚠  .env já existe, pulando.$(RESET)"; \
	else \
		cp .env.example .env; \
		echo "$(GREEN)✔  .env criado. Preencha as variáveis antes de rodar.$(RESET)"; \
	fi

# ─── Desenvolvimento ──────────────────────────────────────────────────────────

dev: ## Inicia o servidor em modo desenvolvimento (hot reload)
	$(POETRY) run uvicorn $(APP_MODULE) \
		--host $(HOST) \
		--port $(PORT) \
		--reload

prod: ## Inicia o servidor em modo produção
	$(POETRY) run uvicorn $(APP_MODULE) \
		--host $(HOST) \
		--port $(PORT) \
		--workers $(WORKERS) \
		--no-access-log

# ─── Qualidade de código ──────────────────────────────────────────────────────

lint: ## Verifica estilo com flake8
	$(POETRY) run flake8 src/

format: ## Formata o código com black
	$(POETRY) run black src/

format-check: ## Verifica formatação sem alterar arquivos
	$(POETRY) run black --check src/

typecheck: ## Verifica tipos com mypy
	$(POETRY) run mypy src/

check: lint format-check typecheck ## Roda lint + format-check + typecheck

# ─── Testes ───────────────────────────────────────────────────────────────────

test: ## Roda os testes
	$(POETRY) run pytest

test-cov: ## Roda os testes com relatório de cobertura
	$(POETRY) run pytest --cov=src --cov-report=term-missing --cov-report=html

# ─── Limpeza ──────────────────────────────────────────────────────────────────

clean: ## Remove arquivos temporários e cache
	find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc"       -not -path "./.venv/*" -delete 2>/dev/null || true
	find . -type f -name "*.pyo"       -not -path "./.venv/*" -delete 2>/dev/null || true
	find . -type d -name ".mypy_cache" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache"                       -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov"                             -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage"                           -delete 2>/dev/null || true
	@echo "$(GREEN)✔  Limpeza concluída.$(RESET)"

# ─── Docker ───────────────────────────────────────────────────────────────────

docker-build: ## Build da imagem Docker
	docker compose build

docker-up: ## Sobe os containers em background
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
