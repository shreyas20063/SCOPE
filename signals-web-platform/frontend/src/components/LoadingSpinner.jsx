/**
 * LoadingSpinner Component
 *
 * Animated loading indicator for async operations.
 */

import React from 'react';

function LoadingSpinner({ size = 'medium', text = 'Loading...' }) {
  const sizeMap = {
    small: 24,
    medium: 40,
    large: 60,
  };

  const spinnerSize = sizeMap[size] || sizeMap.medium;

  return (
    <div className={`loading-spinner loading-spinner--${size}`}>
      <svg
        width={spinnerSize}
        height={spinnerSize}
        viewBox="0 0 50 50"
        className="spinner-svg"
      >
        <circle
          className="spinner-track"
          cx="25"
          cy="25"
          r="20"
          fill="none"
          strokeWidth="4"
        />
        <circle
          className="spinner-progress"
          cx="25"
          cy="25"
          r="20"
          fill="none"
          strokeWidth="4"
          strokeLinecap="round"
        />
      </svg>
      {text && <span className="spinner-text">{text}</span>}
    </div>
  );
}

// Skeleton loader for content placeholders
export function Skeleton({ width = '100%', height = '1rem', className = '' }) {
  return (
    <div
      className={`skeleton ${className}`}
      style={{ width, height }}
      aria-hidden="true"
    />
  );
}

// Plot skeleton for loading plot placeholders
export function PlotSkeleton() {
  return (
    <div className="plot-skeleton">
      <div className="skeleton-title" />
      <div className="skeleton-chart" />
    </div>
  );
}

export default LoadingSpinner;
