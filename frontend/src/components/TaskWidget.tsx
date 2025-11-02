/**
 * TaskWidget - Pure ChatGPT Apps SDK Component
 *
 * Clean, elegant task display using only AppsSDK.
 * No props, no fallbacks - ChatGPT only.
 */

import React, { useMemo, useState } from 'react';
import { getSDK } from '../sdk/AppsSDK';

interface Task {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  priority: number;
  status: string;
  due_date: string | null;
  tags: string | null;
  effort_estimate_minutes: number | null;
  created_at: string;
  updated_at: string;
}

interface TaskReasoning {
  deadline_urgency: number;
  priority_score: number;
  effort_bonus: number;
  total_score: number;
  recommendation: string;
}

interface TaskOutput {
  task: Task;
  score: number;
  reasoning: TaskReasoning;
}

const PRIORITY_LABELS: Record<number, string> = {
  1: 'Very Low',
  2: 'Low',
  3: 'Medium',
  4: 'High',
  5: 'Urgent',
};

export const TaskWidget: React.FC = () => {
  const sdk = getSDK();
  const theme = sdk.theme;
  const isDark = theme === 'dark';

  // Get task data from SDK
  const { task, score, reasoning } = useMemo(() => {
    return sdk.getToolOutput<TaskOutput>();
  }, []);

  // State for button loading
  const [isCompleting, setIsCompleting] = useState(false);
  const [isSnoozing, setIsSnoozing] = useState(false);

  // Handle complete task
  const handleComplete = async () => {
    try {
      setIsCompleting(true);
      await sdk.callTool({
        name: 'complete_task',
        arguments: { task_id: task.id },
      });

      // Send follow-up message
      await window.openai!.sendFollowUpMessage({
        prompt: `Task "${task.title}" completed! What should I work on next?`,
      });
    } catch (error) {
      console.error('Failed to complete task:', error);
    } finally {
      setIsCompleting(false);
    }
  };

  // Handle snooze task
  const handleSnooze = async (hours: number) => {
    try {
      setIsSnoozing(true);
      await sdk.callTool({
        name: 'snooze_task',
        arguments: { task_id: task.id, hours },
      });

      // Send follow-up message
      await window.openai!.sendFollowUpMessage({
        prompt: `Task "${task.title}" snoozed for ${hours} hours. Show me the next task.`,
      });
    } catch (error) {
      console.error('Failed to snooze task:', error);
    } finally {
      setIsSnoozing(false);
    }
  };

  // Format due date
  const dueDateText = useMemo(() => {
    if (!task.due_date) return null;

    const dueDate = new Date(task.due_date);
    const now = new Date();
    const diffMs = dueDate.getTime() - now.getTime();
    const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays < 0) return `Overdue by ${Math.abs(diffDays)}d`;
    if (diffDays === 0) return 'Due today';
    if (diffDays === 1) return 'Due tomorrow';
    if (diffDays <= 7) return `Due in ${diffDays}d`;
    return `Due ${dueDate.toLocaleDateString()}`;
  }, [task.due_date]);

  // Format effort
  const effortText = useMemo(() => {
    if (!task.effort_estimate_minutes) return null;

    const minutes = task.effort_estimate_minutes;
    if (minutes < 60) return `${minutes}m`;

    const hours = Math.floor(minutes / 60);
    const remainingMins = minutes % 60;
    return remainingMins > 0 ? `${hours}h ${remainingMins}m` : `${hours}h`;
  }, [task.effort_estimate_minutes]);

  // Check if overdue
  const isOverdue = useMemo(() => {
    if (!task.due_date) return false;
    return new Date(task.due_date) < new Date();
  }, [task.due_date]);

  // Priority colors
  const priorityColor = useMemo(() => {
    const colors = {
      light: {
        5: { bg: '#ffebee', text: '#c62828', border: '#ef5350' },
        4: { bg: '#fff3e0', text: '#e65100', border: '#ff9800' },
        3: { bg: '#e3f2fd', text: '#1565c0', border: '#2196f3' },
        2: { bg: '#f3e5f5', text: '#6a1b9a', border: '#9c27b0' },
        1: { bg: '#f1f8e9', text: '#558b2f', border: '#8bc34a' },
      },
      dark: {
        5: { bg: '#4a1616', text: '#ffcdd2', border: '#e57373' },
        4: { bg: '#4a3116', text: '#ffe0b2', border: '#ffb74d' },
        3: { bg: '#162a4a', text: '#bbdefb', border: '#64b5f6' },
        2: { bg: '#391646', text: '#e1bee7', border: '#ba68c8' },
        1: { bg: '#2d4a16', text: '#dcedc8', border: '#aed581' },
      },
    };

    return isDark
      ? colors.dark[task.priority as keyof typeof colors.dark]
      : colors.light[task.priority as keyof typeof colors.light];
  }, [task.priority, isDark]);

  // Theme colors
  const colors = {
    bg: isDark ? '#1a1a1a' : '#ffffff',
    text: isDark ? '#ffffff' : '#000000',
    textSecondary: isDark ? '#b0b0b0' : '#666666',
    border: isDark ? '#404040' : '#e0e0e0',
    accent: '#007aff',
    scoreBg: isDark ? 'rgba(0, 122, 255, 0.1)' : 'rgba(0, 122, 255, 0.05)',
    scoreBorder: isDark
      ? 'rgba(0, 122, 255, 0.2)'
      : 'rgba(0, 122, 255, 0.15)',
  };

  return (
    <div
      style={{
        fontFamily:
          "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif",
        backgroundColor: colors.bg,
        border: `1px solid ${colors.border}`,
        borderRadius: '8px',
        padding: '16px',
        maxWidth: '600px',
        width: '100%',
      }}
    >
      {/* Priority Badge */}
      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '4px 12px',
          borderRadius: '12px',
          fontSize: '12px',
          fontWeight: 600,
          backgroundColor: priorityColor.bg,
          color: priorityColor.text,
          border: `1px solid ${priorityColor.border}`,
        }}
      >
        <span
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: priorityColor.border,
          }}
        />
        {PRIORITY_LABELS[task.priority]}
      </div>

      {/* Title */}
      <h3
        style={{
          fontSize: '18px',
          fontWeight: 600,
          color: colors.text,
          margin: '12px 0 8px 0',
          lineHeight: 1.4,
        }}
      >
        {task.title}
      </h3>

      {/* Description */}
      {task.description && (
        <p
          style={{
            fontSize: '14px',
            color: colors.textSecondary,
            lineHeight: 1.5,
            margin: '0 0 12px 0',
          }}
        >
          {task.description}
        </p>
      )}

      {/* Metadata */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '12px',
          fontSize: '13px',
          color: colors.textSecondary,
          marginBottom: '12px',
        }}
      >
        {dueDateText && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              color: isOverdue
                ? isDark
                  ? '#ffcdd2'
                  : '#c62828'
                : colors.textSecondary,
              fontWeight: isOverdue ? 600 : 400,
            }}
          >
            <span>📅</span>
            <span>{dueDateText}</span>
          </div>
        )}
        {effortText && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span>⏱️</span>
            <span>{effortText}</span>
          </div>
        )}
        {task.tags && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span>🏷️</span>
            <span>{task.tags}</span>
          </div>
        )}
      </div>

      {/* AI Score */}
      <div
        style={{
          marginTop: '12px',
          padding: '12px',
          backgroundColor: colors.scoreBg,
          borderRadius: '6px',
          border: `1px solid ${colors.scoreBorder}`,
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '8px',
          }}
        >
          <span
            style={{
              fontSize: '12px',
              fontWeight: 600,
              color: colors.accent,
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}
          >
            AI Score
          </span>
          <span
            style={{
              fontSize: '20px',
              fontWeight: 700,
              color: colors.accent,
            }}
          >
            {score.toFixed(1)}
          </span>
        </div>

        {reasoning.recommendation && (
          <p
            style={{
              fontSize: '13px',
              color: colors.text,
              lineHeight: 1.5,
              margin: '8px 0 0 0',
            }}
          >
            {reasoning.recommendation}
          </p>
        )}

        {/* Reasoning Details */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
            gap: '8px',
            marginTop: '8px',
            fontSize: '12px',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              padding: '4px 0',
            }}
          >
            <span style={{ color: colors.textSecondary }}>Priority:</span>
            <span style={{ fontWeight: 600, color: colors.text }}>
              {reasoning.priority_score}
            </span>
          </div>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              padding: '4px 0',
            }}
          >
            <span style={{ color: colors.textSecondary }}>Urgency:</span>
            <span style={{ fontWeight: 600, color: colors.text }}>
              {reasoning.deadline_urgency.toFixed(1)}
            </span>
          </div>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              padding: '4px 0',
            }}
          >
            <span style={{ color: colors.textSecondary }}>Effort:</span>
            <span style={{ fontWeight: 600, color: colors.text }}>
              {reasoning.effort_bonus}
            </span>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div
        style={{
          marginTop: '16px',
          display: 'flex',
          gap: '8px',
          flexWrap: 'wrap',
        }}
      >
        <button
          onClick={handleComplete}
          disabled={isCompleting}
          style={{
            flex: '1 1 auto',
            minWidth: '120px',
            padding: '10px 16px',
            backgroundColor: isCompleting ? colors.border : colors.accent,
            color: '#ffffff',
            border: 'none',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: 600,
            cursor: isCompleting ? 'not-allowed' : 'pointer',
            opacity: isCompleting ? 0.6 : 1,
            transition: 'all 0.2s',
          }}
        >
          {isCompleting ? 'Completing...' : '✓ Complete Task'}
        </button>

        <button
          onClick={() => handleSnooze(3)}
          disabled={isSnoozing}
          style={{
            flex: '1 1 auto',
            minWidth: '120px',
            padding: '10px 16px',
            backgroundColor: isSnoozing ? colors.border : 'transparent',
            color: isSnoozing ? colors.textSecondary : colors.text,
            border: `1px solid ${colors.border}`,
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: 600,
            cursor: isSnoozing ? 'not-allowed' : 'pointer',
            opacity: isSnoozing ? 0.6 : 1,
            transition: 'all 0.2s',
          }}
        >
          {isSnoozing ? 'Snoozing...' : '⏰ Snooze 3h'}
        </button>
      </div>
    </div>
  );
};
