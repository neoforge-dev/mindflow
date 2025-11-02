/**
 * Date formatting utilities for human-readable due dates
 */

/**
 * Format a due date into human-readable text
 * Examples: "Due today", "Due tomorrow", "Due in 3 days", "Overdue by 2 days"
 *
 * @param dueDateStr ISO 8601 datetime string or null
 * @returns Human-readable due date string or null
 */
export function formatDueDate(dueDateStr: string | null): string | null {
  if (!dueDateStr) {
    return null;
  }

  try {
    const dueDate = new Date(dueDateStr);
    const now = new Date();

    // Reset time to midnight for day comparison
    const dueDateMidnight = new Date(dueDate.getFullYear(), dueDate.getMonth(), dueDate.getDate());
    const nowMidnight = new Date(now.getFullYear(), now.getMonth(), now.getDate());

    const diffMs = dueDateMidnight.getTime() - nowMidnight.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return 'Due today';
    } else if (diffDays === 1) {
      return 'Due tomorrow';
    } else if (diffDays === -1) {
      return 'Overdue by 1 day';
    } else if (diffDays > 1 && diffDays <= 7) {
      return `Due in ${diffDays} days`;
    } else if (diffDays > 7) {
      // For dates more than a week away, show the actual date
      return `Due ${dueDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;
    } else {
      // Overdue by more than 1 day
      return `Overdue by ${Math.abs(diffDays)} days`;
    }
  } catch (error) {
    console.error('Error parsing due date:', error);
    return null;
  }
}

/**
 * Check if a task is overdue
 *
 * @param dueDateStr ISO 8601 datetime string or null
 * @returns true if task is overdue, false otherwise
 */
export function isOverdue(dueDateStr: string | null): boolean {
  if (!dueDateStr) {
    return false;
  }

  try {
    const dueDate = new Date(dueDateStr);
    const now = new Date();

    // Reset time to midnight for day comparison
    const dueDateMidnight = new Date(dueDate.getFullYear(), dueDate.getMonth(), dueDate.getDate());
    const nowMidnight = new Date(now.getFullYear(), now.getMonth(), now.getDate());

    return dueDateMidnight < nowMidnight;
  } catch (error) {
    return false;
  }
}

/**
 * Format effort estimate into human-readable text
 * Examples: "5 min", "1 hour", "2.5 hours"
 *
 * @param minutes Effort estimate in minutes
 * @returns Human-readable effort string or null
 */
export function formatEffort(minutes: number | null): string | null {
  if (!minutes || minutes <= 0) {
    return null;
  }

  if (minutes < 60) {
    return `${minutes} min`;
  }

  const hours = minutes / 60;
  if (hours === 1) {
    return '1 hour';
  }

  // Round to 1 decimal place
  const roundedHours = Math.round(hours * 10) / 10;
  return `${roundedHours} hours`;
}
