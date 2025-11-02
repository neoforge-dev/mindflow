/**
 * MindFlow Apps SDK - Core ChatGPT Integration
 *
 * Clean, elegant interface to window.openai with zero fallbacks.
 * This SDK assumes we're always running in ChatGPT.
 */

export interface ToolOutput<T = any> {
  output: T;
  _meta?: {
    'openai/outputTemplate'?: string;
    'openai/displayMode'?: 'inline' | 'carousel' | 'fullscreen';
    'openai/widgetId'?: string;
  };
}

export interface CallToolOptions {
  name: string;
  arguments?: Record<string, any>;
}

export interface WidgetState {
  [key: string]: any;
}

export class AppsSDKError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AppsSDKError';
  }
}

/**
 * Core Apps SDK singleton
 */
export class AppsSDK {
  private static instance: AppsSDK | null = null;

  private constructor() {
    if (!this.isAvailable()) {
      throw new AppsSDKError(
        'window.openai not available. This component must run in ChatGPT.'
      );
    }
  }

  static getInstance(): AppsSDK {
    if (!AppsSDK.instance) {
      AppsSDK.instance = new AppsSDK();
    }
    return AppsSDK.instance;
  }

  /**
   * Check if window.openai is available
   */
  private isAvailable(): boolean {
    return typeof window !== 'undefined' && !!window.openai;
  }

  /**
   * Get current theme
   */
  get theme(): 'light' | 'dark' {
    return window.openai!.theme;
  }

  /**
   * Get tool output data
   */
  getToolOutput<T = any>(): T {
    const toolOutput = window.openai!.toolOutput;
    if (!toolOutput) {
      throw new AppsSDKError('No tool output available');
    }
    return toolOutput.output as T;
  }

  /**
   * Call an MCP tool
   */
  async callTool<T = any>(options: CallToolOptions): Promise<T> {
    try {
      return await window.openai!.callTool(options);
    } catch (error) {
      throw new AppsSDKError(
        `Failed to call tool "${options.name}": ${error}`
      );
    }
  }

  /**
   * Save widget state
   */
  async saveState(state: WidgetState): Promise<void> {
    try {
      await window.openai!.setWidgetState(state);
    } catch (error) {
      throw new AppsSDKError(`Failed to save widget state: ${error}`);
    }
  }

  /**
   * Load widget state
   */
  async loadState(): Promise<WidgetState | null> {
    try {
      return await window.openai!.getWidgetState();
    } catch (error) {
      throw new AppsSDKError(`Failed to load widget state: ${error}`);
    }
  }

  /**
   * Get metadata from current tool output
   */
  getMetadata(): ToolOutput['_meta'] | null {
    return window.openai!.toolOutput?._meta || null;
  }
}

/**
 * Convenience function to get SDK instance
 */
export function getSDK(): AppsSDK {
  return AppsSDK.getInstance();
}
