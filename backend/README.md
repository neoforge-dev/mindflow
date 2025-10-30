# MindFlow Backend

FastAPI backend with PostgreSQL for the MindFlow AI task manager.

## Quick Start

### Prerequisites

- [uv](https://github.com/astral-sh/uv) (replaces pip/venv)
- Docker (for test database)
- Python 3.11+

### Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv
```

### Setup & Run

```bash
# One-command setup
make quick-start

# Or step by step:
make install-dev   # Install dependencies
make db-up         # Start test database
make test          # Run tests
make run           # Start dev server
```

## Development Commands

### Common Workflows

```bash
make help          # Show all available commands
make test          # Run tests with coverage
make test-fast     # Run tests without coverage
make lint          # Check code style
make format        # Format code
make check         # Run all checks (lint + format + test)
```

### Database Management

```bash
make db-up         # Start PostgreSQL test database
make db-down       # Stop test database
make db-reset      # Reset database (clean slate)
make db-shell      # Open PostgreSQL shell
make db-logs       # Show database logs
```

### Testing

```bash
make test          # All tests with coverage
make test-unit     # Unit tests only
make test-integration  # Integration tests only
make coverage      # Generate HTML coverage report
```

### Code Quality

```bash
make lint          # Run ruff linter
make lint-fix      # Auto-fix linting issues
make format        # Format code with ruff
make format-check  # Check formatting without changes
```

### Development

```bash
make run           # Run FastAPI dev server (hot reload)
make run-prod      # Run production server (4 workers)
make shell         # Python shell with app context
```

### Cleanup

```bash
make clean         # Remove caches and generated files
make clean-all     # Clean everything including database
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py              # Settings & environment
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py        # Async SQLAlchemy setup
│   │   ├── models.py          # User, Task, AuditLog models
│   │   └── crud.py            # Database operations
│   └── schemas/
│       ├── __init__.py
│       └── task.py            # Pydantic validation
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Pytest fixtures
│   └── integration/
│       └── test_database.py   # Database tests
├── pyproject.toml             # Dependencies & config
├── Makefile                   # Development commands
└── .python-version            # Python version (3.11)
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required variables:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:54320/mindflow_test
SECRET_KEY=your-secret-key-min-32-chars
ENVIRONMENT=development
```

## Dependencies

Managed with `uv` - see `pyproject.toml`:

**Production**:
- FastAPI 0.104+
- SQLAlchemy 2.0+ (async)
- PostgreSQL (asyncpg)
- Pydantic 2.5+

**Development**:
- pytest + pytest-asyncio
- ruff (linting & formatting)
- pytest-cov (coverage)

## Testing

Tests use **PostgreSQL** (not SQLite) to match production:

```bash
# Start test database
make db-up

# Run tests
make test

# View coverage
make coverage
```

### Test Coverage

Current: **75.43%** (database layer >90%)

```
Name                Coverage
app/db/crud.py      90%
app/db/models.py    100%
app/db/database.py  78%
```

## Code Quality

### Linting & Formatting with Ruff

```bash
# Check code
make lint

# Auto-fix issues
make lint-fix

# Format code
make format
```

Configuration in `pyproject.toml`:
- Line length: 100
- Python 3.11+ syntax
- Import sorting (isort)
- Bugbear checks

### Pre-commit Checks

Before committing:

```bash
make check  # Runs: lint + format-check + test
```

## Deployment

### DigitalOcean Droplet

```bash
# On server
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

See `../docs/DEPLOYMENT.md` for full deployment guide.

## CI/CD

GitHub Actions workflow:

```bash
make ci  # Runs: install + lint + format-check + test
```

## Troubleshooting

### Database connection issues

```bash
# Check database is running
docker ps | grep mindflow-test-db

# View logs
make db-logs

# Reset database
make db-reset
```

### Import errors

```bash
# Reinstall dependencies
make install-dev

# Verify installation
uv pip list
```

### Test failures

```bash
# Run with verbose output
uv run pytest -vv

# Run specific test
uv run pytest tests/integration/test_database.py::TestTaskCRUD::test_create_task_returns_task_with_id -vv
```

## Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [uv Docs](https://github.com/astral-sh/uv)
- [Ruff Docs](https://docs.astral.sh/ruff/)

## License

MIT
