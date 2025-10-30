# MindFlow – AI-First Task Manager

[![Status](https://img.shields.io/badge/status-Phase%202%20Complete-brightgreen)]()
[![Backend](https://img.shields.io/badge/backend-FastAPI%20%2B%20PostgreSQL-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

> **Natural language task management powered by GPT-4 + FastAPI + PostgreSQL**

MindFlow is an AI-first task manager that combines **Custom GPT** (Actions) with a **FastAPI backend** and **PostgreSQL database** for intelligent task prioritization through conversation.

---

## 🚀 Current Status: Phase 2 Complete

**Database Layer**: ✅ Production-Ready
- AsyncIO SQLAlchemy with PostgreSQL 15
- Connection pooling (10 persistent + 5 overflow)
- Multi-user isolation with user_id validation
- Complete CRUD operations with transaction management
- 19 integration tests passing (>90% coverage)
- Modern tooling: uv + ruff + Makefile

**Next**: Phase 3 - API Endpoints (4-5 hours)

---

## Quick Start

### Backend Setup (Modern Stack)

**Prerequisites**:
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- Docker (for PostgreSQL test database)
- Python 3.11+

**One-command setup**:
```bash
cd backend
make quick-start
```

This will:
1. Install all dependencies with uv
2. Start PostgreSQL test database (Docker)
3. Run 19 integration tests
4. Verify >90% code coverage

**Development commands**:
```bash
make help          # Show all available commands
make test          # Run tests with coverage
make lint          # Check code quality
make format        # Format code with ruff
make db-up         # Start test database
make run           # Start FastAPI dev server (Phase 3+)
```

**Manual setup** (step by step):
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
cd backend
uv sync

# Start test database
make db-up

# Run tests
make test

# See coverage report
make coverage
```

---

## Project Overview

**Goal**: Enable users to manage tasks using natural language while maintaining transparent, explainable AI recommendations.

**Tech Stack** (Updated):
- **Frontend**: Custom GPT with Actions (OpenAI function calling)
- **Backend**: FastAPI (Python 3.11+) with async/await
- **Database**: PostgreSQL 15 (async with asyncpg driver)
- **Intelligence**: GPT-4 + deterministic scoring algorithm
- **Deployment**: DigitalOcean Droplet (backend) + Cloudflare Pages (frontend)

**Key Features**:
- 🎯 Ask "What should I do next?" → Get intelligently ranked task with reasoning
- ✍️ Create/update tasks conversationally (no forms)
- 📊 Real-time database persistence with PostgreSQL
- 🔍 Full audit trail of all operations
- 🧮 Explainable relevance scores (not ML black box)
- 🚀 Production-ready: connection pooling, transactions, multi-user isolation

---

## Architecture

### Current Architecture (Phase 2)

```
┌─────────────────────────────────────────────────────────┐
│                    USER (Natural Language)              │
│          "What should I do next?"                       │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│               CUSTOM GPT (Intent Recognition)           │
│  • Parses user intent                                   │
│  • Calls API via Actions (function calling)            │
│  • Returns natural language response                   │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS (JSON)
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
    /create          /best-task       /complete
    /update          /snooze          /query
        │                │                │
        └────────────────┼────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│         FASTAPI BACKEND (REST API Layer)                │
│  • Async request handling (uvicorn)                    │
│  • Pydantic validation                                 │
│  • Relevance scoring engine                            │
│  • JWT authentication (Phase 4)                        │
│  • Audit logging                                       │
└────────────────────────┬────────────────────────────────┘
                         │ AsyncPG Driver
                         ▼
┌─────────────────────────────────────────────────────────┐
│         POSTGRESQL 15 (Database Layer) ✅                │
│  • Users table (authentication)                         │
│  • Tasks table (with scoring fields)                    │
│  • UserPreferences table (scoring weights)              │
│  • AuditLogs table (operations tracking)                │
│  • Connection pooling (10 + 5 overflow)                 │
│  • Composite indexes for performance                    │
│  • CASCADE deletes for data integrity                   │
└─────────────────────────────────────────────────────────┘
         │
         ▼
    ┌──────────────────────────────────────┐
    │  RELEVANCE SCORING (Deterministic)   │
    │  score = 0.40×priority               │
    │        + 0.35×urgency                │
    │        + 0.15×context                │
    │        + 0.10×momentum               │
    └──────────────────────────────────────┘
```

### Why This Stack?

| Component | Rationale |
|-----------|-----------|
| **Custom GPT** | Natural language interface, built-in function calling, no custom UI needed |
| **FastAPI** | Async performance, automatic API docs, type safety, modern Python |
| **PostgreSQL** | ACID compliance, rich indexing, battle-tested, JSON support (JSONB) |
| **AsyncPG** | Fastest Python PostgreSQL driver, native async/await |
| **uv** | 10-100x faster than pip, reproducible builds, modern Python tooling |
| **Ruff** | 10-100x faster than pylint, auto-formatting, comprehensive linting |
| **Deterministic Scoring** | Explainable (not ML black box), customizable weights, debuggable logic |

---

## Data Model

### Database Schema (PostgreSQL)

#### `users` Table
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | Unique identifier |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | User email (login) |
| `password_hash` | VARCHAR(255) | NOT NULL | Hashed password |
| `full_name` | VARCHAR(255) | NULL | Display name |
| `plan` | VARCHAR(50) | DEFAULT 'free' | Subscription tier |
| `is_active` | BOOLEAN | DEFAULT true | Account status |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Registration time |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last modification |

**Indexes**: `idx_users_email` (unique)

#### `tasks` Table
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | Unique identifier |
| `user_id` | UUID | FK users(id) ON DELETE CASCADE | Owner |
| `title` | VARCHAR(256) | NOT NULL | Task description |
| `description` | TEXT | NULL | Detailed notes |
| `status` | VARCHAR(50) | DEFAULT 'pending' | pending, in_progress, completed, snoozed |
| `priority` | INTEGER | DEFAULT 3, CHECK (1-5) | Urgency level |
| `due_date` | TIMESTAMP | NULL | Deadline |
| `snoozed_until` | TIMESTAMP | NULL | Hidden until |
| `completed_at` | TIMESTAMP | NULL | Completion time |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Creation time |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last modification |
| `effort_estimate_minutes` | INTEGER | NULL | For impact/effort scoring |
| `tags` | VARCHAR(500) | NULL | Comma-separated: "morning,urgent" |

**Indexes**:
- `idx_tasks_user_status` (user_id, status)
- `idx_tasks_user_due` (user_id, due_date)
- `idx_tasks_snoozed_until` (snoozed_until)

#### `user_preferences` Table
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `user_id` | UUID | FK users(id) UNIQUE | One per user |
| `weight_urgency` | INTEGER | DEFAULT 40 | Scoring weight (0-100) |
| `weight_priority` | INTEGER | DEFAULT 35 | Scoring weight (0-100) |
| `weight_impact` | INTEGER | DEFAULT 15 | Scoring weight (0-100) |
| `weight_effort` | INTEGER | DEFAULT 10 | Scoring weight (0-100) |
| `timezone` | VARCHAR(50) | DEFAULT 'UTC' | User timezone |
| `work_start_time` | TIME | DEFAULT '09:00' | Focus hours start |
| `work_end_time` | TIME | DEFAULT '17:00' | Focus hours end |
| `enable_habit_learning` | BOOLEAN | DEFAULT true | AI personalization |

#### `audit_logs` Table
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `timestamp` | TIMESTAMP | DEFAULT NOW(), NOT NULL | When |
| `user_id` | UUID | FK users(id) ON DELETE SET NULL | Who |
| `action` | VARCHAR(100) | NOT NULL | CREATE_TASK, GET_BEST_TASK, etc. |
| `resource_id` | UUID | NULL | Task ID if applicable |
| `result` | VARCHAR(20) | NOT NULL, CHECK (success/error) | Outcome |
| `error_message` | TEXT | NULL | Error details |
| `request_duration_ms` | INTEGER | NULL | Performance tracking |

**Indexes**:
- `idx_audit_user_timestamp` (user_id, timestamp DESC)
- `idx_audit_action` (action)
- `idx_audit_errors` (result) WHERE result = 'error'

---

## API Endpoints

### Status

**Phase 2 (Complete)**: ✅ Database layer with CRUD operations
**Phase 3 (Next)**: 🚧 FastAPI REST endpoints (4-5 hours)

### Planned Endpoints

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/health` | GET | Health check | 🚧 Phase 3 |
| `/api/tasks` | POST | Create task | 🚧 Phase 3 |
| `/api/tasks` | GET | List tasks | 🚧 Phase 3 |
| `/api/tasks/best` | GET | Get best task to work on | 🚧 Phase 3 |
| `/api/tasks/{id}` | GET | Get specific task | 🚧 Phase 3 |
| `/api/tasks/{id}` | PUT | Update task | 🚧 Phase 3 |
| `/api/tasks/{id}` | DELETE | Delete task | 🚧 Phase 3 |
| `/api/auth/register` | POST | Register new user | 🚧 Phase 4 |
| `/api/auth/login` | POST | Login and get JWT | 🚧 Phase 4 |

**Database Layer (Phase 2 - Complete)**:
- ✅ `TaskCRUD.create()` - Create task with transaction management
- ✅ `TaskCRUD.get_by_id()` - Retrieve with user validation
- ✅ `TaskCRUD.list_by_user()` - List with optional status filter
- ✅ `TaskCRUD.update()` - Update with error handling
- ✅ `TaskCRUD.delete()` - Delete with ownership validation
- ✅ `TaskCRUD.get_pending_tasks()` - Get actionable tasks (excludes completed/snoozed)

---

## Testing

### Phase 2 Test Coverage

**Test Suite**: 19 integration tests
**Coverage**: 75.86% overall, **>90% database layer**

**Test Categories**:
- **Database Connection** (2 tests): Engine connectivity, session creation
- **Models** (4 tests): User/Task creation, cascade deletes, audit logs
- **CRUD Operations** (11 tests): Create, read, update, delete with transactions
- **Error Handling** (2 tests): Nonexistent resources, multi-tenancy isolation

**Run tests**:
```bash
cd backend
make test          # All tests with coverage
make test-fast     # Skip coverage (faster)
make test-unit     # Unit tests only
make test-integration  # Integration tests only
make coverage      # HTML coverage report
```

**Test Database**:
- Uses PostgreSQL 15 (not SQLite) to match production
- Docker container on port 54320
- Automatic setup/teardown with `make db-up` / `make db-down`

---

## Development Workflow

### Common Commands

```bash
# Development
make help          # Show all available commands
make install-dev   # Install dependencies with uv
make test          # Run tests with coverage
make lint          # Check code style with ruff
make format        # Auto-format code
make check         # Run all checks (lint + format + test)

# Database
make db-up         # Start PostgreSQL test database
make db-down       # Stop test database
make db-reset      # Reset database (clean slate)
make db-shell      # Open PostgreSQL shell
make db-logs       # Show database logs

# Deployment (Phase 3+)
make run           # Run FastAPI dev server
make run-prod      # Run production server (4 workers)
```

### Making Changes

```bash
# Create feature branch
git checkout -b feature/api-endpoints

# Make changes, test locally
make test
make lint

# Commit (tests must pass)
git add .
git commit -m "feat: add REST API endpoints"
git push origin feature/api-endpoints
```

---

## Phase Roadmap

### ✅ Phase 1: Prototype (Complete)
- Google Apps Script backend
- Google Sheets database
- Custom GPT integration
- Deterministic scoring algorithm
- [Live Demo](https://chatgpt.com/g/g-69035fdcdd648191807929b189684451-mindflow)
- [Video Walkthrough](https://www.loom.com/share/e29f24d461c94396aebe039ef77fb9b7)

### ✅ Phase 2: Database Layer (Complete)
- **Duration**: 4 hours
- **Status**: ✅ Production-Ready
- AsyncIO SQLAlchemy with PostgreSQL 15
- Connection pooling (10 persistent + 5 overflow)
- User, Task, UserPreferences, AuditLog models
- Complete CRUD operations with transactions
- Multi-user isolation verified
- 19 integration tests passing (>90% coverage)
- Modern tooling: uv + ruff + Makefile
- **Deliverables**:
  - ✅ `app/config.py` - Environment configuration
  - ✅ `app/db/database.py` - Async engine + pooling
  - ✅ `app/db/models.py` - SQLAlchemy models
  - ✅ `app/db/crud.py` - Database operations
  - ✅ `app/schemas/task.py` - Pydantic validation
  - ✅ `tests/conftest.py` - Pytest fixtures
  - ✅ `tests/integration/test_database.py` - Integration tests
  - ✅ `pyproject.toml` - Modern dependencies
  - ✅ `Makefile` - Development commands
  - ✅ `README.md` - Comprehensive docs

### 🚧 Phase 3: API Endpoints (Next - 4-5 hours)
- FastAPI REST endpoints
- Request/response validation
- Error handling middleware
- `/api/tasks` CRUD operations
- `/api/tasks/best` scoring endpoint
- OpenAPI documentation
- 15-20 API endpoint tests
- **Deployment**: DigitalOcean Droplet
  - Ubuntu 22.04 LTS
  - Nginx reverse proxy
  - SSL via Let's Encrypt
  - Systemd service

### 🔮 Phase 4: Authentication (5-6 hours)
- JWT token generation
- Password hashing (bcrypt)
- `/api/auth/register` endpoint
- `/api/auth/login` endpoint
- Authentication middleware
- Protected routes
- User session management

### 🔮 Phase 5: Production Hardening (6-8 hours)
- Rate limiting (60 req/min per user)
- Input sanitization
- CORS configuration
- Structured logging (JSON)
- Error monitoring (Sentry)
- Health check endpoint
- Database migrations (Alembic)
- CI/CD pipeline (GitHub Actions)

### 🔮 Phase 6: Frontend Dashboard (Optional)
- LIT web components
- TypeScript
- Real-time task updates
- Drag-and-drop prioritization
- **Deployment**: Cloudflare Pages
  - Static hosting
  - CDN + DDoS protection
  - Free SSL

---

## Deployment Architecture

### Backend: DigitalOcean Droplet

**Specs** (recommended):
- Ubuntu 22.04 LTS
- 2 GB RAM / 1 vCPU (Basic - $12/month)
- Or 4 GB RAM / 2 vCPU (for higher traffic - $24/month)

**Database Options**:
1. **Same Droplet**: PostgreSQL installed on app server (cheaper, simpler)
2. **Managed Database**: DigitalOcean Managed PostgreSQL ($15/month, auto-backups)

**Stack**:
- FastAPI + Uvicorn (4 workers)
- PostgreSQL 15
- Nginx (reverse proxy)
- Systemd (process management)
- Let's Encrypt (free SSL)

**Total Cost**: ~$12-27/month

### Frontend: Cloudflare Pages

**For LIT Dashboard** (optional):
- Static hosting (free tier)
- Global CDN
- Free SSL
- DDoS protection
- Edge caching

**Total Cost**: $0/month

### Primary UI: ChatGPT Custom GPT

**No hosting needed**:
- OpenAI handles all infrastructure
- Update Actions schema with API endpoint
- Configure CORS in FastAPI
- No additional cost

---

## Documentation

### Quick Links

- **Backend README**: [backend/README.md](./backend/README.md) - Development guide
- **Architecture**: [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) - System design
- **Implementation**: [docs/IMPLEMENTATION.md](./docs/IMPLEMENTATION.md) - Code examples
- **Deployment**: [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md) - Production setup
- **Product Vision**: [docs/PRODUCT.md](./docs/PRODUCT.md) - Roadmap & strategy
- **Phase 2 Plan**: [docs/PHASE2-PLAN-V2.md](./docs/PHASE2-PLAN-V2.md) - Database implementation

### Live Demo (Phase 1 Prototype)

- **Custom GPT**: [Try MindFlow](https://chatgpt.com/g/g-69035fdcdd648191807929b189684451-mindflow)
- **Video Demo**: [5-minute walkthrough](https://www.loom.com/share/e29f24d461c94396aebe039ef77fb9b7)

---

## Migration from GAS/Sheets

**Status**: Phase 2 (Database) complete, Phase 3 (API) ready to implement

**What Changed**:
- ❌ Google Apps Script → ✅ FastAPI (Python 3.11+)
- ❌ Google Sheets → ✅ PostgreSQL 15
- ❌ Synchronous → ✅ Async/await throughout
- ✅ Custom GPT integration (unchanged)
- ✅ Scoring algorithm (unchanged)

**Data Migration**:
- Not needed (clean slate for production)
- Phase 1 remains functional as prototype
- Custom GPT will be updated to point to new API (Phase 3)

---

## Troubleshooting

### Backend Won't Start

**Check**:
1. Database connection: `docker ps | grep mindflow-test-db`
2. Environment variables: `cat .env` (if exists)
3. Dependencies: `uv pip list | grep fastapi`

**Fix**:
```bash
# Reinstall dependencies
make install-dev

# Reset database
make db-reset

# Run with verbose logging
make test -v
```

### Database Connection Failed

**Docker container not running**:
```bash
# Check container status
docker ps -a | grep mindflow-test-db

# Start container
make db-up

# View logs
make db-logs
```

**Wrong port**:
- Test database uses port 54320 (not default 5432)
- Check `TEST_DATABASE_URL` in tests/conftest.py
- OrbStack may be using port 5432

### Tests Failing

**Run with verbose output**:
```bash
make test-fast  # Skip coverage for speed
uv run pytest -vv  # Very verbose
uv run pytest tests/integration/test_database.py::TestTaskCRUD::test_create_task_returns_task_with_id -vv  # Specific test
```

**Coverage below 90%**:
- Phase 2 database layer: **>90%** ✅
- Overall: 75.86% (schemas not tested yet - Phase 3)

---

## Contributing

This is a production-focused project. Contributions welcome for:
- **Bug fixes**: Critical issues, edge cases
- **Documentation**: Improvements, examples, guides
- **Test coverage**: Additional test cases
- **Performance**: Optimizations with benchmarks
- **Security**: Hardening, vulnerability fixes

**Not accepting**:
- Major architectural changes (scope already defined)
- ML/AI model integration (deterministic scoring is intentional)
- Feature requests outside roadmap

**Code Standards**:
- Python: Follow PEP 8, type hints required
- Formatting: Use `make format` (ruff)
- Linting: Use `make lint` (ruff)
- Tests: `make test` must pass before commit
- Commits: Conventional commits format

---

## License

MIT License - see [LICENSE](./LICENSE) for details.

---

## Acknowledgments

Built as a demonstration of modern AI-first architecture:
- **OpenAI Custom GPTs** - Natural language interface
- **FastAPI** - Modern async Python framework
- **PostgreSQL** - Battle-tested relational database
- **AsyncPG** - High-performance async driver
- **Deterministic scoring** - Explainable AI recommendations
- **Modern tooling** - uv (fast deps) + ruff (fast linting)

---

## Support

- **Documentation**: [docs/](./docs/)
- **Issues**: GitHub Issues
- **Backend Guide**: [backend/README.md](./backend/README.md)

---

**Status**: Phase 2 Complete ✅ | **Next**: Phase 3 - API Endpoints 🚧

**Questions?** See [backend/README.md](./backend/README.md) for detailed setup instructions.
