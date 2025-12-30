/**
 * RCLowpassViewer Component
 *
 * Custom viewer for RC Lowpass Filter simulation.
 * Renders plots directly to ensure dynamic title updates work correctly.
 */

import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';
import './RCLowpassViewer.css';

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
 * Single plot component - renders Plotly chart with dynamic title
 */
function RCPlot({ plot, theme }) {
  const isDark = theme === 'dark';

  // Build layout fresh every render - no memoization to ensure title updates
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
    height: 280,
    autosize: true,
    showlegend: true,
    // Critical: datarevision changes force Plotly to update
    datarevision: `${plot.id}-${plot.title}-${Date.now()}`,
    // uirevision preserves zoom/pan
    uirevision: plot.id,
  };

  const config = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    displaylogo: false,
  };

  return (
    <div className="rc-plot-card">
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
 * Filter Status Badge Component
 */
function FilterStatusBadge({ metadata }) {
  const filterInfo = metadata?.filter_info;
  if (!filterInfo) return null;

  const statusColors = {
    PASSING: '#10b981',
    TRANSITIONING: '#f59e0b',
    FILTERING: '#ef4444',
  };

  const statusColor = statusColors[filterInfo.status] || '#6b7280';

  return (
    <div className="rc-filter-status">
      <div className="status-row">
        <span
          className="status-badge"
          style={{ backgroundColor: statusColor }}
        >
          {filterInfo.status}
        </span>
        <span className="status-detail">
          f/fc = {filterInfo.ratio}
        </span>
      </div>
      <div className="status-info">
        <span>Input: {filterInfo.frequency} Hz</span>
        <span className="separator">|</span>
        <span>Cutoff: {filterInfo.cutoff_freq} Hz</span>
      </div>
    </div>
  );
}

/**
 * Main RCLowpassViewer Component
 */
function RCLowpassViewer({ metadata, plots }) {
  const theme = useTheme();

  if (!plots || plots.length === 0) {
    return (
      <div className="rc-lowpass-viewer">
        <div className="rc-viewer-empty">
          <p>Loading RC Lowpass Filter simulation...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rc-lowpass-viewer">
      {/* Filter Status Badge */}
      <FilterStatusBadge metadata={metadata} />

      {/* Plots Container */}
      <div className="rc-plots-container">
        {plots.map((plot, index) => (
          <RCPlot
            key={`${plot.id}-${index}`}
            plot={plot}
            theme={theme}
          />
        ))}
      </div>
    </div>
  );
}

export default RCLowpassViewer;
