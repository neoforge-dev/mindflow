# MindFlow Production: FastAPI + LIT + TypeScript Full-Stack SaaS

**Project:** MindFlow — AI-First Task Manager (Phase 2: Production MVP)  
**Stack:** FastAPI (Python) + LIT/Web Components (TypeScript) + Supabase (Postgres) + OpenAI GPT-4 Sonnet  
**Deployment:** Docker + Fly.io  
**Status:** Implementation Ready  
**Date:** October 30, 2025

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Tech Stack & Architecture](#tech-stack--architecture)
3. [Project Structure](#project-structure)
4. [Backend: FastAPI Setup](#backend-fastapi-setup)
5. [Database: Supabase + Postgres](#database-supabase--postgres)
6. [Frontend: LIT + TypeScript](#frontend-lit--typescript)
7. [OpenAI Integration (GPT-4 Sonnet)](#openai-integration-gpt-4-sonnet)
8. [Authentication & Multi-User](#authentication--multi-user)
9. [Real-Time Features (WebSockets)](#real-time-features-websockets)
10. [Deployment (Docker + Fly.io)](#deployment-docker--flyio)
11. [MVP Launch Checklist](#mvp-launch-checklist)
12. [Monitoring & Observability](#monitoring--observability)
13. [Scaling Path (Post-MVP)](#scaling-path-post-mvp)

---

## Executive Summary

This is the **Phase 2 production implementation** of MindFlow, evolving from the GAS MVP to a scalable, multi-user SaaS product. The stack prioritizes:

- **Developer velocity**: FastAPI's async Python + TypeScript for type safety
- **Cost efficiency**: Supabase (Postgres) on shared tier (~$25/mo), Fly.io standard tier (~$10-50/mo)
- **User experience**: LIT web components for lightweight, framework-agnostic UI
- **AI intelligence**: Native GPT-4 Sonnet function calling for task scoring
- **Production readiness**: Auth, monitoring, error handling from day one

### Why This Stack?

| Layer | Choice | Why |
|-------|--------|-----|
| **Backend** | FastAPI | Your Python expertise, async native, auto-docs (OpenAPI) |
| **Frontend** | LIT + TypeScript | Web components (framework-agnostic), tiny bundle (~50KB gzipped) |
| **Database** | Supabase/Postgres | Real-time subscriptions, Row-Level Security, JSON support |
| **Deployment** | Fly.io + Docker | Global deployment, managed Postgres, pay-as-you-go |
| **AI** | OpenAI GPT-4 Sonnet | Function calling, cost-effective, strong reasoning |

---

## Tech Stack & Architecture

### Layer Breakdown

```
┌─────────────────────────────────────────────────────────────┐
│                   USER (Browser/Desktop)                    │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│            FRONTEND (LIT + TypeScript + Vite)               │
│  • Chat interface (custom web components)                   │
│  • Task board (real-time updates via WebSocket)             │
│  • Auth flows (login, signup, password reset)               │
│  • Settings & preferences                                    │
│  • Offline persistence (IndexedDB fallback)                 │
└────────────────────┬────────────────────────────────────────┘
                     │ JSON/WebSocket
┌─────────────────────────────────────────────────────────────┐
│        FASTAPI BACKEND (Async Python + SQLAlchemy)          │
│  • REST endpoints (/api/tasks, /api/users, etc.)            │
│  • WebSocket handler (/ws/tasks)                            │
│  • Auth (JWT + refresh tokens)                              │
│  • GPT-4 Sonnet integration                                 │
│  • Request validation (Pydantic)                            │
│  • Error handling & observability                           │
└────────────────────┬────────────────────────────────────────┘
                     │ SQL (asyncpg)
┌─────────────────────────────────────────────────────────────┐
│      DATABASE (Supabase / PostgreSQL + Real-time)           │
│  • tasks table (id, user_id, title, status, priority, due)  │
│  • users table (id, email, password_hash, plan)             │
│  • subscriptions (Postgres native for Realtime)             │
│  • logs & observability                                     │
└─────────────────────────────────────────────────────────────┘
        │                              │
        │ Read/Write                   ▼ Logical Replication
        │                   ┌─────────────────────────┐
        │                   │ Supabase Realtime Relay │
        │                   │ (Elixir/Phoenix WebSocket)
        │                   └────────┬────────────────┘
        │                            │
        └──────────────────────────┬─┘
                     ▲              │
                     │ WebSocket    │
                 FRONTEND ◄─────────┘
```

### Why This Architecture?

1. **Async-first**: FastAPI's async native + asyncpg prevents database connection blocking
2. **Real-time**: Supabase Realtime pushes live task updates without polling
3. **Web components**: LIT avoids framework overhead; components work in any DOM
4. **Type safety**: TypeScript + Pydantic = compile-time + runtime validation
5. **Scalable**: Stateless FastAPI instances + managed Postgres = easy horizontal scaling

---

## Project Structure

```
mindflow/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app entry
│   │   ├── config.py                  # Environment vars
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── tasks.py              # POST /api/tasks, GET /api/tasks/{id}
│   │   │   ├── users.py              # POST /api/auth/register, /login
│   │   │   ├── ai.py                 # POST /api/ai/complete (GPT-4)
│   │   │   └── health.py             # GET /health (liveness check)
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── database.py           # SQLAlchemy async engine + session
│   │   │   ├── models.py             # Task, User, Subscription ORM models
│   │   │   └── crud.py               # CRUD operations (queries)
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── task.py               # Pydantic models (TaskCreate, TaskResponse)
│   │   │   ├── user.py               # UserCreate, UserResponse
│   │   │   └── ai.py                 # AIRequest, AIResponse
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # JWT validation
│   │   │   └── error_handler.py      # Global error handling
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── task_scorer.py        # Relevance scoring algorithm
│   │   │   ├── ai_service.py         # OpenAI GPT-4 wrapper
│   │   │   └── email_service.py      # SendGrid integration (future)
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── security.py           # JWT, password hashing
│   │       └── logger.py             # Structured logging
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_api.py
│   │   ├── test_db.py
│   │   └── test_ai.py
│   │
│   ├── migrations/
│   │   └── versions/                 # Alembic migrations
│   │
│   ├── requirements.txt              # Python dependencies
│   ├── pyproject.toml               # Modern Python package config
│   ├── Dockerfile                   # Production image
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── index.html               # Entry point
│   │   ├── index.ts                 # App bootstrap
│   │   ├── components/
│   │   │   ├── app-shell.ts         # Root web component
│   │   │   ├── chat-interface.ts    # Chat bubble UI
│   │   │   ├── task-board.ts        # Tasks list/cards
│   │   │   ├── task-card.ts         # Individual task component
│   │   │   ├── login-form.ts        # Auth UI
│   │   │   ├── settings-panel.ts    # User preferences
│   │   │   └── toast.ts             # Notifications
│   │   │
│   │   ├── services/
│   │   │   ├── api.ts               # Fetch wrapper (with retry logic)
│   │   │   ├── websocket.ts         # WebSocket client for real-time
│   │   │   ├── auth.ts              # JWT management
│   │   │   └── storage.ts           # LocalStorage + IndexedDB
│   │   │
│   │   ├── styles/
│   │   │   ├── theme.css            # CSS custom properties (dark/light)
│   │   │   ├── reset.css            # Normalize CSS
│   │   │   └── components.css       # Shared component styles
│   │   │
│   │   └── types/
│   │       ├── index.ts             # Global types
│   │       └── api.ts               # API request/response types
│   │
│   ├── tests/
│   │   ├── components/
│   │   │   └── task-card.test.ts
│   │   └── services/
│   │       └── api.test.ts
│   │
│   ├── package.json                 # NPM scripts, dependencies
│   ├── tsconfig.json               # TypeScript config
│   ├── vite.config.ts              # Vite + build config
│   ├── vitest.config.ts            # Testing framework
│   └── README.md
│
├── docker-compose.yml              # Local dev: FastAPI + Postgres
├── fly.toml                         # Fly.io app config
├── .github/
│   └── workflows/
│       ├── test.yml                # Run tests on PR
│       └── deploy.yml              # Auto-deploy on main branch
└── README.md                        # Root docs
```

---

## Backend: FastAPI Setup

### 1. Environment & Dependencies

**requirements.txt:**
```
# FastAPI & Web
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy[asyncio]==2.0.23
asyncpg==0.29.0
alembic==1.12.1

# Auth & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# AI & External APIs
openai==1.3.9
supabase==2.3.5

# Monitoring & Logging
python-json-logger==2.0.7
sentry-sdk==1.38.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.1

# Development
black==23.12.0
ruff==0.1.8
```

### 2. Database Configuration

**app/db/database.py:**
```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
import os

DATABASE_URL = os.getenv("DATABASE_URL")  # postgresql+asyncpg://...

# For production, use NullPool to prevent connection leaks
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=0,
    poolclass=NullPool if os.getenv("ENV") == "production" else None,
    pool_pre_ping=True  # Verify connections before using
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False  # Keep objects accessible after commit
)

Base = declarative_base()

async def get_db() -> AsyncSession:
    """Dependency for FastAPI to inject async DB session."""
    async with AsyncSessionLocal() as session:
        yield session
```

### 3. ORM Models

**app/db/models.py:**
```python
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum

from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    plan = Column(String(50), default="free")  # free, pro, enterprise
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SNOOZED = "snoozed"

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    description = Column(String(1000), nullable=True)
    status = Column(String(50), default=TaskStatus.PENDING)
    priority = Column(Integer, default=3)  # 1-5
    due_date = Column(DateTime, nullable=True)
    snoozed_until = Column(DateTime, nullable=True)
    tags = Column(String(500), nullable=True)  # Comma-separated
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    
    __table_args__ = (
        # Composite index for common queries
        Index("ix_user_status", "user_id", "status"),
    )
```

### 4. Pydantic Schemas

**app/schemas/task.py:**
```python
from pydantic import BaseModel, Field
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
    pass

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[int] = None
    due_date: Optional[datetime] = None
    snoozed_until: Optional[datetime] = None

class TaskResponse(TaskBase):
    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # SQLAlchemy model → Pydantic
```

### 5. API Endpoints

**app/api/tasks.py:**
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import uuid

from ..db.database import get_db
from ..db.models import Task, User
from ..schemas.task import TaskCreate, TaskResponse, TaskUpdate
from ..services.task_scorer import score_task
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

@router.get("/best", response_model=TaskResponse)
async def get_best_task(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the highest-scored task for the user."""
    result = await db.execute(
        select(Task)
        .where(Task.user_id == current_user.id)
        .where(Task.status != "completed")
    )
    tasks = result.scalars().all()
    
    if not tasks:
        raise HTTPException(status_code=404, detail="No active tasks")
    
    # Score each task
    scored = [(t, score_task(t)) for t in tasks]
    best_task = max(scored, key=lambda x: x[1])[0]
    
    return best_task

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

@router.post("/{task_id}", response_model=TaskResponse)
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

### 6. Authentication

**app/middleware/auth.py:**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os

from ..db.database import get_db
from ..db.models import User
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Validate JWT and return current user."""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

---

## Database: Supabase + Postgres

### 1. Supabase Setup

1. Sign up: https://supabase.com
2. Create new project (choose shared tier for MVP: ~$25/mo after $100 free credits)
3. Wait for deployment (~5 minutes)
4. Note the connection string: `postgresql+asyncpg://[user]:[password]@[host]:5432/postgres`

### 2. Row-Level Security (RLS)

Automatically filter tasks by `user_id`:

```sql
-- Enable RLS on tasks table
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own tasks
CREATE POLICY "Users see only their tasks"
  ON tasks FOR SELECT
  USING (auth.uid() = user_id);

-- Policy: Users can only insert tasks for themselves
CREATE POLICY "Users insert only their tasks"
  ON tasks FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Similar for UPDATE, DELETE...
```

### 3. Real-Time Subscriptions

Supabase auto-broadcasts changes via PostgreSQL logical replication:

```sql
-- Enable Realtime for tasks
ALTER PUBLICATION supabase_realtime ADD TABLE tasks;
```

Frontend subscribes:
```typescript
supabase
  .channel('user-tasks')
  .on(
    'postgres_changes',
    {
      event: '*',
      schema: 'public',
      table: 'tasks',
      filter: `user_id=eq.${userId}`
    },
    (payload) => {
      // Update UI when task changes
      updateTaskInUI(payload.new);
    }
  )
  .subscribe();
```

---

## Frontend: LIT + TypeScript

### 1. Project Setup

```bash
# Initialize with Vite + LIT template
npm create vite@latest mindflow-frontend -- --template lit-ts

cd mindflow-frontend

# Install dependencies
npm install

# Run dev server
npm run dev  # http://localhost:5173
```

### 2. Core Web Component

**src/components/app-shell.ts:**
```typescript
import { LitElement, html, css } from 'lit';
import { customElement, state, property } from 'lit/decorators.js';
import { Router } from '@lit-labs/router';

@customElement('app-shell')
export class AppShell extends LitElement {
  @state() isLoggedIn = false;
  @state() user: any = null;

  static styles = css`
    :host {
      display: block;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      --primary-color: #2563eb;
      --danger-color: #dc2626;
      --text-primary: #1f2937;
      --text-secondary: #6b7280;
      --bg-light: #f9fafb;
    }

    .app-container {
      display: grid;
      grid-template-columns: 250px 1fr;
      min-height: 100vh;
    }

    .sidebar {
      background: var(--bg-light);
      border-right: 1px solid #e5e7eb;
      padding: 1rem;
    }

    .main-content {
      display: flex;
      flex-direction: column;
    }

    header {
      background: white;
      border-bottom: 1px solid #e5e7eb;
      padding: 1rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    main {
      flex: 1;
      padding: 2rem;
      overflow-y: auto;
    }
  `;

  async connectedCallback() {
    super.connectedCallback();
    await this.checkAuth();
  }

  async checkAuth() {
    const token = localStorage.getItem('token');
    if (token) {
      // Verify token with backend
      try {
        const response = await fetch('/api/auth/me', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
          this.user = await response.json();
          this.isLoggedIn = true;
        }
      } catch (e) {
        console.error('Auth check failed:', e);
      }
    }
  }

  render() {
    if (!this.isLoggedIn) {
      return html`<login-form @login=${this.handleLogin}></login-form>`;
    }

    return html`
      <div class="app-container">
        <aside class="sidebar">
          <h1>MindFlow</h1>
          <nav>
            <a href="/tasks">Tasks</a>
            <a href="/chat">Chat</a>
            <a href="/settings">Settings</a>
            <button @click=${this.handleLogout}>Logout</button>
          </nav>
        </aside>
        
        <div class="main-content">
          <header>
            <h2>Welcome, ${this.user?.full_name || this.user?.email}</h2>
            <span>Plan: ${this.user?.plan}</span>
          </header>
          
          <main>
            <router-outlet></router-outlet>
          </main>
        </div>
      </div>
    `;
  }

  private handleLogin(e: CustomEvent) {
    const { token, user } = e.detail;
    localStorage.setItem('token', token);
    this.user = user;
    this.isLoggedIn = true;
  }

  private handleLogout() {
    localStorage.removeItem('token');
    this.isLoggedIn = false;
  }
}
```

### 3. Chat Interface Component

**src/components/chat-interface.ts:**
```typescript
import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { chatAPI } from '../services/api';

@customElement('chat-interface')
export class ChatInterface extends LitElement {
  @state() messages: any[] = [];
  @state() inputValue = '';
  @state() isLoading = false;

  static styles = css`
    :host {
      display: flex;
      flex-direction: column;
      height: 100%;
      gap: 1rem;
    }

    .chat-box {
      flex: 1;
      overflow-y: auto;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      padding: 1rem;
      background: white;
    }

    .message {
      margin-bottom: 1rem;
      display: flex;
      gap: 0.5rem;
    }

    .message.user {
      justify-content: flex-end;
    }

    .message.ai {
      justify-content: flex-start;
    }

    .message-content {
      max-width: 70%;
      padding: 0.75rem 1rem;
      border-radius: 8px;
    }

    .message.user .message-content {
      background: #2563eb;
      color: white;
    }

    .message.ai .message-content {
      background: #f3f4f6;
      color: #1f2937;
    }

    .input-area {
      display: flex;
      gap: 0.5rem;
    }

    input {
      flex: 1;
      padding: 0.75rem;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      font-size: 1rem;
    }

    button {
      padding: 0.75rem 1.5rem;
      background: #2563eb;
      color: white;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 500;
    }

    button:hover:not(:disabled) {
      background: #1d4ed8;
    }

    button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  `;

  async connectedCallback() {
    super.connectedCallback();
    this.loadMessages();
  }

  async loadMessages() {
    const token = localStorage.getItem('token');
    const response = await fetch('/api/chat/history', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    this.messages = await response.json();
  }

  async sendMessage() {
    if (!this.inputValue.trim()) return;

    const userMessage = this.inputValue;
    this.inputValue = '';
    this.isLoading = true;

    this.messages.push({
      id: Date.now(),
      role: 'user',
      content: userMessage,
      timestamp: new Date()
    });

    try {
      const response = await fetch('/api/chat/message', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: userMessage })
      });

      const aiResponse = await response.json();
      this.messages.push({
        id: Date.now() + 1,
        role: 'assistant',
        content: aiResponse.content,
        timestamp: new Date(),
        taskId: aiResponse.task_id // If action created/modified a task
      });
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      this.isLoading = false;
    }

    this.requestUpdate();
  }

  render() {
    return html`
      <div class="chat-box">
        ${this.messages.map(msg => html`
          <div class="message ${msg.role}">
            <div class="message-content">${msg.content}</div>
          </div>
        `)}
      </div>

      <div class="input-area">
        <input
          type="text"
          placeholder="Ask me anything... 'What should I do next?'"
          .value=${this.inputValue}
          @input=${(e: Event) => this.inputValue = (e.target as HTMLInputElement).value}
          @keydown=${(e: KeyboardEvent) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              this.sendMessage();
            }
          }}
          ?disabled=${this.isLoading}
        />
        <button @click=${() => this.sendMessage()} ?disabled=${this.isLoading}>
          ${this.isLoading ? 'Sending...' : 'Send'}
        </button>
      </div>
    `;
  }
}
```

---

## OpenAI Integration (GPT-4 Sonnet)

### Backend Handler

**app/api/ai.py:**
```python
from fastapi import APIRouter, Depends
from openai import OpenAI, APIError
import json
import os

from ..db.database import get_db
from ..db.models import User
from ..middleware.auth import get_current_user
from ..services.task_scorer import score_task
from ..schemas.ai import ChatMessage, ChatResponse

router = APIRouter(prefix="/api/ai", tags=["ai"])
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Function definitions for GPT function calling
TASK_FUNCTIONS = [
    {
        "name": "create_task",
        "description": "Create a new task with title, priority, and due date",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Task title"
                },
                "priority": {
                    "type": "integer",
                    "description": "Priority level 1-5",
                    "minimum": 1,
                    "maximum": 5
                },
                "due_date": {
                    "type": "string",
                    "description": "Due date in ISO8601 format"
                }
            },
            "required": ["title"]
        }
    },
    {
        "name": "get_best_task",
        "description": "Get the most important/urgent task to work on",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "complete_task",
        "description": "Mark a task as completed",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "UUID of task to complete"
                }
            },
            "required": ["task_id"]
        }
    }
]

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Send a message to GPT-4 Sonnet with task management capabilities.
    Handles function calling for task operations.
    """
    
    system_prompt = """You are MindFlow, an AI task manager assistant. Your role is to help users manage tasks through natural conversation.

You have access to task management functions. When a user asks you to:
- "What should I do next?" → Use get_best_task()
- "Create a task..." → Use create_task()
- "Mark as done" → Use complete_task()

Always be conversational and helpful. Explain your actions clearly."""

    # Build messages array for OpenAI
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message.content}
    ]

    try:
        # Initial call to GPT-4 Sonnet with function calling
        response = client.chat.completions.create(
            model="gpt-4-turbo",  # or gpt-4 if using function calling
            messages=messages,
            functions=TASK_FUNCTIONS,
            function_call="auto"
        )

        # Handle function calls
        if response.choices[0].message.function_call:
            func_call = response.choices[0].message.function_call
            func_args = json.loads(func_call.arguments)

            # Execute the function
            if func_call.name == "create_task":
                # Create task in database
                from ..db.models import Task
                task = Task(
                    user_id=current_user.id,
                    title=func_args["title"],
                    priority=func_args.get("priority", 3),
                    due_date=func_args.get("due_date")
                )
                db.add(task)
                await db.commit()
                
                ai_response = f"Created task: '{func_args['title']}' with priority {func_args.get('priority', 3)}"

            elif func_call.name == "get_best_task":
                from ..db.models import Task
                from sqlalchemy.future import select
                
                result = await db.execute(
                    select(Task)
                    .where(Task.user_id == current_user.id)
                    .where(Task.status != "completed")
                )
                tasks = result.scalars().all()
                
                if tasks:
                    scored = [(t, score_task(t)) for t in tasks]
                    best = max(scored, key=lambda x: x[1])[0]
                    ai_response = f"Your best task right now is: **{best.title}** (Priority: {best.priority}/5)"
                else:
                    ai_response = "You have no active tasks. Great job!"

            else:
                ai_response = "Function call not implemented"

            return ChatResponse(
                content=ai_response,
                function_call=func_call.name
            )

        # If no function call, return text response
        else:
            ai_response = response.choices[0].message.content
            return ChatResponse(content=ai_response)

    except APIError as e:
        return ChatResponse(
            content="Sorry, I encountered an error. Please try again.",
            error=str(e)
        )
```

---

## Authentication & Multi-User

### 1. User Registration

**app/api/users.py:**
```python
from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from sqlalchemy.future import select

from ..db.database import get_db
from ..db.models import User
from ..schemas.user import UserCreate, UserResponse
from ..middleware.auth import create_access_token
from ..utils.security import hash_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db = Depends(get_db)
):
    """Register a new user."""
    # Check if user exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    db_user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    # Generate token
    access_token = create_access_token(data={"sub": str(db_user.id)})
    
    return {
        "id": db_user.id,
        "email": db_user.email,
        "full_name": db_user.full_name,
        "access_token": access_token
    }

@router.post("/login")
async def login(credentials: UserLogin, db = Depends(get_db)):
    """Authenticate user and return JWT."""
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalars().first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "user": UserResponse.from_orm(user)
    }
```

---

## Real-Time Features (WebSockets)

### Backend WebSocket Handler

**app/api/ws.py:**
```python
from fastapi import APIRouter, WebSocket, Depends, status
from typing import Set
import json
import logging

from ..middleware.auth import get_current_user

router = APIRouter(prefix="/ws", tags=["websocket"])
logger = logging.getLogger(__name__)

# Store active connections per user
user_connections: dict[str, Set[WebSocket]] = {}

@router.websocket("/tasks")
async def websocket_tasks(websocket: WebSocket):
    """WebSocket for real-time task updates."""
    await websocket.accept()
    
    user_id = None
    try:
        # Receive auth token
        auth_msg = await websocket.receive_text()
        token = json.loads(auth_msg).get("token")
        
        # Verify token (simplified)
        from ..middleware.auth import decode_token
        payload = decode_token(token)
        user_id = payload["sub"]
        
        # Register connection
        if user_id not in user_connections:
            user_connections[user_id] = set()
        user_connections[user_id].add(websocket)
        
        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle incoming messages (e.g., task updates)
            if message["type"] == "task_update":
                # Broadcast to all connections for this user
                for conn in user_connections[user_id]:
                    await conn.send_json({
                        "type": "task_updated",
                        "task": message["task"]
                    })
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    
    finally:
        if user_id and user_id in user_connections:
            user_connections[user_id].discard(websocket)
            await websocket.close()
```

### Frontend WebSocket Client

**src/services/websocket.ts:**
```typescript
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private token: string;
  private listeners: Map<string, Function[]> = new Map();

  constructor(url: string = 'ws://localhost:8000') {
    this.url = url;
    this.token = localStorage.getItem('token') || '';
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(`${this.url}/ws/tasks`);

        this.ws.onopen = () => {
          // Send authentication
          this.ws!.send(JSON.stringify({ token: this.token }));
          resolve();
        };

        this.ws.onmessage = (event) => {
          const message = JSON.parse(event.data);
          this.emit(message.type, message);
        };

        this.ws.onerror = reject;
      } catch (error) {
        reject(error);
      }
    });
  }

  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(callback);
  }

  private emit(event: string, data: any) {
    const callbacks = this.listeners.get(event) || [];
    callbacks.forEach(cb => cb(data));
  }

  disconnect() {
    this.ws?.close();
  }
}
```

---

## Deployment (Docker + Fly.io)

### 1. Dockerfile

```dockerfile
# Multi-stage build
FROM python:3.11-slim as builder

WORKDIR /app

# Install UV for fast dependency installation
RUN pip install uv

COPY requirements.txt .
RUN uv pip compile requirements.txt -o requirements-compiled.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

RUN pip install uv
COPY --from=builder /app/requirements-compiled.txt .
RUN uv pip install -r requirements-compiled.txt --system

COPY ./app /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Fly.toml Configuration

```toml
app = "mindflow-api"
primary_region = "ams"  # Amsterdam

[build]
  image = "mindflow:latest"
  dockerfile = "Dockerfile"

[env]
  ENVIRONMENT = "production"
  LOG_LEVEL = "info"

[deploy]
  release_command = "alembic upgrade head"

[[services]]
  internal_port = 8000
  processes = ["app"]

  [[services.ports]]
    port = 80
    handlers = ["http"]
  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

[[statics]]
  guest_path = "/static"
  url_prefix = "/static"

# Postgres attachment
[[services]]
  protocol = "postgresql"
  internal_port = 5432
```

### 3. Deployment Steps

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login to Fly
flyctl auth login

# Create app
flyctl launch --name mindflow-api --region ams

# Set secrets
flyctl secrets set SECRET_KEY="$(openssl rand -hex 32)"
flyctl secrets set OPENAI_API_KEY="sk-..."
flyctl secrets set DATABASE_URL="postgresql+asyncpg://..."

# Deploy
flyctl deploy

# Check logs
flyctl logs

# Monitor
flyctl status
```

---

## MVP Launch Checklist

### Core Features
- [ ] User authentication (register, login, password reset)
- [ ] Create/read/update/delete tasks
- [ ] Task scoring algorithm (best task logic)
- [ ] Chat interface with GPT-4 Sonnet
- [ ] Function calling (create task via chat, etc.)
- [ ] Real-time task updates (WebSocket)
- [ ] Mobile-responsive UI (LIT + CSS Grid)

### Production Readiness
- [ ] Error handling & validation (Pydantic + custom middleware)
- [ ] Structured logging (JSON format for monitoring)
- [ ] Database migrations (Alembic)
- [ ] JWT auth with refresh tokens
- [ ] CORS + CSRF protection
- [ ] Rate limiting (FastAPI + middleware)
- [ ] Health checks (`/health` endpoint)

### Testing
- [ ] Unit tests for API endpoints (pytest + httpx)
- [ ] Database tests (test fixtures with transactions)
- [ ] Chat/AI function tests
- [ ] Frontend component tests (Web Test Runner or Vitest)

### Monitoring
- [ ] Error tracking (Sentry)
- [ ] Performance monitoring (New Relic or DataDog free tier)
- [ ] Database query monitoring
- [ ] API uptime monitoring (UptimeRobot)

### Security
- [ ] SSL/TLS (auto-configured by Fly.io)
- [ ] SQL injection protection (SQLAlchemy ORM)
- [ ] XSS prevention (Content-Security-Policy header)
- [ ] HTTPS redirect
- [ ] Rate limiting on auth endpoints
- [ ] Password hashing (bcrypt)

### Payment (Optional for MVP)
- [ ] [ ] Stripe integration (future: gated features)
- [ ] Pricing page
- [ ] Subscription webhooks

### Content & Marketing
- [ ] Landing page (simple HTML)
- [ ] Privacy policy
- [ ] Terms of service
- [ ] README + basic docs

---

## Monitoring & Observability

### Structured Logging

**app/utils/logger.py:**
```python
import json
import logging
from pythonjsonlogger import jsonlogger

# Configure JSON logging
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Usage in code
logger.info("Task created", extra={
    "task_id": str(task.id),
    "user_id": str(current_user.id),
    "priority": task.priority
})
```

### Error Tracking with Sentry

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
    ],
    traces_sample_rate=1.0,
    environment=os.getenv("ENV", "development")
)
```

---

## Scaling Path (Post-MVP)

### Phase 2 Improvements (Month 2–3)

1. **Analytics**: Track user behavior (which tasks completed, time-to-completion)
2. **Integrations**: Slack, Gmail, Google Calendar sync
3. **AI Enhancements**: Task suggestions based on history, habit detection
4. **Payments**: Stripe for premium features (team collaboration, advanced analytics)
5. **Mobile App**: React Native using same FastAPI backend

### Phase 3 Enterprise (Month 4+)

1. **Team Collaboration**: Shared tasks, permissions, audit logs
2. **Advanced Scoring**: ML model for personalized recommendations
3. **API**: Third-party integrations via webhooks
4. **SSO**: SAML/OIDC for enterprise customers
5. **White-label**: Custom branding for resellers

---

## Quick Start Script

```bash
#!/bin/bash

# Clone and setup
git clone https://github.com/yourusername/mindflow.git
cd mindflow

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev

# Tests
pytest backend/tests -v
npm run test

# Deploy
flyctl deploy
```

---

## Summary

This **production-ready SaaS stack** enables you to:

✅ **Build fast**: FastAPI's async native + type hints + auto-docs  
✅ **Deploy cheap**: Supabase shared tier ($25) + Fly.io ($10–50), total ~$50/mo  
✅ **Scale smart**: Stateless FastAPI + managed Postgres + global Fly.io regions  
✅ **Iterate quickly**: LIT's minimal overhead + TypeScript for frontend safety  
✅ **Go AI-first**: GPT-4 Sonnet function calling built into core UX  
✅ **Real-time**: Supabase WebSockets for instant task updates  

**Next week**: Deploy Phase 1 (GAS MVP) and gather 10–20 user interviews to validate scoring logic. Use feedback to calibrate Phase 2 FastAPI deployment. Ship Phase 2 (this stack) in 4 weeks.

**Timeline**: MVP → Users → Feedback → FastAPI → Premium → Revenue

---

**Project:** MindFlow v2.0 (Production)  
**Status:** Ready to Build  
**Effort:** 4–6 weeks solo for experienced backend engineer  
**Cost to Launch:** $50–100/month infrastructure + $300 NLP API costs first month

Let's build! 🚀
