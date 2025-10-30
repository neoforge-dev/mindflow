# MindFlow: Implementation Guide

**Last Updated**: 2025-10-30
**Stack**: FastAPI + PostgreSQL + LIT + TypeScript
**Goal**: Copy-paste ready code for production deployment

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Backend Setup (FastAPI)](#backend-setup-fastapi)
3. [Database Setup (PostgreSQL)](#database-setup-postgresql)
4. [Frontend Setup (LIT + TypeScript)](#frontend-setup-lit--typescript)
5. [ChatGPT Custom GPT Integration](#chatgpt-custom-gpt-integration)
6. [Testing](#testing)
7. [Common Patterns](#common-patterns)

---

## Quick Start

### Prerequisites

```bash
# System requirements
- Python 3.11+
- Node.js 20+ (or Bun)
- PostgreSQL 15+ (or Supabase account)
- Docker (optional, for local Postgres)
```

### One-Command Bootstrap

```bash
# Clone and setup
git clone https://github.com/yourusername/mindflow.git
cd mindflow

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your database URL, OpenAI key, etc.

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
# API available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs

# Frontend (optional dashboard)
cd ../frontend
npm install  # or: bun install
npm run dev  # or: bun dev
# UI available at http://localhost:5173
```

---

## Backend Setup (FastAPI)

### Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry
│   ├── config.py            # Settings
│   ├── api/
│   │   ├── tasks.py         # Task endpoints
│   │   ├── users.py         # Auth endpoints
│   │   └── health.py        # Health check
│   ├── db/
│   │   ├── database.py      # Async engine
│   │   ├── models.py        # SQLAlchemy models
│   │   └── crud.py          # Database operations
│   ├── schemas/
│   │   ├── task.py          # Pydantic schemas
│   │   └── user.py
│   ├── services/
│   │   ├── scoring.py       # Task scoring
│   │   └── openai.py        # GPT integration (optional)
│   └── middleware/
│       └── auth.py          # JWT validation
├── migrations/              # Alembic migrations
├── requirements.txt
└── .env
```

### 1. Configuration (`app/config.py`)

```python
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://localhost/mindflow"
    )

    # Security
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-change-in-prod")
    jwt_algorithm: str = "HS256"
    access_token_expire_hours: int = 24

    # OpenAI (optional)
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")

    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = environment == "development"

    class Config:
        env_file = ".env"

settings = Settings()
```

### 2. Database Connection (`app/db/database.py`)

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.config import settings

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True  # Verify connections before use
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# Dependency injection for FastAPI
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

### 3. Models (`app/db/models.py`)

```python
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    plan = Column(String(50), default="free")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    title = Column(String(256), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="pending")
    priority = Column(Integer, default=3)  # 1-5

    due_date = Column(DateTime)
    snoozed_until = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    tags = Column(String(500))

    user = relationship("User", back_populates="tasks")

    __table_args__ = (
        Index("ix_tasks_user_status", "user_id", "status"),
        Index("ix_tasks_due_date", "due_date"),
    )

class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True)

    weight_urgency = Column(Integer, default=40)  # Store as 0-100 integers
    weight_priority = Column(Integer, default=35)
    weight_impact = Column(Integer, default=15)
    weight_effort = Column(Integer, default=10)

    timezone = Column(String(50), default="UTC")
```

### 4. Pydantic Schemas (`app/schemas/task.py`)

```python
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
import uuid

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    description: Optional[str] = Field(None, max_length=1000)
    priority: int = Field(default=3, ge=1, le=5)
    due_date: Optional[datetime] = None
    tags: Optional[str] = None

class TaskCreate(TaskBase):
    @validator('title')
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    due_date: Optional[datetime] = None
    snoozed_until: Optional[datetime] = None

class TaskResponse(TaskBase):
    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
```

### 5. API Endpoints (`app/api/tasks.py`)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import uuid

from ..db.database import get_db
from ..db.models import Task, User
from ..schemas.task import TaskCreate, TaskResponse, TaskUpdate
from ..services.scoring import calculate_best_task
from ..middleware.auth import get_current_user

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new task for the authenticated user."""
    db_task = Task(
        user_id=current_user.id,
        **task.dict()
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task

@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's tasks with optional status filter."""
    query = select(Task).where(Task.user_id == current_user.id)

    if status:
        query = query.where(Task.status == status)

    query = query.order_by(Task.created_at.desc())

    result = await db.execute(query)
    return result.scalars().all()

@router.get("/best", response_model=dict)
async def get_best_task(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the highest-priority task to work on now."""
    result = await db.execute(
        select(Task)
        .where(Task.user_id == current_user.id)
        .where(Task.status != "completed")
    )
    tasks = result.scalars().all()

    if not tasks:
        raise HTTPException(status_code=404, detail="No active tasks")

    best_task, score, explanation = await calculate_best_task(
        tasks, current_user, db
    )

    return {
        "task": TaskResponse.from_orm(best_task),
        "score": score,
        "explanation": explanation
    }

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific task."""
    result = await db.execute(
        select(Task)
        .where(Task.id == task_id)
        .where(Task.user_id == current_user.id)
    )
    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: uuid.UUID,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a task."""
    result = await db.execute(
        select(Task)
        .where(Task.id == task_id)
        .where(Task.user_id == current_user.id)
    )
    db_task = result.scalars().first()

    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    for key, value in task_update.dict(exclude_unset=True).items():
        setattr(db_task, key, value)

    db_task.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(db_task)
    return db_task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a task."""
    result = await db.execute(
        select(Task)
        .where(Task.id == task_id)
        .where(Task.user_id == current_user.id)
    )
    db_task = result.scalars().first()

    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    await db.delete(db_task)
    await db.commit()
```

### 6. Task Scoring Service (`app/services/scoring.py`)

```python
from datetime import datetime
from ..db.models import Task, User, UserPreferences
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

async def calculate_best_task(
    tasks: list[Task],
    user: User,
    db: AsyncSession
) -> tuple[Task, float, str]:
    """
    Calculate the best task to work on now.
    Returns: (task, score, explanation)
    """
    # Get user preferences
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == user.id)
    )
    prefs = result.scalars().first()

    # Use defaults if no preferences set
    weights = {
        'urgency': (prefs.weight_urgency if prefs else 40) / 100.0,
        'priority': (prefs.weight_priority if prefs else 35) / 100.0,
        'impact': (prefs.weight_impact if prefs else 15) / 100.0,
        'effort': (prefs.weight_effort if prefs else 10) / 100.0,
    }

    now = datetime.utcnow()
    scored_tasks = []

    for task in tasks:
        components = {
            'urgency': _urgency_score(task, now),
            'priority': _priority_score(task),
            'impact': _impact_score(task),
            'effort': _effort_score(task)
        }

        score = sum(weights[k] * v for k, v in components.items())
        explanation = _explain_score(task, components, now)

        scored_tasks.append((task, score, explanation, components))

    # Return highest scoring task
    best = max(scored_tasks, key=lambda x: x[1])
    return best[0], best[1], best[2]

def _urgency_score(task: Task, now: datetime) -> float:
    """Calculate urgency based on deadline proximity (0-1)."""
    if not task.due_date:
        return 0.3  # No deadline = medium urgency

    hours_until = (task.due_date - now).total_seconds() / 3600

    if hours_until < 0:
        return 1.0  # Overdue
    elif hours_until < 4:
        return 0.9
    elif hours_until < 24:
        return 0.7
    elif hours_until < 168:  # 1 week
        return 0.4
    else:
        return 0.1

def _priority_score(task: Task) -> float:
    """Normalize priority 1-5 to 0-1."""
    return (task.priority or 3) / 5.0

def _impact_score(task: Task) -> float:
    """High priority + short task = high impact per time."""
    priority_norm = (task.priority or 3) / 5.0
    # Assume 30min default if not specified
    effort_factor = 1.0 - min(30 / 480.0, 1.0)  # 480min = 8hrs
    return priority_norm * effort_factor

def _effort_score(task: Task) -> float:
    """Prefer shorter tasks (quick wins)."""
    # Assume 30min default
    return 1.0 - min(30 / 120.0, 1.0)  # 120min = 2hrs

def _explain_score(task: Task, components: dict, now: datetime) -> str:
    """Generate human-readable explanation."""
    reasons = []

    if components['urgency'] > 0.7:
        if task.due_date:
            delta = task.due_date - now
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
        reasons.append("quick task")

    return "Recommended because: " + ", ".join(reasons) if reasons else "Next in queue"
```

### 7. Authentication (`app/middleware/auth.py`)

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..db.database import get_db
from ..db.models import User
from ..config import settings

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(user_id: str) -> str:
    """Generate JWT token."""
    expire = datetime.utcnow() + timedelta(hours=settings.access_token_expire_hours)
    payload = {
        "sub": user_id,
        "exp": expire
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Validate JWT and return current user."""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
```

### 8. Main App (`app/main.py`)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .api import tasks, users, health

app = FastAPI(
    title="MindFlow API",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(tasks.router)
app.include_router(users.router)
app.include_router(health.router)

@app.get("/")
async def root():
    return {"message": "MindFlow API", "version": "1.0.0"}
```

---

## Database Setup (PostgreSQL)

### Using Supabase (Recommended)

1. Sign up at https://supabase.com
2. Create new project (choose region closest to users)
3. Wait ~5 minutes for provisioning
4. Get connection string from Settings → Database
5. Update `.env`:

```bash
DATABASE_URL=postgresql+asyncpg://postgres.xxx:[password]@aws-0-us-west-1.pooler.supabase.com:5432/postgres
```

### Using Local Postgres (Development)

```bash
# Docker
docker run -d \
  --name mindflow-postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=mindflow \
  -p 5432:5432 \
  postgres:15

# Or docker-compose
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: mindflow
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
EOF

docker-compose up -d
```

### Database Migrations (Alembic)

```bash
# Initialize Alembic (first time only)
alembic init migrations

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1
```

**Migration file example** (`migrations/versions/001_initial.py`):

```python
def upgrade():
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('user_id', postgresql.UUID(), nullable=False),
        sa.Column('title', sa.String(256), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('due_date', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_tasks_user_status', 'tasks', ['user_id', 'status'])
```

---

## Frontend Setup (LIT + TypeScript)

### Project Initialization

```bash
# Using Vite
npm create vite@latest frontend -- --template lit-ts
cd frontend
npm install

# Additional dependencies
npm install @lit-labs/router
```

### Basic LIT Component (`src/components/task-list.ts`)

```typescript
import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';

interface Task {
  id: string;
  title: string;
  status: string;
  priority: number;
  due_date?: string;
}

@customElement('task-list')
export class TaskList extends LitElement {
  @state() tasks: Task[] = [];
  @state() loading = false;

  static styles = css`
    :host {
      display: block;
      padding: 1rem;
    }

    .task-item {
      padding: 1rem;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      margin-bottom: 0.75rem;
      background: white;
    }

    .task-item:hover {
      border-color: #2563eb;
    }

    .task-title {
      font-weight: 600;
      margin-bottom: 0.5rem;
    }

    .task-meta {
      font-size: 0.875rem;
      color: #6b7280;
    }
  `;

  async connectedCallback() {
    super.connectedCallback();
    await this.loadTasks();
  }

  async loadTasks() {
    this.loading = true;
    const token = localStorage.getItem('token');

    try {
      const response = await fetch('http://localhost:8000/api/tasks', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      this.tasks = await response.json();
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      this.loading = false;
    }
  }

  render() {
    if (this.loading) {
      return html`<div>Loading...</div>`;
    }

    return html`
      <div>
        <h2>Your Tasks</h2>
        ${this.tasks.map(task => html`
          <div class="task-item">
            <div class="task-title">${task.title}</div>
            <div class="task-meta">
              Priority: ${task.priority}/5 | Status: ${task.status}
            </div>
          </div>
        `)}
      </div>
    `;
  }
}
```

---

## ChatGPT Custom GPT Integration

### OpenAPI Schema for ChatGPT Actions

Create file: `openapi.yaml`

```yaml
openapi: 3.0.0
info:
  title: MindFlow API
  version: 1.0.0
  description: AI-first task manager

servers:
  - url: https://api.mindflow.app

paths:
  /api/tasks:
    post:
      operationId: createTask
      summary: Create a new task
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                title:
                  type: string
                  description: Task title
                description:
                  type: string
                priority:
                  type: integer
                  minimum: 1
                  maximum: 5
                due_date:
                  type: string
                  format: date-time
              required:
                - title
      responses:
        '201':
          description: Task created

  /api/tasks/best:
    get:
      operationId: getBestTask
      summary: Get the most important task to work on now
      responses:
        '200':
          description: Best task with score and explanation
          content:
            application/json:
              schema:
                type: object
                properties:
                  task:
                    type: object
                  score:
                    type: number
                  explanation:
                    type: string
```

### ChatGPT Instructions

```
You are MindFlow, an AI-powered task manager assistant.

Your role:
1. Help users create, manage, and prioritize tasks through natural conversation
2. Suggest the best task to work on when asked "What should I do next?"
3. Explain your recommendations clearly

When users say:
- "Add task X" → Use createTask function
- "What should I do?" → Use getBestTask function
- "Show my tasks" → Use listTasks function

Always:
- Parse dates from natural language (e.g., "Friday" → actual date)
- Map vague priorities ("high") to numbers (1-5)
- Confirm actions before executing
- Be conversational and helpful
```

---

## Testing

### Backend Tests (`backend/tests/test_tasks.py`)

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_task():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/tasks",
            json={
                "title": "Test task",
                "priority": 5
            },
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test task"
```

### Run Tests

```bash
# Backend
cd backend
pytest tests/ -v --cov=app

# Frontend
cd frontend
npm test
```

---

## Common Patterns

### Error Handling

```python
from fastapi import HTTPException

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": str(exc)}
    )
```

### Logging

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Task created", extra={"task_id": str(task.id)})
```

### Environment Variables

```bash
# .env
DATABASE_URL=postgresql+asyncpg://localhost/mindflow
SECRET_KEY=your-secret-key
OPENAI_API_KEY=sk-...
ENVIRONMENT=development
```

---

## Next Steps

- See **DEPLOYMENT.md** for production deployment guide
- See **ARCHITECTURE.md** for system design details
- See **PRODUCT.md** for roadmap and business logic

---

**Version**: 1.0.0
**Last Updated**: 2025-10-30
