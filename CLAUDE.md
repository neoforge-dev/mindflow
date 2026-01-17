# MindFlow - AI-First Task Manager

AI-powered task management in ChatGPT with interactive widgets.

---

## Project Overview

| Attribute | Value |
|-----------|-------|
| **Domain** | neoforge-dev |
| **Status** | Phase 9B Complete - Production Ready |
| **Tech Stack** | FastAPI + React + PostgreSQL + ChatGPT Apps SDK |
| **Tests** | 256 passing (80.63% coverage) |

---

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15 (async with asyncpg)
- **Auth**: OAuth 2.1 with RS256 JWT, PKCE, token rotation
- **MCP**: FastMCP (Model Context Protocol)
- **Package Manager**: Astral `uv`

### Frontend
- **Widget**: React + TypeScript (9.2kb bundle)
- **ChatGPT**: Apps SDK with interactive widgets

---

## Quick Commands

```bash
# One-command setup
cd backend && make quick-start

# Development
make help          # Show all commands
make test          # Run tests with coverage
make lint          # Check code quality
make format        # Format with ruff
make db-up         # Start test database
make run           # Start FastAPI dev server

# Manual setup
uv sync
make db-up
make test
```

---

## Key Features

- **Interactive Widgets**: TaskWidget with Complete/Snooze buttons in ChatGPT
- **MCP Server**: FastMCP implementing Model Context Protocol
- **OAuth 2.1**: RS256 JWT with PKCE, refresh token rotation
- **Intelligent Prioritization**: Transparent scoring (not ML black box)
- **Natural Language**: Create/update tasks conversationally

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER (Natural Language)              │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│               CUSTOM GPT (Intent Recognition)           │
│  • Parses user intent                                   │
│  • Calls API via Actions (function calling)            │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS (JSON)
                         ▼
┌─────────────────────────────────────────────────────────┐
│         FASTAPI BACKEND (REST API Layer)                │
│  • Async request handling (uvicorn)                    │
│  • Pydantic validation                                 │
│  • Relevance scoring engine                            │
│  • JWT authentication                                  │
└────────────────────────┬────────────────────────────────┘
                         │ AsyncPG Driver
                         ▼
┌─────────────────────────────────────────────────────────┐
│         POSTGRESQL 15 (Database Layer)                  │
│  • Users, Tasks, UserPreferences, AuditLogs            │
│  • Connection pooling (10 + 5 overflow)                │
│  • Composite indexes for performance                    │
└─────────────────────────────────────────────────────────┘
```

---

## Performance Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Test Coverage | 80% | 80.63% |
| Response Time | <500ms | ✅ |
| Widget Bundle | <50kb | 9.2kb |
| Compilation Errors | 0 | 0 |

---

## Human Gates (Required)

1. **GPT Actions**: Changes to Custom GPT action endpoints
2. **OAuth/Auth**: Changes to authentication or token handling
3. **MCP Tools**: New or modified MCP tool definitions
4. **Scoring Algorithm**: Changes to task prioritization logic
5. **Database Schema**: Changes requiring migrations

---

## Directory Structure

```
mindflow/
├── backend/           # FastAPI backend
│   ├── cmd/           # CLI commands
│   ├── internal/      # Business logic
│   └── tests/         # Backend tests
├── frontend/          # React widget
├── src/               # MCP server
├── docs/              # Documentation
└── deployment/        # Docker configs
```

---

## Resources

- **ChatGPT Setup**: `CUSTOM_GPT_SETUP.md`
- **Deployment**: `DEPLOYMENT.md`
- **Testing**: `TESTING.md`
- **Domain Rules**: `../CLAUDE.md`
