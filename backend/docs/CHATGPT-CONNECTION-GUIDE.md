# ChatGPT Connection Guide

**Last Updated**: 2025-11-02
**MindFlow Version**: 1.0
**ChatGPT Apps SDK**: OpenAI Official

---

## 🎯 Quick Start

Connect your MindFlow MCP server to ChatGPT in **3 simple steps**:

1. **Deploy** the backend (or run locally with ngrok)
2. **Configure** MCP connection in ChatGPT settings
3. **Authorize** OAuth 2.1 connection

**Time to complete**: 5-10 minutes

---

## 📋 Prerequisites

### Required
- ✅ MindFlow backend running and accessible via HTTPS
- ✅ Valid OAuth 2.1 configuration (automatic in production)
- ✅ ChatGPT Plus or Team account with Apps SDK access

### Optional
- 🔧 ngrok account (for local development)
- 🔧 Custom domain with SSL certificate (for production)

---

## 🚀 Part 1: Deployment Options

### Option A: Production Deployment (Recommended)

**Deploy to production with SSL**:

```bash
# 1. Set environment variables
export MINDFLOW_DOMAIN="tasks.yourdomain.com"
export API_BASE_URL="https://$MINDFLOW_DOMAIN"
export OAUTH_ISSUER="https://$MINDFLOW_DOMAIN"

# 2. Deploy backend
cd backend
make deploy

# 3. Verify deployment
curl https://$MINDFLOW_DOMAIN/health
```

**Expected response**:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Option B: Local Development with ngrok

**For testing before production deployment**:

```bash
# 1. Start backend locally
cd backend
make run

# 2. In another terminal, start ngrok
ngrok http 8000

# 3. Note your ngrok URL
# Example: https://abc123.ngrok.io

# 4. Update environment variables
export API_BASE_URL="https://abc123.ngrok.io"
export OAUTH_ISSUER="https://abc123.ngrok.io"

# 5. Restart backend with new config
make run
```

**⚠️ Important**: Free ngrok URLs change on restart. Use paid ngrok or deploy to production for persistent URLs.

---

## 🔌 Part 2: Connect MCP Server to ChatGPT

### Step 1: Get MCP Server Configuration

Your MCP server exposes the following endpoints:

```
OAuth Discovery:    https://your-domain.com/.well-known/oauth-authorization-server
MCP Endpoint:       https://your-domain.com/mcp
JWKS:              https://your-domain.com/.well-known/jwks.json
Authorization:     https://your-domain.com/oauth/authorize
Token:             https://your-domain.com/oauth/token
```

### Step 2: Add MCP Server in ChatGPT

1. **Open ChatGPT** → Settings → Apps SDK
2. **Click** "Add MCP Server"
3. **Enter** server details:

   ```
   Server Name:        MindFlow Task Management
   Server URL:         https://your-domain.com/mcp
   Authentication:     OAuth 2.1
   OAuth Discovery:    https://your-domain.com/.well-known/oauth-authorization-server
   ```

4. **Click** "Connect"

### Step 3: Authorize Connection

1. ChatGPT will **redirect you** to MindFlow's OAuth authorization page
2. **Review** the requested permissions:
   - Read your tasks
   - Update task status (complete, snooze)
   - AI-powered task scoring
3. **Click** "Authorize"
4. You'll be **redirected back** to ChatGPT

**Success**: You should see "MindFlow Task Management" in your connected servers list.

---

## 🧪 Part 3: Test the Connection

### Quick Test Prompts

Try these in ChatGPT to verify everything works:

```
1. "What should I work on?"
   → Should call get_next_task and show TaskWidget

2. "Show me my top priority task"
   → Should display task with AI score and reasoning

3. [Click "Complete Task" button in widget]
   → Should mark task complete and ask for next task

4. [Click "Snooze 3h" button]
   → Should snooze task and show next one
```

### Expected Behavior

**For "What should I work on?"**:
1. ChatGPT calls `get_next_task` MCP tool
2. Backend fetches best task via AI scoring
3. TaskWidget renders inline with:
   - Task title, description, priority
   - Due date, effort estimate, tags
   - AI score with reasoning breakdown
   - Complete and Snooze action buttons

**For button clicks**:
1. Widget calls `complete_task` or `snooze_task` tool
2. Backend updates task status
3. ChatGPT receives follow-up message
4. New task recommendation appears

---

## 🔧 Part 4: Troubleshooting

### Issue: "MCP server not responding"

**Cause**: Backend not accessible or SSL certificate issues

**Fix**:
```bash
# 1. Check backend is running
curl https://your-domain.com/health

# 2. Verify SSL certificate
curl -I https://your-domain.com

# 3. Check MCP endpoint
curl https://your-domain.com/mcp

# 4. Review backend logs
make logs
```

### Issue: "OAuth authorization failed"

**Cause**: Mismatch in OAuth configuration

**Fix**:
```bash
# 1. Verify OAuth discovery endpoint
curl https://your-domain.com/.well-known/oauth-authorization-server

# 2. Check OAUTH_ISSUER matches domain
echo $OAUTH_ISSUER
# Should be: https://your-domain.com

# 3. Verify JWKS endpoint
curl https://your-domain.com/.well-known/jwks.json

# 4. Regenerate OAuth keys if needed
make oauth-reset
```

### Issue: "Tool not found"

**Cause**: MCP tool discovery metadata missing or incorrect

**Fix**:
```bash
# 1. Check MCP server tools list
curl https://your-domain.com/mcp/tools

# 2. Should see:
# - get_next_task (with WHEN TO USE section)
# - complete_task
# - snooze_task
# - health_check

# 3. If missing, restart MCP server
make restart
```

### Issue: "TaskWidget not rendering"

**Cause**: Component bundle not deployed or malformed

**Fix**:
```bash
# 1. Verify component bundle exists
ls -lh backend/mcp_server/assets/taskwidget.js
# Should be ~9.2kb

# 2. Rebuild component
cd frontend
npm run build
cp dist/index.js ../backend/mcp_server/assets/taskwidget.js

# 3. Restart backend
cd ../backend
make restart
```

### Issue: "Actions fail silently"

**Cause**: Network errors or invalid task IDs

**Solution**:
- Open browser console (F12)
- Look for error messages in console
- Check backend logs: `make logs`
- Verify task_id is valid UUID

---

## 🔐 Part 5: Security Considerations

### OAuth Token Security

✅ **What we do**:
- RS256 asymmetric JWT signing
- 90-day refresh token rotation
- PKCE (Proof Key for Code Exchange)
- Constant-time token comparison
- Replay attack prevention

⚠️ **What you should do**:
- Keep `JWT_PRIVATE_KEY` secret
- Rotate keys every 90 days
- Use HTTPS only (never HTTP)
- Review OAuth logs regularly

### Production Checklist

Before going live:
- [ ] HTTPS enabled with valid SSL certificate
- [ ] `DEBUG=False` in production environment
- [ ] `CORS_ORIGINS` restricted to ChatGPT domains
- [ ] Database backups configured
- [ ] Monitoring and alerting set up
- [ ] Rate limiting enabled (60 req/min default)
- [ ] Error tracking (Sentry) configured

---

## 📊 Part 6: Monitoring

### Health Check

```bash
# Backend health
curl https://your-domain.com/health

# MCP server health
curl https://your-domain.com/mcp/health

# OAuth discovery
curl https://your-domain.com/.well-known/oauth-authorization-server
```

### Metrics to Monitor

Track these for optimal performance:
- **Request Rate**: Should be < 60/min per user (rate limit)
- **Response Time**: < 500ms for get_next_task
- **Error Rate**: < 1% for all endpoints
- **OAuth Success Rate**: > 99%
- **Component Load Time**: < 100ms

### Logs

```bash
# View all logs
make logs

# Filter by component
make logs | grep "mcp_server"
make logs | grep "oauth"

# Monitor in real-time
make logs --follow
```

---

## 🆘 Need Help?

### Documentation
- [MCP Server Details](./MCP_SERVER.md)
- [Deployment Guide](./DEPLOYMENT-GUIDE.md)
- [Apps SDK Review](./APPS-SDK-REVIEW.md)
- [Project Plan](./PLAN.md)

### External Resources
- [OpenAI Apps SDK Docs](https://developers.openai.com/apps-sdk)
- [OAuth 2.1 Spec](https://oauth.net/2.1/)
- [MCP Protocol](https://modelcontextprotocol.io)

### Support Channels
- GitHub Issues: [Project Issues](https://github.com/yourorg/mindflow/issues)
- Email: support@yourdomain.com

---

## ✅ Success Checklist

You're successfully connected when:
- ✅ ChatGPT shows "MindFlow Task Management" as connected
- ✅ Prompt "What should I work on?" returns TaskWidget
- ✅ Widget displays task with AI score and reasoning
- ✅ Complete and Snooze buttons work
- ✅ Follow-up messages trigger new task recommendations
- ✅ Error messages display properly when actions fail
- ✅ Theme switches between light/dark modes

**Congratulations!** You're now using AI-powered task management in ChatGPT. 🎉

---

## 🔄 Updating Your Integration

### When to Update
- New MCP tools added
- Component UI changes
- OAuth configuration changes
- Backend API updates

### Update Process

```bash
# 1. Pull latest code
git pull origin main

# 2. Rebuild frontend component
cd frontend
npm install
npm run build
cp dist/index.js ../backend/mcp_server/assets/taskwidget.js

# 3. Update backend dependencies
cd ../backend
uv sync

# 4. Run migrations if needed
uv run alembic upgrade head

# 5. Restart services
make restart

# 6. Test connection
curl https://your-domain.com/health
```

### Breaking Changes

**If OAuth configuration changes**:
1. Users will need to **re-authorize**
2. Notify users before deploying
3. Update connection guide if needed

**If MCP tools change**:
1. ChatGPT will **auto-discover** new tools
2. No user action required
3. Test new tools thoroughly

---

## 📈 Advanced Configuration

### Custom Tool Descriptions

Edit `backend/mcp_server/main.py` to customize tool discovery:

```python
@mcp.tool(
    name="get_next_task",
    description="""Your custom description here.

WHEN TO USE:
- Your prompt patterns

DO NOT USE:
- Your exclusion patterns

RETURNS:
Your return value description""",
    readOnlyHint=True
)
```

### Component Customization

Edit `frontend/src/components/TaskWidget.tsx` to customize UI:

```typescript
// Update colors
const colors = {
  accent: '#007aff',  // Your brand color
  // ...
};

// Update button text
{isCompleting ? 'Processing...' : 'Done!'}
```

After changes:
```bash
npm run build
cp dist/index.js ../backend/mcp_server/assets/taskwidget.js
```

### OAuth Customization

Edit `backend/app/config.py`:

```python
# Token lifetimes
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Default: 60
REFRESH_TOKEN_EXPIRE_DAYS = 90   # Default: 90

# Allowed redirect URIs
ALLOWED_REDIRECT_URIS = [
    "https://chatgpt.com/auth/callback",
    # Add custom URIs
]
```

---

**End of Connection Guide**
