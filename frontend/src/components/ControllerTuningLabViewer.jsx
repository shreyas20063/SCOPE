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

function FeedbackLoopDiagram({ metadata }) {
  const [katexReady, setKatexReady] = useState(!!katexModule);

  useEffect(() => {
    loadKatex(() => setKatexReady(true));
  }, []);

  const plantLabel = metadata?.tf_strings?.plant_tf_latex || 'G(s)';
  const ctrlLabel = metadata?.tf_strings?.controller_tf_latex || 'C(s)';

  const W = 700, H = 160;
  const sumX = 120, sumR = 18;
  const ctrlX = 210, ctrlW = 140, ctrlH = 50;
  const plantX = 410, plantW = 140, plantH = 50;
  const outX = 620;
  const feedbackY = 130;
  const mainY = 55;
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
}

// ============================================================================
// PerformanceMetricsStrip
// ============================================================================

function PerformanceMetricsStrip({ metrics }) {
  if (!metrics) return null;

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

const TuningPlot = memo(function TuningPlot({ plot, height = 300 }) {
  const isDark = useIsDark();

  const layout = useMemo(() => ({
    ...(plot.layout || {}),
    title: { text: plot.title, font: { size: 14, color: isDark ? '#f1f5f9' : '#1e293b' } },
    paper_bgcolor: isDark ? '#0a0e27' : 'rgba(255,255,255,0.98)',
    plot_bgcolor: isDark ? '#131b2e' : '#f8fafc',
    font: { family: 'Inter, sans-serif', size: 12, color: isDark ? '#94a3b8' : '#64748b' },
    xaxis: {
      ...(plot.layout?.xaxis || {}),
      gridcolor: 'rgba(148,163,184,0.1)',
      zerolinecolor: 'rgba(148,163,184,0.3)',
    },
    yaxis: {
      ...(plot.layout?.yaxis || {}),
      gridcolor: 'rgba(148,163,184,0.1)',
      zerolinecolor: 'rgba(148,163,184,0.3)',
    },
    margin: { t: 45, r: 25, b: 55, l: 60 },
    height,
    datarevision: `${plot.id}-${Date.now()}`,
    uirevision: plot.id,
    legend: { font: { size: 11 }, bgcolor: 'rgba(0,0,0,0)' },
    annotations: plot.layout?.annotations || [],
  }), [plot, isDark, height]);

  const config = useMemo(() => ({
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['select2d', 'lasso2d', 'autoScale2d'],
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
        <button onClick={onClose} className="ctl-comparison-close">{'\u2715'} Close</button>
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
// Main Component: ControllerTuningLabViewer
// ============================================================================

const PLOT_ORDER = [
  'step_response', 'bode_magnitude', 'bode_phase',
  'pole_zero_map', 'control_effort', 'error_signal', 'nyquist',
];

const PLOT_HEIGHTS = {
  step_response: 350,
  bode_magnitude: 250,
  bode_phase: 250,
  pole_zero_map: 300,
  control_effort: 250,
  error_signal: 250,
  nyquist: 300,
};

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

  const orderedPlots = useMemo(() =>
    PLOT_ORDER.map(id => plots?.find(p => p.id === id)).filter(Boolean),
    [plots]
  );

  return (
    <div className="ctl-viewer">
      {/* 1. Feedback Loop Block Diagram */}
      <FeedbackLoopDiagram metadata={metadata} />

      {/* 2. Performance Metrics Strip */}
      <PerformanceMetricsStrip metrics={performance} />

      {/* 3. Tuning Info Banner */}
      <TuningInfoBanner tuningInfo={tuningInfo} />

      {/* 4. All plots stacked vertically */}
      <div className="ctl-plot-stack">
        {orderedPlots.map(plot => (
          <TuningPlot key={plot.id} plot={plot} height={PLOT_HEIGHTS[plot.id] || 300} />
        ))}
      </div>

      {/* 5. Compare Mode Button */}
      {references.length > 0 && (
        <button className="ctl-compare-btn" onClick={() => setShowComparison(true)}>
          Compare ({references.length} saved)
        </button>
      )}

      {/* 6. Comparison Overlay */}
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
