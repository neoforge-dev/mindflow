/**
 * Tests for AppsSDK core module
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { AppsSDK, AppsSDKError, getSDK } from './AppsSDK';

describe('AppsSDK', () => {
  beforeEach(() => {
    // Reset singleton between tests
    (AppsSDK as any).instance = null;

    // Mock window.openai
    (global as any).window = {
      openai: {
        theme: 'light',
        toolOutput: {
          output: { task: { id: '123', title: 'Test Task' }, score: 8.5 },
          _meta: {
            'openai/displayMode': 'inline',
            'openai/widgetId': 'test-widget',
          },
        },
        callTool: vi.fn(async (options) => ({ result: 'success' })),
        setWidgetState: vi.fn(async (state) => {}),
        getWidgetState: vi.fn(async () => ({ saved: true })),
      },
    };
  });

  describe('getInstance', () => {
    it('should create singleton instance', () => {
      const sdk1 = AppsSDK.getInstance();
      const sdk2 = AppsSDK.getInstance();
      expect(sdk1).toBe(sdk2);
    });

    it('should throw error if window.openai not available', () => {
      (global as any).window = {};
      (AppsSDK as any).instance = null;

      expect(() => AppsSDK.getInstance()).toThrow(AppsSDKError);
      expect(() => AppsSDK.getInstance()).toThrow(
        'window.openai not available'
      );
    });

    it('should throw error if window is undefined', () => {
      (global as any).window = undefined;
      (AppsSDK as any).instance = null;

      expect(() => AppsSDK.getInstance()).toThrow(AppsSDKError);
    });
  });

  describe('theme', () => {
    it('should return light theme', () => {
      const sdk = AppsSDK.getInstance();
      expect(sdk.theme).toBe('light');
    });

    it('should return dark theme', () => {
      (global as any).window.openai.theme = 'dark';
      const sdk = AppsSDK.getInstance();
      expect(sdk.theme).toBe('dark');
    });
  });

  describe('getToolOutput', () => {
    it('should return tool output data', () => {
      const sdk = AppsSDK.getInstance();
      const output = sdk.getToolOutput();

      expect(output).toEqual({
        task: { id: '123', title: 'Test Task' },
        score: 8.5,
      });
    });

    it('should throw error if no tool output available', () => {
      (global as any).window.openai.toolOutput = null;
      const sdk = AppsSDK.getInstance();

      expect(() => sdk.getToolOutput()).toThrow(AppsSDKError);
      expect(() => sdk.getToolOutput()).toThrow('No tool output available');
    });

    it('should handle typed output', () => {
      interface TaskOutput {
        task: { id: string; title: string };
        score: number;
      }

      const sdk = AppsSDK.getInstance();
      const output = sdk.getToolOutput<TaskOutput>();

      expect(output.task.id).toBe('123');
      expect(output.score).toBe(8.5);
    });
  });

  describe('callTool', () => {
    it('should call MCP tool successfully', async () => {
      const sdk = AppsSDK.getInstance();
      const result = await sdk.callTool({ name: 'get_next_task' });

      expect(window.openai!.callTool).toHaveBeenCalledWith({
        name: 'get_next_task',
      });
      expect(result).toEqual({ result: 'success' });
    });

    it('should call tool with arguments', async () => {
      const sdk = AppsSDK.getInstance();
      await sdk.callTool({
        name: 'update_task',
        arguments: { taskId: '123', status: 'completed' },
      });

      expect(window.openai!.callTool).toHaveBeenCalledWith({
        name: 'update_task',
        arguments: { taskId: '123', status: 'completed' },
      });
    });

    it('should throw AppsSDKError on failure', async () => {
      (global as any).window.openai.callTool = vi.fn(async () => {
        throw new Error('Network error');
      });

      const sdk = AppsSDK.getInstance();

      await expect(
        sdk.callTool({ name: 'get_next_task' })
      ).rejects.toThrow(AppsSDKError);

      await expect(
        sdk.callTool({ name: 'get_next_task' })
      ).rejects.toThrow('Failed to call tool');
    });
  });

  describe('saveState', () => {
    it('should save widget state successfully', async () => {
      const sdk = AppsSDK.getInstance();
      const state = { filter: 'active', sortBy: 'priority' };

      await sdk.saveState(state);

      expect(window.openai!.setWidgetState).toHaveBeenCalledWith(state);
    });

    it('should throw AppsSDKError on failure', async () => {
      (global as any).window.openai.setWidgetState = vi.fn(async () => {
        throw new Error('Storage error');
      });

      const sdk = AppsSDK.getInstance();

      await expect(sdk.saveState({ test: true })).rejects.toThrow(
        AppsSDKError
      );

      await expect(sdk.saveState({ test: true })).rejects.toThrow(
        'Failed to save widget state'
      );
    });
  });

  describe('loadState', () => {
    it('should load widget state successfully', async () => {
      const sdk = AppsSDK.getInstance();
      const state = await sdk.loadState();

      expect(window.openai!.getWidgetState).toHaveBeenCalled();
      expect(state).toEqual({ saved: true });
    });

    it('should return null when no state exists', async () => {
      (global as any).window.openai.getWidgetState = vi.fn(async () => null);

      const sdk = AppsSDK.getInstance();
      const state = await sdk.loadState();

      expect(state).toBeNull();
    });

    it('should throw AppsSDKError on failure', async () => {
      (global as any).window.openai.getWidgetState = vi.fn(async () => {
        throw new Error('Storage error');
      });

      const sdk = AppsSDK.getInstance();

      await expect(sdk.loadState()).rejects.toThrow(AppsSDKError);
      await expect(sdk.loadState()).rejects.toThrow(
        'Failed to load widget state'
      );
    });
  });

  describe('getMetadata', () => {
    it('should return metadata from tool output', () => {
      const sdk = AppsSDK.getInstance();
      const metadata = sdk.getMetadata();

      expect(metadata).toEqual({
        'openai/displayMode': 'inline',
        'openai/widgetId': 'test-widget',
      });
    });

    it('should return null if no metadata available', () => {
      (global as any).window.openai.toolOutput = { output: { data: 'test' } };

      const sdk = AppsSDK.getInstance();
      const metadata = sdk.getMetadata();

      expect(metadata).toBeNull();
    });

    it('should return null if no tool output', () => {
      (global as any).window.openai.toolOutput = null;

      const sdk = AppsSDK.getInstance();
      const metadata = sdk.getMetadata();

      expect(metadata).toBeNull();
    });
  });

  describe('getSDK convenience function', () => {
    it('should return SDK instance', () => {
      const sdk = getSDK();
      expect(sdk).toBeInstanceOf(AppsSDK);
    });

    it('should return same instance as getInstance', () => {
      const sdk1 = getSDK();
      const sdk2 = AppsSDK.getInstance();
      expect(sdk1).toBe(sdk2);
    });
  });

  describe('AppsSDKError', () => {
    it('should be instanceof Error', () => {
      const error = new AppsSDKError('test error');
      expect(error).toBeInstanceOf(Error);
    });

    it('should have correct name', () => {
      const error = new AppsSDKError('test error');
      expect(error.name).toBe('AppsSDKError');
    });

    it('should preserve message', () => {
      const error = new AppsSDKError('test error');
      expect(error.message).toBe('test error');
    });
  });
});
