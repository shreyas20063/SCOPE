/**
 * Spinner Component
 *
 * Loading indicator displayed while fetching data or processing.
 */

import React from 'react';

function Spinner({ message = 'Loading...', size = 'medium', fullScreen = false }) {
  const sizeClasses = {
    small: 'spinner-small',
    medium: 'spinner-medium',
    large: 'spinner-large',
  };

  const spinnerContent = (
    <div className={`spinner-container ${fullScreen ? 'spinner-fullscreen' : ''}`}>
      <div className={`spinner ${sizeClasses[size] || sizeClasses.medium}`}>
        <div className="spinner-ring"></div>
        <div className="spinner-ring"></div>
        <div className="spinner-ring"></div>
      </div>
      {message && <p className="spinner-message">{message}</p>}
    </div>
  );

  return spinnerContent;
}

export default Spinner;
