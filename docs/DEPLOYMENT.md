# MindFlow: Deployment Guide

**Last Updated**: 2025-11-02
**Target**: $10 DigitalOcean Droplet + Cloudflare Pages
**Stack**: Docker + FastAPI + PostgreSQL + ChatGPT Apps SDK
**Status**: Production Ready for Open Beta (256 tests passing, 80.63% coverage)

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [OAuth 2.1 & Security Setup](#oauth-21--security-setup)
4. [Docker Setup](#docker-setup)
5. [DigitalOcean Droplet Setup](#digitalocean-droplet-setup)
6. [MCP Server Configuration](#mcp-server-configuration)
7. [ChatGPT Apps SDK Integration](#chatgpt-apps-sdk-integration)
8. [Database Migration](#database-migration)
9. [Environment Configuration](#environment-configuration)
10. [Open Beta Launch Checklist](#open-beta-launch-checklist)
11. [Monitoring & Logging](#monitoring--logging)
12. [Troubleshooting](#troubleshooting)

---

## Overview

### Deployment Architecture

```
┌─────────────────────────────────────────┐
│   users.mindflow.app (Custom GPT)       │
└───────────────┬─────────────────────────┘
                │ HTTPS
┌───────────────▼─────────────────────────┐
│   Cloudflare Pages (Frontend - FREE)    │
│   • Static LIT dashboard (optional)     │
│   • Global CDN                           │
│   • HTTPS auto-configured                │
└───────────────┬─────────────────────────┘
                │ API Requests (HTTPS)
┌───────────────▼─────────────────────────┐
│   Cloudflare (Proxy + DDoS Protection)  │
│   • Caching layer                        │
│   • Rate limiting                        │
│   • SSL termination                      │
└───────────────┬─────────────────────────┘
                │ HTTPS → HTTP
┌───────────────▼─────────────────────────┐
│   DigitalOcean Droplet ($10/month)      │
│   ┌─────────────────────────────────┐   │
│   │  Docker Container: FastAPI      │   │
│   │  • Uvicorn (2 workers)          │   │
│   │  • Port 8000                     │   │
│   └──────────────┬──────────────────┘   │
│   ┌──────────────▼──────────────────┐   │
│   │  Docker Container: PostgreSQL   │   │
│   │  • Port 5432 (internal only)    │   │
│   │  • Data volume mounted          │   │
│   └─────────────────────────────────┘   │
│   ┌─────────────────────────────────┐   │
│   │  Caddy (Reverse Proxy)          │   │
│   │  • Port 80 → 8000               │   │
│   │  • Automatic HTTPS               │   │
│   └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### Cost Breakdown

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| DigitalOcean Droplet | 2 vCPU, 2GB RAM, 50GB SSD | $12/month |
| Cloudflare Pages | Unlimited bandwidth, 500 builds/month | FREE |
| Domain (optional) | Custom domain | $12/year |
| **Total** | | **$12/month + $1/month domain** |

**Note**: This is 70% cheaper than Fly.io + Supabase (~$35-40/month)

---

## Prerequisites

### Required Accounts

1. **DigitalOcean**: https://digitalocean.com (get $200 credit with referral)
2. **Cloudflare**: https://cloudflare.com (free tier)
3. **GitHub**: For CI/CD and Cloudflare Pages deployment

### Required Tools

```bash
# Install Docker
# macOS: https://docs.docker.com/desktop/install/mac-install/
# Linux: https://docs.docker.com/engine/install/ubuntu/

# Verify Docker
docker --version
docker-compose --version

# Install doctl (DigitalOcean CLI)
# macOS
brew install doctl

# Linux
cd ~
wget https://github.com/digitalocean/doctl/releases/download/v1.104.0/doctl-1.104.0-linux-amd64.tar.gz
tar xf doctl-1.104.0-linux-amd64.tar.gz
sudo mv doctl /usr/local/bin

# Verify
doctl version
```

---

## OAuth 2.1 & Security Setup

### Step 1: Generate RS256 Key Pair

**On your local machine**:

```bash
# Generate private key (RS256)
openssl genrsa -out oauth_private_key.pem 2048

# Generate public key
openssl rsa -in oauth_private_key.pem -pubout -out oauth_public_key.pem

# View keys
cat oauth_private_key.pem
cat oauth_public_key.pem
```

**Security Notes**:
- **NEVER** commit private keys to git
- Store private key in `.env` file on server
- Public key can be exposed via `/oauth/jwks` endpoint
- Rotate keys every 90 days

### Step 2: OAuth Client Registration

For open beta, you'll need to register OAuth clients for:
1. ChatGPT Apps SDK integration
2. External service integrations (if any)

**Create OAuth client** (via API or database):

```sql
-- Connect to database
docker-compose -f docker-compose.prod.yml exec postgres psql -U mindflow -d mindflow

-- Create OAuth client for ChatGPT
INSERT INTO oauth_clients (
    id,
    client_id,
    client_name,
    client_secret_hash,
    redirect_uris,
    grant_types,
    scope,
    created_at
) VALUES (
    gen_random_uuid(),
    'chatgpt_mindflow',
    'ChatGPT MindFlow Integration',
    '<bcrypt-hash-of-client-secret>',
    ARRAY['https://chat.openai.com/aip/oauth/callback'],
    ARRAY['authorization_code', 'refresh_token'],
    'read write',
    NOW()
);
```

### Step 3: PKCE Configuration

PKCE (Proof Key for Code Exchange) is **required** for OAuth 2.1:

**Verify configuration** in `backend/app/oauth/authorize.py`:
- ✅ `code_challenge` parameter required
- ✅ `code_challenge_method` set to `S256`
- ✅ Code verifier validation on token exchange

**Test PKCE flow**:
```bash
# Generate code verifier
CODE_VERIFIER=$(openssl rand -base64 32 | tr -d '=+/' | cut -c1-43)

# Generate code challenge (SHA256)
CODE_CHALLENGE=$(echo -n "$CODE_VERIFIER" | openssl dgst -binary -sha256 | openssl base64 | tr -d '=+/' | cut -c1-43)

# Authorization request
curl "https://api.yourdomain.com/oauth/authorize?client_id=chatgpt_mindflow&response_type=code&redirect_uri=https://chat.openai.com/aip/oauth/callback&code_challenge=$CODE_CHALLENGE&code_challenge_method=S256"
```

### Step 4: JWT Configuration

**Update `.env` on server**:
```bash
# OAuth 2.1 RS256 Keys
OAUTH_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n<multiline-key>\n-----END RSA PRIVATE KEY-----"
OAUTH_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n<multiline-key>\n-----END PUBLIC KEY-----"

# JWT Settings
JWT_ALGORITHM=RS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# Token Rotation
REFRESH_TOKEN_ROTATION_ENABLED=true
```

### Step 5: Security Hardening

**Rate Limiting**:
```bash
# Update Caddyfile
nano ~/app/Caddyfile

# Add rate limiting per endpoint
api.yourdomain.com {
    reverse_proxy api:8000

    # OAuth endpoints (more permissive)
    rate_limit /oauth/* {
        zone oauth {
            key {remote_host}
            events 10
            window 1m
        }
    }

    # API endpoints (stricter)
    rate_limit /api/* {
        zone api {
            key {header.Authorization}
            events 100
            window 1m
        }
    }
}
```

**CORS Configuration** (verify in `backend/app/main.py`):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://chat.openai.com",
        "https://yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

## Docker Setup

### Project Structure

```
mindflow/
├── backend/
│   ├── app/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
├── docker-compose.yml
├── docker-compose.prod.yml
└── .env.example
```

### Backend Dockerfile

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY alembic.ini .
COPY migrations/ ./migrations/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run with Uvicorn (2 workers for 2GB RAM droplet)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

### Backend .dockerignore

Create `backend/.dockerignore`:

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env
.venv
pip-log.txt
pip-delete-this-directory.txt
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
.git
.gitignore
README.md
tests/
```

### Docker Compose (Local Development)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: mindflow-postgres
    environment:
      POSTGRES_DB: mindflow
      POSTGRES_USER: mindflow
      POSTGRES_PASSWORD: ${DB_PASSWORD:-password}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mindflow"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: mindflow-api
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://mindflow:${DB_PASSWORD:-password}@postgres:5432/mindflow
      SECRET_KEY: ${SECRET_KEY:-dev-secret-key}
      ENVIRONMENT: development
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  postgres_data:
```

### Docker Compose (Production)

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: mindflow-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: mindflow
      POSTGRES_USER: mindflow
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mindflow"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - mindflow

  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: mindflow-api
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql+asyncpg://mindflow:${DB_PASSWORD}@postgres:5432/mindflow
      SECRET_KEY: ${SECRET_KEY}
      ENVIRONMENT: production
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      SENTRY_DSN: ${SENTRY_DSN}
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - mindflow
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  caddy:
    image: caddy:2-alpine
    container_name: mindflow-caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - api
    networks:
      - mindflow

volumes:
  postgres_data:
  caddy_data:
  caddy_config:

networks:
  mindflow:
    driver: bridge
```

### Caddyfile (Reverse Proxy)

Create `Caddyfile`:

```
api.yourdomain.com {
    reverse_proxy api:8000

    encode gzip

    # CORS headers
    header {
        Access-Control-Allow-Origin https://yourdomain.com
        Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS"
        Access-Control-Allow-Headers "Authorization, Content-Type"
    }

    # Rate limiting (100 requests per minute per IP)
    rate_limit {
        zone dynamic {
            key {remote_host}
            events 100
            window 1m
        }
    }
}
```

### Test Locally

```bash
# Start services
docker-compose up --build

# Verify API
curl http://localhost:8000/health
# Expected: {"status": "ok"}

# Check logs
docker-compose logs -f api

# Stop services
docker-compose down
```

---

## DigitalOcean Droplet Setup

### Step 1: Create Droplet

```bash
# Login to DigitalOcean
doctl auth init
# Enter your API token

# Create SSH key (if you don't have one)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Upload SSH key to DigitalOcean
doctl compute ssh-key import mindflow-key --public-key-file ~/.ssh/id_ed25519.pub

# Get SSH key ID
doctl compute ssh-key list

# Create droplet ($12/month - 2GB RAM, 2 vCPU)
doctl compute droplet create mindflow-api \
  --size s-2vcpu-2gb \
  --image ubuntu-22-04-x64 \
  --region sfo3 \
  --ssh-keys YOUR_SSH_KEY_ID \
  --enable-monitoring \
  --enable-backups

# Get droplet IP
doctl compute droplet list
```

**Via Web UI** (Alternative):
1. Go to https://cloud.digitalocean.com
2. Create Droplets → New Droplet
3. **Image**: Ubuntu 22.04 LTS
4. **Plan**: Basic, Regular, $12/month (2GB RAM, 2 vCPU)
5. **Datacenter**: Closest to your users (e.g., San Francisco, New York)
6. **SSH Keys**: Add your public key
7. **Hostname**: mindflow-api
8. Click "Create Droplet"

### Step 2: Initial Server Setup

```bash
# SSH into droplet
ssh root@YOUR_DROPLET_IP

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Verify installations
docker --version
docker-compose --version

# Create non-root user
adduser mindflow
usermod -aG sudo mindflow
usermod -aG docker mindflow

# Setup firewall
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### Step 3: Deploy Application

```bash
# Switch to app user
su - mindflow

# Create app directory
mkdir -p ~/app
cd ~/app

# Clone repository (or use rsync to copy files)
# Option A: Git
git clone https://github.com/yourusername/mindflow.git .

# Option B: rsync from local machine (in local terminal)
rsync -avz --exclude 'venv' --exclude '__pycache__' \
  ./backend/ mindflow@YOUR_DROPLET_IP:~/app/backend/

rsync -avz docker-compose.prod.yml Caddyfile \
  mindflow@YOUR_DROPLET_IP:~/app/

# Back in droplet SSH session
# Create .env file
cat > .env << 'EOF'
DB_PASSWORD=$(openssl rand -hex 16)
SECRET_KEY=$(openssl rand -hex 32)
OPENAI_API_KEY=your_openai_key
SENTRY_DSN=your_sentry_dsn
EOF

# Source environment
source .env

# Build and start services
docker-compose -f docker-compose.prod.yml up -d --build

# Check services
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Step 4: Run Database Migrations

```bash
# Run migrations inside container
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# Verify database
docker-compose -f docker-compose.prod.yml exec postgres psql -U mindflow -d mindflow -c "\dt"
```

### Step 5: Configure Domain (Cloudflare)

1. **Add A Record** in Cloudflare DNS:
   ```
   Type: A
   Name: api
   Content: YOUR_DROPLET_IP
   Proxy: ON (orange cloud)
   TTL: Auto
   ```

2. **Update Caddyfile** on droplet:
   ```bash
   nano ~/app/Caddyfile
   # Change "api.yourdomain.com" to your actual domain

   # Restart Caddy
   docker-compose -f docker-compose.prod.yml restart caddy
   ```

3. **Verify HTTPS**:
   ```bash
   curl https://api.yourdomain.com/health
   ```

---

## Cloudflare Pages Setup

### Step 1: Prepare Frontend

**Frontend structure**:
```
frontend/
├── src/
│   ├── index.html
│   ├── main.ts
│   └── components/
├── public/
│   └── assets/
├── package.json
├── vite.config.ts
└── .env.production
```

**Configure API endpoint** (`frontend/.env.production`):
```bash
VITE_API_URL=https://api.yourdomain.com
```

**Update vite.config.ts**:
```typescript
import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['lit']
        }
      }
    }
  }
});
```

### Step 2: Deploy to Cloudflare Pages

**Via GitHub Integration** (Recommended):

1. Push code to GitHub:
   ```bash
   git add .
   git commit -m "Configure for Cloudflare Pages"
   git push origin main
   ```

2. Login to Cloudflare Dashboard → Pages → Create Project

3. Connect to Git:
   - Select your repository
   - Branch: `main`

4. Build settings:
   ```
   Framework preset: Vite
   Build command: npm run build
   Build output directory: dist
   Root directory: frontend
   ```

5. Environment variables:
   ```
   VITE_API_URL: https://api.yourdomain.com
   ```

6. Click "Save and Deploy"

**Via Direct Upload**:

```bash
# Build locally
cd frontend
npm run build

# Install Wrangler
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Deploy
wrangler pages deploy dist --project-name mindflow
```

### Step 3: Custom Domain

1. Cloudflare Pages → Your Project → Custom domains
2. Click "Set up a custom domain"
3. Enter: `yourdomain.com`
4. Cloudflare auto-configures DNS (if domain is on Cloudflare)
5. HTTPS is automatic

---

## Database Migration

### Initial Schema Setup

```bash
# SSH into droplet
ssh mindflow@YOUR_DROPLET_IP

# Run migrations
cd ~/app
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
```

### Creating Migrations

**Locally**:
```bash
# Make schema changes in backend/app/db/models.py

# Generate migration
cd backend
alembic revision --autogenerate -m "Add tags to tasks"

# Review migration file in migrations/versions/

# Commit and push
git add migrations/
git commit -m "Add tags migration"
git push origin main
```

**On Server**:
```bash
# Pull changes
git pull origin main

# Rebuild API container
docker-compose -f docker-compose.prod.yml up -d --build api

# Run migration
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
```

### Backup Strategy

**Automated Daily Backups**:

Create `backup.sh` on droplet:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/mindflow/backups"
mkdir -p $BACKUP_DIR

# Backup database
docker-compose -f /home/mindflow/app/docker-compose.prod.yml exec -T postgres \
  pg_dump -U mindflow mindflow > $BACKUP_DIR/mindflow_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "mindflow_*.sql" -mtime +7 -delete

echo "Backup completed: $DATE"
```

**Setup cron job**:
```bash
chmod +x backup.sh
crontab -e

# Add this line (daily at 2 AM)
0 2 * * * /home/mindflow/backup.sh >> /home/mindflow/backup.log 2>&1
```

---

## MCP Server Configuration

### What is MCP?

Model Context Protocol (MCP) is the interface that allows ChatGPT to interact with MindFlow. It exposes tools that ChatGPT can call.

### Step 1: Verify MCP Server Deployment

The MCP server is integrated into the FastAPI backend. Verify it's running:

```bash
# Test MCP tools endpoint
curl https://api.yourdomain.com/mcp/tools

# Expected response: List of available tools
# - get_tasks
# - create_task
# - update_task
# - complete_task
# - snooze_task
```

### Step 2: MCP Server Environment Variables

**Add to `.env` on server**:
```bash
# MCP Configuration
MCP_SERVER_NAME="MindFlow Task Manager"
MCP_SERVER_VERSION="1.0.0"
MCP_SERVER_DESCRIPTION="AI-powered task management with intelligent prioritization"

# MCP Tools Configuration
MCP_ENABLE_TASK_WIDGETS=true
MCP_MAX_TASKS_PER_REQUEST=50
```

### Step 3: Test MCP Tools

**Test each MCP tool**:

```bash
# Get tasks
curl -X POST https://api.yourdomain.com/mcp/tools/get_tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "pending"}'

# Create task
curl -X POST https://api.yourdomain.com/mcp/tools/create_task \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test task", "priority": 3}'

# Complete task
curl -X POST https://api.yourdomain.com/mcp/tools/complete_task \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task_id": "uuid-here"}'
```

---

## ChatGPT Apps SDK Integration

### Step 1: Register MindFlow with OpenAI

1. **Go to** https://platform.openai.com/apps
2. **Click** "Create App"
3. **Fill in details**:
   - Name: MindFlow Task Manager
   - Description: AI-powered task management with intelligent prioritization
   - Category: Productivity
   - Website: https://yourdomain.com

### Step 2: Configure OAuth 2.1

In the OpenAI Apps dashboard:

1. **OAuth Configuration**:
   ```
   Authorization URL: https://api.yourdomain.com/oauth/authorize
   Token URL: https://api.yourdomain.com/oauth/token
   Client ID: chatgpt_mindflow
   Client Secret: <from-oauth-client-registration>
   Scope: read write
   ```

2. **Redirect URIs**:
   ```
   https://chat.openai.com/aip/oauth/callback
   ```

3. **PKCE**: Enable (required for OAuth 2.1)

### Step 3: Configure MCP Tools

In the OpenAI Apps dashboard, add MCP tool definitions:

```json
{
  "name": "get_tasks",
  "description": "Get user's tasks filtered by status",
  "parameters": {
    "type": "object",
    "properties": {
      "status": {
        "type": "string",
        "enum": ["pending", "in_progress", "completed", "snoozed"],
        "description": "Filter tasks by status"
      }
    }
  }
}
```

**See** `backend/docs/CHATGPT-CONNECTION-GUIDE.md` for complete tool definitions.

### Step 4: Add Task Widget

Configure the TaskWidget component in OpenAI Apps dashboard:

```json
{
  "widget_type": "TaskCard",
  "render_url": "https://api.yourdomain.com/widgets/task",
  "actions": [
    {
      "type": "button",
      "label": "Complete",
      "action": "complete_task",
      "style": "primary"
    },
    {
      "type": "button",
      "label": "Snooze",
      "action": "snooze_task",
      "style": "secondary"
    }
  ]
}
```

### Step 5: Test ChatGPT Integration

1. **Open** https://chat.openai.com
2. **Enable** MindFlow app
3. **Test commands**:
   ```
   "Show me my pending tasks"
   "Create a task to review deployment docs"
   "What should I work on next?"
   "Complete task <task-name>"
   "Snooze task <task-name> until tomorrow"
   ```

4. **Verify**:
   - OAuth flow completes successfully
   - Tasks display in interactive widget
   - Complete/Snooze buttons work
   - Follow-up messages appear after actions

---

## Open Beta Launch Checklist

### Pre-Launch Testing (Complete all before inviting users)

#### 1. Infrastructure Health

- [ ] **DigitalOcean Droplet**: Verify droplet is running and healthy
  ```bash
  ssh mindflow@YOUR_DROPLET_IP
  docker-compose -f docker-compose.prod.yml ps
  ```

- [ ] **Database**: Test connectivity and verify migrations
  ```bash
  docker-compose -f docker-compose.prod.yml exec postgres psql -U mindflow -d mindflow -c "\dt"
  ```

- [ ] **API Health**: Verify all endpoints responding
  ```bash
  curl https://api.yourdomain.com/health
  # Expected: {"status": "healthy", "version": "4.1.0", "checks": {"database": "healthy"}}
  ```

#### 2. Security Verification

- [ ] **OAuth 2.1**: Test complete authorization flow
  - [ ] Authorization endpoint (`/oauth/authorize`)
  - [ ] Token endpoint (`/oauth/token`)
  - [ ] PKCE validation
  - [ ] Token refresh
  - [ ] Token rotation

- [ ] **HTTPS**: Verify SSL certificate
  ```bash
  curl -I https://api.yourdomain.com
  # Check for: 200 OK, Strict-Transport-Security header
  ```

- [ ] **CORS**: Test from ChatGPT origin
  ```bash
  curl -H "Origin: https://chat.openai.com" \
       -H "Access-Control-Request-Method: POST" \
       -X OPTIONS https://api.yourdomain.com/api/tasks
  ```

- [ ] **Rate Limiting**: Test rate limits
  ```bash
  for i in {1..110}; do curl https://api.yourdomain.com/api/tasks; done
  # Should get 429 after 100 requests
  ```

#### 3. ChatGPT Integration

- [ ] **MCP Tools**: Test all 5 tools via ChatGPT
  - [ ] `get_tasks` - List tasks
  - [ ] `create_task` - Create new task
  - [ ] `update_task` - Update existing task
  - [ ] `complete_task` - Mark task complete
  - [ ] `snooze_task` - Snooze task

- [ ] **Task Widget**: Verify interactive widget rendering
  - [ ] Widget displays task details correctly
  - [ ] Complete button works and shows follow-up message
  - [ ] Snooze button works with snooze duration selection

- [ ] **Error Handling**: Test error scenarios
  - [ ] Invalid task ID
  - [ ] Unauthorized access
  - [ ] Rate limit exceeded
  - [ ] Database connection failure

#### 4. Performance Testing

- [ ] **Load Test**: Simulate 50 concurrent users
  ```bash
  # Install hey (HTTP load testing tool)
  # https://github.com/rakyll/hey
  hey -n 1000 -c 50 -H "Authorization: Bearer $TOKEN" \
      https://api.yourdomain.com/api/tasks
  ```

- [ ] **Database Performance**: Check query performance
  ```sql
  -- Enable query logging
  ALTER DATABASE mindflow SET log_min_duration_statement = 100;

  -- Review slow queries after load test
  SELECT query, mean_exec_time, calls
  FROM pg_stat_statements
  ORDER BY mean_exec_time DESC
  LIMIT 10;
  ```

- [ ] **Memory Usage**: Monitor under load
  ```bash
  docker stats mindflow-api mindflow-postgres
  # API should stay under 500MB
  # Postgres should stay under 1GB
  ```

#### 5. Monitoring Setup

- [ ] **Sentry**: Verify error tracking
  - [ ] Test error capture: `raise Exception("Test error")`
  - [ ] Verify error appears in Sentry dashboard
  - [ ] Configure alert rules for critical errors

- [ ] **UptimeRobot**: Configure uptime monitoring
  - [ ] Monitor: https://api.yourdomain.com/health
  - [ ] Interval: 5 minutes
  - [ ] Alerts: Email + SMS for downtime

- [ ] **Log Aggregation**: Verify log collection
  ```bash
  docker-compose -f docker-compose.prod.yml logs --tail 100 api | grep ERROR
  ```

#### 6. Backup & Recovery

- [ ] **Database Backup**: Test backup creation
  ```bash
  ./backup.sh
  ls -lh ~/backups/
  # Should see today's backup file
  ```

- [ ] **Backup Restore**: Test restore process
  ```bash
  # Create test database
  docker-compose -f docker-compose.prod.yml exec postgres psql -U mindflow -c "CREATE DATABASE mindflow_test;"

  # Restore backup
  docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U mindflow -d mindflow_test < ~/backups/mindflow_20251102_020000.sql
  ```

- [ ] **Rollback Plan**: Document rollback procedure
  - [ ] Git tag current release: `git tag v1.0.0-beta`
  - [ ] Document how to revert to previous version
  - [ ] Test rollback on staging environment

### Beta User Onboarding

#### 1. Invite Beta Users (Start with 10 users)

**Email Template**:
```
Subject: You're invited to MindFlow Beta! 🚀

Hi [Name],

You're invited to try MindFlow - an AI-powered task manager that works inside ChatGPT.

Getting Started:
1. Open ChatGPT: https://chat.openai.com
2. Enable MindFlow app from the app store
3. Authorize MindFlow to access your tasks
4. Try: "Show me my pending tasks"

What to expect:
- Natural conversation with your task list
- AI-powered task suggestions
- Interactive task widgets
- Intelligent prioritization

We'd love your feedback! Join our beta Slack channel: [link]

Questions? Reply to this email or check our docs: https://yourdomain.com/docs

Happy task managing!
The MindFlow Team
```

#### 2. Beta User Support

- [ ] **Create Slack/Discord channel** for beta users
- [ ] **Setup feedback form**: Google Forms or Typeform
- [ ] **Monitor first-user experience**: Watch logs during first 10 signups
- [ ] **Response SLA**: Respond to beta user questions within 2 hours

#### 3. Success Metrics

Track these metrics during beta:
- **Signups**: Target 100 users in first 30 days
- **Activation**: % users who create first task (target: 80%)
- **Retention**: % users active after 7 days (target: 60%)
- **Engagement**: Average tasks created per user (target: 10)
- **NPS Score**: Net Promoter Score (target: 50+)
- **Bug Rate**: Critical bugs per 100 users (target: <2)

### Post-Launch Monitoring

#### First 24 Hours

- [ ] **Hour 1-4**: Monitor every 30 minutes
  - Check error rates in Sentry
  - Review API response times
  - Watch for OAuth issues

- [ ] **Hour 5-24**: Monitor every 2 hours
  - Check database performance
  - Review user feedback
  - Fix critical issues immediately

#### First Week

- [ ] **Daily health check**:
  ```bash
  # API health
  curl https://api.yourdomain.com/health

  # Database connections
  docker-compose -f docker-compose.prod.yml exec postgres psql -U mindflow -d mindflow -c "SELECT count(*) FROM pg_stat_activity;"

  # Error rate
  docker-compose -f docker-compose.prod.yml logs api | grep ERROR | wc -l
  ```

- [ ] **User feedback review**: Daily review of feedback form responses
- [ ] **Performance review**: Check response times and database queries
- [ ] **Feature requests**: Document and prioritize user requests

### Scaling Plan (When to scale up)

**Scale from $12 to $24 droplet when**:
- API response time > 1s (p95)
- Memory usage > 80% consistently
- More than 500 active users
- Database connections > 80% of pool

**Upgrade to**:
- DigitalOcean: 4GB RAM, 2 vCPU ($24/month)
- Adjust worker count in Dockerfile: `--workers 4`
- Increase connection pool: `pool_size=10, max_overflow=10`

---

## Environment Configuration

### Production Environment Variables

Create `.env` on droplet:

```bash
# Database
DB_PASSWORD=<generate-with-openssl-rand-hex-16>

# Security
SECRET_KEY=<generate-with-openssl-rand-hex-32>

# OpenAI (optional)
OPENAI_API_KEY=sk-...

# Sentry (error tracking)
SENTRY_DSN=https://...@sentry.io/...

# Environment
ENVIRONMENT=production
```

**Generate secrets**:
```bash
# Database password
openssl rand -hex 16

# JWT secret
openssl rand -hex 32
```

### Updating Environment Variables

```bash
# Edit .env
nano ~/app/.env

# Restart services to apply
cd ~/app
docker-compose -f docker-compose.prod.yml restart api
```

---

## Monitoring & Logging

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f api

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail 100 api
```

### Disk Usage Monitoring

```bash
# Check disk space
df -h

# Check Docker disk usage
docker system df

# Clean up old images/volumes
docker system prune -a
```

### Setup Sentry Error Tracking

1. Sign up at https://sentry.io
2. Create new project (FastAPI)
3. Get DSN
4. Add to `.env`:
   ```bash
   SENTRY_DSN=https://...@o1234.ingest.sentry.io/4567
   ```
5. Restart API:
   ```bash
   docker-compose -f docker-compose.prod.yml restart api
   ```

### Uptime Monitoring

**UptimeRobot** (Free):
1. Sign up: https://uptimerobot.com
2. Add monitor:
   - Type: HTTP(s)
   - URL: `https://api.yourdomain.com/health`
   - Interval: 5 minutes
3. Configure alerts (email/SMS)

---

## CI/CD with GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to DigitalOcean

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v --cov=app

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3

      - name: Deploy to DigitalOcean
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.DROPLET_IP }}
          username: mindflow
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd ~/app
            git pull origin main
            docker-compose -f docker-compose.prod.yml up -d --build
            docker-compose -f docker-compose.prod.yml exec -T api alembic upgrade head
```

**Setup GitHub Secrets**:
1. GitHub repo → Settings → Secrets → Actions
2. Add secrets:
   - `DROPLET_IP`: Your droplet IP address
   - `SSH_PRIVATE_KEY`: Your private SSH key (`cat ~/.ssh/id_ed25519`)

---

## Troubleshooting

### Issue: API Container Won't Start

**Check logs**:
```bash
docker-compose -f docker-compose.prod.yml logs api
```

**Common causes**:
1. Database not ready
2. Missing environment variables
3. Port conflict

**Fix**:
```bash
# Check environment
docker-compose -f docker-compose.prod.yml config

# Rebuild containers
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

### Issue: Database Connection Failed

**Test connection**:
```bash
docker-compose -f docker-compose.prod.yml exec postgres psql -U mindflow -d mindflow
```

**Check network**:
```bash
docker network ls
docker network inspect app_mindflow
```

### Issue: Out of Disk Space

**Check usage**:
```bash
df -h
docker system df
```

**Clean up**:
```bash
# Remove unused Docker objects
docker system prune -a --volumes

# Remove old backups
find ~/backups -name "*.sql" -mtime +7 -delete
```

### Issue: SSL Certificate Not Working

**Check Caddy logs**:
```bash
docker-compose -f docker-compose.prod.yml logs caddy
```

**Verify DNS**:
```bash
dig api.yourdomain.com
```

**Force certificate renewal**:
```bash
docker-compose -f docker-compose.prod.yml restart caddy
```

---

## Performance Optimization

### Enable PostgreSQL Connection Pooling

Update `backend/app/db/database.py`:

```python
engine = create_async_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### Enable Response Compression

Already handled by Caddy (`encode gzip` in Caddyfile)

### Optimize Docker Images

```bash
# Multi-stage build for smaller images
# See Dockerfile in this guide

# Check image size
docker images | grep mindflow
```

---

## Security Checklist

- [x] Firewall configured (UFW)
- [x] Non-root user for app
- [x] HTTPS enabled (Caddy auto-cert)
- [x] Database not exposed publicly
- [x] Secrets in .env (not in git)
- [x] Regular security updates (`apt update && apt upgrade`)
- [x] SSH key authentication (disable password auth)
- [x] Rate limiting (Caddy)
- [x] CORS restricted to known origins

**Harden SSH**:
```bash
sudo nano /etc/ssh/sshd_config

# Disable password auth
PasswordAuthentication no
PermitRootLogin no

sudo systemctl restart sshd
```

---

## Cost Summary

| Item | Cost |
|------|------|
| DigitalOcean Droplet (2GB) | $12/month |
| Cloudflare Pages | FREE |
| Domain | $12/year (~$1/month) |
| Backups (DigitalOcean) | $2.40/month (optional) |
| **Total** | **~$13-15/month** |

**Savings vs Original Plan**: ~$25/month (60% cheaper than Fly.io + Supabase)

---

## Next Steps

- See **IMPLEMENTATION.md** for backend code
- See **ARCHITECTURE.md** for system design
- See **TDD-PLAN.md** for test-driven development guide (next document)

---

**Version**: 2.0.0
**Last Updated**: 2025-10-30
**Optimized For**: $10-12 DigitalOcean droplet + Cloudflare Pages
