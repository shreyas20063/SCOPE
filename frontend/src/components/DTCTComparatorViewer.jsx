/**
 * DTCTComparatorViewer
 *
 * Custom viewer for the DT ↔ CT Side-by-Side Comparator simulation.
 * Renders:
 * - Status badge with stability info for both domains
 * - Side-by-side Plotly plots (DT stem + CT continuous)
 * - SVG stability maps (unit circle + s-plane)
 * - Note that the two systems share the number p but are NOT a sampling pair
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
      {/* Backend derives this per domain: decays / marginal / grows */}
      <span className="dtct-status-badge__insight">
        {metadata.insight || ''}
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
// SVG px per unit of p, shared by both maps. Every element (pole marker,
// ticks, ±1 markers and the unit circle itself) uses this one scale, so the
// circle passes through the ±1 ticks and p ∈ [−2, 2] spans CX ± 90 px.
const SCALE = 45;
const toX = (v) => CX + v * SCALE;

// Pole colour by stability status (stable / marginal / unstable)
function poleColorFor(status) {
  if (status === 'Stable') return '#10b981';
  if (status === 'Marginal') return '#f59e0b';
  return '#ef4444';
}

function UnitCircleMap({ poleValue, status, theme }) {
  const isDark = theme === 'dark';
  const axisColor = isDark ? '#475569' : '#94a3b8';
  const textColor = isDark ? '#94a3b8' : '#64748b';

  // Map pole to SVG x coordinate (real axis maps to horizontal)
  const poleX = toX(poleValue);
  const poleColor = poleColorFor(status);
  const isOnBoundary = Math.abs(Math.abs(poleValue) - 1.0) < 0.05;

  return (
    <div className="dtct-stability-map">
      <div className="dtct-stability-map__title">DT: Unit Circle (|p| {'<'} 1)</div>
      <svg viewBox={`0 0 ${MAP_W} ${MAP_H}`} aria-label="DT stability map with unit circle">
        {/* Unstable region fill (outside circle) */}
        <rect x="20" y="20" width={MAP_W - 40} height={MAP_H - 40}
          fill="rgba(239,68,68,0.04)" rx="4" />
        {/* Stable region fill (inside circle, |p| < 1) */}
        <circle cx={CX} cy={CY} r={SCALE}
          fill="rgba(16,185,129,0.12)" stroke="none" />
        {/* Unit circle |p| = 1 */}
        <circle cx={CX} cy={CY} r={SCALE}
          fill="none" stroke={isDark ? '#10b981' : '#059669'}
          strokeWidth="2" strokeDasharray="6,3" opacity="0.8" />

        {/* Axes */}
        <line x1="20" y1={CY} x2={MAP_W - 20} y2={CY}
          stroke={axisColor} strokeWidth="1" />
        <line x1={CX} y1="20" x2={CX} y2={MAP_H - 20}
          stroke={axisColor} strokeWidth="1" />

        {/* Tick marks on real axis */}
        {[-2, -1, 0, 1, 2].map(v => {
          const tx = toX(v);
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

        {/* Axis labels. "Re" sits just past the axis end, on the axis line,
            so the pole label above the axis (up to p = ±2) never collides with it */}
        <text x={MAP_W - 16} y={CY + 3.5} textAnchor="start"
          fontSize="10" fill={textColor} fontFamily="Inter, sans-serif">Re</text>
        <text x={CX + 8} y="18"
          fontSize="10" fill={textColor} fontFamily="Inter, sans-serif">Im</text>

        {/* Boundary markers at ±1 (on the unit circle) */}
        <circle cx={toX(1)} cy={CY} r="3"
          fill="none" stroke={isDark ? '#f59e0b' : '#d97706'} strokeWidth="1.5" />
        <circle cx={toX(-1)} cy={CY} r="3"
          fill="none" stroke={isDark ? '#f59e0b' : '#d97706'} strokeWidth="1.5" />

        {/* Region labels: STABLE inside the circle (below the axis), UNSTABLE
            in the upper-right corner, well outside |p| = 1 */}
        <text x={CX} y={CY + 0.8 * SCALE} textAnchor="middle"
          fontSize="8" fill="#10b981" fontWeight="600" fontFamily="Inter, sans-serif"
          opacity="0.9">STABLE</text>
        <text x={CX + 1.45 * SCALE} y={CY - 1.4 * SCALE} textAnchor="middle"
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

function SPlaneMap({ poleValue, status, theme }) {
  const isDark = theme === 'dark';
  const axisColor = isDark ? '#475569' : '#94a3b8';
  const textColor = isDark ? '#94a3b8' : '#64748b';

  // Map pole to SVG x (left half = stable for CT), same scale as the z-map
  const poleX = toX(poleValue);
  const poleColor = poleColorFor(status);
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
          const tx = toX(v);
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

        {/* Axis labels. "Re" sits just past the axis end, on the axis line,
            so the pole label above the axis (up to p = ±2) never collides with it */}
        <text x={MAP_W - 16} y={CY + 3.5} textAnchor="start"
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

// ── Sampling Note ───────────────────────────────────────────────────────────
// The two systems share the number p but are NOT related by sampling:
// sampling e^{pt} every T seconds gives the DT pole z = e^{pT}, not p.

function SamplingNote({ metadata }) {
  if (!metadata || metadata.sampled_pole == null) return null;

  const T = metadata.sampling_period ?? 1;
  const exponent = String(Number((metadata.pole_value * T).toFixed(4))).replace('-', '−');
  const location = metadata.sampled_pole_location; // inside | on | outside

  return (
    <div className="dtct-note" role="note" aria-label="Not a sampling pair">
      <div className="dtct-note__title">Same number, two different systems: not a sampling pair</div>
      <p className="dtct-note__text">
        The DT system <span className="dtct-note__math">H(z) = 1/(1 − p z<sup>−1</sup>)</span> and
        the CT system <span className="dtct-note__math">H(s) = 1/(s − p)</span> are unrelated
        systems that happen to share the number p. Using the same p in both only contrasts the
        stability regions: <span className="dtct-note__math">|p| {'<'} 1</span> for DT
        versus <span className="dtct-note__math">Re(p) {'<'} 0</span> for CT.
      </p>
      <p className="dtct-note__text">
        Sampling the CT response every T seconds gives{' '}
        <span className="dtct-note__math">e<sup>p·nT</sup> = (e<sup>pT</sup>)<sup>n</sup></span>,
        so its DT counterpart has the pole <span className="dtct-note__math">z = e<sup>pT</sup></span>,{' '}
        <strong>not</strong> <span className="dtct-note__math">z = p</span>. With T = {T} s the
        current p gives <span className="dtct-note__math">z = e<sup>{exponent}</sup> ≈ {metadata.sampled_pole}</span>,{' '}
        {location} the unit circle: the same verdict as the CT system (CT: {metadata.ct_status}).
        Sampling never changes stability, because{' '}
        <span className="dtct-note__math">Re(p) {'<'} 0 ⇔ |e<sup>pT</sup>| {'<'} 1</span>.
      </p>
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
  // While a quiz question is open, the panel borders carry no stability colour
  // (the backend likewise neutralises trace colours and drops the growth note).
  const hideStabilityCues = isQuizMode && !metadata?.quiz?.answered;
  const stabilityClassFor = (stable, status) => (
    hideStabilityCues ? 'neutral' : stable ? 'stable' : status === 'Marginal' ? 'marginal' : 'unstable'
  );
  const dtStabilityClass = stabilityClassFor(metadata?.dt_stable, metadata?.dt_status);
  const ctStabilityClass = stabilityClassFor(metadata?.ct_stable, metadata?.ct_status);

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
            status={metadata?.dt_status}
            theme={theme}
          />
          <SPlaneMap
            poleValue={p}
            status={metadata?.ct_status}
            theme={theme}
          />
        </div>
      )}

      {/* Not-a-sampling-pair note (hidden in quiz mode: e^{pT} reveals CT stability) */}
      {!isQuizMode && <SamplingNote metadata={metadata} />}

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
