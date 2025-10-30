# MindFlow Complete Implementation Plan

**Status**: Phases 1-3 Complete, Phase 4-7 Planned
**Current Version**: 3.0.0
**Target Version**: 7.0.0 (Production MVP)
**Total Estimated Time**: 25-30 hours (6-7 days of focused work)
**Created**: 2025-10-30

---

## Executive Summary

This document outlines the complete roadmap to transform MindFlow from a prototype (Phase 1) to a production-ready AI task manager (Phase 7). Phases 1-3 are complete. Phases 4-7 will add authentication, production hardening, task scoring, and deployment.

**Completed Phases** (12 hours):
- ✅ Phase 1: Prototype (Google Apps Script + Sheets)
- ✅ Phase 2: Database Layer (PostgreSQL + SQLAlchemy)
- ✅ Phase 3: API Endpoints (FastAPI REST API)

**Remaining Phases** (18-23 hours):
- 🚧 Phase 4: Authentication & JWT (6-7 hours)
- 📋 Phase 5: Production Hardening (6-8 hours)
- 📋 Phase 6: Task Scoring & Best Task Endpoint (4-5 hours)
- 📋 Phase 7: Deployment & Monitoring (2-3 hours)

---

## Phase Status Overview

| Phase | Name | Duration | Status | Tests | Coverage |
|-------|------|----------|--------|-------|----------|
| 1 | Prototype | N/A | ✅ Complete | Manual | N/A |
| 2 | Database Layer | 4 hrs | ✅ Complete | 19 tests | 90%+ |
| 3 | API Endpoints | 4 hrs | ✅ Complete | 21 tests | 88%+ |
| 4 | Authentication | 6-7 hrs | 🚧 Ready | 15+ planned | 85%+ target |
| 5 | Production Hardening | 6-8 hrs | 📋 Planned | 20+ planned | 90%+ target |
| 6 | Task Scoring | 4-5 hrs | 📋 Planned | 10+ planned | 85%+ target |
| 7 | Deployment | 2-3 hrs | 📋 Planned | Integration | N/A |

**Total**: 26-31 hours across 7 phases

---

## Phase 4: Authentication & JWT (6-7 hours) 🚧

**Status**: Ready to execute (detailed plan in PHASE4-PLAN.md v1.1)

### Overview
Replace temporary query parameter auth with production-grade JWT authentication. Implement user registration, login, password hashing, and protected endpoints.

### What We're Building
- User registration with bcrypt password hashing (12+ chars)
- JWT token generation and validation (HS256, 24hr expiration)
- Login endpoint returning access tokens
- Protected API endpoints (Authorization: Bearer token)
- Authentication middleware with dependency injection

### Key Components
1. **Security Layer** (`app/auth/security.py`):
   - `hash_password()` - bcrypt with 12 rounds
   - `verify_password()` - constant-time comparison
   - `create_access_token()` - JWT generation
   - `decode_access_token()` - JWT validation

2. **User CRUD** (`app/db/crud.py`):
   - `UserCRUD.create()` - Create user record
   - `UserCRUD.get_by_email()` - Email lookup
   - `UserCRUD.get_by_id()` - ID lookup

3. **Auth Service** (`app/auth/service.py`):
   - `AuthService.register_user()` - Registration with hash
   - `AuthService.authenticate_user()` - Credential verification

4. **Auth Endpoints** (`app/api/auth.py`):
   - `POST /api/auth/register` - User registration
   - `POST /api/auth/login` - Login (returns JWT)
   - `GET /api/auth/me` - Current user info

5. **Auth Middleware** (`app/dependencies.py`):
   - `get_current_user_id()` - Extract user_id from JWT
   - `get_current_user()` - Fetch full User object

### Breaking Changes
- Removes `?user_id=` query parameter auth
- All endpoints require `Authorization: Bearer <token>` header
- Custom GPT must login first to get token

### Success Criteria
- 55+ tests passing (15 auth + 40 existing)
- >85% code coverage
- JWT tokens contain only user_id (no PII)
- Passwords hashed with bcrypt (12+ chars minimum)
- User isolation maintained via JWT claims

### Time Budget
- Setup & UserCRUD: 30 min
- Security utilities: 45 min
- Auth schemas: 20 min
- Auth service: 1 hour
- Auth endpoints: 1.5 hours
- Update dependencies: 45 min
- Migrate task endpoints: 1.5 hours
- Final validation: 30 min
- **Total**: 6.5 hours (7hrs with buffer)

---

## Phase 5: Production Hardening (6-8 hours) 📋

**Status**: Planned (will create detailed plan after Phase 4)

### Overview
Add production-grade features for security, reliability, and maintainability. Focus on rate limiting, input validation, logging, error tracking, and database migrations.

### What We're Building
- Rate limiting (60 req/min per user, 10 req/min for auth)
- Input sanitization and validation
- Structured logging (JSON format for production)
- Error monitoring with Sentry
- Database migrations with Alembic
- Health check improvements (DB connectivity)
- CORS hardening for production
- Request ID tracking

### Key Components

#### 5.1: Rate Limiting (1.5 hours)
**Library**: `slowapi` (FastAPI-compatible rate limiter)

**Files**:
- `app/middleware/rate_limit.py` - Rate limiting middleware
- `app/config.py` - Add rate limit settings
- `tests/middleware/test_rate_limit.py` - Rate limit tests

**Functions**:
- `get_rate_limiter()` - Initialize rate limiter with Redis backend
- `rate_limit_key()` - Generate rate limit key from user_id
- `@limiter.limit("60/minute")` - Decorator for endpoints

**Tests**:
- `test_rate_limit_allows_requests_under_limit` - Requests under limit succeed
- `test_rate_limit_blocks_requests_over_limit` - 429 when limit exceeded
- `test_rate_limit_resets_after_window` - Counter resets after 60 seconds
- `test_rate_limit_per_user_isolation` - User A doesn't affect User B
- `test_auth_endpoints_have_stricter_limits` - Login limited to 10/min

#### 5.2: Input Sanitization (1 hour)
**Library**: `bleach` (HTML sanitization)

**Files**:
- `app/middleware/sanitize.py` - Input sanitization
- `tests/middleware/test_sanitize.py` - Sanitization tests

**Functions**:
- `sanitize_string()` - Remove HTML tags, script injections
- `sanitize_request_body()` - Middleware to clean all inputs
- `validate_task_title()` - Extra validation for task fields

**Tests**:
- `test_sanitize_removes_script_tags` - XSS prevention
- `test_sanitize_preserves_safe_content` - Normal text unchanged
- `test_sanitize_handles_unicode` - UTF-8 support
- `test_task_title_rejects_html` - HTML in task titles rejected

#### 5.3: Structured Logging (1 hour)
**Library**: `structlog` (structured logging)

**Files**:
- `app/logging_config.py` - Logging setup
- `app/middleware/request_logging.py` - Request/response logging
- Update `app/main.py` - Register logging middleware

**Functions**:
- `setup_logging()` - Configure structlog with JSON renderer
- `log_request()` - Log incoming requests with context
- `log_response()` - Log responses with timing
- `log_error()` - Log exceptions with stack traces

**Tests**:
- `test_logging_includes_request_id` - Each request has unique ID
- `test_logging_includes_user_id` - Authenticated requests log user
- `test_logging_json_format_in_prod` - Production uses JSON logs
- `test_logging_human_format_in_dev` - Dev uses readable logs

#### 5.4: Error Monitoring (1.5 hours)
**Library**: `sentry-sdk` (error tracking)

**Files**:
- `app/monitoring/sentry.py` - Sentry initialization
- `app/config.py` - Add `SENTRY_DSN` setting
- Update `app/main.py` - Initialize Sentry

**Functions**:
- `init_sentry()` - Configure Sentry SDK
- `capture_exception()` - Send exception to Sentry
- `set_user_context()` - Add user info to error reports
- `add_breadcrumb()` - Add context to error traces

**Tests**:
- `test_sentry_captures_exceptions` - Errors sent to Sentry
- `test_sentry_includes_user_context` - User ID in error reports
- `test_sentry_disabled_in_tests` - Sentry off during testing
- `test_sentry_filters_sensitive_data` - Passwords not sent

#### 5.5: Database Migrations (2 hours)
**Library**: `alembic` (database migrations)

**Files**:
- `alembic/env.py` - Alembic configuration
- `alembic/versions/001_initial.py` - Initial schema migration
- `Makefile` - Add migration commands

**Commands**:
- `make migrate-create` - Create new migration
- `make migrate-up` - Apply migrations
- `make migrate-down` - Rollback migrations
- `make migrate-history` - Show migration history

**Tests**:
- `test_migration_creates_all_tables` - Initial migration works
- `test_migration_is_reversible` - Can rollback migrations
- `test_migration_handles_existing_data` - Data preserved
- `test_migration_version_tracking` - Version table updated

#### 5.6: Enhanced Health Checks (30 min)
**Files**:
- Update `app/api/health.py` - Add database connectivity check

**Functions**:
- `check_database_health()` - Test DB connection
- `check_redis_health()` - Test rate limiter backend
- `get_health_status()` - Aggregate health checks

**Tests**:
- `test_health_check_includes_database_status` - DB status in response
- `test_health_check_returns_503_on_db_failure` - Unhealthy when DB down
- `test_health_check_includes_version` - API version in response

### Dependencies to Add
```toml
slowapi = "^0.1.9"          # Rate limiting
bleach = "^6.1.0"           # HTML sanitization
structlog = "^24.1.0"       # Structured logging
sentry-sdk = "^1.40.0"      # Error monitoring
alembic = "^1.13.0"         # Database migrations
redis = "^5.0.0"            # Rate limiter backend
```

### Success Criteria
- All 75+ tests passing (20 new + 55 existing)
- >90% code coverage
- Rate limiting active on all endpoints
- No XSS vulnerabilities (sanitization tested)
- JSON logs in production, readable logs in dev
- Sentry captures exceptions with user context
- Database migrations fully reversible
- Health checks include DB connectivity

### Time Budget
- Rate limiting: 1.5 hours
- Input sanitization: 1 hour
- Structured logging: 1 hour
- Error monitoring: 1.5 hours
- Database migrations: 2 hours
- Enhanced health checks: 30 min
- **Total**: 7.5 hours (8hrs with buffer)

---

## Phase 6: Task Scoring & Best Task Endpoint (4-5 hours) 📋

**Status**: Planned

### Overview
Implement the core AI feature: intelligent task prioritization. The scoring algorithm recommends the best task to work on based on deadline urgency, priority, effort, and time of day.

### What We're Building
- Task scoring algorithm (deterministic formula)
- `/api/tasks/best` endpoint (returns highest-scored task)
- Score caching and recalculation
- Time-of-day awareness (morning vs afternoon tasks)
- Deadline urgency calculation
- Effort estimation integration

### Scoring Algorithm
```python
score = (
    deadline_urgency * 40  # 0-40 points (due today = 40, overdue = 50)
    + priority * 10        # 0-50 points (priority 1-5)
    + effort_bonus * 10    # 0-10 points (prefer quick wins)
)
```

**Deadline Urgency**:
- Overdue: 1.25 (50 points)
- Due today: 1.0 (40 points)
- Due tomorrow: 0.75 (30 points)
- Due this week: 0.5 (20 points)
- Due later: 0.25 (10 points)
- No deadline: 0.0 (0 points)

**Priority**: 1-5 (maps to 10-50 points)

**Effort Bonus**:
- ≤15 min: 1.0 (10 points) - quick win
- ≤30 min: 0.75 (7.5 points)
- ≤60 min: 0.5 (5 points)
- >60 min: 0.25 (2.5 points)
- No estimate: 0.0 (0 points)

**Example**:
- Task: "Write blog post"
- Due: Today
- Priority: 4 (high)
- Effort: 30 min
- **Score**: 40 + 40 + 7.5 = 87.5 points

### Key Components

#### 6.1: Scoring Service (2 hours)
**Files**:
- `app/services/scoring.py` - Task scoring logic
- `app/db/crud.py` - Add score calculation to TaskCRUD
- `tests/services/test_scoring.py` - Scoring tests

**Functions**:
- `calculate_task_score()` - Main scoring function
- `calculate_deadline_urgency()` - Urgency from due_date
- `calculate_effort_bonus()` - Bonus from effort estimate
- `get_tasks_ranked_by_score()` - Return sorted task list

**Tests**:
- `test_overdue_task_has_highest_urgency` - Overdue = 1.25 multiplier
- `test_due_today_has_full_urgency` - Due today = 1.0
- `test_high_priority_increases_score` - Priority 5 > Priority 1
- `test_quick_tasks_get_effort_bonus` - ≤15min gets bonus
- `test_no_deadline_has_zero_urgency` - No due_date = 0 urgency
- `test_tasks_sorted_by_score_descending` - Highest score first
- `test_equal_scores_sort_by_created_date` - Tie-breaker

#### 6.2: Best Task Endpoint (1.5 hours)
**Files**:
- Update `app/api/tasks.py` - Add `/api/tasks/best` endpoint
- `tests/api/test_task_scoring.py` - Best task endpoint tests

**Endpoints**:
- `GET /api/tasks/best` - Returns highest-scored pending task
- `GET /api/tasks/ranked` - Returns all tasks sorted by score

**Functions**:
- `get_best_task()` - Return single best task with score
- `get_ranked_tasks()` - Return all tasks with scores
- `calculate_and_cache_scores()` - Batch score calculation

**Tests**:
- `test_best_task_returns_highest_score` - Most urgent task returned
- `test_best_task_excludes_completed` - Only pending/in-progress
- `test_best_task_excludes_snoozed` - Snoozed until > now excluded
- `test_best_task_returns_404_when_no_tasks` - Empty list = 404
- `test_ranked_tasks_returns_all_with_scores` - All tasks scored
- `test_score_included_in_response` - Response contains score field

#### 6.3: Score Caching (1 hour)
**Files**:
- `app/services/cache.py` - Score caching logic
- `app/config.py` - Add cache TTL settings

**Functions**:
- `cache_task_scores()` - Cache scores in Redis (5 min TTL)
- `invalidate_task_cache()` - Clear cache on task update
- `get_cached_score()` - Retrieve cached score

**Tests**:
- `test_cache_stores_calculated_scores` - Scores cached
- `test_cache_returns_cached_scores` - Cache hit works
- `test_cache_expires_after_ttl` - 5min expiration
- `test_cache_invalidated_on_update` - Update clears cache

### Response Schema
```json
{
  "task": {
    "id": "uuid",
    "title": "Write blog post",
    "priority": 4,
    "due_date": "2025-10-31T17:00:00",
    "effort_estimate_minutes": 30,
    ...
  },
  "score": 87.5,
  "reasoning": {
    "deadline_urgency": 1.0,
    "deadline_urgency_score": 40,
    "priority_score": 40,
    "effort_bonus": 0.75,
    "effort_bonus_score": 7.5,
    "total_score": 87.5,
    "recommendation": "Due today with high priority - good time to tackle this"
  }
}
```

### Success Criteria
- All 85+ tests passing (10 new + 75 existing)
- >85% code coverage
- Best task endpoint returns highest-scored task
- Scoring algorithm matches Phase 1 prototype
- Score caching reduces DB load
- Transparent reasoning in response

### Time Budget
- Scoring service: 2 hours
- Best task endpoint: 1.5 hours
- Score caching: 1 hour
- **Total**: 4.5 hours (5hrs with buffer)

---

## Phase 7: Deployment & Monitoring (2-3 hours) 📋

**Status**: Planned

### Overview
Deploy MindFlow to production on DigitalOcean with proper monitoring, SSL, and CI/CD. This phase focuses on infrastructure, not code changes.

### What We're Building
- DigitalOcean Droplet setup (Ubuntu 22.04 LTS)
- PostgreSQL 15 installation (managed DB or same droplet)
- Nginx reverse proxy with SSL (Let's Encrypt)
- Systemd service for FastAPI app
- Environment variables and secrets management
- GitHub Actions CI/CD pipeline
- Monitoring dashboard (Grafana + Prometheus)

### Key Components

#### 7.1: Server Setup (1 hour)
**Infrastructure**:
- DigitalOcean Droplet ($12/month, 2GB RAM, 1 vCPU)
- Ubuntu 22.04 LTS
- SSH key authentication
- Firewall configuration (ufw)

**Commands**:
```bash
# Create droplet
doctl compute droplet create mindflow-prod \
  --region sfo3 \
  --size s-1vcpu-2gb \
  --image ubuntu-22-04-x64

# Configure firewall
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable

# Install dependencies
apt update && apt upgrade -y
apt install -y python3.11 python3-pip nginx postgresql-15
```

#### 7.2: Database Setup (30 min)
**Options**:
- Option A: Managed PostgreSQL ($15/month, recommended)
- Option B: PostgreSQL on same droplet ($0, lower reliability)

**Configuration**:
```bash
# Create production database
createdb mindflow_prod

# Run migrations
alembic upgrade head

# Create app user (limited permissions)
CREATE USER mindflow_app WITH PASSWORD 'secure_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mindflow_app;
```

#### 7.3: Nginx & SSL (45 min)
**Files**:
- `/etc/nginx/sites-available/mindflow` - Nginx config
- SSL certificates from Let's Encrypt

**Configuration**:
```nginx
server {
    listen 80;
    server_name api.mindflow.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.mindflow.example.com;

    ssl_certificate /etc/letsencrypt/live/api.mindflow.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.mindflow.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Commands**:
```bash
# Install certbot
apt install -y certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d api.mindflow.example.com
```

#### 7.4: Systemd Service (15 min)
**Files**:
- `/etc/systemd/system/mindflow.service` - Service config

**Configuration**:
```ini
[Unit]
Description=MindFlow FastAPI Application
After=network.target postgresql.service

[Service]
Type=simple
User=mindflow
WorkingDirectory=/opt/mindflow/backend
Environment="PATH=/opt/mindflow/backend/.venv/bin"
ExecStart=/opt/mindflow/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Commands**:
```bash
systemctl daemon-reload
systemctl enable mindflow
systemctl start mindflow
systemctl status mindflow
```

#### 7.5: Environment Variables (15 min)
**Files**:
- `/opt/mindflow/backend/.env.production` - Production secrets

**Configuration**:
```bash
# Database
DATABASE_URL=postgresql+asyncpg://mindflow_app:password@localhost/mindflow_prod

# Security
SECRET_KEY=<64-char-random-string>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24

# Environment
ENVIRONMENT=production
DEBUG=false

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/xxx

# Rate Limiting
REDIS_URL=redis://localhost:6379/0
```

**Security**:
```bash
# Generate secure secret key
openssl rand -hex 32

# Set file permissions
chmod 600 /opt/mindflow/backend/.env.production
chown mindflow:mindflow /opt/mindflow/backend/.env.production
```

#### 7.6: CI/CD Pipeline (30 min)
**Files**:
- `.github/workflows/deploy.yml` - GitHub Actions workflow

**Workflow**:
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          cd backend
          uv pip install -r requirements.txt
          uv run pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to DigitalOcean
        run: |
          ssh deploy@${{ secrets.SERVER_IP }} '
            cd /opt/mindflow
            git pull origin main
            cd backend
            uv sync
            alembic upgrade head
            systemctl restart mindflow
          '
```

### Cost Breakdown
| Component | Cost/Month |
|-----------|------------|
| Droplet (2GB) | $12 |
| Managed PostgreSQL (optional) | $15 |
| Domain name | $1-2 |
| **Total (Basic)** | **$13-14** |
| **Total (Managed DB)** | **$28-29** |

### Success Criteria
- Application accessible via HTTPS
- SSL certificate valid (Let's Encrypt)
- Systemd service runs automatically
- Database migrations applied
- Environment variables secure (600 permissions)
- CI/CD deploys on git push to main
- Health check returns 200
- Can create tasks via public API

### Time Budget
- Server setup: 1 hour
- Database setup: 30 min
- Nginx & SSL: 45 min
- Systemd service: 15 min
- Environment variables: 15 min
- CI/CD pipeline: 30 min
- **Total**: 3 hours (3.25hrs with buffer)

---

## Complete Timeline

### Week 1
- **Day 1-2**: Phase 4 (Authentication) - 6-7 hours
- **Day 3-4**: Phase 5 (Production Hardening) - 6-8 hours

### Week 2
- **Day 5**: Phase 6 (Task Scoring) - 4-5 hours
- **Day 6**: Phase 7 (Deployment) - 2-3 hours
- **Day 7**: Buffer & polish

**Total**: 18-23 hours actual work, spread over 6-7 days

---

## Dependencies Summary

### Phase 4
```toml
passlib[bcrypt] = "^1.7.4"
python-jose[cryptography] = "^3.3.0"
```

### Phase 5
```toml
slowapi = "^0.1.9"
bleach = "^6.1.0"
structlog = "^24.1.0"
sentry-sdk = "^1.40.0"
alembic = "^1.13.0"
redis = "^5.0.0"
```

### Phase 6
```toml
# No new dependencies (uses existing Redis)
```

### Phase 7
```bash
# System packages (not Python)
nginx
postgresql-15
certbot
```

---

## Test Coverage Targets

| Phase | New Tests | Cumulative Tests | Coverage Target |
|-------|-----------|------------------|-----------------|
| 4 | 15+ | 55+ | 85% |
| 5 | 20+ | 75+ | 90% |
| 6 | 10+ | 85+ | 85% |
| 7 | Integration | 85+ | N/A |

---

## Risk Mitigation

### Phase 4 Risks
- **JWT secret leak**: Use strong random secret, never commit
- **Password brute force**: Phase 5 adds rate limiting
- **Token revocation**: Known limitation, Phase 5 adds refresh tokens

### Phase 5 Risks
- **Redis failure**: Rate limiting degrades gracefully
- **Sentry costs**: Free tier sufficient for MVP
- **Migration failures**: All migrations reversible

### Phase 6 Risks
- **Cache inconsistency**: 5min TTL limits stale data
- **Scoring performance**: Cache reduces DB load
- **Algorithm tuning**: Easy to adjust multipliers

### Phase 7 Risks
- **Deployment downtime**: Zero-downtime with systemd restart
- **SSL expiration**: Certbot auto-renewal
- **Database backups**: DigitalOcean automated backups

---

## Post-Phase 7 (Future Enhancements)

### Phase 8: Advanced Features (Optional)
- Refresh tokens & token revocation
- Email verification & password reset
- Task templates & recurring tasks
- Task dependencies & subtasks
- Team collaboration features
- Mobile app (React Native)

### Phase 9: Scale & Optimize (Optional)
- Horizontal scaling with load balancer
- Redis cluster for caching
- Database read replicas
- CDN for static assets
- WebSocket real-time updates

---

## Success Metrics

### Technical Metrics
- **Uptime**: >99.5% (4 hours downtime/month max)
- **Response time**: <200ms (p95)
- **Test coverage**: >85% across all modules
- **Error rate**: <0.1% of requests
- **Database queries**: <50ms (p95)

### Business Metrics
- **Users**: 100+ registered users
- **Tasks**: 1000+ tasks created
- **API calls**: 10,000+ per month
- **DAU/MAU**: >30% (daily active / monthly active)

---

**Ready to execute**: Start with Phase 4 (Authentication)

**See**: PHASE4-PLAN.md for detailed implementation steps
