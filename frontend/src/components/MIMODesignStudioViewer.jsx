/**
 * MIMODesignStudioViewer
 *
 * Custom tabbed viewer for the MIMO Design Studio simulation.
 * 5 tabs: Response, Pole-Zero, Properties, Controller, Diagram.
 * Metrics strip always visible beneath the tab bar.
 */

import React, { useState, useMemo, useEffect, useRef, useCallback, memo } from 'react';
import Plot from 'react-plotly.js';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import '../styles/MIMODesignStudio.css';

// ============================================================================
// Theme detection hook
// ============================================================================

function useTheme() {
  const [isDark, setIsDark] = useState(
    () => document.documentElement.getAttribute('data-theme') !== 'light'
  );
  useEffect(() => {
    const obs = new MutationObserver(() =>
      setIsDark(document.documentElement.getAttribute('data-theme') !== 'light')
    );
    obs.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme'],
    });
    return () => obs.disconnect();
  }, []);
  return isDark;
}

// ============================================================================
// KaTeX helpers
// ============================================================================

function LaTeX({ math, display = false, className = '' }) {
  const ref = useRef(null);
  useEffect(() => {
    if (ref.current && math) {
      try {
        katex.render(String(math), ref.current, {
          throwOnError: false,
          displayMode: display,
          trust: false,
          output: 'html',
        });
      } catch {
        if (ref.current) ref.current.textContent = String(math);
      }
    }
  }, [math, display]);
  return display
    ? <div ref={ref} className={`mimo-katex-display ${className}`} />
    : <span ref={ref} className={`mimo-katex-inline ${className}`} />;
}

/** Format a number for matrix display. */
function fmtVal(v) {
  const n = typeof v === 'number' ? v : parseFloat(v);
  if (!isFinite(n) || Math.abs(n) < 1e-12) return '0';
  return parseFloat(n.toPrecision(4)).toString();
}

/** Render a labelled matrix as KaTeX bmatrix. */
function MatrixKaTeX({ label, matrix, className = '' }) {
  if (!matrix || matrix.length === 0) return null;
  const rows = Array.isArray(matrix[0]) ? matrix : [matrix];
  const latex = `\\mathbf{${label}} = \\begin{bmatrix} ${rows
    .map(r => (Array.isArray(r) ? r : [r]).map(fmtVal).join(' & '))
    .join(' \\\\ ')} \\end{bmatrix}`;
  return <LaTeX math={latex} display={false} className={className} />;
}

/** Render a diagonal matrix given an array of diagonal entries. */
function DiagKaTeX({ label, values }) {
  if (!values || values.length === 0) return null;
  const n = values.length;
  const rows = [];
  for (let i = 0; i < n; i++) {
    const row = [];
    for (let j = 0; j < n; j++) {
      row.push(i === j ? fmtVal(values[i]) : '0');
    }
    rows.push(row.join(' & '));
  }
  const latex = `\\mathbf{${label}} = \\begin{bmatrix} ${rows.join(' \\\\ ')} \\end{bmatrix}`;
  return <LaTeX math={latex} display={false} />;
}

/** Format a complex eigenvalue as a readable string. */
function fmtEig(re, im) {
  if (Math.abs(im) < 1e-10) return `${re.toFixed(4)}`;
  const sign = im > 0 ? '+' : '\u2212';
  return `${re.toFixed(4)} ${sign} ${Math.abs(im).toFixed(4)}j`;
}

// ============================================================================
// Tab definitions
// ============================================================================

const TABS = [
  { id: 'response',   label: 'Response',   icon: '\u23F1' },
  { id: 'pole_zero',  label: 'Pole-Zero',  icon: '\u2716' },
  { id: 'properties', label: 'Properties', icon: '\u2699' },
  { id: 'controller', label: 'Controller', icon: '\uD83C\uDFAF' },
  { id: 'diagram',    label: 'Diagram',    icon: '\uD83D\uDCD0' },
];

// ============================================================================
// Plotly shared config
// ============================================================================

const plotlyConfig = {
  responsive: true,
  displayModeBar: true,
  modeBarButtonsToRemove: ['lasso2d', 'select2d'],
  displaylogo: false,
  toImageButtonOptions: { format: 'png', scale: 2 },
};

// ============================================================================
// PlotWrapper — Plotly wrapper with theme-aware layout overrides
// ============================================================================

const PlotWrapper = memo(function PlotWrapper({ plotData, isDark, height = 400 }) {
  const layout = useMemo(() => {
    if (!plotData?.layout) return {};
    const pLayout = plotData.layout;

    // Deep-merge axis properties for all subplot axes
    const axisOverrides = {};
    const axisColor = isDark ? '#94a3b8' : '#475569';
    const gridColor = isDark ? 'rgba(148,163,184,0.1)' : 'rgba(100,116,139,0.15)';
    const zeroColor = isDark ? 'rgba(148,163,184,0.3)' : 'rgba(100,116,139,0.4)';

    // Handle xaxis, xaxis2, xaxis3... and yaxis, yaxis2, yaxis3...
    for (const key of Object.keys(pLayout)) {
      if (/^[xy]axis\d*$/.test(key)) {
        axisOverrides[key] = {
          ...(pLayout[key] || {}),
          color: axisColor,
          gridcolor: gridColor,
          zerolinecolor: zeroColor,
        };
      }
    }

    return {
      ...pLayout,
      ...axisOverrides,
      paper_bgcolor: isDark ? '#0a0e27' : 'rgba(255,255,255,0.98)',
      plot_bgcolor: isDark ? '#131b2e' : '#f8fafc',
      font: {
        ...(pLayout.font || {}),
        family: 'Inter, sans-serif',
        color: isDark ? '#f1f5f9' : '#1e293b',
      },
      legend: {
        ...(pLayout.legend || {}),
        font: {
          ...(pLayout.legend?.font || {}),
          color: isDark ? '#94a3b8' : '#64748b',
        },
        bgcolor: 'rgba(0,0,0,0)',
      },
      datarevision: `${plotData.id}-${plotData.title}-${Date.now()}`,
      uirevision: pLayout.uirevision ?? plotData.id,
    };
  }, [plotData, isDark]);

  if (!plotData?.data) return null;

  return (
    <div className="mimo-response-grid">
      <Plot
        data={plotData.data}
        layout={layout}
        config={plotlyConfig}
        style={{ width: '100%', height: `${height}px` }}
        useResizeHandler
      />
    </div>
  );
});

// ============================================================================
// MetricsStrip — always visible below tabs
// ============================================================================

const MetricsStrip = memo(function MetricsStrip({ metadata }) {
  if (!metadata) return null;

  const n = metadata.n_states ?? 0;
  const m = metadata.n_inputs ?? 0;
  const p = metadata.n_outputs ?? 0;

  const ctrlRank = metadata.controllability_rank ?? 0;
  const obsRank = metadata.observability_rank ?? 0;
  const isCtrb = metadata.is_controllable;
  const isObs = metadata.is_observable;

  const isStable = metadata.is_stable;
  const isMarginal = metadata.is_marginal;

  const controller = metadata.controller || {};
  const hasController = controller.type && !controller.error;

  // CL stability: check CL eigenvalues all in LHP
  const clStable = useMemo(() => {
    if (!hasController || !controller.cl_eigs_real) return null;
    return controller.cl_eigs_real.every(re => re < -1e-10);
  }, [hasController, controller.cl_eigs_real]);

  const olStabilityLabel = isStable ? 'Stable' : isMarginal ? 'Marginal' : 'Unstable';
  const olStabilityCls = isStable ? 'stable' : isMarginal ? 'marginal' : 'unstable';

  return (
    <div className="mimo-metrics-strip">
      {/* Dimension badge */}
      <div className="mimo-metric">
        <span className="mimo-metric-label">Dim</span>
        <span className="mimo-metric-value">
          <span className="mimo-dimension-badge">{n}x{m}x{p}</span>
        </span>
      </div>

      {/* Controllability */}
      <div className="mimo-metric">
        <span className="mimo-metric-label">Ctrb</span>
        <span className="mimo-metric-value" style={{
          color: isCtrb ? 'var(--success-color)' : 'var(--error-color)',
        }}>
          {ctrlRank}/{n}
        </span>
      </div>

      {/* Observability */}
      <div className="mimo-metric">
        <span className="mimo-metric-label">Obsv</span>
        <span className="mimo-metric-value" style={{
          color: isObs ? 'var(--success-color)' : 'var(--error-color)',
        }}>
          {obsRank}/{n}
        </span>
      </div>

      {/* OL Stability */}
      <div className="mimo-metric">
        <span className="mimo-metric-label">OL</span>
        <span className="mimo-metric-value">
          <span className={`mimo-stability-badge ${olStabilityCls}`}>
            {olStabilityLabel}
          </span>
        </span>
      </div>

      {/* CL Stability (when controller is active) */}
      {hasController && clStable !== null && (
        <div className="mimo-metric">
          <span className="mimo-metric-label">CL</span>
          <span className="mimo-metric-value">
            <span className={`mimo-stability-badge ${clStable ? 'stable' : 'unstable'}`}>
              {clStable ? 'Stable' : 'Unstable'}
            </span>
          </span>
        </div>
      )}

      {/* Controller type badge */}
      {hasController && (
        <div className="mimo-metric">
          <span className="mimo-metric-label">Design</span>
          <span className="mimo-metric-value" style={{ color: 'var(--primary-color)', fontSize: '12px' }}>
            {controller.type === 'pole_placement' ? 'Pole Placement'
              : controller.type === 'lqr' ? 'LQR'
              : controller.type === 'lqg' ? 'LQG'
              : controller.type}
          </span>
        </div>
      )}
    </div>
  );
});

// ============================================================================
// ResponseTab — step + impulse response plots
// ============================================================================

function ResponseTab({ plots, isDark, hasController }) {
  const stepPlot = plots?.find(p => p.id === 'step_response_grid');
  const impulsePlot = plots?.find(p => p.id === 'impulse_response_grid');

  if (!stepPlot && !impulsePlot) {
    return <div className="mimo-tab-empty">No response data available. Adjust parameters or compute a controller.</div>;
  }

  return (
    <div>
      {/* Legend for OL/CL traces */}
      {hasController && (
        <div className="mimo-legend">
          <span className="mimo-legend-item">
            <span className="mimo-legend-swatch" style={{ background: '#3b82f6' }} />
            Open Loop (dashed)
          </span>
          <span className="mimo-legend-item">
            <span className="mimo-legend-swatch" style={{ background: '#ef4444' }} />
            Closed Loop (solid)
          </span>
        </div>
      )}

      {stepPlot && (
        <div style={{ marginBottom: 16 }}>
          <div className="mimo-section-title">Step Response</div>
          <PlotWrapper plotData={stepPlot} isDark={isDark} height={450} />
        </div>
      )}

      {impulsePlot && (
        <div>
          <div className="mimo-section-title">Impulse Response</div>
          <PlotWrapper plotData={impulsePlot} isDark={isDark} height={450} />
        </div>
      )}
    </div>
  );
}

// ============================================================================
// PoleZeroTab — eigenvalue map
// ============================================================================

function PoleZeroTab({ plots, isDark }) {
  const eigPlot = plots?.find(p => p.id === 'eigenvalue_plot');

  if (!eigPlot) {
    return <div className="mimo-tab-empty">No eigenvalue data available.</div>;
  }

  return <PlotWrapper plotData={eigPlot} isDark={isDark} height={500} />;
}

// ============================================================================
// PropertiesTab — matrices, controllability, observability, variable names
// ============================================================================

function PropertiesTab({ metadata }) {
  if (!metadata) return <div className="mimo-tab-empty">No system data available.</div>;

  const matrices = metadata.matrices || {};
  const n = metadata.n_states ?? 0;
  const m = metadata.n_inputs ?? 0;
  const p = metadata.n_outputs ?? 0;
  const ctrlRank = metadata.controllability_rank ?? 0;
  const obsRank = metadata.observability_rank ?? 0;
  const isCtrb = metadata.is_controllable;
  const isObs = metadata.is_observable;
  const stateNames = metadata.state_names || [];
  const inputNames = metadata.input_names || [];
  const outputNames = metadata.output_names || [];

  return (
    <div>
      {/* State-space equations */}
      <div style={{ marginBottom: 16, textAlign: 'center' }}>
        <LaTeX math="\dot{\mathbf{x}} = A\mathbf{x} + B\mathbf{u}" />
        <span style={{ margin: '0 8px', color: 'var(--text-muted)' }}>,</span>
        <LaTeX math="\mathbf{y} = C\mathbf{x} + D\mathbf{u}" />
      </div>

      {/* Matrix cards */}
      <div className="mimo-matrix-panel">
        {matrices.A && (
          <div className="mimo-matrix-card">
            <h4>State Matrix A ({n}x{n})</h4>
            <MatrixKaTeX label="A" matrix={matrices.A} />
          </div>
        )}
        {matrices.B && (
          <div className="mimo-matrix-card">
            <h4>Input Matrix B ({n}x{m})</h4>
            <MatrixKaTeX label="B" matrix={matrices.B} />
          </div>
        )}
        {matrices.C && (
          <div className="mimo-matrix-card">
            <h4>Output Matrix C ({p}x{n})</h4>
            <MatrixKaTeX label="C" matrix={matrices.C} />
          </div>
        )}
        {matrices.D && (
          <div className="mimo-matrix-card">
            <h4>Feedthrough D ({p}x{m})</h4>
            <MatrixKaTeX label="D" matrix={matrices.D} />
          </div>
        )}
      </div>

      {/* Controllability & Observability */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, marginTop: 16 }}>
        <div className={`mimo-rank-badge ${isCtrb ? 'mimo-rank-full' : 'mimo-rank-deficient'}`}>
          {isCtrb ? 'Controllable' : 'Not Controllable'} — rank(C) = {ctrlRank}/{n}
        </div>
        <div className={`mimo-rank-badge ${isObs ? 'mimo-rank-full' : 'mimo-rank-deficient'}`}>
          {isObs ? 'Observable' : 'Not Observable'} — rank(O) = {obsRank}/{n}
        </div>
      </div>

      {/* Variable names */}
      {(stateNames.length > 0 || inputNames.length > 0 || outputNames.length > 0) && (
        <div className="mimo-controller-info" style={{ marginTop: 16 }}>
          {stateNames.length > 0 && (
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              <span style={{ fontWeight: 600, fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.3px' }}>
                States:
              </span>
              {stateNames.map((name, i) => (
                <span key={i} style={{
                  fontFamily: "'Fira Code', monospace",
                  fontSize: 12,
                  color: 'var(--text-secondary)',
                  padding: '2px 8px',
                  background: 'rgba(20, 184, 166, 0.06)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-full)',
                }}>
                  x{i + 1} = {name}
                </span>
              ))}
            </div>
          )}
          {inputNames.length > 0 && (
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              <span style={{ fontWeight: 600, fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.3px' }}>
                Inputs:
              </span>
              {inputNames.map((name, i) => (
                <span key={i} style={{
                  fontFamily: "'Fira Code', monospace",
                  fontSize: 12,
                  color: 'var(--secondary-color)',
                  padding: '2px 8px',
                  background: 'rgba(59, 130, 246, 0.06)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-full)',
                }}>
                  u{i + 1} = {name}
                </span>
              ))}
            </div>
          )}
          {outputNames.length > 0 && (
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              <span style={{ fontWeight: 600, fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.3px' }}>
                Outputs:
              </span>
              {outputNames.map((name, i) => (
                <span key={i} style={{
                  fontFamily: "'Fira Code', monospace",
                  fontSize: 12,
                  color: 'var(--success-color)',
                  padding: '2px 8px',
                  background: 'rgba(16, 185, 129, 0.06)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-full)',
                }}>
                  y{i + 1} = {name}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Open-loop eigenvalues */}
      {metadata.eigenvalues && metadata.eigenvalues.real.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <div className="mimo-section-title">Open-Loop Eigenvalues</div>
          <EigenvalueChips
            real={metadata.eigenvalues.real}
            imag={metadata.eigenvalues.imag}
          />
        </div>
      )}
    </div>
  );
}

// ============================================================================
// EigenvalueChips — reusable eigenvalue display
// ============================================================================

function EigenvalueChips({ real, imag, label }) {
  if (!real || real.length === 0) return null;
  return (
    <div>
      {label && <div className="mimo-section-title">{label}</div>}
      <div className="mimo-eigenvalue-list">
        {real.map((re, i) => {
          const im = imag[i] ?? 0;
          const cls = re < -1e-10 ? 'stable' : Math.abs(re) < 1e-10 ? 'marginal' : 'unstable';
          return (
            <span key={`${re.toFixed(6)}_${im.toFixed(6)}_${i}`} className={cls}>
              {fmtEig(re, im)}
            </span>
          );
        })}
      </div>
    </div>
  );
}

// ============================================================================
// ControllerTab — gains, eigenvalues, cost matrices
// ============================================================================

function ControllerTab({ metadata }) {
  const designMode = metadata?.design_mode || 'analysis';
  const controller = metadata?.controller || {};

  if (designMode === 'analysis' || !controller.type) {
    return (
      <div className="mimo-tab-empty">
        Select a design mode (Pole Placement, LQR, or LQG) and configure parameters to see controller results.
      </div>
    );
  }

  if (controller.error) {
    return (
      <div className="mimo-error">
        <span>Controller Error:</span> {controller.error}
      </div>
    );
  }

  const typeLabel = controller.type === 'pole_placement' ? 'Pole Placement'
    : controller.type === 'lqr' ? 'LQR (Linear Quadratic Regulator)'
    : controller.type === 'lqg' ? 'LQG (Linear Quadratic Gaussian)'
    : controller.type;

  const isLQR = controller.type === 'lqr';
  const isLQG = controller.type === 'lqg';

  return (
    <div className="mimo-controller-info">
      <div className="mimo-section-title">{typeLabel}</div>

      {/* State-feedback gain K */}
      {controller.K && (
        <div className="mimo-matrix-card">
          <h4>State-Feedback Gain K</h4>
          <MatrixKaTeX label="K" matrix={controller.K} />
        </div>
      )}

      {/* LQR: CARE solution P, Q/R diagonals */}
      {isLQR && controller.P && (
        <div className="mimo-matrix-card">
          <h4>CARE Solution P</h4>
          <MatrixKaTeX label="P" matrix={controller.P} />
        </div>
      )}
      {isLQR && controller.Q_diag && (
        <div className="mimo-matrix-card">
          <h4>State Cost Q (diagonal)</h4>
          <DiagKaTeX label="Q" values={controller.Q_diag} />
        </div>
      )}
      {isLQR && controller.R_diag && (
        <div className="mimo-matrix-card">
          <h4>Input Cost R (diagonal)</h4>
          <DiagKaTeX label="R" values={controller.R_diag} />
        </div>
      )}

      {/* LQG: K, L, both P matrices, all cost diagonals */}
      {isLQG && controller.L && (
        <div className="mimo-matrix-card">
          <h4>Kalman Gain L</h4>
          <MatrixKaTeX label="L" matrix={controller.L} />
        </div>
      )}
      {isLQG && controller.P_lqr && (
        <div className="mimo-matrix-card">
          <h4>CARE Solution P (Regulator)</h4>
          <MatrixKaTeX label="P_{lqr}" matrix={controller.P_lqr} />
        </div>
      )}
      {isLQG && controller.P_kal && (
        <div className="mimo-matrix-card">
          <h4>FARE Solution P (Estimator)</h4>
          <MatrixKaTeX label="P_{kal}" matrix={controller.P_kal} />
        </div>
      )}
      {isLQG && controller.Q_diag && (
        <div className="mimo-matrix-card">
          <h4>State Cost Q</h4>
          <DiagKaTeX label="Q" values={controller.Q_diag} />
        </div>
      )}
      {isLQG && controller.R_diag && (
        <div className="mimo-matrix-card">
          <h4>Input Cost R</h4>
          <DiagKaTeX label="R" values={controller.R_diag} />
        </div>
      )}
      {isLQG && controller.Qw_diag && (
        <div className="mimo-matrix-card">
          <h4>Process Noise Qw</h4>
          <DiagKaTeX label="Q_w" values={controller.Qw_diag} />
        </div>
      )}
      {isLQG && controller.Rv_diag && (
        <div className="mimo-matrix-card">
          <h4>Measurement Noise Rv</h4>
          <DiagKaTeX label="R_v" values={controller.Rv_diag} />
        </div>
      )}

      {/* Closed-loop eigenvalues */}
      {controller.cl_eigs_real && controller.cl_eigs_real.length > 0 && (
        <EigenvalueChips
          real={controller.cl_eigs_real}
          imag={controller.cl_eigs_imag}
          label="Closed-Loop Eigenvalues"
        />
      )}

      {/* LQG: separate regulator and estimator eigenvalue groups */}
      {isLQG && controller.K_eigs_real && controller.K_eigs_real.length > 0 && (
        <EigenvalueChips
          real={controller.K_eigs_real}
          imag={controller.K_eigs_imag}
          label="Regulator Eigenvalues (A - BK)"
        />
      )}
      {isLQG && controller.L_eigs_real && controller.L_eigs_real.length > 0 && (
        <EigenvalueChips
          real={controller.L_eigs_real}
          imag={controller.L_eigs_imag}
          label="Estimator Eigenvalues (A - LC)"
        />
      )}
    </div>
  );
}

// ============================================================================
// DiagramTab — SVG block diagrams (3 variants)
// ============================================================================

function DiagramTab({ metadata, isDark }) {
  const designMode = metadata?.design_mode || 'analysis';
  const controller = metadata?.controller || {};
  const hasController = controller.type && !controller.error;

  const lineColor = 'var(--accent-color, #00d9ff)';
  const arrowId = 'mimo-arrow';
  const W = 650;
  const H = 250;
  const mainY = 70;
  const feedbackY = 200;

  // LQG diagram
  if (hasController && controller.type === 'lqg') {
    const sumX = 80, sumR = 16;
    const plantX = 260, plantW = 140, plantH = 44;
    const outX = 520;
    const takeoffX = plantX + plantW + 40;
    const kX = 380, kW = 80, kH = 36;
    const obsX = 160, obsW = 170, obsH = 36;

    return (
      <div className="mimo-diagram-container">
        <svg viewBox={`0 0 ${W} ${H}`} width="100%" preserveAspectRatio="xMidYMid meet">
          <defs>
            <marker id={arrowId} markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill={lineColor} />
            </marker>
          </defs>

          {/* r(t) input */}
          <line x1={15} y1={mainY} x2={sumX - sumR} y2={mainY}
            stroke={lineColor} strokeWidth={2} markerEnd={`url(#${arrowId})`} />
          <text x={8} y={mainY - 12} className="mimo-svg-label" fill={isDark ? '#f1f5f9' : '#1e293b'}>r(t)</text>

          {/* Sum junction */}
          <circle cx={sumX} cy={mainY} r={sumR} fill="none" stroke={lineColor} strokeWidth={1.5} />
          <text x={sumX} y={mainY + 1} textAnchor="middle" dominantBaseline="middle"
            fill={lineColor} fontSize="14" fontWeight="600">{'\u03A3'}</text>
          <text x={sumX - sumR - 4} y={mainY + sumR + 4} fill="#ef4444" fontSize="11"
            fontWeight="600">{'\u2212'}</text>

          {/* u(t) to plant */}
          <line x1={sumX + sumR} y1={mainY} x2={plantX} y2={mainY}
            stroke={lineColor} strokeWidth={2} markerEnd={`url(#${arrowId})`} />
          <text x={(sumX + sumR + plantX) / 2} y={mainY - 12} textAnchor="middle"
            className="mimo-svg-label" fill={isDark ? '#94a3b8' : '#64748b'} fontSize="10">u</text>

          {/* Plant block */}
          <rect x={plantX} y={mainY - plantH / 2} width={plantW} height={plantH}
            rx={6} fill={isDark ? 'rgba(20,184,166,0.08)' : 'rgba(20,184,166,0.05)'}
            stroke="var(--primary-color)" strokeWidth={1.5} />
          <text x={plantX + plantW / 2} y={mainY - 6} textAnchor="middle"
            fill={isDark ? '#f1f5f9' : '#1e293b'} fontSize="12" fontWeight="600">Plant</text>
          <text x={plantX + plantW / 2} y={mainY + 10} textAnchor="middle"
            fill={isDark ? '#94a3b8' : '#64748b'} fontSize="10">(A, B, C, D)</text>

          {/* y(t) output */}
          <line x1={plantX + plantW} y1={mainY} x2={outX} y2={mainY}
            stroke={lineColor} strokeWidth={2} markerEnd={`url(#${arrowId})`} />
          <text x={outX + 8} y={mainY - 12} className="mimo-svg-label"
            fill={isDark ? '#f1f5f9' : '#1e293b'}>y(t)</text>

          {/* Takeoff point */}
          <circle cx={takeoffX} cy={mainY} r={4} fill={lineColor} />

          {/* Takeoff down to feedback */}
          <line x1={takeoffX} y1={mainY} x2={takeoffX} y2={feedbackY}
            stroke={lineColor} strokeWidth={2} />

          {/* K block (right side of feedback) */}
          <rect x={kX} y={feedbackY - kH / 2} width={kW} height={kH}
            rx={6} fill={isDark ? 'rgba(245,158,11,0.08)' : 'rgba(245,158,11,0.05)'}
            stroke="var(--warning-color)" strokeWidth={1.5} />
          <text x={kX + kW / 2} y={feedbackY + 4} textAnchor="middle"
            fill={isDark ? '#f1f5f9' : '#1e293b'} fontSize="12" fontWeight="600">-K</text>

          {/* Kalman Filter block (left side) */}
          <rect x={obsX} y={feedbackY - obsH / 2} width={obsW} height={obsH}
            rx={6} fill={isDark ? 'rgba(124,58,237,0.08)' : 'rgba(124,58,237,0.05)'}
            stroke="var(--accent-purple, #7c3aed)" strokeWidth={1.5} />
          <text x={obsX + obsW / 2} y={feedbackY + 4} textAnchor="middle"
            fill={isDark ? '#f1f5f9' : '#1e293b'} fontSize="11" fontWeight="600">Kalman Filter (L)</text>

          {/* Takeoff to K (y signal) */}
          <line x1={takeoffX} y1={feedbackY} x2={kX + kW} y2={feedbackY}
            stroke={lineColor} strokeWidth={2} markerEnd={`url(#${arrowId})`} />
          <text x={(takeoffX + kX + kW) / 2} y={feedbackY - 12} textAnchor="middle"
            fill={isDark ? '#94a3b8' : '#64748b'} fontSize="9">y</text>

          {/* K to Observer */}
          <line x1={kX} y1={feedbackY} x2={obsX + obsW} y2={feedbackY}
            stroke={lineColor} strokeWidth={2} markerEnd={`url(#${arrowId})`} />
          <text x={(kX + obsX + obsW) / 2} y={feedbackY - 12} textAnchor="middle"
            fill={isDark ? '#94a3b8' : '#64748b'} fontSize="9">{'\u0078\u0302'}</text>

          {/* Observer to sum */}
          <line x1={obsX} y1={feedbackY} x2={sumX} y2={feedbackY}
            stroke={lineColor} strokeWidth={2} />
          <line x1={sumX} y1={feedbackY} x2={sumX} y2={mainY + sumR}
            stroke={lineColor} strokeWidth={2} markerEnd={`url(#${arrowId})`} />
          <text x={(obsX + sumX) / 2} y={feedbackY - 12} textAnchor="middle"
            fill={isDark ? '#94a3b8' : '#64748b'} fontSize="9">{`K\u0078\u0302`}</text>
        </svg>
      </div>
    );
  }

  // State feedback / pole placement / LQR diagram
  if (hasController && (controller.type === 'pole_placement' || controller.type === 'lqr')) {
    const sumX = 90, sumR = 16;
    const plantX = 260, plantW = 160, plantH = 48;
    const outX = 540;
    const takeoffX = plantX + plantW + 40;
    const kX = 240, kW = 130, kH = 38;

    return (
      <div className="mimo-diagram-container">
        <svg viewBox={`0 0 ${W} ${H}`} width="100%" preserveAspectRatio="xMidYMid meet">
          <defs>
            <marker id={arrowId} markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill={lineColor} />
            </marker>
          </defs>

          {/* r(t) input */}
          <line x1={15} y1={mainY} x2={sumX - sumR} y2={mainY}
            stroke={lineColor} strokeWidth={2} markerEnd={`url(#${arrowId})`} />
          <text x={8} y={mainY - 12} className="mimo-svg-label" fill={isDark ? '#f1f5f9' : '#1e293b'}>r(t)</text>

          {/* Sum junction */}
          <circle cx={sumX} cy={mainY} r={sumR} fill="none" stroke={lineColor} strokeWidth={1.5} />
          <text x={sumX} y={mainY + 1} textAnchor="middle" dominantBaseline="middle"
            fill={lineColor} fontSize="14" fontWeight="600">{'\u03A3'}</text>
          <text x={sumX - sumR - 4} y={mainY + sumR + 4} fill="#ef4444" fontSize="11"
            fontWeight="600">{'\u2212'}</text>

          {/* u = r - Kx label */}
          <line x1={sumX + sumR} y1={mainY} x2={plantX} y2={mainY}
            stroke={lineColor} strokeWidth={2} markerEnd={`url(#${arrowId})`} />
          <text x={(sumX + sumR + plantX) / 2} y={mainY - 12} textAnchor="middle"
            className="mimo-svg-label" fill={isDark ? '#94a3b8' : '#64748b'} fontSize="10">u = r - Kx</text>

          {/* Plant block */}
          <rect x={plantX} y={mainY - plantH / 2} width={plantW} height={plantH}
            rx={6} fill={isDark ? 'rgba(20,184,166,0.08)' : 'rgba(20,184,166,0.05)'}
            stroke="var(--primary-color)" strokeWidth={1.5} />
          <text x={plantX + plantW / 2} y={mainY - 6} textAnchor="middle"
            fill={isDark ? '#f1f5f9' : '#1e293b'} fontSize="12" fontWeight="600">Plant (A, B)</text>
          <text x={plantX + plantW / 2} y={mainY + 10} textAnchor="middle"
            fill={isDark ? '#94a3b8' : '#64748b'} fontSize="10">y = Cx + Du</text>

          {/* y(t) output */}
          <line x1={plantX + plantW} y1={mainY} x2={outX} y2={mainY}
            stroke={lineColor} strokeWidth={2} markerEnd={`url(#${arrowId})`} />
          <text x={outX + 8} y={mainY - 12} className="mimo-svg-label"
            fill={isDark ? '#f1f5f9' : '#1e293b'}>y(t)</text>

          {/* Takeoff point for x */}
          <circle cx={takeoffX} cy={mainY} r={4} fill={lineColor} />
          <text x={takeoffX + 10} y={(mainY + feedbackY) / 2} fill={isDark ? '#94a3b8' : '#64748b'}
            fontSize="10">x(t)</text>

          {/* Feedback path */}
          <line x1={takeoffX} y1={mainY} x2={takeoffX} y2={feedbackY}
            stroke={lineColor} strokeWidth={2} />

          {/* K block */}
          <rect x={kX} y={feedbackY - kH / 2} width={kW} height={kH}
            rx={6} fill={isDark ? 'rgba(245,158,11,0.08)' : 'rgba(245,158,11,0.05)'}
            stroke="var(--warning-color)" strokeWidth={1.5} />
          <text x={kX + kW / 2} y={feedbackY + 4} textAnchor="middle"
            fill={isDark ? '#f1f5f9' : '#1e293b'} fontSize="12" fontWeight="600">-K</text>

          {/* Lines: takeoff -> K -> sum */}
          <line x1={takeoffX} y1={feedbackY} x2={kX + kW} y2={feedbackY}
            stroke={lineColor} strokeWidth={2} markerEnd={`url(#${arrowId})`} />
          <line x1={kX} y1={feedbackY} x2={sumX} y2={feedbackY}
            stroke={lineColor} strokeWidth={2} />
          <line x1={sumX} y1={feedbackY} x2={sumX} y2={mainY + sumR}
            stroke={lineColor} strokeWidth={2} markerEnd={`url(#${arrowId})`} />
        </svg>
      </div>
    );
  }

  // Analysis mode (open-loop state-space diagram)
  if (designMode === 'analysis' || !hasController) {
    const bX = 100, bW = 60, bH = 36;
    const sumX = 220, sumR = 16;
    const intX = 280, intW = 60, intH = 36;
    const cX = 440, cW = 60, cH = 36;
    const aX = 280, aW = 60, aH = 36;
    const outX = 570;
    const aY = 180;

    return (
      <div className="mimo-diagram-container">
        <svg viewBox={`0 0 ${W} ${H}`} width="100%" preserveAspectRatio="xMidYMid meet">
          <defs>
            <marker id={arrowId} markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill={lineColor} />
            </marker>
          </defs>

          {/* u input */}
          <line x1={15} y1={mainY} x2={bX} y2={mainY}
            stroke={lineColor} strokeWidth={2} markerEnd={`url(#${arrowId})`} />
          <text x={8} y={mainY - 12} fill={isDark ? '#f1f5f9' : '#1e293b'} fontSize="12" fontWeight="600">u</text>

          {/* B block */}
          <rect x={bX} y={mainY - bH / 2} width={bW} height={bH}
            rx={6} fill={isDark ? 'rgba(59,130,246,0.08)' : 'rgba(59,130,246,0.05)'}
            stroke="var(--secondary-color)" strokeWidth={1.5} />
          <text x={bX + bW / 2} y={mainY + 4} textAnchor="middle"
            fill={isDark ? '#f1f5f9' : '#1e293b'} fontSize="13" fontWeight="600">B</text>

          {/* B to sum */}
          <line x1={bX + bW} y1={mainY} x2={sumX - sumR} y2={mainY}
            stroke={lineColor} strokeWidth={2} markerEnd={`url(#${arrowId})`} />

          {/* Sum junction */}
          <circle cx={sumX} cy={mainY} r={sumR} fill="none" stroke={lineColor} strokeWidth={1.5} />
          <text x={sumX} y={mainY + 1} textAnchor="middle" dominantBaseline="middle"
            fill={lineColor} fontSize="14" fontWeight="600">+</text>

          {/* Sum to integrator */}
          <line x1={sumX + sumR} y1={mainY} x2={intX} y2={mainY}
            stroke={lineColor} strokeWidth={2} markerEnd={`url(#${arrowId})`} />

          {/* Integrator block */}
          <rect x={intX} y={mainY - intH / 2} width={intW} height={intH}
            rx={6} fill={isDark ? 'rgba(20,184,166,0.08)' : 'rgba(20,184,166,0.05)'}
            stroke="var(--primary-color)" strokeWidth={1.5} />
          <text x={intX + intW / 2} y={mainY + 4} textAnchor="middle"
            fill={isDark ? '#f1f5f9' : '#1e293b'} fontSize="13" fontWeight="600">{'\u222B'}</text>

          {/* Integrator output: x */}
          <line x1={intX + intW} y1={mainY} x2={cX} y2={mainY}
            stroke={lineColor} strokeWidth={2} markerEnd={`url(#${arrowId})`} />
          <text x={(intX + intW + cX) / 2} y={mainY - 12} textAnchor="middle"
            fill={isDark ? '#94a3b8' : '#64748b'} fontSize="11" fontWeight="600">x</text>

          {/* Takeoff for feedback */}
          <circle cx={(intX + intW + cX) / 2} cy={mainY} r={4} fill={lineColor} />

          {/* C block */}
          <rect x={cX} y={mainY - cH / 2} width={cW} height={cH}
            rx={6} fill={isDark ? 'rgba(16,185,129,0.08)' : 'rgba(16,185,129,0.05)'}
            stroke="var(--success-color)" strokeWidth={1.5} />
          <text x={cX + cW / 2} y={mainY + 4} textAnchor="middle"
            fill={isDark ? '#f1f5f9' : '#1e293b'} fontSize="13" fontWeight="600">C</text>

          {/* y output */}
          <line x1={cX + cW} y1={mainY} x2={outX} y2={mainY}
            stroke={lineColor} strokeWidth={2} markerEnd={`url(#${arrowId})`} />
          <text x={outX + 8} y={mainY - 12} fill={isDark ? '#f1f5f9' : '#1e293b'} fontSize="12" fontWeight="600">y</text>

          {/* Feedback path: x -> A -> sum */}
          {/* Down from takeoff */}
          <line x1={(intX + intW + cX) / 2} y1={mainY} x2={(intX + intW + cX) / 2} y2={aY}
            stroke={lineColor} strokeWidth={2} />

          {/* Horizontal to A */}
          <line x1={(intX + intW + cX) / 2} y1={aY} x2={aX + aW} y2={aY}
            stroke={lineColor} strokeWidth={2} markerEnd={`url(#${arrowId})`} />

          {/* A block */}
          <rect x={aX} y={aY - aH / 2} width={aW} height={aH}
            rx={6} fill={isDark ? 'rgba(239,68,68,0.08)' : 'rgba(239,68,68,0.05)'}
            stroke="var(--error-color)" strokeWidth={1.5} />
          <text x={aX + aW / 2} y={aY + 4} textAnchor="middle"
            fill={isDark ? '#f1f5f9' : '#1e293b'} fontSize="13" fontWeight="600">A</text>

          {/* A to sum */}
          <line x1={aX} y1={aY} x2={sumX} y2={aY}
            stroke={lineColor} strokeWidth={2} />
          <line x1={sumX} y1={aY} x2={sumX} y2={mainY + sumR}
            stroke={lineColor} strokeWidth={2} markerEnd={`url(#${arrowId})`} />
        </svg>
      </div>
    );
  }

  return <div className="mimo-tab-empty">Select a design mode to view the block diagram.</div>;
}

// ============================================================================
// Main component
// ============================================================================

export default function MIMODesignStudioViewer({ metadata, plots, onParamChange }) {
  const isDark = useTheme();
  const [activeTab, setActiveTab] = useState('response');

  const designMode = metadata?.design_mode || 'analysis';
  const controller = metadata?.controller || {};
  const hasController = !!(controller.type && !controller.error);
  const errorMsg = metadata?.error;

  // Warnings for controllability/observability
  const isCtrb = metadata?.is_controllable;
  const isObs = metadata?.is_observable;
  const showCtrbWarning = isCtrb === false && designMode !== 'analysis';
  const showObsWarning = isObs === false && designMode === 'lqg';

  return (
    <div className="mimo-studio">
      {/* Error banner */}
      {errorMsg && (
        <div className="mimo-error" role="alert">
          <span style={{ fontSize: 16 }}>{'\u26A0'}</span>
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Controllability / Observability warnings */}
      {showCtrbWarning && (
        <div className="mimo-warning">
          <span>{'\u26A0'}</span>
          <span>System is not fully controllable. Controller design may fail or produce poor results.</span>
        </div>
      )}
      {showObsWarning && (
        <div className="mimo-warning">
          <span>{'\u26A0'}</span>
          <span>System is not fully observable. LQG observer design may fail.</span>
        </div>
      )}

      {/* Metrics strip */}
      <MetricsStrip metadata={metadata} />

      {/* Tab bar */}
      <div className="mimo-tabs" role="tablist">
        {TABS.map(t => (
          <button
            key={t.id}
            role="tab"
            aria-selected={activeTab === t.id}
            className={`mimo-tab ${activeTab === t.id ? 'active' : ''}`}
            onClick={() => setActiveTab(t.id)}
          >
            <span style={{ marginRight: 6 }}>{t.icon}</span>
            <span>{t.label}</span>
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="mimo-tab-content">
        {activeTab === 'response' && (
          <ResponseTab plots={plots} isDark={isDark} hasController={hasController} />
        )}

        {activeTab === 'pole_zero' && (
          <PoleZeroTab plots={plots} isDark={isDark} />
        )}

        {activeTab === 'properties' && (
          <PropertiesTab metadata={metadata} />
        )}

        {activeTab === 'controller' && (
          <ControllerTab metadata={metadata} />
        )}

        {activeTab === 'diagram' && (
          <DiagramTab metadata={metadata} isDark={isDark} />
        )}
      </div>
    </div>
  );
}
