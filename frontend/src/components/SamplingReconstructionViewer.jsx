/**
 * SamplingReconstructionViewer Component
 *
 * Custom two-panel viewer for Sampling & Reconstruction simulation.
 * Left: continuous signal with sample stems. Right: reconstruction methods compared.
 */

import React from 'react';
import Plot from 'react-plotly.js';
import './SamplingReconstructionViewer.css';

/**
 * Get current theme from document
 */
function useTheme() {
  const [theme, setTheme] = React.useState(() => {
    return document.documentElement.getAttribute('data-theme') || 'dark';
  });

  React.useEffect(() => {
    const observer = new MutationObserver(() => {
      const newTheme = document.documentElement.getAttribute('data-theme') || 'dark';
      setTheme(newTheme);
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme'],
    });

    return () => observer.disconnect();
  }, []);

  return theme;
}

/**
 * Single plot component — renders Plotly chart with theme-aware layout
 */
function SRPlot({ plot, theme, height = 320 }) {
  const isDark = theme === 'dark';

  const layout = {
    title: {
      text: plot.title || 'Plot',
      font: { color: isDark ? '#f1f5f9' : '#1e293b', size: 15 },
      x: 0.5,
      xanchor: 'center',
    },
    paper_bgcolor: isDark ? '#0f172a' : 'rgba(255, 255, 255, 0.98)',
    plot_bgcolor: isDark ? '#1e293b' : '#f8fafc',
    font: {
      color: isDark ? '#e2e8f0' : '#1e293b',
      family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      size: 12,
    },
    xaxis: {
      ...plot.layout?.xaxis,
      gridcolor: isDark ? 'rgba(71, 85, 105, 0.4)' : 'rgba(100, 116, 139, 0.2)',
      gridwidth: 1,
      zerolinecolor: isDark ? 'rgba(148, 163, 184, 0.5)' : 'rgba(100, 116, 139, 0.5)',
      zerolinewidth: 1.5,
      tickfont: { color: isDark ? '#94a3b8' : '#475569', size: 11 },
      title: {
        text: plot.layout?.xaxis?.title || '',
        font: { color: isDark ? '#94a3b8' : '#334155', size: 12 },
      },
      showline: true,
      linecolor: isDark ? '#475569' : '#cbd5e1',
      linewidth: 1,
    },
    yaxis: {
      ...plot.layout?.yaxis,
      gridcolor: isDark ? 'rgba(71, 85, 105, 0.4)' : 'rgba(100, 116, 139, 0.2)',
      gridwidth: 1,
      zerolinecolor: isDark ? 'rgba(148, 163, 184, 0.5)' : 'rgba(100, 116, 139, 0.5)',
      zerolinewidth: 1.5,
      tickfont: { color: isDark ? '#94a3b8' : '#475569', size: 11 },
      title: {
        text: plot.layout?.yaxis?.title || '',
        font: { color: isDark ? '#94a3b8' : '#334155', size: 12 },
      },
      showline: true,
      linecolor: isDark ? '#475569' : '#cbd5e1',
      linewidth: 1,
    },
    legend: {
      font: { color: isDark ? '#e2e8f0' : '#1e293b', size: 11 },
      bgcolor: isDark ? 'rgba(30, 41, 59, 0.9)' : 'rgba(255, 255, 255, 0.9)',
      bordercolor: isDark ? '#334155' : '#e2e8f0',
      borderwidth: 1,
      ...plot.layout?.legend,
    },
    margin: { t: 45, r: 25, b: 55, l: 60 },
    height,
    autosize: true,
    showlegend: true,
    datarevision: `${plot.id}-${plot.title}-${Date.now()}`,
    uirevision: plot.id,
  };

  const config = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    displaylogo: false,
  };

  return (
    <div className="sr-plot-card">
      <Plot
        data={plot.data || []}
        layout={layout}
        config={config}
        useResizeHandler={true}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
}

/**
 * Sampling status badge — shows Nyquist info and FAITHFUL/ALIASING status
 */
function SamplingStatusBadge({ metadata }) {
  const info = metadata?.sampling_info;
  if (!info) return null;

  const statusColor = info.status === 'FAITHFUL' ? '#10b981' : '#ef4444';

  return (
    <div className="sr-status-badge">
      <div className="status-row">
        <span
          className="status-pill"
          style={{ backgroundColor: statusColor }}
        >
          {info.status}
        </span>
        <span className="status-detail">
          fs = {info.sampling_frequency} Hz
        </span>
        <span className="sr-separator">|</span>
        <span className="status-detail">
          f<sub>Nyquist</sub> = {info.nyquist_frequency} Hz
        </span>
        <span className="sr-separator">|</span>
        <span className="status-detail">
          f<sub>max</sub> = {info.max_signal_frequency} Hz
        </span>
        <span className="sr-separator">|</span>
        <span className="status-detail">
          N = {info.num_samples} samples
        </span>
      </div>
    </div>
  );
}

/**
 * MSE comparison badges — color-coded to match reconstruction trace colors
 */
function MSEBadges({ metadata }) {
  const mse = metadata?.reconstruction_mse;
  if (!mse) return null;

  const methods = [
    { key: 'zoh', label: 'ZOH', color: '#f59e0b' },
    { key: 'linear', label: 'Linear', color: '#10b981' },
    { key: 'sinc', label: 'Sinc', color: '#8b5cf6' },
  ];

  return (
    <div className="sr-mse-badges">
      {methods.map(({ key, label, color }) => (
        <span
          key={key}
          className="sr-mse-badge"
          style={{ borderColor: color, color }}
        >
          {label} MSE: {mse[key]?.toFixed(4) ?? '—'}
        </span>
      ))}
    </div>
  );
}

/**
 * Main SamplingReconstructionViewer Component
 */
function SamplingReconstructionViewer({ metadata, plots }) {
  const theme = useTheme();

  if (!plots || plots.length === 0) {
    return (
      <div className="sr-viewer">
        <div className="sr-viewer-empty">
          <p>Loading Sampling & Reconstruction simulation...</p>
        </div>
      </div>
    );
  }

  const samplingPlot = plots.find(p => p.id === 'sampling');
  const reconstructionPlot = plots.find(p => p.id === 'reconstruction');
  const errorPlot = plots.find(p => p.id === 'error');

  return (
    <div className="sr-viewer">
      {/* Status badges */}
      <SamplingStatusBadge metadata={metadata} />
      <MSEBadges metadata={metadata} />

      {/* Two-column grid: sampling (left) + reconstruction (right) */}
      <div className="sr-plots-grid">
        {samplingPlot && (
          <div className="sr-plot-column">
            <SRPlot plot={samplingPlot} theme={theme} />
          </div>
        )}
        {reconstructionPlot && (
          <div className="sr-plot-column">
            <SRPlot plot={reconstructionPlot} theme={theme} />
          </div>
        )}
      </div>

      {/* Error plot — full width, shown only when enabled */}
      {errorPlot && errorPlot.data?.length > 0 && (
        <div className="sr-error-row">
          <SRPlot plot={errorPlot} theme={theme} height={250} />
        </div>
      )}
    </div>
  );
}

export default SamplingReconstructionViewer;
