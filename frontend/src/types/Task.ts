/**
 * TypeScript type definitions for MindFlow tasks
 * Based on backend API schema and responses
 */

/**
 * Priority levels for tasks (1 = lowest, 5 = highest)
 */
export type TaskPriority = 1 | 2 | 3 | 4 | 5;

/**
 * Task status values
 */
export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'snoozed';

/**
 * Core task interface matching backend TaskResponse schema
 */
export interface Task {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  priority: TaskPriority;
  status: TaskStatus;
  due_date: string | null; // ISO 8601 datetime string
  tags: string | null;
  effort_estimate_minutes: number | null;
  created_at: string; // ISO 8601 datetime string
  updated_at: string; // ISO 8601 datetime string
  completed_at: string | null; // ISO 8601 datetime string
  snoozed_until: string | null; // ISO 8601 datetime string
}

/**
 * Task scoring reasoning from /api/v1/tasks/next endpoint
 */
export interface TaskReasoning {
  deadline_urgency: number;
  priority_score: number;
  effort_bonus: number;
  total_score: number;
  recommendation: string;
}

/**
 * Response from /api/v1/tasks/next endpoint
 */
export interface NextTaskResponse {
  task: Task;
  score: number;
  reasoning: TaskReasoning;
}

/**
 * Props for TaskCard component
 */
export interface TaskCardProps {
  task: Task;
  score?: number;
  reasoning?: TaskReasoning;
  onTaskClick?: (taskId: string) => void;
  className?: string;
}
