# ChatGPT Apps SDK Integration Guide

This document explains how MindFlow integrates with ChatGPT Apps SDK to provide interactive task management widgets directly in ChatGPT conversations.

## Architecture Overview

```
ChatGPT Chat Interface
    ↓
  [User: "What should I work on?"]
    ↓
MCP Server (FastMCP)
    ├─ Authenticates via OAuth 2.1 Bearer token
    ├─ Calls get_next_task tool
    └─ Embeds React component in response
    ↓
FastAPI Backend
    ├─ Validates user authentication
    ├─ Runs AI scoring algorithm
    └─ Returns best task with reasoning
    ↓
React TaskCard Component
    ├─ Accesses window.openai API
    ├─ Renders with ChatGPT theme
    └─ Displays interactive task widget
```

## Components

### 1. Frontend (React + TypeScript)

**Location:** `frontend/src/`

#### Core Files
- `components/TaskCard.tsx` - Main task display component
- `hooks/useOpenAI.ts` - Hook to access ChatGPT's window.openai API
- `hooks/useWidgetState.ts` - Hook for widget state persistence
- `types/openai.ts` - TypeScript definitions for window.openai

#### Build System
- `build.js` - esbuild configuration for ESM bundle
- `build-and-deploy.sh` - Build and deploy to backend assets
- Output: `dist/index.js` (6.9kb minified)

### 2. Backend MCP Server (Python + FastMCP)

**Location:** `backend/mcp_server/`

#### Core Files
- `main.py` - FastMCP server with get_next_task tool
- `tools/tasks.py` - Task retrieval and component embedding
- `component_loader.py` - Component loading and _meta field injection
- `assets/taskcard.js` - Deployed React component code

### 3. Integration Tests

**Location:** `backend/tests/mcp_server/`

- `test_component_loader.py` - Component loading/embedding tests (10 tests)
- `test_tasks_tool.py` - MCP tool integration tests (7 tests)
- `test_auth.py` - OAuth token verification tests (9 tests)

**Total:** 26 tests, all passing ✅

## How It Works

### 1. User Interaction Flow

```typescript
// User in ChatGPT: "What should I work on?"

// ChatGPT calls MCP tool
get_next_task({
  authorization: "Bearer eyJhbGc..."
})

// MCP server response
{
  "task": { /* task data */ },
  "score": 8.5,
  "reasoning": { /* AI reasoning */ },
  "_meta": {
    "openai/outputTemplate": "/* React component code */",
    "openai/displayMode": "inline",
    "openai/widgetId": "task-550e8400-..."
  }
}

// ChatGPT renders the React component
<TaskCard /> // Displays interactive widget
```

### 2. Component Rendering

The TaskCard component:
1. Checks for `window.openai` (ChatGPT environment)
2. Gets task data from `window.openai.toolOutput`
3. Uses ChatGPT's theme (`window.openai.theme`)
4. Renders with system fonts and colors (Apps SDK compliant)
5. Falls back to props for standalone mode

### 3. Component Embedding

```python
# backend/mcp_server/tools/tasks.py

async def get_best_task(authorization: str) -> dict:
    # Get task from backend
    result = await _call_api_with_retry(...)

    # Embed React component
    return embed_component(
        data=result,
        component_name="taskcard",
        display_mode="inline",
    )
```

The `embed_component` function:
1. Loads compiled React code from `assets/taskcard.js`
2. Adds `_meta` field with component template
3. Sets display mode (inline/carousel/fullscreen)
4. Generates unique widget ID for state persistence

## Development Workflow

### Building the Frontend

```bash
cd frontend

# Install dependencies
npm install

# Build only
npm run build

# Build and deploy to backend
npm run deploy

# Watch mode for development
npm run dev

# Type checking
npm run typecheck
```

### Running the Backend

```bash
cd backend

# Install dependencies
uv sync

# Run FastAPI backend (port 8000)
uv run python -m mindflow.main

# Run MCP server (port 8001)
uv run fastmcp run mcp_server.main:mcp

# Run tests
uv run pytest tests/mcp_server/ -v
```

### Full Integration Test

1. Start backend: `cd backend && make run`
2. Build frontend: `cd frontend && npm run deploy`
3. Configure ChatGPT MCP integration
4. Test in ChatGPT: "What should I work on?"

## ChatGPT Apps SDK Compliance

### ✅ Implemented Features

1. **System Fonts & Colors**
   - Uses `-apple-system, BlinkMacSystemFont, ...`
   - No custom fonts or external CSS
   - Semantic color system for light/dark modes

2. **Dark Mode Support**
   - Detects `window.openai.theme`
   - Falls back to `prefers-color-scheme`
   - Fully responsive color palettes

3. **Accessibility**
   - ARIA labels on all interactive elements
   - Keyboard navigation support
   - Semantic HTML structure

4. **Component Embedding**
   - React component via `_meta.openai/outputTemplate`
   - Display mode support (inline/carousel/fullscreen)
   - Widget state persistence via `window.openai.setWidgetState()`

5. **OAuth 2.1 Authentication**
   - PKCE flow with SHA-256
   - JWT tokens with proper audience validation
   - Bearer token verification in MCP server

### 📋 Future Enhancements

1. **Carousel Mode** - Swipeable task cards
2. **Fullscreen Mode** - Dedicated task focus view
3. **Additional MCP Tools**
   - `update_task_status`
   - `snooze_task`
   - `get_task_details`
4. **Widget Interactions**
   - Mark complete button
   - Snooze action
   - Quick edit functionality

## File Structure

```
mindflow/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── TaskCard.tsx          # Main component
│   │   ├── hooks/
│   │   │   ├── useOpenAI.ts          # ChatGPT API hook
│   │   │   └── useWidgetState.ts     # State persistence
│   │   ├── types/
│   │   │   ├── Task.ts               # Task type definitions
│   │   │   └── openai.ts             # window.openai types
│   │   ├── utils/
│   │   │   ├── dateFormat.ts         # Date formatting
│   │   │   └── priorityColors.ts     # Priority color schemes
│   │   └── index.tsx                 # Entry point
│   ├── build.js                      # esbuild config
│   ├── build-and-deploy.sh           # Build script
│   ├── package.json
│   └── tsconfig.json
├── backend/
│   ├── mcp_server/
│   │   ├── assets/
│   │   │   └── taskcard.js           # Deployed React component
│   │   ├── tools/
│   │   │   └── tasks.py              # Task tools
│   │   ├── auth.py                   # OAuth verification
│   │   ├── component_loader.py       # Component embedding
│   │   ├── config.py                 # MCP config
│   │   └── main.py                   # FastMCP server
│   └── tests/
│       └── mcp_server/
│           ├── test_auth.py          # OAuth tests
│           ├── test_component_loader.py  # Component tests
│           └── test_tasks_tool.py    # Tool integration tests
└── docs/
    ├── APPS-SDK-STATUS.md            # Detailed status report
    └── CHATGPT-APPS-SDK-INTEGRATION.md  # This file
```

## Testing

### Frontend Tests

```bash
cd frontend

# Type checking
npm run typecheck
```

### Backend Tests

```bash
cd backend

# All MCP tests
uv run pytest tests/mcp_server/ -v

# Component loader tests only
uv run pytest tests/mcp_server/test_component_loader.py -v

# Task tool tests only
uv run pytest tests/mcp_server/test_tasks_tool.py -v

# With coverage
uv run pytest tests/mcp_server/ -v --cov=mcp_server
```

**Current Test Status:**
- ✅ 26 tests passing
- ✅ 100% coverage of MCP server modules
- ✅ Component loading and caching
- ✅ _meta field embedding
- ✅ OAuth token verification

## Troubleshooting

### Component Not Found Error

```
FileNotFoundError: Component file not found: .../assets/taskcard.js
Make sure to build the frontend first: cd frontend && npm run build
```

**Solution:**
```bash
cd frontend
npm run deploy
```

### window.openai Not Available

The component works in both ChatGPT and standalone modes:
- **ChatGPT:** Uses `window.openai` for data and theme
- **Standalone:** Uses props and system preferences

### Theme Not Updating

Clear the component cache in development:
```python
from mcp_server.component_loader import clear_component_cache
clear_component_cache()
```

### OAuth Token Verification Failed

Check:
1. Token is valid JWT format
2. Token has correct audience claim
3. Token hasn't expired
4. Environment variables are set correctly

## Performance

### Frontend Bundle
- **Size:** 6.9kb minified
- **Load Time:** <10ms
- **Dependencies:** React (peer dependency)

### Backend Response
- **Token Verification:** <5ms
- **API Call:** <100ms (with caching)
- **Component Loading:** <1ms (cached)
- **Total Response Time:** <110ms

### Caching Strategy
- Component code cached in memory
- JWT public keys cached (1 hour TTL)
- No database queries for component rendering

## Security

### OAuth 2.1 Best Practices
- ✅ PKCE required for all flows
- ✅ SHA-256 code challenge method
- ✅ Short-lived access tokens (1 hour)
- ✅ Secure token verification
- ✅ Audience claim validation

### Component Security
- ✅ No eval() or Function() usage
- ✅ No inline scripts
- ✅ CSP-compatible rendering
- ✅ XSS prevention via React
- ✅ No external resource loading

## Next Steps

1. **Deploy to Production**
   - Configure MCP server URL in ChatGPT
   - Set up OAuth client credentials
   - Test end-to-end flow

2. **Add More Tools**
   - Task completion
   - Task snoozing
   - Task editing

3. **Enhanced UI**
   - Carousel mode implementation
   - Fullscreen task focus view
   - Interactive actions (complete, snooze)

4. **Monitoring**
   - MCP server metrics
   - Component render tracking
   - Error reporting

## Resources

- [ChatGPT Apps SDK Documentation](https://platform.openai.com/docs/chatgpt-apps)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [OAuth 2.1 Specification](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1)
- [MindFlow Apps SDK Status](./APPS-SDK-STATUS.md)

---

**Status:** ✅ Integration Complete (2025-01-02)
**Tests:** 26/26 passing
**Bundle Size:** 6.9kb
**Ready for:** ChatGPT Testing
