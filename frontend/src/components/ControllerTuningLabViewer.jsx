import React, { useState, useCallback, useMemo, useRef, useEffect, memo } from 'react';
import Plot from 'react-plotly.js';
import '../styles/ControllerTuningLab.css';

// ============================================================================
// KaTeX rendering helper (same pattern as BlockDiagramViewer)
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

function renderLatex(latex) {
  if (!katexModule || !latex) return latex || '';
  try {
    return katexModule.renderToString(latex, { throwOnError: false, displayMode: false });
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
// FeedbackLoopDiagram (SVG with KaTeX transfer functions)
// ============================================================================

const MODERN_CONTROLLERS = ['state_feedback', 'pole_placement', 'lqr'];

const FeedbackLoopDiagram = memo(function FeedbackLoopDiagram({ metadata }) {
  const [katexReady, setKatexReady] = useState(!!katexModule);

  useEffect(() => {
    loadKatex(() => setKatexReady(true));
  }, []);

  const plantLabel = metadata?.tf_strings?.plant_tf_latex || 'G(s)';
  const ctrlLabel = metadata?.tf_strings?.controller_tf_latex || 'C(s)';
  const isStateFeedback = MODERN_CONTROLLERS.includes(
    metadata?.parameters?.controller_type || ''
  );

  const W = 700, H = 160;
  const sumX = 120, sumR = 18;
  const mainY = 55;
  const feedbackY = 130;

  if (isStateFeedback) {
    // State-feedback block diagram: R → Σ → Plant → Y, with K on feedback
    const plantX = 260, plantW = 160, plantH = 50;
    const kX = 260, kW = 140, kH = 40;
    const outX = 520;
    const takeoffX = plantX + plantW + 30;
    const kLabel = metadata?.state_feedback_K_str || 'K';

    return (
      <div className="ctl-block-diagram">
        <svg viewBox={`0 0 ${W} ${H}`} width="100%" preserveAspectRatio="xMidYMid meet">
          <defs>
            <marker id="ctl-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill="var(--accent-color, #00d9ff)" />
            </marker>
          </defs>

          {/* r(t) input */}
          <line x1={30} y1={mainY} x2={sumX - sumR} y2={mainY}
            stroke="var(--accent-color, #00d9ff)" strokeWidth={2} markerEnd="url(#ctl-arrow)" />
          <text x={15} y={mainY - 10} className="ctl-signal-label">r(t)</text>

          {/* Summing junction */}
          <circle cx={sumX} cy={mainY} r={sumR} fill="none"
            stroke="var(--accent-color, #00d9ff)" strokeWidth={1.5} />
          <text x={sumX} y={mainY + 1} textAnchor="middle" dominantBaseline="middle"
            className="ctl-sum-label">{'\u03A3'}</text>
          <text x={sumX - sumR - 5} y={mainY + sumR + 2} className="ctl-sign-label">{'\u2212'}</text>

          {/* u(t) arrow to plant */}
          <line x1={sumX + sumR} y1={mainY} x2={plantX} y2={mainY}
            stroke="var(--accent-color, #00d9ff)" strokeWidth={2} markerEnd="url(#ctl-arrow)" />
          <text x={(sumX + sumR + plantX) / 2} y={mainY - 10} textAnchor="middle"
            className="ctl-signal-label">u = r{'\u2212'}Kx</text>

          {/* Plant block */}
          <rect x={plantX} y={mainY - plantH / 2} width={plantW} height={plantH}
            rx={6} className="ctl-tf-block" />
          {katexReady ? (
            <foreignObject x={plantX + 4} y={mainY - plantH / 2 + 2} width={plantW - 8} height={plantH - 4}>
              <div xmlns="http://www.w3.org/1999/xhtml" className="ctl-katex-container"
                dangerouslySetInnerHTML={{ __html: renderLatex(plantLabel) }} />
            </foreignObject>
          ) : (
            <text x={plantX + plantW / 2} y={mainY + 4} textAnchor="middle"
              className="ctl-signal-label" fontSize="14">G(s)</text>
          )}

          {/* y(t) output */}
          <line x1={plantX + plantW} y1={mainY} x2={outX} y2={mainY}
            stroke="var(--accent-color, #00d9ff)" strokeWidth={2} markerEnd="url(#ctl-arrow)" />
          <text x={outX + 5} y={mainY - 10} className="ctl-signal-label">y(t)</text>

          {/* Takeoff point */}
          <circle cx={takeoffX} cy={mainY} r={4} fill="var(--accent-color, #00d9ff)" />

          {/* Feedback path with K block */}
          <line x1={takeoffX} y1={mainY} x2={takeoffX} y2={feedbackY}
            stroke="var(--accent-color, #00d9ff)" strokeWidth={2} />
          <text x={takeoffX + 10} y={(mainY + feedbackY) / 2} className="ctl-signal-label"
            fontSize="10">x(t)</text>

          {/* K block on feedback */}
          <rect x={kX} y={feedbackY - kH / 2} width={kW} height={kH}
            rx={6} className="ctl-tf-block ctl-sf-block" />
          <text x={kX + kW / 2} y={feedbackY + 4} textAnchor="middle"
            className="ctl-signal-label" fontSize="11">{kLabel}</text>

          {/* Lines: takeoff → K block → summing junction */}
          <line x1={takeoffX} y1={feedbackY} x2={kX + kW} y2={feedbackY}
            stroke="var(--accent-color, #00d9ff)" strokeWidth={2} markerEnd="url(#ctl-arrow)" />
          <line x1={kX} y1={feedbackY} x2={sumX} y2={feedbackY}
            stroke="var(--accent-color, #00d9ff)" strokeWidth={2} />
          <line x1={sumX} y1={feedbackY} x2={sumX} y2={mainY + sumR}
            stroke="var(--accent-color, #00d9ff)" strokeWidth={2} markerEnd="url(#ctl-arrow)" />
        </svg>
      </div>
    );
  }

  // Classical controller block diagram
  const ctrlX = 210, ctrlW = 140, ctrlH = 50;
  const plantX = 410, plantW = 140, plantH = 50;
  const outX = 620;
  const takeoffX = plantX + plantW + 30;

  return (
    <div className="ctl-block-diagram">
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" preserveAspectRatio="xMidYMid meet">
        <defs>
          <marker id="ctl-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="var(--accent-color, #00d9ff)" />
          </marker>
        </defs>

        {/* R(s) input */}
        <line x1={30} y1={mainY} x2={sumX - sumR} y2={mainY}
          stroke="var(--accent-color, #00d9ff)" strokeWidth={2} markerEnd="url(#ctl-arrow)" />
        <text x={15} y={mainY - 10} className="ctl-signal-label">R(s)</text>

        {/* Summing junction */}
        <circle cx={sumX} cy={mainY} r={sumR} fill="none"
          stroke="var(--accent-color, #00d9ff)" strokeWidth={1.5} />
        <text x={sumX} y={mainY + 1} textAnchor="middle" dominantBaseline="middle"
          className="ctl-sum-label">{'\u03A3'}</text>
        <text x={sumX - sumR - 5} y={mainY + sumR + 2} className="ctl-sign-label">{'\u2212'}</text>

        {/* E(s) arrow */}
        <line x1={sumX + sumR} y1={mainY} x2={ctrlX} y2={mainY}
          stroke="var(--accent-color, #00d9ff)" strokeWidth={2} markerEnd="url(#ctl-arrow)" />
        <text x={(sumX + sumR + ctrlX) / 2} y={mainY - 10} textAnchor="middle" className="ctl-signal-label">E(s)</text>

        {/* Controller block */}
        <rect x={ctrlX} y={mainY - ctrlH / 2} width={ctrlW} height={ctrlH}
          rx={6} className="ctl-tf-block" />
        {katexReady ? (
          <foreignObject x={ctrlX + 4} y={mainY - ctrlH / 2 + 2} width={ctrlW - 8} height={ctrlH - 4}>
            <div xmlns="http://www.w3.org/1999/xhtml" className="ctl-katex-container"
              dangerouslySetInnerHTML={{ __html: renderLatex(ctrlLabel) }} />
          </foreignObject>
        ) : (
          <text x={ctrlX + ctrlW / 2} y={mainY + 4} textAnchor="middle"
            className="ctl-signal-label" fontSize="14">C(s)</text>
        )}

        {/* U(s) arrow */}
        <line x1={ctrlX + ctrlW} y1={mainY} x2={plantX} y2={mainY}
          stroke="var(--accent-color, #00d9ff)" strokeWidth={2} markerEnd="url(#ctl-arrow)" />
        <text x={(ctrlX + ctrlW + plantX) / 2} y={mainY - 10} textAnchor="middle" className="ctl-signal-label">U(s)</text>

        {/* Plant block */}
        <rect x={plantX} y={mainY - plantH / 2} width={plantW} height={plantH}
          rx={6} className="ctl-tf-block" />
        {katexReady ? (
          <foreignObject x={plantX + 4} y={mainY - plantH / 2 + 2} width={plantW - 8} height={plantH - 4}>
            <div xmlns="http://www.w3.org/1999/xhtml" className="ctl-katex-container"
              dangerouslySetInnerHTML={{ __html: renderLatex(plantLabel) }} />
          </foreignObject>
        ) : (
          <text x={plantX + plantW / 2} y={mainY + 4} textAnchor="middle"
            className="ctl-signal-label" fontSize="14">G(s)</text>
        )}

        {/* Y(s) output */}
        <line x1={plantX + plantW} y1={mainY} x2={outX} y2={mainY}
          stroke="var(--accent-color, #00d9ff)" strokeWidth={2} markerEnd="url(#ctl-arrow)" />
        <text x={outX + 5} y={mainY - 10} className="ctl-signal-label">Y(s)</text>

        {/* Takeoff point */}
        <circle cx={takeoffX} cy={mainY} r={4} fill="var(--accent-color, #00d9ff)" />

        {/* Feedback path */}
        <polyline
          points={`${takeoffX},${mainY} ${takeoffX},${feedbackY} ${sumX},${feedbackY} ${sumX},${mainY + sumR}`}
          fill="none" stroke="var(--accent-color, #00d9ff)" strokeWidth={2}
          markerEnd="url(#ctl-arrow)" />
        <text x={(takeoffX + sumX) / 2} y={feedbackY - 8}
          textAnchor="middle" className="ctl-signal-label">H(s) = 1</text>
      </svg>
    </div>
  );
});

// ============================================================================
// StateSpaceDisplay (KaTeX-rendered A, B, C, D matrices)
// ============================================================================

function StateSpaceDisplay({ metadata }) {
  const [katexReady, setKatexReady] = useState(!!katexModule);

  useEffect(() => {
    loadKatex(() => setKatexReady(true));
  }, []);

  const ssMatrices = metadata?.ss_matrices;
  if (!katexReady || !ssMatrices) return null;

  const matToLatex = (mat) => {
    const rows = mat.map(row =>
      row.map(v => {
        const val = typeof v === 'number' ? v : parseFloat(v);
        return Math.abs(val) < 1e-10 ? '0' : val.toFixed(3).replace(/\.?0+$/, '');
      }).join(' & ')
    ).join(' \\\\ ');
    return `\\begin{bmatrix} ${rows} \\end{bmatrix}`;
  };

  const A_latex = matToLatex(ssMatrices.A);
  const B_latex = matToLatex(ssMatrices.B);
  const C_latex = matToLatex(ssMatrices.C);
  const D_latex = matToLatex(ssMatrices.D);

  const eq1 = `\\dot{\\mathbf{x}} = ${A_latex} \\mathbf{x} + ${B_latex} u`;
  const eq2 = `y = ${C_latex} \\mathbf{x} + ${D_latex} u`;

  return (
    <div className="ctl-ss-display">
      <div className="ctl-ss-equation"
        dangerouslySetInnerHTML={{ __html: renderLatex(eq1) }} />
      <div className="ctl-ss-equation"
        dangerouslySetInnerHTML={{ __html: renderLatex(eq2) }} />
    </div>
  );
}

// ============================================================================
// PerformanceMetricsStrip
// ============================================================================

function PerformanceMetricsStrip({ metrics, metadata }) {
  if (!metrics) return null;

  const isModern = MODERN_CONTROLLERS.includes(
    metadata?.parameters?.controller_type || ''
  );

  const items = [
    { label: 't\u1D63', value: metrics.rise_time, unit: 's', fmt: 3 },
    { label: 't\u209B', value: metrics.settling_time, unit: 's', fmt: 3 },
    { label: 'Mp', value: metrics.overshoot_pct, unit: '%', fmt: 1 },
    { label: 'e\u209B\u209B', value: metrics.steady_state_error, unit: '', fmt: 4 },
    { label: 'GM', value: metrics.gain_margin_db, unit: ' dB', fmt: 1 },
    { label: 'PM', value: metrics.phase_margin_deg, unit: '\u00b0', fmt: 1 },
    { label: 'BW', value: metrics.bandwidth, unit: ' rad/s', fmt: 1 },
  ];

  const stabilityColor = metrics.is_stable ? 'var(--success-color)' :
    metrics.stability_class === 'Marginally Stable' ? 'var(--warning-color)' : 'var(--error-color)';

  return (
    <div className="ctl-metrics-strip">
      {items.map(item => (
        <div key={item.label} className="ctl-metric-badge">
          <span className="ctl-metric-label">{item.label}</span>
          <span className="ctl-metric-value">
            {item.value != null ? item.value.toFixed(item.fmt) : '\u2014'}{item.value != null ? item.unit : ''}
          </span>
        </div>
      ))}
      <div className="ctl-metric-badge ctl-stability-badge" style={{ borderColor: stabilityColor }}>
        <span className="ctl-metric-label">Status</span>
        <span className="ctl-metric-value" style={{ color: stabilityColor }}>
          {metrics.stability_class || 'Unknown'}
        </span>
      </div>
      {isModern && (
        <div className="ctl-metric-badge" style={{
          borderColor: metadata?.is_controllable ? 'var(--success-color)' : 'var(--error-color)'
        }}>
          <span className="ctl-metric-label">Ctrb</span>
          <span className="ctl-metric-value" style={{
            color: metadata?.is_controllable ? 'var(--success-color)' : 'var(--error-color)'
          }}>
            {metadata?.is_controllable ? 'Yes' : 'No'}
          </span>
        </div>
      )}
      {isModern && metadata?.plant_order && (
        <div className="ctl-metric-badge">
          <span className="ctl-metric-label">Order</span>
          <span className="ctl-metric-value">{metadata.plant_order}</span>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// TuningInfoBanner
// ============================================================================

function TuningInfoBanner({ tuningInfo }) {
  if (!tuningInfo) return null;
  return (
    <div className="ctl-tuning-banner">
      <span>{'\u26a1'}</span>
      <span>{tuningInfo}</span>
    </div>
  );
}

// ============================================================================
// TuningPlot (Plotly wrapper with theme)
// ============================================================================

const TuningPlot = memo(function TuningPlot({ plot, height = 300, compact = false }) {
  const isDark = useIsDark();

  const layout = useMemo(() => {
    const plotXaxis = plot.layout?.xaxis || {};
    const plotYaxis = plot.layout?.yaxis || {};
    const margins = compact
      ? { t: 36, r: 16, b: 44, l: 52 }
      : { t: 40, r: 20, b: 50, l: 56 };

    return {
      ...(plot.layout || {}),
      title: {
        text: plot.title,
        font: { size: compact ? 13 : 14, color: isDark ? '#f1f5f9' : '#1e293b' },
        y: 0.98, yanchor: 'top',
      },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: isDark ? 'rgba(19,27,46,0.6)' : 'rgba(248,250,252,0.8)',
      font: { family: 'Inter, sans-serif', size: compact ? 11 : 12, color: isDark ? '#94a3b8' : '#64748b' },
      xaxis: {
        ...plotXaxis,
        autorange: plotXaxis.range ? undefined : true,
        gridcolor: isDark ? 'rgba(148,163,184,0.08)' : 'rgba(148,163,184,0.15)',
        zerolinecolor: isDark ? 'rgba(148,163,184,0.2)' : 'rgba(148,163,184,0.3)',
        title: { ...((typeof plotXaxis.title === 'string') ? { text: plotXaxis.title } : (plotXaxis.title || {})), font: { size: compact ? 11 : 12 } },
      },
      yaxis: {
        ...plotYaxis,
        autorange: plotYaxis.range ? undefined : true,
        gridcolor: isDark ? 'rgba(148,163,184,0.08)' : 'rgba(148,163,184,0.15)',
        zerolinecolor: isDark ? 'rgba(148,163,184,0.2)' : 'rgba(148,163,184,0.3)',
        title: { ...((typeof plotYaxis.title === 'string') ? { text: plotYaxis.title } : (plotYaxis.title || {})), font: { size: compact ? 11 : 12 } },
      },
      margin: margins,
      height,
      autosize: true,
      datarevision: `${plot.id}-${Date.now()}`,
      uirevision: plot.id,
      legend: {
        font: { size: compact ? 10 : 11 },
        bgcolor: 'rgba(0,0,0,0)',
        orientation: compact ? 'h' : 'v',
        ...(compact ? { y: -0.18, x: 0.5, xanchor: 'center' } : {}),
      },
      annotations: plot.layout?.annotations || [],
    };
  }, [plot, isDark, height, compact]);

  const config = useMemo(() => ({
    responsive: true,
    displayModeBar: 'hover',
    displaylogo: false,
    modeBarButtonsToRemove: ['select2d', 'lasso2d'],
  }), []);

  return (
    <div className="ctl-plot-card">
      <Plot data={plot.data || []} layout={layout} config={config}
        style={{ width: '100%', height: `${height}px` }}
        useResizeHandler={true} />
    </div>
  );
});

// ============================================================================
// ComparisonOverlay (fullscreen)
// ============================================================================

const COMPARE_COLORS = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899'];

const METRIC_LABELS = {
  rise_time: 'Rise Time (s)',
  settling_time: 'Settling Time (s)',
  overshoot_pct: 'Overshoot (%)',
  steady_state_error: 'SS Error',
  gain_margin_db: 'GM (dB)',
  phase_margin_deg: 'PM (\u00b0)',
  ise: 'ISE',
  iae: 'IAE',
  itae: 'ITAE',
};

function ComparisonOverlay({ references, currentStepPlot, currentMetrics, currentLabel, onClose }) {
  const isDark = useIsDark();

  // Build list of all responses: current + references
  const allResponses = useMemo(() => {
    const current = currentStepPlot?.data?.[0]
      ? { t: currentStepPlot.data[0].x, y: currentStepPlot.data[0].y, label: currentLabel, isCurrent: true, metrics: currentMetrics }
      : null;
    const refs = (references || []).map(r => ({ t: r.t, y: r.y, label: r.label, isCurrent: false, metrics: null }));
    return current ? [current, ...refs] : refs;
  }, [references, currentStepPlot, currentLabel, currentMetrics]);

  const overlapPlotData = allResponses.map((resp, i) => ({
    x: resp.t, y: resp.y, type: 'scatter', mode: 'lines',
    name: resp.label || `Response ${i + 1}`,
    line: {
      color: COMPARE_COLORS[i % COMPARE_COLORS.length],
      width: resp.isCurrent ? 3 : 2,
      dash: resp.isCurrent ? 'solid' : 'dash',
    },
  }));

  const overlapLayout = {
    title: { text: 'Step Response Comparison', font: { size: 16, color: isDark ? '#f1f5f9' : '#1e293b' } },
    paper_bgcolor: isDark ? '#0a0e27' : 'rgba(255,255,255,0.98)',
    plot_bgcolor: isDark ? '#131b2e' : '#f8fafc',
    font: { family: 'Inter, sans-serif', size: 12, color: isDark ? '#94a3b8' : '#64748b' },
    xaxis: { title: 'Time (s)', gridcolor: 'rgba(148,163,184,0.1)' },
    yaxis: { title: 'Amplitude', gridcolor: 'rgba(148,163,184,0.1)' },
    height: 450,
    margin: { t: 50, r: 25, b: 55, l: 60 },
    legend: { font: { size: 12 } },
  };

  const metricKeys = Object.keys(METRIC_LABELS);

  return (
    <div className="ctl-comparison-overlay">
      <div className="ctl-comparison-header">
        <h2>Controller Comparison</h2>
        <button onClick={onClose} className="ctl-comparison-close" aria-label="Close comparison overlay">{'\u2715'} Close</button>
      </div>
      <div className="ctl-comparison-content">
        <div className="ctl-comparison-plot">
          <Plot data={overlapPlotData} layout={overlapLayout}
            config={{ responsive: true, displayModeBar: true, displaylogo: false }}
            style={{ width: '100%', height: '450px' }} useResizeHandler={true} />
        </div>

        {/* Metrics comparison table */}
        {currentMetrics && (
          <div className="ctl-comparison-metrics-table">
            <table>
              <thead>
                <tr>
                  <th>Metric</th>
                  {allResponses.map((r, i) => (
                    <th key={i} style={{ color: COMPARE_COLORS[i % COMPARE_COLORS.length] }}>
                      {r.label || `#${i + 1}`}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {metricKeys.map(key => (
                  <tr key={key}>
                    <td style={{ textAlign: 'left', fontWeight: 600, color: 'var(--text-secondary)' }}>
                      {METRIC_LABELS[key]}
                    </td>
                    {allResponses.map((r, i) => (
                      <td key={i}>
                        {r.metrics?.[key] != null ? r.metrics[key].toFixed(3) : '\u2014'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// TrainingPanel (ES / Policy Gradient training UI)
// ============================================================================

const RL_METHODS = ['es_adaptive', 'ppo_rl'];

const TrainingPanel = memo(function TrainingPanel({ currentParams }) {
  const [status, setStatus] = useState('idle');
  const [progress, setProgress] = useState(null);
  const [error, setError] = useState(null);

  const method = currentParams?.tuning_method;
  const isES = method === 'es_adaptive';
  const isPG = method === 'ppo_rl';

  // Reset status when switching methods
  useEffect(() => {
    setStatus('idle');
    setProgress(null);
    setError(null);
  }, [method]);

  const startTraining = useCallback(async () => {
    setStatus('training');
    setError(null);
    const endpoint = isES
      ? '/api/simulations/controller_tuning_lab/es/train'
      : '/api/simulations/controller_tuning_lab/ppo/train';
    const body = isES
      ? { generations: currentParams?.es_generations || 200, pop_size: 50 }
      : { timesteps: currentParams?.rl_timesteps || 5000 };
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const data = await res.json();
        setError(data.error || 'Failed to start training');
        setStatus('error');
      }
    } catch (e) {
      setError(e.message);
      setStatus('error');
    }
  }, [isES, currentParams]);

  const cancelTraining = useCallback(async () => {
    if (!isPG) return;
    try {
      await fetch('/api/simulations/controller_tuning_lab/ppo/cancel', { method: 'POST' });
      setStatus('cancelled');
    } catch { /* ignore */ }
  }, [isPG]);

  // Poll status during training
  useEffect(() => {
    if (status !== 'training') return;
    const endpoint = isES
      ? '/api/simulations/controller_tuning_lab/es/status'
      : '/api/simulations/controller_tuning_lab/ppo/status';
    const interval = setInterval(async () => {
      try {
        const res = await fetch(endpoint);
        const data = await res.json();
        const st = data.data;
        setProgress(st);
        if (st?.state === 'complete') setStatus('complete');
        if (st?.state === 'error') {
          setStatus('error');
          setError(st.error || 'Training failed');
        }
        if (st?.state === 'cancelled') setStatus('cancelled');
      } catch { /* ignore poll errors */ }
    }, 2000);
    return () => clearInterval(interval);
  }, [status, isES]);

  if (!RL_METHODS.includes(method)) return null;

  const methodLabel = isES ? 'Evolution Strategies' : 'Actor-Critic RL (A2C)';
  const trainLabel = isES ? 'Train ES Policy' : 'Train A2C Agent';

  return (
    <div className="ctl-training-panel">
      <div className="ctl-training-header">
        <span className={`ctl-training-status ctl-training-status--${status}`} />
        <span>{methodLabel}</span>
      </div>

      {(status === 'idle' || status === 'complete' || status === 'cancelled' || status === 'error') && (
        <button className="ctl-compare-btn" onClick={startTraining}
          style={status === 'complete' ? { opacity: 0.75 } : {}}>
          {status === 'complete' || status === 'cancelled' || status === 'error'
            ? `Re-train ${isES ? 'ES' : 'PG'}`
            : trainLabel}
        </button>
      )}

      {status === 'training' && (
        <div className="ctl-training-progress">
          {progress ? (
            <>
              <div className="ctl-progress-bar">
                <div className="ctl-progress-fill"
                  style={{ width: `${progress.progress_pct || 0}%` }} />
              </div>
              <div className="ctl-training-metrics">
                <span>{isES
                  ? `Gen ${progress.generation || 0}/${progress.total_generations || '?'}`
                  : `Ep ${progress.timestep || 0}/${progress.total_timesteps || '?'}`}</span>
                <span>Best: {(progress.best_fitness ?? progress.reward_mean ?? 0).toFixed(2)}</span>
                <span>{(progress.progress_pct || 0).toFixed(0)}%</span>
              </div>
            </>
          ) : (
            <div className="ctl-training-metrics"><span>Starting...</span></div>
          )}
          {isPG && (
            <button className="ctl-compare-btn" onClick={cancelTraining}
              style={{ marginTop: 8, background: 'var(--error-color)' }}>
              Cancel Training
            </button>
          )}
        </div>
      )}

      {status === 'complete' && (
        <div className="ctl-training-complete">
          Training complete — click "Apply Auto-Tune" to use the model.
        </div>
      )}

      {status === 'cancelled' && (
        <div className="ctl-training-error">Training cancelled.</div>
      )}

      {status === 'error' && (
        <div className="ctl-training-error">{error || 'Training failed. Check server logs.'}</div>
      )}
    </div>
  );
});

// ============================================================================
// Main Component: ControllerTuningLabViewer
// ============================================================================

// Plot pair definitions for 2-column grid layout
const PLOT_PAIRS = [
  // Hero plot: step response (full width)
  { type: 'hero', ids: ['step_response'], height: 340 },
  // Bode pair
  { type: 'pair', ids: ['bode_magnitude', 'bode_phase'], height: 260, label: 'Frequency Response' },
  // Pole-zero + Nyquist
  { type: 'pair', ids: ['pole_zero_map', 'nyquist'], height: 280, label: 'Stability Analysis' },
  // Control effort + Error
  { type: 'pair', ids: ['control_effort', 'error_signal'], height: 240, label: 'Signals' },
];

function ControllerTuningLabViewer({ metadata, plots, currentParams }) {
  const [showComparison, setShowComparison] = useState(false);

  const performance = metadata?.performance;
  const tuningInfo = metadata?.tuning_info;
  const references = metadata?.reference_responses || [];

  const currentStepPlot = useMemo(() =>
    plots?.find(p => p.id === 'step_response'),
    [plots]
  );

  const currentLabel = useMemo(() => {
    const ctype = currentParams?.controller_type || 'PID';
    const method = currentParams?.tuning_method || 'manual';
    return `Current: ${ctype} (${method})`;
  }, [currentParams]);

  // Resolve plot pairs
  const resolvedPairs = useMemo(() =>
    PLOT_PAIRS.map(pair => ({
      ...pair,
      plots: pair.ids.map(id => plots?.find(p => p.id === id)).filter(Boolean),
    })).filter(pair => pair.plots.length > 0),
    [plots]
  );

  return (
    <div className="ctl-viewer">
      {/* Block Diagram */}
      <FeedbackLoopDiagram metadata={metadata} />

      {/* State-space matrices (modern controllers only) */}
      <StateSpaceDisplay metadata={metadata} />

      {/* Performance Metrics Strip */}
      <PerformanceMetricsStrip metrics={performance} metadata={metadata} />

      {/* Tuning Info Banner */}
      <TuningInfoBanner tuningInfo={tuningInfo} />

      {/* RL Training Panel (ES/PPO) */}
      <TrainingPanel currentParams={currentParams} />

      {/* Plot sections */}
      <div className="ctl-plot-stack">
        {resolvedPairs.map((pair, idx) => (
          <div key={idx} className={pair.type === 'hero' ? 'ctl-plot-hero' : 'ctl-plot-section'}>
            {pair.label && (
              <div className="ctl-section-label">{pair.label}</div>
            )}
            <div className={pair.type === 'pair' ? 'ctl-plot-row' : ''}>
              {pair.plots.map(plot => (
                <TuningPlot
                  key={plot.id}
                  plot={plot}
                  height={pair.height}
                  compact={pair.type === 'pair'}
                />
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Compare Mode */}
      {references.length > 0 && (
        <button className="ctl-compare-btn" onClick={() => setShowComparison(true)}>
          Compare ({references.length} saved)
        </button>
      )}

      {showComparison && (
        <ComparisonOverlay
          references={references}
          currentStepPlot={currentStepPlot}
          currentMetrics={performance}
          currentLabel={currentLabel}
          onClose={() => setShowComparison(false)}
        />
      )}
    </div>
  );
}

export default memo(ControllerTuningLabViewer);
