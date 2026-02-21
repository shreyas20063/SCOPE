/**
 * FundamentalModesViewer
 *
 * Custom viewer for the Fundamental Modes Superposition simulation.
 * Shows equation banner, mode summary cards, plots, and reconstruct mode UI.
 */

import React, { useCallback, useMemo } from 'react';
import PlotDisplay from './PlotDisplay';
import '../styles/FundamentalModesViewer.css';

function FundamentalModesViewer({ metadata, plots, onButtonClick, isUpdating }) {
  const equation = metadata?.equation;
  const modeInfo = metadata?.mode_info || [];
  const isReconstruct = metadata?.is_reconstruct;
  const reconstructInfo = metadata?.reconstruct_info;

  // Separate plots by ID for custom layout
  const modesPlot = useMemo(() => plots?.filter(p => p.id === 'modes_overlay') || [], [plots]);
  const poleMapPlot = useMemo(() => plots?.filter(p => p.id === 'pole_map') || [], [plots]);
  const envelopesPlot = useMemo(() => plots?.filter(p => p.id === 'mode_envelopes') || [], [plots]);

  const handleNewChallenge = useCallback(() => {
    if (!isUpdating) onButtonClick('new_challenge', {});
  }, [onButtonClick, isUpdating]);

  const handleReveal = useCallback(() => {
    if (!isUpdating) onButtonClick('show_answer', {});
  }, [onButtonClick, isUpdating]);

  // Rating color
  const ratingColor = useMemo(() => {
    if (!reconstructInfo) return null;
    const colors = {
      EXCELLENT: 'var(--success-color)',
      GOOD: 'var(--primary-color)',
      FAIR: 'var(--warning-color)',
      POOR: 'var(--error-color)',
    };
    return colors[reconstructInfo.rating] || 'var(--text-secondary)';
  }, [reconstructInfo]);

  return (
    <div className="fundamental-modes-viewer">
      {/* Equation banner */}
      {equation && (
        <div className="fm-equation-banner" role="status" aria-live="polite">
          <span className="fm-equation-text">{equation}</span>
          <span className="fm-equation-label">for n &ge; 0</span>
        </div>
      )}

      {/* Mode summary cards */}
      {modeInfo.length > 0 && (
        <div className="fm-mode-cards" role="list" aria-label="Fundamental modes summary">
          {modeInfo.map((mode) => (
            <div
              key={mode.index}
              className="fm-mode-card"
              style={{ borderLeftColor: mode.color }}
              role="listitem"
            >
              <div className="fm-mode-header">
                <span
                  className="fm-mode-dot"
                  style={{ backgroundColor: mode.color }}
                  aria-hidden="true"
                />
                <span className="fm-mode-title">Mode {mode.index}</span>
              </div>
              <div className="fm-mode-details">
                <span className="fm-mode-param">
                  p = {mode.pole}
                </span>
                <span className="fm-mode-param">
                  A = {mode.weight}
                </span>
              </div>
              <div className="fm-mode-status">
                <span className={`fm-mode-badge ${mode.convergence}`}>
                  {mode.convergence === 'converges' ? 'Stable' : mode.convergence === 'diverges' ? 'Unstable' : 'Marginal'}
                </span>
                {mode.sign_behavior === 'alternating' && (
                  <span className="fm-mode-badge alternating">alternating</span>
                )}
                {mode.half_life !== null && (
                  <span className="fm-mode-halflife">
                    t&frac12; = {mode.half_life} samples
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Reconstruct mode score panel */}
      {isReconstruct && reconstructInfo && (
        <div className="fm-reconstruct-panel" role="status" aria-live="polite">
          <div className="fm-score-section">
            <span className="fm-score-label">RMS Error:</span>
            <span className="fm-score-value" style={{ color: ratingColor }}>
              {reconstructInfo.rms_error.toFixed(4)}
            </span>
            <span className="fm-rating-badge" style={{ color: ratingColor, borderColor: ratingColor }}>
              {reconstructInfo.rating}
            </span>
          </div>
          <div className="fm-challenge-actions">
            <button
              className="fm-action-btn new-challenge"
              onClick={handleNewChallenge}
              disabled={isUpdating}
              aria-label="Generate new challenge"
            >
              New Challenge
            </button>
            <button
              className="fm-action-btn reveal"
              onClick={handleReveal}
              disabled={isUpdating || reconstructInfo.revealed}
              aria-label="Reveal answer"
            >
              {reconstructInfo.revealed ? 'Revealed' : 'Reveal Answer'}
            </button>
          </div>
          {reconstructInfo.revealed && reconstructInfo.answer_poles && (
            <div className="fm-answer-reveal">
              <span className="fm-answer-label">Answer:</span>
              {reconstructInfo.answer_poles.map((p, i) => (
                <span key={i} className="fm-answer-term">
                  {reconstructInfo.answer_weights[i] >= 0 && i > 0 ? ' + ' : i > 0 ? ' ' : ''}
                  {reconstructInfo.answer_weights[i]}&middot;({p})&#x207F;
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Plot layout: main modes plot + pole map side by side */}
      <div className="fm-plots-row">
        <div className="fm-plot-main">
          <PlotDisplay plots={modesPlot} isLoading={false} />
        </div>
        <div className="fm-plot-side">
          <PlotDisplay plots={poleMapPlot} isLoading={false} />
        </div>
      </div>

      {/* Envelopes plot (full width) */}
      <div className="fm-plot-full">
        <PlotDisplay plots={envelopesPlot} isLoading={false} />
      </div>
    </div>
  );
}

export default FundamentalModesViewer;
