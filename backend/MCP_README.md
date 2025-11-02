# MindFlow MCP Server - Quick Start

## What is the MCP Server?

The MindFlow MCP (Model Context Protocol) Server enables ChatGPT to intelligently recommend tasks from your MindFlow task list through the ChatGPT Apps SDK. It provides secure OAuth-authenticated access to AI-powered task scoring.

## Quick Start

### 1. Start the FastAPI Backend

```bash
make run
# Backend runs on http://localhost:8000
```

### 2. Start the MCP Server

```bash
make mcp-server
# MCP Server runs on http://localhost:8001
```

### 3. Test the MCP Server

```bash
make mcp-test
# Runs 16 comprehensive tests covering OAuth and task tools
```

## Architecture

```
ChatGPT → MCP Server (OAuth) → FastAPI Backend (JWT) → PostgreSQL
  :8001                          :8000
```

## Available Tools

### get_next_task
Returns the best task to work on based on AI scoring of deadlines, priorities, and effort estimates.

**Usage in ChatGPT:**
```
User: "What should I work on next?"
→ ChatGPT automatically calls get_next_task tool
→ Returns: "Complete project documentation (Priority 4, Due Feb 1)"
```

### health_check
Verifies MCP server is running and can connect to the backend.

## Configuration

See `.env` file for configuration options:

```env
# MCP Server
MCP_SERVER_PORT=8001
API_BASE_URL=http://localhost:8000

# OAuth (must match FastAPI backend)
OAUTH_ISSUER=https://mindflow.example.com
JWT_AUDIENCE=mindflow-api
```

## Security

- **OAuth 2.1** with RS256 asymmetric JWT signatures
- **Token Verification** on every request
- **No Token Logging** for security
- **Rate Limiting** to prevent abuse

## Development

```bash
# Run tests
make mcp-test

# Run with auto-reload (for development)
uv run fastmcp dev mcp_server.main:mcp --port 8001

# Check code formatting
make lint format
```

## Full Documentation

See [docs/MCP_SERVER.md](docs/MCP_SERVER.md) for comprehensive documentation including:
- Architecture details
- Authentication flow
- Error handling
- Monitoring and logging
- Troubleshooting guide
- Integration with ChatGPT Apps SDK

## Makefile Commands

```bash
make mcp-server   # Start MCP server
make mcp-test     # Run MCP tests
make help         # Show all available commands
```

## Testing

The MCP server includes 16 comprehensive tests:

- **9 OAuth tests**: Token verification, expiration, signatures, scopes
- **7 Tool tests**: Success cases, error handling, retries, API integration

All tests use TDD methodology and mock external dependencies.

## Next Steps

1. Start both servers (`make run` and `make mcp-server`)
2. Configure ChatGPT app to use MCP server endpoint
3. Test OAuth flow with your ChatGPT app
4. Query ChatGPT: "What should I work on next?"

## Support

- Documentation: `docs/MCP_SERVER.md`
- Tests: `tests/mcp_server/`
- Issues: GitHub Issues
