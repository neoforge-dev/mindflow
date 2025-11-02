/**
 * ChatGPT Apps SDK entry point
 * Exports MindFlow task components for use in ChatGPT interface
 */

// Export main component
export { TaskCard, default as TaskCardDefault } from './components/TaskCard';

// Export types for external usage
export type {
  Task,
  TaskPriority,
  TaskStatus,
  TaskReasoning,
  NextTaskResponse,
  TaskCardProps,
} from './types/Task';

// Export utilities for external usage
export { formatDueDate, formatEffort, isOverdue } from './utils/dateFormat';
export {
  getPriorityColors,
  getPriorityColorsLight,
  getPriorityColorsDark,
} from './utils/priorityColors';

// Version info
export const VERSION = '1.0.0';
