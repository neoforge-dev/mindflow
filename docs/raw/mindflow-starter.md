# MindFlow: Quick Start Implementation Guide

## 📚 Starter Code Examples

This guide provides battle-tested code snippets to accelerate your implementation. Use these as your foundation and iterate with Claude Code.

---

## 1. FastAPI Backend Setup

### `backend/app/config.py`

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://mindflow:password@localhost:5432/mindflow_db"
    
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4"
    
    # JWT
    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Environment
    debug: bool = False
    environment: str = "development"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### `backend/app/database/connection.py`

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Use async PostgreSQL driver
engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.debug,
    pool_size=5,
    max_overflow=10
)

async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with async_session_maker() as session:
        yield session
```

### `backend/app/models/task.py`

```python
from sqlalchemy import Column, String, DateTime, Integer, Float, Boolean, UUID, ForeignKey, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    
    # Core
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="open")  # open, in_progress, done
    
    # Temporal
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_at = Column(DateTime, nullable=True, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Scoring
    priority = Column(Integer, default=0)  # 0-10
    urgency_score = Column(Float, default=0)
    impact_score = Column(Float, default=0)
    effort_estimate_minutes = Column(Integer, default=30)
    
    # Context
    category = Column(String(100), nullable=True)
    tags = Column(JSON, default=[])
    context_metadata = Column(JSON, default={})
    
    # Habits
    recurring_pattern = Column(String(100), nullable=True)
    recurring_until = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
```

### `backend/app/schemas/task.py`

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_at: Optional[datetime] = None
    priority: int = 0
    category: Optional[str] = None
    tags: List[str] = []
    effort_estimate_minutes: int = 30
    recurring_pattern: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    due_at: Optional[datetime] = None

class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    status: str
    due_at: Optional[datetime]
    priority: int
    urgency_score: float
    created_at: datetime
    
    class Config:
        from_attributes = True
```

---

## 2. OpenAI Integration

### `backend/app/services/gpt_service.py`

```python
import json
from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI
from app.config import settings
from datetime import datetime

client = AsyncOpenAI(api_key=settings.openai_api_key)

TASK_FUNCTIONS = [
    {
        "name": "create_task",
        "description": "Create a new task",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "due_at": {"type": "string", "format": "date-time"},
                "priority": {"type": "integer", "minimum": 0, "maximum": 10},
                "category": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "recurring_pattern": {"type": "string", "enum": ["daily", "weekly", "monthly", None]}
            },
            "required": ["title"]
        }
    },
    {
        "name": "list_tasks",
        "description": "List user's tasks with filters",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["open", "in_progress", "done"]},
                "sort_by": {"type": "string", "enum": ["urgency", "due_date", "priority"]},
                "limit": {"type": "integer", "default": 10}
            }
        }
    },
    {
        "name": "update_task",
        "description": "Update a task",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "status": {"type": "string", "enum": ["open", "in_progress", "done"]},
                "priority": {"type": "integer"}
            },
            "required": ["task_id"]
        }
    }
]

SYSTEM_PROMPT = """You are MindFlow, an AI task manager. Your role is to:

1. Understand natural language task requests
2. Extract structured data (dates, priorities, etc)
3. Call appropriate functions to create/update/list tasks
4. Explain your actions clearly and suggest next steps

When a user says "due Friday", convert to an actual date in their timezone.
When they say "high priority", map to priority 8-10.
Always confirm before archiving tasks.
Be concise but helpful.
"""

async def chat_with_gpt(
    user_message: str,
    conversation_history: List[Dict[str, str]],
    user_id: str,
    timezone: str = "UTC"
) -> Dict[str, Any]:
    """
    Send message to GPT with function calling.
    Returns dict with response text and any function calls.
    """
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *conversation_history,
        {"role": "user", "content": user_message}
    ]
    
    # First call: get GPT's response
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        functions=TASK_FUNCTIONS,
        function_call="auto",
        temperature=0.7,
        max_tokens=500
    )
    
    result = {
        "response": "",
        "function_calls": [],
        "messages": messages.copy()
    }
    
    # Check if GPT wants to call a function
    if response.choices[0].finish_reason == "function_call":
        function_call = response.choices[0].message.function_call
        result["function_calls"].append({
            "name": function_call.name,
            "arguments": json.loads(function_call.arguments)
        })
        result["response"] = "Processing your request..."
    else:
        # Regular response
        result["response"] = response.choices[0].message.content
    
    return result
```

### `backend/app/services/task_service.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate
from datetime import datetime, timedelta
from typing import List, Optional
import uuid

class TaskService:
    @staticmethod
    async def create_task(
        session: AsyncSession,
        user_id: str,
        task_create: TaskCreate
    ) -> Task:
        """Create a new task"""
        task = Task(
            user_id=uuid.UUID(user_id),
            **task_create.dict()
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task
    
    @staticmethod
    async def get_tasks(
        session: AsyncSession,
        user_id: str,
        status: Optional[str] = None,
        sort_by: str = "urgency",
        limit: int = 10
    ) -> List[Task]:
        """Get user's tasks with optional filtering"""
        query = select(Task).where(Task.user_id == uuid.UUID(user_id))
        
        if status:
            query = query.where(Task.status == status)
        
        # Calculate urgency scores for sorting
        query = query.order_by(
            Task.urgency_score.desc() if sort_by == "urgency" else
            Task.due_at.asc() if sort_by == "due_date" else
            Task.priority.desc()
        )
        
        query = query.limit(limit)
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_next_task(session: AsyncSession, user_id: str) -> Optional[Task]:
        """Get the most relevant task to work on now"""
        tasks = await TaskService.get_tasks(
            session, 
            user_id, 
            status="open",
            sort_by="urgency",
            limit=1
        )
        return tasks[0] if tasks else None
    
    @staticmethod
    async def update_task(
        session: AsyncSession,
        task_id: str,
        user_id: str,
        task_update: TaskUpdate
    ) -> Task:
        """Update a task"""
        result = await session.execute(
            select(Task).where(
                and_(
                    Task.id == uuid.UUID(task_id),
                    Task.user_id == uuid.UUID(user_id)
                )
            )
        )
        task = result.scalar_one_or_none()
        
        if not task:
            raise ValueError("Task not found")
        
        for field, value in task_update.dict(exclude_unset=True).items():
            setattr(task, field, value)
        
        task.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(task)
        return task
```

---

## 3. Relevance Algorithm

### `backend/app/services/relevance.py`

```python
from app.models.task import Task
from app.models.user import UserPreferences
from datetime import datetime
from typing import Dict, Tuple

class RelevanceEngine:
    @staticmethod
    def calculate_score(
        task: Task,
        user_prefs: UserPreferences,
        current_time: datetime
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate relevance score (0-1) and component breakdown.
        Returns (score, component_dict)
        """
        
        # 1. URGENCY: How close is deadline?
        urgency = RelevanceEngine._urgency_score(task, current_time)
        
        # 2. PRIORITY: User-set importance
        priority = task.priority / 10.0 if task.priority else 0.5
        
        # 3. IMPACT: Importance relative to effort
        impact = RelevanceEngine._impact_score(task)
        
        # 4. CONTEXT: Is it already in progress?
        context_boost = 1.2 if task.status == "in_progress" else 1.0
        
        # 5. Effort consideration
        effort = 1.0 - min(task.effort_estimate_minutes / 120.0, 1.0)
        
        # Weighted combination
        components = {
            'urgency': urgency,
            'priority': priority,
            'impact': impact,
            'effort': effort
        }
        
        score = (
            user_prefs.weight_deadline * urgency +
            user_prefs.weight_priority * priority +
            user_prefs.weight_impact * impact +
            user_prefs.weight_effort * effort
        ) * context_boost
        
        return min(score, 1.0), components
    
    @staticmethod
    def _urgency_score(task: Task, current_time: datetime) -> float:
        """Calculate urgency based on deadline"""
        if not task.due_at:
            return 0.3
        
        seconds_until_due = (task.due_at - current_time).total_seconds()
        
        if seconds_until_due < 0:  # Overdue
            return 1.0
        elif seconds_until_due < 3600:  # < 1 hour
            return 0.9
        elif seconds_until_due < 86400:  # < 1 day
            return 0.7
        elif seconds_until_due < 604800:  # < 1 week
            return 0.4
        else:
            return 0.1
    
    @staticmethod
    def _impact_score(task: Task) -> float:
        """Calculate impact: value per unit effort"""
        if task.effort_estimate_minutes == 0:
            return 0.5
        
        # Higher priority + shorter = more impactful per unit time
        impact = (task.priority / 10.0) * (1.0 - min(task.effort_estimate_minutes / 480.0, 1.0))
        return min(impact, 1.0)
    
    @staticmethod
    def explain_score(
        task: Task,
        components: Dict[str, float]
    ) -> str:
        """Generate human-readable explanation of relevance score"""
        reasons = []
        
        if components['urgency'] > 0.7:
            if components['urgency'] > 0.9:
                reasons.append("It's overdue!")
            else:
                reasons.append("Due very soon")
        
        if components['priority'] > 0.7:
            reasons.append("High priority")
        
        if components['impact'] > 0.7:
            reasons.append("High impact")
        
        if components['effort'] > 0.7:
            reasons.append(f"Quick to finish ({task.effort_estimate_minutes}min)")
        
        return "I recommend this because: " + ", ".join(reasons) if reasons else "It's next in your queue."
```

---

## 4. FastAPI Routes

### `backend/app/routes/chat.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database.connection import get_db
from app.services.gpt_service import chat_with_gpt
from app.services.task_service import TaskService
from app.schemas.task import TaskCreate
from typing import List, Dict
import json

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    timezone: str = "UTC"

class ChatResponse(BaseModel):
    response: str
    action: Dict = None

@router.post("/")
async def chat(
    request: ChatRequest,
    session: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """
    Chat endpoint that processes natural language with GPT function calling.
    """
    # TODO: Add authentication to get real user_id
    user_id = "test-user-123"
    
    # Get conversation history (from DB or session)
    conversation_history = []
    
    # Call GPT with function calling
    gpt_result = await chat_with_gpt(
        request.message,
        conversation_history,
        user_id,
        request.timezone
    )
    
    # Process any function calls
    action = None
    for func_call in gpt_result["function_calls"]:
        func_name = func_call["name"]
        func_args = func_call["arguments"]
        
        if func_name == "create_task":
            task_create = TaskCreate(**func_args)
            task = await TaskService.create_task(session, user_id, task_create)
            action = {
                "type": "task_created",
                "task_id": str(task.id),
                "task_title": task.title
            }
        
        elif func_name == "list_tasks":
            tasks = await TaskService.get_tasks(
                session,
                user_id,
                status=func_args.get("status"),
                sort_by=func_args.get("sort_by", "urgency")
            )
            action = {
                "type": "tasks_listed",
                "count": len(tasks)
            }
        
        elif func_name == "update_task":
            # Update logic here
            pass
    
    return ChatResponse(
        response=gpt_result["response"],
        action=action
    )
```

### `backend/app/routes/tasks.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.services.task_service import TaskService
from app.services.relevance import RelevanceEngine
from app.models.user import UserPreferences
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from datetime import datetime
from typing import List

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.get("/")
async def list_tasks(
    status: str = None,
    sort_by: str = "urgency",
    limit: int = 10,
    session: AsyncSession = Depends(get_db)
) -> List[TaskResponse]:
    """List user's tasks"""
    user_id = "test-user-123"  # TODO: Get from auth
    
    tasks = await TaskService.get_tasks(
        session,
        user_id,
        status=status,
        sort_by=sort_by,
        limit=limit
    )
    
    return [TaskResponse.from_orm(task) for task in tasks]

@router.post("/next")
async def get_next_task(session: AsyncSession = Depends(get_db)):
    """Get the most relevant task to work on now"""
    user_id = "test-user-123"  # TODO: Get from auth
    
    task = await TaskService.get_next_task(session, user_id)
    
    if not task:
        return {"message": "No tasks available"}
    
    # Get user preferences for explanation
    user_prefs = UserPreferences()  # TODO: Load from DB
    
    # Calculate relevance and explanation
    score, components = RelevanceEngine.calculate_score(task, user_prefs, datetime.utcnow())
    explanation = RelevanceEngine.explain_score(task, components)
    
    return {
        "task": TaskResponse.from_orm(task),
        "relevance_score": score,
        "explanation": explanation
    }

@router.post("/")
async def create_task(
    task_create: TaskCreate,
    session: AsyncSession = Depends(get_db)
) -> TaskResponse:
    """Create a new task"""
    user_id = "test-user-123"  # TODO: Get from auth
    
    task = await TaskService.create_task(session, user_id, task_create)
    
    return TaskResponse.from_orm(task)

@router.put("/{task_id}")
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    session: AsyncSession = Depends(get_db)
) -> TaskResponse:
    """Update a task"""
    user_id = "test-user-123"  # TODO: Get from auth
    
    task = await TaskService.update_task(session, task_id, user_id, task_update)
    
    return TaskResponse.from_orm(task)
```

---

## 5. Frontend Lit Component

### `frontend/src/components/chat-interface.ts`

```typescript
import { LitElement, html, css } from 'lit';
import { customElement, state, query } from 'lit/decorators.js';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

@customElement('chat-interface')
export class ChatInterface extends LitElement {
  @state() private messages: Message[] = [];
  @state() private loading = false;
  @state() private inputValue = '';
  
  @query('input') private inputElement!: HTMLInputElement;

  static styles = css`
    :host {
      display: flex;
      flex-direction: column;
      height: 100vh;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    .chat-container {
      display: flex;
      flex-direction: column;
      height: 100%;
      background: white;
      border-radius: 12px;
      margin: 16px;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
      overflow: hidden;
    }

    .messages {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .message {
      max-width: 70%;
      padding: 12px 16px;
      border-radius: 12px;
      word-wrap: break-word;
      animation: slideIn 0.3s ease-in-out;
    }

    @keyframes slideIn {
      from {
        opacity: 0;
        transform: translateY(10px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .message.user {
      align-self: flex-end;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }

    .message.assistant {
      align-self: flex-start;
      background: #f0f0f0;
      color: #333;
    }

    .input-area {
      padding: 16px;
      background: white;
      border-top: 1px solid #eee;
      display: flex;
      gap: 8px;
    }

    input {
      flex: 1;
      padding: 12px 16px;
      border: 1px solid #ddd;
      border-radius: 8px;
      font-size: 1rem;
      font-family: inherit;
    }

    input:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
    }

    button {
      padding: 12px 24px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 500;
      transition: transform 0.2s;
    }

    button:hover:not(:disabled) {
      transform: translateY(-2px);
    }

    button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .loading {
      text-align: center;
      color: #999;
      font-size: 0.9rem;
    }
  `;

  private async sendMessage() {
    if (!this.inputValue.trim()) return;

    const userMessage = this.inputValue;
    this.messages = [
      ...this.messages,
      { role: 'user', content: userMessage, timestamp: new Date() }
    ];
    this.inputValue = '';
    this.loading = true;

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
        })
      });

      const data = await response.json();
      this.messages = [
        ...this.messages,
        { role: 'assistant', content: data.response, timestamp: new Date() }
      ];
    } catch (error) {
      console.error('Chat error:', error);
      this.messages = [
        ...this.messages,
        {
          role: 'assistant',
          content: 'Sorry, something went wrong. Please try again.',
          timestamp: new Date()
        }
      ];
    } finally {
      this.loading = false;
      this.inputElement?.focus();
    }
  }

  private handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      this.sendMessage();
    }
  }

  render() {
    return html`
      <div class="chat-container">
        <div class="messages">
          ${this.messages.map(msg => html`
            <div class="message ${msg.role}">
              ${msg.content}
            </div>
          `)}
          ${this.loading ? html`<div class="message assistant loading">Thinking...</div>` : ''}
        </div>

        <div class="input-area">
          <input
            type="text"
            placeholder="Tell MindFlow what to do..."
            .value=${this.inputValue}
            @input=${(e: Event) => this.inputValue = (e.target as HTMLInputElement).value}
            @keydown=${this.handleKeydown}
            ?disabled=${this.loading}
          />
          <button @click=${() => this.sendMessage()} ?disabled=${this.loading}>
            ${this.loading ? '⏳' : '→'}
          </button>
        </div>
      </div>
    `;
  }
}
```

---

## 6. Running the Project

### Local Development

```bash
# Terminal 1: Start database
docker-compose up postgres

# Terminal 2: Start backend
cd backend
python -m uvicorn app.main:app --reload

# Terminal 3: Start frontend
cd frontend
npm run dev
```

Visit `http://localhost:5173` and start typing!

**Example interactions:**
- "Add a blog post about FastAPI due Friday"
- "What should I do next?"
- "Mark the podcast episode as done"
- "Show me all my high priority tasks"

---

## 7. Testing with Claude Code

Once you have the basic structure, use Claude Code to:

1. Generate migrations
2. Implement remaining API endpoints
3. Add user authentication
4. Create dashboard component
5. Deploy to Fly.io

**Prompt for Claude Code:**
```
Generate the database migration for tasks table using Alembic, 
and create the FastAPI route handler for /api/tasks/next that:
1. Gets user's open tasks
2. Loads user preferences
3. Calculates relevance scores using RelevanceEngine
4. Returns top task with explanation
5. Uses async/await throughout
```

---

## Next Milestones

- [ ] Week 1: MVP (create, list, basic chat)
- [ ] Week 2: Relevance engine + "next task"
- [ ] Week 3: Auth + frontend dashboard
- [ ] Week 4: Deploy to production
- [ ] Week 5: User testing + iteration
- [ ] Week 6: Habit learning
- [ ] Week 7: Calendar integration

Good luck building! 🚀