/**
 * Tests for TaskWidget component
 */

import React from 'react';
import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { TaskWidget } from './TaskWidget';

describe('TaskWidget', () => {
  const mockTaskOutput = {
    task: {
      id: '550e8400-e29b-41d4-a716-446655440000',
      user_id: 'user-123',
      title: 'Complete project documentation',
      description: 'Write comprehensive docs for the new feature',
      priority: 4,
      status: 'pending',
      due_date: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(), // 2 days from now
      tags: 'documentation, high-priority',
      effort_estimate_minutes: 120,
      created_at: '2024-01-15T08:00:00Z',
      updated_at: '2024-01-15T08:00:00Z',
    },
    score: 8.5,
    reasoning: {
      deadline_urgency: 2.5,
      priority_score: 40,
      effort_bonus: 10,
      total_score: 8.5,
      recommendation: 'High priority task worth focusing on',
    },
  };

  beforeEach(() => {
    // Reset window.openai mock
    (global as any).window = {
      openai: {
        theme: 'light',
        toolOutput: {
          output: mockTaskOutput,
        },
      },
    };
  });

  describe('Rendering', () => {
    it('should render task title', () => {
      render(<TaskWidget />);
      expect(
        screen.getByText('Complete project documentation')
      ).toBeInTheDocument();
    });

    it('should render task description', () => {
      render(<TaskWidget />);
      expect(
        screen.getByText('Write comprehensive docs for the new feature')
      ).toBeInTheDocument();
    });

    it('should render priority badge', () => {
      render(<TaskWidget />);
      expect(screen.getByText('High')).toBeInTheDocument();
    });

    it('should render AI score', () => {
      render(<TaskWidget />);
      expect(screen.getByText('8.5')).toBeInTheDocument();
    });

    it('should render recommendation', () => {
      render(<TaskWidget />);
      expect(
        screen.getByText('High priority task worth focusing on')
      ).toBeInTheDocument();
    });

    it('should render tags', () => {
      render(<TaskWidget />);
      expect(
        screen.getByText('documentation, high-priority')
      ).toBeInTheDocument();
    });
  });

  describe('Priority Levels', () => {
    it('should display "Urgent" for priority 5', () => {
      (global as any).window.openai.toolOutput.output.task.priority = 5;
      render(<TaskWidget />);
      expect(screen.getByText('Urgent')).toBeInTheDocument();
    });

    it('should display "High" for priority 4', () => {
      (global as any).window.openai.toolOutput.output.task.priority = 4;
      render(<TaskWidget />);
      expect(screen.getByText('High')).toBeInTheDocument();
    });

    it('should display "Medium" for priority 3', () => {
      (global as any).window.openai.toolOutput.output.task.priority = 3;
      render(<TaskWidget />);
      expect(screen.getByText('Medium')).toBeInTheDocument();
    });

    it('should display "Low" for priority 2', () => {
      (global as any).window.openai.toolOutput.output.task.priority = 2;
      render(<TaskWidget />);
      expect(screen.getByText('Low')).toBeInTheDocument();
    });

    it('should display "Very Low" for priority 1', () => {
      (global as any).window.openai.toolOutput.output.task.priority = 1;
      render(<TaskWidget />);
      expect(screen.getByText('Very Low')).toBeInTheDocument();
    });
  });

  describe('Due Date Formatting', () => {
    it('should show "Due in 2d" for task due in 2 days', () => {
      render(<TaskWidget />);
      expect(screen.getByText('Due in 2d')).toBeInTheDocument();
    });

    it('should show "Due today" for task due today', () => {
      (global as any).window.openai.toolOutput.output.task.due_date =
        new Date().toISOString();
      render(<TaskWidget />);
      expect(screen.getByText('Due today')).toBeInTheDocument();
    });

    it('should show "Due tomorrow" for task due tomorrow', () => {
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      (global as any).window.openai.toolOutput.output.task.due_date =
        tomorrow.toISOString();
      render(<TaskWidget />);
      expect(screen.getByText('Due tomorrow')).toBeInTheDocument();
    });

    it('should show "Overdue" for past due task', () => {
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      (global as any).window.openai.toolOutput.output.task.due_date =
        yesterday.toISOString();
      render(<TaskWidget />);
      expect(screen.getByText(/Overdue by \d+d/)).toBeInTheDocument();
    });

    it('should not render due date if null', () => {
      (global as any).window.openai.toolOutput.output.task.due_date = null;
      const { container } = render(<TaskWidget />);
      expect(container.textContent).not.toContain('Due');
    });
  });

  describe('Effort Estimation', () => {
    it('should show "2h" for 120 minutes', () => {
      render(<TaskWidget />);
      expect(screen.getByText('2h')).toBeInTheDocument();
    });

    it('should show "45m" for 45 minutes', () => {
      (global as any).window.openai.toolOutput.output.task.effort_estimate_minutes = 45;
      render(<TaskWidget />);
      expect(screen.getByText('45m')).toBeInTheDocument();
    });

    it('should show "1h 30m" for 90 minutes', () => {
      (global as any).window.openai.toolOutput.output.task.effort_estimate_minutes = 90;
      render(<TaskWidget />);
      expect(screen.getByText('1h 30m')).toBeInTheDocument();
    });

    it('should not render effort if null', () => {
      (global as any).window.openai.toolOutput.output.task.effort_estimate_minutes =
        null;
      const { container } = render(<TaskWidget />);
      expect(container.querySelector('[aria-label*="effort"]')).toBeNull();
    });
  });

  describe('Dark Mode', () => {
    it('should apply dark mode colors when theme is dark', () => {
      (global as any).window.openai.theme = 'dark';
      const { container } = render(<TaskWidget />);

      const widget = container.firstChild as HTMLElement;
      // Browser returns hex colors, not rgb
      expect(widget.style.backgroundColor).toMatch(/#1a1a1a|rgb\(26,\s*26,\s*26\)/);
    });

    it('should apply light mode colors when theme is light', () => {
      (global as any).window.openai.theme = 'light';
      const { container } = render(<TaskWidget />);

      const widget = container.firstChild as HTMLElement;
      // Browser returns hex colors, not rgb
      expect(widget.style.backgroundColor).toMatch(/#ffffff|rgb\(255,\s*255,\s*255\)/);
    });
  });

  describe('Reasoning Details', () => {
    it('should display priority score', () => {
      render(<TaskWidget />);
      expect(screen.getByText('40')).toBeInTheDocument();
    });

    it('should display deadline urgency', () => {
      render(<TaskWidget />);
      expect(screen.getByText('2.5')).toBeInTheDocument();
    });

    it('should display effort bonus', () => {
      render(<TaskWidget />);
      expect(screen.getByText('10')).toBeInTheDocument();
    });
  });

  describe('Optional Fields', () => {
    it('should not render description if null', () => {
      (global as any).window.openai.toolOutput.output.task.description = null;
      const { container } = render(<TaskWidget />);
      expect(
        container.textContent?.includes(
          'Write comprehensive docs for the new feature'
        )
      ).toBe(false);
    });

    it('should not render tags if null', () => {
      (global as any).window.openai.toolOutput.output.task.tags = null;
      render(<TaskWidget />);
      expect(
        screen.queryByText('documentation, high-priority')
      ).not.toBeInTheDocument();
    });

    it('should render recommendation if available', () => {
      render(<TaskWidget />);
      expect(
        screen.getByText('High priority task worth focusing on')
      ).toBeInTheDocument();
    });
  });
});
