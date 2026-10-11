/**
 * KeyboardShortcuts Component
 *
 * Modal displaying available keyboard shortcuts.
 * Also provides the useKeyboardShortcuts hook for handling shortcuts.
 */

import React, { useEffect, useCallback } from 'react';

const SHORTCUTS = [
  { key: 'R', description: 'Reset simulation parameters to defaults' },
  { key: 'D', description: 'Toggle dark/light mode' },
  { key: '?', description: 'Show keyboard shortcuts' },
  { key: 'Esc', description: 'Close dialog / Stop animation' },
  { key: 'Space', description: 'Play/Pause animation (animated simulations)' },
];

// Focus targets where single-key shortcuts must not fire: the user is typing.
const TEXT_ENTRY_SELECTOR = 'input, textarea, select, [contenteditable=""], [contenteditable="true"]';
// Focus targets that Space natively activates (or scrolls within).
const SPACE_ACTIVATED_SELECTOR = [
  'button', 'a[href]', 'summary', 'audio', 'video',
  '[role="button"]', '[role="link"]', '[role="checkbox"]', '[role="switch"]', '[role="radio"]',
  '[role="tab"]', '[role="menuitem"]', '[role="option"]', '[role="slider"]', '[role="listbox"]',
].join(', ');

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
 *
 * A key is only claimed (preventDefault) when its callback is provided, so
 * unhandled keys keep their browser behaviour (Space scrolls / activates the
 * focused button). Shortcuts never fire while typing in a form field, with
 * Ctrl/Cmd/Alt held (Cmd+R, Ctrl+D stay with the browser), or — apart from
 * "?" — while a modal dialog is open.
 */
export function useKeyboardShortcuts({
  onReset,
  onToggleTheme,
  onShowShortcuts,
  onToggleAnimation,
  onEscape,
}) {
  const handleKeyDown = useCallback((e) => {
    if (e.defaultPrevented || e.isComposing) return;
    if (e.ctrlKey || e.metaKey || e.altKey) return;

    const target = e.target instanceof Element ? e.target : null;
    if (target && (target.isContentEditable || target.closest(TEXT_ENTRY_SELECTOR))) {
      return;
    }

    const modalOpen = !!document.querySelector('[aria-modal="true"]');
    let handler;
    switch (e.key) {
      case '?':
        handler = onShowShortcuts;
        break;
      case 'r':
      case 'R':
        handler = modalOpen ? undefined : onReset;
        break;
      case 'd':
      case 'D':
        handler = modalOpen ? undefined : onToggleTheme;
        break;
      case ' ':
        if (!modalOpen && !target?.closest(SPACE_ACTIVATED_SELECTOR)) {
          handler = onToggleAnimation;
        }
        break;
      case 'Escape':
        // Never claimed: dialogs and other widgets handle Escape themselves.
        if (!modalOpen) onEscape?.();
        return;
      default:
        return;
    }

    if (!handler) return;
    e.preventDefault();
    if (!e.repeat) handler();
  }, [onReset, onToggleTheme, onShowShortcuts, onToggleAnimation, onEscape]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}

export default KeyboardShortcutsModal;
