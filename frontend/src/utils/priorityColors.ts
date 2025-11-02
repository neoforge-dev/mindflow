/**
 * Priority color utilities for visual task indicators
 * Uses system-compatible colors for ChatGPT Apps SDK
 */

import { TaskPriority } from '../types/Task';

/**
 * Color scheme for light and dark modes
 */
interface PriorityColors {
  background: string;
  text: string;
  border: string;
  label: string;
}

/**
 * Get priority colors for light mode
 *
 * @param priority Task priority level (1-5)
 * @returns Color scheme for the priority level
 */
export function getPriorityColorsLight(priority: TaskPriority): PriorityColors {
  switch (priority) {
    case 5: // Urgent - Red
      return {
        background: '#ffebee',
        text: '#c62828',
        border: '#ef5350',
        label: 'Urgent',
      };
    case 4: // High - Orange
      return {
        background: '#fff3e0',
        text: '#e65100',
        border: '#ff9800',
        label: 'High',
      };
    case 3: // Medium - Yellow
      return {
        background: '#fffde7',
        text: '#f57f17',
        border: '#fdd835',
        label: 'Medium',
      };
    case 2: // Low - Green
      return {
        background: '#e8f5e9',
        text: '#2e7d32',
        border: '#66bb6a',
        label: 'Low',
      };
    case 1: // Very Low - Gray
      return {
        background: '#f5f5f5',
        text: '#616161',
        border: '#9e9e9e',
        label: 'Very Low',
      };
  }
}

/**
 * Get priority colors for dark mode
 *
 * @param priority Task priority level (1-5)
 * @returns Color scheme for the priority level
 */
export function getPriorityColorsDark(priority: TaskPriority): PriorityColors {
  switch (priority) {
    case 5: // Urgent - Red
      return {
        background: '#4a1a1a',
        text: '#ffcdd2',
        border: '#e57373',
        label: 'Urgent',
      };
    case 4: // High - Orange
      return {
        background: '#4a2a1a',
        text: '#ffccbc',
        border: '#ffb74d',
        label: 'High',
      };
    case 3: // Medium - Yellow
      return {
        background: '#4a4a1a',
        text: '#fff9c4',
        border: '#ffee58',
        label: 'Medium',
      };
    case 2: // Low - Green
      return {
        background: '#1a3a1a',
        text: '#c8e6c9',
        border: '#81c784',
        label: 'Low',
      };
    case 1: // Very Low - Gray
      return {
        background: '#2a2a2a',
        text: '#e0e0e0',
        border: '#bdbdbd',
        label: 'Very Low',
      };
  }
}

/**
 * Get priority colors based on color scheme preference
 *
 * @param priority Task priority level (1-5)
 * @param isDark Whether dark mode is active
 * @returns Color scheme for the priority level
 */
export function getPriorityColors(priority: TaskPriority, isDark: boolean): PriorityColors {
  return isDark ? getPriorityColorsDark(priority) : getPriorityColorsLight(priority);
}
