/**
 * useMemoizedPlots Hook
 *
 * Memoizes plot data to prevent unnecessary re-renders.
 * Uses deep comparison for plot objects.
 */

import { useMemo, useRef } from 'react';

/**
 * Deep comparison for plot arrays
 */
function arePlotsEqual(prev, next) {
  if (prev.length !== next.length) return false;

  for (let i = 0; i < prev.length; i++) {
    const prevPlot = prev[i];
    const nextPlot = next[i];

    // Compare plot IDs and data lengths
    if (prevPlot.id !== nextPlot.id) return false;
    if (prevPlot.title !== nextPlot.title) return false;

    // Compare traces
    if (prevPlot.traces?.length !== nextPlot.traces?.length) return false;

    for (let j = 0; j < (prevPlot.traces?.length || 0); j++) {
      const prevTrace = prevPlot.traces[j];
      const nextTrace = nextPlot.traces[j];

      // Compare trace names and data lengths
      if (prevTrace.name !== nextTrace.name) return false;
      if (prevTrace.x?.length !== nextTrace.x?.length) return false;
      if (prevTrace.y?.length !== nextTrace.y?.length) return false;

      // Sample a few points to check for data changes
      const sampleIndices = [0, Math.floor(prevTrace.x?.length / 2), prevTrace.x?.length - 1];
      for (const idx of sampleIndices) {
        if (prevTrace.x?.[idx] !== nextTrace.x?.[idx]) return false;
        if (prevTrace.y?.[idx] !== nextTrace.y?.[idx]) return false;
      }
    }
  }

  return true;
}

/**
 * Hook to memoize plot data
 * @param {Array} plots - Array of plot objects
 * @returns {Array} Memoized plots
 */
export function useMemoizedPlots(plots) {
  const prevPlotsRef = useRef(plots);

  const memoizedPlots = useMemo(() => {
    if (arePlotsEqual(prevPlotsRef.current, plots)) {
      return prevPlotsRef.current;
    }
    prevPlotsRef.current = plots;
    return plots;
  }, [plots]);

  return memoizedPlots;
}

export default useMemoizedPlots;
