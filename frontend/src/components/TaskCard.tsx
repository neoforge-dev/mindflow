/**
 * TaskCard component for ChatGPT Apps SDK
 * Displays MindFlow tasks with priority, due date, and AI scoring
 *
 * Design follows ChatGPT Apps SDK guidelines:
 * - System fonts and colors only
 * - Semantic HTML
 * - Responsive and accessible
 * - Light/dark mode support
 * - No external CSS frameworks
 */

import React, { useState } from 'react';
import { TaskCardProps } from '../types/Task';
import { formatDueDate, formatEffort, isOverdue } from '../utils/dateFormat';
import { getPriorityColors } from '../utils/priorityColors';
import { useOpenAI } from '../hooks/useOpenAI';

/**
 * TaskCard component
 *
 * When running in ChatGPT:
 * - Gets task data from window.openai.toolOutput
 * - Uses ChatGPT's theme preference
 *
 * When running standalone:
 * - Uses props directly
 * - Falls back to system theme preference
 */
export const TaskCard: React.FC<TaskCardProps> = ({
  task: propTask,
  score: propScore,
  reasoning: propReasoning,
  onTaskClick,
  className = '',
}) => {
  // Use OpenAI hook for ChatGPT integration
  const { theme, toolOutput } = useOpenAI();
  const isDark = theme === 'dark';

  // Get task data from toolOutput (ChatGPT) or props (standalone)
  const taskData = toolOutput?.output || { task: propTask, score: propScore, reasoning: propReasoning };
  const task = taskData.task || propTask;
  const score = taskData.score ?? propScore;
  const reasoning = taskData.reasoning || propReasoning;

  // Early return if no task data
  if (!task) {
    return (
      <div style={{ padding: '16px', color: isDark ? '#ffffff' : '#000000' }}>
        No task data available
      </div>
    );
  }

  const priorityColors = getPriorityColors(task.priority, isDark);
  const dueDateText = formatDueDate(task.due_date);
  const effortText = formatEffort(task.effort_estimate_minutes);
  const overdueStatus = isOverdue(task.due_date);

  // Base colors
  const colors = {
    background: isDark ? '#1a1a1a' : '#ffffff',
    text: isDark ? '#ffffff' : '#000000',
    textSecondary: isDark ? '#b0b0b0' : '#666666',
    border: isDark ? '#404040' : '#e0e0e0',
    accent: '#007aff',
  };

  // Container styles
  const containerStyle: React.CSSProperties = {
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif",
    backgroundColor: colors.background,
    border: `1px solid ${colors.border}`,
    borderRadius: '8px',
    padding: '16px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
    cursor: onTaskClick ? 'pointer' : 'default',
    transition: 'box-shadow 0.2s ease, transform 0.2s ease',
    maxWidth: '600px',
    width: '100%',
  };

  const containerHoverStyle: React.CSSProperties = onTaskClick
    ? {
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        transform: 'translateY(-2px)',
      }
    : {};

  // Priority badge styles
  const priorityBadgeStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
    padding: '4px 12px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: '600',
    backgroundColor: priorityColors.background,
    color: priorityColors.text,
    border: `1px solid ${priorityColors.border}`,
  };

  const priorityDotStyle: React.CSSProperties = {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: priorityColors.border,
  };

  // Title styles
  const titleStyle: React.CSSProperties = {
    fontSize: '18px',
    fontWeight: '600',
    color: colors.text,
    margin: '12px 0 8px 0',
    lineHeight: '1.4',
  };

  // Description styles
  const descriptionStyle: React.CSSProperties = {
    fontSize: '14px',
    color: colors.textSecondary,
    lineHeight: '1.5',
    margin: '0 0 12px 0',
  };

  // Metadata row styles
  const metadataRowStyle: React.CSSProperties = {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '12px',
    alignItems: 'center',
    fontSize: '13px',
    color: colors.textSecondary,
    marginBottom: '12px',
  };

  const metadataItemStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  };

  const dueDateStyle: React.CSSProperties = {
    ...metadataItemStyle,
    color: overdueStatus ? (isDark ? '#ffcdd2' : '#c62828') : colors.textSecondary,
    fontWeight: overdueStatus ? '600' : '400',
  };

  // Score section styles
  const scoreSectionStyle: React.CSSProperties = {
    marginTop: '12px',
    padding: '12px',
    backgroundColor: isDark ? 'rgba(0, 122, 255, 0.1)' : 'rgba(0, 122, 255, 0.05)',
    borderRadius: '6px',
    border: `1px solid ${isDark ? 'rgba(0, 122, 255, 0.2)' : 'rgba(0, 122, 255, 0.15)'}`,
  };

  const scoreHeaderStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
  };

  const scoreLabelStyle: React.CSSProperties = {
    fontSize: '12px',
    fontWeight: '600',
    color: colors.accent,
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  };

  const scoreValueStyle: React.CSSProperties = {
    fontSize: '20px',
    fontWeight: '700',
    color: colors.accent,
  };

  const recommendationStyle: React.CSSProperties = {
    fontSize: '13px',
    color: colors.text,
    lineHeight: '1.5',
    margin: '8px 0 0 0',
  };

  const reasoningDetailsStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
    gap: '8px',
    marginTop: '8px',
    fontSize: '12px',
  };

  const reasoningItemStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '4px 0',
  };

  const reasoningLabelStyle: React.CSSProperties = {
    color: colors.textSecondary,
  };

  const reasoningValueStyle: React.CSSProperties = {
    fontWeight: '600',
    color: colors.text,
  };

  // Event handlers
  const [isHovered, setIsHovered] = useState(false);

  const handleClick = () => {
    if (onTaskClick) {
      onTaskClick(task.id);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (onTaskClick && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      onTaskClick(task.id);
    }
  };

  return (
    <div
      className={className}
      style={{
        ...containerStyle,
        ...(isHovered ? containerHoverStyle : {}),
      }}
      onClick={handleClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onKeyDown={handleKeyDown}
      role={onTaskClick ? 'button' : 'article'}
      tabIndex={onTaskClick ? 0 : undefined}
      aria-label={`Task: ${task.title}`}
    >
      {/* Priority Badge */}
      <div style={priorityBadgeStyle} aria-label={`Priority: ${priorityColors.label}`}>
        <span style={priorityDotStyle} aria-hidden="true" />
        <span>{priorityColors.label}</span>
      </div>

      {/* Title */}
      <h3 style={titleStyle}>{task.title}</h3>

      {/* Description */}
      {task.description && (
        <p style={descriptionStyle}>{task.description}</p>
      )}

      {/* Metadata Row */}
      <div style={metadataRowStyle}>
        {dueDateText && (
          <div style={dueDateStyle} aria-label={`Due date: ${dueDateText}`}>
            <span aria-hidden="true">📅</span>
            <span>{dueDateText}</span>
          </div>
        )}
        {effortText && (
          <div style={metadataItemStyle} aria-label={`Estimated effort: ${effortText}`}>
            <span aria-hidden="true">⏱️</span>
            <span>{effortText}</span>
          </div>
        )}
        {task.tags && (
          <div style={metadataItemStyle} aria-label={`Tags: ${task.tags}`}>
            <span aria-hidden="true">🏷️</span>
            <span>{task.tags}</span>
          </div>
        )}
      </div>

      {/* AI Score Section */}
      {score !== undefined && reasoning && (
        <div style={scoreSectionStyle}>
          <div style={scoreHeaderStyle}>
            <span style={scoreLabelStyle}>AI Score</span>
            <span style={scoreValueStyle} aria-label={`Score: ${score.toFixed(1)}`}>
              {score.toFixed(1)}
            </span>
          </div>

          {reasoning.recommendation && (
            <p style={recommendationStyle}>{reasoning.recommendation}</p>
          )}

          {/* Reasoning Details */}
          <div style={reasoningDetailsStyle} aria-label="Scoring breakdown">
            <div style={reasoningItemStyle}>
              <span style={reasoningLabelStyle}>Priority:</span>
              <span style={reasoningValueStyle}>{reasoning.priority_score}</span>
            </div>
            <div style={reasoningItemStyle}>
              <span style={reasoningLabelStyle}>Urgency:</span>
              <span style={reasoningValueStyle}>{reasoning.deadline_urgency.toFixed(1)}</span>
            </div>
            <div style={reasoningItemStyle}>
              <span style={reasoningLabelStyle}>Effort:</span>
              <span style={reasoningValueStyle}>{reasoning.effort_bonus}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TaskCard;
