/**
 * SteadyStateErrorViewer
 *
 * Custom viewer for the Steady-State Error Analyzer.
 * Layout: SVG block diagram (with optional H(s) and disturbance), enhanced
 * metrics strip with GM/PM/performance, error table, FVT derivation,
 * disturbance response panel, and 3x2 plot grid.
 *
 * KaTeX rendering follows the same trusted pattern used in RootLocusViewer,
 * ControllerTuningLabViewer, BlockDiagramViewer, etc. KaTeX.renderToString
 * produces sanitized HTML output from LaTeX math expressions.
 */

import React, { useState, useMemo, useEffect, useCallback, memo } from 'react';
import Plot from 'react-plotly.js';
import '../styles/SteadyStateError.css';

// ============================================================================
// KaTeX rendering helper (trusted: KaTeX sanitizes its own output)
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

/** Render a KaTeX HTML string into a span. KaTeX output is self-sanitized. */
function KatexSpan({ html, className, style }) {
  if (!html) return null;
  // eslint-disable-next-line react/no-danger -- KaTeX.renderToString produces sanitized output
  return <span className={className} style={style} dangerouslySetInnerHTML={{ __html: html }} />;
}

/** Render a KaTeX HTML string into a div. KaTeX output is self-sanitized. */
function KatexDiv({ html, className, style }) {
  if (!html) return null;
  // eslint-disable-next-line react/no-danger -- KaTeX.renderToString produces sanitized output
  return <div className={className} style={style} dangerouslySetInnerHTML={{ __html: html }} />;
}

// ============================================================================
// Theme detection
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
// Block Diagram — supports unity/non-unity feedback + disturbance
// ============================================================================

const BlockDiagram = memo(function BlockDiagram({ metadata, isDark }) {
  const [katexReady, setKatexReady] = useState(!!katexModule);
  useEffect(() => { loadKatex(() => setKatexReady(true)); }, []);

  const plantLatex = metadata?.plant_latex || 'G(s)';
  const feedbackLatex = metadata?.feedback_latex;
  const isUnity = metadata?.is_unity_feedback !== false;
  const distMode = metadata?.disturbance_mode || 'none';

  const W = 680, H = isUnity ? 130 : 150;
  const mainY = 40;
  const sumX = 110, sumR = 14;
  const blockX = 260, blockW = 160, blockH = 40;
  const outX = 560;
  const takeoffX = blockX + blockW + 40;
  const feedbackY = isUnity ? 110 : 130;

  // H(s) block on feedback path
  const hBlockX = 180, hBlockW = 100, hBlockH = 30;

  const plantHtml = useMemo(() => katexReady ? renderLatex(plantLatex) : null, [katexReady, plantLatex]);
  const feedbackHtml = useMemo(() => katexReady ? renderLatex(feedbackLatex || 'H(s)') : null, [katexReady, feedbackLatex]);

  return (
    <div className="sse-block-diagram">
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" preserveAspectRatio="xMidYMid meet">
        <defs>
          <marker id="sse-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="var(--accent-color, #00d9ff)" />
          </marker>
        </defs>

        {/* R(s) input */}
        <line x1={20} y1={mainY} x2={sumX - sumR} y2={mainY}
          stroke="var(--accent-color, #00d9ff)" strokeWidth={2} markerEnd="url(#sse-arrow)" />
        <text x={10} y={mainY - 10} className="sse-signal-label">R(s)</text>

        {/* Sum junction */}
        <circle cx={sumX} cy={mainY} r={sumR} fill="none"
          stroke="var(--accent-color, #00d9ff)" strokeWidth={1.5} />
        <text x={sumX} y={mainY + 1} textAnchor="middle" dominantBaseline="middle"
          className="sse-sum-label">{'\u03A3'}</text>
        <text x={sumX - sumR - 4} y={mainY + sumR + 4} className="sse-sign-label">{'\u2212'}</text>

        {/* E(s) to G(s) */}
        <line x1={sumX + sumR} y1={mainY} x2={blockX} y2={mainY}
          stroke="var(--accent-color, #00d9ff)" strokeWidth={2} markerEnd="url(#sse-arrow)" />
        <text x={(sumX + sumR + blockX) / 2} y={mainY - 10} textAnchor="middle"
          className="sse-signal-label" fontSize="10">E(s)</text>

        {/* Input disturbance marker */}
        {distMode === 'input' && (
          <>
            <circle cx={(sumX + sumR + blockX) / 2} cy={mainY} r={10} fill="none"
              stroke="#f59e0b" strokeWidth={1.5} strokeDasharray="3,2" />
            <line x1={(sumX + sumR + blockX) / 2} y1={mainY - 22} x2={(sumX + sumR + blockX) / 2} y2={mainY - 10}
              stroke="#f59e0b" strokeWidth={1.5} markerEnd="url(#sse-arrow)" />
            <text x={(sumX + sumR + blockX) / 2} y={mainY - 26} textAnchor="middle"
              className="sse-signal-label" style={{ fill: '#f59e0b', fontSize: '9px' }}>D(s)</text>
          </>
        )}

        {/* G(s) block */}
        <rect x={blockX} y={mainY - blockH / 2} width={blockW} height={blockH}
          rx={6} className="sse-tf-block" />
        {plantHtml ? (
          <foreignObject x={blockX + 4} y={mainY - blockH / 2 + 2} width={blockW - 8} height={blockH - 4}>
            <KatexDiv html={plantHtml} className="sse-katex-container" />
          </foreignObject>
        ) : (
          <text x={blockX + blockW / 2} y={mainY + 4} textAnchor="middle"
            className="sse-signal-label" fontSize="13">G(s)</text>
        )}

        {/* G(s) to Y(s) */}
        <line x1={blockX + blockW} y1={mainY} x2={outX} y2={mainY}
          stroke="var(--accent-color, #00d9ff)" strokeWidth={2} markerEnd="url(#sse-arrow)" />
        <text x={outX + 8} y={mainY - 10} className="sse-signal-label">Y(s)</text>

        {/* Output disturbance marker */}
        {distMode === 'output' && (
          <>
            <circle cx={(blockX + blockW + outX) / 2} cy={mainY} r={10} fill="none"
              stroke="#f59e0b" strokeWidth={1.5} strokeDasharray="3,2" />
            <line x1={(blockX + blockW + outX) / 2} y1={mainY - 22} x2={(blockX + blockW + outX) / 2} y2={mainY - 10}
              stroke="#f59e0b" strokeWidth={1.5} markerEnd="url(#sse-arrow)" />
            <text x={(blockX + blockW + outX) / 2} y={mainY - 26} textAnchor="middle"
              className="sse-signal-label" style={{ fill: '#f59e0b', fontSize: '9px' }}>D(s)</text>
          </>
        )}

        {/* Takeoff point */}
        <circle cx={takeoffX} cy={mainY} r={4} fill="var(--accent-color, #00d9ff)" />

        {/* Feedback path */}
        <line x1={takeoffX} y1={mainY} x2={takeoffX} y2={feedbackY}
          stroke="var(--accent-color, #00d9ff)" strokeWidth={2} />

        {isUnity ? (
          <>
            <line x1={takeoffX} y1={feedbackY} x2={sumX} y2={feedbackY}
              stroke="var(--accent-color, #00d9ff)" strokeWidth={2} />
            <line x1={sumX} y1={feedbackY} x2={sumX} y2={mainY + sumR}
              stroke="var(--accent-color, #00d9ff)" strokeWidth={2} markerEnd="url(#sse-arrow)" />
            <text x={(takeoffX + sumX) / 2} y={feedbackY - 6} textAnchor="middle"
              className="sse-signal-label" fontSize="10">Unity Feedback</text>
          </>
        ) : (
          <>
            <line x1={takeoffX} y1={feedbackY} x2={hBlockX + hBlockW} y2={feedbackY}
              stroke="var(--accent-color, #00d9ff)" strokeWidth={2} markerEnd="url(#sse-arrow)" />
            <rect x={hBlockX} y={feedbackY - hBlockH / 2} width={hBlockW} height={hBlockH}
              rx={5} className="sse-tf-block sse-feedback-block" />
            {feedbackHtml ? (
              <foreignObject x={hBlockX + 3} y={feedbackY - hBlockH / 2 + 1} width={hBlockW - 6} height={hBlockH - 2}>
                <KatexDiv html={feedbackHtml} className="sse-katex-container" style={{ fontSize: '9px' }} />
              </foreignObject>
            ) : (
              <text x={hBlockX + hBlockW / 2} y={feedbackY + 4} textAnchor="middle"
                className="sse-signal-label" fontSize="11">H(s)</text>
            )}
            <line x1={hBlockX} y1={feedbackY} x2={sumX} y2={feedbackY}
              stroke="var(--accent-color, #00d9ff)" strokeWidth={2} />
            <line x1={sumX} y1={feedbackY} x2={sumX} y2={mainY + sumR}
              stroke="var(--accent-color, #00d9ff)" strokeWidth={2} markerEnd="url(#sse-arrow)" />
          </>
        )}
      </svg>
    </div>
  );
});

// ============================================================================
// Metrics Strip
// ============================================================================

const MetricsStrip = memo(function MetricsStrip({ metadata }) {
  if (!metadata) return null;

  const sysType = metadata.system_type;
  const ecDisplay = metadata.error_constants_display || {};
  const clStable = metadata.cl_stable;
  const gm = metadata.gain_margin;
  const pm = metadata.phase_margin;
  const perf = metadata.performance || {};
  const Ms = metadata.Ms;

  const fmtMargin = (v) => {
    if (v == null) return '\u2014';
    if (v === Infinity || v === 'Infinity') return '\u221e';
    return typeof v === 'number' ? v.toFixed(1) : String(v);
  };

  return (
    <div className="sse-info-strip">
      <div className="sse-type-badge">Type {sysType ?? '?'}</div>

      {['Kp', 'Kv', 'Ka'].map(key => (
        <div key={key} className="sse-info-item">
          <span className="sse-info-label">{key}</span>
          <span className="sse-info-value">{ecDisplay[key] ?? '\u2014'}</span>
        </div>
      ))}

      <div className={`sse-stability-badge ${clStable ? 'stable' : 'unstable'}`}>
        {clStable ? '\u2713 Stable' : '\u2717 Unstable'}
      </div>

      {pm != null && pm !== Infinity && (
        <div className="sse-info-item">
          <span className="sse-info-label">PM</span>
          <span className="sse-info-value" style={{ color: pm > 30 ? '#10b981' : pm > 0 ? '#f59e0b' : '#ef4444' }}>
            {fmtMargin(pm)}{'\u00b0'}
          </span>
        </div>
      )}

      {gm != null && gm !== Infinity && (
        <div className="sse-info-item">
          <span className="sse-info-label">GM</span>
          <span className="sse-info-value" style={{ color: gm > 6 ? '#10b981' : gm > 0 ? '#f59e0b' : '#ef4444' }}>
            {fmtMargin(gm)} dB
          </span>
        </div>
      )}

      {perf.overshoot != null && (
        <div className="sse-info-item">
          <span className="sse-info-label">OS</span>
          <span className="sse-info-value">{perf.overshoot.toFixed(1)}%</span>
        </div>
      )}

      {perf.rise_time != null && (
        <div className="sse-info-item">
          <span className="sse-info-label">t_r</span>
          <span className="sse-info-value">{perf.rise_time.toFixed(3)}s</span>
        </div>
      )}

      {perf.settling_time != null && (
        <div className="sse-info-item">
          <span className="sse-info-label">t_s</span>
          <span className="sse-info-value">{perf.settling_time.toFixed(3)}s</span>
        </div>
      )}

      {Ms != null && (
        <div className="sse-info-item">
          <span className="sse-info-label">Ms</span>
          <span className="sse-info-value" style={{ color: Ms > 2 ? '#ef4444' : Ms > 1.5 ? '#f59e0b' : '#10b981' }}>
            {Ms.toFixed(2)}
          </span>
        </div>
      )}
    </div>
  );
});

// ============================================================================
// Error Table
// ============================================================================

const ERROR_ROWS = [
  { input: 'step',      label: 'Step',      formula: '\\frac{A}{1 + K_p}', constantKey: 'Kp' },
  { input: 'ramp',      label: 'Ramp',      formula: '\\frac{A}{K_v}',     constantKey: 'Kv' },
  { input: 'parabolic', label: 'Parabolic', formula: '\\frac{A}{K_a}',     constantKey: 'Ka' },
];

const ErrorTable = memo(function ErrorTable({ metadata, onSelectInput }) {
  const [katexReady, setKatexReady] = useState(!!katexModule);
  useEffect(() => { loadKatex(() => setKatexReady(true)); }, []);

  if (!metadata) return null;

  const ecDisplay = metadata.error_constants_display || {};
  const seDisplay = metadata.steady_state_errors_display || {};
  const se = metadata.steady_state_errors || {};
  const clStable = metadata.cl_stable;
  const inputType = metadata.input_type || 'step';

  const getRowClass = (input) => {
    if (!clStable) return 'unstable-row';
    const raw = se[input];
    if (raw === null) return 'infinite-error';
    if (raw === 0) return 'zero-error';
    return 'finite-error';
  };

  // Pre-render formula HTML
  const formulaHtmls = useMemo(() => {
    if (!katexReady) return {};
    return Object.fromEntries(ERROR_ROWS.map(row => [row.input, renderLatex(row.formula)]));
  }, [katexReady]);

  return (
    <div className="sse-error-table-wrapper">
      <div className="sse-section-header">
        <span className="sse-section-title">Steady-State Error Summary</span>
        {onSelectInput && (
          <span className="sse-section-hint">Click a row to switch input type</span>
        )}
      </div>
      <table className="sse-error-table">
        <thead>
          <tr><th>Input</th><th>Formula</th><th>Error Constant</th><th>e_ss</th></tr>
        </thead>
        <tbody>
          {ERROR_ROWS.map(row => {
            const isActive = inputType === row.input || inputType === 'all';
            const rowClass = getRowClass(row.input);
            return (
              <tr key={row.input}
                className={`sse-error-row ${rowClass} ${isActive ? 'active' : ''} ${onSelectInput ? 'clickable' : ''}`}
                onClick={() => onSelectInput && onSelectInput(row.input)}>
                <td className="sse-error-input">{row.label}</td>
                <td className="sse-error-formula">
                  {formulaHtmls[row.input] ? (
                    <KatexSpan html={formulaHtmls[row.input]} />
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
// FVT Display
// ============================================================================

const FVTDisplay = memo(function FVTDisplay({ metadata }) {
  const [isOpen, setIsOpen] = useState(false);
  const [katexReady, setKatexReady] = useState(!!katexModule);
  useEffect(() => { loadKatex(() => setKatexReady(true)); }, []);

  if (!metadata) return null;
  const fvtLatex = metadata.fvt_latex;
  const fvtValid = metadata.fvt_valid;
  const fvtHtml = useMemo(() => katexReady ? renderLatex(fvtLatex, true) : null, [katexReady, fvtLatex]);

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
          {fvtHtml ? (
            <KatexDiv html={fvtHtml} className="sse-fvt-latex" />
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
// Disturbance Response Panel
// ============================================================================

const DisturbancePanel = memo(function DisturbancePanel({ metadata, isDark }) {
  const dist = metadata?.disturbance;
  if (!dist || !dist.y_d) return null;

  const modeLabel = dist.mode === 'input' ? 'Input' : 'Output';

  return (
    <div className="sse-disturbance-panel">
      <div className="sse-section-header">
        <span className="sse-section-title">{modeLabel} Disturbance Response</span>
      </div>
      <div className="sse-disturbance-plot">
        <Plot
          data={[{
            x: dist.t, y: dist.y_d, type: 'scatter', mode: 'lines',
            name: `y_d(t) [D=${dist.d_mag}]`,
            line: { color: '#f59e0b', width: 2 },
          }]}
          layout={{
            paper_bgcolor: isDark ? '#0a0e27' : 'rgba(255,255,255,0.98)',
            plot_bgcolor: isDark ? '#131b2e' : '#f8fafc',
            font: { family: 'Inter, sans-serif', size: 12, color: isDark ? '#f1f5f9' : '#1e293b' },
            margin: { t: 30, r: 25, b: 45, l: 55 },
            xaxis: { title: 'Time (s)',
              gridcolor: isDark ? 'rgba(148,163,184,0.1)' : 'rgba(148,163,184,0.2)',
              zerolinecolor: isDark ? 'rgba(148,163,184,0.3)' : 'rgba(148,163,184,0.4)' },
            yaxis: { title: 'y_d(t)',
              gridcolor: isDark ? 'rgba(148,163,184,0.1)' : 'rgba(148,163,184,0.2)',
              zerolinecolor: isDark ? 'rgba(148,163,184,0.3)' : 'rgba(148,163,184,0.4)' },
            autosize: true,
            legend: { bgcolor: 'rgba(0,0,0,0)' },
          }}
          config={{ responsive: true, displayModeBar: false }}
          useResizeHandler
          style={{ width: '100%', height: '100%' }}
        />
      </div>
    </div>
  );
});

// ============================================================================
// Main Viewer
// ============================================================================

export default function SteadyStateErrorViewer({ metadata, plots, onUpdateParams }) {
  const isDark = useIsDark();

  const findPlot = useCallback((id) => plots?.find(p => p.id === id), [plots]);
  const timeResponsePlot = findPlot('time_response');
  const errorSignalPlot = findPlot('error_signal');
  const bodePlot = findPlot('bode_ol');
  const essVsGainPlot = findPlot('ess_vs_gain');
  const sensitivityPlot = findPlot('sensitivity');
  const poleZeroPlot = findPlot('pole_zero_map');

  const handleSelectInput = useCallback((inputType) => {
    if (onUpdateParams) {
      onUpdateParams({ input_type: inputType });
    }
  }, [onUpdateParams]);

  const themeLayout = useMemo(() => ({
    paper_bgcolor: isDark ? '#0a0e27' : 'rgba(255,255,255,0.98)',
    plot_bgcolor: isDark ? '#131b2e' : '#f8fafc',
    font: { family: 'Inter, sans-serif', size: 12, color: isDark ? '#f1f5f9' : '#1e293b' },
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
    const yaxis2 = plotData.layout?.yaxis2;
    const layout = {
      ...plotData.layout,
      ...themeLayout,
      xaxis: { ...plotData.layout?.xaxis, ...themeLayout.xaxis },
      yaxis: { ...plotData.layout?.yaxis, ...themeLayout.yaxis },
      ...(yaxis2 ? { yaxis2: { ...yaxis2, gridcolor: isDark ? 'rgba(148,163,184,0.05)' : 'rgba(148,163,184,0.1)' } } : {}),
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
          config={{ responsive: true, displayModeBar: true,
            modeBarButtonsToRemove: ['select2d', 'lasso2d'], displaylogo: false }}
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
      {metadata.preset_description && (
        <div className="sse-preset-desc">{metadata.preset_description}</div>
      )}
      <BlockDiagram metadata={metadata} isDark={isDark} />
      <MetricsStrip metadata={metadata} />
      <ErrorTable metadata={metadata} onSelectInput={handleSelectInput} />
      <FVTDisplay metadata={metadata} />
      <DisturbancePanel metadata={metadata} isDark={isDark} />
      <div className="sse-plot-grid">
        {renderPlot(timeResponsePlot)}
        {renderPlot(errorSignalPlot)}
        {renderPlot(bodePlot)}
        {renderPlot(essVsGainPlot)}
        {renderPlot(sensitivityPlot)}
        {renderPlot(poleZeroPlot)}
      </div>
    </div>
  );
}
