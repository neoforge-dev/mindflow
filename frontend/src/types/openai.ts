/**
 * Type definitions for ChatGPT Apps SDK window.openai API
 * Based on official ChatGPT Apps SDK documentation
 */

export type DisplayMode = 'inline' | 'carousel' | 'fullscreen';
export type Theme = 'light' | 'dark';

export interface ToolOutput {
  /**
   * The output data from the MCP tool call
   */
  output: any;

  /**
   * Metadata about the tool execution
   */
  _meta?: {
    'openai/outputTemplate'?: string;
    'openai/displayMode'?: DisplayMode;
    'openai/widgetId'?: string;
  };
}

export interface CallToolOptions {
  /**
   * Name of the MCP tool to call
   */
  name: string;

  /**
   * Arguments to pass to the tool
   */
  arguments?: Record<string, any>;
}

export interface OpenAIGlobal {
  /**
   * Current theme (light or dark)
   */
  theme: Theme;

  /**
   * Get the tool output that triggered this component render
   */
  toolOutput: ToolOutput | null;

  /**
   * Call an MCP tool from within the component
   */
  callTool: (options: CallToolOptions) => Promise<any>;

  /**
   * Save widget state for persistence across sessions
   */
  setWidgetState: (state: Record<string, any>) => Promise<void>;

  /**
   * Load saved widget state
   */
  getWidgetState: () => Promise<Record<string, any> | null>;

  /**
   * Render a custom component (for carousel/fullscreen modes)
   */
  render?: (component: React.ReactElement) => void;
}

/**
 * Extend the Window interface to include openai global
 */
declare global {
  interface Window {
    openai?: OpenAIGlobal;
  }
}

export {};
