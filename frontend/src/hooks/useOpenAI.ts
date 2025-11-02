/**
 * React hook to access ChatGPT's window.openai API
 * Provides safe access to the OpenAI global object with proper error handling
 */

import { useState, useEffect } from 'react';
import type { OpenAIGlobal, Theme, ToolOutput } from '../types/openai';

interface UseOpenAIResult {
  /**
   * Whether the component is running in ChatGPT
   */
  isInChatGPT: boolean;

  /**
   * Current theme (light or dark)
   */
  theme: Theme;

  /**
   * Tool output data from MCP server
   */
  toolOutput: ToolOutput | null;

  /**
   * Call an MCP tool
   */
  callTool: (name: string, args?: Record<string, any>) => Promise<any>;

  /**
   * The raw OpenAI global object (for advanced use)
   */
  openai: OpenAIGlobal | null;
}

/**
 * Hook to access ChatGPT's window.openai API
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { isInChatGPT, theme, toolOutput, callTool } = useOpenAI();
 *
 *   if (!isInChatGPT) {
 *     return <div>Not running in ChatGPT</div>;
 *   }
 *
 *   return (
 *     <div style={{ background: theme === 'dark' ? '#000' : '#fff' }}>
 *       <pre>{JSON.stringify(toolOutput, null, 2)}</pre>
 *       <button onClick={() => callTool('refresh_task')}>Refresh</button>
 *     </div>
 *   );
 * }
 * ```
 */
export function useOpenAI(): UseOpenAIResult {
  const [openai, setOpenai] = useState<OpenAIGlobal | null>(null);
  const [theme, setTheme] = useState<Theme>('light');

  useEffect(() => {
    // Check if window.openai is available
    if (typeof window !== 'undefined' && window.openai) {
      setOpenai(window.openai);
      setTheme(window.openai.theme || 'light');

      // Listen for theme changes if supported
      // Note: ChatGPT may not support theme change events yet
      // This is future-proofing for when they add it
      const handleThemeChange = () => {
        if (window.openai) {
          setTheme(window.openai.theme || 'light');
        }
      };

      // Check if there's a theme change event
      // @ts-ignore - This may not exist in all versions
      if (window.openai.onThemeChange) {
        // @ts-ignore
        window.openai.onThemeChange(handleThemeChange);
      }

      return () => {
        // Cleanup if needed
        // @ts-ignore
        if (window.openai?.offThemeChange) {
          // @ts-ignore
          window.openai.offThemeChange(handleThemeChange);
        }
      };
    } else {
      // Not in ChatGPT - use system preference as fallback
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light';
      setTheme(systemTheme);
    }
  }, []);

  const callTool = async (name: string, args?: Record<string, any>): Promise<any> => {
    if (!openai) {
      throw new Error('window.openai not available - not running in ChatGPT');
    }

    try {
      return await openai.callTool({
        name,
        arguments: args,
      });
    } catch (error) {
      console.error(`Failed to call tool "${name}":`, error);
      throw error;
    }
  };

  return {
    isInChatGPT: !!openai,
    theme,
    toolOutput: openai?.toolOutput || null,
    callTool,
    openai,
  };
}
