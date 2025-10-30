# MindFlow: System Architecture

**Last Updated**: 2025-10-30
**Status**: Production-Ready Design
**Target**: ChatGPT Custom Application with FastAPI Backend

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Tech Stack Decisions](#tech-stack-decisions)
4. [Data Model](#data-model)
5. [API Design](#api-design)
6. [Task Scoring Algorithm](#task-scoring-algorithm)
7. [Real-Time Updates](#real-time-updates)
8. [Security & Multi-Tenancy](#security--multi-tenancy)

---

## System Overview

**MindFlow** is an AI-first task manager that replaces traditional UI forms with natural conversation. Users interact with GPT to manage tasks, and the system intelligently suggests "what to do next" based on context-aware scoring.

### Core User Flow

```
User: "Add blog post about FastAPI, due Friday, high priority"
  ↓
ChatGPT: [Parses intent, calls create_task function]
  ↓
FastAPI Backend: [Validates, stores in Postgres]
  ↓
ChatGPT: "Created task: 'Blog post about FastAPI' (Priority: 5/5, Due: Nov 3)"

User: "What should I do next?"
  ↓
ChatGPT: [Calls get_best_task function]
  ↓
FastAPI: [Scores all pending tasks, returns highest]
  ↓
ChatGPT: "I recommend: 'Blog post about FastAPI' - due in 2 days, high priority"
```

### Key Differentiators

| Feature | Todoist | Asana | MindFlow |
|---------|---------|-------|----------|
| **Primary Interface** | GUI Forms | Web/Mobile App | Natural Conversation |
| **Task Input** | Manual clicks | Forms + templates | "Add X due Y" |
| **Prioritization** | Manual sorting | Basic AI suggestions | Context-aware scoring |
| **Intelligence** | None | Limited | Learns user patterns |
| **Conversation** | No | No | Central to UX |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    USER (Browser/Mobile)                     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS
┌─────────────────────────────────────────────────────────────┐
│                  CHATGPT CUSTOM GPT                          │
│  • System prompt defines personality                         │
│  • Function calling for task operations                      │
│  • Conversation context management                           │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS (OpenAI Actions)
┌─────────────────────────────────────────────────────────────┐
│              FASTAPI BACKEND (Python 3.11+)                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ REST Endpoints                                       │   │
│  │  POST /api/tasks         - Create task              │   │
│  │  GET  /api/tasks         - List tasks               │   │
│  │  GET  /api/tasks/best    - Get next task            │   │
│  │  PUT  /api/tasks/{id}    - Update task              │   │
│  │  POST /api/auth/login    - Authenticate             │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Business Logic                                       │   │
│  │  • Task scoring engine (relevance algorithm)        │   │
│  │  • JWT authentication                               │   │
│  │  • Request validation (Pydantic)                    │   │
│  │  • OpenAI function execution                        │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │ SQL (asyncpg)
┌─────────────────────────────────────────────────────────────┐
│         POSTGRESQL DATABASE (Supabase Managed)               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Tables:                                              │   │
│  │  • users (id, email, password_hash, plan)           │   │
│  │  • tasks (id, user_id, title, status, priority,     │   │
│  │            due_date, created_at)                     │   │
│  │  • user_preferences (scoring weights, timezone)     │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Features:                                            │   │
│  │  • Row-Level Security (RLS) for multi-tenancy       │   │
│  │  • Real-time subscriptions (optional)               │   │
│  │  • Full-text search on task titles/descriptions     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack Decisions

### Backend: FastAPI

**Why FastAPI over Django/Flask:**
- **Async Native**: Non-blocking I/O for database and OpenAI API calls
- **Type Safety**: Pydantic models ensure runtime validation
- **Auto-Generated Docs**: OpenAPI/Swagger at `/docs` endpoint
- **Performance**: Handles 1000+ concurrent requests on modest hardware
- **Modern Python**: Uses Python 3.11+ features (async/await, type hints)

**Key Dependencies:**
```
fastapi==0.104.1
uvicorn[standard]==0.24.0       # ASGI server
sqlalchemy[asyncio]==2.0.23     # ORM with async support
asyncpg==0.29.0                 # Fast PostgreSQL driver
pydantic==2.5.0                 # Data validation
python-jose[cryptography]==3.3.0  # JWT tokens
openai==1.3.9                   # GPT-4 function calling
```

### Database: PostgreSQL (Supabase)

**Why Postgres over MongoDB/Firebase:**
- **Relational Model**: Tasks have clear relationships (user → tasks)
- **JSONB Support**: Flexible metadata storage when needed
- **Row-Level Security**: Built-in multi-tenancy at database level
- **Real-Time Subscriptions**: WebSocket broadcasts via logical replication
- **Cost**: $25/month shared tier scales to 100K+ users

**Supabase Benefits:**
- Managed hosting (no DevOps)
- Built-in authentication (can replace JWT if needed)
- Database GUI for debugging
- Automatic backups

### Frontend: LIT + TypeScript (Optional Dashboard)

**Why LIT over React:**
- **Web Components**: Framework-agnostic, works anywhere
- **Bundle Size**: ~50KB vs React's 200KB+ with dependencies
- **TypeScript Native**: Full type safety
- **Fast Compilation**: No JSX transform overhead

**Note**: ChatGPT Custom GPT handles primary UI. Dashboard is optional for power users.

### Deployment: Fly.io

**Why Fly.io over Heroku/Vercel:**
- **Docker Native**: Deploy any containerized app
- **Global Edge Network**: 30+ regions worldwide
- **Pricing**: Pay-as-you-go ($10-50/month for MVP)
- **Postgres Included**: Managed database attachments
- **CLI**: `flyctl deploy` works out-of-box

---

## Data Model

### Core Tables

#### `users`

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    plan VARCHAR(50) DEFAULT 'free',  -- free, pro, enterprise
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
```

#### `tasks`

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Core fields
    title VARCHAR(256) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, in_progress, completed, snoozed
    priority INTEGER DEFAULT 3,            -- 1-5 scale

    -- Temporal
    due_date TIMESTAMP,
    snoozed_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,

    -- Metadata
    tags TEXT,  -- Comma-separated for simplicity
    context_metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_tasks_user_status ON tasks(user_id, status);
CREATE INDEX idx_tasks_due_date ON tasks(user_id, due_date);
```

#### `user_preferences`

```sql
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Scoring weights (0.0-1.0, must sum to 1.0)
    weight_urgency FLOAT DEFAULT 0.40,
    weight_priority FLOAT DEFAULT 0.35,
    weight_impact FLOAT DEFAULT 0.15,
    weight_effort FLOAT DEFAULT 0.10,

    -- Time preferences
    timezone VARCHAR(50) DEFAULT 'UTC',
    work_start_time TIME DEFAULT '09:00',
    work_end_time TIME DEFAULT '17:00',

    -- AI configuration
    enable_habit_learning BOOLEAN DEFAULT true
);
```

### Data Validation Rules

**Task Constraints:**
- `title`: 1-256 characters, required
- `description`: 0-1000 characters, optional
- `status`: Must be in ['pending', 'in_progress', 'completed', 'snoozed']
- `priority`: Integer 1-5 (enforced by Pydantic)
- `due_date`: ISO8601 timestamp, optional
- `tags`: Comma-separated string, max 500 chars

**User Preferences:**
- Scoring weights must sum to 1.0 (enforced in application logic)
- `timezone`: Valid IANA timezone string (e.g., "America/New_York")

---

## API Design

### OpenAPI Function Definitions (for ChatGPT)

```yaml
openapi: 3.0.0
info:
  title: MindFlow API
  version: 1.0.0

paths:
  /api/tasks:
    post:
      operationId: create_task
      summary: Create a new task
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                title:
                  type: string
                  description: Task title (required)
                description:
                  type: string
                priority:
                  type: integer
                  minimum: 1
                  maximum: 5
                due_date:
                  type: string
                  format: date-time
                tags:
                  type: string
              required:
                - title
      responses:
        '201':
          description: Task created successfully

  /api/tasks/best:
    get:
      operationId: get_best_task
      summary: Get the highest-priority task to work on now
      responses:
        '200':
          description: Best task with explanation
          content:
            application/json:
              schema:
                type: object
                properties:
                  task:
                    $ref: '#/components/schemas/Task'
                  score:
                    type: number
                  explanation:
                    type: string
```

### Request/Response Examples

**Create Task:**
```bash
POST /api/tasks
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "title": "Blog post about FastAPI",
  "description": "Cover async patterns and deployment",
  "priority": 5,
  "due_date": "2025-11-03T17:00:00Z",
  "tags": "writing,technical"
}

# Response (201 Created)
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Blog post about FastAPI",
  "status": "pending",
  "priority": 5,
  "due_date": "2025-11-03T17:00:00Z",
  "created_at": "2025-10-30T14:30:00Z"
}
```

**Get Best Task:**
```bash
GET /api/tasks/best
Authorization: Bearer <jwt_token>

# Response (200 OK)
{
  "task": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Blog post about FastAPI",
    "priority": 5,
    "due_date": "2025-11-03T17:00:00Z"
  },
  "score": 0.87,
  "explanation": "High priority (5/5) and due in 3 days. Estimated 2 hours."
}
```

---

## Task Scoring Algorithm

### Relevance Formula

```
score = (w_urgency × urgency) + (w_priority × priority) +
        (w_impact × impact) + (w_effort × effort)

where:
  w_urgency + w_priority + w_impact + w_effort = 1.0
```

### Component Calculations

**1. Urgency Score (0-1):**
```python
def urgency_score(task, now):
    if not task.due_date:
        return 0.3  # No deadline = medium urgency

    hours_until_due = (task.due_date - now).total_seconds() / 3600

    if hours_until_due < 0:        # Overdue
        return 1.0
    elif hours_until_due < 4:      # < 4 hours
        return 0.9
    elif hours_until_due < 24:     # < 1 day
        return 0.7
    elif hours_until_due < 168:    # < 1 week
        return 0.4
    else:
        return 0.1
```

**2. Priority Score (0-1):**
```python
def priority_score(task):
    return task.priority / 5.0  # Normalize 1-5 scale to 0-1
```

**3. Impact Score (0-1):**
```python
def impact_score(task):
    # High priority + shorter task = high impact per unit time
    priority_norm = task.priority / 5.0
    effort_minutes = task.effort_estimate_minutes or 30
    effort_factor = 1.0 - min(effort_minutes / 480.0, 1.0)  # 480 min = 8 hours

    return priority_norm * effort_factor
```

**4. Effort Score (0-1):**
```python
def effort_score(task):
    # Prefer shorter tasks (quick wins)
    effort_minutes = task.effort_estimate_minutes or 30
    return 1.0 - min(effort_minutes / 120.0, 1.0)  # 120 min = 2 hours
```

### Default Weights

```python
DEFAULT_WEIGHTS = {
    'urgency': 0.40,   # Deadline proximity is most important
    'priority': 0.35,  # User-set importance
    'impact': 0.15,    # Value per unit time
    'effort': 0.10     # Slight preference for quick wins
}
```

### Explanation Generation

```python
def explain_score(task, components):
    reasons = []

    if components['urgency'] > 0.7:
        if task.due_date:
            delta = task.due_date - datetime.now()
            if delta.days == 0:
                reasons.append("due TODAY")
            elif delta.days < 0:
                reasons.append("OVERDUE")
            else:
                reasons.append(f"due in {delta.days} days")

    if components['priority'] >= 0.8:
        reasons.append("high priority (5/5)")
    elif components['priority'] >= 0.6:
        reasons.append("medium-high priority")

    if components['effort'] > 0.7:
        reasons.append(f"quick task (~{task.effort_estimate_minutes}min)")

    return "I recommend this because: " + ", ".join(reasons)
```

---

## Real-Time Updates

### Approach 1: Polling (Simple MVP)

**Frontend polls every 30 seconds:**
```typescript
setInterval(async () => {
  const response = await fetch('/api/tasks?status=pending');
  const tasks = await response.json();
  updateUI(tasks);
}, 30000);
```

**Pros:** Simple, works everywhere
**Cons:** Wastes bandwidth, 30s latency

### Approach 2: WebSockets (Production)

**Backend WebSocket handler:**
```python
from fastapi import WebSocket

@app.websocket("/ws/tasks")
async def websocket_endpoint(websocket: WebSocket, token: str):
    await websocket.accept()
    user_id = verify_jwt(token)

    # Register connection
    connections[user_id].add(websocket)

    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        connections[user_id].remove(websocket)

# Broadcast task updates
async def broadcast_task_update(user_id: UUID, task: Task):
    for ws in connections[user_id]:
        await ws.send_json({
            "type": "task_updated",
            "task": task.dict()
        })
```

**Frontend WebSocket client:**
```typescript
const ws = new WebSocket('wss://api.mindflow.app/ws/tasks?token=' + jwt);

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  if (update.type === 'task_updated') {
    updateTaskInUI(update.task);
  }
};
```

**Pros:** Real-time, efficient
**Cons:** More complex, requires connection management

### Approach 3: Supabase Realtime (Recommended)

**Enable Postgres logical replication:**
```sql
ALTER PUBLICATION supabase_realtime ADD TABLE tasks;
```

**Frontend subscribes to changes:**
```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

supabase
  .channel('tasks')
  .on('postgres_changes',
      { event: '*', schema: 'public', table: 'tasks' },
      (payload) => {
        console.log('Task changed:', payload.new);
        updateUI(payload.new);
      }
  )
  .subscribe();
```

**Pros:** Zero backend code, scales automatically
**Cons:** Requires Supabase

---

## Security & Multi-Tenancy

### Authentication: JWT Tokens

```python
from jose import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY")

def create_access_token(user_id: UUID) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> UUID:
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return UUID(payload["sub"])
```

### Multi-Tenancy: Row-Level Security

**Automatic user_id filtering:**
```python
@app.get("/api/tasks")
async def list_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Task)
        .where(Task.user_id == current_user.id)
        .where(Task.status != 'completed')
    )
    return result.scalars().all()
```

**Database-level enforcement (Supabase RLS):**
```sql
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only see own tasks"
  ON tasks FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can only insert own tasks"
  ON tasks FOR INSERT
  WITH CHECK (auth.uid() = user_id);
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/tasks")
@limiter.limit("100/minute")
async def create_task(request: Request, ...):
    # Only 100 task creations per minute per IP
    pass
```

### Input Validation

```python
from pydantic import BaseModel, Field, validator

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    priority: int = Field(default=3, ge=1, le=5)
    due_date: Optional[datetime] = None

    @validator('title')
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
```

---

## Performance Considerations

### Database Optimization

**Indexes:**
```sql
CREATE INDEX idx_tasks_user_status ON tasks(user_id, status);
CREATE INDEX idx_tasks_due_date ON tasks(due_date) WHERE status != 'completed';
CREATE INDEX idx_users_email ON users(email);
```

**Query Optimization:**
```python
# BAD: N+1 queries
tasks = await db.execute(select(Task).where(Task.user_id == user_id))
for task in tasks:
    user = await db.execute(select(User).where(User.id == task.user_id))

# GOOD: Single query with join
result = await db.execute(
    select(Task)
    .join(User)
    .where(Task.user_id == user_id)
    .options(selectinload(Task.user))
)
```

### Caching Strategy

**Cache expensive computations:**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def calculate_score(task_id: str, user_prefs_hash: str) -> float:
    # Expensive scoring calculation
    # Cached per task + user preference combination
    pass
```

### Async Operations

**Concurrent API calls:**
```python
import asyncio

async def get_dashboard_data(user_id: UUID):
    # Run queries in parallel
    tasks, prefs, stats = await asyncio.gather(
        db.execute(select(Task).where(Task.user_id == user_id)),
        db.execute(select(UserPreferences).where(UserPreferences.user_id == user_id)),
        calculate_user_stats(user_id)
    )
    return {"tasks": tasks, "prefs": prefs, "stats": stats}
```

---

## Next Steps

See companion documents:
- **IMPLEMENTATION.md** - Code examples and setup guide
- **DEPLOYMENT.md** - Docker and Fly.io deployment
- **PRODUCT.md** - Roadmap and business logic

---

**Document Version**: 1.0.0
**Last Updated**: 2025-10-30
**Maintained By**: MindFlow Team
