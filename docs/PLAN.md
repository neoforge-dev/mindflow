# MindFlow Implementation Plan - Phases 5-7

**Status**: Phases 1-4 Complete, Phase 5-7 Planned
**Current Version**: 4.0.0
**Target Version**: 7.0.0 (Production MVP)
**Total Estimated Time**: 11-14 hours (2-3 days of focused work)
**Last Updated**: 2025-10-31

---

## Executive Summary

This document outlines the remaining roadmap to transform MindFlow into a production-ready AI task manager. Phases 1-4 are complete with 73 tests passing at 88% coverage. Phases 5-7 will add production hardening, task scoring, and deployment.

**Completed Phases** (18-19 hours):
- ✅ Phase 1: Prototype (Google Apps Script + Sheets)
- ✅ Phase 2: Database Layer (PostgreSQL + SQLAlchemy) - 19 tests
- ✅ Phase 3: API Endpoints (FastAPI REST API) - 21 tests
- ✅ Phase 4: Authentication & JWT (33 tests, 88% coverage)

**Remaining Phases** (11-14 hours):
- 📋 Phase 5: Production Hardening (5-6 hours)
- 📋 Phase 6: Task Scoring & Best Task Endpoint (4-5 hours)
- 📋 Phase 7: Deployment & Monitoring (2-3 hours)

---

## Phase Status Overview

| Phase | Name | Duration | Status | Tests | Coverage |
|-------|------|----------|--------|-------|----------|
| 1 | Prototype | N/A | ✅ Complete | Manual | N/A |
| 2 | Database Layer | 4 hrs | ✅ Complete | 19 tests | 90%+ |
| 3 | API Endpoints | 4 hrs | ✅ Complete | 21 tests | 88%+ |
| 4 | Authentication | 6-7 hrs | ✅ Complete | 33 tests | 88% |
| 5 | Production Hardening | 5-6 hrs | 📋 Planned | 20+ planned | 90%+ target |
| 6 | Task Scoring | 4-5 hrs | 📋 Planned | 10+ planned | 85%+ target |
| 7 | Deployment | 2-3 hrs | 📋 Planned | Integration | N/A |

**Total**: 30-33 hours across 7 phases (19 complete, 11-14 remaining)

---

## Phase 5: Production Hardening (5-6 hours) 📋

**Status**: Planned

### Overview
Add production-grade features for security, reliability, and maintainability. Focus on rate limiting, input validation, logging, error tracking, and database migrations. **Optimized for MVP**: Uses in-memory solutions instead of Redis to reduce complexity and cost.

### What We're Building
- Rate limiting (60 req/min per user, 10 req/min for auth) with in-memory storage
- Input sanitization using Pydantic validators (no new dependencies)
- Structured logging (JSON format for production) with request ID tracking
- Error monitoring with Sentry
- Database migrations with Alembic (migration from current setup)
- Enhanced health checks (DB connectivity)
- CORS hardening for production

### Key Components

#### 5.1: Rate Limiting (1 hour)
**Library**: `slowapi` (FastAPI-compatible rate limiter with in-memory storage)

**Files**:
- `app/middleware/rate_limit.py` - Rate limiting middleware
- `app/config.py` - Add rate limit settings
- `tests/middleware/test_rate_limit.py` - Rate limit tests

**Functions**:
- `get_rate_limiter()` - Initialize rate limiter with in-memory backend (no Redis needed)
- `rate_limit_key()` - Generate rate limit key from user_id
- `@limiter.limit("60/minute")` - Decorator for endpoints

**Implementation**:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

# In-memory storage (no Redis required for MVP)
limiter = Limiter(key_func=get_remote_address)

# Apply to endpoints
@router.post("/api/tasks")
@limiter.limit("60/minute")
async def create_task(...):
    ...

# Stricter limits for auth
@router.post("/api/auth/login")
@limiter.limit("10/minute")
async def login(...):
    ...
```

**Tests**:
- `test_rate_limit_allows_requests_under_limit` - Requests under limit succeed
- `test_rate_limit_blocks_requests_over_limit` - 429 when limit exceeded
- `test_rate_limit_resets_after_window` - Counter resets after 60 seconds
- `test_rate_limit_per_user_isolation` - User A doesn't affect User B
- `test_auth_endpoints_have_stricter_limits` - Login limited to 10/min

**MVP Note**: In-memory rate limiting resets on server restart. This is acceptable for single-server MVP. Migrate to Redis in Phase 8+ for horizontal scaling.

#### 5.2: Input Sanitization (30 min)
**Library**: None (uses Pydantic validators + Python stdlib)

**Files**:
- Update `app/schemas/task.py` - Add validators
- `tests/schemas/test_task_validation.py` - Validation tests

**Functions**:
- `@field_validator` decorators on Pydantic models
- Uses Python's `html.escape()` for XSS prevention

**Implementation**:
```python
from pydantic import BaseModel, field_validator
import html

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None

    @field_validator('title')
    def sanitize_title(cls, v):
        # Remove HTML tags and escape special chars
        v = html.escape(v)
        # Limit length
        if len(v) > 200:
            raise ValueError("Title must be 200 characters or less")
        return v.strip()

    @field_validator('description')
    def sanitize_description(cls, v):
        if v is None:
            return v
        v = html.escape(v)
        if len(v) > 2000:
            raise ValueError("Description must be 2000 characters or less")
        return v.strip()
```

**Tests**:
- `test_sanitize_escapes_html_in_title` - XSS prevention
- `test_sanitize_preserves_safe_content` - Normal text unchanged
- `test_sanitize_handles_unicode` - UTF-8 support
- `test_title_length_validation` - Length limits enforced
- `test_description_length_validation` - Description limits enforced

**Benefits**:
- ✅ No new dependencies (uses Python stdlib)
- ✅ Validation at schema level (clear separation)
- ✅ Better error messages (Pydantic validation)
- ✅ Type-safe (integrated with existing models)

#### 5.3: Structured Logging (1 hour)
**Library**: `structlog` (structured logging)

**Files**:
- `app/logging_config.py` - Logging setup
- `app/middleware/request_logging.py` - Request/response logging + request ID
- Update `app/main.py` - Register logging middleware

**Functions**:
- `setup_logging()` - Configure structlog with JSON renderer
- `log_request()` - Log incoming requests with context
- `log_response()` - Log responses with timing
- `log_error()` - Log exceptions with stack traces
- `RequestIDMiddleware` - Add unique request ID to each request

**Implementation**:
```python
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.state.request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

# Logging config
import structlog

def setup_logging():
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer() if settings.ENVIRONMENT == "production"
            else structlog.dev.ConsoleRenderer()
        ]
    )
```

**Tests**:
- `test_logging_includes_request_id` - Each request has unique ID
- `test_logging_includes_user_id` - Authenticated requests log user
- `test_logging_json_format_in_prod` - Production uses JSON logs
- `test_logging_human_format_in_dev` - Dev uses readable logs
- `test_request_id_in_response_header` - X-Request-ID header present

**Benefits**:
- Request ID makes debugging easy (trace request through logs)
- JSON logs in production (parseable by log aggregators)
- Human-readable logs in development

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

#### 5.5: Database Migrations (1.5 hours)
**Library**: `alembic` (database migrations)

**Files**:
- `alembic/env.py` - Alembic configuration
- `alembic/versions/001_initial_schema.py` - Initial migration from existing models
- `Makefile` - Add migration commands
- Update `tests/conftest.py` - Use migrations instead of `create_all()`

**Migration Strategy** (Critical for existing deployments):

**Step 1: Initialize Alembic** (15 min)
```bash
# Initialize Alembic
alembic init alembic

# Configure alembic.ini to use DATABASE_URL from settings
```

**Step 2: Generate Initial Migration** (30 min)
```bash
# Generate migration from current SQLAlchemy models
alembic revision --autogenerate -m "Initial schema from Phase 1-4"

# Review generated migration
# Verify it creates: users, tasks, user_preferences, audit_logs tables
```

**Step 3: Handle Existing Deployments** (15 min)
```bash
# For databases already created with create_all()
alembic stamp head  # Mark current schema as migrated (don't recreate tables)

# For new deployments
alembic upgrade head  # Run migrations to create tables
```

**Step 4: Update Tests** (30 min)
```python
# tests/conftest.py - Replace create_all with migrations
@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Use Alembic instead of create_all
    with engine.begin() as conn:
        alembic_cfg = Config("alembic.ini")
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public"))
        command.upgrade(alembic_cfg, "head")

    yield engine

    await engine.dispose()
```

**Makefile Commands**:
```makefile
migrate-create:  # Create new migration
	alembic revision --autogenerate -m "$(message)"

migrate-up:  # Apply all pending migrations
	alembic upgrade head

migrate-down:  # Rollback last migration
	alembic downgrade -1

migrate-history:  # Show migration history
	alembic history

migrate-current:  # Show current revision
	alembic current
```

**Tests**:
- `test_migration_creates_all_tables` - Initial migration creates users, tasks, etc.
- `test_migration_is_reversible` - Can rollback (`downgrade -1`)
- `test_migration_matches_models` - Generated schema matches SQLAlchemy models
- `test_migration_preserves_data` - Existing data not lost on upgrade
- `test_migration_version_tracking` - alembic_version table tracks current revision

**Critical Success Criteria**:
- ✅ Migration creates same schema as `Base.metadata.create_all()`
- ✅ Migration is fully reversible (rollback tested)
- ✅ Existing Phase 4 deployments can adopt Alembic with `stamp head`
- ✅ Tests use migrations instead of `create_all()`

#### 5.6: Enhanced Health Checks (30 min)
**Files**:
- Update `app/api/health.py` - Add database connectivity check

**Functions**:
- `check_database_health()` - Test DB connection with simple query
- `get_health_status()` - Aggregate health checks with granular status

**Implementation**:
```python
from sqlalchemy import text

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Enhanced health check with dependency status."""
    health = {
        "status": "healthy",
        "version": "4.0.0",
        "environment": settings.ENVIRONMENT,
        "checks": {}
    }

    # Database connectivity check
    try:
        await db.execute(text("SELECT 1"))
        health["checks"]["database"] = "healthy"
    except Exception as e:
        health["checks"]["database"] = "unhealthy"
        health["status"] = "degraded"
        logger.error("Database health check failed", error=str(e))

    status_code = 200 if health["status"] == "healthy" else 503
    return JSONResponse(content=health, status_code=status_code)
```

**Tests**:
- `test_health_check_includes_database_status` - DB status in response
- `test_health_check_returns_503_on_db_failure` - Unhealthy when DB down
- `test_health_check_includes_version` - API version in response
- `test_health_check_degraded_mode` - Returns 503 with details when DB down

**Benefits**:
- Partial degradation (app still responds with error details)
- Version info helps debugging ("which version is deployed?")
- Granular checks (know exactly what's broken)

### Dependencies to Add
```toml
slowapi = "^0.1.9"          # Rate limiting (in-memory storage for MVP)
structlog = "^24.1.0"       # Structured logging
sentry-sdk = "^1.40.0"      # Error monitoring
alembic = "^1.13.0"         # Database migrations
```

**Removed from original plan**:
- ❌ `redis` - Not needed (using in-memory rate limiting for MVP)
- ❌ `bleach` - Not needed (using Pydantic validators + html.escape)

**Cost Savings**: No Redis infrastructure ($15-25/month saved)

### Success Criteria
- All 93+ tests passing (20 new + 73 existing)
- >90% code coverage
- Rate limiting active on all endpoints (in-memory storage)
- No XSS vulnerabilities (Pydantic validation tested)
- JSON logs in production, readable logs in dev
- Request ID tracking in all logs
- Sentry captures exceptions with user context
- Database migrations fully reversible
- Existing Phase 4 deployments can adopt Alembic without data loss
- Health checks include DB connectivity with degraded mode

### Time Budget (Optimized)
- Rate limiting: 1 hour (down from 1.5hrs - no Redis setup)
- Input sanitization: 30 min (down from 1hr - Pydantic validators)
- Structured logging + request ID: 1 hour
- Error monitoring: 1.5 hours
- Database migrations: 1.5 hours (down from 2hrs - clearer strategy)
- Enhanced health checks: 30 min
- **Total**: 5.5 hours (6hrs with buffer)

**Time Saved**: 1.5-2 hours vs original plan

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

### Scoring Algorithm (Enhanced)
```python
score = (
    deadline_urgency * 40  # 0-50 points (due today = 40, overdue = 50)
    + priority * 10        # 10-50 points (priority 1-5)
    + effort_bonus * 10    # 0-10 points (prefer quick wins)
) * time_of_day_multiplier  # 0.9-1.1 (±10% based on user preferences)
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

**Time-of-Day Multiplier** (NEW):
- Matches preferred time: 1.1 (10% bonus)
- No preference: 1.0 (neutral)
- Wrong time of day: 0.9 (10% penalty)

**Example 1** (Basic):
- Task: "Write blog post"
- Due: Today
- Priority: 4 (high)
- Effort: 30 min
- Preferred time: None
- **Score**: (40 + 40 + 7.5) * 1.0 = 87.5 points

**Example 2** (Time-aware):
- Task: "Morning review"
- Due: Today
- Priority: 3 (medium)
- Effort: 15 min
- Preferred time: "morning"
- Current time: 9:00 AM
- **Score**: (40 + 30 + 10) * 1.1 = 88 points

### Key Components

#### 6.1: Scoring Service (2 hours)
**Files**:
- `app/services/scoring.py` - Task scoring logic
- `app/db/crud.py` - Add score calculation to TaskCRUD
- `tests/services/test_scoring.py` - Scoring tests

**Functions**:
- `calculate_task_score()` - Main scoring function with time-of-day awareness
- `calculate_deadline_urgency()` - Urgency from due_date
- `calculate_effort_bonus()` - Bonus from effort estimate
- `calculate_time_of_day_multiplier()` - Time preference matching (NEW)
- `get_tasks_ranked_by_score()` - Return sorted task list

**Implementation** (Time-of-Day):
```python
def calculate_time_of_day_multiplier(task, current_hour: int) -> float:
    """Apply bonus/penalty based on time preferences."""
    if not task.preferred_time:
        return 1.0  # No preference

    # Define time windows
    if task.preferred_time == "morning" and 6 <= current_hour < 12:
        return 1.1  # 10% bonus
    elif task.preferred_time == "afternoon" and 12 <= current_hour < 18:
        return 1.1
    elif task.preferred_time == "evening" and 18 <= current_hour < 22:
        return 1.1
    else:
        return 0.9  # 10% penalty for wrong time
```

**Tests**:
- `test_overdue_task_has_highest_urgency` - Overdue = 1.25 multiplier
- `test_due_today_has_full_urgency` - Due today = 1.0
- `test_high_priority_increases_score` - Priority 5 > Priority 1
- `test_quick_tasks_get_effort_bonus` - ≤15min gets bonus
- `test_no_deadline_has_zero_urgency` - No due_date = 0 urgency
- `test_tasks_sorted_by_score_descending` - Highest score first
- `test_equal_scores_sort_by_created_date` - Tie-breaker
- `test_time_of_day_bonus_applied` - Morning task at 9am gets 1.1x (NEW)
- `test_time_of_day_penalty_applied` - Morning task at 8pm gets 0.9x (NEW)
- `test_no_time_preference_neutral` - No preference = 1.0x (NEW)

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

#### 6.3: Score Caching (30 min)
**Library**: None (in-memory Python dict)

**Files**:
- `app/services/cache.py` - In-memory score caching logic
- `app/config.py` - Add cache TTL settings

**Functions**:
- `cache_task_score()` - Cache score with timestamp (in-memory dict)
- `invalidate_task_cache()` - Clear cache on task update
- `get_cached_score()` - Retrieve cached score if fresh (< 5 min old)

**Implementation**:
```python
from datetime import datetime, timedelta
from typing import Optional

# Simple in-memory cache
_score_cache: dict[str, dict] = {}
_CACHE_TTL = timedelta(minutes=5)

def get_cached_score(task_id: str) -> Optional[float]:
    """Get cached score if fresh."""
    cached = _score_cache.get(task_id)
    if cached and (datetime.utcnow() - cached['timestamp']) < _CACHE_TTL:
        return cached['score']
    return None

def cache_task_score(task_id: str, score: float):
    """Cache score with timestamp."""
    _score_cache[task_id] = {
        'score': score,
        'timestamp': datetime.utcnow()
    }

def invalidate_task_cache(task_id: str):
    """Remove task from cache (called on update)."""
    _score_cache.pop(task_id, None)
```

**Tests**:
- `test_cache_stores_calculated_scores` - Scores cached with timestamp
- `test_cache_returns_cached_scores` - Cache hit works
- `test_cache_expires_after_ttl` - 5min expiration
- `test_cache_invalidated_on_update` - Update clears cache
- `test_cache_miss_returns_none` - Unknown task returns None

**MVP Note**: In-memory cache is cleared on server restart. This is acceptable for MVP (<10k tasks). Migrate to Redis in Phase 8+ for horizontal scaling.

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
- All 96+ tests passing (13 new + 83 existing from Phase 5)
- >85% code coverage
- Best task endpoint returns highest-scored task
- Scoring algorithm matches Phase 1 prototype + time-of-day awareness
- Score caching reduces DB load (in-memory)
- Transparent reasoning in response
- Time-of-day multiplier working (10% bonus/penalty)

### Time Budget (Optimized)
- Scoring service: 2 hours (includes time-of-day logic)
- Best task endpoint: 1.5 hours
- Score caching: 30 min (down from 1hr - in-memory dict)
- **Total**: 4 hours (4.5hrs with buffer)

**Time Saved**: 30 min vs original plan (no Redis cache setup)

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
**Recommendation**: PostgreSQL on same droplet for MVP (save $15/month)

**Why This Works for MVP**:
- ✅ 2GB RAM handles PostgreSQL + FastAPI easily (<1000 users)
- ✅ DigitalOcean automated backups included
- ✅ Can migrate to managed DB later with zero code changes
- ✅ Standard pattern for single-server deployments

**Configuration**:
```bash
# Install PostgreSQL on droplet
apt install -y postgresql-15 postgresql-contrib

# Create production database
sudo -u postgres createdb mindflow_prod

# Run migrations (using Alembic from Phase 5)
cd /opt/mindflow/backend
alembic upgrade head

# Create app user (limited permissions for security)
sudo -u postgres psql <<EOF
CREATE USER mindflow_app WITH PASSWORD 'secure_random_password';
GRANT CONNECT ON DATABASE mindflow_prod TO mindflow_app;
\c mindflow_prod
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mindflow_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO mindflow_app;
EOF
```

**When to Upgrade to Managed PostgreSQL**:
- Database size >10GB
- 24/7 uptime requirement (>99.9%)
- Multiple regions needed
- Advanced features (read replicas, point-in-time recovery)

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

#### 7.6: CI/CD Pipeline (45 min)
**Files**:
- `.github/workflows/deploy.yml` - GitHub Actions workflow with rollback safety

**Enhanced Workflow** (with rollback on failure):
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
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install uv
        run: pip install uv
      - name: Run tests
        run: |
          cd backend
          uv sync
          uv run pytest --cov

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy with rollback on failure
        run: |
          ssh deploy@${{ secrets.SERVER_IP }} 'bash -s' << 'EOF'
            set -e  # Exit on any error

            cd /opt/mindflow

            # Backup current version
            LAST_COMMIT=$(git rev-parse HEAD)
            echo $LAST_COMMIT > .last-deploy
            echo "Current version: $LAST_COMMIT"

            # Pull new code
            git pull origin main
            NEW_COMMIT=$(git rev-parse HEAD)
            echo "New version: $NEW_COMMIT"

            # Install dependencies
            cd backend
            uv sync

            # Run migrations (with rollback on failure)
            if ! alembic upgrade head; then
              echo "❌ Migration failed, rolling back..."
              alembic downgrade -1
              git reset --hard $LAST_COMMIT
              exit 1
            fi

            # Restart service
            sudo systemctl restart mindflow

            # Health check (wait 10 seconds for startup)
            echo "Waiting for service to start..."
            sleep 10

            # Verify health endpoint
            if ! curl -f http://localhost:8000/health; then
              echo "❌ Health check failed, rolling back..."
              git reset --hard $LAST_COMMIT
              alembic downgrade -1
              sudo systemctl restart mindflow
              exit 1
            fi

            echo "✅ Deployment successful: $NEW_COMMIT"
          EOF
```

**Key Safety Features**:
- ✅ Automatic rollback on migration failure
- ✅ Health check validation after deployment
- ✅ Version tracking for quick rollback
- ✅ Clear error messages with status emojis
- ✅ Database schema rollback on failure

**Time Increased**: 45 min (up from 30 min) - worth it for safety

### Cost Breakdown (Optimized for MVP)

| Component | Cost/Month | Notes |
|-----------|------------|-------|
| **DigitalOcean Droplet (2GB)** | $12 | Includes PostgreSQL + FastAPI |
| **Domain name** | $1-2 | namecheap.com or similar |
| **Sentry Free Tier** | $0 | 5,000 errors/month |
| **SSL Certificate** | $0 | Let's Encrypt (free) |
| **GitHub Actions** | $0 | 2,000 min/month free tier |
| **TOTAL (MVP)** | **$13-14/month** | |

**Cost Savings vs Original Plan**:
- ❌ No Redis ($15-25/month saved)
- ❌ No Managed PostgreSQL ($15/month saved)
- **Total Savings**: **$30-40/month** = **$360-480/year**

**Upgrade Path** (when needed):
| Component | Trigger | Added Cost |
|-----------|---------|------------|
| Managed PostgreSQL | >10GB DB or >99.9% uptime needed | +$15/month |
| Redis (managed) | Horizontal scaling (>1 server) | +$15/month |
| Larger Droplet (4GB) | >1000 concurrent users | +$12/month |

**Sweet Spot**: MVP runs well on $13-14/month until ~500-1000 users

### Success Criteria
- Application accessible via HTTPS
- SSL certificate valid (Let's Encrypt auto-renewal working)
- Systemd service runs automatically on boot
- Database migrations applied successfully
- Environment variables secure (600 permissions, owned by app user)
- CI/CD deploys on git push to main with automatic rollback on failure
- Health check returns 200 with version and DB status
- Can register user and create tasks via public API
- PostgreSQL running on same droplet (no managed DB needed)
- No Redis infrastructure (in-memory rate limiting working)

### Time Budget (Updated)
- Server setup: 1 hour
- Database setup (on droplet): 30 min
- Nginx & SSL: 45 min
- Systemd service: 15 min
- Environment variables: 15 min
- CI/CD pipeline with rollback: 45 min (up from 30 min)
- **Total**: 3.25 hours (3.5hrs with buffer)

**Time Increase**: +15 min for enhanced CI/CD safety (worth it)

---

## Complete Timeline (Updated)

### ✅ Completed (Phases 1-4)
- **Phase 1**: Prototype - Complete
- **Phase 2**: Database Layer - 4 hours (19 tests)
- **Phase 3**: API Endpoints - 4 hours (21 tests)
- **Phase 4**: Authentication & JWT - 6-7 hours (33 tests, 73 total)
- **Total Completed**: 18-19 hours

### 📋 Remaining (Phases 5-7)

**Week 1** (11-12.5 hours):
- **Day 1-2**: Phase 5 (Production Hardening) - 5.5-6 hours
  - Rate limiting (1hr)
  - Input sanitization (30min)
  - Structured logging (1hr)
  - Error monitoring (1.5hrs)
  - Database migrations (1.5hrs)
  - Enhanced health checks (30min)

- **Day 3**: Phase 6 (Task Scoring) - 4-4.5 hours
  - Scoring service with time-of-day (2hrs)
  - Best task endpoint (1.5hrs)
  - Score caching (30min)

- **Day 4**: Phase 7 (Deployment) - 3.25-3.5 hours
  - Server + DB setup (1.5hrs)
  - Nginx & SSL (45min)
  - Systemd service (15min)
  - Environment setup (15min)
  - CI/CD with rollback (45min)

**Total Remaining**: 11-14 hours actual work (2-3 focused days)
**Grand Total**: 29-33 hours across all 7 phases

---

## Dependencies Summary (Optimized)

### Phase 4 (Complete) ✅
```toml
bcrypt = "^4.0.0"              # Password hashing (direct, not passlib)
pyjwt = "^2.8.0"               # JWT tokens (direct, not python-jose)
```

### Phase 5 (Planned)
```toml
slowapi = "^0.1.9"             # Rate limiting (in-memory, no Redis)
structlog = "^24.1.0"          # Structured logging
sentry-sdk = "^1.40.0"         # Error monitoring (free tier)
alembic = "^1.13.0"            # Database migrations
```

**Removed from original plan**:
- ❌ `redis` - Using in-memory storage for MVP
- ❌ `bleach` - Using Pydantic validators + html.escape

### Phase 6 (Planned)
```toml
# No new dependencies
# Uses in-memory dict for caching (no Redis)
```

### Phase 7 (Planned)
```bash
# System packages (Ubuntu 22.04 LTS)
nginx                          # Reverse proxy
postgresql-15                  # Database (on same droplet)
certbot                        # SSL certificates (Let's Encrypt)
python3.11                     # Python runtime
```

**Total Python Dependencies**: 7 packages (down from 9 in original plan)
**Infrastructure Dependencies**: 0 managed services (save $30-40/month)

---

## Test Coverage Targets (Updated)

| Phase | New Tests | Cumulative Tests | Coverage Target | Status |
|-------|-----------|------------------|-----------------|--------|
| 1 | Manual | N/A | N/A | ✅ Complete |
| 2 | 19 | 19 | 90% | ✅ Complete |
| 3 | 21 | 40 | 88% | ✅ Complete |
| 4 | 33 | 73 | 88% | ✅ Complete |
| 5 | 20+ | 93+ | 90% | 📋 Planned |
| 6 | 13+ | 106+ | 85% | 📋 Planned |
| 7 | Integration | 106+ | N/A | 📋 Planned |

**Current Status**: 73 tests passing, 88% coverage
**Target**: 106+ tests, 90% coverage after Phase 6

---

## Risk Mitigation (Updated)

### Phase 5 Risks
- **In-memory rate limit reset on restart**: ✅ Acceptable for MVP, won't affect users long-term
- **Sentry costs**: ✅ Free tier (5,000 errors/month) sufficient for MVP
- **Migration failures**: ✅ All migrations reversible + rollback logic in CI/CD
- **Alembic adoption**: ✅ Existing deployments use `alembic stamp head` (no data loss)

### Phase 6 Risks
- **In-memory cache lost on restart**: ✅ Acceptable, recalculates on first request
- **Cache inconsistency**: ✅ 5min TTL limits stale data
- **Scoring performance**: ✅ Cache reduces DB load by ~80%
- **Algorithm tuning**: ✅ Easy to adjust multipliers without code changes

### Phase 7 Risks
- **PostgreSQL on same droplet**: ✅ Mitigated by DigitalOcean automated backups
- **Deployment downtime**: ✅ Systemd restart takes <5 seconds
- **Migration rollback failure**: ✅ CI/CD tests health endpoint before accepting deploy
- **SSL expiration**: ✅ Certbot auto-renewal runs weekly
- **Database backups**: ✅ DigitalOcean automated daily backups (7-day retention)

### NEW: Cost/Complexity Trade-offs
**Decision: In-Memory Solutions for MVP**

**Pros**:
- ✅ $30-40/month cost savings ($360-480/year)
- ✅ Zero infrastructure setup complexity
- ✅ Faster (no network calls)
- ✅ Can migrate to Redis later with minimal code changes

**Cons**:
- ⚠️ Rate limits reset on restart (acceptable for <1000 users)
- ⚠️ Cache lost on restart (acceptable, auto-recalculates)
- ⚠️ Won't work with horizontal scaling (not needed until Phase 8+)

**When to Migrate to Redis**:
- Horizontal scaling needed (>1 server)
- Rate limit persistence critical (>1000 concurrent users)
- Multi-region deployment

**Verdict**: In-memory is correct choice for MVP. Migrate in Phase 8+.

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

## Summary of Changes from Original Plan

### ✅ Optimizations Implemented

**Cost Savings**:
- Removed Redis dependency → Save $15-25/month
- PostgreSQL on droplet instead of managed → Save $15/month
- **Total Savings**: $30-40/month = $360-480/year

**Time Savings**:
- Phase 5: 5.5hrs (down from 7.5hrs) → Save 2 hours
- Phase 6: 4hrs (down from 4.5hrs) → Save 30 min
- **Total Time Saved**: 2.5 hours

**Complexity Reduction**:
- 2 fewer Python dependencies (bleach, redis)
- 0 managed services to configure
- In-memory solutions (simpler, faster)

**Safety Improvements**:
- Enhanced CI/CD with automatic rollback
- Health check validation before accepting deployments
- Alembic migration strategy for existing deployments
- Version tracking for quick rollback

### 📊 Final Numbers

| Metric | Original Plan | Optimized Plan | Improvement |
|--------|--------------|----------------|-------------|
| **Remaining Time** | 18-23 hours | 11-14 hours | **-7 to -9 hours** |
| **Monthly Cost** | $28-29 | $13-14 | **-$15 savings** |
| **Dependencies** | 9 packages | 7 packages | **-2 packages** |
| **Infrastructure** | 3 services | 1 service | **-2 services** |
| **Tests (final)** | 85+ | 106+ | **+21 tests** |

### 🎯 Ready to Execute

**Next Step**: Start with Phase 5 (Production Hardening)

**Current State**:
- ✅ 73 tests passing
- ✅ 88% code coverage
- ✅ JWT authentication working
- ✅ All Phase 1-4 complete

**Remaining Work**: 11-14 hours (2-3 focused days)
