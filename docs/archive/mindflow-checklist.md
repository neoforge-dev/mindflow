# MindFlow: Week-by-Week Implementation Checklist

## Week 1: Foundation & Core API

### Day 1-2: Project Setup & Database

**Backend Structure**
- [ ] Create `backend/` directory with Python 3.11+
- [ ] Initialize virtual environment and `requirements.txt`
  ```
  fastapi==0.104.1
  uvicorn==0.24.0
  sqlalchemy==2.0.0
  psycopg2-binary==2.9.0
  openai==1.3.0
  pydantic==2.0.0
  pydantic-settings==2.0.0
  alembic==1.13.0
  python-dotenv==1.0.0
  pytest==7.4.0
  ```
- [ ] Create `app/` package structure:
  ```
  app/
  ├── __init__.py
  ├── main.py
  ├── config.py
  ├── models/
  ├── schemas/
  ├── routes/
  ├── services/
  ├── database/
  └── utils/
  ```
- [ ] Set up Supabase project or local PostgreSQL
  - [ ] Create database: `mindflow_db`
  - [ ] Connection string: `postgresql://user:pass@localhost/mindflow_db`
- [ ] Create `app/config.py` with Settings class (use mindflow-starter.txt)
- [ ] Create `app/database/connection.py` with async engine setup

**Database Schema**
- [ ] Initialize Alembic: `alembic init migrations`
- [ ] Create `app/models/user.py` (User, UserPreferences)
- [ ] Create `app/models/task.py` (Task model with all fields from spec)
- [ ] Create `app/models/conversation.py` (ConversationLog model)
- [ ] Generate Alembic migration: `alembic revision --autogenerate -m "initial"`
- [ ] Apply migration: `alembic upgrade head`
- [ ] Verify tables created in database

**Frontend Structure**
- [ ] Create `frontend/` directory
- [ ] Initialize Vite project: `npm create vite@latest frontend -- --template lit-ts`
- [ ] Create folder structure:
  ```
  src/
  ├── main.ts
  ├── index.html
  ├── components/
  ├── services/
  └── styles/
  ```
- [ ] Install dependencies: Lit, TypeScript, Tailwind
- [ ] Set up Vite dev server

**Docker Setup**
- [ ] Create `docker-compose.yml` (from mindflow-summary.txt)
- [ ] Test with `docker-compose up postgres`
- [ ] Create `.env.example` for both backend and frontend

**Deliverable:** Project structure complete, database running

---

### Day 3: FastAPI Setup & Basic Routes

**FastAPI Application**
- [ ] Create `app/main.py` with FastAPI app initialization
  ```python
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  
  app = FastAPI(title="MindFlow")
  
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["localhost:5173"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  
  @app.get("/health")
  async def health():
      return {"status": "ok"}
  ```
- [ ] Test server: `python -m uvicorn app.main:app --reload`
- [ ] Verify Swagger docs at `http://localhost:8000/docs`

**Database Service**
- [ ] Create `app/services/task_service.py` with TaskService class
  - [ ] `create_task()` method
  - [ ] `get_tasks()` method
  - [ ] `update_task()` method
  - [ ] `delete_task()` method
  - [ ] `get_next_task()` method (placeholder for now)
- [ ] Use code from mindflow-starter.txt

**API Routes**
- [ ] Create `app/routes/tasks.py`
  - [ ] `GET /api/tasks` - list tasks
  - [ ] `POST /api/tasks` - create task
  - [ ] `PUT /api/tasks/{id}` - update task
  - [ ] `DELETE /api/tasks/{id}` - delete task
  - [ ] `GET /api/tasks/next` - get next task (placeholder)
- [ ] Include in main.py: `app.include_router(router, prefix="/api")`
- [ ] Test with curl or Postman

**Test Data**
- [ ] Create test script to populate sample tasks
- [ ] Verify GET endpoints return correct data

**Deliverable:** API endpoints working, can create/list tasks

---

### Day 4-5: OpenAI Integration

**Function Definitions**
- [ ] Create `app/services/gpt_service.py`
- [ ] Define TASK_FUNCTIONS schema (from mindflow-starter.txt):
  - [ ] `create_task` function schema
  - [ ] `list_tasks` function schema
  - [ ] `update_task` function schema
  - [ ] `delete_task` function schema
  - [ ] `get_next_task` function schema

**GPT Chat Integration**
- [ ] Create `chat_with_gpt()` async function in gpt_service.py
- [ ] Implement Chat Completions API call with function calling
- [ ] Handle function call responses (extract function name + args)
- [ ] Create system prompt for MindFlow personality

**Chat Route**
- [ ] Create `app/routes/chat.py`
- [ ] POST `/api/chat` endpoint:
  ```python
  @router.post("/")
  async def chat(request: ChatRequest, session: AsyncSession):
      # 1. Call GPT with function calling
      # 2. Parse function calls
      # 3. Execute task operations
      # 4. Return response
  ```
- [ ] Handle the function calling loop:
  - GPT suggests function → Extract args
  - Execute (create_task, list_tasks, etc)
  - Add result to conversation
  - Get final response from GPT

**Testing**
- [ ] Test with curl:
  ```bash
  curl -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "Add a task about FastAPI due Friday"}'
  ```
- [ ] Verify task is created in database
- [ ] Check GPT response is natural language

**Deliverable:** Chat endpoint working end-to-end

---

## Week 2: Relevance Engine & Dashboard

### Day 6-7: Relevance Scoring

**Relevance Engine**
- [ ] Create `app/services/relevance.py`
- [ ] Implement `RelevanceEngine` class with:
  - [ ] `calculate_score()` - main scoring function
  - [ ] `_urgency_score()` - deadline proximity
  - [ ] `_priority_score()` - user-set priority
  - [ ] `_impact_score()` - value per effort
  - [ ] `_effort_score()` - task duration
  - [ ] `explain_score()` - natural language explanation

**Algorithm Testing**
- [ ] Create test cases for different task scenarios:
  - [ ] Overdue task (urgency = 1.0)
  - [ ] Task due today (urgency = 0.7)
  - [ ] Task due next week (urgency = 0.4)
  - [ ] High priority + short (high impact)
  - [ ] Low priority + long (low impact)
- [ ] Verify weighting logic works correctly
- [ ] Test edge cases (no due date, priority 0, etc)

**Get Next Task**
- [ ] Implement `get_next_task()` in TaskService
- [ ] Update `/api/tasks/next` route:
  ```python
  @router.get("/next")
  async def get_next_task(session: AsyncSession):
      task = await TaskService.get_next_task(session, user_id)
      prefs = await UserPreferences.load(session, user_id)
      score, components = RelevanceEngine.calculate_score(task, prefs)
      explanation = RelevanceEngine.explain_score(task, components)
      return {"task": task, "score": score, "explanation": explanation}
  ```
- [ ] Manual testing with multiple tasks

**Deliverable:** Relevance engine complete and tested

---

### Day 8-10: Frontend Chat Interface

**Lit Component Structure**
- [ ] Create `src/components/chat-interface.ts`:
  - [ ] Extend LitElement
  - [ ] Define properties: messages[], inputValue, loading
  - [ ] Implement sendMessage() handler
  - [ ] Implement render() with HTML template
  - [ ] Add CSS styles (from mindflow-starter.ts)

**Chat Component Details**
- [ ] Message state management with Lit @state() decorator
- [ ] Input field with @input event binding
- [ ] Send button with @click handler
- [ ] Message rendering with user/assistant styling
- [ ] Auto-scroll to latest message
- [ ] Loading indicator while waiting for response

**API Integration**
- [ ] Create `src/services/api.ts`:
  ```typescript
  export async function sendChatMessage(message: string): Promise<ChatResponse> {
      const response = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message, timezone: getUserTimezone() })
      });
      return await response.json();
  }
  ```
- [ ] Error handling and retry logic
- [ ] Loading states

**Dashboard Component**
- [ ] Create `src/components/task-list.ts`
- [ ] Display tasks in sortable list
- [ ] Show urgency score, due date, priority
- [ ] Highlight "next task" recommendation
- [ ] Mark tasks complete with checkbox

**Main App**
- [ ] Create `src/main.ts` entry point
- [ ] Import and register components
- [ ] Add Tailwind CSS imports
- [ ] Create main layout

**Testing**
- [ ] Run `npm run dev` and verify UI loads
- [ ] Test sending a message from browser
- [ ] Verify chat bubbles appear
- [ ] Check API calls in Network tab

**Deliverable:** Functional chat UI connected to backend

---

## Week 3: Polish & Deployment

### Day 11: Authentication (Basic)

**JWT Setup**
- [ ] Create `app/auth/jwt_auth.py`:
  - [ ] `create_access_token()` - generate JWT
  - [ ] `verify_token()` - validate JWT
  - [ ] `get_current_user()` - dependency for routes
- [ ] Add JWT secret to config

**Authentication Endpoints**
- [ ] Create `app/routes/auth.py`:
  - [ ] POST `/api/auth/login` - generate token
  - [ ] POST `/api/auth/signup` - create user
- [ ] Hash passwords with bcrypt

**Apply Auth to Routes**
- [ ] Update `/api/tasks` routes to require auth
- [ ] Update `/api/chat` to require auth
- [ ] Extract user_id from JWT token

**Frontend Auth**
- [ ] Create login form component
- [ ] Store JWT token in localStorage
- [ ] Include token in API request headers
- [ ] Redirect to login if unauthorized

**Deliverable:** Multi-user support with basic auth

---

### Day 12: Dashboard & Final Polish

**Task Dashboard**
- [ ] Display "Next Task" suggestion prominently
- [ ] Show all open tasks in list
- [ ] Display relevance score breakdown
- [ ] Show explanation of why task is recommended
- [ ] Add completion checkbox for tasks

**UI Polish**
- [ ] Responsive design (mobile + desktop)
- [ ] Smooth animations (message slide-in)
- [ ] Loading skeletons for better UX
- [ ] Error messages and toast notifications
- [ ] Dark mode toggle (optional)

**Performance**
- [ ] Minify frontend bundle
- [ ] Optimize API queries with indexes
- [ ] Add caching where appropriate
- [ ] Measure Lighthouse scores

**Deliverable:** Production-ready UI

---

### Day 13-14: Deployment

**Docker Build & Push**
- [ ] Create `backend/Dockerfile`:
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install -r requirements.txt
  COPY app/ app/
  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
  ```
- [ ] Create `frontend/Dockerfile`:
  ```dockerfile
  FROM node:18-alpine AS build
  WORKDIR /app
  COPY package*.json .
  RUN npm install && npm run build
  
  FROM nginx:alpine
  COPY --from=build /app/dist /usr/share/nginx/html
  ```
- [ ] Test locally: `docker-compose up`

**Fly.io Deployment**
- [ ] Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
- [ ] Create `backend/fly.toml`:
  ```toml
  app = "mindflow-backend"
  
  [build]
    image = "mindflow-backend:latest"
  
  [env]
    DATABASE_URL = "postgresql://..."
    OPENAI_API_KEY = "sk-..."
  ```
- [ ] Deploy: `fly deploy`
- [ ] Verify API is accessible at `https://mindflow-backend.fly.dev`

**Frontend Deployment**
- [ ] Deploy to Vercel or Netlify (simpler for frontend)
- [ ] Or use Fly.io for unified deployment
- [ ] Update API_URL to point to deployed backend

**Database**
- [ ] Use Supabase PostgreSQL (managed, auto-backup)
- [ ] Run migrations on production
- [ ] Verify tables and indexes created

**Testing**
- [ ] Test chat endpoint with deployed version
- [ ] Create a task via deployed UI
- [ ] Verify data persists
- [ ] Check performance (should be < 500ms)

**Deliverable:** Live product at public URL

---

## Week 4-6: Iteration & Polish

### Day 15-21: User Testing & Feedback

**Beta Users**
- [ ] Recruit 5-10 beta testers (friends, colleagues, LinkedIn)
- [ ] Create onboarding guide
- [ ] Send link to deployed product
- [ ] Collect feedback via form/survey
- [ ] Track usage analytics

**Common Feedback Patterns**
- [ ] Fix bugs reported
- [ ] Improve UX based on suggestions
- [ ] Add most requested feature
- [ ] Optimize slow queries

**Habit Learning (Optional)**
- [ ] Start learning user preferences
- [ ] Analyze completed tasks to refine weights
- [ ] Show personalization improving over time

**Deliverable:** Refined product based on real usage

---

## Daily Standup Template

```
Date: [Date]
Week: [1-6]
Day: [1-21]

✅ Completed:
- [List what was done]

⏳ In Progress:
- [What you're working on now]

🚧 Blockers:
- [Any issues]

📅 Tomorrow:
- [Next task]
```

---

## Success Metrics

### MVP Complete (End of Week 3)
- [ ] 500 lines of code total
- [ ] ✅ Chat endpoint working
- [ ] ✅ Create tasks via natural language
- [ ] ✅ List tasks with relevance sort
- [ ] ✅ Get "next task" recommendation
- [ ] ✅ Frontend deployed
- [ ] ✅ Zero "sticky" clicks (all conversation)

### Phase 2 Complete (End of Week 6)
- [ ] 1200 lines of code
- [ ] ✅ 5-10 beta users
- [ ] ✅ Habit learning prototype
- [ ] ✅ Calendar sync (optional)
- [ ] ✅ Average response time < 500ms
- [ ] ✅ 95% uptime
- [ ] ✅ Database optimized

---

## Quick Reference Commands

```bash
# Backend
poetry add fastapi uvicorn sqlalchemy
alembic revision --autogenerate -m "description"
alembic upgrade head
python -m uvicorn app.main:app --reload

# Frontend
npm create vite@latest frontend -- --template lit-ts
npm install lit typescript vite tailwindcss
npm run dev
npm run build

# Docker
docker-compose up postgres
docker-compose down

# Deployment
fly apps create mindflow-backend
fly deploy
fly logs
```

---

## Resources & Support

- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/
- **OpenAI Function Calling:** https://platform.openai.com/docs/guides/function-calling
- **Lit Documentation:** https://lit.dev/docs/
- **Supabase Docs:** https://supabase.com/docs
- **Fly.io Docs:** https://fly.io/docs/

---

## Your Success Path

Week 1 → MVP with chat ✅
Week 2 → Relevance engine ✅
Week 3 → Deploy & polish ✅
Week 4-6 → User feedback & iteration ✅

**Total effort:** ~40-50 hours of focused work
**Result:** Production-grade AI task manager
**Timeline:** Ready to show users by end of week 3

Let's build! 🚀