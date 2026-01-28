/**
 * @fileoverview Custom React hooks for the Portfolio Optimizer.
 * 
 * This module provides a collection of reusable hooks for:
 * - Async operations with loading/error states
 * - Input debouncing and throttling
 * - Persistent state with localStorage
 * - Responsive design with media queries
 * - Keyboard shortcut handling
 * 
 * @module hooks/useAsync
 * @author Portfolio Optimizer Team
 * @version 2.0.0
 */

import { useState, useCallback, useRef, useEffect } from 'react';

/**
 * Hook for managing async operations with loading, error, and retry logic.
 * 
 * Provides a consistent pattern for handling API calls with:
 * - Automatic loading state management
 * - Error capture and display
 * - Configurable retry logic with exponential backoff
 * - Success/error callbacks
 * 
 * @template T - The type of data returned by the async function
 * @template Args - The argument types for the async function
 * 
 * @param asyncFunction - The async function to execute
 * @param options - Configuration options
 * @param options.immediate - Execute immediately on mount (not implemented)
 * @param options.onSuccess - Callback when operation succeeds
 * @param options.onError - Callback when operation fails
 * @param options.retryCount - Number of retry attempts (default: 0)
 * @param options.retryDelay - Base delay between retries in ms (default: 1000)
 * 
 * @returns Object containing:
 *   - data: The result of the async operation (or null)
 *   - error: Any error that occurred (or null)
 *   - isLoading: Whether the operation is in progress
 *   - execute: Function to trigger the async operation
 *   - reset: Function to reset all state
 *   - retries: Number of retry attempts made
 * 
 * @example
 * const { data, isLoading, error, execute } = useAsync(
 *   (id: string) => fetchUserData(id),
 *   {
 *     onSuccess: (data) => console.log('Loaded:', data),
 *     onError: (err) => console.error('Failed:', err),
 *     retryCount: 3
 *   }
 * );
 * 
 * // Later, trigger the operation
 * await execute('user-123');
 */
export function useAsync<T, Args extends unknown[] = []>(
  asyncFunction: (...args: Args) => Promise<T>,
  options: {
    immediate?: boolean;
    onSuccess?: (data: T) => void;
    onError?: (error: Error) => void;
    retryCount?: number;
    retryDelay?: number;
  } = {}
) {
  const { onSuccess, onError, retryCount = 0, retryDelay = 1000 } = options;
  
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [retries, setRetries] = useState(0);
  
  const isMountedRef = useRef(true);
  
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);
  
  const execute = useCallback(
    async (...args: Args): Promise<T | null> => {
      setIsLoading(true);
      setError(null);
      
      let lastError: Error | null = null;
      let attempts = 0;
      
      while (attempts <= retryCount) {
        try {
          const result = await asyncFunction(...args);
          if (isMountedRef.current) {
            setData(result);
            setIsLoading(false);
            setRetries(attempts);
            onSuccess?.(result);
          }
          return result;
        } catch (err) {
          lastError = err instanceof Error ? err : new Error(String(err));
          attempts++;
          
          if (attempts <= retryCount) {
            await new Promise(resolve => setTimeout(resolve, retryDelay * attempts));
          }
        }
      }
      
      if (isMountedRef.current) {
        setError(lastError);
        setIsLoading(false);
        setRetries(attempts - 1);
        onError?.(lastError!);
      }
      
      return null;
    },
    [asyncFunction, onSuccess, onError, retryCount, retryDelay]
  );
  
  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setIsLoading(false);
    setRetries(0);
  }, []);
  
  return {
    data,
    error,
    isLoading,
    retries,
    execute,
    reset,
  };
}

/**
 * Hook for debouncing a value.
 * 
 * Delays updating the returned value until after the specified delay
 * has passed without the input value changing. Useful for search inputs
 * and other scenarios where you want to limit API calls.
 * 
 * @template T - The type of the value being debounced
 * @param value - The value to debounce
 * @param delay - Delay in milliseconds before updating
 * @returns The debounced value
 * 
 * @example
 * const [searchTerm, setSearchTerm] = useState('');
 * const debouncedSearch = useDebounce(searchTerm, 300);
 * 
 * useEffect(() => {
 *   if (debouncedSearch) {
 *     fetchSearchResults(debouncedSearch);
 *   }
 * }, [debouncedSearch]);
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    
    return () => clearTimeout(timer);
  }, [value, delay]);
  
  return debouncedValue;
}

/**
 * Hook for throttling callback execution.
 * 
 * Ensures the callback is only called at most once per delay period.
 * Unlike debounce, throttle allows the first call through immediately
 * and then limits subsequent calls.
 * 
 * @template T - The callback function type
 * @param callback - The function to throttle
 * @param delay - Minimum time between calls in milliseconds
 * @returns Throttled version of the callback
 * 
 * @example
 * const throttledScroll = useThrottle((event) => {
 *   console.log('Scroll position:', window.scrollY);
 * }, 100);
 * 
 * window.addEventListener('scroll', throttledScroll);
 */
export function useThrottle<T extends (...args: unknown[]) => unknown>(
  callback: T,
  delay: number
): T {
  const lastCallRef = useRef(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  return useCallback(
    ((...args) => {
      const now = Date.now();
      const timeSinceLastCall = now - lastCallRef.current;
      
      if (timeSinceLastCall >= delay) {
        lastCallRef.current = now;
        callback(...args);
      } else {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
        timeoutRef.current = setTimeout(() => {
          lastCallRef.current = Date.now();
          callback(...args);
        }, delay - timeSinceLastCall);
      }
    }) as T,
    [callback, delay]
  );
}

/**
 * Hook for persistent state with localStorage.
 * 
 * Works like useState but persists the value to localStorage, so it
 * survives page refreshes. Automatically serializes/deserializes JSON.
 * 
 * @template T - The type of the stored value
 * @param key - The localStorage key
 * @param initialValue - Default value if nothing is stored
 * @returns Tuple of [storedValue, setValue] like useState
 * 
 * @example
 * const [theme, setTheme] = useLocalStorage<'light' | 'dark'>('theme', 'dark');
 * 
 * // Value persists across page refreshes
 * setTheme('light');
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T | ((prev: T) => T)) => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch {
      return initialValue;
    }
  });
  
  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      setStoredValue(prev => {
        const nextValue = value instanceof Function ? value(prev) : value;
        try {
          window.localStorage.setItem(key, JSON.stringify(nextValue));
        } catch (error) {
          console.error('Failed to save to localStorage:', error);
        }
        return nextValue;
      });
    },
    [key]
  );
  
  return [storedValue, setValue];
}

/**
 * Hook for responsive design with CSS media queries.
 * 
 * Tracks whether a media query matches and updates when it changes.
 * Useful for responsive behavior that can't be achieved with CSS alone.
 * 
 * @param query - CSS media query string
 * @returns Boolean indicating if the query matches
 * 
 * @example
 * const isMobile = useMediaQuery('(max-width: 768px)');
 * const prefersReducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)');
 * 
 * if (isMobile) {
 *   return <MobileLayout />;
 * }
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia(query).matches;
    }
    return false;
  });
  
  useEffect(() => {
    const mediaQuery = window.matchMedia(query);
    const handler = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };
    
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, [query]);
  
  return matches;
}

/**
 * Hook for global keyboard shortcuts.
 * 
 * Registers a keyboard event listener for the specified key combination.
 * Automatically cleans up on unmount.
 * 
 * @param key - The key to listen for (e.g., 'r', 'Escape', 'Enter')
 * @param callback - Function to call when the shortcut is triggered
 * @param modifiers - Optional modifier keys that must be held
 * @param modifiers.ctrl - Require Ctrl key
 * @param modifiers.shift - Require Shift key
 * @param modifiers.alt - Require Alt key
 * @param modifiers.meta - Require Meta/Cmd key
 * 
 * @example
 * // Ctrl+R to run optimization
 * useKeyboardShortcut('r', handleRunOptimization, { ctrl: true });
 * 
 * // Escape to close modal
 * useKeyboardShortcut('Escape', handleCloseModal);
 * 
 * // Ctrl+Shift+S to save
 * useKeyboardShortcut('s', handleSave, { ctrl: true, shift: true });
 */
export function useKeyboardShortcut(
  key: string,
  callback: () => void,
  modifiers: { ctrl?: boolean; shift?: boolean; alt?: boolean; meta?: boolean } = {}
) {
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (
        event.key.toLowerCase() === key.toLowerCase() &&
        (!modifiers.ctrl || event.ctrlKey) &&
        (!modifiers.shift || event.shiftKey) &&
        (!modifiers.alt || event.altKey) &&
        (!modifiers.meta || event.metaKey)
      ) {
        event.preventDefault();
        callback();
      }
    };
    
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [key, callback, modifiers]);
}
