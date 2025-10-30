# MindFlow – AI-First Task Manager

[![Status](https://img.shields.io/badge/status-MVP-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

> **Natural language task management powered by GPT-4 + deterministic relevance scoring**

MindFlow demonstrates an AI-first vertical slice integrating **Custom GPT** (Actions), **Google Apps Script** (API), and **Google Sheets** (data store) for intelligent task prioritization through conversation.

---

## Project Overview

**Goal:** Enable users to manage tasks using natural language while maintaining transparent, explainable AI recommendations.

**Tech Stack:**
- **Frontend:** Custom GPT with Actions (OpenAI function calling)
- **Backend:** Google Apps Script (REST API)
- **Database:** Google Sheets (tasks + audit logs)
- **Intelligence:** GPT-4 + deterministic scoring algorithm

**Key Features:**
- 🎯 Ask "What should I do next?" → Get intelligently ranked task with reasoning
- ✍️ Create/update tasks conversationally (no forms)
- 📊 Real-time updates visible in Google Sheet
- 🔍 Full audit trail of all operations
- 🧮 Explainable relevance scores (not ML black box)

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    USER (Natural Language)              │
│          "What should I do next?"                       │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│               CUSTOM GPT (Intent Recognition)           │
│  • Parses user intent                                   │
│  • Calls API via Actions (function calling)            │
│  • Returns natural language response                   │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS (JSON)
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
    /create          /best-task       /complete
    /update          /snooze          /query
        │                │                │
        └────────────────┼────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│         GOOGLE APPS SCRIPT (REST API Layer)             │
│  • Input validation                                     │
│  • Relevance scoring engine                            │
│  • CRUD operations on Sheets                           │
│  • Audit logging                                       │
└────────────────────────┬────────────────────────────────┘
                         │ Sheets API
         ┌───────────────┴───────────────┐
         ▼                               ▼
    ┌──────────┐                  ┌──────────┐
    │  Tasks   │                  │   Logs   │
    │  Sheet   │                  │  Sheet   │
    └──────────┘                  └──────────┘
         │
         ▼
    ┌──────────────────────────────────────┐
    │  RELEVANCE SCORING (Deterministic)   │
    │  score = 0.40×priority               │
    │        + 0.35×urgency                │
    │        + 0.15×context                │
    │        + 0.10×momentum               │
    └──────────────────────────────────────┘
```

### Why This Stack?

| Component | Rationale |
|-----------|-----------|
| **Custom GPT** | Natural language interface, built-in function calling, no custom UI needed |
| **Google Apps Script** | Zero server ops, free tier, rapid prototyping, native Sheets integration |
| **Google Sheets** | Transparent data store, real-time collaboration, familiar UX, instant audit trail |
| **Deterministic Scoring** | Explainable (not ML black box), customizable weights, debuggable logic |

---

## Data Model

### Tasks Table

**Sheet Name:** `tasks`

| Column | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `id` | UUID | ✓ | Unique identifier | `a1b2c3d4-e5f6-...` |
| `title` | String(256) | ✓ | Task description | `Review Q4 metrics` |
| `description` | String(1000) | ✗ | Detailed notes | `Analyze quarterly performance...` |
| `status` | Enum | ✓ | Current state | `pending`, `in_progress`, `completed`, `snoozed` |
| `priority` | Integer(1-5) | ✓ | Urgency level | `5` (most urgent) to `1` (low) |
| `due_date` | ISO8601 | ✗ | Deadline | `2025-11-15T17:00:00Z` |
| `snoozed_until` | ISO8601 | ✗ | Hidden until | `2025-10-31T14:00:00Z` |
| `created_at` | ISO8601 | ✓ | Creation time | `2025-10-30T10:00:00Z` |
| `updated_at` | ISO8601 | ✓ | Last modified | `2025-10-30T11:00:00Z` |

**Validation Rules:**
- `status` must be one of: `pending`, `in_progress`, `completed`, `snoozed`
- `priority` must be integer 1-5 (inclusive)
- `title` must be non-empty, max 256 characters
- Date fields must be valid ISO8601 or empty

### Logs Table

**Sheet Name:** `logs`

| Column | Description | Example |
|--------|-------------|---------|
| `timestamp` | When request occurred | `2025-10-30T11:00:00Z` |
| `action` | Operation performed | `GET_BEST_TASK`, `CREATE_TASK` |
| `result` | Outcome | `success`, `error` |
| `status_code` | HTTP status | `200`, `400`, `500` |
| `request_id` | Tracing UUID | `req-xyz-123` |
| `error_message` | Error details (if failed) | `Missing required field: title` |

**Purpose:** Full audit trail for debugging and compliance.

---

## API Endpoints

### Base URL
```
https://script.google.com/macros/s/{YOUR_SCRIPT_ID}/exec
```

### 1. Create Task

**Endpoint:** `POST /?action=create`

**Request:**
```json
{
  "title": "Review Q4 metrics",
  "description": "Analyze quarterly performance data",
  "priority": 4,
  "due_date": "2025-11-15T17:00:00Z"
}
```

**Response (201):**
```json
{
  "status": "success",
  "code": 201,
  "data": {
    "id": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8",
    "title": "Review Q4 metrics",
    "status": "pending",
    "created_at": "2025-10-30T11:00:00Z"
  }
}
```

---

### 2. Get Best Task

**Endpoint:** `GET /?action=best`

**Query Parameters:**
- `timezone` (optional): IANA timezone, default `UTC`

**Response (200):**
```json
{
  "status": "success",
  "code": 200,
  "data": {
    "id": "a1b2c3d4-e5f6",
    "title": "Review Q4 metrics",
    "priority": 4,
    "due_date": "2025-11-15T17:00:00Z",
    "score": 52,
    "reasoning": "High priority (4) + due in 16 days"
  }
}
```

**Response (200 - No Tasks):**
```json
{
  "status": "success",
  "code": 200,
  "data": {
    "status": "no_tasks",
    "message": "No active tasks"
  }
}
```

---

### 3. Update Task

**Endpoint:** `POST /?action=update&id={task_id}`

**Request:**
```json
{
  "status": "in_progress",
  "priority": 5
}
```

**Response (200):**
```json
{
  "status": "success",
  "code": 200,
  "data": {
    "id": "a1b2c3d4-e5f6",
    "updated_at": "2025-10-30T11:05:00Z"
  }
}
```

---

### 4. Complete Task

**Endpoint:** `POST /?action=complete&id={task_id}`

**Response (200):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Task marked as completed"
}
```

---

### 5. Snooze Task

**Endpoint:** `POST /?action=snooze&id={task_id}`

**Request:**
```json
{
  "snooze_duration": "2h"
}
```

Supported durations: `1h`, `2h`, `4h`, `1d`, `2d`, `1w`

**Response (200):**
```json
{
  "status": "success",
  "code": 200,
  "data": {
    "snoozed_until": "2025-10-30T13:00:00Z"
  }
}
```

---

### 6. Query Tasks

**Endpoint:** `GET /?action=query`

**Query Parameters:**
- `status` (optional): Filter by status
- `priority` (optional): Filter by priority
- `limit` (optional): Max results (default 10, max 20)

**Example:**
```
GET /?action=query&status=pending&priority=5
```

**Response (200):**
```json
{
  "status": "success",
  "code": 200,
  "data": [
    {
      "id": "a1b2c3d4-e5f6",
      "title": "Review Q4 metrics",
      "status": "pending",
      "priority": 4,
      "due_date": "2025-11-15T17:00:00Z"
    }
  ]
}
```

---

### Error Responses

All errors follow this format:

```json
{
  "status": "error",
  "code": 400,
  "message": "Validation failed",
  "errors": [
    {
      "field": "title",
      "issue": "Title is required"
    }
  ],
  "requestId": "req-a1b2c3d4"
}
```

**Common Error Codes:**
- `400` – Validation failed (invalid input)
- `404` – Task not found
- `500` – Internal server error

---

## Relevance Logic (Task Scoring)

### Algorithm Overview

The "best task right now" is determined using a **weighted scoring model**:

```
score = (0.40 × priority_score)
      + (0.35 × urgency_score)
      + (0.15 × context_score)
      + (0.10 × momentum_score)
```

### Component 1: Priority Score (0-100)

```
priority_score = priority_level × 20
```

| Priority | Score | Meaning |
|----------|-------|---------|
| 5 | 100 | Urgent (do now) |
| 4 | 80 | High (this week) |
| 3 | 60 | Normal |
| 2 | 40 | Low (can wait) |
| 1 | 20 | Nice-to-have |

### Component 2: Urgency Score (0-100)

Based on **time remaining until due_date**:

| Time Remaining | Urgency Score | Rationale |
|----------------|---------------|-----------|
| Overdue | 100 | Critical! |
| < 4 hours | 90 | Immediate attention |
| < 24 hours | 75 | Today's work |
| < 72 hours | 50 | This week |
| > 10 days | 0-40 | Linear decay |

### Component 3: Context Score (0-100)

Currently fixed at `50`. Future enhancement: time-of-day awareness.

**Planned Logic:**
- Tasks tagged `morning` get +20 boost from 6am-12pm
- Tasks tagged `afternoon` get +20 boost from 12pm-6pm
- Tasks tagged `evening` get +20 boost from 6pm-11pm

### Component 4: Momentum Score (0-100)

Encourages task completion and focus:

| Status | Momentum Score | Rationale |
|--------|----------------|-----------|
| `in_progress` | 80 | Don't lose focus on started work |
| `pending` (old) | 20-40 | Age encourages completion |
| `completed` | 0 | Filtered out |
| `snoozed` | 0 | Filtered out |

---

### Example Calculation

**Task:** "Review Q4 metrics"
- **Priority:** 4 (high)
- **Due:** 2025-11-15 (16 days away)
- **Status:** pending
- **Created:** 4 days ago
- **Current Time:** 2025-10-30 14:00 UTC

**Calculation:**
```
priority_score = 4 × 20 = 80
urgency_score = 30  (16 days away → light decay)
context_score = 50  (no time-of-day tag)
momentum_score = 20  (4 days old)

total_score = (0.40 × 80) + (0.35 × 30) + (0.15 × 50) + (0.10 × 20)
            = 32 + 10.5 + 7.5 + 2
            = 52 (moderate priority)
```

**GPT Response:**
> "You should work on **'Review Q4 metrics'** next. It's high priority (4) and due in 16 days, giving it a score of 52."

---

## Operational Details

### Timezone Handling

- **Default:** All timestamps stored in UTC (ISO8601)
- **Query Support:** `timezone` parameter for `/best` endpoint
- **Apps Script:** Uses `Session.getScriptTimeZone()` for server locale

### Idempotency

- **Task Creation:** Unique `id` (UUID) prevents duplicates
- **Updates:** Based on `id`, safe to retry
- **Completion:** Idempotent (multiple calls = same result)

### Observability

**Every API request logs:**
1. Timestamp (when)
2. Action (what)
3. Result (success/error)
4. Status code (HTTP)
5. Request ID (tracing)
6. Error message (if failed)

**Query logs:**
```javascript
// Open Logs sheet
// Filter by status_code >= 400 to see errors
// Use request_id to trace user sessions
```

### Rate Limiting

**Current:** None (demo only)

**Production Recommendation:** 60 requests/minute per user

---

## Setup & Deployment

### Option 1: Quick Start with Modern Tooling (Recommended) ⚡

**Fastest method using modern Python tooling:**

```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --all-extras

# Seed test data (47 realistic tasks)
make seed

# Run tests
make test
```

**Estimated Time:** 10-15 minutes

**Features:**
- ✅ Modern Python package management with `uv` (blazing fast)
- ✅ Factory-generated realistic test data (60+ test cases)
- ✅ Comprehensive test coverage with pytest
- ✅ Make commands for easy workflow
- ✅ Full documentation with guides

**Guides:**
- [`TESTING.md`](./TESTING.md) - Testing guide with uv commands
- [`CUSTOM_GPT_SETUP.md`](./CUSTOM_GPT_SETUP.md) - Custom GPT configuration

---

### Option 2: Manual Setup

**Step-by-step walkthrough for those who prefer full control:**

**Summary:**
1. Create Google Sheet with `tasks` and `logs` tabs
2. Deploy Google Apps Script as web app
3. Configure Custom GPT with Actions schema
4. Test end-to-end flow

**Estimated Time:** 45 minutes

**Guide:** Follow [`DEPLOYMENT.md`](./DEPLOYMENT.md) for complete manual instructions.

**Choose manual setup if:**
- You want to understand every step in detail
- You're deploying in a restricted environment
- You prefer manual configuration over automation

---

## Testing & Demo

### Manual API Testing

Use `curl` or Postman to test endpoints:

```bash
# Replace YOUR_SCRIPT_ID with your actual deployment ID
BASE_URL="https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec"

# Test 1: Create a task
curl -X POST "${BASE_URL}?action=create" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test task",
    "priority": 3,
    "due_date": "2025-11-01T17:00:00Z"
  }'

# Test 2: Get best task
curl "${BASE_URL}?action=best"

# Test 3: Query tasks
curl "${BASE_URL}?action=query&status=pending"
```

### Conversational Testing (Custom GPT)

**Test Case 1: Empty State**
```
User: What should I do next?
Expected: "You currently have no active tasks! Would you like to create one?"
```

**Test Case 2: Task Creation**
```
User: Create a task to prepare presentation by tomorrow, priority 5
Expected: [Task created, shows confirmation with ID]
```

**Test Case 3: Best Task Query**
```
User: What should I do next?
Expected: "You should work on 'Prepare presentation' - it's urgent (priority 5)
          and due tomorrow (score: 92)."
```

**Test Case 4: Task Completion**
```
User: Mark that task as complete
Expected: "Done! I've marked 'Prepare presentation' as complete."
```

### Verification Checklist

After each test:
- ✅ Check `tasks` sheet for correct data
- ✅ Check `logs` sheet for audit trail
- ✅ Verify `updated_at` timestamps change
- ✅ Confirm GPT responses match reality

---

## Assumptions & Trade-offs

### Design Decisions

| Decision | Assumption | Trade-off | Mitigation |
|----------|-----------|-----------|------------|
| **Public GAS endpoint** | Demo/testing only | Anyone can access | Use OAuth for production |
| **Google Sheets as DB** | < 1000 tasks, single user | Limited scalability | Clear migration path to Postgres |
| **Deterministic scoring** | Explainability > accuracy | No ML personalization | Can add ML layer later |
| **No authentication** | Trusted environment | Security risk | Document hardening steps |
| **Synchronous API** | Low concurrency | May timeout at scale | Use async/queue for production |

### Why NOT Use ML for Scoring?

**Reasons for rule-based approach:**
1. **Explainability:** Users see exact reasoning ("due today + high priority")
2. **Debuggability:** Scores are reproducible and testable
3. **Transparency:** No black box; weights are visible
4. **Speed:** No model inference latency
5. **Simplicity:** No training data needed

**When to switch to ML:**
- User feedback on recommendations
- Personalization (different users = different priorities)
- Context awareness (calendar integration, location, etc.)

---

## Future Improvements

### Phase 2: Feature Enhancements
- [ ] `/metrics` endpoint (tasks completed today, average completion time)
- [ ] Google Calendar integration (block focus time automatically)
- [ ] Recurring tasks (daily standup, weekly review)
- [ ] Task dependencies (can't start B until A is complete)
- [ ] Collaborative tasks (assign to others)

### Phase 3: Production Hardening
- [ ] OAuth 2.0 authentication
- [ ] Rate limiting (60 req/min per user)
- [ ] Input sanitization (XSS prevention)
- [ ] HTTPS enforcement
- [ ] Backup/restore functionality

### Phase 4: Scale Migration

**Transition to FastAPI + Postgres:**

```python
# Equivalent FastAPI endpoint
from fastapi import FastAPI

app = FastAPI()

@app.get("/tasks/best")
async def get_best_task(timezone: str = "UTC"):
    tasks = await db.query(Task).filter(Task.status != 'completed')
    scored = [(t, score_task(t)) for t in tasks]
    best = max(scored, key=lambda x: x[1])
    return {"id": best[0].id, "score": best[1], "reasoning": "..."}
```

**Benefits:**
- 1000+ QPS (vs GAS ~5-10 QPS)
- Rich SQL queries
- Multi-tenancy support
- Background jobs
- WebSocket support (real-time updates)

**Migration Checklist:**
- [ ] Implement Postgres schema
- [ ] Port GAS logic to FastAPI
- [ ] Deploy to Fly.io / Render
- [ ] Update OpenAPI schema (new URL)
- [ ] Sync data from Sheets → Postgres
- [ ] Update Custom GPT config
- [ ] Run integration tests
- [ ] Switch traffic
- [ ] Decommission GAS

---

## Links

### Live Demo
- **Custom GPT:** [Try MindFlow](https://chatgpt.com/g/g-69035fdcdd648191807929b189684451-mindflow) - Live conversational task manager
- **Video Demo:** [Watch 5-minute walkthrough](https://www.loom.com/share/e29f24d461c94396aebe039ef77fb9b7) - See MindFlow in action
- **Google Sheet:** `[Configure your own - see DEPLOYMENT.md]`
- **API Endpoint:** `[Deploy your own - see DEPLOYMENT.md]`

### Documentation
- **Deployment Guide:** [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Architecture Deep-Dive:** [docs/raw/architecture-1pager.md](./docs/raw/architecture-1pager.md)
- **Testing Guide:** [TESTING.md](./TESTING.md)
- **Custom GPT Setup:** [CUSTOM_GPT_SETUP.md](./CUSTOM_GPT_SETUP.md)

### Source Code
- **Google Apps Script:** [src/gas/Code.gs](./src/gas/Code.gs) - Complete API implementation
- **OpenAPI Schema:** [src/gas/openapi-schema-gpt.json](./src/gas/openapi-schema-gpt.json) - GPT-optimized (6 operations, response limits)

---

## Contributing

This is an MVP demonstration project. Contributions welcome for:
- Bug fixes
- Documentation improvements
- Test coverage
- Security hardening
- Performance optimizations

**Not accepting:**
- Major architectural changes (out of scope for MVP)
- ML/AI model integration (future phase)

---

## License

MIT License - see [LICENSE](./LICENSE) for details.

---

## Acknowledgments

Built as a demonstration of AI-first architecture combining:
- OpenAI Custom GPTs (Actions)
- Google Apps Script (serverless backend)
- Google Sheets (transparent data store)
- Deterministic relevance scoring (explainable AI)

---

**Questions?** Open an issue or see [DEPLOYMENT.md](./DEPLOYMENT.md) for setup help.
