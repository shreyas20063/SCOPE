/**
 * ResetButton Component
 *
 * Button to reset all simulation parameters to their default values.
 */

import React, { useState, useCallback } from 'react';

function ResetButton({ onReset, className = '' }) {
  const [resetting, setResetting] = useState(false);

  const handleReset = useCallback(() => {
    setResetting(true);

    // Call reset handler
    onReset?.();

    // Visual feedback
    setTimeout(() => {
      setResetting(false);
    }, 300);
  }, [onReset]);

  return (
    <button
      className={`reset-button ${resetting ? 'resetting' : ''} ${className}`}
      onClick={handleReset}
      aria-label="Reset parameters to defaults"
      title="Reset parameters to defaults (R)"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className={resetting ? 'spin' : ''}
      >
        <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
        <path d="M3 3v5h5" />
      </svg>
      <span>Reset</span>
    </button>
  );
}

export default ResetButton;
