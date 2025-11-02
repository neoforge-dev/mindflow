/**
 * React hook for widget state persistence in ChatGPT
 * Allows saving and loading state across chat sessions
 */

import { useState, useEffect, useCallback } from 'react';
import { useOpenAI } from './useOpenAI';

interface UseWidgetStateOptions<T> {
  /**
   * Default state value if no saved state exists
   */
  defaultState: T;

  /**
   * Key to use for state storage (optional, defaults to widgetId)
   */
  storageKey?: string;
}

interface UseWidgetStateResult<T> {
  /**
   * Current state value
   */
  state: T;

  /**
   * Update state and persist to ChatGPT
   */
  setState: (newState: T | ((prev: T) => T)) => Promise<void>;

  /**
   * Whether the state is loaded
   */
  isLoaded: boolean;

  /**
   * Whether a save operation is in progress
   */
  isSaving: boolean;

  /**
   * Error from last save/load operation
   */
  error: Error | null;
}

/**
 * Hook to persist widget state in ChatGPT across sessions
 *
 * @example
 * ```tsx
 * interface FilterState {
 *   showCompleted: boolean;
 *   sortBy: 'priority' | 'dueDate';
 * }
 *
 * function TaskWidget() {
 *   const { state, setState } = useWidgetState<FilterState>({
 *     defaultState: { showCompleted: false, sortBy: 'priority' }
 *   });
 *
 *   return (
 *     <div>
 *       <button onClick={() => setState({ ...state, showCompleted: !state.showCompleted })}>
 *         Toggle Completed Tasks
 *       </button>
 *     </div>
 *   );
 * }
 * ```
 */
export function useWidgetState<T = any>(
  options: UseWidgetStateOptions<T>
): UseWidgetStateResult<T> {
  const { defaultState, storageKey } = options;
  const { openai, isInChatGPT } = useOpenAI();

  const [state, setStateInternal] = useState<T>(defaultState);
  const [isLoaded, setIsLoaded] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // Load saved state on mount
  useEffect(() => {
    const loadState = async () => {
      if (!isInChatGPT || !openai) {
        setIsLoaded(true);
        return;
      }

      try {
        const savedState = await openai.getWidgetState();

        if (savedState) {
          const stateKey = storageKey || 'default';
          const value = savedState[stateKey];

          if (value !== undefined) {
            setStateInternal(value as T);
          }
        }

        setIsLoaded(true);
      } catch (err) {
        console.error('Failed to load widget state:', err);
        setError(err instanceof Error ? err : new Error(String(err)));
        setIsLoaded(true);
      }
    };

    loadState();
  }, [isInChatGPT, openai, storageKey]);

  // Set state and persist to ChatGPT
  const setState = useCallback(async (newState: T | ((prev: T) => T)) => {
    const nextState = typeof newState === 'function'
      ? (newState as (prev: T) => T)(state)
      : newState;

    setStateInternal(nextState);

    if (!isInChatGPT || !openai) {
      // Not in ChatGPT - just update local state
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      const stateKey = storageKey || 'default';
      await openai.setWidgetState({ [stateKey]: nextState });
    } catch (err) {
      console.error('Failed to save widget state:', err);
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setIsSaving(false);
    }
  }, [state, isInChatGPT, openai, storageKey]);

  return {
    state,
    setState,
    isLoaded,
    isSaving,
    error,
  };
}
