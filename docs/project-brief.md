# MindFlow - Project Brief

## Overview

**MindFlow** is an AI-first task manager that replaces traditional UI forms with natural conversation. Users interact with GPT about their work, and the system intelligently suggests what to prioritize next using context-aware scoring.

| Attribute | Value |
|-----------|-------|
| **Domain** | neoforge-dev |
| **Status** | MVP Complete (Production Ready) |
| **Tech Stack** | FastAPI + React + PostgreSQL + ChatGPT Apps SDK |
| **Deploy** | Railway (backend) + Cloudflare Pages (frontend) |

---

## Problem Statement

Traditional task managers require users to:
- Click through menus and fill forms
- Manually decide what to work on next
- Switch between apps to manage tasks
- Learn complex interfaces

This creates friction that reduces productivity and adoption.

---

## Solution

MindFlow provides:

1. **Natural Interface**: Talk instead of click
   - "Add blog post about FastAPI, due Friday, high priority"
   - "What should I do next?"
   - "Show me everything due this week"

2. **Intelligent Prioritization**: AI-powered task scoring
   - Context-aware (time of day, deadlines, user patterns)
   - Transparent reasoning ("Due today + high priority + quick win")
   - Learns from user behavior over time

3. **Zero Friction**: No app switching
   - Works where you already are (ChatGPT)
   - No new app to learn
   - Instant access from any device

---

## Target Users

**Primary**: Knowledge workers managing multiple projects
- Software engineers juggling features, bugs, and tech debt
- Product managers coordinating across teams
- Founders managing strategic and tactical work
- Content creators balancing research, writing, editing

**Secondary**: Teams needing lightweight coordination
- Small teams (2-5 people)
- Consulting teams managing client projects
- Research teams tracking experiments

---

## Key Features

### Core Functionality
- Natural language task creation and management
- Interactive ChatGPT widgets with Complete/Snooze buttons
- MCP Server implementing Model Context Protocol
- OAuth 2.1 with RS256 JWT, PKCE, token rotation

### Technical Highlights
- 256 tests passing (80.63% coverage)
- 9.2kb frontend widget bundle
- <500ms API response time
- PostgreSQL with async operations

---

## Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Test Coverage | 80% | 80.63% |
| API Response | <500ms | Met |
| Widget Bundle | <50kb | 9.2kb |
| User Adoption | 100 beta users | Pending |

---

## Competitive Position

| Product | Interface | AI Features | MindFlow Advantage |
|---------|-----------|-------------|-------------------|
| Todoist | GUI | None | Conversational interface |
| Asana | GUI | Basic | AI is core, not bolt-on |
| Linear | GUI | Triage | Cross-platform via ChatGPT |
| ClickUp | Complex GUI | Summaries | Zero learning curve |

**Key Differentiator**: AI conversation is the primary interface, not an add-on feature.

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER (Natural Language)              │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│               CUSTOM GPT (Intent Recognition)           │
│  • Parses user intent                                   │
│  • Calls API via Actions                                │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────┐
│         FASTAPI BACKEND (REST API Layer)                │
│  • Async request handling                               │
│  • Relevance scoring engine                             │
│  • JWT authentication                                   │
└────────────────────────┬────────────────────────────────┘
                         │ AsyncPG
                         ▼
┌─────────────────────────────────────────────────────────┐
│         POSTGRESQL 15 (Database Layer)                  │
│  • Users, Tasks, UserPreferences, AuditLogs            │
│  • Connection pooling                                   │
└─────────────────────────────────────────────────────────┘
```

---

## Roadmap

### Completed
- [x] FastAPI backend with PostgreSQL
- [x] OAuth 2.1 authentication
- [x] ChatGPT Apps SDK integration
- [x] Interactive widgets
- [x] MCP Server implementation
- [x] 80%+ test coverage

### Next Phase
- [ ] Beta user onboarding (100 users)
- [ ] Team collaboration features
- [ ] Mobile-optimized widgets
- [ ] Usage analytics dashboard

---

## Resources

- **Setup Guide**: `CUSTOM_GPT_SETUP.md`
- **Deployment**: `docs/DEPLOYMENT.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **Sprint Plan**: `docs/PLAN.md`
