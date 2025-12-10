import { useEffect, useState } from 'react';

/**
 * Generic debounced value hook used across forms and pickers.
 */
export const useDebouncedValue = <T>(value: T, delay: number): T => {
  const [current, setCurrent] = useState(value);

  useEffect(() => {
    const handle = window.setTimeout(() => setCurrent(value), delay);
    return () => window.clearTimeout(handle);
  }, [value, delay]);

  return current;
};
