# MindFlow Master Implementation Plan (v8.0 - First Principles)

**Version**: 8.0.0
**Last Updated**: 2025-10-31
**Approach**: First Principles + Pareto (20% work → 80% value)
**Status**: Phases 1-7 Complete, Minimal Path to Launch

---

## 🎯 CORE MISSION (Fundamental Truth #1)

**MindFlow helps users accomplish more by telling them what to work on next through natural conversation with ChatGPT.**

Everything else is secondary.

---

## ✅ COMPLETED WORK (Phases 1-7)

### What We Have
- ✅ **Backend API**: 13 endpoints, 138 tests, 87% coverage
- ✅ **Database**: PostgreSQL with 4 tables (users, tasks, preferences, audit_log)
- ✅ **Authentication**: JWT tokens, bcrypt hashing
- ✅ **AI Scoring**: 7.2ms response time (278x faster than target)
- ✅ **CI/CD**: GitHub Actions deployment automation
- ✅ **Custom GPT**: Live prototype using Google Sheets

### What Works Today
```
User: "What should I work on?"
  ↓
ChatGPT Custom GPT
  ↓
Google Apps Script (Phase 1)
  ↓
Google Sheets Database
  ↓
"Work on Q4 Report - due today, high priority"
```

### What's Ready (Not Deployed)
```
User: "What should I work on?"
  ↓
ChatGPT Custom GPT
  ↓
FastAPI Backend (Phase 7) ← READY BUT NOT LIVE
  ↓
PostgreSQL Database
  ↓
AI Scoring Algorithm (7.2ms)
  ↓
"Work on Q4 Report - due in 2 hours, score 85/100"
```

---

## 🚀 MINIMAL PATH TO PUBLIC LAUNCH

### First Principles Analysis

**Question**: What's blocking us from launching to 1000 users?

**Answer** (working backwards from user pain):
1. ❌ Users can't reset forgotten passwords → **Phase 8A**
2. ❌ Users re-login every 24 hours → **Phase 8A**
3. ❌ No landing page to explain product → **Phase 8B**
4. ❌ Backend not deployed to production → **Phase 8C**
5. ✅ Everything else works

**Conclusion**: Only need 3 things before launch:
- Enhanced auth (password reset + refresh tokens)
- Simple landing page
- Production deployment

---

## 📦 PHASE 8: MINIMUM VIABLE LAUNCH (MVP)

**Timeline**: 2 weeks
**Effort**: 40 hours
**Business Value**: Can accept first 1000 paying users

### 8A: Critical Auth Features ✅ COMPLETE (6 days, 24 hours)

**Status**: ✅ **PRODUCTION READY** (Completed 2025-10-31)
**Why Critical**: Users locked out = churn

#### Features (Pareto 20%)
1. **Password Reset** (MUST HAVE)
   - Email link → reset password
   - Blocks: Users can't recover accounts

2. **Refresh Tokens** (MUST HAVE)
   - 30-day sessions vs 24-hour
   - Blocks: Daily re-login friction

3. **Email Verification** (NICE TO HAVE → Skip for MVP)
   - Prevents fake accounts
   - Can add post-launch

4. **OAuth (Google)** (NICE TO HAVE → Skip for MVP)
   - Faster signup
   - Can add post-launch

#### Implementation Plan

**Database Changes** (1 day):
```sql
-- Password reset tokens
CREATE TABLE password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL DEFAULT (NOW() + INTERVAL '1 hour'),
    used_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_expires (expires_at) WHERE used_at IS NULL
);

-- Refresh tokens
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL DEFAULT (NOW() + INTERVAL '30 days'),
    revoked_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP DEFAULT NOW(),
    user_agent VARCHAR(500),
    ip_address INET,
    INDEX idx_user_active (user_id, expires_at) WHERE revoked_at IS NULL
);
```

**Files to Create** (3 days):
```
backend/app/services/email_service.py
  ├─ send_password_reset_email(email, reset_token)
  │  └─ Uses SendGrid free tier (100 emails/day)
  └─ render_email_template(template_name, context)
     └─ Simple HTML email with reset link

backend/app/db/crud.py (additions)
  ├─ PasswordResetTokenCRUD.create(session, user_id) → token
  ├─ PasswordResetTokenCRUD.validate_and_use(session, token) → user_id
  ├─ RefreshTokenCRUD.create(session, user_id, user_agent, ip) → refresh_token
  ├─ RefreshTokenCRUD.validate(session, token) → user_id
  └─ RefreshTokenCRUD.revoke_all_for_user(session, user_id)

backend/app/api/auth.py (additions)
  ├─ POST /api/auth/forgot-password
  │  └─ Input: email
  │  └─ Output: {"message": "If email exists, reset link sent"}
  │  └─ Rate limit: 3 requests/hour per email
  │
  ├─ POST /api/auth/reset-password
  │  └─ Input: token, new_password
  │  └─ Output: {"message": "Password reset successful"}
  │  └─ Validates token, updates password, marks token used
  │
  ├─ POST /api/auth/refresh
  │  └─ Input: refresh_token (body or cookie)
  │  └─ Output: {"access_token": "...", "token_type": "bearer"}
  │  └─ Issues new access token, updates last_used_at
  │
  └─ POST /api/auth/revoke
     └─ Input: none (uses current user from JWT)
     └─ Output: {"message": "All sessions revoked"}
     └─ Revokes all refresh tokens for user
```

**Tests to Write** (2 days):
```python
tests/auth/test_password_reset.py
  ├─ test_forgot_password_sends_email_for_existing_user
  │  └─ Verify email sent with valid token
  ├─ test_forgot_password_generic_response_for_nonexistent_user
  │  └─ Prevent email enumeration attack
  ├─ test_reset_password_with_valid_token_succeeds
  │  └─ Password updated, token marked used
  ├─ test_reset_password_with_expired_token_fails
  │  └─ Token older than 1 hour rejected
  ├─ test_reset_password_with_used_token_fails
  │  └─ One-time use enforcement
  └─ test_forgot_password_rate_limiting
     └─ Max 3 requests per hour per email

tests/auth/test_refresh_tokens.py
  ├─ test_login_returns_refresh_token
  │  └─ Access token + refresh token issued
  ├─ test_refresh_endpoint_issues_new_access_token
  │  └─ Valid refresh token → new access token
  ├─ test_refresh_updates_last_used_timestamp
  │  └─ Track token usage for security monitoring
  ├─ test_refresh_with_expired_token_fails
  │  └─ Expired tokens rejected (>30 days)
  ├─ test_refresh_with_revoked_token_fails
  │  └─ Revoked tokens cannot be used
  ├─ test_revoke_all_sessions_invalidates_refresh_tokens
  │  └─ User can logout all devices
  └─ test_refresh_token_rotation
     └─ Optional: issue new refresh token on use
```

**Target**: 20+ new tests, maintain 87%+ coverage

---

### 8B: Landing Page ✅ COMPLETE (2 days, 8 hours)

**Status**: ✅ Production-ready landing page delivered
**Why Critical**: Users need to understand what MindFlow is

#### First Principles: What Does Landing Page NEED?

**Goal**: Convert visitor → Custom GPT user in <30 seconds

**Essential Elements** (Pareto 20%):
1. **Hero**: "AI task manager in ChatGPT" (5 seconds to understand)
2. **Demo**: Video or animated GIF showing conversation
3. **CTA**: "Try in ChatGPT" button → Custom GPT link
4. **Trust**: "Used by X people, saves Y hours/week"

**Non-Essential** (can skip):
- Pricing page (free for now)
- Feature comparison
- Customer testimonials (no customers yet)
- Blog
- FAQ (ChatGPT can answer)

#### Implementation

**Tech Stack** (simplest possible):
```
Single HTML file + Tailwind CSS (CDN) + Alpine.js (interactivity)
Total: 1 file, ~300 lines, <50KB, loads in <1s
```

**File to Create**:
```
frontend/index.html
  ├─ <head>
  │  ├─ Tailwind CSS CDN (no build step)
  │  ├─ Alpine.js CDN (lightweight interactivity)
  │  └─ Meta tags (SEO, social sharing)
  │
  ├─ <section class="hero">
  │  ├─ Headline: "Your AI task manager lives in ChatGPT"
  │  ├─ Subhead: "Stop context switching. Just ask what to work on next."
  │  └─ CTA: "Try MindFlow in ChatGPT →"
  │
  ├─ <section class="demo">
  │  ├─ Animated conversation showing:
  │  │  User: "What should I work on?"
  │  │  MindFlow: "Work on Q4 Report - due in 2 hours, high priority"
  │  └─ Auto-plays on viewport scroll
  │
  ├─ <section class="how-it-works">
  │  ├─ Step 1: Install Custom GPT (link)
  │  ├─ Step 2: Tell it your tasks
  │  └─ Step 3: Ask what to work on
  │
  ├─ <section class="pricing">
  │  └─ "Free beta - 100 users only" (creates urgency)
  │
  └─ <footer>
     ├─ GitHub link
     ├─ Twitter/X link
     └─ Privacy policy link
```

**Deployment**:
```
Cloudflare Pages (free tier)
  ├─ Connect GitHub repo
  ├─ Auto-deploy on push to main
  ├─ Custom domain: mindflow.ai (optional, $12/year)
  └─ Global CDN, <100ms latency worldwide
```

**Tests** (minimal, since it's static):
```javascript
tests/landing-page.spec.js (Playwright)
  ├─ test_hero_loads_in_under_1_second
  ├─ test_cta_button_links_to_custom_gpt
  ├─ test_demo_animation_plays_on_scroll
  └─ test_mobile_responsive_layout
```

#### ✅ What Was Delivered

**Files Created**:
```
frontend/
├── index.html (17KB)                  # Production landing page
├── README.md (12KB)                   # Deployment guide (5 options)
├── DEPLOYMENT-CHECKLIST.md (8.5KB)    # 100+ validation items
├── IMPLEMENTATION-SUMMARY.md (15KB)   # Technical deep dive
├── QUICKSTART.md (7KB)                # 5-minute setup guide
├── package.json (1.2KB)               # Dev dependencies
└── validate.sh (4.5KB)                # Automated validation

tests/frontend/
└── landing-page.spec.js (16KB)        # 40+ Playwright tests
```

**Validation Results**:
- ✅ File size: 17KB (target: <50KB)
- ✅ All HTML structure checks passing
- ✅ SEO optimized (meta tags, Open Graph, Twitter Cards)
- ✅ WCAG AA accessible
- ✅ Mobile responsive (320px - 2560px)
- ✅ 2 CTA links to Custom GPT
- ✅ Privacy-friendly analytics integrated
- ✅ Expected Lighthouse score: 98+ (performance)

**Key Features Implemented**:
1. Animated ChatGPT conversation demo (CSS only, no JS)
2. 3-step "How It Works" section
3. Glass-effect feature cards
4. Dual CTAs (hero + footer)
5. GitHub stars + Twitter integration
6. Mobile-first responsive design

**Deployment Ready**:
- Cloudflare Pages (recommended, <5 min setup)
- Vercel, Netlify, GitHub Pages (alternatives)
- DigitalOcean Static Sites (if needed)

**Next Steps** (before launch):
1. Update Custom GPT link (line 115 + 385 in index.html)
2. Update GitHub username (replace `yourusername`)
3. Update Twitter handle (replace `@yourusername`)
4. Run `./validate.sh` to confirm all checks pass
5. Deploy: `wrangler pages publish . --project-name=mindflow`

---

### 8C: Production Deployment (2 days, 8 hours)

**Why Critical**: Backend must be live for Custom GPT migration

#### Deployment Checklist

**Already Have** (from Phase 7):
- ✅ Deployment scripts (`backend/deployment/`)
- ✅ Nginx config
- ✅ Systemd service
- ✅ Alembic migrations
- ✅ CI/CD workflow (`.github/workflows/deploy.yml`)

**New Tasks**:
1. **Provision DigitalOcean Droplet** (1 hour)
   - 2 CPU, 2GB RAM, Ubuntu 22.04 LTS ($12/month)
   - Reserve static IP
   - Configure firewall (ports 22, 80, 443)

2. **Run Automated Setup** (1 hour)
   ```bash
   cd backend/deployment
   ./setup.sh <droplet-ip> mindflow.ai
   ```
   - Installs Python, PostgreSQL, Nginx
   - Configures SSL via Let's Encrypt
   - Sets up systemd service
   - Runs database migrations

3. **Configure Environment** (1 hour)
   ```bash
   # On droplet: /opt/mindflow/backend/.env
   DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@localhost/mindflow
   SECRET_KEY=<random-32-chars>
   SENDGRID_API_KEY=<key-from-sendgrid>
   SENTRY_DSN=<optional-error-tracking>
   ENVIRONMENT=production
   ```

4. **Migrate Custom GPT** (2 hours)
   - Generate OpenAPI schema: `curl https://mindflow.ai/openapi.json`
   - Update Custom GPT Actions configuration
   - Test end-to-end: register user → create task → get best task

5. **Monitoring Setup** (3 hours)
   - Sentry error tracking (free tier: 5k errors/month)
   - Uptime monitoring (UptimeRobot, free tier: 50 monitors)
   - Log aggregation (Papertrail, free tier: 50MB/month)

**Testing** (already in CI/CD):
- ✅ Unit tests run on every push
- ✅ Integration tests with test database
- ✅ Smoke tests post-deployment

---

## 🎨 PHASE 9: OPTIONAL WEB DASHBOARD (FUTURE)

**Status**: DEFERRED - Not needed for launch
**Reason**: Custom GPT already provides excellent UX

### When to Build

**Triggers** (any of these):
1. 1000+ users requesting web interface
2. Feature parity with Todoist required for competitive reasons
3. Need offline support (Progressive Web App)
4. Want to monetize non-ChatGPT users

### Implementation (when needed)

**Tech Stack** (from archived docs):
- LIT web components (50KB bundle)
- TypeScript
- Vite build tool
- Deployment: Cloudflare Pages

**Key Views** (from `docs/archive/custom-views-todoist-ui.md`):
1. **Upcoming View**: Week navigator + task cards (primary view)
2. **Today View**: Focus mode for current tasks
3. **Inbox View**: Unscheduled tasks
4. **Settings View**: User preferences

**Effort**: 4-6 weeks (160-240 hours)

---

## 📈 PHASE 10-12: ADVANCED FEATURES (FUTURE)

### Phase 10: Task Management Enhancements (3 weeks)
**Status**: DEFERRED
**Features**: Recurring tasks, subtasks, dependencies, templates
**Trigger**: 500+ users requesting these features

### Phase 11: Team Collaboration (4 weeks)
**Status**: DEFERRED
**Features**: Shared tasks, workspaces, permissions
**Trigger**: 100+ teams using MindFlow

### Phase 12: ML Personalization (6 weeks)
**Status**: DEFERRED
**Features**: Learn user preferences, smart predictions
**Trigger**: 6+ months of user data collected

---

## 🗓️ IMPLEMENTATION TIMELINE

### Week 1: Enhanced Authentication
**Days 1-2**: Database schema + migrations
- Create `password_reset_tokens` table
- Create `refresh_tokens` table
- Write Alembic migration
- Test migration rollback

**Days 3-4**: Password Reset Implementation
- Email service (SendGrid integration)
- CRUD operations
- API endpoints (`/forgot-password`, `/reset-password`)
- Email templates (HTML + plaintext)
- Rate limiting (3 req/hour per email)

**Days 5-6**: Refresh Tokens Implementation
- CRUD operations
- Update `/login` to return refresh token
- New `/refresh` endpoint
- Token rotation logic (optional)
- Session management (`/revoke`)

**Day 7**: Testing + Bug Fixes
- Write 20+ auth tests
- Manual testing (password reset flow)
- Security review (token expiry, rate limiting)
- Performance testing (token lookup speed)

---

### Week 2: Landing Page + Deployment

**Days 8-9**: Landing Page ✅ COMPLETE (2025-10-30)
- ✅ Designed and built `frontend/index.html` with Tailwind CSS
- ✅ Created animated demo (ChatGPT conversation with typewriter effect)
- ✅ Added dual CTAs to Custom GPT
- ✅ Tested on mobile devices (responsive 320px-2560px)
- ✅ 40+ Playwright tests written
- ✅ Validation script passing all checks

**Days 10-11**: Production Deployment (NEXT - Phase 8C)
- Provision DigitalOcean droplet
- Run `deployment/setup.sh` script
- Configure environment variables
- SSL certificate setup (Let's Encrypt)
- Database migrations on production

**Days 12-13**: Custom GPT Migration
- Generate FastAPI OpenAPI schema
- Update Custom GPT Actions configuration
- Test with beta users (5-10 people)
- Monitor logs for errors
- Fix critical bugs

**Day 14**: Launch Prep
- Write launch announcement
- Prepare social media posts
- Set up analytics (Plausible or Simple Analytics)
- Final smoke tests
- Go/No-Go decision

---

## 📊 SUCCESS METRICS

### Phase 8 (MVP Launch)

**Launch Readiness** (Week 2, Day 14):
- ✅ Password reset working (test with 5+ users)
- ✅ Refresh tokens reducing re-login to <1% daily active users
- ✅ Landing page converting >5% visitors → Custom GPT users
- ✅ Backend uptime >99.5% (measure via UptimeRobot)
- ✅ Zero critical bugs in production (Sentry)

**User Acquisition** (Month 1):
- 100 registered users
- 10+ daily active users
- 50+ tasks created per day
- <5% churn (users who stop using)

**Technical Health** (Ongoing):
- API response time <100ms (p95)
- Database queries <50ms (p95)
- Test coverage maintained >85%
- Zero data loss incidents
- <1 hour mean time to recovery (MTTR)

---

## 💰 COST PROJECTIONS

### MVP Launch (0-100 users)
| Service | Usage | Cost/Month |
|---------|-------|------------|
| DigitalOcean Droplet | 2 CPU, 2GB RAM | $12 |
| Domain (mindflow.ai) | 1 domain | $1 (annual $12) |
| SendGrid | 100 emails/day | $0 (free tier) |
| Cloudflare Pages | Unlimited | $0 (free tier) |
| Sentry | 5k errors/month | $0 (free tier) |
| UptimeRobot | 50 monitors | $0 (free tier) |
| **Total** | | **$13/month** |

### Growth (100-1000 users)
| Service | Usage | Cost/Month |
|---------|-------|------------|
| DigitalOcean Droplet | 4 CPU, 8GB RAM | $48 |
| Managed PostgreSQL | 2 CPU, 4GB RAM | $15 |
| SendGrid | 1,000 emails/day | $15 (paid tier) |
| **Total** | | **$78/month** |

**Revenue Target**: $500/month (50 users × $10/month subscription)
**Profitability**: Month 2-3 after launch

---

## 🔧 TECHNICAL DEBT & RISKS

### Known Issues (To Fix)

1. **In-Memory Rate Limiting**
   - Won't work with multiple droplets
   - Fix: Migrate to Redis (add when scaling to 1000+ users)
   - Cost: $20/month for managed Redis

2. **No Database Backups**
   - Risk: Data loss if droplet fails
   - Fix: Automated daily backups to S3 (DigitalOcean Spaces)
   - Cost: $5/month for 100GB storage

3. **JWT Secret in .env File**
   - Risk: Secret exposed if .env committed to git
   - Fix: Use AWS Secrets Manager or HashiCorp Vault
   - Cost: $0.40/secret/month (AWS Secrets Manager)

4. **No Email Verification**
   - Risk: Fake accounts, spam
   - Fix: Add in Phase 8.5 (post-launch)
   - Effort: 1 day

5. **Test Coverage 87%**
   - Target: 95%+
   - Missing: Edge cases, error paths
   - Effort: 1 week to reach 95%

---

## 🎯 PRIORITY DECISION MATRIX

### Must Have (Blocks Launch)
- ✅ Password reset (Phase 8A - COMPLETE)
- ✅ Refresh tokens (Phase 8A - COMPLETE)
- ✅ Landing page (Phase 8B - COMPLETE)
- ⏳ Production deployment (Phase 8C - IN PROGRESS)
- ⏳ Custom GPT migration (Phase 8C - IN PROGRESS)

### Should Have (Launch Week 2)
- ⏳ Email verification
- ⏳ OAuth (Google login)
- ⏳ Database backups
- ⏳ Better error messages

### Nice to Have (Post-Launch)
- 🔮 Web dashboard
- 🔮 Recurring tasks
- 🔮 Mobile app
- 🔮 Team collaboration

### Won't Have (For Now)
- ❌ Machine learning personalization
- ❌ Advanced analytics
- ❌ Third-party integrations (Slack, Calendar)
- ❌ Offline mode

---

## 📝 IMPLEMENTATION CHECKLIST

### Week 1: Authentication ✅ COMPLETE
- [x] Day 1: Create database tables (password_reset_tokens, refresh_tokens)
- [x] Day 2: Write Alembic migration, test rollback
- [x] Day 3: SendGrid integration, email templates
- [x] Day 4: Password reset endpoints (/forgot-password, /reset-password)
- [x] Day 5: Refresh token CRUD + /login modifications
- [x] Day 6: /refresh endpoint + /revoke endpoint
- [x] Day 7: Write 20+ tests, manual testing, security review

### Week 2: Launch
- [x] Day 8: Design landing page wireframe
- [x] Day 9: Build frontend/index.html with Tailwind
- [ ] Day 10: Provision DigitalOcean droplet (NEXT)
- [ ] Day 11: Run deployment scripts, configure SSL
- [ ] Day 12: Generate OpenAPI schema, update Custom GPT
- [ ] Day 13: Beta testing with 5-10 users
- [ ] Day 14: Fix critical bugs, launch announcement

### Post-Launch (Week 3+)
- [ ] Monitor error rates (Sentry)
- [ ] Track user signups (analytics)
- [ ] Collect feedback (in-app survey)
- [ ] Fix non-critical bugs
- [ ] Plan Phase 9 based on user requests

---

## 🚦 GO/NO-GO CRITERIA (Day 14)

### Launch if ALL true:
1. ✅ Zero critical bugs (P0/P1) in production
2. ✅ Password reset tested with 5+ users
3. ✅ Refresh tokens working (verified in logs)
4. ✅ Landing page loads <1s (tested on 4G)
5. ✅ Custom GPT integrated with FastAPI backend
6. ✅ Database migrations applied successfully
7. ✅ SSL certificate valid (Let's Encrypt)
8. ✅ Monitoring active (Sentry + UptimeRobot)

### Delay launch if ANY true:
- ❌ Critical data loss bug discovered
- ❌ Authentication bypass vulnerability
- ❌ Backend crashes under load (>5 req/s)
- ❌ Custom GPT returns errors >10% of requests

---

## 🎓 LESSONS LEARNED (First Principles Review)

### What Worked
1. **Custom GPT as Frontend**: Saved 6-8 weeks of UI development
2. **Phases 1-7 Backlog**: Having production-ready backend was key
3. **Test-Driven Development**: 87% coverage caught bugs early
4. **Modern Tooling (uv, ruff)**: Faster development, fewer errors

### What to Improve
1. **Overengineering**: Built features not needed for MVP (audit_log table)
2. **Documentation**: 28 files created redundancy (now consolidated)
3. **Scope Creep**: Phases 9-12 planned too far ahead

### First Principles Mindset
1. **Always ask**: "Does this block user value?"
2. **Pareto everywhere**: 20% of code delivers 80% of value
3. **Ship fast, iterate**: Perfect is the enemy of good
4. **User feedback > assumptions**: Build what users request, not what we imagine

---

## 📞 NEXT STEPS

1. **Review this plan** with stakeholders
2. **Commit to 2-week timeline** (or adjust)
3. **Start Week 1, Day 1**: Create database migration
4. **Ship MVP on Day 14**: Launch to first 100 users
5. **Iterate based on feedback**: Users tell us Phase 9-12 priorities

---

**Version**: 10.0.0 (Major Update: Complete Apps SDK Specification)
**Philosophy**: First Principles + Pareto Principle
**Mantra**: "Ship working software that delivers business value"

---

## 🎨 PHASE 9: OPENAI APPS SDK INTEGRATION (Post-Launch Enhancement)

**Timeline**: 1.5-2 weeks (after Phase 8C deployment)
**Effort**: 40-50 hours (updated estimate with OAuth + compliance)
**Business Value**: Enhanced ChatGPT UX with interactive task cards
**Trigger**: Launch complete + initial user feedback positive

### Why Apps SDK?

**First Principles Analysis**:
- **Current**: Text-based responses in ChatGPT (works great, 80% of value)
- **Enhancement**: Visual task cards with inline actions (adds 20% more delight)
- **User Pain**: "I want to complete tasks without leaving the chat"

**Value Proposition**:
- Interactive task cards render inline in ChatGPT
- Visual priority indicators (color-coded badges)
- One-click actions (complete, snooze, reschedule)
- State persistence across conversation turns
- Carousel mode for browsing multiple tasks
- Fullscreen mode for rich editing

### 9A: MCP Server + React Components + OAuth (7-10 days, 40-50 hours)

**Status**: PLANNED (build after Phase 8C deployment)

#### Architecture Overview

**Updated Architecture** (Python MCP Server):
```
ChatGPT (OAuth Client)
  ↓ Discovery: GET /.well-known/oauth-authorization-server
FastAPI Backend (Authorization Server)
  ├── OAuth Discovery Endpoints:
  │   ├── /oauth/authorize (user login flow)
  │   ├── /oauth/token (exchange code for access token)
  │   ├── /oauth/register (dynamic client registration)
  │   └── /.well-known/jwks.json (public keys for verification)
  ↓
ChatGPT → User authorizes → Receives access token
  ↓ User asks: "what should I work on?"
ChatGPT calls MCP tool: "mindflow.get_best_task"
  ↓ Includes OAuth access token
Python MCP Server (FastMCP) - https://your-domain.com/mcp
  ├── Verifies JWT token (issuer, audience, expiration, scopes)
  ├── Proxies to FastAPI Backend with user context
  └── Returns task with widget metadata
  ↓
FastAPI Backend (https://api.yourdomain.com)
  ↓ Returns task data
{
  "task": {
    "id": "...",
    "title": "Review pull request",
    "priority": 5,
    "due_date": "2025-11-03T14:00:00Z",
    "score": 95.5
  },
  "_meta": {
    "openai/outputTemplate": "<embedded React component code>",
    "openai/displayMode": "inline",
    "openai/widgetId": "task-card-123"
  }
}
  ↓
ChatGPT renders React component in iframe
  ↓ Component accesses via window.openai API
window.openai.toolOutput → Task data
window.openai.callTool("mindflow.complete_task", {taskId})
window.openai.setWidgetState({selectedFilter: "high-priority"})
  ↓
User sees interactive task card with live actions
```

**Key Changes from Previous Plan**:
1. ✅ **Python MCP Server** (not Node.js) using FastMCP library
2. ✅ **OAuth 2.1** with MCP Authorization Spec (full implementation)
3. ✅ **HTTPS Public Endpoint** required (ngrok for dev, production hosting)
4. ✅ **Embedded Component** in metadata (single ESM bundle)
5. ✅ **Display Mode Strategy** (inline, carousel, fullscreen, PiP)

#### Files to Create

**Frontend (React + TypeScript)** - Build to single ESM bundle:
```
frontend/apps-sdk/
├── src/
│   ├── components/
│   │   ├── TaskCard.tsx                    # Main task display component
│   │   ├── TaskList.tsx                    # Multiple tasks view (carousel)
│   │   ├── TaskEditor.tsx                  # Fullscreen edit mode
│   │   ├── PriorityBadge.tsx              # Visual priority indicator
│   │   ├── TaskActions.tsx                # Complete/snooze/reschedule buttons
│   │   └── EmptyState.tsx                 # No tasks state
│   ├── services/
│   │   ├── openai-client.ts               # window.openai wrapper
│   │   └── state-manager.ts               # 3-tier state management
│   ├── hooks/
│   │   ├── useWidgetState.ts              # Widget-level state hook
│   │   ├── useOpenAiGlobal.ts             # Theme/locale reactive hook
│   │   └── useDisplayMode.ts              # Display mode transitions
│   ├── types/
│   │   └── task.ts                        # Task type definitions
│   ├── App.tsx                            # Root component with mode router
│   └── index.tsx                          # Entry point
├── package.json                           # React 18+, TypeScript (NO Tailwind*)
├── tsconfig.json                          # TypeScript config
├── esbuild.config.js                      # ⚠️ Single ESM bundle (not Vite)
└── README.md                              # Build instructions

*Note: Design guidelines require system fonts/colors only
```

**Python MCP Server** (FastMCP) - Connects ChatGPT to FastAPI:
```
mcp_server/
├── server.py                              # MCP server entry point (FastMCP)
├── tools/
│   ├── __init__.py
│   ├── get_best_task.py                   # GET /api/tasks/best
│   ├── create_task.py                     # POST /api/tasks
│   ├── complete_task.py                   # PUT /api/tasks/{id} (status=completed)
│   ├── snooze_task.py                     # PUT /api/tasks/{id} (snoozed_until)
│   ├── reschedule_task.py                 # PUT /api/tasks/{id} (due_date)
│   └── get_pending_tasks.py               # GET /api/tasks/pending (carousel)
├── auth/
│   ├── __init__.py
│   ├── jwt_verifier.py                    # Verify OAuth tokens via JWKS
│   └── oauth_client.py                    # Token introspection (if needed)
├── config.py                              # Backend URL, JWKS URL, scopes
├── types.py                               # MCP tool schemas
├── assets/
│   └── component.js                       # Built React component (embedded)
├── requirements.txt                       # fastmcp, httpx, pyjwt, etc.
├── pyproject.toml                         # uv project config
├── Dockerfile                             # Containerized deployment
└── README.md                              # Setup + deployment instructions
```

**FastAPI Backend Updates** (OAuth endpoints):
```
backend/app/
├── oauth/
│   ├── __init__.py
│   ├── discovery.py                       # /.well-known/oauth-authorization-server
│   ├── authorize.py                       # /oauth/authorize (login flow)
│   ├── token.py                           # /oauth/token (code exchange)
│   ├── register.py                        # /oauth/register (dynamic clients)
│   └── jwks.py                            # /.well-known/jwks.json (public keys)
└── (existing files remain unchanged)
```

**Tests**:
```
tests/apps-sdk/
├── components/
│   ├── test_task_card.tsx                  # Component rendering tests
│   ├── test_task_actions.tsx               # Button interaction tests
│   ├── test_display_modes.tsx              # Inline/carousel/fullscreen
│   └── test_integration.tsx                # Full flow tests
├── mcp/
│   ├── test_server.py                      # FastMCP server tests
│   ├── test_tools.py                       # Tool invocation tests
│   ├── test_auth.py                        # OAuth token verification
│   └── test_metadata.py                    # Widget metadata generation
├── oauth/
│   ├── test_discovery.py                   # Discovery endpoint tests
│   ├── test_authorize.py                   # Authorization flow tests
│   ├── test_token.py                       # Token exchange tests
│   └── test_jwks.py                        # JWKS generation/validation
└── e2e/
    ├── test_chatgpt_flow.py                # End-to-end ChatGPT simulation
    └── test_oauth_flow.py                  # Full OAuth 2.1 flow test
```

#### Component Functions

**TaskCard.tsx**:
```typescript
function TaskCard(props: TaskCardProps): JSX.Element
// Renders interactive task card with priority badge, title, due date, and action buttons.
// Handles state updates via window.openai.setWidgetState().

function formatDueDate(dueDate: string): string
// Converts ISO date to human-readable format ("Due in 2 hours", "Tomorrow", etc.).

function getPriorityColor(priority: number): string
// Maps priority (1-5) to Tailwind color class (red-500, orange-400, etc.).
```

**TaskActions.tsx**:
```typescript
async function handleCompleteTask(taskId: string): Promise<void>
// Calls window.openai.callTool("completeTask", {taskId}), updates local state, shows success toast.

async function handleSnoozeTask(taskId: string, duration: "1h" | "tomorrow"): Promise<void>
// Calculates snooze time, calls MCP tool, removes task from view temporarily.

async function handleReschedule(taskId: string, newDate: string): Promise<void>
// Opens date picker, calls rescheduleTask tool, updates card display.
```

**openai-client.ts**:
```typescript
async function callTool(toolName: string, params: object): Promise<any>
// Wraps window.openai.callTool with error handling, retry logic, and loading states.

async function saveWidgetState(state: object): Promise<void>
// Persists component state using window.openai.setWidgetState for conversation continuity.

function subscribeToThemeChanges(callback: (theme: "light" | "dark") => void): void
// Listens to ChatGPT theme changes, updates component styling accordingly.
```

#### MCP Server Functions

**server.ts**:
```typescript
async function startMCPServer(port: number = 3000): Promise<void>
// Initializes MCP server, registers tools, connects to FastAPI backend via HTTP client.

function registerTools(server: MCPServer): void
// Registers all task management tools (getBestTask, createTask, etc.) with their schemas.
```

**tools/getBestTask.ts**:
```typescript
async function getBestTaskTool(params: {}, context: ToolContext): Promise<ToolResult>
// Calls GET /api/tasks/best, returns task with _meta.openai/outputTemplate = "task-card".

function formatTaskForWidget(task: Task): object
// Transforms FastAPI task response into Apps SDK widget format with metadata.
```

**tools/completeTask.ts**:
```typescript
async function completeTaskTool(params: {taskId: string}, context: ToolContext): Promise<ToolResult>
// Calls PUT /api/tasks/{taskId} with status=completed, returns success message and updated task list.
```

#### Test Cases

**Component Tests**:
```typescript
test_task_card_renders_with_priority_5_as_red_badge
// Verifies priority 5 tasks display red badge with "Urgent" label

test_complete_button_calls_mcp_tool_and_removes_card
// Simulates button click, mocks callTool, asserts card disappears

test_due_date_formats_correctly_for_overdue_tasks
// Checks "Overdue by 2 hours" displays for past due dates

test_state_persists_across_component_remounts
// Saves state, unmounts component, remounts, verifies state restored

test_dark_mode_theme_applies_correct_colors
// Toggles theme, asserts Tailwind dark: classes active
```

**MCP Server Tests**:
```typescript
test_mcp_server_starts_and_listens_on_port_3000
// Starts server, verifies HTTP endpoint accessible

test_get_best_task_tool_returns_valid_widget_metadata
// Invokes getBestTask, asserts _meta.openai/outputTemplate present

test_complete_task_tool_updates_backend_via_fastapi
// Mocks FastAPI PUT request, verifies status=completed sent

test_mcp_server_handles_backend_500_errors_gracefully
// Simulates FastAPI error, verifies user-friendly error message returned

test_authentication_token_passed_to_fastapi_requests
// Verifies JWT token from ChatGPT user forwarded to backend
```

**End-to-End Tests**:
```typescript
test_full_flow_ask_gpt_see_card_complete_task
// Simulates: ChatGPT message → MCP call → FastAPI → widget render → button click → backend update

test_multiple_tasks_render_as_scrollable_list
// Requests pending tasks, verifies TaskList component renders 10+ cards

test_error_recovery_when_backend_unreachable
// Disconnects backend, verifies fallback message displayed in ChatGPT
```

---

### 🔐 OAuth 2.1 Implementation (Critical Addition)

**Why OAuth 2.1?**: Required by Apps SDK for user authentication and authorization

#### FastAPI Backend - OAuth Endpoints

**Discovery Endpoint** (`backend/app/oauth/discovery.py`):
```python
@router.get("/.well-known/oauth-authorization-server")
async def oauth_discovery():
    """OAuth 2.1 AS metadata (RFC 8414)"""
    return {
        "issuer": "https://api.yourdomain.com",
        "authorization_endpoint": "https://api.yourdomain.com/oauth/authorize",
        "token_endpoint": "https://api.yourdomain.com/oauth/token",
        "registration_endpoint": "https://api.yourdomain.com/oauth/register",
        "jwks_uri": "https://api.yourdomain.com/.well-known/jwks.json",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic"],
        "scopes_supported": ["tasks:read", "tasks:write", "openid", "profile"]
    }
```

**Authorization Endpoint** (`backend/app/oauth/authorize.py`):
```python
@router.get("/oauth/authorize")
async def authorize(
    client_id: str,
    redirect_uri: str,
    response_type: str,  # Must be "code"
    scope: str,  # Space-separated scopes
    state: str,  # CSRF protection
    code_challenge: str | None = None,  # PKCE (recommended)
    code_challenge_method: str = "S256"
):
    """OAuth authorization flow - redirects to login if not authenticated"""
    # 1. Validate client_id against registered clients
    # 2. Show login form if user not authenticated
    # 3. After login, show consent screen with requested scopes
    # 4. Generate authorization code
    # 5. Redirect to redirect_uri with code + state
    pass
```

**Token Endpoint** (`backend/app/oauth/token.py`):
```python
@router.post("/oauth/token")
async def token(
    grant_type: str,  # "authorization_code" or "refresh_token"
    code: str | None = None,  # Authorization code
    redirect_uri: str | None = None,
    client_id: str,
    client_secret: str,
    refresh_token: str | None = None,
    code_verifier: str | None = None  # PKCE verifier
):
    """Exchange authorization code for access token"""
    if grant_type == "authorization_code":
        # 1. Verify code is valid and not expired
        # 2. Verify redirect_uri matches
        # 3. Verify code_verifier (if PKCE used)
        # 4. Generate access_token (JWT) + refresh_token
        # 5. Return tokens
        return {
            "access_token": "eyJ...",  # JWT with user_id + scopes
            "token_type": "Bearer",
            "expires_in": 86400,  # 24 hours
            "refresh_token": "...",  # 30 days
            "scope": "tasks:read tasks:write"
        }
    elif grant_type == "refresh_token":
        # Verify refresh token, issue new access token
        pass
```

**JWKS Endpoint** (`backend/app/oauth/jwks.py`):
```python
@router.get("/.well-known/jwks.json")
async def jwks():
    """JSON Web Key Set for token verification"""
    # Return public keys used to sign JWTs
    return {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "kid": "2024-11-02",
                "n": "...",  # RSA public key modulus
                "e": "AQAB"  # RSA public key exponent
            }
        ]
    }
```

#### Python MCP Server - Token Verification

**JWT Verification** (`mcp_server/auth/jwt_verifier.py`):
```python
import httpx
from jose import jwt, JWTError
from fastapi import HTTPException

class JWTVerifier:
    def __init__(self, jwks_url: str):
        self.jwks_url = jwks_url
        self.keys_cache = None

    async def verify_token(self, token: str, required_scopes: list[str]) -> dict:
        """Verify JWT token and check scopes"""
        try:
            # 1. Fetch JWKS (cache for 1 hour)
            if not self.keys_cache:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(self.jwks_url)
                    self.keys_cache = resp.json()

            # 2. Decode JWT header to get kid (key ID)
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header["kid"]

            # 3. Find matching key
            key = next(k for k in self.keys_cache["keys"] if k["kid"] == kid)

            # 4. Verify signature, issuer, audience, expiration
            payload = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                issuer="https://api.yourdomain.com",
                audience="https://your-domain.com/mcp"
            )

            # 5. Check scopes
            token_scopes = payload.get("scope", "").split()
            if not all(scope in token_scopes for scope in required_scopes):
                raise HTTPException(401, "Insufficient scopes")

            return payload  # Contains user_id, scopes, etc.

        except JWTError:
            raise HTTPException(401, "Invalid token")
```

**MCP Tool with OAuth** (`mcp_server/tools/get_best_task.py`):
```python
from fastmcp import FastMCP

mcp = FastMCP("MindFlow")

@mcp.tool(security="oauth2", scopes=["tasks:read"])
async def get_best_task(auth_token: str) -> dict:
    """Get your highest priority task based on AI scoring.

    This tool requires authentication and the 'tasks:read' scope.
    """
    # 1. Verify token
    verifier = JWTVerifier(jwks_url="https://api.yourdomain.com/.well-known/jwks.json")
    user = await verifier.verify_token(auth_token, ["tasks:read"])

    # 2. Call FastAPI backend
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.yourdomain.com/api/tasks/best",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        task = response.json()

    # 3. Load embedded component
    with open("assets/component.js") as f:
        component_code = f.read()

    # 4. Return with widget metadata
    return {
        "task": task,
        "_meta": {
            "openai/outputTemplate": component_code,  # Embedded React component
            "openai/displayMode": "inline",
            "openai/widgetId": f"task-{task['id']}"
        }
    }

@mcp.tool(security="noauth")  # Read-only, no auth required
async def get_task_count() -> dict:
    """Get total count of pending tasks (no authentication required)."""
    # This tool can be called without OAuth
    pass
```

---

### 📱 Display Mode Strategy (Complete)

**All 4 Display Modes**:

| Mode | Use Case | Size Constraints | Max Actions | Best For |
|------|----------|------------------|-------------|----------|
| **inline** | Default cards | 300-500px height | 2 buttons | Single tasks, quick actions |
| **inline-carousel** | Browsing items | 300-400px height | 2 per card | 3-8 similar tasks |
| **fullscreen** | Rich interactions | Full screen | Unlimited | Editing, complex forms |
| **picture-in-picture** | Persistent state | Floating window | Unlimited | Games, collaboration |

**Decision Matrix**:
```python
def get_display_mode(tool_name: str, result_count: int, action_type: str) -> str:
    """Determine optimal display mode for tool response."""

    if tool_name == "mindflow.get_best_task":
        return "inline"  # Single card, simple actions

    elif tool_name == "mindflow.get_pending_tasks":
        if result_count <= 8:
            return "inline-carousel"  # Swipeable card list
        else:
            return "fullscreen"  # Too many for carousel

    elif tool_name == "mindflow.create_task":
        return "fullscreen"  # Rich form with date pickers

    elif tool_name == "mindflow.edit_task":
        return "fullscreen"  # Multi-field editing

    else:
        return "inline"  # Safe default
```

**Component Implementation**:
```typescript
// App.tsx - Display mode router
function App() {
  const { displayMode } = useOpenAiGlobal();

  switch (displayMode) {
    case 'inline':
      return <TaskCard />;
    case 'inline-carousel':
      return <TaskList />;
    case 'fullscreen':
      return <TaskEditor />;
    default:
      return <TaskCard />;
  }
}
```

---

### 🔄 State Management (3-Tier Architecture)

**Type 1: Business Data (Server Authority)**:
- **Ownership**: FastAPI backend
- **Lifespan**: Long-lived (database)
- **Examples**: Task title, due date, priority, completion status
- **Update Pattern**: Server-driven; widget reads from `window.openai.toolOutput`

**Type 2: UI State (Widget Ephemeral)**:
- **Ownership**: React component
- **Lifespan**: Duration of widget instance
- **Examples**: Expanded panels, selected filters, sort order
- **Storage**: `window.openai.setWidgetState(widgetId, state)` (max 4k tokens)

**Type 3: Cross-Session State (Backend Persistent)**:
- **Ownership**: FastAPI backend (user preferences table)
- **Lifespan**: Persists across conversations and devices
- **Examples**: Default view mode, saved filters, workspace selection
- **Access**: Via authenticated API calls; requires OAuth

**Implementation Example**:
```typescript
// state-manager.ts
interface StateManager {
  // Business data (read-only from tool output)
  getTaskData(): Task;

  // UI state (widget-scoped)
  getUIState(): { filter: string; sortBy: string };
  setUIState(state: { filter?: string; sortBy?: string }): void;

  // Cross-session state (backend API)
  getUserPreferences(): Promise<UserPreferences>;
  saveUserPreferences(prefs: UserPreferences): Promise<void>;
}

// Usage in component
function TaskList() {
  const task = useToolOutput();  // Business data
  const [uiState, setUIState] = useWidgetState();  // UI state
  const [prefs] = useUserPreferences();  // Cross-session state

  return (
    <div>
      <FilterBar
        currentFilter={uiState.filter}
        onChange={(f) => setUIState({ filter: f })}
      />
      <TaskCard task={task} />
    </div>
  );
}
```

**State Size Limits**:
- Widget state: **< 4k tokens** (enforced by ChatGPT)
- Strategies for large datasets:
  - Store IDs only, fetch full data via `callTool`
  - Paginate results
  - Use backend storage for large state

---

### 🎨 Design Guidelines & Constraints

**MUST Follow** (enforced during ChatGPT review):

1. **Typography**:
   ```css
   /* ✅ REQUIRED: Inherit system fonts */
   font-family: inherit;
   font-size: inherit;

   /* ❌ FORBIDDEN: Custom fonts */
   font-family: 'Custom Font', sans-serif;  /* REJECTED */
   ```

2. **Colors**:
   ```css
   /* ✅ ALLOWED: System-defined colors */
   color: var(--text-primary);
   background: var(--surface-primary);

   /* ❌ FORBIDDEN: Custom brand colors in backgrounds */
   background: #FF6B6B;  /* REJECTED if used for backgrounds */

   /* ✅ ALLOWED: Brand colors in logos/icons only */
   <img src="logo.svg" style="fill: #FF6B6B" />  /* OK */
   ```

3. **Spacing**: Use consistent margins/padding
   ```css
   /* ✅ System grid values */
   padding: 8px 12px;  /* or 12px 16px or 16px 20px */

   /* ❌ Random values */
   padding: 7px 13px;  /* Inconsistent */
   ```

4. **Icons**: Monochromatic, outlined style
   ```tsx
   /* ✅ Simple, outlined icons */
   <CheckCircleIcon stroke="currentColor" fill="none" />

   /* ❌ Filled or multi-color icons */
   <CheckCircleIcon fill="#00FF00" />  /* REJECTED */
   ```

5. **Actions in Inline Cards**: Maximum 2 primary buttons
   ```tsx
   /* ✅ OK: 2 actions */
   <Button>Complete</Button>
   <Button>Snooze</Button>

   /* ❌ REJECTED: 3+ actions in inline */
   <Button>Complete</Button>
   <Button>Snooze</Button>
   <Button>Edit</Button>  /* Too many */
   ```

6. **No Internal Scrolling in Inline Mode**:
   ```tsx
   /* ❌ FORBIDDEN in inline */
   <div style="overflow-y: scroll; height: 300px">
     {tasks.map(...)}  /* REJECTED */
   </div>

   /* ✅ Use carousel or fullscreen instead */
   displayMode: "inline-carousel"  /* For scrolling lists */
   ```

---

### 📊 Metadata Optimization Strategy

**Why Critical**: Tool descriptions control when ChatGPT calls your app

#### Best Practices

**1. Domain-Paired Naming**:
```python
# ✅ GOOD: Namespaced tool names
@mcp.tool()
async def mindflow_get_best_task():  # or "mindflow.get_best_task"
    """Get the user's highest priority task from MindFlow."""
    pass

# ❌ BAD: Generic names
@mcp.tool()
async def get_task():  # Conflicts with other apps
    pass
```

**2. "Use This When..." Descriptions**:
```python
@mcp.tool()
async def mindflow_get_best_task():
    """Get the user's highest priority task from MindFlow.

    Use this when:
    - User asks "what should I work on?"
    - User asks "what's my top priority?"
    - User wants AI-powered task recommendations

    Do NOT use for:
    - Creating new tasks (use mindflow.create_task)
    - Setting reminders (out of scope)
    """
    pass
```

**3. Parameter Examples & Constraints**:
```python
from pydantic import Field

@mcp.tool()
async def mindflow_create_task(
    title: str = Field(..., description="Task title", example="Review PR #123"),
    priority: int = Field(3, ge=1, le=5, description="Priority 1-5, where 5 is highest"),
    due_date: str | None = Field(None, description="ISO 8601 datetime", example="2025-11-05T14:00:00Z")
):
    """Create a new task in MindFlow."""
    pass
```

**4. Read-Only Hints**:
```python
@mcp.tool(readOnlyHint=True)
async def mindflow_get_pending_tasks():
    """List all pending tasks (read-only, no side effects)."""
    pass

@mcp.tool(readOnlyHint=False)
async def mindflow_complete_task(task_id: str):
    """Mark a task as completed (write operation, requires confirmation)."""
    pass
```

#### Testing & Optimization Workflow

**Golden Prompt Dataset** (20-50 test cases):
```python
GOLDEN_PROMPTS = [
    # Direct references
    "What should I work on?",
    "Show me my top priority task",
    "Get my best task from MindFlow",

    # Indirect requests
    "I'm ready to be productive, what's next?",
    "Help me prioritize my work",

    # Negative cases (should NOT trigger)
    "Set a reminder for 3pm",  # Not our domain
    "Create a calendar event",  # Not our domain

    # Edge cases
    "Show me all my tasks",  # get_pending_tasks, not get_best_task
]
```

**Weekly Review Process**:
1. Run golden prompt dataset against production
2. Track precision (correct tool called) and recall (tool called when should be)
3. Analyze false positives (wrong tool called) and false negatives (missed calls)
4. Iterate metadata changes ONE AT A TIME
5. Document changes with timestamps and diffs

---

### 🚀 Deployment Strategy

**Requirements**:
1. **HTTPS Public Endpoint**: MCP server must be publicly accessible
2. **SSL Certificate**: Required for production
3. **CORS**: Must allow ChatGPT origins

#### Development: ngrok Tunnel

```bash
# Terminal 1: Start MCP server locally
cd mcp_server
uv run python server.py  # Runs on localhost:3000

# Terminal 2: Expose with ngrok
ngrok http 3000
# Output: https://abc123.ngrok.io → localhost:3000

# Terminal 3: Update ChatGPT connector
# In ChatGPT Settings → Connectors → Create
# Connector URL: https://abc123.ngrok.io/mcp
```

**Alternative: Cloudflare Tunnel** (persistent URLs):
```bash
cloudflared tunnel --url http://localhost:3000
```

#### Production: DigitalOcean Deployment

**Option 1: Same Droplet as FastAPI** (recommended for MVP):
```
DigitalOcean Droplet
├── Port 8000: FastAPI Backend
├── Port 3000: Python MCP Server
└── Nginx:
    ├── api.yourdomain.com → :8000 (FastAPI)
    └── mcp.yourdomain.com → :3000 (MCP Server)
```

**Nginx Config** (`/etc/nginx/sites-available/mcp`):
```nginx
server {
    listen 443 ssl http2;
    server_name mcp.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/mcp.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mcp.yourdomain.com/privkey.pem;

    location /mcp {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Systemd Service** (`/etc/systemd/system/mindflow-mcp.service`):
```ini
[Unit]
Description=MindFlow MCP Server
After=network.target mindflow.service

[Service]
Type=simple
User=deploy
WorkingDirectory=/opt/mindflow/mcp_server
Environment="PATH=/opt/mindflow/mcp_server/.venv/bin:$PATH"
ExecStart=/opt/mindflow/mcp_server/.venv/bin/python server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**Option 2: Separate Service** (for scale):
- Deploy MCP server to Cloud Run, Lambda, or separate droplet
- Benefits: Independent scaling, isolated failures
- Cost: +$5-10/month

---

### ✅ Compliance Checklist & Review Process

**Pre-Submission Requirements**:

- [ ] **Developer Verification**: Identity verification complete
- [ ] **Support Contact**: Active email address provided
- [ ] **Demo Credentials**: Full-featured test account for review
- [ ] **Production Ready**: No beta/demo disclaimers
- [ ] **Accurate Metadata**: Tool names, descriptions match actual functionality
- [ ] **Age Appropriate**: Suitable for 13+ (no NSFW content)

**Privacy & Data Protection**:

- [ ] **Minimal Data Collection**: Only request necessary fields
- [ ] **No Prohibited Data**: No PCI, PHI, government IDs, passwords, raw location
- [ ] **No Surveillance**: No tracking or behavioral profiling without disclosure
- [ ] **Write Actions Labeled**: All mutations have clear labels and require confirmation
- [ ] **No Chat Log Reconstruction**: Cannot pull or store full conversation history

**Functional Requirements**:

- [ ] **Stability**: Thoroughly tested, no crashes or errors
- [ ] **Clear Error Messages**: User-friendly fallbacks for failures
- [ ] **Responsive**: Low latency (<500ms tool calls)
- [ ] **As Described**: Functions exactly as metadata describes
- [ ] **No Hidden Actions**: Transparent about all operations

**Design Compliance** (Apps SDK):

- [ ] **System Fonts**: Inherits ChatGPT typography (no custom fonts)
- [ ] **System Colors**: Uses system palettes (branding via logos only)
- [ ] **Inline Actions**: Max 2 primary buttons in inline mode
- [ ] **No Internal Scrolling**: Inline cards auto-fit content
- [ ] **Accessible**: Keyboard navigation, screen reader support

**OAuth & Security**:

- [ ] **OAuth 2.1**: Discovery endpoints implemented
- [ ] **JWKS**: Public keys exposed for token verification
- [ ] **Scopes**: Per-tool security declarations
- [ ] **Transparent Login**: Clear permission requests
- [ ] **No Machine-to-Machine**: All requests are user sessions

**Post-Approval**:

- ⚠️ **Metadata Locked**: Tool names/signatures cannot change without resubmission
- ⚠️ **Ongoing Compliance**: Violations lead to removal
- ⚠️ **Support Responsiveness**: Must respond to user reports

**Rejection Reasons to Avoid**:
- Beta/demo quality
- Misleading descriptions
- Custom fonts or non-system colors
- More than 2 actions in inline cards
- Prohibited data collection
- Poor error handling
- Missing OAuth endpoints

---

### 🧪 ChatGPT Integration Testing

**Mock window.openai API**:
```typescript
// tests/mocks/openai-api.ts
export const mockOpenAi = {
  toolOutput: { task: { id: "123", title: "Test task", priority: 5 } },
  theme: "light",
  locale: "en-US",

  callTool: jest.fn(async (name, params) => {
    // Simulate MCP server response
    return { success: true };
  }),

  setWidgetState: jest.fn((widgetId, state) => {
    // Store state in mock
  }),

  getWidgetState: jest.fn((widgetId) => {
    return { filter: "high-priority" };
  }),

  requestDisplayMode: jest.fn((mode) => {
    console.log(`Display mode requested: ${mode}`);
  })
};

// Inject into window
(global as any).window = { openai: mockOpenAi };
```

**Integration Test Example**:
```typescript
import { render, fireEvent, waitFor } from '@testing-library/react';
import TaskCard from '../components/TaskCard';
import { mockOpenAi } from './mocks/openai-api';

test('complete button calls MCP tool and updates state', async () => {
  const { getByText } = render(<TaskCard />);

  const completeButton = getByText('Complete');
  fireEvent.click(completeButton);

  await waitFor(() => {
    expect(mockOpenAi.callTool).toHaveBeenCalledWith(
      'mindflow.complete_task',
      { taskId: '123' }
    );
  });

  expect(mockOpenAi.setWidgetState).toHaveBeenCalledWith(
    'task-card-123',
    { completed: true }
  );
});
```

---

## 🎨 PHASE 9B: LANDING PAGE ENHANCEMENT (Post-Apps SDK)

**Timeline**: 2 days (after Apps SDK complete)
**Effort**: 8 hours
**Business Value**: Showcase interactive UX, increase conversion

### Current State
- ✅ `frontend/index.html` exists (17KB, Phase 8B)
- ✅ Animated ChatGPT conversation demo
- ✅ Dual CTAs to Custom GPT
- ✅ Mobile responsive

### Enhancement Plan

**What to Add**:
1. **Apps SDK Screenshots**: Show interactive task cards in ChatGPT
2. **Feature Comparison**: Text-based vs interactive UX
3. **Video Demo**: 30-second screen recording of Apps SDK in action
4. **Updated CTA**: "Try Interactive Task Cards in ChatGPT"

**Files to Modify**:
```
frontend/index.html                        # Add Apps SDK section
frontend/assets/
  ├── screenshots/
  │   ├── task-card-demo.png              # Interactive card screenshot
  │   ├── complete-action.gif             # Button click animation
  │   └── chatgpt-integration.mp4         # Video demo
  └── styles/
      └── animations.css                   # New animations for demos
```

#### Functions to Add

**index.html** (JavaScript inline):
```javascript
function playVideoOnScroll(videoElement: HTMLVideoElement): void
// Plays video demo when scrolled into viewport using IntersectionObserver.

function trackCTAClick(ctaType: "hero" | "footer" | "apps-sdk"): void
// Sends analytics event (via Plausible) when CTA clicked, differentiates button types.

function toggleFeatureComparison(view: "text" | "interactive"): void
// Switches between text-based and Apps SDK demo views using CSS classes.
```

#### Sections to Update

**Hero Section** (update):
```html
<h1>Your AI Task Manager Lives in ChatGPT</h1>
<p>Interactive task cards with one-click actions. No app switching.</p>
<a href="..." class="cta-button">
  Try Interactive Cards in ChatGPT →
</a>
```

**New Section: Apps SDK Demo**:
```html
<section class="apps-sdk-demo">
  <h2>See It in Action</h2>
  <div class="demo-grid">
    <div class="demo-text">
      <p>Ask: "What should I work on?"</p>
      <p>Get visual task cards with inline actions</p>
    </div>
    <div class="demo-visual">
      <video autoplay loop muted playsinline>
        <source src="assets/chatgpt-integration.mp4" type="video/mp4">
      </video>
    </div>
  </div>
</section>
```

**Feature Comparison Table**:
```html
<section class="comparison">
  <table>
    <tr>
      <th>Feature</th>
      <th>Text Mode</th>
      <th>Interactive Cards</th>
    </tr>
    <tr>
      <td>Get recommendations</td>
      <td>✅</td>
      <td>✅</td>
    </tr>
    <tr>
      <td>Visual priority</td>
      <td>❌</td>
      <td>✅</td>
    </tr>
    <tr>
      <td>One-click complete</td>
      <td>❌</td>
      <td>✅</td>
    </tr>
  </table>
</section>
```

#### Tests to Add

```javascript
test_apps_sdk_section_renders_above_fold
// Verifies Apps SDK demo visible without scrolling on desktop

test_video_auto_plays_when_scrolled_into_view
// Simulates scroll, asserts video.play() called

test_feature_comparison_toggle_switches_views
// Clicks toggle, verifies correct demo visible

test_cta_tracking_fires_different_events
// Clicks each CTA, verifies unique analytics events sent

test_mobile_video_displays_poster_image_not_autoplay
// On mobile viewport, asserts video has poster, no autoplay
```

---

## 🖥️ PHASE 11: FULL WEB FRONTEND (Future - User Demand Driven)

**Timeline**: 4-6 weeks (if 100+ users request it)
**Effort**: 160-240 hours
**Business Value**: Serve non-ChatGPT users, power user features
**Trigger**: 100+ support requests for "web access" or "standalone app"

### Why Deferred?

**First Principles**:
- **Core Mission**: Task recommendations via ChatGPT
- **Apps SDK**: Provides full functionality IN ChatGPT
- **Web Frontend**: Only needed for minority use cases

**Pareto Analysis**:
- **Apps SDK**: 20% effort, 60% value (enhances core)
- **Web Frontend**: 80% effort, 20% value (serves edge cases)

**Decision**: Build ONLY if users explicitly ask for it.

### When to Build

**Triggers**:
1. 100+ users request "I want to manage tasks without ChatGPT"
2. Enterprise customers need team collaboration (not possible in GPT)
3. Offline access required (PWA for mobile)
4. Advanced filtering/reporting needed (beyond ChatGPT capabilities)

### Architecture (Based on archived design)

**Tech Stack**:
- **Frontend**: LIT web components (50KB bundle)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + custom design tokens
- **Build**: Vite
- **State**: Context API + local storage
- **Real-time**: WebSocket connection to FastAPI
- **Deployment**: Cloudflare Pages (same as landing page)

**Files to Create** (from `docs/archive/custom-views-todoist-ui.md`):

```
frontend/web-app/
├── src/
│   ├── components/
│   │   ├── upcoming-view.ts              # Main view (1,323 lines from archive)
│   │   ├── week-navigator.ts             # Horizontal calendar
│   │   ├── task-card.ts                  # Individual task display
│   │   ├── task-filters.ts               # Filtering UI
│   │   └── app-shell.ts                  # Navigation shell
│   ├── services/
│   │   ├── task-service.ts               # API client (FastAPI)
│   │   ├── websocket.ts                  # Real-time sync
│   │   └── auth-service.ts               # Login/logout
│   ├── types/
│   │   └── api.ts                        # TypeScript types
│   ├── styles/
│   │   └── main.css                      # Tailwind + custom styles
│   └── main.ts                           # App entry point
├── package.json
├── tsconfig.json
├── vite.config.ts
└── index.html                            # SPA shell
```

#### Core Components (from archive)

**upcoming-view.ts** (Main View):
```typescript
class UpcomingView extends LitElement
// Displays week navigator + date-grouped task list with sticky headers.
// Handles drag-drop rescheduling, swipe gestures, real-time updates via WebSocket.

async function loadTasks(): Promise<void>
// Fetches pending tasks from FastAPI, groups by date, sorts by priority.

function groupTasksByDate(): void
// Maps tasks to date buckets (Today, Tomorrow, Mon Oct 31, etc.), stores in Map.

function setupRealTimeSync(): void
// Subscribes to WebSocket events (task_created, task_updated, task_deleted), updates UI.
```

**week-navigator.ts**:
```typescript
class WeekNavigator extends LitElement
// Horizontal scrolling calendar showing 7 days with task count indicators.

function generateWeeks(): void
// Creates Date[] for current week + 2 weeks ahead, enables infinite scroll.

function isToday(date: Date): boolean
// Highlights current day with active styling.
```

**task-card.ts**:
```typescript
class TaskCard extends LitElement
// Renders draggable task card with priority badge, title, due date, tags, swipe actions.

function handleDragStart(event: DragEvent): void
// Captures task ID in dataTransfer, adds dragging class for visual feedback.

async function handleCompleteTask(): Promise<void>
// Calls PUT /api/tasks/{id} with status=completed, dispatches event to parent.
```

#### Gesture Support

**Drag-Drop Rescheduling**:
```typescript
function setupDragDrop(): void
// Attaches dragover/drop listeners to date groups, updates task.due_date on drop.

async function rescheduleTask(taskId: string, newDate: string): Promise<void>
// Calls FastAPI PUT endpoint, optimistically updates UI, rolls back on error.
```

**Swipe Actions** (mobile):
```typescript
function setupGestureDetection(): void
// Detects horizontal swipes (touchstart/touchmove), reveals action buttons (complete, snooze).

function handleSwipeRight(taskElement: HTMLElement): void
// Marks task complete via API, animates card removal.
```

#### Real-Time Sync

**websocket.ts**:
```typescript
class WebSocketClient
// Connects to ws://localhost:8000/ws/tasks, handles reconnection with exponential backoff.

function handleMessage(message: WebSocketMessage): void
// Parses event type (task_updated, etc.), triggers callbacks, updates component state.

function attemptReconnect(): void
// Retries connection up to 5 times with increasing delay (1s, 2s, 4s, 8s, 16s).
```

#### Tests

```typescript
test_upcoming_view_groups_tasks_by_date_correctly
// Creates 10 tasks across 5 days, verifies 5 date groups rendered

test_week_navigator_highlights_today_with_active_class
// Asserts today's date has .active class, tomorrow does not

test_drag_task_to_tomorrow_updates_due_date
// Simulates drag from Today to Tomorrow, verifies API called with new date

test_swipe_right_completes_task_and_removes_card
// Simulates touch gesture, asserts task marked completed, card animates out

test_websocket_task_updated_event_refreshes_card
// Sends mock WebSocket message, verifies task card re-renders with new data

test_empty_state_displays_when_no_tasks_pending
// Clears task list, asserts "No tasks" message and emoji displayed

test_virtual_scrolling_handles_500_tasks_smoothly
// Creates 500 tasks, verifies only visible cards rendered (performance test)
```

### Implementation Phases (if triggered)

**Phase 11A: Core Views** (2 weeks):
- Upcoming view with week navigator
- Task cards with basic actions
- Basic filtering (priority, status)

**Phase 11B: Advanced Interactions** (1 week):
- Drag-drop rescheduling
- Swipe gestures
- Keyboard shortcuts

**Phase 11C: Real-Time Sync** (1 week):
- WebSocket integration
- Optimistic updates
- Conflict resolution

**Phase 11D: Polish** (1-2 weeks):
- Empty states, loading states
- Error handling, offline mode
- Accessibility (WCAG AA)
- Performance optimization (virtual scrolling)

---

## 📋 UPDATED IMPLEMENTATION ROADMAP

### ✅ COMPLETE
- Phase 1-7: Backend API, database, auth, scoring, CI/CD
- Phase 8A: Enhanced authentication (password reset, refresh tokens)
- Phase 8B: Landing page (text-based ChatGPT focus)

### 🔄 IN PROGRESS
- **Phase 8C: Production Deployment** (IMMEDIATE - 2 days)
  - Deploy FastAPI to DigitalOcean
  - Migrate Custom GPT to production
  - Setup monitoring

### 📅 PLANNED (Post-Launch)
- **Phase 9A: OpenAI Apps SDK** (Week 3 - 5 days, 28 hours)
  - React task card components
  - MCP server integration
  - Interactive ChatGPT UX

- **Phase 9B: Landing Page Enhancement** (Week 4 - 2 days, 8 hours)
  - Apps SDK screenshots/video
  - Feature comparison table
  - Updated CTAs

- **Phase 11: Web Frontend** (DEFERRED - 4-6 weeks, IF requested)
  - Full LIT-based web app
  - Todoist-style UI
  - Real-time sync

---

## 🎯 DECISION TREE

```
Launch MindFlow?
├─ YES → Phase 8C: Deploy (2 days) → Get 10-100 users
│   └─ Users love it?
│       ├─ YES → Phase 9A: Apps SDK (5 days) → Enhanced UX
│       │   └─ 50+ users request web access?
│       │       ├─ YES → Phase 11: Build web app (6 weeks)
│       │       └─ NO → Done, iterate on Apps SDK
│       └─ NO → Pivot or shut down
└─ NO → Keep planning forever (not recommended 😉)
```

---

**Version**: 9.0.0
**Philosophy**: First Principles + Pareto Principle + User Demand
**Mantra**: "Ship, learn, iterate. Build what users actually want."

Let's ship it. 🚀
