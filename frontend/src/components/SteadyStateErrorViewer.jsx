/**
 * SteadyStateErrorViewer
 *
 * Custom viewer for the Steady-State Error Analyzer simulation.
 * Layout: SVG block diagram, system info strip, error table (centerpiece),
 * collapsible FVT derivation, and 2x2 plot grid.
 */

import React, { useState, useMemo, useEffect, useCallback, memo } from 'react';
import Plot from 'react-plotly.js';
import '../styles/SteadyStateError.css';

// ============================================================================
// KaTeX rendering helper (same pattern as LeadLagDesignerViewer)
// ============================================================================

let katexModule = null;
let katexLoading = false;
const katexCallbacks = [];

function loadKatex(cb) {
  if (katexModule) { cb(katexModule); return; }
  katexCallbacks.push(cb);
  if (katexLoading) return;
  katexLoading = true;
  import('katex').then(mod => {
    katexModule = mod.default || mod;
    import('katex/dist/katex.min.css');
    katexCallbacks.forEach(fn => fn(katexModule));
    katexCallbacks.length = 0;
  }).catch(() => { katexLoading = false; });
}

function renderLatex(latex, displayMode = false) {
  if (!katexModule || !latex) return latex || '';
  try {
    return katexModule.renderToString(latex, { throwOnError: false, displayMode });
  } catch {
    return latex;
  }
}

// ============================================================================
// Theme detection hook
// ============================================================================

function useIsDark() {
  const [isDark, setIsDark] = useState(true);
  useEffect(() => {
    const check = () => setIsDark(document.documentElement.getAttribute('data-theme') !== 'light');
    check();
    const observer = new MutationObserver(check);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => observer.disconnect();
  }, []);
  return isDark;
}

// ============================================================================
// Block Diagram — Unity Feedback Loop (SVG)
// ============================================================================

const BlockDiagram = memo(function BlockDiagram({ metadata, isDark }) {
  const [katexReady, setKatexReady] = useState(!!katexModule);

  useEffect(() => {
    loadKatex(() => setKatexReady(true));
  }, []);

  const plantLatex = metadata?.plant_latex || 'G(s)';

  const W = 600, H = 120;
  const mainY = 40;
  const sumX = 100, sumR = 14;
  const blockX = 240, blockW = 160, blockH = 40;
  const outX = 500;
  const takeoffX = blockX + blockW + 30;
  const feedbackY = 100;

  const lineColor = isDark ? '#94a3b8' : '#64748b';
  const arrowId = 'sse-arrow';

  return (
    <div className="sse-block-diagram">
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" preserveAspectRatio="xMidYMid meet">
        <defs>
          <marker id={arrowId} markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="var(--accent-color, #00d9ff)" />
          </marker>
        </defs>

        {/* R(s) input */}
        <line x1={20} y1={mainY} x2={sumX - sumR} y2={mainY}
          stroke="var(--accent-color, #00d9ff)" strokeWidth={2} markerEnd={`url(#${arrowId})`} />
        <text x={10} y={mainY - 10} className="sse-signal-label">R(s)</text>

        {/* Sum junction */}
        <circle cx={sumX} cy={mainY} r={sumR} fill="none"
          stroke="var(--accent-color, #00d9ff)" strokeWidth={1.5} />
        <text x={sumX} y={mainY + 1} textAnchor="middle" dominantBaseline="middle"
          className="sse-sum-label">{'\u03A3'}</text>
        <text x={sumX - sumR - 4} y={mainY + sumR + 4} className="sse-sign-label">{'\u2212'}</text>

        {/* E(s) to G(s) block */}
        <line x1={sumX + sumR} y1={mainY} x2={blockX} y2={mainY}
          stroke="var(--accent-color, #00d9ff)" strokeWidth={2} markerEnd={`url(#${arrowId})`} />
        <text x={(sumX + sumR + blockX) / 2} y={mainY - 10} textAnchor="middle"
          className="sse-signal-label" fontSize="10">E(s)</text>

        {/* G(s) block */}
        <rect x={blockX} y={mainY - blockH / 2} width={blockW} height={blockH}
          rx={6} className="sse-tf-block" />
        {katexReady ? (
          <foreignObject x={blockX + 4} y={mainY - blockH / 2 + 2} width={blockW - 8} height={blockH - 4}>
            <div xmlns="http://www.w3.org/1999/xhtml" className="sse-katex-container"
              dangerouslySetInnerHTML={{ __html: renderLatex(plantLatex) }} />
          </foreignObject>
        ) : (
          <text x={blockX + blockW / 2} y={mainY + 4} textAnchor="middle"
            className="sse-signal-label" fontSize="13">G(s)</text>
        )}

        {/* G(s) to Y(s) output */}
        <line x1={blockX + blockW} y1={mainY} x2={outX} y2={mainY}
          stroke="var(--accent-color, #00d9ff)" strokeWidth={2} markerEnd={`url(#${arrowId})`} />
        <text x={outX + 8} y={mainY - 10} className="sse-signal-label">Y(s)</text>

        {/* Takeoff point */}
        <circle cx={takeoffX} cy={mainY} r={4} fill="var(--accent-color, #00d9ff)" />

        {/* Feedback path */}
        <line x1={takeoffX} y1={mainY} x2={takeoffX} y2={feedbackY}
          stroke="var(--accent-color, #00d9ff)" strokeWidth={2} />
        <line x1={takeoffX} y1={feedbackY} x2={sumX} y2={feedbackY}
          stroke="var(--accent-color, #00d9ff)" strokeWidth={2} />
        <line x1={sumX} y1={feedbackY} x2={sumX} y2={mainY + sumR}
          stroke="var(--accent-color, #00d9ff)" strokeWidth={2} markerEnd={`url(#${arrowId})`} />

        {/* Unity feedback label */}
        <text x={(takeoffX + sumX) / 2} y={feedbackY - 6} textAnchor="middle"
          className="sse-signal-label" fontSize="10">Unity Feedback</text>
      </svg>
    </div>
  );
});

// ============================================================================
// System Info Strip
// ============================================================================

const SystemInfoStrip = memo(function SystemInfoStrip({ metadata }) {
  if (!metadata) return null;

  const systemType = metadata.system_type;
  const ecDisplay = metadata.error_constants_display || {};
  const ec = metadata.error_constants || {};
  const seDisplay = metadata.steady_state_errors_display || {};
  const se = metadata.steady_state_errors || {};
  const clStable = metadata.cl_stable;
  const inputType = metadata.input_type || 'step';

  const getConstantColor = (key) => {
    const raw = ec[key];
    if (raw === null) return '#14b8a6'; // inf -> teal
    if (raw === 0) return '#64748b';    // zero -> muted
    return '#10b981';                    // finite -> green
  };

  const getEssColor = () => {
    const raw = se[inputType];
    if (raw === null) return '#ef4444'; // inf -> red
    if (raw === 0) return '#10b981';    // zero -> green
    return '#f59e0b';                    // finite -> amber
  };

  return (
    <div className="sse-info-strip">
      <div className="sse-type-badge">
        Type {systemType != null ? systemType : '?'}
      </div>

      {['Kp', 'Kv', 'Ka'].map(key => (
        <div key={key} className="sse-info-item">
          <span className="sse-info-label">{key}</span>
          <span className="sse-info-value" style={{ color: getConstantColor(key) }}>
            {ecDisplay[key] ?? '\u2014'}
          </span>
        </div>
      ))}

      <div className={`sse-stability-badge ${clStable ? 'stable' : 'unstable'}`}>
        {clStable ? '\u2713 Stable' : '\u2717 Unstable'}
      </div>

      <div className="sse-info-item sse-info-ess">
        <span className="sse-info-label">e_ss ({inputType})</span>
        <span className="sse-info-value" style={{ color: getEssColor() }}>
          {seDisplay[inputType] ?? '\u2014'}
        </span>
      </div>
    </div>
  );
});

// ============================================================================
// Error Table — THE CENTERPIECE
// ============================================================================

const ERROR_ROWS = [
  { input: 'step',      label: 'Step',      formula: '\\frac{A}{1 + K_p}', constantKey: 'Kp' },
  { input: 'ramp',      label: 'Ramp',      formula: '\\frac{A}{K_v}',     constantKey: 'Kv' },
  { input: 'parabolic', label: 'Parabolic', formula: '\\frac{A}{K_a}',     constantKey: 'Ka' },
];

const ErrorTable = memo(function ErrorTable({ metadata, isDark }) {
  const [katexReady, setKatexReady] = useState(!!katexModule);

  useEffect(() => {
    loadKatex(() => setKatexReady(true));
  }, []);

  if (!metadata) return null;

  const ecDisplay = metadata.error_constants_display || {};
  const seDisplay = metadata.steady_state_errors_display || {};
  const se = metadata.steady_state_errors || {};
  const ec = metadata.error_constants || {};
  const clStable = metadata.cl_stable;
  const inputType = metadata.input_type || 'step';

  const getRowClass = (input) => {
    if (!clStable) return 'unstable-row';
    const raw = se[input];
    if (raw === null) return 'infinite-error';
    if (raw === 0) return 'zero-error';
    return 'finite-error';
  };

  return (
    <div className="sse-error-table-wrapper">
      <div className="sse-section-header">
        <span className="sse-section-title">Steady-State Error Summary</span>
      </div>
      <table className="sse-error-table">
        <thead>
          <tr>
            <th>Input</th>
            <th>Formula</th>
            <th>Error Constant</th>
            <th>e_ss</th>
          </tr>
        </thead>
        <tbody>
          {ERROR_ROWS.map(row => {
            const isActive = inputType === row.input;
            const rowClass = getRowClass(row.input);

            return (
              <tr
                key={row.input}
                className={`sse-error-row ${rowClass} ${isActive ? 'active' : ''}`}
              >
                <td className="sse-error-input">{row.label}</td>
                <td className="sse-error-formula">
                  {katexReady ? (
                    <span dangerouslySetInnerHTML={{ __html: renderLatex(row.formula) }} />
                  ) : (
                    <span className="sse-fallback-formula">{row.formula}</span>
                  )}
                </td>
                <td className="sse-error-constant">
                  {!clStable ? (
                    <span className="sse-na-text">N/A</span>
                  ) : (
                    <span className="sse-constant-value">
                      {row.constantKey} = {ecDisplay[row.constantKey] ?? '\u2014'}
                    </span>
                  )}
                </td>
                <td className="sse-error-ess">
                  {!clStable ? (
                    <span className="sse-na-text">N/A (unstable)</span>
                  ) : (
                    <span className={`sse-ess-value ${se[row.input] === null ? 'infinite' : se[row.input] === 0 ? 'zero' : 'finite'}`}>
                      {seDisplay[row.input] ?? '\u2014'}
                    </span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
});

// ============================================================================
// FVT Display — Collapsible
// ============================================================================

const FVTDisplay = memo(function FVTDisplay({ metadata, isDark }) {
  const [isOpen, setIsOpen] = useState(false);
  const [katexReady, setKatexReady] = useState(!!katexModule);

  useEffect(() => {
    loadKatex(() => setKatexReady(true));
  }, []);

  if (!metadata) return null;

  const fvtLatex = metadata.fvt_latex;
  const fvtValid = metadata.fvt_valid;

  return (
    <div className="sse-fvt-panel">
      <button className="sse-fvt-toggle" onClick={() => setIsOpen(!isOpen)}>
        <span className="sse-fvt-chevron">{isOpen ? '\u25BE' : '\u25B8'}</span>
        <span className="sse-fvt-title">Final Value Theorem Derivation</span>
      </button>
      {isOpen && (
        <div className="sse-fvt-content">
          {!fvtValid && (
            <div className="sse-fvt-warning">
              FVT does not apply — closed-loop system is unstable
            </div>
          )}
          {fvtLatex && katexReady ? (
            <div
              className="sse-fvt-latex"
              dangerouslySetInnerHTML={{ __html: renderLatex(fvtLatex, true) }}
            />
          ) : fvtLatex ? (
            <div className="sse-fvt-fallback">{fvtLatex}</div>
          ) : (
            <div className="sse-fvt-empty">No FVT derivation available</div>
          )}
        </div>
      )}
    </div>
  );
});

// ============================================================================
// Main Viewer
// ============================================================================

export default function SteadyStateErrorViewer({ metadata, plots }) {
  const isDark = useIsDark();

  // Find plots by ID
  const findPlot = useCallback((id) => plots?.find(p => p.id === id), [plots]);
  const timeResponsePlot = findPlot('time_response');
  const errorSignalPlot = findPlot('error_signal');
  const essVsGainPlot = findPlot('ess_vs_gain');
  const poleZeroPlot = findPlot('pole_zero_map');

  // Standard Plotly layout overrides for theme
  const themeLayout = useMemo(() => ({
    paper_bgcolor: isDark ? '#0a0e27' : 'rgba(255,255,255,0.98)',
    plot_bgcolor: isDark ? '#131b2e' : '#f8fafc',
    font: {
      family: 'Inter, sans-serif',
      size: 12,
      color: isDark ? '#f1f5f9' : '#1e293b',
    },
    xaxis: {
      gridcolor: isDark ? 'rgba(148,163,184,0.1)' : 'rgba(148,163,184,0.2)',
      zerolinecolor: isDark ? 'rgba(148,163,184,0.3)' : 'rgba(148,163,184,0.4)',
    },
    yaxis: {
      gridcolor: isDark ? 'rgba(148,163,184,0.1)' : 'rgba(148,163,184,0.2)',
      zerolinecolor: isDark ? 'rgba(148,163,184,0.3)' : 'rgba(148,163,184,0.4)',
    },
  }), [isDark]);

  const renderPlot = useCallback((plotData) => {
    if (!plotData) return null;
    const layout = {
      ...plotData.layout,
      ...themeLayout,
      xaxis: { ...plotData.layout?.xaxis, ...themeLayout.xaxis },
      yaxis: { ...plotData.layout?.yaxis, ...themeLayout.yaxis },
      legend: { ...plotData.layout?.legend, font: { color: isDark ? '#94a3b8' : '#64748b', size: 11 }, bgcolor: 'rgba(0,0,0,0)' },
      autosize: true,
      datarevision: `${plotData.id}-${Date.now()}`,
      uirevision: plotData.id,
    };
    return (
      <div className="sse-plot-card" key={plotData.id}>
        <Plot
          data={plotData.data || []}
          layout={layout}
          config={{
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['select2d', 'lasso2d'],
            displaylogo: false,
          }}
          useResizeHandler
          style={{ width: '100%', height: '100%' }}
        />
      </div>
    );
  }, [themeLayout, isDark]);

  if (!metadata) {
    return (
      <div className="sse-viewer" style={{ padding: '40px', color: 'var(--text-muted)', textAlign: 'center' }}>
        Loading simulation...
      </div>
    );
  }

  return (
    <div className="sse-viewer">
      {/* Preset description */}
      {metadata.preset_description && (
        <div className="sse-preset-desc">{metadata.preset_description}</div>
      )}

      {/* 1. Block Diagram */}
      <BlockDiagram metadata={metadata} isDark={isDark} />

      {/* 2. System Info Strip */}
      <SystemInfoStrip metadata={metadata} />

      {/* 3. Error Table (centerpiece) */}
      <ErrorTable metadata={metadata} isDark={isDark} />

      {/* 4. FVT Derivation (collapsible) */}
      <FVTDisplay metadata={metadata} isDark={isDark} />

      {/* 5. 2x2 Plot Grid */}
      <div className="sse-plot-grid">
        {renderPlot(timeResponsePlot)}
        {renderPlot(errorSignalPlot)}
        {renderPlot(essVsGainPlot)}
        {renderPlot(poleZeroPlot)}
      </div>
    </div>
  );
}
