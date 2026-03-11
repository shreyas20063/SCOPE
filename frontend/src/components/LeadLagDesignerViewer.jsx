import React, { useState, useMemo, useEffect, memo } from 'react';
import Plot from 'react-plotly.js';
import '../styles/LeadLagDesigner.css';

// ============================================================================
// KaTeX rendering helper
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
// Feedback Loop Block Diagram (SVG)
// ============================================================================

const BlockDiagram = memo(function BlockDiagram({ metadata }) {
  const [katexReady, setKatexReady] = useState(!!katexModule);

  useEffect(() => {
    loadKatex(() => setKatexReady(true));
  }, []);

  const plantLabel = metadata?.tf_labels?.plant_latex || 'G(s)';
  const compLabel = metadata?.tf_labels?.comp_latex || 'C(s)';

  const W = 700, H = 140;
  const sumX = 100, sumR = 16;
  const mainY = 45;
  const feedbackY = 115;
  const compX = 170, compW = 180, compH = 44;
  const plantX = 390, plantW = 150, plantH = 44;
  const outX = 600;
  const takeoffX = plantX + plantW + 25;

  return (
    <div className="lld-block-diagram">
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" preserveAspectRatio="xMidYMid meet">
        <defs>
          <marker id="lld-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="var(--accent-color, #00d9ff)" />
          </marker>
        </defs>

        {/* r(t) input */}
        <line x1={25} y1={mainY} x2={sumX - sumR} y2={mainY}
          stroke="var(--accent-color, #00d9ff)" strokeWidth={2} markerEnd="url(#lld-arrow)" />
        <text x={12} y={mainY - 10} className="lld-signal-label">R(s)</text>

        {/* Summing junction */}
        <circle cx={sumX} cy={mainY} r={sumR} fill="none"
          stroke="var(--accent-color, #00d9ff)" strokeWidth={1.5} />
        <text x={sumX} y={mainY + 1} textAnchor="middle" dominantBaseline="middle"
          className="lld-sum-label">{'\u03A3'}</text>
        <text x={sumX - sumR - 4} y={mainY + sumR + 4} className="lld-sign-label">{'\u2212'}</text>

        {/* e(t) to compensator */}
        <line x1={sumX + sumR} y1={mainY} x2={compX} y2={mainY}
          stroke="var(--accent-color, #00d9ff)" strokeWidth={2} markerEnd="url(#lld-arrow)" />
        <text x={(sumX + sumR + compX) / 2} y={mainY - 10} textAnchor="middle"
          className="lld-signal-label" fontSize="10">E(s)</text>

        {/* Compensator block */}
        <rect x={compX} y={mainY - compH / 2} width={compW} height={compH}
          rx={6} className="lld-tf-block" />
        {katexReady ? (
          <foreignObject x={compX + 4} y={mainY - compH / 2 + 2} width={compW - 8} height={compH - 4}>
            <div xmlns="http://www.w3.org/1999/xhtml" className="lld-katex-container"
              dangerouslySetInnerHTML={{ __html: renderLatex(compLabel) }} />
          </foreignObject>
        ) : (
          <text x={compX + compW / 2} y={mainY + 4} textAnchor="middle"
            className="lld-signal-label" fontSize="13">C(s)</text>
        )}

        {/* Compensator to plant */}
        <line x1={compX + compW} y1={mainY} x2={plantX} y2={mainY}
          stroke="var(--accent-color, #00d9ff)" strokeWidth={2} markerEnd="url(#lld-arrow)" />

        {/* Plant block */}
        <rect x={plantX} y={mainY - plantH / 2} width={plantW} height={plantH}
          rx={6} className="lld-tf-block" />
        {katexReady ? (
          <foreignObject x={plantX + 4} y={mainY - plantH / 2 + 2} width={plantW - 8} height={plantH - 4}>
            <div xmlns="http://www.w3.org/1999/xhtml" className="lld-katex-container"
              dangerouslySetInnerHTML={{ __html: renderLatex(plantLabel) }} />
          </foreignObject>
        ) : (
          <text x={plantX + plantW / 2} y={mainY + 4} textAnchor="middle"
            className="lld-signal-label" fontSize="13">G(s)</text>
        )}

        {/* y(t) output */}
        <line x1={plantX + plantW} y1={mainY} x2={outX} y2={mainY}
          stroke="var(--accent-color, #00d9ff)" strokeWidth={2} markerEnd="url(#lld-arrow)" />
        <text x={outX + 5} y={mainY - 10} className="lld-signal-label">Y(s)</text>

        {/* Takeoff point */}
        <circle cx={takeoffX} cy={mainY} r={4} fill="var(--accent-color, #00d9ff)" />

        {/* Feedback path */}
        <line x1={takeoffX} y1={mainY} x2={takeoffX} y2={feedbackY}
          stroke="var(--accent-color, #00d9ff)" strokeWidth={2} />
        <line x1={takeoffX} y1={feedbackY} x2={sumX} y2={feedbackY}
          stroke="var(--accent-color, #00d9ff)" strokeWidth={2} />
        <line x1={sumX} y1={feedbackY} x2={sumX} y2={mainY + sumR}
          stroke="var(--accent-color, #00d9ff)" strokeWidth={2} markerEnd="url(#lld-arrow)" />

        {/* Unity feedback label */}
        <text x={(takeoffX + sumX) / 2} y={feedbackY - 6} textAnchor="middle"
          className="lld-signal-label" fontSize="10">Unity Feedback</text>
      </svg>
    </div>
  );
});

// ============================================================================
// Design Info Panel
// ============================================================================

const DesignInfoPanel = memo(function DesignInfoPanel({ designInfo }) {
  const [katexReady, setKatexReady] = useState(!!katexModule);

  useEffect(() => {
    loadKatex(() => setKatexReady(true));
  }, []);

  if (!designInfo) return null;

  const lead = designInfo.lead;
  const lag = designInfo.lag;

  const renderVal = (v, unit = '') => {
    if (v == null || v === undefined) return '\u2014';
    return typeof v === 'number' ? `${v.toFixed(v < 0.1 ? 4 : 2)}${unit}` : `${v}${unit}`;
  };

  return (
    <div className="lld-design-info">
      {/* Lead section */}
      <div className={`lld-design-section lld-design-section--lead ${!lead ? 'lld-design-section--disabled' : ''}`}>
        <div className="lld-section-title">Lead Compensator</div>
        {lead ? (
          <>
            <div className="lld-design-row">
              <span className="lld-design-label">{'\u03b1'}</span>
              <span className="lld-design-value">{lead.alpha}</span>
            </div>
            <div className="lld-design-row">
              <span className="lld-design-label">{'\u03c6_max'}</span>
              <span className="lld-design-value" style={{ color: '#10b981' }}>
                {lead.phi_max.toFixed(1)}{'\u00b0'}
              </span>
            </div>
            <div className="lld-design-row">
              <span className="lld-design-label">{'\u03c9_m'}</span>
              <span className="lld-design-value">{renderVal(lead.wm, ' rad/s')}</span>
            </div>
            <div className="lld-design-row">
              <span className="lld-design-label">zero</span>
              <span className="lld-design-value">{renderVal(lead.wz, ' rad/s')}</span>
            </div>
            <div className="lld-design-row">
              <span className="lld-design-label">pole</span>
              <span className="lld-design-value">{renderVal(lead.wp, ' rad/s')}</span>
            </div>
            <div className="lld-design-row">
              <span className="lld-design-label">HF gain</span>
              <span className="lld-design-value">+{renderVal(lead.hf_gain_db, ' dB')}</span>
            </div>
          </>
        ) : (
          <div style={{ color: 'var(--text-muted)', fontSize: '11px', fontStyle: 'italic' }}>
            Disabled
          </div>
        )}
      </div>

      {/* Lag section */}
      <div className={`lld-design-section lld-design-section--lag ${!lag ? 'lld-design-section--disabled' : ''}`}>
        <div className="lld-section-title">Lag Compensator</div>
        {lag ? (
          <>
            <div className="lld-design-row">
              <span className="lld-design-label">{'\u03b2'}</span>
              <span className="lld-design-value">{lag.beta}</span>
            </div>
            <div className="lld-design-row">
              <span className="lld-design-label">{'\u03c6_lag'}</span>
              <span className="lld-design-value" style={{ color: '#ef4444' }}>
                {lag.phi_max_lag.toFixed(1)}{'\u00b0'}
              </span>
            </div>
            <div className="lld-design-row">
              <span className="lld-design-label">{'\u03c9_m'}</span>
              <span className="lld-design-value">{renderVal(lag.wm, ' rad/s')}</span>
            </div>
            <div className="lld-design-row">
              <span className="lld-design-label">zero</span>
              <span className="lld-design-value">{renderVal(lag.wz, ' rad/s')}</span>
            </div>
            <div className="lld-design-row">
              <span className="lld-design-label">pole</span>
              <span className="lld-design-value">{renderVal(lag.wp, ' rad/s')}</span>
            </div>
            <div className="lld-design-row">
              <span className="lld-design-label">LF boost</span>
              <span className="lld-design-value">+{renderVal(lag.lf_gain_boost_db, ' dB')}</span>
            </div>
          </>
        ) : (
          <div style={{ color: 'var(--text-muted)', fontSize: '11px', fontStyle: 'italic' }}>
            Disabled
          </div>
        )}
      </div>
    </div>
  );
});

// ============================================================================
// Metrics Strip
// ============================================================================

const MetricsStrip = memo(function MetricsStrip({ designInfo }) {
  if (!designInfo) return null;

  const stable = designInfo.cl_stable;
  const pm = designInfo.pm;
  const gm = designInfo.gm;
  const wgc = designInfo.wgc;
  const sm = designInfo.step_metrics || {};

  const fmt = (v, dec = 1, unit = '') => {
    if (v == null || v === undefined) return '\u2014';
    return `${typeof v === 'number' ? v.toFixed(dec) : v}${unit}`;
  };

  return (
    <div className="lld-metrics-strip">
      <div className={`lld-metric-badge lld-stability-badge`}
        style={{ borderColor: stable ? 'var(--success-color)' : 'var(--error-color)' }}>
        <span className="lld-metric-label">Status</span>
        <span className="lld-metric-value" style={{
          color: stable ? 'var(--success-color)' : 'var(--error-color)',
          fontSize: '12px'
        }}>
          {stable ? '\u2713 Stable' : '\u2717 Unstable'}
        </span>
      </div>
      <div className="lld-metric-badge">
        <span className="lld-metric-label">PM</span>
        <span className="lld-metric-value" style={{
          color: pm != null ? (pm >= 30 ? 'var(--success-color)' : pm >= 10 ? 'var(--warning-color)' : 'var(--error-color)') : 'var(--text-muted)'
        }}>
          {fmt(pm, 1, '\u00b0')}
        </span>
      </div>
      <div className="lld-metric-badge">
        <span className="lld-metric-label">GM</span>
        <span className="lld-metric-value" style={{
          color: gm != null ? (gm >= 6 ? 'var(--success-color)' : gm >= 2 ? 'var(--warning-color)' : 'var(--error-color)') : 'var(--text-muted)'
        }}>
          {fmt(gm, 1, ' dB')}
        </span>
      </div>
      <div className="lld-metric-badge">
        <span className="lld-metric-label">{'\u03c9gc'}</span>
        <span className="lld-metric-value">{fmt(wgc, 2, ' r/s')}</span>
      </div>
      <div className="lld-metric-badge">
        <span className="lld-metric-label">Rise</span>
        <span className="lld-metric-value">{fmt(sm.rise_time, 3, 's')}</span>
      </div>
      <div className="lld-metric-badge">
        <span className="lld-metric-label">OS%</span>
        <span className="lld-metric-value" style={{
          color: sm.overshoot != null ? (sm.overshoot <= 10 ? 'var(--success-color)' : sm.overshoot <= 25 ? 'var(--warning-color)' : 'var(--error-color)') : 'var(--text-muted)'
        }}>
          {fmt(sm.overshoot, 1, '%')}
        </span>
      </div>
      <div className="lld-metric-badge">
        <span className="lld-metric-label">Settle</span>
        <span className="lld-metric-value">{fmt(sm.settling_time, 3, 's')}</span>
      </div>
      <div className="lld-metric-badge">
        <span className="lld-metric-label">ess</span>
        <span className="lld-metric-value">{fmt(sm.ss_error, 4)}</span>
      </div>
    </div>
  );
});

// ============================================================================
// Main Viewer
// ============================================================================

function LeadLagDesignerViewer({ metadata, plots }) {
  const isDark = useIsDark();

  const designInfo = metadata?.design_info;

  // Find plots by ID
  const findPlot = (id) => plots?.find(p => p.id === id);
  const bodeMag = findPlot('bode_magnitude');
  const bodePhase = findPlot('bode_phase');
  const stepResp = findPlot('step_response');
  const pzMap = findPlot('pole_zero_map');
  const compPhase = findPlot('compensator_phase');
  const nichols = findPlot('nichols_chart');

  // Standard Plotly layout overrides for theme
  const themeLayout = useMemo(() => ({
    paper_bgcolor: isDark ? '#0a0e27' : 'rgba(255,255,255,0.98)',
    plot_bgcolor: isDark ? '#131b2e' : '#f8fafc',
    font: {
      family: 'Inter, sans-serif',
      size: 12,
      color: isDark ? '#f1f5f9' : '#1e293b',
    },
    xaxis: { gridcolor: isDark ? 'rgba(148,163,184,0.1)' : 'rgba(148,163,184,0.2)',
             zerolinecolor: isDark ? 'rgba(148,163,184,0.3)' : 'rgba(148,163,184,0.4)' },
    yaxis: { gridcolor: isDark ? 'rgba(148,163,184,0.1)' : 'rgba(148,163,184,0.2)',
             zerolinecolor: isDark ? 'rgba(148,163,184,0.3)' : 'rgba(148,163,184,0.4)' },
  }), [isDark]);

  const renderPlot = (plotData, height = 300) => {
    if (!plotData) return null;
    const layout = {
      ...plotData.layout,
      ...themeLayout,
      xaxis: { ...plotData.layout?.xaxis, ...themeLayout.xaxis },
      yaxis: { ...plotData.layout?.yaxis, ...themeLayout.yaxis },
      autosize: true,
      height,
      datarevision: `${plotData.id}-${Date.now()}`,
      uirevision: plotData.id,
    };
    return (
      <Plot
        data={plotData.data || []}
        layout={layout}
        config={{
          responsive: true,
          displayModeBar: true,
          modeBarButtonsToRemove: ['lasso2d', 'select2d'],
          displaylogo: false,
        }}
        useResizeHandler
        style={{ width: '100%', height: `${height}px` }}
      />
    );
  };

  return (
    <div className="lld-viewer">
      {/* Block Diagram */}
      <BlockDiagram metadata={metadata} />

      {/* Design Info Panel */}
      <DesignInfoPanel designInfo={designInfo} />

      {/* Metrics Strip */}
      <MetricsStrip designInfo={designInfo} />

      {/* Plot Grid: 3 rows × 2 cols */}
      <div className="lld-plot-stack">
        {/* Row 1: Bode */}
        <div className="lld-plot-section">
          <div className="lld-section-label">Frequency Response</div>
          <div className="lld-plot-row">
            <div className="lld-plot-card">{renderPlot(bodeMag, 280)}</div>
            <div className="lld-plot-card">{renderPlot(bodePhase, 280)}</div>
          </div>
        </div>

        {/* Row 2: Step + PZ */}
        <div className="lld-plot-section">
          <div className="lld-section-label">Time Domain & Poles</div>
          <div className="lld-plot-row">
            <div className="lld-plot-card">{renderPlot(stepResp, 280)}</div>
            <div className="lld-plot-card">{renderPlot(pzMap, 280)}</div>
          </div>
        </div>

        {/* Row 3: Comp Phase + Nichols */}
        <div className="lld-plot-section">
          <div className="lld-section-label">Compensator Analysis</div>
          <div className="lld-plot-row">
            <div className="lld-plot-card">{renderPlot(compPhase, 280)}</div>
            <div className="lld-plot-card">{renderPlot(nichols, 280)}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LeadLagDesignerViewer;
