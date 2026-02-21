/**
 * CTImpulseResponseViewer Component
 *
 * Custom viewer for the CT Impulse Response Builder simulation.
 * Shows an SVG block diagram of the CT feedback loop with animated signal path,
 * an s-plane inset showing pole position, info panel with convergence status,
 * and term-by-term description as partial sums are added.
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import PlotDisplay from './PlotDisplay';
import '../styles/CTImpulseResponseViewer.css';

/**
 * SVG Block Diagram: delta(t) -> (+) -> [A (integral)] -> y(t) with xp feedback
 */
function CTBlockDiagram({ poleP, convergence, currentTerms, revision }) {
  const [pulseClass, setPulseClass] = useState('');
  const prevTermsRef = useRef(0);
  const prevRevisionRef = useRef(revision);

  useEffect(() => {
    // If revision changed (reset or pole change), clear animation
    if (revision !== prevRevisionRef.current) {
      prevRevisionRef.current = revision;
      prevTermsRef.current = 0;
      setPulseClass('');
      return;
    }

    if (currentTerms > prevTermsRef.current) {
      if (currentTerms === 1) {
        setPulseClass('active path-input');
      } else {
        setPulseClass('active path-loop');
      }
      const timer = setTimeout(() => setPulseClass(''), 1300);
      prevTermsRef.current = currentTerms;
      return () => clearTimeout(timer);
    }

    if (currentTerms < prevTermsRef.current) {
      prevTermsRef.current = currentTerms;
      setPulseClass('');
    }
  }, [currentTerms, revision]);

  const statusColor = convergence === 'converging' ? '#10b981'
    : convergence === 'diverging' ? '#ef4444'
    : '#f59e0b';

  const pDisplay = poleP % 1 === 0 ? poleP.toFixed(0) : poleP.toFixed(1);

  return (
    <div className="ct-svg-container">
      <svg viewBox="0 0 320 130" width="320" height="130" aria-label="CT feedback loop block diagram">
        <defs>
          <marker id="ct-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" className="arrow-head" />
          </marker>
        </defs>

        {/* Input delta(t) label */}
        <text x="3" y="54" className="signal-label" style={{ fontSize: '11px' }}>{'δ(t)'}</text>

        {/* Input arrow -> Adder */}
        <line x1="32" y1="50" x2="52" y2="50" className="arrow-line" markerEnd="url(#ct-arrow)" />

        {/* Adder circle (+) */}
        <circle cx="64" cy="50" r="11" className="adder-circle" />
        <line x1="58" y1="50" x2="70" y2="50" stroke="var(--primary-color)" strokeWidth="1.5" />
        <line x1="64" y1="44" x2="64" y2="56" stroke="var(--primary-color)" strokeWidth="1.5" />

        {/* Adder -> Integrator */}
        <line x1="75" y1="50" x2="115" y2="50" className="arrow-line" markerEnd="url(#ct-arrow)" />

        {/* Integrator block [A] */}
        <rect x="118" y="34" width="54" height="32" className="integrator-rect" />
        <text x="145" y="48" textAnchor="middle"
          style={{ fontSize: '14px', fontFamily: "'Fira Code', monospace", fill: 'var(--primary-color)', fontWeight: 700 }}>
          {'𝒜'}
        </text>
        <text x="145" y="60" textAnchor="middle"
          style={{ fontSize: '8px', fontFamily: "'Fira Code', monospace", fill: 'var(--text-muted)' }}>
          {'∫ dt'}
        </text>

        {/* Integrator -> Output */}
        <line x1="172" y1="50" x2="270" y2="50" className="arrow-line" markerEnd="url(#ct-arrow)" />

        {/* Output y(t) label */}
        <text x="278" y="54" className="signal-label" style={{ fontSize: '11px' }}>{'y(t)'}</text>

        {/* Y node down to feedback path */}
        <line x1="248" y1="50" x2="248" y2="98" className="arrow-line" />

        {/* Feedback path: horizontal line to gain block */}
        <line x1="248" y1="95" x2="155" y2="95" className="arrow-line" markerEnd="url(#ct-arrow)" />

        {/* Gain block (triangle pointing left) */}
        <polygon points="145,83 110,95 145,107" className="gain-triangle" />
        <text x="130" y="99" textAnchor="middle"
          style={{ fontSize: '11px', fontFamily: "'Fira Code', monospace", fill: statusColor, fontWeight: 600 }}>
          {'×p'}
        </text>

        {/* p value annotation */}
        <text x="127" y="120" textAnchor="middle"
          style={{ fontSize: '9px', fontFamily: "'Fira Code', monospace", fill: statusColor, opacity: 0.8 }}>
          {'=' + pDisplay}
        </text>

        {/* Gain -> Adder feedback */}
        <line x1="110" y1="95" x2="64" y2="95" className="arrow-line" />
        <line x1="64" y1="95" x2="64" y2="61" className="arrow-line" markerEnd="url(#ct-arrow)" />

        {/* Signal pulse dot */}
        <circle className={`ct-signal-pulse ${pulseClass}`} cx="20" cy="50" />
      </svg>
    </div>
  );
}

/**
 * S-Plane inset showing pole position on the real axis
 */
function SPlaneInset({ poleP }) {
  const svgW = 120;
  const svgH = 90;
  const padX = 12;
  const midX = svgW / 2;
  const midY = svgH / 2;

  const pClamped = Math.max(-5, Math.min(5, poleP));
  const poleX = midX + (pClamped / 5) * (midX - padX);
  const poleColor = poleP < 0 ? '#3b82f6' : poleP > 0 ? '#ef4444' : '#f59e0b';

  return (
    <div className="ct-splane-container">
      <span className="ct-splane-title">s-plane</span>
      <div className="ct-splane-inset">
        <svg viewBox={`0 0 ${svgW} ${svgH}`}>
          {/* LHP shading (stable) */}
          <rect x={padX} y="5" width={midX - padX} height={svgH - 10}
            fill="rgba(59,130,246,0.06)" />
          {/* RHP shading (unstable) */}
          <rect x={midX} y="5" width={midX - padX} height={svgH - 10}
            fill="rgba(239,68,68,0.06)" />

          {/* Imaginary axis (vertical at center) */}
          <line x1={midX} y1="5" x2={midX} y2={svgH - 5}
            stroke="rgba(148,163,184,0.4)" strokeWidth="1" strokeDasharray="3,3" />

          {/* Real axis (horizontal) */}
          <line x1={padX} y1={midY} x2={svgW - padX} y2={midY}
            stroke="rgba(148,163,184,0.3)" strokeWidth="1" />

          {/* Axis labels */}
          <text x={svgW - padX + 2} y={midY + 3}
            style={{ fontSize: '7px', fill: 'var(--text-muted)', fontFamily: "'Fira Code', monospace" }}>
            {'σ'}
          </text>
          <text x={midX + 3} y="10"
            style={{ fontSize: '7px', fill: 'var(--text-muted)', fontFamily: "'Fira Code', monospace" }}>
            {'jω'}
          </text>

          {/* LHP / RHP labels */}
          <text x={midX / 2 + padX / 2} y={svgH - 8} textAnchor="middle"
            style={{ fontSize: '6px', fill: 'rgba(59,130,246,0.5)', fontWeight: 600 }}>
            {'LHP'}
          </text>
          <text x={midX + (midX - padX) / 2} y={svgH - 8} textAnchor="middle"
            style={{ fontSize: '6px', fill: 'rgba(239,68,68,0.5)', fontWeight: 600 }}>
            {'RHP'}
          </text>

          {/* Pole marker */}
          <circle cx={poleX} cy={midY} r="5"
            fill={poleColor} stroke="white" strokeWidth="1.5"
            style={{ filter: `drop-shadow(0 0 4px ${poleColor})` }} />

          {/* Pole value label */}
          <text x={poleX} y={midY - 10} textAnchor="middle"
            style={{ fontSize: '8px', fill: poleColor, fontFamily: "'Fira Code', monospace", fontWeight: 600 }}>
            {poleP.toFixed(1)}
          </text>
        </svg>
      </div>
    </div>
  );
}

/**
 * Info panel showing equation and convergence status
 */
function InfoPanel({ metadata }) {
  if (!metadata) return null;

  const { pole_p, convergence, current_terms, max_terms, max_error } = metadata;
  const pDisplay = pole_p % 1 === 0 ? pole_p.toFixed(0) : pole_p.toFixed(1);

  const statusLabels = {
    converging: 'Stable',
    diverging: 'Unstable',
    marginal: 'Marginal',
  };

  const statusIcons = {
    converging: '\u25cf',
    diverging: '\u25b2',
    marginal: '\u25c6',
  };

  return (
    <div className="ct-info-panel">
      <div className="ct-equation">
        <span className="ct-equation-label">Operator Series:</span>
        <span style={{ color: 'var(--primary-color)' }}>{'𝒜'}</span>
        {'(1 + p𝒜 + p\u00b2𝒜\u00b2 + \u2026)'}
        <span style={{ color: 'var(--text-muted)', margin: '0 0.15rem' }}>{'\u2192'}</span>
        <span style={{ color: 'var(--accent-color)' }}>
          {'e'}
          <sup>{pDisplay}t</sup>
          {'u(t)'}
        </span>
      </div>
      <div className="ct-status-group">
        <span className={`ct-status-badge ${convergence}`} role="status" aria-live="polite">
          <span style={{ fontSize: '0.65rem' }}>{statusIcons[convergence]}</span>
          {statusLabels[convergence] || convergence}
        </span>
        <span className="ct-terms-info">
          {current_terms} / {max_terms} terms
        </span>
        {current_terms > 0 && (
          <span className="ct-error-info">
            max err: {max_error < 0.001 ? max_error.toExponential(1) : max_error.toFixed(3)}
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * Term description text during progressive buildup
 */
function TermDescription({ metadata }) {
  if (!metadata || metadata.current_terms === 0) return null;

  const k = metadata.current_terms;
  const p = metadata.pole_p;
  const pDisplay = p % 1 === 0 ? p.toFixed(0) : p.toFixed(1);

  let description;
  if (k === 1) {
    description = (
      <>
        <span className="highlight">Term 1:</span>{' '}
        Apply <span className="math">{'𝒜'}</span> to {'δ(t)'}: integral of {'δ(t)'} ={'  '}
        <span className="highlight">u(t)</span>{' '}
        <span style={{ color: 'var(--text-muted)' }}>{'— the constant "1" term'}</span>
      </>
    );
  } else if (k === 2) {
    description = (
      <>
        <span className="highlight">Term 2:</span>{' '}
        Signal loops back through {'×p'}, then <span className="math">{'𝒜'}</span> integrates:{' '}
        <span className="highlight">{'+ '}{pDisplay}{'t'}</span>{' '}
        <span style={{ color: 'var(--text-muted)' }}>{'— sum is now 1 + pt'}</span>
      </>
    );
  } else if (k === 3) {
    description = (
      <>
        <span className="highlight">Term 3:</span>{' '}
        Second loop: {'×p → 𝒜 → '}<span className="highlight">{'+ p\u00b2t\u00b2/2!'}</span>{' '}
        <span style={{ color: 'var(--text-muted)' }}>{'— sum = 1 + pt + p\u00b2t\u00b2/2!'}</span>
      </>
    );
  } else {
    description = (
      <>
        <span className="highlight">Term {k}:</span>{' '}
        Loop {k - 1}: {'𝒜'}^{k - 1} {'δ(t) = '}<span className="highlight">{'(pt)'}^{k - 1}/{(k - 1)}!</span>{' '}
        <span style={{ color: 'var(--text-muted)' }}>{'— partial sum \u2192 e'}^({pDisplay}t)</span>
      </>
    );
  }

  return (
    <div className="ct-term-description" aria-live="polite">
      {description}
    </div>
  );
}

/**
 * Main CTImpulseResponseViewer component
 */
function CTImpulseResponseViewer({ metadata, plots, onButtonClick, isUpdating }) {
  const handleAddTerm = useCallback(() => {
    if (onButtonClick) onButtonClick('add_term', {});
  }, [onButtonClick]);

  const handleRemoveTerm = useCallback(() => {
    if (onButtonClick) onButtonClick('remove_term', {});
  }, [onButtonClick]);

  const handleResetTerms = useCallback(() => {
    if (onButtonClick) onButtonClick('reset_terms', {});
  }, [onButtonClick]);

  const poleP = metadata?.pole_p ?? -2.0;
  const convergence = metadata?.convergence ?? 'converging';
  const currentTerms = metadata?.current_terms ?? 0;
  const maxTerms = metadata?.max_terms ?? 10;
  const revision = metadata?.revision ?? 0;

  return (
    <div className="ct-impulse-response-viewer">
      {/* Info Panel */}
      <InfoPanel metadata={metadata} />

      {/* Block Diagram Section */}
      <div className="ct-block-diagram-section">
        <div className="ct-diagram-header">
          <span className="ct-diagram-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
              <path d="M3 9h18M9 3v18" />
            </svg>
            CT Feedback Loop
          </span>
          <div className="ct-animation-controls">
            <button
              className="ct-animate-btn"
              onClick={handleRemoveTerm}
              disabled={isUpdating || currentTerms <= 0}
              aria-label="Remove term"
            >
              {'◀'}
            </button>
            <button
              className="ct-animate-btn primary"
              onClick={handleAddTerm}
              disabled={isUpdating || currentTerms >= maxTerms}
              aria-label="Add term"
            >
              {'▶ Add Term'}
            </button>
            <span className="ct-step-counter">
              {currentTerms > 0 ? `${currentTerms} / ${maxTerms}` : '— / —'}
            </span>
            <button
              className="ct-animate-btn"
              onClick={handleResetTerms}
              disabled={isUpdating || currentTerms === 0}
              aria-label="Reset terms"
            >
              {'↺ Reset'}
            </button>
          </div>
        </div>

        <div className="ct-diagram-content">
          <div className="ct-diagram-main">
            <CTBlockDiagram
              poleP={poleP}
              convergence={convergence}
              currentTerms={currentTerms}
              revision={revision}
            />
          </div>
          <SPlaneInset poleP={poleP} />
        </div>

        <TermDescription metadata={metadata} />
      </div>

      {/* Plots */}
      <PlotDisplay
        plots={plots}
        isLoading={false}
        emptyMessage="Click 'Add Term' to build up the Taylor series."
      />
    </div>
  );
}

export default CTImpulseResponseViewer;
