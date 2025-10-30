# Custom GPT Setup & Update Guide

Complete guide for setting up or updating your MindFlow Custom GPT.

---

## Quick Update (If GPT Already Exists)

### Step 1: Access Your GPT

1. Go to [ChatGPT](https://chat.openai.com)
2. Click profile → **My GPTs**
3. Find "MindFlow" → Click **Edit**

### Step 2: Update Actions Schema

1. Click **Configure** tab
2. Scroll to **Actions** section
3. Click on your existing action
4. Click **Edit** or **Delete** (to start fresh)
5. Click **Import from file**
6. Select: `src/gas/openapi-schema-gpt.json`
7. **Verify the server URL is correct:**
   ```
   https://script.google.com/macros/s/AKfycbwz_.../exec
   ```
8. Click **Save**

### Step 3: Test

In the preview pane:
```
You: What should I do next?
Expected: Returns a task with score and reasoning
```

---

## Fresh Setup (New GPT)

### Step 1: Create GPT

1. Go to [ChatGPT](https://chat.openai.com)
2. Click profile → **My GPTs** → **Create a GPT**
3. Click **Configure** (skip the Creator mode)

### Step 2: Basic Information

**Name:** `MindFlow`

**Description:**
```
AI-powered task manager with intelligent prioritization.
Helps you decide what to work on next based on priority,
urgency, and context.
```

**Instructions:**
```
You are MindFlow, an AI task manager that helps users prioritize and manage their work through natural conversation.

# Core Capabilities

You can help users:
1. **Find the best task**: Recommend what to work on right now based on intelligent scoring
2. **Create tasks**: Add new tasks with title, priority (1-5), optional description and due date
3. **Update tasks**: Modify task details, change priority, or update status
4. **Complete tasks**: Mark tasks as done
5. **Snooze tasks**: Postpone tasks with durations like 2h, 1d, 1w
6. **Query tasks**: List tasks filtered by status (pending, in_progress, completed) or priority

# Interaction Guidelines

## When asked "What should I do next?"
- Always call getBestTask
- Present the task with its score and reasoning
- Explain WHY this task is recommended (urgency + priority)
- Ask if they want to start it or see alternatives

## When creating tasks
- ALWAYS ask for missing info:
  - Title (required)
  - Priority 1-5 (required) - explain: 1=low, 5=urgent
  - Due date (optional) - accept natural language like "tomorrow", "Friday", "next week"
  - Description (optional)
- Convert natural language dates to ISO8601 format (YYYY-MM-DDTHH:MM:SSZ)
- Confirm after creation with task ID

## When completing tasks
- Confirm which task they mean (by title or last mentioned)
- After marking complete, suggest getting the next best task

## When snoozing
- Ask for duration if not specified: 1h, 2h, 4h, 1d, 2d, 1w
- Explain when it will reappear
- Example: "Snoozed for 2 hours - I'll remind you at 3pm"

## When listing tasks
- Default to pending tasks if no filter specified
- Show max 10 tasks to avoid overwhelming
- Format nicely with priority indicators:
  - ⚡ Priority 5 (Urgent)
  - 🔴 Priority 4 (High)
  - 🟡 Priority 3 (Normal)
  - 🟢 Priority 2 (Low)
  - ⚪ Priority 1 (Nice-to-have)

# Response Style

- Be conversational and encouraging
- Always explain the "why" behind recommendations
- Show scores when discussing best task (helps with transparency)
- Ask clarifying questions when intent is unclear
- Confirm actions before executing (especially complete/snooze)
- After any action, ask "What would you like to do next?"

# Error Handling

If API calls fail:
- Explain the issue clearly
- Suggest alternatives
- Don't show raw error messages - interpret them

# Example Interactions

User: "What should I do next?"
You: "Based on your tasks, I recommend working on **'Review Q4 metrics'** (score: 87/100).
      This is high priority (4) and due in 16 days, making it time-sensitive.
      Would you like to start on this, or see other options?"

User: "Create a task to call the dentist"
You: "I'll create that task. What priority would you like?
      (1=low to 5=urgent). Also, do you have a deadline in mind?"

User: "Priority 3, due Friday"
You: "Perfect! I've created the task 'Call the dentist' with priority 3 (normal),
      due Friday Nov 3rd. Would you like me to find your next best task?"

User: "Mark that complete"
You: "Done! I've marked 'Call the dentist' as complete.
      Want to see what you should work on next?"
```

**Conversation Starters:**
1. "What should I do next?"
2. "Create a new task"
3. "Show my pending tasks"
4. "Mark my last task complete"

### Step 3: Add Actions

1. Click **Create new action**
2. **Authentication:** None (for demo)
3. **Import Schema:**
   - Click **Import from file**
   - Select `src/gas/openapi-schema-gpt.json`
4. **Verify Server URL:**
   ```
   https://script.google.com/macros/s/AKfycbwz_zgYRCztreHox0qpWBQLdo5F174ZE8oiNUb_IcOYjtR3jJho8GHpSlruQaqJ1eJWqQ/exec
   ```
5. **Privacy:**
   - This URL is configured for "Anyone" access (demo only)
   - For production, would use OAuth
6. Click **Save**

### Step 4: Test All Operations

Test each operation in the preview pane:

**Test 1: Get Best Task**
```
You: What should I do next?
Expected: Returns task with score + reasoning
```

**Test 2: Create Task**
```
You: Create a task: Prepare presentation, priority 5, due tomorrow
Expected: Confirms creation with task ID
```

**Test 3: Query Tasks**
```
You: Show my pending tasks
Expected: Lists pending tasks (max 10)
```

**Test 4: Update Task**
```
You: Change the presentation task to priority 4
Expected: Confirms update
```

**Test 5: Complete Task**
```
You: Mark the presentation task as complete
Expected: Confirms completion
```

**Test 6: Snooze Task**
```
You: Snooze my report task for 2 hours
Expected: Confirms snooze with time
```

---

## Fixing "ResponseTooLargeError"

### Problem

Custom GPT shows: `ResponseTooLargeError`

### Cause

The API is returning too much data (likely from query endpoint returning 100+ tasks).

### Solution 1: Update Query Limits

The new schema limits responses:
- Default limit: 10 tasks
- Maximum limit: 20 tasks
- Uses `limit` parameter to control size

### Solution 2: Filter Queries

Always use filters when querying:
```
// Instead of:
"Show all my tasks"

// Use:
"Show my pending tasks" (filters by status)
"Show my urgent tasks" (filters by priority=5)
"Show my 5 most important tasks" (uses limit)
```

### Solution 3: Check Sheet Size

If you have 100+ tasks:
1. Open your Google Sheet
2. Archive old completed tasks
3. Keep active tasks < 50 for best performance

---

## Troubleshooting

### Issue: "The requested action requires approval"

**Cause:** Custom GPT asking for user confirmation before calling API

**Solution:** This is expected behavior - just click "Allow"

**Why:** OpenAI requires approval for first-time API calls to new domains

**Make it permanent:** After allowing once, GPT remembers for this conversation

### Issue: Only 3 operations visible instead of 6

**Cause:** Old schema had grouped operations

**Solution:**
1. Delete existing action
2. Import new `openapi-schema-gpt.json`
3. Verify all 6 operations appear:
   - getBestTask
   - createTask
   - updateTask
   - completeTask
   - snoozeTask
   - queryTasks

### Issue: GPT not understanding priority levels

**Cause:** Instructions unclear about priority scale

**Solution:** Already fixed in new instructions:
- Priority 1 = low, nice-to-have
- Priority 2 = low
- Priority 3 = normal
- Priority 4 = high
- Priority 5 = urgent, do now

### Issue: Date format errors

**Cause:** GPT not converting to ISO8601

**Solution:** Instructions now specify:
- Accept natural language ("tomorrow", "next Friday")
- Convert to ISO8601: `YYYY-MM-DDTHH:MM:SSZ`
- Example: `2025-11-15T17:00:00Z`

### Issue: API calls timing out

**Cause:** Too many tasks or slow sheet operations

**Solution:**
1. Reduce query limits (use new schema's default of 10)
2. Archive old tasks in sheet
3. Add filters to queries

---

## Schema Differences

### Old Schema (3 operations)
```
/ GET - getBestTask
/ POST - manageTask (combined create/update/complete/snooze)
/query GET - queryTasks
```

**Problem:** `manageTask` was confusing - one operation doing 4 things

### New Schema (6 operations)
```
/exec?action=best GET - getBestTask
/exec?action=query GET - queryTasks
/exec?action=create POST - createTask
/exec?action=update POST - updateTask
/exec?action=complete POST - completeTask
/exec?action=snooze POST - snoozeTask
```

**Benefits:**
- Clear separation of operations
- GPT knows exactly which endpoint to call
- Better error messages
- Easier to test individual operations

---

## Verification Checklist

After updating, verify:

- [ ] All 6 operations visible in Actions configuration
- [ ] Server URL is correct (your deployed GAS endpoint)
- [ ] Can get best task successfully
- [ ] Can create a task
- [ ] Can query tasks (returns max 10)
- [ ] Can update a task
- [ ] Can complete a task
- [ ] Can snooze a task
- [ ] No ResponseTooLargeError
- [ ] Scores and reasoning are shown

---

## Production Recommendations

For real-world use (beyond demo):

### Security
```yaml
Authentication: OAuth 2.0
Access: Restricted to specific users
API Keys: Add header-based authentication
Rate Limiting: 60 requests/minute per user
```

### Performance
```yaml
Sheet Size: Keep < 100 active tasks
Query Limits: Default 10, max 20
Caching: Consider adding GAS cache layer
Indexing: Use separate sheets by status
```

### Monitoring
```yaml
Logs Sheet: Review daily for errors
Error Tracking: Set up notifications for failures
Usage Stats: Track API calls per day
Performance: Monitor response times
```

---

## File Locations

**OpenAPI Schema:**
```
src/gas/openapi-schema-gpt.json
```

**Import into Custom GPT:** This is the GPT-optimized schema with 6 clear operations and response size limits

---

## Next Steps

1. ✅ Update Custom GPT with new schema
2. ✅ Test all 6 operations
3. ✅ Verify no ResponseTooLargeError
4. ✅ Check Google Sheet for task data
5. ✅ Share GPT link (Settings → Share → Anyone with link)

---

**Need help?** Check the debug logs in Custom GPT (click the operation name to see request/response)

**Still having issues?** See DEPLOYMENT.md troubleshooting section
