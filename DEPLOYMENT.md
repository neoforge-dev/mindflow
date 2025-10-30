# MindFlow Deployment Guide

Complete step-by-step instructions for deploying MindFlow from scratch.

---

## Prerequisites

- Google Account (for Google Sheets & Apps Script)
- OpenAI Plus subscription (for Custom GPT)
- Web browser (Chrome/Firefox recommended)

---

## Phase 1: Create Google Sheet (5 minutes)

### Step 1: Create New Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Click **Blank** to create a new spreadsheet
3. Rename it to **"MindFlow Tasks"**

### Step 2: Set Up Tasks Tab

1. Rename **Sheet1** to **`tasks`**
2. Add the following headers in Row 1:

| A | B | C | D | E | F | G | H | I |
|---|---|---|---|---|---|---|---|---|
| id | title | description | status | priority | due_date | snoozed_until | created_at | updated_at |

3. **Format columns:**
   - Column A (id): Plain text
   - Columns F, G, H, I (dates): Format → Number → Date time
   - Column E (priority): Number (1-5)

### Step 3: Set Up Logs Tab

1. Click **+** at bottom left to add new sheet
2. Rename it to **`logs`**
3. Add the following headers in Row 1:

| A | B | C | D | E | F |
|---|---|---|---|---|---|
| timestamp | action | result | status_code | request_id | error_message |

4. **Format columns:**
   - Column A (timestamp): Format → Number → Date time

### Step 4: Save Sheet URL

- Copy the URL from your browser
- Save it for later: `https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit`
- Extract just the `YOUR_SHEET_ID` part (between `/d/` and `/edit`)

---

## Phase 2: Deploy Google Apps Script (10 minutes)

### Step 1: Open Apps Script Editor

1. In your Google Sheet, click **Extensions → Apps Script**
2. This opens a new tab with the Apps Script editor
3. Delete any default code in `Code.gs`

### Step 2: Add Implementation Code

1. Copy the entire contents from `src/gas/Code.gs` (I'll create this file next)
2. Paste it into the Apps Script editor
3. Click **Save** (💾 icon)
4. Rename the project to **"MindFlow API"**

### Step 3: Deploy as Web App

1. Click **Deploy → New deployment**
2. Click the gear icon ⚙️ next to "Select type"
3. Choose **Web app**
4. Configure settings:
   - **Description:** "MindFlow Task API v1"
   - **Execute as:** Me (your email)
   - **Who has access:** Anyone

   ⚠️ **Note:** "Anyone" means public access (demo only). For production, use OAuth.

5. Click **Deploy**
6. **Authorize access:**
   - Click **Authorize access**
   - Choose your Google account
   - Click **Advanced → Go to MindFlow API (unsafe)**
   - Click **Allow**

7. **Copy the Web App URL**
   - You'll see: `https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec`
   - Save this URL — you'll need it for the Custom GPT

### Step 4: Test the Deployment

Open a terminal and test with curl:

```bash
# Test the "best task" endpoint (should return empty initially)
curl "https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec?action=best"

# Expected response:
# {"status":"success","code":200,"data":{"status":"no_tasks","message":"No active tasks"}}
```

If you see the JSON response, your API is working! ✅

---

## Phase 3: Create Custom GPT (10 minutes)

### Step 1: Access GPT Builder

1. Go to [ChatGPT](https://chat.openai.com)
2. Click your profile icon (bottom left)
3. Select **My GPTs → Create a GPT**

### Step 2: Configure GPT Details

1. **Name:** MindFlow
2. **Description:** "AI-powered task manager that helps you decide what to work on next using intelligent prioritization."
3. **Instructions:** Paste the following:

```
You are MindFlow, an AI-powered task manager assistant. Your role is to help users manage their tasks through natural conversation.

You have access to a task management API with the following capabilities:
- Create new tasks with title, description, priority (1-5), and due date
- View the best task to work on right now (using intelligent scoring)
- Mark tasks as complete, in progress, or snooze them
- Query existing tasks by status or priority
- Get an overview of all pending work

When the user speaks to you, interpret their intent and use the appropriate API actions. For example:
- "What should I do next?" → Fetch the best-scored task
- "I want to review the metrics by Friday" → Create a task with that title and due date
- "Mark that as done" → Complete the last mentioned task
- "Snooze this for 2 hours" → Snooze the referenced task

Always be conversational, provide context about WHY a task is recommended (mention its score and reasoning), and confirm actions before executing them (especially status changes).

When creating tasks, ALWAYS ask for missing information if not provided:
- Priority (1-5, where 5 is most urgent)
- Due date (in ISO8601 format or natural language you'll convert)

After every action that modifies data, confirm what was done and ask if there's anything else.
```

4. **Conversation starters (add these 4):**
   - "What should I do next?"
   - "Create a new task"
   - "Show me all my pending tasks"
   - "Mark my last task as complete"

### Step 3: Configure Actions

1. Click **Create** (top right)
2. In the Configure tab, scroll to **Actions**
3. Click **Create new action**
4. Click **Import from file**
5. Select: `src/gas/openapi-schema-gpt.json` from your local repository

   **OR** if uploading from URL, use: `https://raw.githubusercontent.com/YOUR_USERNAME/mindflow/main/src/gas/openapi-schema-gpt.json`

6. **Update the server URL** in the schema:
   - Find the `"servers"` section
   - Replace `YOUR_SCRIPT_ID` with your actual GAS deployment ID
   - Example: `https://script.google.com/macros/s/AKfycbx.../exec`

7. **Authentication:** None (for demo)
8. Click **Save**

### Step 4: Test Your GPT

1. Click **Preview** (top right)
2. Try these queries:

**Test 1: Check for tasks (should be empty)**
```
You: What should I do next?
GPT: You currently have no active tasks! Would you like to create one?
```

**Test 2: Create a task**
```
You: Create a task to review Q4 metrics by November 15th, high priority
GPT: [Creates task and confirms]
```

**Test 3: Get best task**
```
You: What should I do next?
GPT: You should work on "Review Q4 metrics" - it's high priority (4) and due on Nov 15...
```

If all tests pass, your Custom GPT is working! ✅

---

## Phase 4: Verify End-to-End (5 minutes)

### Complete Flow Test

1. **In Custom GPT, say:**
   ```
   Create a task: "Prepare presentation" due tomorrow, priority 5
   ```

2. **Check Google Sheet:**
   - Open your `tasks` tab
   - You should see a new row with the task details
   - Note the `id` value

3. **In Custom GPT, say:**
   ```
   What should I do next?
   ```

4. **GPT should respond:**
   ```
   You should work on "Prepare presentation" - it's urgent (priority 5)
   and due tomorrow (score: 92).
   ```

5. **Check Logs Sheet:**
   - Open your `logs` tab
   - You should see entries for each API call

6. **Mark complete:**
   ```
   Mark that task as complete
   ```

7. **Verify in Sheet:**
   - `status` should change to "completed"
   - `updated_at` should have current timestamp

---

## Phase 5: Update README Links (2 minutes)

Now that everything is deployed, update the placeholders in `README.md`:

```markdown
## Live Demo

- **Google Sheet:** https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
- **API Endpoint:** https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec
- **Custom GPT:** [Share link from GPT settings]
```

---

## Troubleshooting

### Issue: "Authorization required" when calling GAS

**Solution:**
1. Go to Apps Script editor
2. Click **Deploy → Manage deployments**
3. Verify "Who has access" is set to "Anyone"
4. Redeploy if needed

### Issue: GPT says "API call failed"

**Solution:**
1. Check the GAS logs: **Executions** tab in Apps Script editor
2. Look for error messages
3. Common causes:
   - Wrong URL in OpenAPI schema
   - Sheet structure doesn't match expected columns
   - Permission issues

### Issue: Sheet not updating

**Solution:**
1. Check Apps Script has permission to edit the sheet
2. Verify sheet tabs are named exactly `tasks` and `logs`
3. Check column headers match exactly (case-sensitive)

### Issue: "No active tasks" when tasks exist

**Solution:**
1. Check `status` column values are exactly: `pending`, `in_progress`, `completed`, or `snoozed`
2. If `snoozed_until` has a future date, task won't appear
3. If `status` is `completed`, task is filtered out

---

## Security Notes

⚠️ **Current setup is PUBLIC (demo only)**

For production:
- Use Google OAuth for authentication
- Add API key validation
- Restrict "Who has access" to specific users
- Add rate limiting
- Sanitize all inputs

See README.md "Assumptions & Trade-offs" section for additional production recommendations.

---

## Next Steps

After successful deployment:

1. ✅ Test all 6 API endpoints manually (see README Testing section)
2. ✅ Create sample tasks with different priorities/due dates
3. ✅ Record a demo video showing the 4 conversational flows
4. ✅ Add the video URL to README
5. ✅ Share your Custom GPT (Settings → Share → Anyone with link)
6. ✅ Update all URLs in README

---

## Estimated Total Time

- **Setup:** 32 minutes
- **Testing:** 10 minutes
- **Documentation:** 5 minutes
- **Total:** ~45 minutes

---

**Deployed successfully?** Open an issue or create a PR if you have suggestions for improving this guide!
