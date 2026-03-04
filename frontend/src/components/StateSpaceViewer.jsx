import React, { useRef, useEffect, useCallback, useState, useMemo } from 'react';
import Plot from 'react-plotly.js';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import '../styles/StateSpaceViewer.css';

// ---------------------------------------------------------------------------
// KaTeX renderer component
// Uses div for display mode (block) and span for inline to avoid
// the block-inside-inline collapse problem.
// ---------------------------------------------------------------------------
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
  // IMPORTANT: display mode renders a block element, so the wrapper must also
  // be a block element. Using <span> causes it to collapse to zero height.
  return display
    ? <div ref={ref} className={`ss-katex-display ${className}`} />
    : <span ref={ref} className={`ss-katex-inline ${className}`} />;
}

// ---------------------------------------------------------------------------
// useTheme hook
// ---------------------------------------------------------------------------
function useTheme() {
  const [isDark, setIsDark] = useState(
    () => document.documentElement.getAttribute('data-theme') !== 'light'
  );
  useEffect(() => {
    const observer = new MutationObserver(() => {
      setIsDark(document.documentElement.getAttribute('data-theme') !== 'light');
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => observer.disconnect();
  }, []);
  return isDark;
}

// ---------------------------------------------------------------------------
// Matrix display component
// ---------------------------------------------------------------------------
function MatrixDisplay({ label, matrix, isDark }) {
  if (!matrix || matrix.length === 0) return null;

  const formatVal = (v) => {
    const n = typeof v === 'number' ? v : parseFloat(v);
    if (!isFinite(n)) return '0';
    if (Math.abs(n) < 1e-12) return '0';
    // Use 4 significant digits
    return parseFloat(n.toPrecision(4)).toString();
  };

  const rows = Array.isArray(matrix[0]) ? matrix : [matrix];

  const latex = `${label} = \\begin{bmatrix} ${rows
    .map(row => (Array.isArray(row) ? row : [row]).map(formatVal).join(' & '))
    .join(' \\\\ ')} \\end{bmatrix}`;

  return (
    <div className="ss-matrix-display">
      <LaTeX math={latex} display={false} />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Derivation step card
// ---------------------------------------------------------------------------
function DerivationStep({ step, index, isExpanded, onToggle }) {
  const btnId = `ss-step-btn-${index}`;
  const panelId = `ss-step-panel-${index}`;
  // P4: Call onToggle(index) so parent's useCallback(toggleStep) isn't wrapped in an
  // inline arrow at the call site (enables future React.memo optimisation).
  const handleToggle = useCallback(() => onToggle(index), [onToggle, index]);
  return (
    <div className={`ss-step-card ${isExpanded ? 'expanded' : ''}`}>
      <button
        id={btnId}
        className="ss-step-header"
        onClick={handleToggle}
        aria-expanded={isExpanded}
        aria-controls={panelId}
      >
        <span className="ss-step-title">{step.title}</span>
        <span className="ss-step-chevron" aria-hidden="true">{isExpanded ? '▾' : '▸'}</span>
      </button>
      {isExpanded && (
        <div id={panelId} role="region" aria-labelledby={btnId} className="ss-step-body">
          <div className="ss-step-latex">
            <LaTeX math={step.latex} display={true} />
          </div>
          {step.explanation && (
            <p className="ss-step-explanation">{step.explanation}</p>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Eigenvalue badge row
// ---------------------------------------------------------------------------
function EigenvalueBadges({ eigenvalues }) {
  const reals = eigenvalues?.real ?? [];
  const imags = eigenvalues?.imag ?? [];
  if (!reals.length) return null;

  return (
    <div className="ss-eigenvalue-row">
      {reals.map((r, i) => {
        const im = imags[i] ?? 0;
        const stable = r < -1e-10;
        const label =
          Math.abs(im) < 1e-10
            ? `λ = ${r.toFixed(3)}`
            : im > 0
            ? `λ = ${r.toFixed(3)} + ${im.toFixed(3)}j`
            : `λ = ${r.toFixed(3)} − ${Math.abs(im).toFixed(3)}j`;
        // P5: Stable key from value — avoids stale badge styles when eigenvalue count changes
        const key = `${r.toFixed(6)}_${im.toFixed(6)}`;
        return (
          <span key={key} className={`ss-eigenvalue-badge ${stable ? 'stable' : 'unstable'}`}>
            {label}
          </span>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Plotly wrapper
// ---------------------------------------------------------------------------
function SSPlot({ plotData, isDark }) {
  const config = useMemo(() => ({
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    displaylogo: false,
    toImageButtonOptions: { format: 'png', scale: 2 },
  }), []);

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
    <div className="ss-plot-wrapper">
      <div className="ss-plot-title">{plotData.title}</div>
      <Plot
        data={plotData.data || []}
        layout={layout}
        config={config}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main StateSpaceViewer
// ---------------------------------------------------------------------------
export default function StateSpaceViewer({ metadata, plots, onButtonClick, isUpdating }) {
  const isDark = useTheme();

  const systemType = metadata?.system_type ?? 'linear_tf';
  const presetName = metadata?.preset_name ?? '';
  const latexSteps = metadata?.latex_steps ?? [];
  const fingerprint = `${systemType}-${presetName}-${latexSteps.length}`;
  const matrices = metadata?.matrices ?? {};
  const eigenvalues = metadata?.eigenvalues ?? { real: [], imag: [] };
  const isStable = metadata?.is_stable;
  const isMarginal = metadata?.is_marginal ?? false;
  const equilibriumPts = metadata?.equilibrium_points ?? [];
  const selEqIdx = metadata?.selected_eq_idx ?? 0;
  const systemOrder = metadata?.system_order ?? 0;
  const errorMsg = metadata?.error;

  // Track step expansion using an object keyed by step index.
  // We expand ALL steps by default whenever the step list changes.
  const [expandedSteps, setExpandedSteps] = useState({});
  const prevStepCountRef = useRef(0);

  useEffect(() => {
    if (latexSteps.length > 0 && latexSteps.length !== prevStepCountRef.current) {
      prevStepCountRef.current = latexSteps.length;
      const expanded = {};
      latexSteps.forEach((_, i) => { expanded[i] = true; });
      setExpandedSteps(expanded);
    }
  }, [latexSteps.length]);

  const toggleStep = useCallback((i) => {
    setExpandedSteps(prev => ({ ...prev, [i]: !prev[i] }));
  }, []);
  const expandAll = useCallback(() => {
    const expanded = {};
    latexSteps.forEach((_, i) => { expanded[i] = true; });
    setExpandedSteps(expanded);
  }, [latexSteps]);
  const collapseAll = useCallback(() => setExpandedSteps({}), []);

  const handleCompute = useCallback(() => {
    if (onButtonClick) onButtonClick('compute', {});
  }, [onButtonClick]);

  // P6: Memoize found plots so SSPlot's useMemo(layout) doesn't re-fire on every parent render.
  // plots array reference itself changes per API response; stabilise the individual objects.
  const eigenPlot = useMemo(
    () => plots?.find(p => p.id === 'eigenvalue_map') ?? null,
    [plots]
  );
  const secondPlot = useMemo(
    () => plots?.find(p => p.id === 'step_response' || p.id === 'phase_portrait') ?? null,
    [plots]
  );

  // Stability badge — distinguish marginal from unstable
  const stabilityBadge =
    isStable === true  ? { label: 'Asympt. Stable', cls: 'stable' } :
    isMarginal         ? { label: 'Marginally Stable', cls: 'marginal' } :
    isStable === false ? { label: 'Unstable', cls: 'unstable' } :
    { label: 'Unknown', cls: 'unknown' };

  return (
    <div className="ss-viewer">
      {/* Header row */}
      <div className="ss-header">
        <div className="ss-header-left">
          {presetName && <span className="ss-preset-badge">{presetName}</span>}
          <span className={`ss-stability-badge ${stabilityBadge.cls}`}>
            {stabilityBadge.label}
          </span>
          {systemOrder > 0 && (
            <span className="ss-order-badge">Order {systemOrder}</span>
          )}
          <span className="ss-type-badge">
            {systemType === 'nonlinear' ? 'Nonlinear → Linearized' : 'Linear TF'}
          </span>
        </div>
        <div className="ss-header-right">
          <button
            className="ss-compute-btn"
            onClick={handleCompute}
            disabled={isUpdating}
            aria-label="Re-compute state-space matrices"
          >
            {isUpdating ? 'Computing…' : 'Compute System'}
          </button>
        </div>
      </div>

      {/* Error banner */}
      {errorMsg && (
        <div className="ss-error-banner" role="alert">
          <span className="ss-error-icon">⚠</span>
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Equilibrium info (nonlinear only) */}
      {systemType === 'nonlinear' && equilibriumPts.length > 0 && (
        <div className="ss-eq-info">
          <span className="ss-eq-label">Equilibria found:</span>
          {equilibriumPts.map(([x1, x2], i) => (
            <span
              key={`${x1.toFixed(6)}_${x2.toFixed(6)}`}
              className={`ss-eq-badge ${i === selEqIdx ? 'selected' : ''}`}
            >
              #{i + 1} ({x1.toFixed(3)}, {x2.toFixed(3)})
            </span>
          ))}
        </div>
      )}

      {/* Eigenvalue badges */}
      <EigenvalueBadges eigenvalues={eigenvalues} />

      {/* Main two-column layout */}
      <div className="ss-main-layout">
        {/* Left: derivation panel */}
        <div className="ss-derivation-panel">
          <div className="ss-panel-header">
            <h3 className="ss-panel-title">Step-by-Step Derivation</h3>
            <div className="ss-panel-actions">
              <button className="ss-text-btn" onClick={expandAll}>Expand all</button>
              <span className="ss-divider" aria-hidden="true">|</span>
              <button className="ss-text-btn" onClick={collapseAll}>Collapse all</button>
            </div>
          </div>

          {/* A B C D matrix summary at top */}
          {matrices.A && (
            <div className="ss-matrix-summary">
              <div className="ss-matrix-summary-title">State-Space Matrices</div>
              <div className="ss-matrix-grid">
                {matrices.A && <MatrixDisplay label="A" matrix={matrices.A} isDark={isDark} />}
                {matrices.B && <MatrixDisplay label="B" matrix={matrices.B} isDark={isDark} />}
                {matrices.C && <MatrixDisplay label="C" matrix={matrices.C} isDark={isDark} />}
                {matrices.D && (
                  <div className="ss-matrix-display">
                    <LaTeX
                      math={`D = ${
                        Array.isArray(matrices.D[0])
                          ? parseFloat(matrices.D[0][0].toPrecision(4)).toString()
                          : parseFloat(matrices.D[0].toPrecision(4)).toString()
                      }`}
                      display={false}
                    />
                  </div>
                )}
              </div>

              {/* Core equations — double backslashes required in JS string literals */}
              <div className="ss-core-equations">
                <div className="ss-core-eq">
                  <LaTeX math={"\\dot{\\mathbf{x}} = A\\mathbf{x} + Bu"} display={true} />
                </div>
                <div className="ss-core-eq">
                  <LaTeX math={"y = C\\mathbf{x} + Du"} display={true} />
                </div>
              </div>
            </div>
          )}

          {/* Derivation steps */}
          <div className="ss-steps-list">
            {latexSteps.length === 0 && !errorMsg && (
              <div className="ss-empty-state">
                Adjust parameters to compute the state-space representation.
              </div>
            )}
            {latexSteps.map((step, i) => (
              <DerivationStep
                key={`${fingerprint}-step-${i}`}
                step={step}
                index={i}
                isExpanded={expandedSteps[i] ?? false}
                onToggle={toggleStep}
              />
            ))}
          </div>
        </div>

        {/* Right: plots panel */}
        <div className="ss-plots-panel">
          {eigenPlot && <SSPlot plotData={eigenPlot} isDark={isDark} />}
          {secondPlot && <SSPlot plotData={secondPlot} isDark={isDark} />}
          {!eigenPlot && !secondPlot && !errorMsg && (
            <div className="ss-empty-state">Plots will appear here after computation.</div>
          )}
        </div>
      </div>
    </div>
  );
}
