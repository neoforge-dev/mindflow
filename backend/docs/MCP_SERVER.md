# MindFlow MCP Server

## Overview

The MindFlow MCP (Model Context Protocol) Server provides AI-powered task management tools for ChatGPT via the Apps SDK. It enables ChatGPT to access and recommend tasks based on intelligent scoring algorithms.

## Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌──────────────────┐
│   ChatGPT App   │ ─────▶  │   MCP Server    │ ─────▶  │  FastAPI Backend │
│   (Apps SDK)    │  OAuth  │   (Port 8001)   │   JWT   │   (Port 8000)    │
└─────────────────┘         └─────────────────┘         └──────────────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │  OAuth Token    │
                            │  Verification   │
                            │  (RS256/JWT)    │
                            └─────────────────┘
```

## Features

- **OAuth 2.1 Authentication**: Secure JWT token verification using RS256 asymmetric signatures
- **AI-Powered Task Scoring**: Intelligent task recommendations based on multiple factors
- **Exponential Backoff Retry**: Automatic retry with exponential backoff for network errors
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Structured Logging**: Detailed logging for monitoring and debugging

## Installation

### Prerequisites

- Python 3.11+
- FastAPI backend running on port 8000
- OAuth keys generated (see OAuth setup below)

### Install Dependencies

```bash
make install-dev
# or
uv sync
```

## Configuration

The MCP server is configured via environment variables (`.env` file):

```env
# MCP Server Settings
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8001

# FastAPI Backend
API_BASE_URL=http://localhost:8000

# JWT Settings (must match FastAPI backend)
JWT_PUBLIC_KEY_PATH=app/oauth/keys/public_key.pem
OAUTH_ISSUER=https://mindflow.example.com
JWT_AUDIENCE=mindflow-api

# Rate Limiting
MAX_REQUESTS_PER_MINUTE=60

# Retry Settings
MAX_RETRIES=3
RETRY_BACKOFF_FACTOR=2.0
RETRY_BASE_DELAY=1.0
```

## Running the MCP Server

### Development Mode

```bash
make mcp-server
```

### Manual Start

```bash
uv run fastmcp run mcp_server.main:mcp --port 8001 --host 0.0.0.0
```

### Production Mode

For production, use a process manager like systemd or supervisor:

```bash
# Using systemd (example)
sudo systemctl start mindflow-mcp
```

## Available Tools

### 1. get_next_task

Get the best task to work on right now based on AI scoring.

**Parameters:**
- `authorization` (string, required): OAuth Bearer token

**Returns:**
```json
{
  "task": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Complete project documentation",
    "description": "Write comprehensive docs for the new feature",
    "priority": 4,
    "due_date": "2024-02-01T10:00:00Z",
    "effort_estimate_minutes": 120,
    "status": "pending",
    "created_at": "2024-01-15T08:00:00Z",
    "updated_at": "2024-01-15T08:00:00Z"
  },
  "score": 8.5,
  "reasoning": {
    "deadline_urgency": 2.5,
    "priority_score": 40,
    "effort_bonus": 10,
    "total_score": 8.5,
    "recommendation": "High priority task worth focusing on"
  }
}
```

**Example Usage (ChatGPT):**
```
User: "What should I work on next?"
ChatGPT: [Calls get_next_task tool]
ChatGPT: "You should work on 'Complete project documentation' (Priority 4,
          Due Feb 1). This is a high priority task worth focusing on."
```

### 2. health_check

Check if the MCP server is healthy and can connect to the backend.

**Parameters:** None

**Returns:**
```json
{
  "status": "healthy",
  "server": "MindFlow MCP Server",
  "version": "1.0.0",
  "api_base_url": "http://localhost:8000"
}
```

## Authentication

### OAuth 2.1 Flow

1. **User Authorization**: User authorizes ChatGPT app via OAuth flow
2. **Token Generation**: Backend generates JWT access token signed with RS256
3. **Token Verification**: MCP server verifies token using public key
4. **API Access**: MCP server calls backend API with verified user context

### Token Structure

```json
{
  "sub": "123",                                    // User ID
  "client_id": "chatgpt-client",                  // OAuth client
  "scope": "tasks:read tasks:write",              // Granted scopes
  "iss": "https://mindflow.example.com",          // Issuer
  "aud": "mindflow-api",                          // Audience
  "exp": 1704196800,                              // Expiration timestamp
  "iat": 1704110400,                              // Issued at timestamp
  "jti": "a1b2c3d4e5f6..."                        // Unique token ID
}
```

### Security Features

- **RS256 Asymmetric Signing**: Private key for signing, public key for verification
- **Token Expiration**: Tokens expire after 1 hour (configurable)
- **Audience Validation**: Ensures token is intended for this API
- **Issuer Validation**: Verifies token came from trusted issuer
- **No Token Logging**: Access tokens are never logged for security

## Error Handling

### Client Errors (4xx)

- **401 Unauthorized**: Invalid or expired token
- **404 Not Found**: No pending tasks available

**Example:**
```json
{
  "error": "Unauthorized: Token has expired"
}
```

### Server Errors (5xx)

- **500 Internal Server Error**: FastAPI backend error
- **503 Service Unavailable**: Backend temporarily unavailable

**Retry Behavior:**
- Client errors (4xx): No retry, return error immediately
- Server errors (5xx): Retry up to 3 times with exponential backoff
- Network errors: Retry up to 3 times with exponential backoff

### Exponential Backoff

```
Attempt 1: Immediate
Attempt 2: Wait 1.0s
Attempt 3: Wait 2.0s
Attempt 4: Wait 4.0s
```

## Testing

### Run All MCP Tests

```bash
make mcp-test
```

### Run Specific Test Suite

```bash
# OAuth verification tests
uv run pytest tests/mcp_server/test_auth.py -v

# Task tool tests
uv run pytest tests/mcp_server/test_tasks_tool.py -v
```

### Test Coverage

```bash
uv run pytest tests/mcp_server/ --cov=mcp_server --cov-report=term-missing
```

## Integration with ChatGPT Apps SDK

### 1. Register MCP Server

In your ChatGPT app configuration:

```json
{
  "mcp_servers": {
    "mindflow": {
      "url": "http://localhost:8001",
      "authentication": {
        "type": "oauth2",
        "authorization_url": "http://localhost:8000/oauth/authorize",
        "token_url": "http://localhost:8000/oauth/token",
        "scopes": ["tasks:read"]
      }
    }
  }
}
```

### 2. Tool Invocation

ChatGPT will automatically invoke tools based on user queries:

```
User: "What should I focus on today?"
→ ChatGPT invokes get_next_task()
→ Returns best task with reasoning
→ ChatGPT presents recommendation to user
```

## Monitoring and Logging

### Structured Logs

The MCP server uses `structlog` for structured logging:

```json
{
  "event": "get_next_task_called",
  "has_auth": true,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Log Events

- `starting_mcp_server`: Server startup
- `get_next_task_called`: Tool invocation
- `get_next_task_success`: Successful task retrieval
- `get_next_task_auth_failed`: Authentication failure
- `get_next_task_failed`: General error

### Metrics to Monitor

- Request rate (requests/minute)
- Error rate (errors/requests)
- Response time (p50, p95, p99)
- Token verification failures
- API call failures

## Troubleshooting

### Issue: "Authentication failed: Token has expired"

**Solution:** Token expired. User needs to re-authorize the ChatGPT app.

### Issue: "No pending tasks available"

**Solution:** User has no pending tasks. This is expected behavior.

### Issue: "API call failed after 4 attempts"

**Possible Causes:**
1. FastAPI backend is down
2. Network connectivity issues
3. Backend is overloaded

**Debug Steps:**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check MCP server logs
journalctl -u mindflow-mcp -f

# Test OAuth token manually
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/tasks/best
```

### Issue: "Invalid token signature"

**Possible Causes:**
1. Public key mismatch between MCP server and backend
2. Token was signed with different private key

**Solution:**
```bash
# Ensure MCP server uses correct public key
ls -la app/oauth/keys/public_key.pem

# Verify key matches backend
diff app/oauth/keys/public_key.pem /path/to/backend/keys/public_key.pem
```

## Development

### Project Structure

```
mcp_server/
├── __init__.py              # Package init
├── main.py                  # MCP server entry point
├── config.py                # Configuration settings
├── auth.py                  # OAuth token verification
└── tools/
    ├── __init__.py
    └── tasks.py             # Task management tools

tests/mcp_server/
├── __init__.py
├── test_auth.py             # OAuth verification tests
└── test_tasks_tool.py       # Task tool tests
```

### Adding New Tools

1. Create tool function in `mcp_server/tools/`
2. Add `@mcp.tool()` decorator in `main.py`
3. Implement OAuth verification
4. Write comprehensive tests
5. Update documentation

Example:

```python
@mcp.tool()
async def create_task(authorization: str, title: str, description: str) -> dict:
    """Create a new task."""
    # Verify token
    payload = verify_bearer_token(authorization)

    # Call backend API
    result = await create_task_api(authorization, title, description)

    return result
```

## Security Best Practices

1. **Never Log Tokens**: Access tokens must never be logged
2. **HTTPS in Production**: Use HTTPS for all API calls
3. **Rate Limiting**: Enforce rate limits to prevent abuse
4. **Token Expiration**: Keep token lifetimes short (1 hour recommended)
5. **Scope Validation**: Verify token has required scopes
6. **Input Validation**: Validate all inputs from ChatGPT
7. **Error Messages**: Don't leak sensitive information in errors

## Performance Optimization

### Recommendations

1. **Connection Pooling**: Use httpx connection pooling for API calls
2. **Caching**: Cache frequently accessed data (with TTL)
3. **Async Operations**: All I/O operations are async
4. **Retry Configuration**: Tune retry settings based on backend SLA

### Benchmarks

- Token verification: <5ms
- API call (without retry): <100ms
- API call (with 3 retries): <7s (worst case)

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: https://github.com/mindflow/backend/issues
- Email: support@mindflow.example.com
