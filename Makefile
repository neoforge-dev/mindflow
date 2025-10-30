.PHONY: help install test seed lint format clean

# Default target
help:
	@echo "MindFlow - Available Commands:"
	@echo ""
	@echo "  make install     Install all dependencies with uv"
	@echo "  make test        Run all tests"
	@echo "  make test-v      Run tests with verbose output"
	@echo "  make test-cov    Run tests with coverage report"
	@echo "  make seed        Seed test data (47 tasks)"
	@echo "  make lint        Run linter (ruff)"
	@echo "  make lint-fix    Fix linting issues automatically"
	@echo "  make format      Format code with ruff"
	@echo "  make typecheck   Run type checker (mypy)"
	@echo "  make clean       Remove generated files and caches"
	@echo "  make fresh       Clean and reinstall everything"
	@echo ""

# Install dependencies
install:
	uv sync --all-extras

# Run tests
test:
	uv run pytest

test-v:
	uv run pytest -v

test-fast:
	uv run pytest -n auto

test-cov:
	uv run pytest --cov --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

test-edge:
	uv run pytest -m edge_case

# Seed test data
seed:
	uv run python -m tests.seed_data

# Code quality
lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .

format:
	uv run ruff format .

typecheck:
	uv run mypy tests/

# Clean up
clean:
	rm -rf .venv
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf .pytest_cache
	rm -rf tests/__pycache__
	rm -rf **/__pycache__
	rm -f uv.lock
	@echo "Cleaned up generated files"

# Fresh start
fresh: clean install
	@echo "Fresh installation complete!"
