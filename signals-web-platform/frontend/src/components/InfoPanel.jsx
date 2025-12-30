/**
 * InfoPanel Component
 *
 * Collapsible panel showing simulation description and educational content.
 */

import React, { useState } from 'react';

function InfoPanel({ title, description, equations = [], tips = [] }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className={`info-panel ${isExpanded ? 'expanded' : ''}`}>
      <button
        className="info-panel-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
        aria-controls="info-panel-content"
      >
        <div className="info-panel-header">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="10" />
            <path d="M12 16v-4" />
            <path d="M12 8h.01" />
          </svg>
          <span>About this simulation</span>
        </div>
        <svg
          className={`info-panel-chevron ${isExpanded ? 'rotated' : ''}`}
          xmlns="http://www.w3.org/2000/svg"
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      <div
        id="info-panel-content"
        className="info-panel-content"
        aria-hidden={!isExpanded}
      >
        {description && (
          <div className="info-section">
            <p className="info-description">{description}</p>
          </div>
        )}

        {equations.length > 0 && (
          <div className="info-section">
            <h4>Key Equations</h4>
            <div className="info-equations">
              {equations.map((eq, index) => (
                <div key={index} className="equation">
                  <code>{eq.formula}</code>
                  {eq.description && <span>{eq.description}</span>}
                </div>
              ))}
            </div>
          </div>
        )}

        {tips.length > 0 && (
          <div className="info-section">
            <h4>Tips</h4>
            <ul className="info-tips">
              {tips.map((tip, index) => (
                <li key={index}>{tip}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

export default InfoPanel;
