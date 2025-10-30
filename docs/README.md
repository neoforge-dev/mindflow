# MindFlow Documentation

**Version**: 2.0.0
**Last Updated**: 2025-10-30
**Status**: Phase 2 Complete - Database Layer Production-Ready

---

## Quick Navigation

| Document | Purpose | Audience |
|----------|---------|----------|
| **[ARCHITECTURE.md](./ARCHITECTURE.md)** | System design, tech stack, data flow | Engineers, architects |
| **[IMPLEMENTATION.md](./IMPLEMENTATION.md)** | Code examples, setup guide | Developers |
| **[DEPLOYMENT.md](./DEPLOYMENT.md)** | DigitalOcean deployment, production setup | DevOps, engineers |
| **[PRODUCT.md](./PRODUCT.md)** | Roadmap, business model, vision | Product managers, founders |
| **[PHASE2-PLAN-V2.md](./PHASE2-PLAN-V2.md)** | Database implementation plan (completed) | Engineers |

---

## What is MindFlow?

**MindFlow** is an AI-first task manager that replaces traditional UI forms with natural conversation. Instead of clicking through menus, users talk to ChatGPT about their work, and the system intelligently suggests what to do next.

### Core Features

- **Natural Language Interface**: "Add blog post about FastAPI, due Friday"
- **Intelligent Prioritization**: AI suggests best task based on deadline, priority, effort
- **ChatGPT Integration**: Works as a Custom GPT (no app switching)
- **Transparent Reasoning**: "Recommended because: due today, high priority"
- **Production Database**: PostgreSQL 15 with async/await performance
- **Modern Tooling**: uv (fast deps) + ruff (fast linting) + Makefile (easy commands)

---

## Getting Started

### For Developers

**Quick Start** (5 minutes):

```bash
# Clone repository
git clone https://github.com/yourusername/mindflow.git
cd mindflow/backend

# One-command setup (installs deps, starts DB, runs tests)
make quick-start
```

**This will**:
1. Install dependencies with uv (10-100x faster than pip)
2. Start PostgreSQL test database (Docker)
3. Run 19 integration tests
4. Verify >90% code coverage on database layer

**Next Steps**:
1. Read [IMPLEMENTATION.md](./IMPLEMENTATION.md) for detailed code examples
2. See [ARCHITECTURE.md](./ARCHITECTURE.md) for system design
3. Deploy to production using [DEPLOYMENT.md](./DEPLOYMENT.md)

### For Product Managers

**Start Here**:
1. Read [PRODUCT.md](./PRODUCT.md) for vision and roadmap
2. Review [ARCHITECTURE.md](./ARCHITECTURE.md) for technical constraints
3. See deployment timeline in [DEPLOYMENT.md](./DEPLOYMENT.md)

### For Users

**Live Prototype**: [Try MindFlow Custom GPT](https://chatgpt.com/g/g-69035fdcdd648191807929b189684451-mindflow)

**Watch 5-Minute Demo**: [Loom Video Walkthrough](https://www.loom.com/share/e29f24d461c94396aebe039ef77fb9b7)

**Production Beta**: Coming Q2 2026 (after Phase 3-5 completion)

---

## Documentation Overview

### 📐 ARCHITECTURE.md

**System design and technical decisions**

- High-level architecture diagram
- Tech stack rationale (FastAPI, PostgreSQL, AsyncPG)
- Data model (database schema)
- API design (planned for Phase 3)
- Task scoring algorithm (relevance formula)
- Security & multi-tenancy
- Performance considerations

**Best For**: Understanding how the system works, making technical decisions

### 💻 IMPLEMENTATION.md

**Copy-paste ready code and setup instructions**

- Quick start guide (one-command setup)
- Backend setup (FastAPI + PostgreSQL)
- Database configuration (Docker or DigitalOcean)
- Modern tooling (uv + ruff + Makefile)
- Testing strategies (19 integration tests)
- Common patterns
- Development workflow

**Best For**: Building the application, debugging issues

### 🚀 DEPLOYMENT.md

**Production deployment to DigitalOcean**

- DigitalOcean Droplet setup (Ubuntu 22.04 LTS)
- PostgreSQL installation (same droplet or managed)
- Nginx reverse proxy configuration
- SSL with Let's Encrypt
- Systemd service setup
- Environment configuration (secrets management)
- Monitoring & logging
- Troubleshooting guide
- Cost breakdown (~$12-27/month)

**Best For**: Deploying to production, maintaining infrastructure

### 📊 PRODUCT.md

**Business vision, roadmap, and strategy**

- Product vision (what we're building and why)
- Current status (Phase 2 complete)
- Transition plan (GAS/Sheets → FastAPI/PostgreSQL)
- Roadmap (Q4 2025 → Q3 2026)
- Business model (pricing, revenue projections)
- Success metrics (KPIs, north star metric)
- Go-to-market strategy

**Best For**: Understanding product direction, planning features

### 📋 PHASE2-PLAN-V2.md

**Database layer implementation plan (COMPLETED)**

- Test-Driven Development approach
- Function & test specifications
- Implementation order (step-by-step)
- Verification checklist
- Time budget (4 hours actual)
- Production deployment notes

**Best For**: Understanding Phase 2 implementation, reference for Phase 3

---

## Current Status: Phase 2 Complete ✅

### What's Been Built

**Database Layer** (Production-Ready):
- ✅ AsyncIO SQLAlchemy with PostgreSQL 15
- ✅ Connection pooling (10 persistent + 5 overflow)
- ✅ User, Task, UserPreferences, AuditLog models
- ✅ Complete CRUD operations with transaction management
- ✅ Multi-user isolation verified
- ✅ 19 integration tests passing (>90% database layer coverage)
- ✅ Modern tooling: uv + ruff + Makefile

**Files Created**:
```
backend/
├── app/
│   ├── config.py              # ✅ Environment configuration
│   ├── db/
│   │   ├── database.py        # ✅ Async engine + pooling
│   │   ├── models.py          # ✅ SQLAlchemy models
│   │   └── crud.py            # ✅ Database operations
│   └── schemas/
│       └── task.py            # ✅ Pydantic validation
├── tests/
│   ├── conftest.py            # ✅ Pytest fixtures
│   └── integration/
│       └── test_database.py   # ✅ 19 integration tests
├── pyproject.toml             # ✅ Modern dependencies (uv)
├── Makefile                   # ✅ Development commands (30+)
└── README.md                  # ✅ Comprehensive docs
```

### What's Next

**Phase 3: API Endpoints** (4-5 hours):
- FastAPI REST endpoints
- `/api/tasks` CRUD operations
- `/api/tasks/best` scoring endpoint
- Request/response validation
- Error handling middleware
- OpenAPI documentation
- 15-20 API endpoint tests
- Deployment to DigitalOcean Droplet

---

## Tech Stack Summary

| Layer | Technology | Why | Status |
|-------|-----------|-----|--------|
| **Frontend** | Custom GPT | Natural conversation interface | ✅ Phase 1 |
| **Optional UI** | LIT + TypeScript (TBD) | Web components, 50KB bundle | 🔮 Phase 6 |
| **API** | FastAPI (Python 3.11+) | Async, type-safe, auto-docs | 🚧 Phase 3 |
| **Database** | PostgreSQL 15 | ACID compliance, rich indexing | ✅ Phase 2 |
| **Driver** | AsyncPG | Fastest Python driver, native async | ✅ Phase 2 |
| **Package Manager** | uv | 10-100x faster than pip | ✅ Phase 2 |
| **Linter/Formatter** | Ruff | 10-100x faster than pylint | ✅ Phase 2 |
| **Backend Host** | DigitalOcean Droplet | Global regions, $12-27/month | 🚧 Phase 3 |
| **Frontend Host** | Cloudflare Pages (optional) | Free tier, global CDN | 🔮 Phase 6 |
| **Auth** | JWT tokens | Stateless, multi-user | 🔮 Phase 4 |
| **Monitoring** | Structured logs + Sentry (TBD) | Error tracking, debugging | 🔮 Phase 5 |

**Total Infrastructure Cost**: ~$12-27/month for production MVP

---

## Project Structure

```
mindflow/
├── backend/                     # ✅ Phase 2 Complete
│   ├── app/
│   │   ├── config.py            # Settings & environment
│   │   ├── db/
│   │   │   ├── database.py      # Async SQLAlchemy engine
│   │   │   ├── models.py        # User, Task, Preferences, AuditLog
│   │   │   └── crud.py          # Database operations
│   │   ├── schemas/
│   │   │   └── task.py          # Pydantic validation
│   │   ├── api/                 # 🚧 Phase 3 - REST endpoints
│   │   ├── services/            # 🚧 Phase 3 - Business logic
│   │   └── middleware/          # 🔮 Phase 4 - JWT auth
│   ├── tests/
│   │   ├── conftest.py          # Pytest fixtures
│   │   └── integration/
│   │       └── test_database.py # 19 integration tests
│   ├── pyproject.toml           # Dependencies (uv)
│   ├── Makefile                 # 30+ development commands
│   └── README.md                # Backend documentation
├── frontend/                    # 🔮 Phase 6 - Optional LIT dashboard
├── docs/
│   ├── README.md                # This file
│   ├── ARCHITECTURE.md          # System design
│   ├── IMPLEMENTATION.md        # Setup guide
│   ├── DEPLOYMENT.md            # DigitalOcean deployment
│   ├── PRODUCT.md               # Business vision
│   └── PHASE2-PLAN-V2.md        # Database implementation (done)
├── src/gas/                     # Phase 1 prototype (archived)
└── README.md                    # Project README
```

---

## Development Workflow

### 1. Local Development

```bash
# Start backend (terminal 1)
cd backend
make quick-start   # Or: make install-dev && make db-up && make test

# Development server (Phase 3+)
make run           # FastAPI with hot reload

# Run tests
make test          # All tests with coverage
make test-fast     # Skip coverage (faster)

# Code quality
make lint          # Check code style
make format        # Auto-format code
make check         # Run all checks (lint + format + test)
```

### 2. Making Changes

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

### 3. Deploying to Production (Phase 3+)

```bash
# SSH to DigitalOcean Droplet
ssh root@your-droplet-ip

# Pull changes
cd /opt/mindflow/backend
git pull origin main

# Install dependencies
uv sync

# Restart service
sudo systemctl restart mindflow

# Check logs
sudo journalctl -u mindflow -f
```

See [DEPLOYMENT.md](./DEPLOYMENT.md) for full deployment guide.

---

## API Endpoints

### Status

**Phase 2 (Complete)**: ✅ Database layer with CRUD operations
**Phase 3 (Next)**: 🚧 FastAPI REST endpoints (4-5 hours)

### Database Layer (Phase 2 - Complete)

**Available Operations**:
- ✅ `TaskCRUD.create(session, data)` - Create task with transaction management
- ✅ `TaskCRUD.get_by_id(session, task_id, user_id)` - Retrieve with user validation
- ✅ `TaskCRUD.list_by_user(session, user_id, status)` - List with optional filter
- ✅ `TaskCRUD.update(session, task_id, user_id, data)` - Update with error handling
- ✅ `TaskCRUD.delete(session, task_id, user_id)` - Delete with ownership validation
- ✅ `TaskCRUD.get_pending_tasks(session, user_id)` - Get actionable tasks

### Planned REST Endpoints (Phase 3)

**Base URL**: `https://your-droplet-ip:8000` (or custom domain)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/health` | GET | Health check | 🚧 Phase 3 |
| `/api/tasks` | POST | Create task | 🚧 Phase 3 |
| `/api/tasks` | GET | List tasks | 🚧 Phase 3 |
| `/api/tasks/best` | GET | Get best task to work on | 🚧 Phase 3 |
| `/api/tasks/{id}` | GET | Get specific task | 🚧 Phase 3 |
| `/api/tasks/{id}` | PUT | Update task | 🚧 Phase 3 |
| `/api/tasks/{id}` | DELETE | Delete task | 🚧 Phase 3 |
| `/api/auth/register` | POST | Register new user | 🔮 Phase 4 |
| `/api/auth/login` | POST | Login and get JWT | 🔮 Phase 4 |

**API Documentation**: `http://localhost:8000/docs` (automatic with FastAPI)

---

## Environment Variables

**Required**:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key (32+ random bytes)

**Optional**:
- `ENVIRONMENT`: `development` or `production`
- `DEBUG`: `true` or `false`

**Example** (`.env`):
```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:54320/mindflow_test

# Security
SECRET_KEY=your-secret-key-min-32-chars-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24

# Environment
ENVIRONMENT=development
DEBUG=true
```

---

## Common Tasks

### Run Tests

```bash
cd backend
make test          # All tests with coverage
make test-fast     # Skip coverage (faster)
make test-unit     # Unit tests only
make test-integration  # Integration tests only
make coverage      # HTML coverage report
```

### Check Code Quality

```bash
make lint          # Check code style
make lint-fix      # Auto-fix linting issues
make format        # Format code with ruff
make format-check  # Check formatting without changes
make check         # Run all checks (lint + format + test)
```

### Manage Database

```bash
make db-up         # Start PostgreSQL test database
make db-down       # Stop test database
make db-reset      # Reset database (clean slate)
make db-shell      # Open PostgreSQL shell
make db-logs       # Show database logs
```

### View API Documentation (Phase 3+)

```bash
# Start server
make run

# Open browser
open http://localhost:8000/docs
```

---

## Troubleshooting

### Backend Won't Start

**Check**:
1. Database connection: `docker ps | grep mindflow-test-db`
2. Environment variables: `cat .env`
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
- Check `TEST_DATABASE_URL` in `tests/conftest.py`
- OrbStack may be using port 5432

### Tests Failing

**Run with verbose output**:
```bash
make test-fast  # Skip coverage for speed
uv run pytest -vv  # Very verbose
uv run pytest tests/integration/test_database.py::TestTaskCRUD::test_create_task_returns_task_with_id -vv  # Specific test
```

**Import errors**:
```bash
# Reinstall dependencies
make install-dev

# Verify installation
uv pip list
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

### 🚧 Phase 3: API Endpoints (Next - 4-5 hours)
- FastAPI REST endpoints
- Request/response validation
- Error handling middleware
- `/api/tasks` CRUD operations
- `/api/tasks/best` scoring endpoint
- OpenAPI documentation
- 15-20 API endpoint tests
- Deployment to DigitalOcean Droplet

### 🔮 Phase 4: Authentication (5-6 hours)
- JWT token generation
- Password hashing (bcrypt)
- `/api/auth/register` endpoint
- `/api/auth/login` endpoint
- Authentication middleware
- Protected routes

### 🔮 Phase 5: Production Hardening (6-8 hours)
- Rate limiting (60 req/min per user)
- Input sanitization
- CORS configuration
- Structured logging (JSON)
- Error monitoring (Sentry)
- Database migrations (Alembic)
- CI/CD pipeline (GitHub Actions)

### 🔮 Phase 6: Frontend Dashboard (Optional)
- LIT web components
- TypeScript
- Real-time task updates
- Deployment to Cloudflare Pages

---

## Contributing

This is a production-focused project. Contributions welcome for:
- Bug fixes
- Documentation improvements
- Test coverage
- Security hardening
- Performance optimizations

**Not accepting**:
- Major architectural changes (out of scope)
- ML/AI model integration (future phase)

**Code Standards**:
- Python: Follow PEP 8, use type hints
- Formatting: Use `make format` (ruff)
- Linting: Use `make lint` (ruff)
- Tests: `make test` must pass
- Commits: Conventional commits format

---

## Support

- **Documentation**: This directory
- **Backend Guide**: [../backend/README.md](../backend/README.md)
- **Issues**: GitHub Issues
- **Live Prototype**: [Custom GPT](https://chatgpt.com/g/g-69035fdcdd648191807929b189684451-mindflow)

---

## License

MIT License - see [LICENSE](../LICENSE) for details.

---

## Changelog

### Version 2.0.0 (2025-10-30)

**Phase 2 Complete - Database Layer**:
- ✅ AsyncIO SQLAlchemy with PostgreSQL 15
- ✅ Connection pooling configuration
- ✅ User, Task, UserPreferences, AuditLog models
- ✅ Complete CRUD operations with transactions
- ✅ Multi-user isolation verified
- ✅ 19 integration tests passing
- ✅ Modern tooling: uv + ruff + Makefile
- ✅ Comprehensive documentation

### Version 1.0.0 (2025-10-30)

**Phase 1 Complete - Prototype**:
- Google Apps Script backend
- Google Sheets database
- Custom GPT integration
- Deterministic scoring algorithm
- Live demo and video walkthrough

---

**Next Steps**: Proceed with Phase 3 (API Endpoints) or read [ARCHITECTURE.md](./ARCHITECTURE.md) for system design details.
