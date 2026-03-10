import React, { useRef, useEffect, useCallback, useState, useMemo } from 'react';
import Plot from 'react-plotly.js';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import '../styles/StateSpaceViewer.css';

// ---------------------------------------------------------------------------
// Tiny helpers
// ---------------------------------------------------------------------------

function useTheme() {
  const [isDark, setIsDark] = useState(
    () => document.documentElement.getAttribute('data-theme') !== 'light'
  );
  useEffect(() => {
    const obs = new MutationObserver(() =>
      setIsDark(document.documentElement.getAttribute('data-theme') !== 'light')
    );
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => obs.disconnect();
  }, []);
  return isDark;
}

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
    ? <div ref={ref} className={`ss-katex-display ${className}`} />
    : <span ref={ref} className={`ss-katex-inline ${className}`} />;
}

// ---------------------------------------------------------------------------
// Tab definitions  —  order matters, rendered left→right
// ---------------------------------------------------------------------------

const TABS = [
  { id: 'time',       label: 'Time Response',  icon: '\u23F1' },
  { id: 'pole_zero',  label: 'Pole-Zero',      icon: '\u2716' },
  { id: 'bode',       label: 'Bode',           icon: '\u223F' },
  { id: 'properties', label: 'Properties',     icon: '\u2699' },
  { id: 'derivation', label: 'Derivation',     icon: '\u03A3' },
];

// Map plot IDs to tabs
const PLOT_TAB_MAP = {
  step_response:    'time',
  impulse_response: 'time',
  eigenvalue_map:   'pole_zero',
  phase_portrait:   'pole_zero',
  bode_magnitude:   'bode',
  bode_phase:       'bode',
};

// ---------------------------------------------------------------------------
// Matrix display (KaTeX inline)
// ---------------------------------------------------------------------------

function MatrixKaTeX({ label, matrix }) {
  if (!matrix || matrix.length === 0) return null;
  const fmt = (v) => {
    const n = typeof v === 'number' ? v : parseFloat(v);
    if (!isFinite(n) || Math.abs(n) < 1e-12) return '0';
    return parseFloat(n.toPrecision(4)).toString();
  };
  const rows = Array.isArray(matrix[0]) ? matrix : [matrix];
  const latex = `\\mathbf{${label}} = \\begin{bmatrix} ${rows
    .map(r => (Array.isArray(r) ? r : [r]).map(fmt).join(' & '))
    .join(' \\\\ ')} \\end{bmatrix}`;
  return <LaTeX math={latex} display={false} />;
}

// ---------------------------------------------------------------------------
// Plotly wrapper (shared by all tabs)
// ---------------------------------------------------------------------------

const plotlyConfig = {
  responsive: true,
  displayModeBar: true,
  modeBarButtonsToRemove: ['lasso2d', 'select2d'],
  displaylogo: false,
  toImageButtonOptions: { format: 'png', scale: 2 },
};

function SSPlot({ plotData, isDark, height = 340 }) {
  const layout = useMemo(() => ({
    ...plotData.layout,
    paper_bgcolor: isDark ? 'rgba(13,20,45,0)' : 'rgba(255,255,255,0)',
    plot_bgcolor: isDark ? 'rgba(19,27,46,0.6)' : 'rgba(248,250,252,0.8)',
    font: {
      ...(plotData.layout?.font || {}),
      color: isDark ? '#f1f5f9' : '#1e293b',
    },
    xaxis: {
      ...(plotData.layout?.xaxis || {}),
      color: isDark ? '#94a3b8' : '#475569',
      gridcolor: isDark ? 'rgba(148,163,184,0.1)' : 'rgba(100,116,139,0.15)',
      zerolinecolor: isDark ? 'rgba(148,163,184,0.3)' : 'rgba(100,116,139,0.4)',
    },
    yaxis: {
      ...(plotData.layout?.yaxis || {}),
      color: isDark ? '#94a3b8' : '#475569',
      gridcolor: isDark ? 'rgba(148,163,184,0.1)' : 'rgba(100,116,139,0.15)',
      zerolinecolor: isDark ? 'rgba(148,163,184,0.3)' : 'rgba(100,116,139,0.4)',
      autorange: plotData.layout?.yaxis?.autorange ?? true,
    },
    datarevision: `${plotData.id}-${plotData.title}-${Date.now()}`,
    uirevision: plotData.layout?.uirevision ?? plotData.id,
  }), [plotData, isDark]);

  return (
    <div className="ss-plot-card">
      <div className="ss-plot-card-title">{plotData.title}</div>
      <Plot
        data={plotData.data || []}
        layout={layout}
        config={plotlyConfig}
        style={{ width: '100%', height }}
        useResizeHandler
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// System Summary banner  (always visible above tabs)
// ---------------------------------------------------------------------------

function SystemSummary({ metadata }) {
  const presetName = metadata?.preset_name ?? '';
  const eigenvalues = metadata?.eigenvalues ?? { real: [], imag: [] };
  const isStable = metadata?.is_stable;
  const isMarginal = metadata?.is_marginal ?? false;
  const systemOrder = metadata?.system_order ?? 0;
  const systemType = metadata?.system_type ?? 'linear_tf';
  const matrices = metadata?.matrices ?? {};

  const stabilityBadge =
    isStable === true  ? { label: 'Stable',    cls: 'stable' } :
    isMarginal         ? { label: 'Marginal',  cls: 'marginal' } :
    isStable === false ? { label: 'Unstable',  cls: 'unstable' } :
    { label: 'Unknown', cls: 'unknown' };

  const typeLabel =
    systemType === 'nonlinear' ? 'Nonlinear \u2192 Linearized' :
    systemType === 'state_space' ? 'Direct SS' : 'Linear TF';

  return (
    <div className="ss-summary">
      {/* Row 1: badges */}
      <div className="ss-summary-badges">
        {presetName && <span className="ss-badge ss-badge-preset">{presetName}</span>}
        <span className={`ss-badge ss-badge-stability ${stabilityBadge.cls}`}>
          {stabilityBadge.label}
        </span>
        {systemOrder > 0 && (
          <span className="ss-badge ss-badge-order">n={systemOrder}</span>
        )}
        <span className="ss-badge ss-badge-type">{typeLabel}</span>
      </div>

      {/* Row 2: matrices */}
      {matrices.A && (
        <div className="ss-summary-matrices">
          <div className="ss-matrix-row">
            {matrices.A && <span className="ss-matrix-item"><MatrixKaTeX label="A" matrix={matrices.A} /></span>}
            {matrices.B && <span className="ss-matrix-item"><MatrixKaTeX label="B" matrix={matrices.B} /></span>}
            {matrices.C && <span className="ss-matrix-item"><MatrixKaTeX label="C" matrix={matrices.C} /></span>}
            {matrices.D != null && (
              <span className="ss-matrix-item">
                <LaTeX math={`\\mathbf{D} = ${Array.isArray(matrices.D[0])
                  ? parseFloat(matrices.D[0][0].toPrecision(4))
                  : parseFloat(matrices.D[0].toPrecision(4))}`} />
              </span>
            )}
          </div>
          <div className="ss-core-eqs">
            <LaTeX math="\\dot{\\mathbf{x}} = A\\mathbf{x} + Bu" />
            <span className="ss-eq-sep">,</span>
            <LaTeX math="y = C\\mathbf{x} + Du" />
          </div>
        </div>
      )}

      {/* Row 3: eigenvalue chips */}
      {eigenvalues.real.length > 0 && (
        <div className="ss-eigenvalue-chips">
          {eigenvalues.real.map((r, i) => {
            const im = eigenvalues.imag[i] ?? 0;
            const stable = r < -1e-10;
            const label =
              Math.abs(im) < 1e-10
                ? `\u03BB = ${r.toFixed(3)}`
                : im > 0
                ? `\u03BB = ${r.toFixed(3)} + ${im.toFixed(3)}j`
                : `\u03BB = ${r.toFixed(3)} \u2212 ${Math.abs(im).toFixed(3)}j`;
            return (
              <span key={`${r.toFixed(6)}_${im.toFixed(6)}`}
                    className={`ss-eig-chip ${stable ? 'stable' : 'unstable'}`}>
                {label}
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Equilibrium info bar (nonlinear only)
// ---------------------------------------------------------------------------

function EquilibriumBar({ equilibriumPts, selEqIdx }) {
  if (!equilibriumPts || equilibriumPts.length === 0) return null;
  return (
    <div className="ss-eq-bar">
      <span className="ss-eq-bar-label">Equilibria:</span>
      {equilibriumPts.map(([x1, x2], i) => (
        <span key={`${x1.toFixed(4)}_${x2.toFixed(4)}`}
              className={`ss-eq-chip ${i === selEqIdx ? 'selected' : ''}`}>
          #{i + 1} ({x1.toFixed(3)}, {x2.toFixed(3)})
        </span>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Properties Tab content
// ---------------------------------------------------------------------------

function PropertiesPanel({ properties, eigenvalues, isStable, isMarginal, systemType }) {
  if (!properties || Object.keys(properties).length === 0) {
    return <div className="ss-empty-tab">Compute a system to see properties.</div>;
  }

  const {
    controllability_rank, is_controllable,
    observability_rank, is_observable,
    system_order, pole_info, dc_gain,
    tf_num, tf_den,
  } = properties;

  return (
    <div className="ss-properties-grid">
      {/* Controllability */}
      <div className="ss-prop-card">
        <div className="ss-prop-title">Controllability</div>
        <div className={`ss-prop-value ${is_controllable ? 'good' : 'bad'}`}>
          {is_controllable ? 'Controllable' : 'Not Controllable'}
        </div>
        <div className="ss-prop-detail">
          rank(C) = {controllability_rank} / {system_order}
        </div>
        <div className="ss-prop-explain">
          <LaTeX math={`\\mathcal{C} = [B \\;\\; AB \\;\\; \\cdots \\;\\; A^{${system_order - 1}}B]`} />
        </div>
      </div>

      {/* Observability */}
      <div className="ss-prop-card">
        <div className="ss-prop-title">Observability</div>
        <div className={`ss-prop-value ${is_observable ? 'good' : 'bad'}`}>
          {is_observable ? 'Observable' : 'Not Observable'}
        </div>
        <div className="ss-prop-detail">
          rank(O) = {observability_rank} / {system_order}
        </div>
        <div className="ss-prop-explain">
          <LaTeX math={`\\mathcal{O} = [C^T \\;\\; (CA)^T \\;\\; \\cdots \\;\\; (CA^{${system_order - 1}})^T]^T`} />
        </div>
      </div>

      {/* Stability */}
      <div className="ss-prop-card">
        <div className="ss-prop-title">Stability</div>
        <div className={`ss-prop-value ${isStable ? 'good' : isMarginal ? 'warn' : 'bad'}`}>
          {isStable ? 'Asymptotically Stable' : isMarginal ? 'Marginally Stable' : 'Unstable'}
        </div>
        <div className="ss-prop-detail">
          {isStable
            ? 'All eigenvalues in open left half-plane'
            : isMarginal
            ? 'Eigenvalue(s) on j\u03c9 axis'
            : 'Eigenvalue(s) in right half-plane'}
        </div>
      </div>

      {/* DC Gain */}
      <div className="ss-prop-card">
        <div className="ss-prop-title">DC Gain</div>
        <div className="ss-prop-value neutral">
          {dc_gain != null && isFinite(dc_gain) ? dc_gain.toFixed(4) : 'N/A'}
        </div>
        {dc_gain != null && (
          <div className="ss-prop-explain">
            <LaTeX math="K_{dc} = C(-A)^{-1}B + D" />
          </div>
        )}
      </div>

      {/* Pole analysis table */}
      {pole_info && pole_info.length > 0 && (
        <div className="ss-prop-card ss-prop-wide">
          <div className="ss-prop-title">Pole Analysis</div>
          <table className="ss-pole-table">
            <thead>
              <tr>
                <th>Pole</th>
                <th>\u03c9<sub>n</sub> (rad/s)</th>
                <th>\u03b6</th>
                <th>Type</th>
              </tr>
            </thead>
            <tbody>
              {pole_info.map((p, i) => {
                const poleStr = Math.abs(p.imag) < 1e-10
                  ? p.real.toFixed(4)
                  : p.imag > 0
                  ? `${p.real.toFixed(4)} + ${p.imag.toFixed(4)}j`
                  : `${p.real.toFixed(4)} \u2212 ${Math.abs(p.imag).toFixed(4)}j`;
                const type =
                  p.zeta >= 1.0 ? 'Overdamped' :
                  Math.abs(p.zeta - 1.0) < 0.01 ? 'Crit. Damped' :
                  p.zeta > 0 ? 'Underdamped' :
                  p.zeta === 0 ? 'Undamped' : 'Unstable';
                return (
                  <tr key={i}>
                    <td className="mono">{poleStr}</td>
                    <td>{p.omega_n.toFixed(4)}</td>
                    <td>{p.zeta.toFixed(4)}</td>
                    <td className={p.zeta > 0 ? 'good' : 'bad'}>{type}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Transfer Function (if available) */}
      {tf_num && tf_den && (
        <div className="ss-prop-card ss-prop-wide">
          <div className="ss-prop-title">Equivalent Transfer Function</div>
          <div className="ss-prop-explain">
            <LaTeX math={`H(s) = \\frac{${polyToLatex(tf_num)}}{${polyToLatex(tf_den)}}`} display />
          </div>
        </div>
      )}
    </div>
  );
}

function polyToLatex(coeffs) {
  if (!coeffs || coeffs.length === 0) return '0';
  const n = coeffs.length - 1;
  const terms = [];
  for (let i = 0; i < coeffs.length; i++) {
    const c = coeffs[i];
    const power = n - i;
    if (Math.abs(c) < 1e-12) continue;
    const cAbs = Math.abs(c);
    const sign = c < 0 ? '-' : (terms.length > 0 ? '+' : '');
    let coefStr = '';
    if (power === 0) {
      coefStr = cAbs.toPrecision(4);
    } else {
      coefStr = Math.abs(cAbs - 1) < 1e-12 ? '' : cAbs.toPrecision(4);
    }
    let varStr = power === 0 ? '' : power === 1 ? 's' : `s^{${power}}`;
    terms.push(`${sign} ${coefStr}${varStr}`);
  }
  return terms.join(' ').trim() || '0';
}

// ---------------------------------------------------------------------------
// Derivation Tab content
// ---------------------------------------------------------------------------

function DerivationPanel({ latexSteps }) {
  const [expanded, setExpanded] = useState({});
  const prevCount = useRef(0);

  useEffect(() => {
    if (latexSteps.length > 0 && latexSteps.length !== prevCount.current) {
      prevCount.current = latexSteps.length;
      const all = {};
      latexSteps.forEach((_, i) => { all[i] = true; });
      setExpanded(all);
    }
  }, [latexSteps.length]);

  const toggle = useCallback((i) => {
    setExpanded(prev => ({ ...prev, [i]: !prev[i] }));
  }, []);

  const expandAll = useCallback(() => {
    const all = {};
    latexSteps.forEach((_, i) => { all[i] = true; });
    setExpanded(all);
  }, [latexSteps]);

  const collapseAll = useCallback(() => setExpanded({}), []);

  if (!latexSteps || latexSteps.length === 0) {
    return <div className="ss-empty-tab">Compute a system to see the derivation.</div>;
  }

  return (
    <div className="ss-derivation">
      <div className="ss-deriv-toolbar">
        <button className="ss-text-btn" onClick={expandAll}>Expand all</button>
        <span className="ss-sep">|</span>
        <button className="ss-text-btn" onClick={collapseAll}>Collapse all</button>
      </div>
      <div className="ss-deriv-steps">
        {latexSteps.map((step, i) => (
          <div key={i} className={`ss-step ${expanded[i] ? 'open' : ''}`}>
            <button className="ss-step-header" onClick={() => toggle(i)}
                    aria-expanded={!!expanded[i]}>
              <span className="ss-step-title">{step.title}</span>
              <span className="ss-step-chevron">{expanded[i] ? '\u25BE' : '\u25B8'}</span>
            </button>
            {expanded[i] && (
              <div className="ss-step-body">
                <div className="ss-step-latex">
                  <LaTeX math={step.latex} display />
                </div>
                {step.explanation && (
                  <p className="ss-step-explain">{step.explanation}</p>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main StateSpaceViewer — tabbed workspace
// ---------------------------------------------------------------------------

export default function StateSpaceViewer({ metadata, plots, onButtonClick, isUpdating }) {
  const isDark = useTheme();
  const [activeTab, setActiveTab] = useState('time');

  const systemType = metadata?.system_type ?? 'linear_tf';
  const latexSteps = metadata?.latex_steps ?? [];
  const equilibriumPts = metadata?.equilibrium_points ?? [];
  const selEqIdx = metadata?.selected_eq_idx ?? 0;
  const errorMsg = metadata?.error;
  const properties = metadata?.properties ?? {};

  // Group plots by tab
  const plotsByTab = useMemo(() => {
    const map = { time: [], pole_zero: [], bode: [] };
    (plots || []).forEach(p => {
      const tab = PLOT_TAB_MAP[p.id];
      if (tab && map[tab]) map[tab].push(p);
    });
    return map;
  }, [plots]);

  // Auto-select first non-empty tab when data arrives
  const prevPlotsLen = useRef(0);
  useEffect(() => {
    const totalPlots = (plots || []).length;
    if (totalPlots > 0 && prevPlotsLen.current === 0) {
      if (plotsByTab.time.length > 0) setActiveTab('time');
      else if (plotsByTab.pole_zero.length > 0) setActiveTab('pole_zero');
    }
    prevPlotsLen.current = totalPlots;
  }, [plots, plotsByTab]);

  const handleCompute = useCallback(() => {
    if (onButtonClick) onButtonClick('compute', {});
  }, [onButtonClick]);

  // Determine which tabs are available
  const availableTabs = useMemo(() => {
    return TABS.filter(t => {
      if (t.id === 'time') return plotsByTab.time.length > 0;
      if (t.id === 'pole_zero') return plotsByTab.pole_zero.length > 0;
      if (t.id === 'bode') return plotsByTab.bode.length > 0;
      if (t.id === 'properties') return Object.keys(properties).length > 0;
      if (t.id === 'derivation') return latexSteps.length > 0;
      return true;
    });
  }, [plotsByTab, properties, latexSteps]);

  return (
    <div className="ss-viewer">
      {/* Error banner */}
      {errorMsg && (
        <div className="ss-error" role="alert">
          <span className="ss-error-icon">\u26A0</span>
          <span>{errorMsg}</span>
        </div>
      )}

      {/* System summary */}
      <SystemSummary metadata={metadata} />

      {/* Equilibrium bar (nonlinear) */}
      {systemType === 'nonlinear' && (
        <EquilibriumBar equilibriumPts={equilibriumPts} selEqIdx={selEqIdx} />
      )}

      {/* Compute button (prominent, above tabs) */}
      <div className="ss-toolbar">
        <button className="ss-compute-btn" onClick={handleCompute} disabled={isUpdating}>
          {isUpdating ? 'Computing\u2026' : 'Compute System'}
        </button>
      </div>

      {/* Tab bar */}
      {availableTabs.length > 0 && (
        <div className="ss-tabs" role="tablist">
          {availableTabs.map(t => (
            <button
              key={t.id}
              role="tab"
              aria-selected={activeTab === t.id}
              className={`ss-tab ${activeTab === t.id ? 'active' : ''}`}
              onClick={() => setActiveTab(t.id)}
            >
              <span className="ss-tab-icon">{t.icon}</span>
              <span className="ss-tab-label">{t.label}</span>
            </button>
          ))}
        </div>
      )}

      {/* Tab content */}
      <div className="ss-tab-content">
        {activeTab === 'time' && (
          <div className="ss-plot-grid ss-plot-grid-2">
            {plotsByTab.time.map(p => (
              <SSPlot key={p.id} plotData={p} isDark={isDark} height={360} />
            ))}
          </div>
        )}

        {activeTab === 'pole_zero' && (
          <div className={`ss-plot-grid ${plotsByTab.pole_zero.length > 1 ? 'ss-plot-grid-2' : 'ss-plot-grid-1'}`}>
            {plotsByTab.pole_zero.map(p => (
              <SSPlot key={p.id} plotData={p} isDark={isDark}
                      height={plotsByTab.pole_zero.length === 1 ? 500 : 400} />
            ))}
          </div>
        )}

        {activeTab === 'bode' && (
          <div className="ss-plot-grid ss-plot-grid-bode">
            {plotsByTab.bode.map(p => (
              <SSPlot key={p.id} plotData={p} isDark={isDark} height={300} />
            ))}
          </div>
        )}

        {activeTab === 'properties' && (
          <PropertiesPanel
            properties={properties}
            eigenvalues={metadata?.eigenvalues}
            isStable={metadata?.is_stable}
            isMarginal={metadata?.is_marginal}
            systemType={systemType}
          />
        )}

        {activeTab === 'derivation' && (
          <DerivationPanel latexSteps={latexSteps} />
        )}

        {/* Fallback if active tab has no content */}
        {!['time', 'pole_zero', 'bode', 'properties', 'derivation'].includes(activeTab) && (
          <div className="ss-empty-tab">Select a tab to view analysis results.</div>
        )}
      </div>
    </div>
  );
}
