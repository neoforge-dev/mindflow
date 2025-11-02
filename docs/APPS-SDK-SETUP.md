# ChatGPT Apps SDK - Developer Quick Start

**Last Updated**: 2025-11-02
**Target Audience**: Developers building or extending the ChatGPT Apps SDK integration
**Time to Complete**: 30 minutes

---

## 🎯 Overview

This guide walks you through the complete ChatGPT Apps SDK integration:
- MCP (Model Context Protocol) server setup
- Interactive React widget development
- OAuth 2.1 authentication flow
- Local development and testing
- Production deployment

### What You'll Build

By following this guide, you'll understand how MindFlow's ChatGPT integration works:

1. **MCP Server**: Exposes tools (`get_next_task`, `complete_task`, `snooze_task`)
2. **TaskWidget**: Interactive React component rendered inline in ChatGPT
3. **OAuth Flow**: Secure user authentication with token rotation
4. **API Integration**: FastAPI backend connected to ChatGPT

---

## 📋 Prerequisites

### Required
- **Python 3.11+** with `uv` package manager
- **Node.js 18+** with `npm`
- **PostgreSQL 15** (Docker or local)
- **ChatGPT Plus or Team** account with Apps SDK access
- **ngrok** (for local development) or production HTTPS domain

### Optional
- **VS Code** with Python and TypeScript extensions
- **Postman** or `curl` for API testing
- **Docker Desktop** for containerized database

---

## 🚀 Part 1: Local Development Setup (10 minutes)

### Step 1: Clone and Install Dependencies

```bash
# Clone repository
git clone https://github.com/yourusername/mindflow.git
cd mindflow

# Backend setup
cd backend
uv sync                    # Install Python dependencies
make db-up                 # Start PostgreSQL test database

# Frontend setup
cd ../frontend
npm install                # Install Node.js dependencies
```

### Step 2: Environment Configuration

Create `backend/.env`:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:54320/mindflow_test

# OAuth 2.1 Configuration
OAUTH_ISSUER=http://localhost:8000
API_BASE_URL=http://localhost:8000

# JWT Keys (auto-generated on first run)
JWT_PRIVATE_KEY=auto-generated
JWT_PUBLIC_KEY=auto-generated

# Environment
ENVIRONMENT=development
DEBUG=true
```

### Step 3: Run All Tests

```bash
# Backend tests (45 MCP server tests)
cd backend
make test
# Expected: 45/45 tests passing

# Frontend tests (52 component tests)
cd ../frontend
npm test
# Expected: 52/52 tests passing
```

---

## 🏗️ Part 2: Architecture Overview (5 minutes)

### Component Interaction Flow

```
ChatGPT User
    ↓
    ↓ "What should I work on?"
    ↓
ChatGPT (calls MCP tool)
    ↓
    ↓ POST /mcp with tool_name="get_next_task"
    ↓
MCP Server (FastMCP)
    ↓
    ↓ Calls tasks_tool.get_next_task()
    ↓
FastAPI Backend
    ↓
    ↓ SELECT * FROM tasks ORDER BY ai_score DESC
    ↓
PostgreSQL Database
    ↓
    ↓ Returns top task
    ↓
TaskWidget (React)
    ↓
    ↓ Renders inline in ChatGPT with Complete/Snooze buttons
    ↓
User clicks "Complete Task"
    ↓
    ↓ window.openai.callTool({name: "complete_task", arguments: {task_id}})
    ↓
MCP Server → FastAPI → Database (status='completed')
    ↓
    ↓ window.openai.sendFollowUpMessage("Task completed! What's next?")
    ↓
ChatGPT responds with next task
```

### Key Files

```
backend/
├── mcp_server/
│   ├── main.py                  # FastMCP server definition
│   ├── tools/
│   │   └── tasks.py             # get_next_task, complete_task, snooze_task
│   ├── component_loader.py      # React widget embedding
│   ├── renderer.py              # Component rendering
│   ├── auth.py                  # JWT token validation
│   └── assets/
│       └── taskwidget.js        # Compiled React widget (9.2kb)
├── app/
│   ├── api/
│   │   └── tasks.py             # REST API endpoints
│   └── oauth/
│       └── routes.py            # OAuth 2.1 authorization + token

frontend/
├── src/
│   ├── components/
│   │   └── TaskWidget.tsx       # Interactive task component
│   ├── AppsSDK.ts               # window.openai API wrapper
│   └── types/
│       └── openai.ts            # TypeScript definitions
└── dist/
    └── index.js                 # Production bundle → backend/mcp_server/assets/
```

---

## 💻 Part 3: Local Development Workflow (10 minutes)

### Terminal 1: Backend Server

```bash
cd backend
make run
# Server starts on http://localhost:8000

# Endpoints available:
# - http://localhost:8000/health
# - http://localhost:8000/mcp (MCP server)
# - http://localhost:8000/.well-known/oauth-authorization-server
# - http://localhost:8000/docs (FastAPI documentation)
```

### Terminal 2: Frontend Development

```bash
cd frontend
npm run dev
# Vite dev server on http://localhost:5173

# File watching enabled - changes auto-rebuild
```

### Terminal 3: ngrok (for ChatGPT connection)

```bash
ngrok http 8000
# Note your public URL: https://abc123.ngrok.io

# Update backend/.env:
export API_BASE_URL="https://abc123.ngrok.io"
export OAUTH_ISSUER="https://abc123.ngrok.io"

# Restart backend server (Terminal 1)
```

### Testing Changes

```bash
# 1. Modify component
code frontend/src/components/TaskWidget.tsx

# 2. Build for production
cd frontend
npm run build

# 3. Copy to backend assets
cp dist/index.js ../backend/mcp_server/assets/taskwidget.js

# 4. Restart backend (Terminal 1)
# MCP server will serve updated component

# 5. Test in ChatGPT
# Refresh ChatGPT conversation to load new widget
```

---

## 🧪 Part 4: Testing Guide (5 minutes)

### Backend Testing

```bash
cd backend

# Run all MCP tests
make test

# Run specific test file
uv run pytest backend/tests/mcp/test_tasks_tool.py -v

# Test with coverage
make test-coverage

# Expected output:
# ✅ 45 tests passing
# ✅ 100% coverage for mcp_server/ module
```

### Frontend Testing

```bash
cd frontend

# Run all tests
npm test

# Run specific test
npm test TaskWidget.test.tsx

# Run with coverage
npm run test:coverage

# Expected output:
# ✅ 52 tests passing (24 SDK + 28 Widget tests)
# ✅ 100% coverage for src/components/
```

### Manual Testing with ChatGPT

1. **Connect MCP Server** (see [CHATGPT-CONNECTION-GUIDE.md](../backend/docs/CHATGPT-CONNECTION-GUIDE.md))

2. **Test Commands**:
```
User: "What should I work on?"
Expected: TaskWidget renders with task, AI score, Complete/Snooze buttons

User: [Clicks "Complete Task"]
Expected: Task marked complete, follow-up message sent, new task shown

User: [Clicks "Snooze 3h"]
Expected: Task snoozed, follow-up message sent, next task shown
```

3. **Test Error Handling**:
```
User: "What should I work on?"
Backend: Returns 500 error
Expected: Error boundary catches, user-friendly message displayed
```

---

## 🔧 Part 5: Common Development Tasks

### Add a New MCP Tool

1. **Define tool in `backend/mcp_server/main.py`**:

```python
@mcp.tool(
    name="my_new_tool",
    description="""Use this tool when the user wants to...

    WHEN TO USE:
    - User prompt pattern 1
    - User prompt pattern 2

    DO NOT USE:
    - When user wants something else

    RETURNS:
    Description of what this tool returns""",
    readOnlyHint=True  # If tool doesn't modify data
)
async def my_new_tool(
    arguments: dict[str, Any]
) -> str:
    # Extract arguments
    param = arguments.get("param")

    # Call implementation
    result = await my_tool_implementation(param)

    # Return JSON response
    return json.dumps({
        "success": True,
        "data": result
    })
```

2. **Implement logic in `backend/mcp_server/tools/tasks.py`**:

```python
async def my_tool_implementation(param: str) -> dict[str, Any]:
    """Implementation logic"""
    # ... your code here
    return {"result": "data"}
```

3. **Add tests in `backend/tests/mcp/test_my_tool.py`**:

```python
import pytest

async def test_my_tool_success(mcp_client):
    response = await mcp_client.call_tool(
        "my_new_tool",
        {"param": "value"}
    )
    assert response["success"] is True
```

4. **Run tests**:
```bash
make test
# Ensure all tests pass before committing
```

### Modify TaskWidget UI

1. **Edit component** (`frontend/src/components/TaskWidget.tsx`):

```typescript
// Add new button
<button
  onClick={handleNewAction}
  disabled={isLoading}
  style={{
    flex: '1 1 auto',
    minWidth: '120px',
    padding: '10px 16px',
    backgroundColor: colors.accent,
    color: '#ffffff',
    border: 'none',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: 600,
    cursor: isLoading ? 'not-allowed' : 'pointer',
  }}
>
  {isLoading ? 'Processing...' : '✨ New Action'}
</button>
```

2. **Test locally**:
```bash
npm run dev
# Test in Vite dev server at http://localhost:5173
```

3. **Build and deploy**:
```bash
npm run build
cp dist/index.js ../backend/mcp_server/assets/taskwidget.js
```

4. **Test in ChatGPT** with ngrok connection

### Update OAuth Configuration

1. **Edit `backend/app/config.py`**:

```python
# Token lifetimes
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Default: 60
REFRESH_TOKEN_EXPIRE_DAYS = 90   # Default: 90

# Allowed redirect URIs
ALLOWED_REDIRECT_URIS = [
    "https://chatgpt.com/auth/callback",
    "https://your-custom-domain.com/callback"
]
```

2. **Regenerate keys** (if needed):
```bash
cd backend
uv run python -c "from app.oauth.keys import generate_rsa_keys; generate_rsa_keys()"
```

3. **Restart server** and re-authorize in ChatGPT

---

## 🚀 Part 6: Production Deployment

### Prerequisites
- Production domain with SSL certificate
- PostgreSQL database (managed or self-hosted)
- Environment variables configured

### Deployment Steps

1. **Build frontend**:
```bash
cd frontend
npm run build
cp dist/index.js ../backend/mcp_server/assets/taskwidget.js
```

2. **Update environment variables**:
```bash
export MINDFLOW_DOMAIN="tasks.yourdomain.com"
export API_BASE_URL="https://$MINDFLOW_DOMAIN"
export OAUTH_ISSUER="https://$MINDFLOW_DOMAIN"
export DATABASE_URL="postgresql+asyncpg://user:pass@prod-host:5432/mindflow"
export ENVIRONMENT="production"
export DEBUG="false"
```

3. **Deploy backend**:
```bash
cd backend
make deploy
# Or follow your deployment process (Docker, systemd, etc.)
```

4. **Verify deployment**:
```bash
curl https://$MINDFLOW_DOMAIN/health
# Expected: {"status": "healthy"}

curl https://$MINDFLOW_DOMAIN/.well-known/oauth-authorization-server
# Expected: OAuth discovery document
```

5. **Connect ChatGPT** using [CHATGPT-CONNECTION-GUIDE.md](../backend/docs/CHATGPT-CONNECTION-GUIDE.md)

---

## 🐛 Troubleshooting

### "MCP server not responding"

**Cause**: Backend not running or not accessible

**Fix**:
```bash
# Check backend is running
curl http://localhost:8000/health

# Check logs
cd backend && make logs

# Restart backend
make run
```

### "Widget not rendering"

**Cause**: Bundle not copied to assets or malformed

**Fix**:
```bash
# Verify bundle exists
ls -lh backend/mcp_server/assets/taskwidget.js
# Should be ~9.2kb

# Rebuild
cd frontend
npm run build
cp dist/index.js ../backend/mcp_server/assets/taskwidget.js

# Restart backend
cd ../backend && make run
```

### "OAuth authorization failed"

**Cause**: Mismatch in OAuth configuration

**Fix**:
```bash
# Verify issuer matches domain
echo $OAUTH_ISSUER
echo $API_BASE_URL
# Should match your actual domain

# Check discovery endpoint
curl $API_BASE_URL/.well-known/oauth-authorization-server
```

### "Tests failing"

**Cause**: Dependencies out of sync or database issues

**Fix**:
```bash
# Reinstall dependencies
cd backend && uv sync
cd ../frontend && npm install

# Reset database
cd backend && make db-reset

# Run tests individually
cd backend && uv run pytest tests/mcp/ -v
cd ../frontend && npm test
```

---

## 📚 Additional Resources

### Documentation
- [ChatGPT Connection Guide](../backend/docs/CHATGPT-CONNECTION-GUIDE.md) - Production deployment
- [MCP Server Architecture](../backend/docs/MCP_SERVER.md) - Deep dive into MCP implementation
- [Apps SDK Review](../backend/docs/APPS-SDK-REVIEW.md) - OpenAI best practices analysis
- [Phase 9B Validation](../backend/docs/PHASE-9B-VALIDATION.md) - Complete test results

### External Resources
- [OpenAI Apps SDK Documentation](https://developers.openai.com/apps-sdk)
- [Model Context Protocol Spec](https://modelcontextprotocol.io)
- [OAuth 2.1 Specification](https://oauth.net/2.1/)
- [FastMCP Library](https://github.com/jlowin/fastmcp)

### Support Channels
- GitHub Issues: [Project Issues](https://github.com/yourorg/mindflow/issues)
- Documentation: [Main README](../docs/README.md)

---

## ✅ Quick Checklist

Use this checklist to verify your setup:

- [ ] Backend running on http://localhost:8000
- [ ] PostgreSQL database accessible
- [ ] Frontend building without errors
- [ ] All 97 tests passing (45 backend + 52 frontend)
- [ ] TaskWidget bundle exists (~9.2kb)
- [ ] ngrok tunnel active for local ChatGPT testing
- [ ] OAuth discovery endpoint responding
- [ ] MCP tools visible in `/mcp/tools` endpoint
- [ ] Can connect and authorize in ChatGPT
- [ ] TaskWidget renders with task data
- [ ] Complete and Snooze buttons functional

---

## 🎓 Next Steps

Once your local environment is working:

1. **Explore the Codebase**
   - Read through `backend/mcp_server/main.py` to understand tool definitions
   - Study `frontend/src/components/TaskWidget.tsx` for UI patterns
   - Review `backend/tests/mcp/` for testing approaches

2. **Make Your First Change**
   - Add a new button to TaskWidget
   - Create a new MCP tool
   - Customize OAuth flow

3. **Deploy to Production**
   - Follow [CHATGPT-CONNECTION-GUIDE.md](../backend/docs/CHATGPT-CONNECTION-GUIDE.md)
   - Set up monitoring and logging
   - Configure production database

4. **Share Feedback**
   - Report issues on GitHub
   - Suggest improvements to documentation
   - Contribute test cases

---

**Happy Building!** 🚀

For questions or issues, see [Support Channels](#additional-resources) above.
