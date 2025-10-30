/**
 * MindFlow Task Manager - Google Apps Script Implementation
 *
 * This script provides REST-like endpoints for task management,
 * using Google Sheets as the data store.
 *
 * Endpoints:
 * - POST /?action=create      - Create new task
 * - POST /?action=update      - Update task fields
 * - POST /?action=complete    - Mark task as complete
 * - POST /?action=snooze      - Snooze task
 * - GET  /?action=best        - Get best task right now
 * - GET  /?action=query       - Query tasks with filters
 */

// Configuration
const SHEET_NAME_TASKS = 'tasks';
const SHEET_NAME_LOGS = 'logs';

/**
 * Main POST handler - routes to appropriate action
 */
function doPost(e) {
  const startTime = new Date();
  const requestId = Utilities.getUuid();

  try {
    // Parse request
    const content = e.postData ? JSON.parse(e.postData.contents) : {};
    const action = e.parameter.action || content.action;
    const taskId = e.parameter.id || content.id;

    if (!action) {
      return jsonResponse(400, {
        status: 'error',
        message: "Missing 'action' parameter"
      });
    }

    // Route to handler
    let result;
    switch (action) {
      case 'create':
        result = handleCreateTask(content);
        break;
      case 'update':
        if (!taskId) {
          return jsonResponse(400, { status: 'error', message: 'Missing task id' });
        }
        result = handleUpdateTask(taskId, content);
        break;
      case 'complete':
        if (!taskId) {
          return jsonResponse(400, { status: 'error', message: 'Missing task id' });
        }
        result = handleCompleteTask(taskId);
        break;
      case 'snooze':
        if (!taskId) {
          return jsonResponse(400, { status: 'error', message: 'Missing task id' });
        }
        result = handleSnoozeTask(taskId, content);
        break;
      default:
        return jsonResponse(400, {
          status: 'error',
          message: `Unknown action: ${action}`
        });
    }

    // Log successful request
    logRequest(requestId, action, 'success', result.code, null);

    return jsonResponse(result.code, result.data);

  } catch (error) {
    // Log error
    logRequest(requestId, e.parameter?.action || 'unknown', 'error', 500, error.message);

    return jsonResponse(500, {
      status: 'error',
      message: 'Internal server error',
      requestId: requestId,
      details: error.message
    });
  }
}

/**
 * Main GET handler - routes to appropriate action
 */
function doGet(e) {
  const startTime = new Date();
  const requestId = Utilities.getUuid();

  try {
    const action = e.parameter.action;

    if (!action) {
      return jsonResponse(400, {
        status: 'error',
        message: "Missing 'action' parameter"
      });
    }

    let result;
    switch (action) {
      case 'best':
        result = handleBestTask(e.parameter);
        break;
      case 'query':
        result = handleQueryTasks(e.parameter);
        break;
      default:
        return jsonResponse(400, {
          status: 'error',
          message: `Unknown action: ${action}`
        });
    }

    // Log successful request
    logRequest(requestId, action, 'success', result.code, null);

    return jsonResponse(result.code, result.data);

  } catch (error) {
    // Log error
    logRequest(requestId, e.parameter?.action || 'unknown', 'error', 500, error.message);

    return jsonResponse(500, {
      status: 'error',
      message: 'Internal server error',
      requestId: requestId,
      details: error.message
    });
  }
}

/**
 * Create a new task
 */
function handleCreateTask(content) {
  // Validate required fields
  const validation = validateInput(content, ['title', 'priority']);
  if (validation.errors.length > 0) {
    return {
      code: 400,
      data: {
        status: 'error',
        message: 'Validation failed',
        errors: validation.errors
      }
    };
  }

  // Generate ID and timestamps
  const taskId = Utilities.getUuid();
  const now = new Date().toISOString();

  // Build task row
  const taskRow = [
    taskId,                         // id
    content.title,                  // title
    content.description || '',      // description
    'pending',                      // status
    content.priority,               // priority
    content.due_date || '',         // due_date
    '',                             // snoozed_until
    now,                            // created_at
    now                             // updated_at
  ];

  // Append to sheet
  const sheet = getSheet(SHEET_NAME_TASKS);
  sheet.appendRow(taskRow);

  return {
    code: 201,
    data: {
      status: 'created',
      id: taskId,
      title: content.title,
      priority: content.priority,
      created_at: now
    }
  };
}

/**
 * Update an existing task
 */
function handleUpdateTask(taskId, content) {
  const sheet = getSheet(SHEET_NAME_TASKS);
  const data = sheet.getDataRange().getValues();

  // Find task by ID
  const rowIndex = findTaskRowById(data, taskId);
  if (rowIndex === -1) {
    return {
      code: 404,
      data: {
        status: 'error',
        message: 'Task not found'
      }
    };
  }

  // Update fields (row is 1-indexed in Sheets)
  const row = data[rowIndex];
  const now = new Date().toISOString();

  // Column mapping: [id, title, description, status, priority, due_date, snoozed_until, created_at, updated_at]
  if (content.title !== undefined) row[1] = content.title;
  if (content.description !== undefined) row[2] = content.description;
  if (content.status !== undefined) row[3] = content.status;
  if (content.priority !== undefined) row[4] = content.priority;
  if (content.due_date !== undefined) row[5] = content.due_date;
  row[8] = now; // updated_at

  // Write back to sheet (add 1 for 1-indexed)
  sheet.getRange(rowIndex + 1, 1, 1, row.length).setValues([row]);

  return {
    code: 200,
    data: {
      status: 'success',
      id: taskId,
      updated_at: now
    }
  };
}

/**
 * Mark task as complete
 */
function handleCompleteTask(taskId) {
  const sheet = getSheet(SHEET_NAME_TASKS);
  const data = sheet.getDataRange().getValues();

  const rowIndex = findTaskRowById(data, taskId);
  if (rowIndex === -1) {
    return {
      code: 404,
      data: {
        status: 'error',
        message: 'Task not found'
      }
    };
  }

  const row = data[rowIndex];
  const now = new Date().toISOString();

  // Update status and timestamp
  row[3] = 'completed'; // status
  row[8] = now;         // updated_at

  sheet.getRange(rowIndex + 1, 1, 1, row.length).setValues([row]);

  return {
    code: 200,
    data: {
      status: 'success',
      message: 'Task marked as completed',
      id: taskId
    }
  };
}

/**
 * Snooze a task
 */
function handleSnoozeTask(taskId, content) {
  const sheet = getSheet(SHEET_NAME_TASKS);
  const data = sheet.getDataRange().getValues();

  const rowIndex = findTaskRowById(data, taskId);
  if (rowIndex === -1) {
    return {
      code: 404,
      data: {
        status: 'error',
        message: 'Task not found'
      }
    };
  }

  // Parse snooze duration
  const duration = content.snooze_duration || '2h';
  const snoozedUntil = calculateSnoozeTime(duration);

  const row = data[rowIndex];
  const now = new Date().toISOString();

  // Update snooze time and status
  row[3] = 'snoozed';           // status
  row[6] = snoozedUntil;        // snoozed_until
  row[8] = now;                 // updated_at

  sheet.getRange(rowIndex + 1, 1, 1, row.length).setValues([row]);

  return {
    code: 200,
    data: {
      status: 'success',
      snoozed_until: snoozedUntil
    }
  };
}

/**
 * Get the best task to work on right now
 */
function handleBestTask(params) {
  const sheet = getSheet(SHEET_NAME_TASKS);
  const rows = sheet.getDataRange().getValues();

  if (rows.length <= 1) {
    return {
      code: 200,
      data: {
        status: 'no_tasks',
        message: 'No active tasks'
      }
    };
  }

  const now = new Date();
  const timezone = params.timezone || 'UTC';

  // Parse tasks (skip header row)
  const tasks = rows.slice(1).map((row, idx) => ({
    rowIndex: idx + 2, // +2 because: +1 for header, +1 for 1-indexed
    id: row[0],
    title: row[1],
    description: row[2],
    status: row[3],
    priority: row[4],
    due_date: row[5],
    snoozed_until: row[6],
    created_at: row[7],
    updated_at: row[8]
  }));

  // Filter active tasks
  const activeTasks = tasks.filter(task => {
    // Exclude completed tasks
    if (task.status === 'completed') return false;

    // Exclude snoozed tasks (if snooze time hasn't passed)
    if (task.snoozed_until && new Date(task.snoozed_until) > now) return false;

    return true;
  });

  if (activeTasks.length === 0) {
    return {
      code: 200,
      data: {
        status: 'no_tasks',
        message: 'No active tasks'
      }
    };
  }

  // Score each task
  const scored = activeTasks.map(task => ({
    ...task,
    score: scoreTask(task, now)
  }));

  // Get highest scorer
  const best = scored.reduce((a, b) => a.score > b.score ? a : b);

  return {
    code: 200,
    data: {
      status: 'success',
      id: best.id,
      title: best.title,
      description: best.description,
      priority: best.priority,
      due_date: best.due_date,
      score: best.score,
      reasoning: generateReasoning(best, now)
    }
  };
}

/**
 * Query tasks with filters
 */
function handleQueryTasks(params) {
  const sheet = getSheet(SHEET_NAME_TASKS);
  const rows = sheet.getDataRange().getValues();

  if (rows.length <= 1) {
    return {
      code: 200,
      data: []
    };
  }

  // Parse tasks
  const tasks = rows.slice(1).map(row => ({
    id: row[0],
    title: row[1],
    description: row[2],
    status: row[3],
    priority: row[4],
    due_date: row[5],
    snoozed_until: row[6],
    created_at: row[7],
    updated_at: row[8]
  }));

  // Apply filters
  let filtered = tasks;

  if (params.status) {
    filtered = filtered.filter(t => t.status === params.status);
  }

  if (params.priority) {
    filtered = filtered.filter(t => t.priority === parseInt(params.priority));
  }

  // Apply limit
  const limit = params.limit ? parseInt(params.limit) : 50;
  filtered = filtered.slice(0, limit);

  return {
    code: 200,
    data: filtered
  };
}

/**
 * Score a task based on relevance algorithm
 */
function scoreTask(task, now) {
  // Component 1: Priority Score (0-100)
  const priorityScore = (task.priority || 3) * 20;

  // Component 2: Urgency Score (0-100)
  let urgencyScore = 0;
  if (task.due_date) {
    const due = new Date(task.due_date);
    const hoursRemaining = (due - now) / (1000 * 3600);

    if (hoursRemaining < 0) {
      urgencyScore = 100; // Overdue!
    } else if (hoursRemaining < 4) {
      urgencyScore = 90;
    } else if (hoursRemaining < 24) {
      urgencyScore = 75;
    } else if (hoursRemaining < 72) {
      urgencyScore = 50;
    } else {
      // Linear decay over 10 days (240 hours)
      urgencyScore = Math.max(0, 100 - (hoursRemaining / 240 * 100));
    }
  }

  // Component 3: Context Score (0-100)
  // Currently fixed; future: time-of-day awareness
  const contextScore = 50;

  // Component 4: Momentum Score (0-100)
  let momentumScore = 0;
  if (task.status === 'in_progress') {
    momentumScore = 80; // Don't lose focus
  } else if (task.status === 'pending' && task.created_at) {
    // Encourage completion of older tasks
    const daysSinceCreated = (now - new Date(task.created_at)) / (1000 * 3600 * 24);
    momentumScore = Math.min(40, daysSinceCreated * 5);
  }

  // Weighted total
  const totalScore =
    (0.40 * priorityScore) +
    (0.35 * urgencyScore) +
    (0.15 * contextScore) +
    (0.10 * momentumScore);

  return Math.round(totalScore);
}

/**
 * Generate human-readable reasoning for task score
 */
function generateReasoning(task, now) {
  const reasons = [];

  // Priority
  const priorityLabels = { 5: 'urgent', 4: 'high', 3: 'normal', 2: 'low', 1: 'nice-to-have' };
  reasons.push(`${priorityLabels[task.priority] || 'normal'} priority (${task.priority})`);

  // Due date
  if (task.due_date) {
    const due = new Date(task.due_date);
    const hoursRemaining = (due - now) / (1000 * 3600);
    const daysRemaining = Math.floor(hoursRemaining / 24);

    if (hoursRemaining < 0) {
      reasons.push('OVERDUE');
    } else if (hoursRemaining < 24) {
      reasons.push(`due in ${Math.round(hoursRemaining)} hours`);
    } else {
      reasons.push(`due in ${daysRemaining} days`);
    }
  }

  // Status
  if (task.status === 'in_progress') {
    reasons.push('already started');
  }

  return reasons.join(' + ');
}

/**
 * Calculate snooze time from duration string
 */
function calculateSnoozeTime(duration) {
  const now = new Date();
  const match = duration.match(/^(\d+)(h|d|w)$/);

  if (!match) {
    // Default to 2 hours
    now.setHours(now.getHours() + 2);
    return now.toISOString();
  }

  const value = parseInt(match[1]);
  const unit = match[2];

  switch (unit) {
    case 'h':
      now.setHours(now.getHours() + value);
      break;
    case 'd':
      now.setDate(now.getDate() + value);
      break;
    case 'w':
      now.setDate(now.getDate() + (value * 7));
      break;
  }

  return now.toISOString();
}

/**
 * Validate input data
 */
function validateInput(content, requiredFields) {
  const errors = [];

  // Check required fields
  requiredFields.forEach(field => {
    if (!content[field]) {
      errors.push({
        field: field,
        issue: `${field} is required`
      });
    }
  });

  // Validate priority
  if (content.priority !== undefined) {
    const priority = parseInt(content.priority);
    if (isNaN(priority) || priority < 1 || priority > 5) {
      errors.push({
        field: 'priority',
        issue: 'Priority must be an integer between 1 and 5'
      });
    }
  }

  // Validate due_date format
  if (content.due_date) {
    const date = new Date(content.due_date);
    if (isNaN(date.getTime())) {
      errors.push({
        field: 'due_date',
        issue: 'Invalid ISO8601 date format'
      });
    }
  }

  // Validate title length
  if (content.title && content.title.length > 256) {
    errors.push({
      field: 'title',
      issue: 'Title must be 256 characters or less'
    });
  }

  return { errors };
}

/**
 * Find task row index by ID
 */
function findTaskRowById(data, taskId) {
  for (let i = 1; i < data.length; i++) { // Skip header row
    if (data[i][0] === taskId) {
      return i;
    }
  }
  return -1;
}

/**
 * Get sheet by name
 */
function getSheet(sheetName) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(sheetName);

  if (!sheet) {
    throw new Error(`Sheet "${sheetName}" not found. Please create it first.`);
  }

  return sheet;
}

/**
 * Log request to logs sheet
 */
function logRequest(requestId, action, result, statusCode, errorMsg) {
  try {
    const logsSheet = getSheet(SHEET_NAME_LOGS);
    const timestamp = new Date().toISOString();

    const logRow = [
      timestamp,
      action || 'unknown',
      result,
      statusCode,
      requestId,
      errorMsg || ''
    ];

    logsSheet.appendRow(logRow);
  } catch (error) {
    // Don't fail request if logging fails
    Logger.log('Failed to log request: ' + error.message);
  }
}

/**
 * Create JSON response
 */
function jsonResponse(code, data) {
  return ContentService
    .createTextOutput(JSON.stringify({
      status: code < 400 ? 'success' : 'error',
      code: code,
      data: data
    }))
    .setMimeType(ContentService.MimeType.JSON);
}
