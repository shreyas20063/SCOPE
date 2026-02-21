/**
 * ZTransformPropertiesViewer Component
 *
 * Custom viewer for the Z-Transform Properties Lab simulation.
 * Demonstrates linearity, time delay, multiply-by-n, and convolution
 * with split time-domain / z-domain panels and animated convolution.
 *
 * Animation is handled entirely on the frontend (no backend round-trips).
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import Plot from 'react-plotly.js';
import '../styles/ZTransformPropertiesViewer.css';

/* ── Theme hook ────────────────────────────────────────── */

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

/* ── Property Formula Badge ────────────────────────────── */

function PropertyFormulaBadge({ metadata }) {
  if (!metadata) return null;
  const formula = metadata.property_formula || '';
  const property = metadata.property || '';

  const propertyLabels = {
    linearity: 'Linearity',
    delay: 'Time Delay',
    multiply_n: 'Multiply by n',
    convolution: 'Convolution',
  };

  return (
    <div className="zt-formula-badge">
      <span className="zt-formula-label">{propertyLabels[property] || property}</span>
      <span className="zt-formula-text">{formula}</span>
    </div>
  );
}

/* ── Signal Info Cards ─────────────────────────────────── */

function SignalInfoCards({ signal1, signal2, needsSecond, roc1, roc2 }) {
  if (!signal1) return null;

  const formatRoc = (roc) => {
    if (!roc) return '';
    if (roc.type === 'all') return 'ROC: all z';
    if (roc.type === 'nonzero') return 'ROC: z \u2260 0';
    if (roc.type === 'outside') return `ROC: |z| > ${roc.radius.toFixed(2)}`;
    return '';
  };

  return (
    <div className="zt-signal-cards">
      <div className="zt-signal-card" style={{ '--signal-color': '#3b82f6' }}>
        <div className="zt-signal-card-title">Signal 1</div>
        <div className="zt-signal-card-label">{signal1.label}</div>
        <div className="zt-signal-card-z">X\u2081(z) = {signal1.z_expr}</div>
        <div className="zt-signal-card-roc">{formatRoc(roc1)}</div>
      </div>
      {needsSecond && signal2 && (
        <div className="zt-signal-card" style={{ '--signal-color': '#ef4444' }}>
          <div className="zt-signal-card-title">Signal 2</div>
          <div className="zt-signal-card-label">{signal2.label}</div>
          <div className="zt-signal-card-z">X\u2082(z) = {signal2.z_expr}</div>
          <div className="zt-signal-card-roc">{formatRoc(roc2)}</div>
        </div>
      )}
    </div>
  );
}

/* ── Result Info Bar ───────────────────────────────────── */

function ResultInfoBar({ resultInfo }) {
  if (!resultInfo) return null;
  return (
    <div className="zt-result-info">
      <span className="zt-result-label">Z-Domain:</span>
      <span className="zt-result-expr">{resultInfo.z_expr}</span>
    </div>
  );
}

/* ── Animation Controls ────────────────────────────────── */

function AnimationControls({ step, maxStep, playing, onPlay, onPause, onStepFwd, onStepBack, onReset }) {
  return (
    <div className="zt-animation-controls">
      <button className="zt-anim-btn" onClick={onReset} title="Reset Animation">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M2 2v5h5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M3.05 10A6 6 0 1 0 4.2 4.2L2 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </button>
      <button className="zt-anim-btn" onClick={onStepBack} disabled={step <= 0} title="Step Back">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M10 12L5 8l5-4v8z" fill="currentColor"/>
        </svg>
      </button>
      {playing ? (
        <button className="zt-anim-btn zt-anim-btn--primary" onClick={onPause} title="Pause">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="4" y="3" width="3" height="10" rx="0.5" fill="currentColor"/>
            <rect x="9" y="3" width="3" height="10" rx="0.5" fill="currentColor"/>
          </svg>
        </button>
      ) : (
        <button className="zt-anim-btn zt-anim-btn--primary" onClick={onPlay} disabled={step >= maxStep} title="Play">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M4 3l9 5-9 5V3z" fill="currentColor"/>
          </svg>
        </button>
      )}
      <button className="zt-anim-btn" onClick={onStepFwd} disabled={step >= maxStep} title="Step Forward">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M6 4l5 4-5 4V4z" fill="currentColor"/>
        </svg>
      </button>
      <span className="zt-anim-counter">
        Step {step} / {maxStep}
      </span>
    </div>
  );
}

/* ── Stem Plot (Plotly) ────────────────────────────────── */

function StemPlot({ plot, theme, height = 220, revision }) {
  const isDark = theme === 'dark';
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
    showlegend: false,
    datarevision: `${plot.id}-${revision}-${Date.now()}`,
    uirevision: `${plot.id}-${revision}`,
  };

  return (
    <div className="zt-stem-card">
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

/* ── Z-Plane Plot ──────────────────────────────────────── */

function ZPlanePlot({ plot, theme, height = 340, revision }) {
  const isDark = theme === 'dark';
  const backendLayout = plot.layout || {};
  const bx = backendLayout.xaxis || {};
  const by = backendLayout.yaxis || {};

  const layout = {
    title: {
      text: plot.title || 'Z-Plane',
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
      ...bx,
      gridcolor: isDark ? 'rgba(71, 85, 105, 0.4)' : 'rgba(100, 116, 139, 0.2)',
      zerolinecolor: isDark ? 'rgba(148, 163, 184, 0.5)' : 'rgba(100, 116, 139, 0.5)',
      tickfont: { color: isDark ? '#94a3b8' : '#475569', size: 10 },
      title: {
        text: bx.title?.text || bx.title || 'Real',
        font: { color: isDark ? '#94a3b8' : '#334155', size: 11 },
      },
      showline: true,
      linecolor: isDark ? '#475569' : '#cbd5e1',
    },
    yaxis: {
      ...by,
      gridcolor: isDark ? 'rgba(71, 85, 105, 0.4)' : 'rgba(100, 116, 139, 0.2)',
      zerolinecolor: isDark ? 'rgba(148, 163, 184, 0.5)' : 'rgba(100, 116, 139, 0.5)',
      tickfont: { color: isDark ? '#94a3b8' : '#475569', size: 10 },
      title: {
        text: by.title?.text || by.title || 'Imaginary',
        font: { color: isDark ? '#94a3b8' : '#334155', size: 11 },
      },
      showline: true,
      linecolor: isDark ? '#475569' : '#cbd5e1',
      scaleanchor: 'x',
      scaleratio: 1,
    },
    legend: {
      ...backendLayout.legend,
      font: { color: isDark ? '#e2e8f0' : '#1e293b', size: 10 },
      bgcolor: isDark ? 'rgba(30, 41, 59, 0.9)' : 'rgba(255, 255, 255, 0.9)',
      bordercolor: isDark ? '#334155' : '#e2e8f0',
      borderwidth: 1,
    },
    margin: { l: 55, r: 25, t: 45, b: 50 },
    height,
    autosize: true,
    showlegend: true,
    datarevision: backendLayout.datarevision || `${plot.id}-${revision}-${Date.now()}`,
    uirevision: backendLayout.uirevision || `${plot.id}-${revision}`,
  };

  return (
    <div className="zt-zplane-card">
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

/* ── Animated Convolution Result ───────────────────────── */

function AnimatedConvolutionResult({ convSteps, animStep, theme }) {
  const isDark = theme === 'dark';
  if (!convSteps || convSteps.length === 0) return null;

  const totalSteps = convSteps.length;
  const visibleCount = Math.min(animStep, totalSteps);

  // Pre-compute stable y-range from ALL results
  const allValues = convSteps.map((s) => s.result_value);
  const allMin = Math.min(0, ...allValues);
  const allMax = Math.max(0, ...allValues);
  const span = allMax - allMin;
  const pad = span > 0.001 ? span * 0.2 : 1.0;
  const yRange = [allMin - pad, allMax + pad];

  // Build stem data for revealed steps
  const stemX = [];
  const stemY = [];
  const markerX = [];
  const markerY = [];

  for (let i = 0; i < visibleCount; i++) {
    stemX.push(i, i, null);
    stemY.push(0, convSteps[i].result_value, null);
    markerX.push(i);
    markerY.push(convSteps[i].result_value);
  }

  // Pending markers for unrevealed steps
  const pendingX = [];
  const pendingY = [];
  for (let i = visibleCount; i < totalSteps; i++) {
    pendingX.push(i);
    pendingY.push(0);
  }

  const traces = [];

  if (stemX.length > 0) {
    traces.push({
      x: stemX,
      y: stemY,
      type: 'scatter',
      mode: 'lines',
      line: { color: '#14b8a6', width: 2.5 },
      showlegend: false,
      hoverinfo: 'skip',
    });
    traces.push({
      x: markerX,
      y: markerY,
      type: 'scatter',
      mode: 'markers',
      name: 'y[n] (convolution)',
      marker: {
        color: '#14b8a6',
        size: 11,
        line: { color: isDark ? '#0a0e27' : '#ffffff', width: 2 },
      },
      hovertemplate: 'n=%{x}<br>y[n]=%{y:.4f}<extra></extra>',
    });
  }

  if (pendingX.length > 0) {
    traces.push({
      x: pendingX,
      y: pendingY,
      type: 'scatter',
      mode: 'markers',
      marker: { color: 'rgba(148,163,184,0.25)', size: 7 },
      showlegend: false,
      hoverinfo: 'skip',
    });
  }

  const layout = {
    title: {
      text: 'Convolution Result: y[n] = x\u2081[n] \u2217 x\u2082[n]',
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
      dtick: totalSteps <= 25 ? 1 : 5,
      range: [-0.5, totalSteps - 0.5],
      showline: true,
      linecolor: isDark ? '#475569' : '#cbd5e1',
    },
    yaxis: {
      title: { text: 'y[n]', font: { color: isDark ? '#94a3b8' : '#334155', size: 11 } },
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
    datarevision: `conv-anim-${animStep}-${Date.now()}`,
    uirevision: 'conv-anim',
  };

  return (
    <div className="zt-stem-card">
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

/* ── ROC Legend ─────────────────────────────────────────── */

function ROCLegend({ roc1, roc2, rocResult, property }) {
  const formatRoc = (roc) => {
    if (!roc) return '';
    if (roc.type === 'all') return 'all z';
    if (roc.type === 'nonzero') return 'z \u2260 0';
    if (roc.type === 'outside') return `|z| > ${roc.radius.toFixed(2)}`;
    return '';
  };

  const needsSecond = property === 'linearity' || property === 'convolution';

  return (
    <div className="zt-roc-legend">
      <div className="zt-roc-item">
        <span
          className="zt-roc-swatch"
          style={{
            '--swatch-color': 'rgba(59,130,246,0.6)',
            '--swatch-bg': 'rgba(59,130,246,0.15)',
          }}
        />
        <span>ROC\u2081: {formatRoc(roc1)}</span>
      </div>
      {needsSecond && roc2 && (
        <div className="zt-roc-item">
          <span
            className="zt-roc-swatch"
            style={{
              '--swatch-color': 'rgba(239,68,68,0.6)',
              '--swatch-bg': 'rgba(239,68,68,0.15)',
            }}
          />
          <span>ROC\u2082: {formatRoc(roc2)}</span>
        </div>
      )}
      {rocResult && (
        <div className="zt-roc-item">
          <span
            className="zt-roc-swatch"
            style={{
              '--swatch-color': 'rgba(20,184,166,0.8)',
              '--swatch-bg': 'rgba(20,184,166,0.2)',
            }}
          />
          <span>Result ROC: {formatRoc(rocResult)}</span>
        </div>
      )}
      {rocResult?.note && <div className="zt-roc-note">{rocResult.note}</div>}
    </div>
  );
}

/* ── Main Viewer ───────────────────────────────────────── */

function ZTransformPropertiesViewer({ metadata, plots, currentParams, onParamChange, onButtonClick }) {
  const theme = useTheme();
  const isDark = theme === 'dark';
  const [animStep, setAnimStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const timerRef = useRef(null);

  const property = metadata?.property || 'linearity';
  const convSteps = metadata?.conv_steps;
  const convNumSteps = metadata?.conv_num_steps || 0;
  const needsSecond = metadata?.needs_second_signal;
  const revision = metadata?.revision || 0;

  // Reset animation when any parameter changes (use backend revision counter)
  const prevRevision = useRef(revision);
  useEffect(() => {
    if (prevRevision.current !== revision) {
      setAnimStep(0);
      setPlaying(false);
      prevRevision.current = revision;
    }
  }, [revision]);

  // Animation timer for convolution
  useEffect(() => {
    if (playing && property === 'convolution' && animStep < convNumSteps) {
      timerRef.current = setTimeout(() => {
        setAnimStep((s) => s + 1);
      }, 400);
    } else if (playing && animStep >= convNumSteps) {
      setPlaying(false);
    }
    return () => clearTimeout(timerRef.current);
  }, [playing, animStep, convNumSteps, property]);

  const onPlay = useCallback(() => {
    if (animStep >= convNumSteps) setAnimStep(0);
    setPlaying(true);
  }, [animStep, convNumSteps]);

  const onPause = useCallback(() => setPlaying(false), []);

  const onStepFwd = useCallback(() => {
    setPlaying(false);
    setAnimStep((s) => Math.min(s + 1, convNumSteps));
  }, [convNumSteps]);

  const onStepBack = useCallback(() => {
    setPlaying(false);
    setAnimStep((s) => Math.max(s - 1, 0));
  }, []);

  const onAnimReset = useCallback(() => {
    setPlaying(false);
    setAnimStep(0);
  }, []);

  if (!metadata || !plots || plots.length === 0) {
    return (
      <div className="zt-viewer">
        <div className="zt-viewer-empty">
          <p>Loading Z-Transform Properties simulation...</p>
        </div>
      </div>
    );
  }

  // Find plots by ID
  const signal1Plot = plots.find((p) => p.id === 'signal_1');
  const signal2Plot = plots.find((p) => p.id === 'signal_2');
  const resultPlot = plots.find((p) => p.id === 'result');
  const zPlanePlot = plots.find((p) => p.id === 'z_plane');

  return (
    <div className="zt-viewer">
      {/* Property Formula */}
      <PropertyFormulaBadge metadata={metadata} />

      {/* Signal Info Cards */}
      <SignalInfoCards
        signal1={metadata.signal_1_info}
        signal2={metadata.signal_2_info}
        needsSecond={needsSecond}
        roc1={metadata.roc_1}
        roc2={metadata.roc_2}
      />

      {/* Result Z-domain expression */}
      <ResultInfoBar resultInfo={metadata.result_info} />

      {/* ── Time Domain ─────────────────────────────────── */}
      <div className="zt-time-domain">
        <div className="zt-section-header">
          <span className="zt-section-tag zt-section-tag--time">TIME</span>
          <span className="zt-section-title">Time-Domain Signals</span>
        </div>
        <div className={`zt-signal-plots${!needsSecond ? ' zt-signal-plots--single' : ''}`}>
          {signal1Plot && <StemPlot plot={signal1Plot} theme={theme} height={200} revision={revision} />}
          {needsSecond && signal2Plot && (
            <StemPlot plot={signal2Plot} theme={theme} height={200} revision={revision} />
          )}
        </div>

        {/* Convolution animation controls */}
        {property === 'convolution' && (
          <AnimationControls
            step={animStep}
            maxStep={convNumSteps}
            playing={playing}
            onPlay={onPlay}
            onPause={onPause}
            onStepFwd={onStepFwd}
            onStepBack={onStepBack}
            onReset={onAnimReset}
          />
        )}

        {/* Result plot */}
        {property === 'convolution' ? (
          <AnimatedConvolutionResult
            convSteps={convSteps}
            animStep={animStep}
            theme={theme}
          />
        ) : (
          resultPlot && <StemPlot plot={resultPlot} theme={theme} height={240} revision={revision} />
        )}
      </div>

      {/* ── Z Domain ────────────────────────────────────── */}
      <div className="zt-z-domain">
        <div className="zt-section-header">
          <span className="zt-section-tag zt-section-tag--z">Z</span>
          <span className="zt-section-title">Z-Plane: Poles, Zeros & ROC</span>
        </div>
        {zPlanePlot && <ZPlanePlot plot={zPlanePlot} theme={theme} height={340} revision={revision} />}
        <ROCLegend
          roc1={metadata.roc_1}
          roc2={metadata.roc_2}
          rocResult={metadata.roc_result}
          property={property}
        />
      </div>
    </div>
  );
}

export default ZTransformPropertiesViewer;
