# MindFlow: 1-Page Architecture & Data Flow Summary

## System Overview

**MindFlow** is an AI-first task manager that combines GPT-4 Sonnet (natural language interface), Google Apps Script (REST backend), and Google Sheets (data store) to enable users to manage tasks through conversation.

---

## Complete Data Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                          USER                                    │
│              (Types natural language query)                      │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼ "What should I do next?"
┌──────────────────────────────────────────────────────────────────┐
│               CUSTOM GPT (OpenAI Function Calling)                │
│  • Interprets intent (e.g., GET_BEST_TASK, CREATE_TASK)         │
│  • Generates JSON payload for API                                │
│  • Returns natural language response to user                     │
└────────────────────────┬─────────────────────────────────────────┘
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
    ▼                    ▼                    ▼
POST /create         GET /best-task       POST /complete
POST /update         POST /snooze         GET /query
    │                    │                    │
    └────────────────────┼────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│              GOOGLE APPS SCRIPT (doPost/doGet Handlers)          │
│  • Validates input (type, range, format)                         │
│  • Computes relevance scores (if query = /best-task)             │
│  • Executes CRUD on Sheets                                       │
│  • Logs all operations to audit trail                            │
└────────────────────────┬─────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼ (Read/Write)                  ▼ (Append)
    ┌──────────────┐              ┌──────────────┐
    │  Tasks      │              │   Logs       │
    │  Sheet      │              │   Sheet      │
    │ (Data Model)│              │ (Observability)
    └──────┬───────┘              └──────────────┘
           │
           ▼
    ┌──────────────────────────────────────────┐
    │    RELEVANCE SCORING (Deterministic)     │
    │  score = 0.40×priority + 0.35×urgency    │
    │        + 0.15×context + 0.10×momentum    │
    └──────────────────────────────────────────┘
           │
           ▼ (Ranked tasks)
    Return best task + explanation
           │
           └──────────► Back to GPT ──► Natural language response
```

---

## Data Model: Tasks Table

| Column | Type | Purpose |
|--------|------|---------|
| `id` | UUID | Primary key |
| `title` | String | Task name |
| `description` | String | Details |
| `status` | Enum | pending / in_progress / completed / snoozed |
| `priority` | 1–5 | 5 = urgent |
| `due_date` | ISO8601 | When it's due |
| `snoozed_until` | ISO8601 | Hiding until this time |
| `created_at` | ISO8601 | Audit trail |
| `updated_at` | ISO8601 | Audit trail |
| `tags` | String | Labels (e.g., "work,morning") |

**Schema Validation:**
- `status` ∈ {pending, in_progress, completed, snoozed}
- `priority` ∈ {1, 2, 3, 4, 5}
- `due_date`, `snoozed_until` are valid ISO8601 or null

---

## Logs Table (Observability)

| Column | Purpose |
|--------|---------|
| `timestamp` | When request arrived |
| `query` | User's natural language input |
| `action` | Parsed operation (CREATE_TASK, GET_BEST_TASK, etc.) |
| `status_code` | HTTP response (200, 400, 500) |
| `task_id` | Related task (if applicable) |
| `error_message` | Error detail (if status_code ≥ 400) |
| `request_id` | UUID for distributed tracing |

**Purpose:** Audit trail + debugging GPT interactions

---

## Relevance Scoring Algorithm

Determines the "best task right now" using a **weighted formula**:

```
score = (0.40 × priority_score) 
      + (0.35 × urgency_score) 
      + (0.15 × context_score) 
      + (0.10 × momentum_score)

Priority Score:  priority_level × 20  (range: 0–100)

Urgency Score:   Based on hours until due_date
  • Overdue          → 100
  • < 4 hours        → 90
  • < 24 hours       → 75
  • < 72 hours       → 50
  • > 10 days        → Linear decay to 0

Context Score:   50 + time-of-day bonus (e.g., "morning" task at 08:00 → +20)

Momentum Score:  Penalizes/rewards task state
  • in_progress      → 80 (don't lose focus)
  • pending for days → 20–100 (age encourages completion)
```

**Example:**
- Task: "Review Q4 metrics"
- Priority: 4, Due: 2025-11-15 (16 days), Status: pending
- Current: 2025-10-30 14:00 UTC

```
priority_score = 80
urgency_score = 30  (16 days away)
context_score = 50
momentum_score = 20

score = 0.40×80 + 0.35×30 + 0.15×50 + 0.10×20 = 52 (moderate)
```

---

## API Endpoints

### 1. Create Task
```
POST /?action=create
{
  "title": "Review metrics",
  "priority": 4,
  "due_date": "2025-11-15T17:00:00Z",
  "description": "Q4 data",
  "tags": "work"
}
→ 201 { id, status: "created" }
```

### 2. Get Best Task
```
GET /?action=best&timezone=Europe/Bucharest
→ 200 { id, title, priority, score, reasoning }
```

### 3. Update Task
```
POST /?action=update&id={task_id}
{ "status": "in_progress", "priority": 5 }
→ 200 { success }
```

### 4. Complete Task
```
POST /?action=complete&id={task_id}
→ 200 { success }
```

### 5. Snooze Task
```
POST /?action=snooze&id={task_id}
{ "snooze_duration": "2h" }
→ 200 { snoozed_until }
```

### 6. Query Tasks
```
GET /?action=query&status=pending&priority=5
→ 200 { tasks: [...] }
```

---

## Error Handling

| Code | Scenario | Example Response |
|------|----------|------------------|
| **201** | Created successfully | `{ id, status: "created" }` |
| **200** | Success | `{ status: "success", data }` |
| **400** | Validation failed | `{ status: "error", errors: [{field, issue}] }` |
| **404** | Task not found | `{ status: "error", message: "Task not found" }` |
| **500** | Server error | `{ status: "error", requestId, message }` |

All errors include:
- `status`: "error"
- `code`: HTTP status code
- `errors`: Array of field-level issues (if validation)
- `requestId`: UUID for tracing

---

## Google Apps Script Implementation

### Core Handler Structure

```javascript
function doPost(e) {
  try {
    const content = JSON.parse(e.postData.contents);
    const action = e.parameter.action;
    
    let result;
    switch(action) {
      case 'create':    result = handleCreateTask(content); break;
      case 'update':    result = handleUpdateTask(content); break;
      case 'complete':  result = handleCompleteTask(content); break;
      case 'snooze':    result = handleSnoozeTask(content); break;
      case 'query':     result = handleQueryTasks(content); break;
      case 'best':      result = handleBestTask(content); break;
      default:          return error(400, "Unknown action");
    }
    
    logRequest(action, 'success', result.code);
    return jsonResponse(result.code, result.data);
  } catch(e) {
    logRequest(action, 'error', 500, e.message);
    return jsonResponse(500, { status: 'error', message: 'Server error' });
  }
}
```

### Task Scoring Implementation

```javascript
function scoreTask(task, now) {
  const p_score = (task.priority || 3) * 20;
  
  let u_score = 0;
  if (task.due_date) {
    const hours = (new Date(task.due_date) - now) / 3600000;
    if (hours < 0) u_score = 100;
    else if (hours < 4) u_score = 90;
    else if (hours < 24) u_score = 75;
    else if (hours < 72) u_score = 50;
    else u_score = Math.max(0, 100 - hours/240);
  }
  
  const c_score = 50;
  const m_score = task.status === 'in_progress' ? 80 : 0;
  
  return Math.round(0.40*p_score + 0.35*u_score + 0.15*c_score + 0.10*m_score);
}
```

---

## Custom GPT Setup

### System Prompt
```
You are MindFlow, an AI task manager. Interpret user intent 
and call the appropriate API action. Ask for missing info 
(due date, priority) before creating tasks. Confirm before 
marking complete or changing status.
```

### OpenAPI Actions
Map the 6 endpoints (create, update, complete, snooze, query, best) 
to the GAS web app URL with action as query parameter.

### Natural Language → API Examples
- "What should I do next?" → `GET /?action=best`
- "Create task: review metrics by Friday" → `POST /?action=create` with parsed title + due_date
- "Done!" → `POST /?action=complete&id={last_task_id}`
- "Snooze 2 hours" → `POST /?action=snooze&id={id}` with duration

---

## Deployment Checklist

- [ ] Create 2 Google Sheets (`tasks`, `logs`)
- [ ] Deploy Google Apps Script as Web App (public)
- [ ] Copy GAS deployment URL
- [ ] Create Custom GPT with system prompt + OpenAPI schema
- [ ] Test manually with curl / Postman
- [ ] Test with GPT: "What should I do next?"
- [ ] Verify data in Sheets after operations

---

## Future: Scaling to Production

### Phase 2: FastAPI + Postgres
```python
# Replace GAS doPost with FastAPI endpoints
@app.post("/tasks")
async def create_task(task: TaskCreate):
    db.add(Task(**task.dict()))
    db.commit()
    return {"id": task.id, "status": "created"}

@app.get("/tasks/best")
async def get_best_task(timezone: str = "UTC"):
    tasks = db.query(Task).filter(Task.status != 'completed')
    best = max(tasks, key=score_task)
    return best
```

### Benefits
- Horizontal scalability (1000+ QPS)
- Richer querying (SQL)
- Multi-tenancy support
- Cost predictability

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **GAS (not FastAPI MVP)** | No ops, free tier, rapid iteration |
| **Google Sheets (not DB)** | Audit trail, familiar UX, observability |
| **Weighted scoring** | Deterministic, explainable, customizable |
| **GPT-4 Sonnet (not GPT-3.5)** | Function calling native, reasoning |
| **OpenAPI schema** | Standard, portable, integrable |

---

## Success Metrics (MVP)

✅ User can ask "What should I do next?" and get a ranked task  
✅ User can create/update/complete tasks via conversation  
✅ Scoring is transparent (shows reasoning)  
✅ All operations logged with request IDs  
✅ Error messages are clear and actionable  
✅ < 2s latency for best-task queries  
✅ Zero data loss (Sheets as backup)  

---

**Ready to build?** Start with Google Apps Script, deploy as web app, create the Custom GPT, and iterate!

**Project:** MindFlow  
**Version:** MVP  
**Date:** October 30, 2025  
**Status:** Implementation Ready
