/**
 * PolynomialMultiplicationViewer Component
 *
 * Custom viewer for the Polynomial Multiplication simulation.
 * Two view modes:
 *   - Tabular: animated multiplication table with anti-diagonal highlighting
 *   - Graphical: cascade block diagram with stem plots
 *
 * Animation is handled entirely on the frontend (no backend round-trips).
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import Plot from 'react-plotly.js';
import './PolynomialMultiplicationViewer.css';

/* ── Theme hook ────────────────────────────────────────────── */

function useTheme() {
  const [theme, setTheme] = useState(() =>
    document.documentElement.getAttribute('data-theme') || 'dark'
  );

  useEffect(() => {
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

/* ── Anti-diagonal color palette ──────────────────────────── */

const DIAG_COLORS = [
  '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
  '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#06b6d4',
  '#84cc16', '#e11d48', '#a855f7', '#22d3ee', '#facc15',
  '#fb923c', '#4ade80', '#c084fc', '#f472b6',
];

function getDiagColor(diagIdx) {
  return DIAG_COLORS[diagIdx % DIAG_COLORS.length];
}

/* ── Format number for table cells ────────────────────────── */

function fmt(val) {
  if (val == null || isNaN(val)) return '—';
  if (Math.abs(val) < 0.0005) return '0';
  if (Math.abs(val - 1) < 0.0005) return '1';
  if (Math.abs(val + 1) < 0.0005) return '-1';
  if (Math.abs(val) >= 100) return val.toFixed(1);
  if (Math.abs(val) >= 10) return val.toFixed(2);
  return val.toFixed(3);
}

/* ── Animation Controls ───────────────────────────────────── */

function AnimationControls({ step, maxStep, playing, onPlay, onPause, onStepFwd, onStepBack, onReset }) {
  return (
    <div className="poly-animation-controls">
      <button className="poly-anim-btn" onClick={onReset} title="Reset Animation">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M2 2v5h5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M3.05 10A6 6 0 1 0 4.2 4.2L2 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </button>
      <button className="poly-anim-btn" onClick={onStepBack} disabled={step <= 0} title="Step Back">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M10 12L5 8l5-4v8z" fill="currentColor"/>
        </svg>
      </button>
      {playing ? (
        <button className="poly-anim-btn poly-anim-btn--primary" onClick={onPause} title="Pause">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="4" y="3" width="3" height="10" rx="0.5" fill="currentColor"/>
            <rect x="9" y="3" width="3" height="10" rx="0.5" fill="currentColor"/>
          </svg>
        </button>
      ) : (
        <button className="poly-anim-btn poly-anim-btn--primary" onClick={onPlay} disabled={step >= maxStep} title="Play">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M4 3l9 5-9 5V3z" fill="currentColor"/>
          </svg>
        </button>
      )}
      <button className="poly-anim-btn" onClick={onStepFwd} disabled={step >= maxStep} title="Step Forward">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M6 4l5 4-5 4V4z" fill="currentColor"/>
        </svg>
      </button>
      <span className="poly-anim-counter">
        Diagonal {step} / {maxStep}
      </span>
    </div>
  );
}

/* ── Multiplication Table ─────────────────────────────────── */

function MultiplicationTable({ metadata, animStep, isDark }) {
  const {
    table_data,
    row_labels,
    col_labels,
    row_values,
    col_values,
  } = metadata;

  if (!table_data || !row_labels || !col_labels) return null;

  return (
    <div className="poly-table-wrapper">
      <table className="poly-mul-table">
        <thead>
          <tr>
            <th className="poly-table-corner">
              <span className="poly-corner-symbol">×</span>
            </th>
            {col_labels.map((label, j) => (
              <th key={j} className="poly-col-header">
                <span className="poly-label-symbol">{label}</span>
                <span className="poly-label-value">{fmt(col_values[j])}</span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {row_labels.map((rLabel, i) => (
            <tr key={i}>
              <td className="poly-row-header">
                <span className="poly-label-symbol">{rLabel}</span>
                <span className="poly-label-value">{fmt(row_values[i])}</span>
              </td>
              {table_data[i].map((val, j) => {
                const diag = i + j;
                const isRevealed = diag < animStep;
                const isCurrent = diag === animStep - 1;
                const cellColor = getDiagColor(diag);

                return (
                  <td
                    key={j}
                    className={`poly-cell${isRevealed ? ' poly-cell--revealed' : ''}${isCurrent ? ' poly-cell--current' : ''}`}
                    style={{
                      '--diag-color': cellColor,
                      '--diag-bg': isRevealed
                        ? (isDark ? `${cellColor}22` : `${cellColor}18`)
                        : 'transparent',
                    }}
                  >
                    {isRevealed ? (
                      <span className="poly-cell-value">{fmt(val)}</span>
                    ) : (
                      <span className="poly-cell-placeholder">·</span>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ── Anti-diagonal Legend ──────────────────────────────────── */

function DiagonalLegend({ metadata, animStep }) {
  const sums = metadata?.anti_diagonal_sums;
  if (!sums) return null;

  const revealed = sums.slice(0, animStep);
  if (revealed.length === 0) return null;

  return (
    <div className="poly-diag-legend">
      <span className="poly-diag-legend-title">Coefficients cₙ:</span>
      <div className="poly-diag-chips">
        {revealed.map((val, n) => (
          <span
            key={n}
            className={`poly-diag-chip${n === animStep - 1 ? ' poly-diag-chip--active' : ''}`}
            style={{ '--chip-color': getDiagColor(n) }}
          >
            c<sub>{n}</sub> = {fmt(val)}
          </span>
        ))}
      </div>
    </div>
  );
}

/* ── Cascade Block Diagram (SVG) ──────────────────────────── */

function CascadeBlockDiagram({ a, b, isDark }) {
  const textColor = isDark ? '#f1f5f9' : '#1e293b';
  const boxFill = isDark ? '#1e293b' : '#f1f5f9';
  const arrowColor = isDark ? '#94a3b8' : '#475569';

  const fmtPole = (p) => {
    if (p < 0) return `(${p})`;
    return `${p}`;
  };

  return (
    <div className="poly-block-diagram">
      <svg viewBox="0 0 700 100" className="poly-block-svg">
        <text x="30" y="55" fill={textColor} fontSize="14" fontFamily="Inter, sans-serif" textAnchor="middle">
          δ[n]
        </text>

        <line x1="55" y1="50" x2="140" y2="50" stroke={arrowColor} strokeWidth="2" markerEnd="url(#poly-arrow)"/>

        <rect x="140" y="25" width="140" height="50" rx="8" fill={boxFill} stroke="#3b82f6" strokeWidth="2"/>
        <text x="210" y="45" fill="#3b82f6" fontSize="13" fontFamily="'Fira Code', monospace" textAnchor="middle" fontWeight="600">
          H₁(R)
        </text>
        <text x="210" y="62" fill={textColor} fontSize="11" fontFamily="'Fira Code', monospace" textAnchor="middle" opacity="0.8">
          {`1/(1−${fmtPole(a)}R)`}
        </text>

        <line x1="280" y1="50" x2="360" y2="50" stroke={arrowColor} strokeWidth="2" markerEnd="url(#poly-arrow)"/>

        <rect x="360" y="25" width="140" height="50" rx="8" fill={boxFill} stroke="#ef4444" strokeWidth="2"/>
        <text x="430" y="45" fill="#ef4444" fontSize="13" fontFamily="'Fira Code', monospace" textAnchor="middle" fontWeight="600">
          H₂(R)
        </text>
        <text x="430" y="62" fill={textColor} fontSize="11" fontFamily="'Fira Code', monospace" textAnchor="middle" opacity="0.8">
          {`1/(1−${fmtPole(b)}R)`}
        </text>

        <line x1="500" y1="50" x2="580" y2="50" stroke={arrowColor} strokeWidth="2" markerEnd="url(#poly-arrow)"/>

        <text x="620" y="55" fill={textColor} fontSize="14" fontFamily="Inter, sans-serif" textAnchor="middle">
          y[n]
        </text>

        <defs>
          <marker id="poly-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill={arrowColor}/>
          </marker>
        </defs>
      </svg>
    </div>
  );
}

/* ── Stem plot using Plotly ────────────────────────────────── */

function StemPlot({ plot, theme, height = 240 }) {
  const isDark = theme === 'dark';

  // Spread backend layout but override with theme-aware colors
  const backendXAxis = plot.layout?.xaxis || {};
  const backendYAxis = plot.layout?.yaxis || {};

  const layout = {
    title: {
      text: plot.title || 'Plot',
      font: { color: isDark ? '#f1f5f9' : '#1e293b', size: 14 },
      x: 0.5,
      xanchor: 'center',
    },
    paper_bgcolor: isDark ? '#0f172a' : 'rgba(255, 255, 255, 0.98)',
    plot_bgcolor: isDark ? '#1e293b' : '#f8fafc',
    font: {
      color: isDark ? '#e2e8f0' : '#1e293b',
      family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      size: 11,
    },
    xaxis: {
      ...backendXAxis,
      gridcolor: isDark ? 'rgba(71, 85, 105, 0.4)' : 'rgba(100, 116, 139, 0.2)',
      zerolinecolor: isDark ? 'rgba(148, 163, 184, 0.5)' : 'rgba(100, 116, 139, 0.5)',
      tickfont: { color: isDark ? '#94a3b8' : '#475569', size: 10 },
      title: {
        text: backendXAxis.title?.text || backendXAxis.title || '',
        font: { color: isDark ? '#94a3b8' : '#334155', size: 11 },
      },
      showline: true,
      linecolor: isDark ? '#475569' : '#cbd5e1',
    },
    yaxis: {
      ...backendYAxis,
      gridcolor: isDark ? 'rgba(71, 85, 105, 0.4)' : 'rgba(100, 116, 139, 0.2)',
      zerolinecolor: isDark ? 'rgba(148, 163, 184, 0.5)' : 'rgba(100, 116, 139, 0.5)',
      tickfont: { color: isDark ? '#94a3b8' : '#475569', size: 10 },
      title: {
        text: backendYAxis.title?.text || backendYAxis.title || '',
        font: { color: isDark ? '#94a3b8' : '#334155', size: 11 },
      },
      showline: true,
      linecolor: isDark ? '#475569' : '#cbd5e1',
    },
    legend: {
      font: { color: isDark ? '#e2e8f0' : '#1e293b', size: 10 },
      bgcolor: isDark ? 'rgba(30, 41, 59, 0.9)' : 'rgba(255, 255, 255, 0.9)',
      bordercolor: isDark ? '#334155' : '#e2e8f0',
      borderwidth: 1,
    },
    margin: { t: 40, r: 20, b: 45, l: 50 },
    height,
    autosize: true,
    showlegend: true,
    datarevision: `${plot.id}-${plot.title}-${Date.now()}`,
    uirevision: plot.id,
  };

  return (
    <div className="poly-stem-card">
      <Plot
        data={plot.data || []}
        layout={layout}
        config={{ responsive: true, displayModeBar: false, displaylogo: false }}
        useResizeHandler={true}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
}

/* ── Partial Combined Stem Plot (animated, tabular view) ──── */

function AnimatedCombinedPlot({ metadata, animStep, theme }) {
  const isDark = theme === 'dark';
  const sums = metadata?.anti_diagonal_sums;
  if (!sums) return null;

  const numDiags = metadata.num_anti_diagonals || sums.length;
  const visibleCount = Math.min(animStep, numDiags);

  // Pre-compute stable y-range from ALL sums (prevents jumping)
  const allMin = Math.min(0, ...sums);
  const allMax = Math.max(0, ...sums);
  const span = allMax - allMin;
  const pad = span > 0.001 ? span * 0.2 : 1.0;
  const yRange = [allMin - pad, allMax + pad];

  // Build stem data for revealed diagonals
  const stemX = [];
  const stemY = [];
  const markerX = [];
  const markerY = [];
  const markerColors = [];

  for (let n = 0; n < visibleCount; n++) {
    stemX.push(n, n, null);
    stemY.push(0, sums[n], null);
    markerX.push(n);
    markerY.push(sums[n]);
    markerColors.push(getDiagColor(n));
  }

  // Pending (greyed-out) markers for unrevealed diagonals
  const pendingX = [];
  const pendingY = [];
  for (let n = visibleCount; n < numDiags; n++) {
    pendingX.push(n);
    pendingY.push(0);
  }

  const traces = [];

  if (stemX.length > 0) {
    traces.push({
      x: stemX,
      y: stemY,
      type: 'scatter',
      mode: 'lines',
      name: 'Stems',
      line: { color: '#14b8a6', width: 2.5 },
      showlegend: false,
      hoverinfo: 'skip',
    });
    traces.push({
      x: markerX,
      y: markerY,
      type: 'scatter',
      mode: 'markers',
      name: 'cₙ (anti-diagonal sum)',
      marker: {
        color: markerColors,
        size: 11,
        line: { color: isDark ? '#0a0e27' : '#ffffff', width: 2 },
      },
      hovertemplate: 'n=%{x}<br>cₙ=%{y:.4f}<extra></extra>',
    });
  }

  if (pendingX.length > 0) {
    traces.push({
      x: pendingX,
      y: pendingY,
      type: 'scatter',
      mode: 'markers',
      name: 'Pending',
      marker: { color: 'rgba(148,163,184,0.25)', size: 7 },
      showlegend: false,
      hoverinfo: 'skip',
    });
  }

  const layout = {
    title: {
      text: 'Combined Response cₙ = Σ aᵏbⁿ⁻ᵏ',
      font: { color: isDark ? '#f1f5f9' : '#1e293b', size: 14 },
      x: 0.5,
      xanchor: 'center',
    },
    paper_bgcolor: isDark ? '#0f172a' : 'rgba(255, 255, 255, 0.98)',
    plot_bgcolor: isDark ? '#1e293b' : '#f8fafc',
    font: {
      color: isDark ? '#e2e8f0' : '#1e293b',
      family: 'Inter, sans-serif',
      size: 11,
    },
    xaxis: {
      title: { text: 'n', font: { color: isDark ? '#94a3b8' : '#334155', size: 11 } },
      gridcolor: isDark ? 'rgba(71,85,105,0.4)' : 'rgba(100,116,139,0.2)',
      zerolinecolor: isDark ? 'rgba(148,163,184,0.5)' : 'rgba(100,116,139,0.5)',
      tickfont: { color: isDark ? '#94a3b8' : '#475569', size: 10 },
      dtick: 1,
      range: [-0.5, numDiags - 0.5],
      showline: true,
      linecolor: isDark ? '#475569' : '#cbd5e1',
    },
    yaxis: {
      title: { text: 'cₙ', font: { color: isDark ? '#94a3b8' : '#334155', size: 11 } },
      gridcolor: isDark ? 'rgba(71,85,105,0.4)' : 'rgba(100,116,139,0.2)',
      zerolinecolor: isDark ? 'rgba(148,163,184,0.5)' : 'rgba(100,116,139,0.5)',
      tickfont: { color: isDark ? '#94a3b8' : '#475569', size: 10 },
      showline: true,
      linecolor: isDark ? '#475569' : '#cbd5e1',
      range: yRange,
      autorange: false,
    },
    margin: { t: 40, r: 20, b: 45, l: 50 },
    height: 260,
    autosize: true,
    showlegend: false,
    datarevision: `combined-anim-${animStep}-${Date.now()}`,
    uirevision: 'combined-anim',
  };

  return (
    <div className="poly-stem-card">
      <Plot
        data={traces}
        layout={layout}
        config={{ responsive: true, displayModeBar: false, displaylogo: false }}
        useResizeHandler={true}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
}

/* ── Closed-Form Info Badge ───────────────────────────────── */

function ClosedFormBadge({ metadata }) {
  if (!metadata) return null;
  const { pole_a: a, pole_b: b, closed_form } = metadata;

  return (
    <div className="poly-info-badge">
      <div className="poly-info-row">
        <span className="poly-info-label">Series:</span>
        <span className="poly-info-value poly-info-mono">
          {`(1 + ${a}R + ${a}²R² + …) × (1 + ${b}R + ${b}²R² + …)`}
        </span>
      </div>
      <div className="poly-info-row">
        <span className="poly-info-label">Closed form:</span>
        <span className="poly-info-value poly-info-mono">
          cₙ = {closed_form}
        </span>
      </div>
    </div>
  );
}

/* ── Main Viewer ──────────────────────────────────────────── */

function PolynomialMultiplicationViewer({ metadata, plots, currentParams, onParamChange, onButtonClick }) {
  const theme = useTheme();
  const isDark = theme === 'dark';
  const [animStep, setAnimStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const timerRef = useRef(null);

  const viewMode = metadata?.view_mode || 'tabular';
  const numDiags = metadata?.num_anti_diagonals || 0;

  // Reset animation whenever any data-affecting parameter changes
  // (pole values, num_terms, or view_mode)
  const resetKey = `${metadata?.pole_a}-${metadata?.pole_b}-${metadata?.num_terms}-${metadata?.view_mode}`;
  const prevResetKey = useRef(resetKey);
  useEffect(() => {
    if (prevResetKey.current !== resetKey) {
      setAnimStep(0);
      setPlaying(false);
      prevResetKey.current = resetKey;
    }
  }, [resetKey]);

  // Animation timer
  useEffect(() => {
    if (playing && animStep < numDiags) {
      timerRef.current = setTimeout(() => {
        setAnimStep((s) => s + 1);
      }, 400);
    } else if (playing && animStep >= numDiags) {
      setPlaying(false);
    }
    return () => clearTimeout(timerRef.current);
  }, [playing, animStep, numDiags]);

  const onPlay = useCallback(() => {
    if (animStep >= numDiags) setAnimStep(0);
    setPlaying(true);
  }, [animStep, numDiags]);

  const onPause = useCallback(() => setPlaying(false), []);

  const onStepFwd = useCallback(() => {
    setPlaying(false);
    setAnimStep((s) => Math.min(s + 1, numDiags));
  }, [numDiags]);

  const onStepBack = useCallback(() => {
    setPlaying(false);
    setAnimStep((s) => Math.max(s - 1, 0));
  }, []);

  const onAnimReset = useCallback(() => {
    setPlaying(false);
    setAnimStep(0);
  }, []);

  // Full simulation reset: reset all params to defaults + reset animation
  const onFullReset = useCallback(() => {
    setPlaying(false);
    setAnimStep(0);
    if (onParamChange) {
      // Reset each param to its default
      onParamChange('pole_a', 0.5);
      onParamChange('pole_b', 0.3);
      onParamChange('num_terms', 6);
      onParamChange('view_mode', 'tabular');
    }
  }, [onParamChange]);

  if (!metadata || !plots || plots.length === 0) {
    return (
      <div className="poly-viewer">
        <div className="poly-viewer-empty">
          <p>Loading Polynomial Multiplication simulation...</p>
        </div>
      </div>
    );
  }

  // Find individual plots by ID
  const h1Plot = plots.find((p) => p.id === 'h1_response');
  const h2Plot = plots.find((p) => p.id === 'h2_response');
  const combinedPlot = plots.find((p) => p.id === 'combined_response');

  return (
    <div className="poly-viewer">
      <ClosedFormBadge metadata={metadata} />

      {viewMode === 'tabular' ? (
        /* ── Tabular View ──────────────────────────────────── */
        <>
          <AnimationControls
            step={animStep}
            maxStep={numDiags}
            playing={playing}
            onPlay={onPlay}
            onPause={onPause}
            onStepFwd={onStepFwd}
            onStepBack={onStepBack}
            onReset={onAnimReset}
          />
          <MultiplicationTable
            metadata={metadata}
            animStep={animStep}
            isDark={isDark}
          />
          <DiagonalLegend metadata={metadata} animStep={animStep} />
          <AnimatedCombinedPlot
            metadata={metadata}
            animStep={animStep}
            theme={theme}
          />
        </>
      ) : (
        /* ── Graphical View ────────────────────────────────── */
        <>
          <CascadeBlockDiagram
            a={metadata.pole_a}
            b={metadata.pole_b}
            isDark={isDark}
          />
          <div className="poly-plots-row">
            {h1Plot && <StemPlot plot={h1Plot} theme={theme} height={220} />}
            {h2Plot && <StemPlot plot={h2Plot} theme={theme} height={220} />}
          </div>
          {combinedPlot && <StemPlot plot={combinedPlot} theme={theme} height={260} />}
        </>
      )}
    </div>
  );
}

export default PolynomialMultiplicationViewer;
