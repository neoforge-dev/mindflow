# MindFlow Documentation

**Version**: 1.0.0
**Last Updated**: 2025-10-30
**Status**: Production-Ready

---

## Quick Navigation

| Document | Purpose | Audience |
|----------|---------|----------|
| **[ARCHITECTURE.md](./ARCHITECTURE.md)** | System design, tech stack, data flow | Engineers, architects |
| **[IMPLEMENTATION.md](./IMPLEMENTATION.md)** | Code examples, setup guide | Developers |
| **[DEPLOYMENT.md](./DEPLOYMENT.md)** | Docker, Fly.io, production setup | DevOps, engineers |
| **[PRODUCT.md](./PRODUCT.md)** | Roadmap, business model, vision | Product managers, founders |

---

## What is MindFlow?

**MindFlow** is an AI-first task manager that replaces traditional UI forms with natural conversation. Instead of clicking through menus, users talk to ChatGPT about their work, and the system intelligently suggests what to do next.

### Core Features

- **Natural Language Interface**: "Add blog post about FastAPI, due Friday"
- **Intelligent Prioritization**: AI suggests best task based on deadline, priority, effort
- **ChatGPT Integration**: Works as a Custom GPT (no app switching)
- **Transparent Reasoning**: "Recommended because: due today, high priority"

---

## Getting Started

### For Developers

**Quick Start** (5 minutes):

```bash
# Clone repository
git clone https://github.com/yourusername/mindflow.git
cd mindflow

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL, SECRET_KEY, etc.

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
# API available at http://localhost:8000
```

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

**Coming Soon**: Public beta launch (Q4 2025)

MindFlow will be available as a ChatGPT Custom GPT. To get early access:
1. Join waitlist: [TBD]
2. Follow updates on Twitter: [@mindflow_app]

---

## Documentation Overview

### 📐 ARCHITECTURE.md

**System design and technical decisions**

- High-level architecture diagram
- Tech stack rationale (FastAPI, PostgreSQL, LIT)
- Data model (database schema)
- API design (OpenAPI specification)
- Task scoring algorithm (relevance formula)
- Real-time updates (WebSockets)
- Security & multi-tenancy

**Best For**: Understanding how the system works, making technical decisions

### 💻 IMPLEMENTATION.md

**Copy-paste ready code and setup instructions**

- Quick start guide (one-command setup)
- Backend setup (FastAPI + PostgreSQL)
- Database configuration (Supabase or local)
- Frontend setup (LIT + TypeScript)
- ChatGPT Custom GPT integration
- Testing strategies
- Common patterns

**Best For**: Building the application, debugging issues

### 🚀 DEPLOYMENT.md

**Production deployment to Fly.io**

- Docker setup (Dockerfile, docker-compose)
- Fly.io deployment (step-by-step)
- Database migration (Supabase or Fly.io Postgres)
- Environment configuration (secrets management)
- Monitoring & logging (Sentry, structured logs)
- Troubleshooting guide
- CI/CD with GitHub Actions

**Best For**: Deploying to production, maintaining infrastructure

### 📊 PRODUCT.md

**Business vision, roadmap, and strategy**

- Product vision (what we're building and why)
- Current status (prototype → production transition)
- Transition plan (dropping GAS/Sheets for FastAPI)
- Roadmap (Q4 2025 → Q3 2026)
- Business model (pricing, revenue projections)
- Success metrics (KPIs, north star metric)
- Go-to-market strategy

**Best For**: Understanding product direction, planning features

---

## Tech Stack Summary

| Layer | Technology | Why |
|-------|-----------|-----|
| **Frontend** | LIT + TypeScript (optional) | Web components, 50KB bundle |
| **Primary UI** | ChatGPT Custom GPT | Natural conversation interface |
| **API** | FastAPI (Python 3.11+) | Async, type-safe, auto-docs |
| **Database** | PostgreSQL (Supabase) | Relational + JSONB flexibility |
| **Deployment** | Fly.io + Docker | Global edge, $10-50/month |
| **Auth** | JWT tokens | Stateless, multi-user |
| **Monitoring** | Sentry + structured logs | Error tracking, debugging |

**Total Infrastructure Cost**: ~$35-40/month for production MVP

---

## Project Structure

```
mindflow/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings
│   │   ├── api/                 # REST endpoints
│   │   │   ├── tasks.py
│   │   │   ├── users.py
│   │   │   └── health.py
│   │   ├── db/                  # Database
│   │   │   ├── database.py      # Async engine
│   │   │   ├── models.py        # SQLAlchemy ORM
│   │   │   └── crud.py
│   │   ├── schemas/             # Pydantic validation
│   │   ├── services/            # Business logic
│   │   │   └── scoring.py       # Task scoring
│   │   └── middleware/
│   │       └── auth.py          # JWT validation
│   ├── migrations/              # Alembic
│   ├── requirements.txt
│   ├── Dockerfile
│   └── fly.toml
├── frontend/                    # Optional LIT dashboard
│   ├── src/
│   │   ├── components/
│   │   └── services/
│   └── package.json
├── docs/
│   ├── README.md                # This file
│   ├── ARCHITECTURE.md
│   ├── IMPLEMENTATION.md
│   ├── DEPLOYMENT.md
│   └── PRODUCT.md
└── README.md                    # Project README
```

---

## Development Workflow

### 1. Local Development

```bash
# Start backend (terminal 1)
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Start frontend (terminal 2, optional)
cd frontend
npm run dev

# Run tests (terminal 3)
cd backend
pytest tests/ -v
```

### 2. Making Changes

```bash
# Create feature branch
git checkout -b feature/task-filtering

# Make changes, test locally
# ...

# Create database migration (if needed)
alembic revision --autogenerate -m "Add task filtering"
alembic upgrade head

# Run tests
pytest tests/ -v --cov=app

# Commit and push
git add .
git commit -m "Add task filtering feature"
git push origin feature/task-filtering
```

### 3. Deploying to Production

```bash
# Deploy to Fly.io
flyctl deploy

# Check logs
flyctl logs

# Verify deployment
curl https://mindflow-api.fly.dev/health
```

---

## API Endpoints

**Base URL**: `https://mindflow-api.fly.dev` (or `http://localhost:8000` locally)

### Core Endpoints

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/health` | GET | Health check | No |
| `/api/tasks` | POST | Create task | Yes |
| `/api/tasks` | GET | List tasks | Yes |
| `/api/tasks/best` | GET | Get best task to work on | Yes |
| `/api/tasks/{id}` | GET | Get specific task | Yes |
| `/api/tasks/{id}` | PUT | Update task | Yes |
| `/api/tasks/{id}` | DELETE | Delete task | Yes |
| `/api/auth/register` | POST | Register new user | No |
| `/api/auth/login` | POST | Login and get JWT | No |

**API Documentation**: `http://localhost:8000/docs` (when running locally)

---

## Environment Variables

**Required**:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key (32+ random bytes)

**Optional**:
- `OPENAI_API_KEY`: For GPT features (if needed)
- `SENTRY_DSN`: Error tracking
- `ENVIRONMENT`: `development` or `production`

**Example** (`.env`):
```bash
DATABASE_URL=postgresql+asyncpg://localhost/mindflow
SECRET_KEY=your-secret-key-change-in-production
ENVIRONMENT=development
```

---

## Common Tasks

### Run Database Migrations

```bash
cd backend
alembic upgrade head
```

### Create New Migration

```bash
alembic revision --autogenerate -m "Description of change"
alembic upgrade head
```

### View Logs (Production)

```bash
flyctl logs
flyctl logs --follow  # Stream logs
```

### Run Tests

```bash
cd backend
pytest tests/ -v --cov=app
```

### Check API Health

```bash
# Local
curl http://localhost:8000/health

# Production
curl https://mindflow-api.fly.dev/health
```

---

## Troubleshooting

### Backend Won't Start

**Check**:
1. Database connection: `psql $DATABASE_URL`
2. Environment variables: `printenv | grep DATABASE_URL`
3. Dependencies: `pip list | grep fastapi`

**Fix**:
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check database
alembic upgrade head

# Run with verbose logging
uvicorn app.main:app --reload --log-level debug
```

### Database Connection Failed

**Check Supabase**:
1. Project is running (not paused)
2. Connection pooling enabled (port 5432)
3. Connection string format: `postgresql+asyncpg://...`

**Test connection**:
```bash
psql "postgresql://user:pass@host:5432/postgres"
```

### Deployment Failed

**Check Fly.io**:
```bash
flyctl status
flyctl logs
```

**Common issues**:
- Missing secrets: `flyctl secrets list`
- Out of memory: `flyctl scale memory 512`
- Wrong region: `flyctl regions list`

---

## Contributing

**Workflow**:
1. Fork repository
2. Create feature branch
3. Make changes + add tests
4. Submit pull request

**Code Standards**:
- Python: Follow PEP 8, use `black` formatter
- TypeScript: Use Prettier
- Tests: Maintain >80% coverage
- Commits: Use conventional commits format

---

## Support

- **Documentation**: This directory
- **Issues**: github.com/yourusername/mindflow/issues
- **Discussions**: github.com/yourusername/mindflow/discussions
- **Discord**: [TBD]
- **Email**: support@mindflow.app

---

## License

[TBD - Add license information]

---

## Changelog

### Version 1.0.0 (2025-10-30)

**Initial Release**:
- FastAPI backend with async PostgreSQL
- JWT authentication
- Task CRUD operations
- Task scoring algorithm
- ChatGPT Custom GPT integration
- Fly.io deployment
- Comprehensive documentation

---

**Next Steps**: Read [ARCHITECTURE.md](./ARCHITECTURE.md) to understand system design, or jump to [IMPLEMENTATION.md](./IMPLEMENTATION.md) to start coding.
