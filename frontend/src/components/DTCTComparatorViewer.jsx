/**
 * DTCTComparatorViewer
 *
 * Custom viewer for the DT ↔ CT Side-by-Side Comparator simulation.
 * Renders:
 * - Status badge with stability info for both domains
 * - Side-by-side Plotly plots (DT stem + CT continuous)
 * - SVG stability maps (unit circle + s-plane)
 * - Quiz mode for testing stability intuition
 */

import React, { useState, useCallback, useMemo } from 'react';
import Plot from 'react-plotly.js';
import '../styles/DTCTComparatorViewer.css';

// ── Theme hook ──────────────────────────────────────────────────────────────

function useTheme() {
  const [theme, setTheme] = React.useState(() =>
    document.documentElement.getAttribute('data-theme') || 'dark'
  );

  React.useEffect(() => {
    const observer = new MutationObserver(() => {
      setTheme(document.documentElement.getAttribute('data-theme') || 'dark');
    });
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme'],
    });
    return () => observer.disconnect();
  }, []);

  return theme;
}

// ── StatusBadge ─────────────────────────────────────────────────────────────

function StatusBadge({ metadata }) {
  if (!metadata) return null;

  const dtTagClass = metadata.dt_stable
    ? 'dtct-status-badge__tag--stable'
    : metadata.dt_status === 'Marginal'
    ? 'dtct-status-badge__tag--marginal'
    : 'dtct-status-badge__tag--unstable';

  const ctTagClass = metadata.ct_stable
    ? 'dtct-status-badge__tag--stable'
    : metadata.ct_status === 'Marginal'
    ? 'dtct-status-badge__tag--marginal'
    : 'dtct-status-badge__tag--unstable';

  const insightMap = {
    both_stable: 'Both systems converge',
    dt_only: 'DT converges but CT diverges!',
    ct_only: 'CT converges but DT diverges!',
    neither_stable: 'Both systems diverge',
  };

  return (
    <div className="dtct-status-badge" role="status" aria-live="polite">
      <span className="dtct-status-badge__pole">
        p = {metadata.pole_value}
      </span>
      <span className={`dtct-status-badge__tag ${dtTagClass}`}>
        DT: {metadata.dt_status}
      </span>
      <span className={`dtct-status-badge__tag ${ctTagClass}`}>
        CT: {metadata.ct_status}
      </span>
      {metadata.dt_is_alternating && (
        <span style={{
          padding: '2px 8px', border: '1px solid var(--warning-color)',
          borderRadius: 'var(--radius-sm)', color: 'var(--warning-color)',
          fontSize: '0.75rem',
        }}>
          Alternating
        </span>
      )}
      <span className="dtct-status-badge__insight">
        {insightMap[metadata.agreement] || ''}
      </span>
    </div>
  );
}

// ── ResponsePlot ────────────────────────────────────────────────────────────

function ResponsePlot({ plot, stabilityClass, label, theme }) {
  const isDark = theme === 'dark';

  const layout = useMemo(() => ({
    ...(plot.layout || {}),
    paper_bgcolor: isDark ? 'rgba(0,0,0,0)' : 'rgba(255,255,255,0.98)',
    plot_bgcolor: isDark ? 'rgba(0,0,0,0)' : '#f8fafc',
    font: {
      family: 'Inter, sans-serif',
      size: 12,
      color: isDark ? '#f1f5f9' : '#1e293b',
    },
    xaxis: {
      ...(plot.layout?.xaxis || {}),
      title: {
        ...(plot.layout?.xaxis?.title || {}),
        font: { color: isDark ? '#f1f5f9' : '#1e293b', size: 13 },
      },
      gridcolor: isDark ? 'rgba(148,163,184,0.1)' : 'rgba(148,163,184,0.25)',
      zerolinecolor: isDark ? 'rgba(148,163,184,0.3)' : 'rgba(148,163,184,0.5)',
      color: isDark ? '#94a3b8' : '#64748b',
    },
    yaxis: {
      ...(plot.layout?.yaxis || {}),
      title: {
        ...(plot.layout?.yaxis?.title || {}),
        font: { color: isDark ? '#f1f5f9' : '#1e293b', size: 13 },
      },
      gridcolor: isDark ? 'rgba(148,163,184,0.1)' : 'rgba(148,163,184,0.25)',
      zerolinecolor: isDark ? 'rgba(148,163,184,0.3)' : 'rgba(148,163,184,0.5)',
      color: isDark ? '#94a3b8' : '#64748b',
    },
    legend: {
      font: { color: isDark ? '#94a3b8' : '#64748b', size: 10 },
      bgcolor: 'rgba(0,0,0,0)',
    },
    margin: { t: 40, r: 20, b: 50, l: 55 },
    datarevision: plot.layout?.datarevision || `${plot.id}-${Date.now()}`,
    uirevision: plot.layout?.uirevision,
  }), [plot, isDark]);

  const config = useMemo(() => ({
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    displaylogo: false,
  }), []);

  return (
    <div className={`dtct-plot-panel dtct-plot-panel--${stabilityClass}`}>
      <Plot
        data={plot.data || []}
        layout={layout}
        config={config}
        useResizeHandler={true}
        style={{ width: '100%', height: '100%' }}
      />
      <div className="dtct-plot-panel__label">{label}</div>
    </div>
  );
}

// ── SVG Stability Maps ─────────────────────────────────────────────────────

const MAP_W = 240;
const MAP_H = 240;
const CX = MAP_W / 2;
const CY = MAP_H / 2;
const RADIUS = 80; // Unit circle radius in SVG coords

function UnitCircleMap({ poleValue, isStable, theme }) {
  const isDark = theme === 'dark';
  const axisColor = isDark ? '#475569' : '#94a3b8';
  const textColor = isDark ? '#94a3b8' : '#64748b';

  // Map pole to SVG x coordinate (real axis maps to horizontal)
  const poleX = CX + (poleValue / 2) * RADIUS;
  const poleColor = isStable ? '#10b981' : '#ef4444';
  const isOnBoundary = Math.abs(Math.abs(poleValue) - 1.0) < 0.05;

  return (
    <div className="dtct-stability-map">
      <div className="dtct-stability-map__title">DT: Unit Circle (|p| {'<'} 1)</div>
      <svg viewBox={`0 0 ${MAP_W} ${MAP_H}`} aria-label="DT stability map with unit circle">
        {/* Stable region fill (inside circle) */}
        <circle cx={CX} cy={CY} r={RADIUS}
          fill="rgba(16,185,129,0.08)" stroke="none" />
        {/* Unit circle */}
        <circle cx={CX} cy={CY} r={RADIUS}
          fill="none" stroke={isDark ? '#10b981' : '#059669'}
          strokeWidth="2" strokeDasharray="6,3" opacity="0.7" />

        {/* Axes */}
        <line x1="20" y1={CY} x2={MAP_W - 20} y2={CY}
          stroke={axisColor} strokeWidth="1" />
        <line x1={CX} y1="20" x2={CX} y2={MAP_H - 20}
          stroke={axisColor} strokeWidth="1" />

        {/* Tick marks on real axis */}
        {[-2, -1, 0, 1, 2].map(v => {
          const tx = CX + (v / 2) * RADIUS;
          return (
            <g key={v}>
              <line x1={tx} y1={CY - 4} x2={tx} y2={CY + 4}
                stroke={axisColor} strokeWidth="1" />
              <text x={tx} y={CY + 16} textAnchor="middle"
                fontSize="9" fill={textColor} fontFamily="'Fira Code', monospace">
                {v}
              </text>
            </g>
          );
        })}

        {/* Axis labels */}
        <text x={MAP_W - 15} y={CY - 8} textAnchor="end"
          fontSize="10" fill={textColor} fontFamily="Inter, sans-serif">Re</text>
        <text x={CX + 8} y="18"
          fontSize="10" fill={textColor} fontFamily="Inter, sans-serif">Im</text>

        {/* Boundary markers at ±1 */}
        <circle cx={CX + RADIUS / 2} cy={CY} r="3"
          fill="none" stroke={isDark ? '#f59e0b' : '#d97706'} strokeWidth="1.5" />
        <circle cx={CX - RADIUS / 2} cy={CY} r="3"
          fill="none" stroke={isDark ? '#f59e0b' : '#d97706'} strokeWidth="1.5" />

        {/* Region labels */}
        <text x={CX} y={CY - RADIUS / 2 - 4} textAnchor="middle"
          fontSize="8" fill="#10b981" fontWeight="600" fontFamily="Inter, sans-serif"
          opacity="0.8">STABLE</text>
        <text x={CX + RADIUS + 16} y={CY - 4} textAnchor="middle"
          fontSize="7" fill="#ef4444" fontWeight="500" fontFamily="Inter, sans-serif"
          opacity="0.7">UNSTABLE</text>

        {/* Pole marker glow */}
        <circle cx={poleX} cy={CY} r="12"
          fill={`${poleColor}20`} stroke="none" />
        {/* Pole marker */}
        <circle cx={poleX} cy={CY} r="7"
          fill={poleColor} stroke={isDark ? '#0f172a' : '#fff'}
          strokeWidth="2"
          style={{ filter: isOnBoundary ? 'drop-shadow(0 0 8px #f59e0b)' : `drop-shadow(0 0 4px ${poleColor})` }} />
        {/* Pole label */}
        <text x={poleX} y={CY - 16} textAnchor="middle"
          fontSize="10" fill={poleColor} fontWeight="600"
          fontFamily="'Fira Code', monospace">
          p={poleValue}
        </text>
      </svg>
    </div>
  );
}

function SPlaneMap({ poleValue, isStable, theme }) {
  const isDark = theme === 'dark';
  const axisColor = isDark ? '#475569' : '#94a3b8';
  const textColor = isDark ? '#94a3b8' : '#64748b';

  // Map pole to SVG x (left half = stable for CT)
  // Scale: p in [-2, 2] maps to [20, MAP_W-20]
  const poleX = CX + (poleValue / 2) * RADIUS;
  const poleColor = isStable ? '#10b981' : '#ef4444';
  const isOnBoundary = Math.abs(poleValue) < 0.05;

  return (
    <div className="dtct-stability-map">
      <div className="dtct-stability-map__title">CT: S-Plane (Re(p) {'<'} 0)</div>
      <svg viewBox={`0 0 ${MAP_W} ${MAP_H}`} aria-label="CT stability map with s-plane">
        {/* Stable region fill (left half-plane) */}
        <rect x="20" y="20" width={CX - 20} height={MAP_H - 40}
          fill="rgba(16,185,129,0.08)" rx="4" />

        {/* Unstable region fill (right half-plane) */}
        <rect x={CX} y="20" width={MAP_W - CX - 20} height={MAP_H - 40}
          fill="rgba(239,68,68,0.04)" rx="4" />

        {/* Stability boundary at Re=0 */}
        <line x1={CX} y1="20" x2={CX} y2={MAP_H - 20}
          stroke={isDark ? '#f59e0b' : '#d97706'}
          strokeWidth="2" strokeDasharray="6,3" opacity="0.7" />

        {/* Real axis */}
        <line x1="20" y1={CY} x2={MAP_W - 20} y2={CY}
          stroke={axisColor} strokeWidth="1" />
        {/* Imaginary axis */}
        <line x1={CX} y1="20" x2={CX} y2={MAP_H - 20}
          stroke={axisColor} strokeWidth="1" />

        {/* Tick marks */}
        {[-2, -1, 0, 1, 2].map(v => {
          const tx = CX + (v / 2) * RADIUS;
          return (
            <g key={v}>
              <line x1={tx} y1={CY - 4} x2={tx} y2={CY + 4}
                stroke={axisColor} strokeWidth="1" />
              <text x={tx} y={CY + 16} textAnchor="middle"
                fontSize="9" fill={textColor} fontFamily="'Fira Code', monospace">
                {v}
              </text>
            </g>
          );
        })}

        {/* Axis labels */}
        <text x={MAP_W - 15} y={CY - 8} textAnchor="end"
          fontSize="10" fill={textColor} fontFamily="Inter, sans-serif">Re</text>
        <text x={CX + 8} y="18"
          fontSize="10" fill={textColor} fontFamily="Inter, sans-serif">Im</text>

        {/* Region labels */}
        <text x={CX / 2 + 10} y={38} textAnchor="middle"
          fontSize="8" fill="#10b981" fontWeight="600" fontFamily="Inter, sans-serif"
          opacity="0.8">STABLE</text>
        <text x={CX + (MAP_W - CX) / 2 - 10} y={38} textAnchor="middle"
          fontSize="8" fill="#ef4444" fontWeight="600" fontFamily="Inter, sans-serif"
          opacity="0.8">UNSTABLE</text>

        {/* Pole marker glow */}
        <circle cx={poleX} cy={CY} r="12"
          fill={`${poleColor}20`} stroke="none" />
        {/* Pole marker */}
        <circle cx={poleX} cy={CY} r="7"
          fill={poleColor} stroke={isDark ? '#0f172a' : '#fff'}
          strokeWidth="2"
          style={{ filter: isOnBoundary ? 'drop-shadow(0 0 8px #f59e0b)' : `drop-shadow(0 0 4px ${poleColor})` }} />
        {/* Pole label */}
        <text x={poleX} y={CY - 16} textAnchor="middle"
          fontSize="10" fill={poleColor} fontWeight="600"
          fontFamily="'Fira Code', monospace">
          p={poleValue}
        </text>
      </svg>
    </div>
  );
}

// ── Quiz Panel ──────────────────────────────────────────────────────────────

const QUIZ_OPTIONS = [
  { value: 'both_stable', label: 'Both Stable' },
  { value: 'dt_only', label: 'DT Only' },
  { value: 'ct_only', label: 'CT Only' },
  { value: 'neither_stable', label: 'Neither' },
];

function QuizPanel({ quiz, onAnswer, onNewQuiz, isUpdating }) {
  if (!quiz) return null;

  const getOptionClass = (optValue) => {
    if (!quiz.answered) return 'dtct-quiz-option';
    if (optValue === quiz.correct_answer) return 'dtct-quiz-option dtct-quiz-option--correct';
    if (optValue === quiz.user_answer && !quiz.correct) return 'dtct-quiz-option dtct-quiz-option--incorrect';
    return 'dtct-quiz-option dtct-quiz-option--dimmed';
  };

  return (
    <div className="dtct-quiz-panel" role="region" aria-label="Quiz">
      <div className="dtct-quiz-panel__question">
        For <em>p = {quiz.quiz_p}</em>, which system(s) are stable?
      </div>

      <div className="dtct-quiz-options">
        {QUIZ_OPTIONS.map(opt => (
          <button
            key={opt.value}
            className={getOptionClass(opt.value)}
            onClick={() => !quiz.answered && onAnswer(opt.value)}
            disabled={quiz.answered || isUpdating}
            aria-label={opt.label}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {quiz.answered && (
        <div className="dtct-quiz-result">
          <span className={`dtct-quiz-result__text ${quiz.correct ? 'dtct-quiz-result__text--correct' : 'dtct-quiz-result__text--incorrect'}`}>
            {quiz.correct
              ? 'Correct!'
              : `Incorrect — the answer is "${QUIZ_OPTIONS.find(o => o.value === quiz.correct_answer)?.label}"`
            }
          </span>
          <button
            className="dtct-quiz-next-btn"
            onClick={onNewQuiz}
            disabled={isUpdating}
          >
            Next Question
          </button>
        </div>
      )}
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────────────

function DTCTComparatorViewer({ metadata, plots, onButtonClick, isUpdating }) {
  const theme = useTheme();
  const isQuizMode = metadata?.mode === 'quiz';

  const dtPlot = plots?.find(p => p.id === 'dt_response');
  const ctPlot = plots?.find(p => p.id === 'ct_response');

  const p = metadata?.pole_value ?? 0.5;
  const dtStabilityClass = metadata?.dt_stable ? 'stable' : metadata?.dt_status === 'Marginal' ? 'marginal' : 'unstable';
  const ctStabilityClass = metadata?.ct_stable ? 'stable' : metadata?.ct_status === 'Marginal' ? 'marginal' : 'unstable';

  const handleQuizAnswer = useCallback((answer) => {
    onButtonClick('check_quiz', { answer });
  }, [onButtonClick]);

  const handleNewQuiz = useCallback(() => {
    onButtonClick('new_quiz', {});
  }, [onButtonClick]);

  return (
    <div className="dtct-viewer">
      {/* Status badge (explore mode) */}
      {!isQuizMode && <StatusBadge metadata={metadata} />}

      {/* Side-by-side response plots */}
      <div className="dtct-plots-grid">
        {dtPlot && (
          <ResponsePlot
            plot={dtPlot}
            stabilityClass={dtStabilityClass}
            label="Discrete-Time (Delay + Feedback)"
            theme={theme}
          />
        )}
        {ctPlot && (
          <ResponsePlot
            plot={ctPlot}
            stabilityClass={ctStabilityClass}
            label="Continuous-Time (Integrator + Feedback)"
            theme={theme}
          />
        )}
      </div>

      {/* Side-by-side stability maps */}
      {!isQuizMode && (
        <div className="dtct-stability-maps">
          <UnitCircleMap
            poleValue={p}
            isStable={metadata?.dt_stable ?? false}
            theme={theme}
          />
          <SPlaneMap
            poleValue={p}
            isStable={metadata?.ct_stable ?? false}
            theme={theme}
          />
        </div>
      )}

      {/* Quiz panel */}
      {isQuizMode && (
        <QuizPanel
          quiz={metadata?.quiz}
          onAnswer={handleQuizAnswer}
          onNewQuiz={handleNewQuiz}
          isUpdating={isUpdating}
        />
      )}
    </div>
  );
}

export default DTCTComparatorViewer;
