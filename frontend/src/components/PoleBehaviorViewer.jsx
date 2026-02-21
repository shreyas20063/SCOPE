/**
 * PoleBehaviorViewer
 *
 * Custom viewer for the Pole Behavior Explorer simulation.
 * Renders an interactive SVG number line with a draggable pole,
 * color-coded stability regions, and a Plotly stem plot of y[n] = p₀ⁿ u[n].
 * Supports quiz mode where users click the number line to guess the pole.
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import Plot from 'react-plotly.js';

// ── Theme hook (shared pattern) ───────────────────────────────────────────────

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

// ── SVG Number Line Constants ─────────────────────────────────────────────────

const SVG_W = 640;
const SVG_H = 120;
const PAD = 50;
const LINE_Y = 70;
const REGION_TOP = 38;
const REGION_H = 36;

const poleToX = (p) => PAD + ((p + 2) / 4) * (SVG_W - 2 * PAD);
const xToPole = (x) => ((x - PAD) / (SVG_W - 2 * PAD)) * 4 - 2;
const clampPole = (p) => Math.max(-2, Math.min(2, Math.round(p * 100) / 100));

// ── PoleInfoBadge ─────────────────────────────────────────────────────────────

function PoleInfoBadge({ metadata }) {
  if (!metadata) return null;

  const colorMap = {
    convergent: '#10b981',
    divergent: '#ef4444',
    marginally_stable: '#f59e0b',
  };
  const color = colorMap[metadata.behavior] || '#6b7280';

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 12, padding: '10px 16px',
      background: 'var(--surface-color)', border: '1px solid var(--border-color)',
      borderRadius: 'var(--radius-md)', flexWrap: 'wrap',
    }}>
      <span style={{
        color: 'var(--accent-color)', fontFamily: "'Fira Code', monospace",
        fontSize: '1.05rem', fontWeight: 500,
      }}>
        p<sub>0</sub> = {metadata.pole_position}
      </span>
      <span style={{
        padding: '2px 10px', borderRadius: 'var(--radius-full)',
        color: 'white', fontSize: '0.8rem', fontWeight: 600,
        textTransform: 'uppercase', letterSpacing: '0.03em',
        backgroundColor: color,
      }}>
        {metadata.stability}
      </span>
      <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
        |p<sub>0</sub>| = {metadata.abs_pole}
      </span>
      {metadata.is_alternating && (
        <span style={{
          padding: '2px 8px', border: '1px solid var(--warning-color)',
          borderRadius: 'var(--radius-sm)', color: 'var(--warning-color)',
          fontSize: '0.75rem',
        }}>
          Alternating Sign
        </span>
      )}
    </div>
  );
}

// ── NumberLine (SVG) ──────────────────────────────────────────────────────────

function NumberLine({ polePosition, onPoleChange, isQuizMode, quizState, onQuizGuess, theme }) {
  const svgRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const isDark = theme === 'dark';

  const getPointerPole = useCallback((e) => {
    const svg = svgRef.current;
    if (!svg) return 0;
    const rect = svg.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const svgX = ((clientX - rect.left) / rect.width) * SVG_W;
    return clampPole(xToPole(svgX));
  }, []);

  const handlePointerDown = useCallback((e) => {
    if (isQuizMode) return;
    e.preventDefault();
    setIsDragging(true);
  }, [isQuizMode]);

  const handlePointerMove = useCallback((e) => {
    if (!isDragging) return;
    e.preventDefault();
    onPoleChange(getPointerPole(e));
  }, [isDragging, onPoleChange, getPointerPole]);

  const handlePointerUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Click handler for quiz mode
  const handleSvgClick = useCallback((e) => {
    if (!isQuizMode || quizState?.answered) return;
    const pole = getPointerPole(e);
    onQuizGuess(pole);
  }, [isQuizMode, quizState?.answered, getPointerPole, onQuizGuess]);

  // Attach window-level listeners for drag
  useEffect(() => {
    if (!isDragging) return;
    const onMove = (e) => handlePointerMove(e);
    const onUp = () => handlePointerUp();
    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
    return () => {
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
    };
  }, [isDragging, handlePointerMove, handlePointerUp]);

  const ticks = [-2, -1.5, -1, -0.5, 0, 0.5, 1, 1.5, 2];
  const majorTicks = [-2, -1, 0, 1, 2];
  const textColor = isDark ? '#94a3b8' : '#64748b';
  const lineColor = isDark ? '#475569' : '#94a3b8';

  const px = poleToX(polePosition);

  // Quiz: show actual pole after answer
  const showQuizActual = isQuizMode && quizState?.answered && quizState.actual_pole != null;
  const showQuizGuess = isQuizMode && quizState?.answered && quizState.user_answer != null;

  return (
    <div style={{
      background: 'var(--surface-color)', border: '1px solid var(--border-color)',
      borderRadius: 'var(--radius-lg)', padding: '12px 8px', overflow: 'visible',
    }}>
      <svg
        ref={svgRef}
        viewBox={`0 0 ${SVG_W} ${SVG_H}`}
        style={{
          width: '100%', height: 'auto', userSelect: 'none', touchAction: 'none',
          cursor: isQuizMode && !quizState?.answered ? 'crosshair' : 'default',
        }}
        onClick={handleSvgClick}
      >
        <defs>
          {/* Hatching patterns for negative (alternating-sign) regions */}
          <pattern id="hatch-green" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">
            <line x1="0" y1="0" x2="0" y2="6" stroke="rgba(16,185,129,0.35)" strokeWidth="1.5" />
          </pattern>
          <pattern id="hatch-red" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">
            <line x1="0" y1="0" x2="0" y2="6" stroke="rgba(239,68,68,0.35)" strokeWidth="1.5" />
          </pattern>
        </defs>

        {/* Color-coded regions */}
        {/* (-2, -1): divergent + alternating → red hatched */}
        <rect x={poleToX(-2)} y={REGION_TOP} width={poleToX(-1) - poleToX(-2)} height={REGION_H}
          fill="rgba(239,68,68,0.12)" rx="4" />
        <rect x={poleToX(-2)} y={REGION_TOP} width={poleToX(-1) - poleToX(-2)} height={REGION_H}
          fill="url(#hatch-red)" rx="4" />

        {/* (-1, 0): convergent + alternating → green hatched */}
        <rect x={poleToX(-1)} y={REGION_TOP} width={poleToX(0) - poleToX(-1)} height={REGION_H}
          fill="rgba(16,185,129,0.12)" rx="4" />
        <rect x={poleToX(-1)} y={REGION_TOP} width={poleToX(0) - poleToX(-1)} height={REGION_H}
          fill="url(#hatch-green)" rx="4" />

        {/* (0, 1): convergent → green solid */}
        <rect x={poleToX(0)} y={REGION_TOP} width={poleToX(1) - poleToX(0)} height={REGION_H}
          fill="rgba(16,185,129,0.15)" rx="4" />

        {/* (1, 2): divergent → red solid */}
        <rect x={poleToX(1)} y={REGION_TOP} width={poleToX(2) - poleToX(1)} height={REGION_H}
          fill="rgba(239,68,68,0.15)" rx="4" />

        {/* Region labels */}
        <text x={(poleToX(-2) + poleToX(-1)) / 2} y={REGION_TOP - 6} textAnchor="middle"
          fontSize="9" fill="#ef4444" fontWeight="600" fontFamily="Inter, sans-serif">DIVERGENT</text>
        <text x={(poleToX(-1) + poleToX(0)) / 2} y={REGION_TOP - 6} textAnchor="middle"
          fontSize="9" fill="#10b981" fontWeight="600" fontFamily="Inter, sans-serif">CONVERGENT</text>
        <text x={(poleToX(0) + poleToX(1)) / 2} y={REGION_TOP - 6} textAnchor="middle"
          fontSize="9" fill="#10b981" fontWeight="600" fontFamily="Inter, sans-serif">CONVERGENT</text>
        <text x={(poleToX(1) + poleToX(2)) / 2} y={REGION_TOP - 6} textAnchor="middle"
          fontSize="9" fill="#ef4444" fontWeight="600" fontFamily="Inter, sans-serif">DIVERGENT</text>

        {/* Main axis line */}
        <line x1={PAD} y1={LINE_Y} x2={SVG_W - PAD} y2={LINE_Y}
          stroke={lineColor} strokeWidth="2" />

        {/* Tick marks and labels */}
        {ticks.map(t => {
          const tx = poleToX(t);
          const isMajor = majorTicks.includes(t);
          return (
            <g key={t}>
              <line x1={tx} y1={LINE_Y - (isMajor ? 8 : 5)} x2={tx} y2={LINE_Y + (isMajor ? 8 : 5)}
                stroke={lineColor} strokeWidth={isMajor ? 1.5 : 1} />
              {isMajor && (
                <text x={tx} y={LINE_Y + 22} textAnchor="middle"
                  fontSize="12" fill={textColor} fontFamily="'Fira Code', monospace" fontWeight="500">
                  {t}
                </text>
              )}
            </g>
          );
        })}

        {/* Boundary markers at |p₀| = 1 */}
        <line x1={poleToX(-1)} y1={REGION_TOP} x2={poleToX(-1)} y2={LINE_Y + 10}
          stroke={isDark ? '#f59e0b' : '#d97706'} strokeWidth="1.5" strokeDasharray="4,3" />
        <line x1={poleToX(1)} y1={REGION_TOP} x2={poleToX(1)} y2={LINE_Y + 10}
          stroke={isDark ? '#f59e0b' : '#d97706'} strokeWidth="1.5" strokeDasharray="4,3" />

        {/* Alternating-sign annotation */}
        <text x={(poleToX(-2) + poleToX(0)) / 2} y={LINE_Y + 36} textAnchor="middle"
          fontSize="9" fill={textColor} fontFamily="Inter, sans-serif" fontStyle="italic">
          alternating sign (p₀ &lt; 0)
        </text>
        <text x={(poleToX(0) + poleToX(2)) / 2} y={LINE_Y + 36} textAnchor="middle"
          fontSize="9" fill={textColor} fontFamily="Inter, sans-serif" fontStyle="italic">
          same sign (p₀ &gt; 0)
        </text>

        {/* Quiz: show actual pole marker after answering */}
        {showQuizActual && (
          <>
            <line x1={poleToX(quizState.actual_pole)} y1={LINE_Y - 18}
              x2={poleToX(quizState.actual_pole)} y2={LINE_Y + 10}
              stroke="#10b981" strokeWidth="2" />
            <circle cx={poleToX(quizState.actual_pole)} cy={LINE_Y}
              r="8" fill="#10b981" stroke="#065f46" strokeWidth="2" />
            <text x={poleToX(quizState.actual_pole)} y={LINE_Y - 22} textAnchor="middle"
              fontSize="10" fill="#10b981" fontWeight="600" fontFamily="'Fira Code', monospace">
              actual
            </text>
          </>
        )}

        {/* Quiz: show user guess marker after answering */}
        {showQuizGuess && (
          <>
            <circle cx={poleToX(quizState.user_answer)} cy={LINE_Y}
              r="6" fill="none" stroke={quizState.correct ? '#10b981' : '#ef4444'} strokeWidth="2"
              strokeDasharray="3,2" />
            <text x={poleToX(quizState.user_answer)} y={LINE_Y - 14} textAnchor="middle"
              fontSize="9" fill={quizState.correct ? '#10b981' : '#ef4444'} fontFamily="'Fira Code', monospace">
              guess
            </text>
          </>
        )}

        {/* Draggable pole circle (explore mode only) */}
        {!isQuizMode && (
          <g
            onPointerDown={handlePointerDown}
            style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
          >
            {/* Glow */}
            <circle cx={px} cy={LINE_Y} r="14"
              fill="rgba(0,217,255,0.15)" stroke="none" />
            {/* Main circle */}
            <circle cx={px} cy={LINE_Y} r="9"
              fill="#00d9ff" stroke="#0d9488" strokeWidth="2.5"
              style={{ filter: 'drop-shadow(0 0 6px rgba(0,217,255,0.5))' }} />
            {/* Label above */}
            <text x={px} y={LINE_Y - 18} textAnchor="middle"
              fontSize="11" fill="var(--accent-color)" fontWeight="600"
              fontFamily="'Fira Code', monospace">
              p₀ = {polePosition}
            </text>
          </g>
        )}

        {/* Quiz crosshair hint */}
        {isQuizMode && !quizState?.answered && (
          <text x={SVG_W / 2} y={LINE_Y - 22} textAnchor="middle"
            fontSize="11" fill="#f59e0b" fontWeight="500" fontFamily="Inter, sans-serif">
            Click the number line to guess the pole location
          </text>
        )}
      </svg>
    </div>
  );
}

// ── StemPlot (Plotly) ─────────────────────────────────────────────────────────

function StemPlot({ plot, theme }) {
  const isDark = theme === 'dark';

  const layout = {
    title: {
      text: plot.title || 'Stem Plot',
      font: { color: isDark ? '#f1f5f9' : '#1e293b', size: 15 },
      x: 0.5,
      xanchor: 'center',
    },
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
      zerolinewidth: 2,
      color: isDark ? '#94a3b8' : '#64748b',
      autorange: true,
    },
    legend: {
      font: { color: isDark ? '#94a3b8' : '#64748b', size: 11 },
      bgcolor: 'rgba(0,0,0,0)',
    },
    margin: { t: 45, r: 25, b: 55, l: 60 },
    datarevision: `${plot.id}-${plot.title}-${Date.now()}`,
    // No uirevision — y-range changes drastically as pole moves, so always auto-scale
  };

  const config = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    displaylogo: false,
  };

  return (
    <div style={{
      background: 'var(--surface-color)', border: '1px solid var(--border-color)',
      borderRadius: 'var(--radius-lg)', padding: 8, minHeight: 300,
    }}>
      <Plot
        data={plot.data || []}
        layout={layout}
        config={config}
        useResizeHandler={true}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
}

// ── QuizPanel ─────────────────────────────────────────────────────────────────

function QuizPanel({ quiz, onNewQuiz, isUpdating }) {
  if (!quiz) return null;

  return (
    <div style={{
      padding: 16, background: 'var(--surface-color)',
      border: '1px solid var(--border-color)', borderRadius: 'var(--radius-lg)',
      display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap',
    }}>
      {quiz.answered ? (
        <>
          <span style={{
            fontSize: '0.95rem', fontWeight: 600,
            color: quiz.correct ? '#10b981' : '#ef4444',
          }}>
            {quiz.correct
              ? 'Correct!'
              : `Incorrect. You guessed ${quiz.user_answer?.toFixed(2)}, actual was ${quiz.actual_pole?.toFixed(2)}`
            }
          </span>
          <button
            onClick={onNewQuiz}
            disabled={isUpdating}
            style={{
              padding: '8px 20px', background: 'var(--primary-color)', color: 'white',
              border: 'none', borderRadius: 'var(--radius-md)', cursor: 'pointer',
              fontSize: '0.9rem', transition: 'background var(--transition-fast)',
              opacity: isUpdating ? 0.6 : 1,
            }}
          >
            Next Question
          </button>
        </>
      ) : (
        <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          Look at the stem plot and click the number line where you think p₀ is located.
        </span>
      )}
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

function PoleBehaviorViewer({ metadata, plots, currentParams, onParamChange, onButtonClick, isUpdating }) {
  const theme = useTheme();
  const isQuizMode = metadata?.mode === 'quiz';
  const stemPlot = plots?.find(p => p.id === 'stem_plot');

  const handlePoleChange = useCallback((val) => {
    onParamChange('pole_position', val);
  }, [onParamChange]);

  const handleQuizGuess = useCallback((val) => {
    onButtonClick('check_answer', { answer: val });
  }, [onButtonClick]);

  const handleNewQuiz = useCallback(() => {
    onButtonClick('new_quiz', {});
  }, [onButtonClick]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, width: '100%' }}>
      {/* Info badge (explore mode only) */}
      {!isQuizMode && <PoleInfoBadge metadata={metadata} />}

      {/* Interactive number line */}
      <NumberLine
        polePosition={currentParams?.pole_position ?? 0.5}
        onPoleChange={handlePoleChange}
        isQuizMode={isQuizMode}
        quizState={metadata?.quiz}
        onQuizGuess={handleQuizGuess}
        theme={theme}
      />

      {/* Stem plot */}
      {stemPlot && <StemPlot plot={stemPlot} theme={theme} />}

      {/* Quiz panel */}
      {isQuizMode && (
        <QuizPanel
          quiz={metadata?.quiz}
          onNewQuiz={handleNewQuiz}
          isUpdating={isUpdating}
        />
      )}
    </div>
  );
}

export default PoleBehaviorViewer;
