/**
 * HubButton.jsx
 *
 * Nav bar button for toggling the System Hub panel.
 * Shows a green activity badge when any hub slot contains data.
 */

import React, { useMemo } from 'react';
import { useHubContext } from '../contexts/HubContext';

function HubButton({ isOpen, onToggle }) {
  const { hubState } = useHubContext();

  const hasData = useMemo(() => {
    return hubState.control !== null;
  }, [hubState]);

  return (
    <button
      className={`hub-button toolbar-button${isOpen ? ' hub-button--open' : ''}`}
      onClick={onToggle}
      aria-label="System Hub"
      title="System Hub"
    >
      <svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {/* Central circle */}
        <circle cx="12" cy="12" r="3" />
        {/* Corner circles */}
        <circle cx="4" cy="4" r="2" />
        <circle cx="20" cy="4" r="2" />
        <circle cx="4" cy="20" r="2" />
        <circle cx="20" cy="20" r="2" />
        {/* Connecting lines */}
        <line x1="9.5" y1="9.5" x2="5.5" y2="5.5" />
        <line x1="14.5" y1="9.5" x2="18.5" y2="5.5" />
        <line x1="9.5" y1="14.5" x2="5.5" y2="18.5" />
        <line x1="14.5" y1="14.5" x2="18.5" y2="18.5" />
      </svg>
      {hasData && <span className="hub-button__badge" />}
    </button>
  );
}

export default HubButton;
