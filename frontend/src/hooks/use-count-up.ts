'use client';

import { useEffect, useRef, useState } from 'react';

/**
 * Hook that animates a number counting up from 0 to the target value.
 * Useful for KPI cards and dashboard stats.
 *
 * @param target The final value to count up to
 * @param duration Animation duration in milliseconds (default: 1000)
 * @returns The current animated value
 */
export function useCountUp(target: number, duration: number = 1000): number {
  const [value, setValue] = useState(0);
  const frameRef = useRef<number | undefined>(undefined);
  const startTimeRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    // Reset start time when target changes
    startTimeRef.current = undefined;

    const animate = (timestamp: number) => {
      if (startTimeRef.current === undefined) {
        startTimeRef.current = timestamp;
      }

      const elapsed = timestamp - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1);

      // Ease-out cubic for smooth deceleration
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(target * eased);

      setValue(current);

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(animate);
      }
    };

    frameRef.current = requestAnimationFrame(animate);

    return () => {
      if (frameRef.current) {
        cancelAnimationFrame(frameRef.current);
      }
    };
  }, [target, duration]);

  return value;
}

/**
 * Hook that animates a percentage value counting up, returning a formatted string.
 */
export function useCountUpPercent(target: number, duration: number = 1000): string {
  const value = useCountUp(target, duration);
  return `${value}%`;
}
