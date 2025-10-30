# MindFlow: Week-by-Week Build Plan + Bootstrap Script

**Goal**: Deploy Phase 1 (GAS MVP) this week, Phase 2 (FastAPI) production in 4 weeks  
**Effort**: 20–30 hours/week  
**Target Users**: Early access in 3 weeks

---

## Week 1: Phase 1 MVP (GAS + Sheets) ✅ LAUNCH

### Day 1–2: Setup GAS & Sheets

```bash
# Step 1: Create Google Sheet
1. Go to sheets.google.com → Create new sheet
2. Name it "MindFlow MVP"
3. Add tabs: tasks, logs, users
4. Create headers from the data model doc

# Step 2: Deploy Google Apps Script
1. Go to script.google.com → New project
2. Copy the GAS code from the implementation guide
3. Deploy → Web App (public access)
4. Copy deployment URL
```

### Day 3: Custom GPT Setup

```bash
# Step 3: Create Custom GPT
1. Go to https://chat.openai.com/gpts
2. Click "Create a GPT"
3. Name: "MindFlow Assistant"
4. Paste system prompt from guide
5. Add actions (OpenAPI schema with GAS URL)
6. Test with: "What should I do next?"

# Step 4: Verify end-to-end
- Ask GPT: "Create task: review metrics by Friday"
- Check Google Sheets: task should appear
- Ask GPT: "What should I do?"
- GPT should return highest-scored task
```

### Day 4–5: First Users & Feedback

```bash
# Step 5: Recruit 10 early users
- Post on ProductHunt Ship
- Tweet/LinkedIn about it
- Ask Discord/Twitter communities
- Record Loom demo

# Step 6: Collect feedback (typeform)
- Does scoring feel right?
- Missing features?
- What would make you pay?
```

**Milestone**: Phase 1 MVP deployed, 10 signups, feedback collected

---

## Week 2–3: Phase 1 Iteration

### Improve Scoring Based on Feedback

```python
# If users say "scoring feels off":
# Adjust weights in scoreTask() function
# Example: If urgent tasks ignored, increase urgency_weight from 0.35 → 0.45
```

### Add Simple Features

- [ ] Snooze task (in GAS)
- [ ] Update task priority via chat
- [ ] View all tasks via GPT
- [ ] Recurring tasks (simple)

### Track Metrics

- DAU (daily active users)
- Tasks created/completed per user
- Feature most used

---

## Week 4: Begin Phase 2 Backend (Parallel Build)

### Days 1–2: FastAPI Project Scaffold

```bash
# Initialize project
mkdir mindflow-v2
cd mindflow-v2

# Backend setup
mkdir -p backend/app/{api,db,schemas,services,middleware,utils}
cd backend

# Create Python environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize git
git init
git add .
git commit -m "Initial FastAPI scaffold"

# Create main.py
cat > app/main.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="MindFlow API", version="2.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://mindflow.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# Run locally
uvicorn app.main:app --reload
# Should see: http://localhost:8000/docs (Swagger UI)
```

### Days 3–4: Supabase Setup

```bash
# 1. Sign up at https://supabase.com
# 2. Create project (shared tier)
# 3. Wait for deployment (~5 minutes)

# 4. Get connection string from Settings → Database

# 5. Save to .env
cat > .env << 'EOF'
DATABASE_URL=postgresql+asyncpg://postgres:[password]@[host]:5432/postgres
SECRET_KEY=$(openssl rand -hex 32)
OPENAI_API_KEY=sk-...
ENVIRONMENT=development
EOF

# 6. Run migrations (create tables)
alembic upgrade head
```

### Day 5: First Endpoints

```bash
# Implement:
# POST /api/auth/register
# POST /api/auth/login
# POST /api/tasks (create)
# GET /api/tasks/best (get best task)

# Test with curl
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"secret"}'
```

**Milestone**: FastAPI server running locally, connected to Supabase, basic auth working

---

## Week 5: Phase 2 Frontend

### Days 1–2: LIT Project Setup

```bash
# Frontend setup
cd frontend
npm create vite@latest mindflow-ui -- --template lit-ts
cd mindflow-ui
npm install

# Install additional libraries
npm install --save-dev vitest @testing-library/lit

# Run dev server
npm run dev
# Should see http://localhost:5173
```

### Days 3–4: Core Components

```typescript
// src/components/app-shell.ts
// Copy from production guide

// src/services/api.ts
// Create API wrapper with retry logic

// src/components/task-board.ts
// Display tasks from backend
```

### Day 5: Connect Frontend ↔ Backend

```typescript
// In chat-interface.ts
async sendMessage(userInput: string) {
  const response = await fetch('http://localhost:8000/api/chat', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ message: userInput })
  });
  
  const aiResponse = await response.json();
  this.messages.push({
    role: 'assistant',
    content: aiResponse.content
  });
}
```

**Milestone**: Frontend fetching tasks from FastAPI, real-time updates via WebSocket

---

## Week 6: Docker + Deployment

### Days 1–2: Dockerize

```dockerfile
# backend/Dockerfile (see production guide)
# frontend/Dockerfile (simple nginx)

# Test locally
docker-compose up -d
# Should see API at :8000, Frontend at :80
```

### Days 3–5: Deploy to Fly.io

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Deploy API
cd backend
flyctl launch --name mindflow-api --region ams
flyctl secrets set SECRET_KEY="..."
flyctl secrets set OPENAI_API_KEY="..."
flyctl secrets set DATABASE_URL="..."
flyctl deploy

# Deploy Frontend
cd ../frontend
flyctl launch --name mindflow-ui --region ams
flyctl deploy
```

**Milestone**: Production MVP deployed at mindflow-api.fly.dev, mindflow-ui.fly.dev

---

## Bootstrap Script (Copy & Run)

Save as `bootstrap.sh`:

```bash
#!/bin/bash

set -e  # Exit on error

echo "🚀 MindFlow Bootstrap"
echo "===================="

# Color output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create project structure
echo -e "${BLUE}📁 Creating project structure...${NC}"
mkdir -p mindflow/{backend,frontend}
cd mindflow

# Backend initialization
echo -e "${BLUE}🐍 Setting up FastAPI backend...${NC}"
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Create requirements.txt
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
sqlalchemy[asyncio]==2.0.23
asyncpg==0.29.0
alembic==1.12.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
openai==1.3.9
supabase==2.3.5
python-json-logger==2.0.7
sentry-sdk==1.38.0
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.1
black==23.12.0
ruff==0.1.8
EOF

# Install dependencies
pip install -r requirements.txt

# Create app directory structure
mkdir -p app/{api,db,schemas,services,middleware,utils}
touch app/__init__.py

# Create main.py
cat > app/main.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="MindFlow API",
    version="2.0.0",
    description="AI-first task management"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://*.fly.dev"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "environment": os.getenv("ENVIRONMENT", "development")}

# Import routers
from app.api import tasks, users, ai
app.include_router(tasks.router)
app.include_router(users.router)
app.include_router(ai.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENVIRONMENT") != "production"
    )
EOF

# Create config
cat > app/config.py << 'EOF'
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://localhost/mindflow")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")

settings = Settings()
EOF

# Create .env
cat > .env << 'EOF'
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/mindflow
SECRET_KEY=$(openssl rand -hex 32)
OPENAI_API_KEY=sk-your-key-here
EOF

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
RUN pip install uv
COPY requirements.txt .
RUN uv pip install -r requirements.txt --system
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

echo -e "${GREEN}✅ Backend initialized${NC}"

# Frontend initialization
echo -e "${BLUE}⚛️  Setting up LIT + TypeScript frontend...${NC}"
cd ../frontend

npm create vite@latest . -- --template lit-ts
npm install

# Create .env
cat > .env << 'EOF'
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
EOF

echo -e "${GREEN}✅ Frontend initialized${NC}"

# Create docker-compose
cd ..
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: mindflow
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  fastapi:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/mindflow
      ENVIRONMENT: development
    depends_on:
      - postgres
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app

volumes:
  postgres_data:
EOF

# Create git repo
git init
cat > .gitignore << 'EOF'
venv/
node_modules/
.env
__pycache__/
*.pyc
.DS_Store
dist/
build/
*.egg-info/
.pytest_cache/
EOF

git add .
git commit -m "🚀 Initial MindFlow project scaffold"

echo -e "${GREEN}✅ Project bootstrap complete!${NC}"
echo ""
echo -e "${BLUE}📝 Next steps:${NC}"
echo "1. Update .env with your settings"
echo "2. Run: docker-compose up -d"
echo "3. Backend: http://localhost:8000/docs"
echo "4. Frontend: http://localhost:5173"
echo ""
echo "Or run locally (dev):"
echo "  cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "  cd frontend && npm run dev"
```

### Run Bootstrap

```bash
curl -fsSL https://raw.githubusercontent.com/yourusername/mindflow/main/bootstrap.sh | bash
# Or
chmod +x bootstrap.sh
./bootstrap.sh
```

---

## Development Workflow (After Bootstrap)

### Local Development

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
# Visit: http://localhost:8000/docs

# Terminal 2: Frontend
cd frontend
npm run dev
# Visit: http://localhost:5173

# Terminal 3: Database (Docker)
docker run -d \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=mindflow \
  -p 5432:5432 \
  postgres:15
```

### Testing

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npm run test

# Type checking
npx tsc --noEmit
```

### Code Quality

```bash
# Format Python
black app/

# Lint Python
ruff check app/

# Format TypeScript
npx prettier --write src/

# Lint TypeScript
npx eslint src/
```

### Deploy to Fly.io

```bash
# First time setup
flyctl launch

# Subsequent deploys
flyctl deploy

# View logs
flyctl logs

# Set secrets
flyctl secrets set OPENAI_API_KEY="sk-..."
```

---

## Success Metrics

### Week 1 (Phase 1 MVP)
- [ ] GAS deployed and public
- [ ] Custom GPT created and tested
- [ ] 10+ early users
- [ ] 5+ feedback submissions
- [ ] Zero bugs reported

### Week 4–6 (Phase 2 MVP)
- [ ] FastAPI server running locally
- [ ] Frontend fetching from API
- [ ] Docker setup working
- [ ] Deployed to Fly.io
- [ ] 20+ DAU
- [ ] Avg. 10+ tasks/user

### Month 2 (Production Ready)
- [ ] JWT auth + refresh tokens
- [ ] Real-time WebSocket updates
- [ ] Error monitoring (Sentry)
- [ ] Database migrations (Alembic)
- [ ] 100+ DAU
- [ ] Positive NPS score (>40)

---

## Rapid Debug Checklist

| Issue | Solution |
|-------|----------|
| **API not responding** | Check: `uvicorn app.main:app --reload` running, port 8000 free |
| **Frontend blank** | Check: VITE_API_URL correct in .env, npm build succeeds |
| **Database errors** | Check: DATABASE_URL valid, Postgres running, tables migrated |
| **Auth failing** | Check: SECRET_KEY set, JWT token format correct, exp not passed |
| **GPT not responding** | Check: OPENAI_API_KEY valid, API quota remaining, function schema correct |
| **Deployment fails** | Check: Docker builds locally, fly.toml syntax, secrets set |

---

## Reference Links

- FastAPI: https://fastapi.tiangolo.com/
- LIT: https://lit.dev/
- Supabase: https://supabase.com/docs
- Fly.io: https://fly.io/docs/
- OpenAI: https://platform.openai.com/docs/guides/gpt
- Alembic (DB migrations): https://alembic.sqlalchemy.org/

---

**Created**: October 30, 2025  
**For**: Solo Python backend engineer building AI-first SaaS  
**Effort**: 4–6 weeks to Phase 2 MVP  
**Cost**: $50–100/mo infrastructure  
**Target**: Launch to 100 DAU by end of November
