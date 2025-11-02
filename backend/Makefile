.PHONY: help install install-dev test test-watch lint format check clean run migrate db-up db-down db-reset coverage mcp-server mcp-test

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)MindFlow Backend - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

# Installation
install: ## Install production dependencies using uv
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	uv sync --no-dev

install-dev: ## Install all dependencies including dev tools
	@echo "$(BLUE)Installing all dependencies (including dev)...$(NC)"
	uv sync

# Testing
test: ## Run all tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	uv run pytest

test-fast: ## Run tests without coverage (faster)
	@echo "$(BLUE)Running tests (no coverage)...$(NC)"
	uv run pytest --no-cov

test-unit: ## Run only unit tests
	@echo "$(BLUE)Running unit tests...$(NC)"
	uv run pytest -m unit

test-integration: ## Run only integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	uv run pytest -m integration

test-watch: ## Run tests in watch mode (requires pytest-watch)
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	uv run ptw -- --no-cov

coverage: ## Generate coverage report and open in browser
	@echo "$(BLUE)Generating coverage report...$(NC)"
	uv run pytest --cov-report=html
	@echo "$(GREEN)Opening coverage report...$(NC)"
	open htmlcov/index.html || xdg-open htmlcov/index.html

# Linting and Formatting
lint: ## Run ruff linter
	@echo "$(BLUE)Running ruff linter...$(NC)"
	uv run ruff check .

lint-fix: ## Run ruff linter and fix issues
	@echo "$(BLUE)Running ruff linter with auto-fix...$(NC)"
	uv run ruff check --fix .

format: ## Format code with ruff
	@echo "$(BLUE)Formatting code with ruff...$(NC)"
	uv run ruff format .

format-check: ## Check code formatting without changes
	@echo "$(BLUE)Checking code formatting...$(NC)"
	uv run ruff format --check .

check: lint format-check test ## Run all checks (lint, format, test)
	@echo "$(GREEN)✅ All checks passed!$(NC)"

# Database
db-up: ## Start PostgreSQL test database (Docker)
	@echo "$(BLUE)Starting PostgreSQL test database...$(NC)"
	docker run -d \
		--name mindflow-test-db \
		-e POSTGRES_PASSWORD=postgres \
		-e POSTGRES_DB=mindflow_test \
		-p 54320:5432 \
		postgres:15-alpine
	@echo "$(GREEN)Waiting for database to be ready...$(NC)"
	@sleep 3
	@docker exec mindflow-test-db pg_isready -U postgres && echo "$(GREEN)✅ Database ready$(NC)" || echo "$(RED)❌ Database not ready$(NC)"

db-down: ## Stop and remove test database
	@echo "$(YELLOW)Stopping test database...$(NC)"
	docker stop mindflow-test-db 2>/dev/null || true
	docker rm mindflow-test-db 2>/dev/null || true
	@echo "$(GREEN)✅ Test database removed$(NC)"

db-reset: db-down db-up ## Reset test database (stop, remove, start fresh)
	@echo "$(GREEN)✅ Test database reset complete$(NC)"

db-logs: ## Show database logs
	@docker logs mindflow-test-db -f

db-shell: ## Open PostgreSQL shell
	@docker exec -it mindflow-test-db psql -U postgres -d mindflow_test

# Development
run: ## Run the FastAPI development server
	@echo "$(BLUE)Starting FastAPI development server...$(NC)"
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Run the FastAPI production server
	@echo "$(BLUE)Starting FastAPI production server...$(NC)"
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

shell: ## Open Python shell with app context
	@uv run python -i -c "from app.db.database import *; from app.db.models import *; from app.db.crud import *"

# MCP Server
mcp-server: ## Run the MCP server for ChatGPT Apps SDK integration
	@echo "$(BLUE)Starting MCP server...$(NC)"
	@echo "$(GREEN)MCP Server will run on $(YELLOW)http://0.0.0.0:8001$(NC)"
	@echo "$(GREEN)FastAPI backend: $(YELLOW)$(shell grep -E '^api_base_url' .env 2>/dev/null || echo 'http://localhost:8000')$(NC)"
	uv run fastmcp run mcp_server.main:mcp --port 8001 --host 0.0.0.0

mcp-test: ## Run MCP server tests
	@echo "$(BLUE)Running MCP server tests...$(NC)"
	uv run pytest tests/mcp_server/ -v --no-cov

# Migrations (for Phase 3+)
migrate: ## Run database migrations (alembic)
	@echo "$(BLUE)Running database migrations...$(NC)"
	uv run alembic upgrade head

migrate-create: ## Create a new migration
	@read -p "Migration name: " name; \
	uv run alembic revision --autogenerate -m "$$name"

migrate-rollback: ## Rollback last migration
	@echo "$(YELLOW)Rolling back last migration...$(NC)"
	uv run alembic downgrade -1

# Cleanup
clean: ## Remove generated files and caches
	@echo "$(YELLOW)Cleaning up...$(NC)"
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

clean-all: clean db-down ## Clean everything including test database
	@echo "$(GREEN)✅ Full cleanup complete$(NC)"

# Deployment helpers
build: ## Build the project
	@echo "$(BLUE)Building project...$(NC)"
	uv build

lock: ## Update uv.lock file
	@echo "$(BLUE)Updating uv.lock...$(NC)"
	uv lock

# Quick start
quick-start: install-dev db-up test ## Quick start: install deps, start db, run tests
	@echo "$(GREEN)✅ Quick start complete! Ready to develop.$(NC)"

# CI/CD
ci: install-dev lint format-check test ## Run CI checks
	@echo "$(GREEN)✅ CI checks passed!$(NC)"
