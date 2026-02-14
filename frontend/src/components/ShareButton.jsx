/**
 * ShareButton Component
 *
 * Button to copy shareable URL with current simulation parameters.
 */

import React, { useState, useCallback } from 'react';
import { getShareableUrl, copyToClipboard } from '../utils/urlParams';

function ShareButton({ params, className = '' }) {
  const [copied, setCopied] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  const handleShare = useCallback(async () => {
    const baseUrl = window.location.origin + window.location.pathname;
    const shareableUrl = getShareableUrl(baseUrl, params);

    const success = await copyToClipboard(shareableUrl);

    if (success) {
      setCopied(true);
      setShowTooltip(true);

      // Reset after 2 seconds
      setTimeout(() => {
        setCopied(false);
        setShowTooltip(false);
      }, 2000);
    }
  }, [params]);

  return (
    <div className={`share-button-container ${className}`}>
      <button
        className={`share-button ${copied ? 'copied' : ''}`}
        onClick={handleShare}
        aria-label="Copy shareable link"
        title="Copy shareable link"
      >
        {copied ? (
          <>
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
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <span>Copied!</span>
          </>
        ) : (
          <>
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
            >
              <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
              <polyline points="16 6 12 2 8 6" />
              <line x1="12" y1="2" x2="12" y2="15" />
            </svg>
            <span>Share</span>
          </>
        )}
      </button>
      {showTooltip && (
        <div className="share-tooltip" role="status" aria-live="polite">
          Link copied to clipboard!
        </div>
      )}
    </div>
  );
}

export default ShareButton;
