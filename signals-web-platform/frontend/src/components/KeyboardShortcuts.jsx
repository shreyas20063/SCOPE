/**
 * KeyboardShortcuts Component
 *
 * Modal displaying available keyboard shortcuts.
 * Also provides the useKeyboardShortcuts hook for handling shortcuts.
 */

import React, { useEffect, useCallback } from 'react';

const SHORTCUTS = [
  { key: 'R', description: 'Reset parameters to defaults' },
  { key: 'D', description: 'Toggle dark/light mode' },
  { key: '?', description: 'Show keyboard shortcuts' },
  { key: 'Esc', description: 'Close modal / Stop animation' },
  { key: 'Space', description: 'Play/Pause animation' },
];

function KeyboardShortcutsModal({ isOpen, onClose }) {
  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Close on backdrop click
  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="shortcuts-modal-overlay"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="shortcuts-title"
    >
      <div className="shortcuts-modal">
        <h3 id="shortcuts-title">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <rect x="2" y="4" width="20" height="16" rx="2" ry="2" />
            <path d="M6 8h.001" />
            <path d="M10 8h.001" />
            <path d="M14 8h.001" />
            <path d="M18 8h.001" />
            <path d="M8 12h.001" />
            <path d="M12 12h.001" />
            <path d="M16 12h.001" />
            <path d="M7 16h10" />
          </svg>
          Keyboard Shortcuts
        </h3>
        <div className="shortcuts-list">
          {SHORTCUTS.map(({ key, description }) => (
            <div key={key} className="shortcut-item">
              <span className="shortcut-desc">{description}</span>
              <span className="shortcut-key">{key}</span>
            </div>
          ))}
        </div>
        <button className="shortcuts-close" onClick={onClose}>
          Close
        </button>
      </div>
    </div>
  );
}

/**
 * Hook for handling keyboard shortcuts
 */
export function useKeyboardShortcuts({
  onReset,
  onToggleTheme,
  onShowShortcuts,
  onToggleAnimation,
  onEscape,
}) {
  const handleKeyDown = useCallback((e) => {
    // Don't trigger shortcuts when typing in inputs
    if (
      e.target.tagName === 'INPUT' ||
      e.target.tagName === 'TEXTAREA' ||
      e.target.tagName === 'SELECT'
    ) {
      return;
    }

    switch (e.key.toLowerCase()) {
      case 'r':
        e.preventDefault();
        onReset?.();
        break;
      case 'd':
        e.preventDefault();
        onToggleTheme?.();
        break;
      case '?':
        e.preventDefault();
        onShowShortcuts?.();
        break;
      case ' ':
        e.preventDefault();
        onToggleAnimation?.();
        break;
      case 'escape':
        onEscape?.();
        break;
      default:
        break;
    }
  }, [onReset, onToggleTheme, onShowShortcuts, onToggleAnimation, onEscape]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}

export default KeyboardShortcutsModal;
