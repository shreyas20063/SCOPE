/**
 * LaplacePropertiesViewer Component
 *
 * Custom viewer for the Laplace Transform Properties Lab simulation.
 * Demonstrates 7 properties: linearity, time delay, multiply-by-t,
 * frequency shift, differentiation, integration, and convolution.
 * Split time-domain (continuous lines) / s-domain (pole-zero + ROC) panels.
 */

import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import '../styles/LaplacePropertiesViewer.css';

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

/* ── Property labels ──────────────────────────────────── */

const propertyLabels = {
  linearity: 'Linearity',
  delay: 'Time Delay',
  multiply_t: 'Multiply by t',
  freq_shift: 'Frequency Shift (e\u207b\u1d43\u1d57)',
  differentiate: 'Differentiation',
  integrate: 'Integration',
  convolution: 'Convolution',
};

/* ── Property Formula Badge ───────────────────────────── */

function PropertyFormulaBadge({ metadata }) {
  if (!metadata) return null;
  const formula = metadata.property_formula || '';
  const property = metadata.property || '';

  return (
    <div className="lp-formula-badge">
      <span className="lp-formula-label">{propertyLabels[property] || property}</span>
      <span className="lp-formula-text">{formula}</span>
    </div>
  );
}

/* ── Signal Info Cards ────────────────────────────────── */

function SignalInfoCards({ signal1, signal2, needsSecond, roc1, roc2 }) {
  if (!signal1) return null;

  const formatRoc = (roc) => {
    if (!roc) return '';
    if (roc.type === 'all') return 'ROC: all s (entire \u2102)';
    if (roc.type === 'right_half') {
      const b = roc.boundary;
      if (b === null || b === undefined) return '';
      if (b === 0) return 'ROC: Re(s) > 0';
      return `ROC: Re(s) > ${b.toFixed(2)}`;
    }
    return '';
  };

  return (
    <div className="lp-signal-cards">
      <div className="lp-signal-card" style={{ '--signal-color': '#3b82f6' }}>
        <div className="lp-signal-card-title">Signal 1</div>
        <div className="lp-signal-card-label">{signal1.label}</div>
        <div className="lp-signal-card-s">X&#x2081;(s) = {signal1.s_expr}</div>
        <div className="lp-signal-card-roc">{formatRoc(roc1)}</div>
      </div>
      {needsSecond && signal2 && (
        <div className="lp-signal-card" style={{ '--signal-color': '#ef4444' }}>
          <div className="lp-signal-card-title">Signal 2</div>
          <div className="lp-signal-card-label">{signal2.label}</div>
          <div className="lp-signal-card-s">X&#x2082;(s) = {signal2.s_expr}</div>
          <div className="lp-signal-card-roc">{formatRoc(roc2)}</div>
        </div>
      )}
    </div>
  );
}

/* ── Result Info Bar ──────────────────────────────────── */

function ResultInfoBar({ resultInfo }) {
  if (!resultInfo) return null;
  return (
    <div className="lp-result-info">
      <span className="lp-result-label">S-Domain:</span>
      <span className="lp-result-expr">{resultInfo.s_expr}</span>
    </div>
  );
}

/* ── Line Plot (Plotly) ───────────────────────────────── */

function LinePlot({ plot, theme, height = 220, revision }) {
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
    <div className="lp-line-card">
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

/* ── S-Plane Plot ─────────────────────────────────────── */

function SPlanePlot({ plot, theme, height = 340, revision }) {
  const isDark = theme === 'dark';
  const backendLayout = plot.layout || {};
  const bx = backendLayout.xaxis || {};
  const by = backendLayout.yaxis || {};

  const layout = {
    title: {
      text: plot.title || 'S-Plane',
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
        text: bx.title?.text || bx.title || 'Re(s)',
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
        text: by.title?.text || by.title || 'Im(s)',
        font: { color: isDark ? '#94a3b8' : '#334155', size: 11 },
      },
      showline: true,
      linecolor: isDark ? '#475569' : '#cbd5e1',
      scaleanchor: 'x',
      scaleratio: 1,
      constrain: 'domain',
    },
    annotations: backendLayout.annotations || [],
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
    <div className="lp-splane-card">
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

/* ── ROC Legend ────────────────────────────────────────── */

function ROCLegend({ roc1, roc2, rocResult, property }) {
  const formatRoc = (roc) => {
    if (!roc) return '';
    if (roc.type === 'all') return 'all s (entire \u2102)';
    if (roc.type === 'right_half') {
      const b = roc.boundary;
      if (b === null || b === undefined) return '';
      if (b === 0) return 'Re(s) > 0';
      return `Re(s) > ${b.toFixed(2)}`;
    }
    return '';
  };

  const needsSecond = property === 'linearity' || property === 'convolution';

  return (
    <div className="lp-roc-legend">
      <div className="lp-roc-item">
        <span
          className="lp-roc-swatch"
          style={{
            '--swatch-color': 'rgba(59,130,246,0.6)',
            '--swatch-bg': 'rgba(59,130,246,0.15)',
          }}
        />
        <span>ROC&#x2081;: {formatRoc(roc1)}</span>
      </div>
      {needsSecond && roc2 && (
        <div className="lp-roc-item">
          <span
            className="lp-roc-swatch"
            style={{
              '--swatch-color': 'rgba(239,68,68,0.6)',
              '--swatch-bg': 'rgba(239,68,68,0.15)',
            }}
          />
          <span>ROC&#x2082;: {formatRoc(roc2)}</span>
        </div>
      )}
      {rocResult && (
        <div className="lp-roc-item">
          <span
            className="lp-roc-swatch"
            style={{
              '--swatch-color': 'rgba(20,184,166,0.8)',
              '--swatch-bg': 'rgba(20,184,166,0.2)',
            }}
          />
          <span>Result ROC: {formatRoc(rocResult)}</span>
        </div>
      )}
      {rocResult?.note && <div className="lp-roc-note">{rocResult.note}</div>}
    </div>
  );
}

/* ── Main Viewer ──────────────────────────────────────── */

function LaplacePropertiesViewer({ metadata, plots, currentParams, onParamChange, onButtonClick }) {
  const theme = useTheme();

  const property = metadata?.property || 'linearity';
  const needsSecond = metadata?.needs_second_signal;
  const revision = metadata?.revision || 0;

  if (!metadata || !plots || plots.length === 0) {
    return (
      <div className="lp-viewer">
        <div className="lp-viewer-empty">
          <p>Loading Laplace Properties simulation...</p>
        </div>
      </div>
    );
  }

  // Find plots by ID
  const signal1Plot = plots.find((p) => p.id === 'signal_1');
  const signal2Plot = plots.find((p) => p.id === 'signal_2');
  const resultPlot = plots.find((p) => p.id === 'result');
  const sPlanePlot = plots.find((p) => p.id === 's_plane');

  return (
    <div className="lp-viewer">
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

      {/* Result S-domain expression */}
      <ResultInfoBar resultInfo={metadata.result_info} />

      {/* ── Time Domain ─────────────────────────────────── */}
      <div className="lp-time-domain">
        <div className="lp-section-header">
          <span className="lp-section-tag lp-section-tag--time">TIME</span>
          <span className="lp-section-title">Time-Domain Signals</span>
        </div>
        <div className={`lp-signal-plots${!needsSecond ? ' lp-signal-plots--single' : ''}`}>
          {signal1Plot && <LinePlot plot={signal1Plot} theme={theme} height={200} revision={revision} />}
          {needsSecond && signal2Plot && (
            <LinePlot plot={signal2Plot} theme={theme} height={200} revision={revision} />
          )}
        </div>
        {resultPlot && <LinePlot plot={resultPlot} theme={theme} height={240} revision={revision} />}
      </div>

      {/* ── S Domain ────────────────────────────────────── */}
      <div className="lp-s-domain">
        <div className="lp-section-header">
          <span className="lp-section-tag lp-section-tag--s">S</span>
          <span className="lp-section-title">S-Plane: Poles, Zeros & ROC</span>
        </div>
        {sPlanePlot && <SPlanePlot plot={sPlanePlot} theme={theme} height={340} revision={revision} />}
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

export default LaplacePropertiesViewer;
