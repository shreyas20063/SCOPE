/**
 * RCLowpassViewer Component
 *
 * Custom viewer for RC Lowpass Filter simulation.
 * Renders plots directly to ensure dynamic title updates work correctly.
 * Uses Claude/Anthropic warm theme colors.
 */

import React from 'react';
import Plot from 'react-plotly.js';
import './RCLowpassViewer.css';

/**
 * Claude theme colors for Plotly — warm, muted palette
 */
const CLAUDE_PLOT_THEME = {
  paper_bgcolor: '#FFFFFF',
  plot_bgcolor: '#FAFAF7',
  gridcolor: 'rgba(0, 0, 0, 0.05)',
  zerolinecolor: 'rgba(0, 0, 0, 0.1)',
  axislinecolor: '#E8E2DB',
  titleColor: '#1A1A1A',
  textColor: '#6B6560',
  tickColor: '#9B9590',
  legendBg: 'rgba(255, 255, 255, 0.95)',
  legendBorder: '#E8E2DB',
  fontFamily: "'Styrene A', 'Styrene B', -apple-system, BlinkMacSystemFont, sans-serif",
};

/**
 * Single plot component — renders Plotly chart with Claude theme
 */
function RCPlot({ plot }) {
  const layout = {
    title: {
      text: plot.title || 'Plot',
      font: { color: CLAUDE_PLOT_THEME.titleColor, size: 14, family: CLAUDE_PLOT_THEME.fontFamily },
      x: 0.5,
      xanchor: 'center',
    },
    paper_bgcolor: CLAUDE_PLOT_THEME.paper_bgcolor,
    plot_bgcolor: CLAUDE_PLOT_THEME.plot_bgcolor,
    font: {
      color: CLAUDE_PLOT_THEME.textColor,
      family: CLAUDE_PLOT_THEME.fontFamily,
      size: 12,
    },
    xaxis: {
      ...plot.layout?.xaxis,
      gridcolor: CLAUDE_PLOT_THEME.gridcolor,
      gridwidth: 1,
      zerolinecolor: CLAUDE_PLOT_THEME.zerolinecolor,
      zerolinewidth: 1,
      tickfont: { color: CLAUDE_PLOT_THEME.tickColor, size: 11, family: CLAUDE_PLOT_THEME.fontFamily },
      title: {
        text: plot.layout?.xaxis?.title || '',
        font: { color: CLAUDE_PLOT_THEME.textColor, size: 12, family: CLAUDE_PLOT_THEME.fontFamily },
      },
      showline: true,
      linecolor: CLAUDE_PLOT_THEME.axislinecolor,
      linewidth: 1,
    },
    yaxis: {
      ...plot.layout?.yaxis,
      gridcolor: CLAUDE_PLOT_THEME.gridcolor,
      gridwidth: 1,
      zerolinecolor: CLAUDE_PLOT_THEME.zerolinecolor,
      zerolinewidth: 1,
      tickfont: { color: CLAUDE_PLOT_THEME.tickColor, size: 11, family: CLAUDE_PLOT_THEME.fontFamily },
      title: {
        text: plot.layout?.yaxis?.title || '',
        font: { color: CLAUDE_PLOT_THEME.textColor, size: 12, family: CLAUDE_PLOT_THEME.fontFamily },
      },
      showline: true,
      linecolor: CLAUDE_PLOT_THEME.axislinecolor,
      linewidth: 1,
    },
    legend: {
      font: { color: CLAUDE_PLOT_THEME.titleColor, size: 11, family: CLAUDE_PLOT_THEME.fontFamily },
      bgcolor: CLAUDE_PLOT_THEME.legendBg,
      bordercolor: CLAUDE_PLOT_THEME.legendBorder,
      borderwidth: 1,
      ...plot.layout?.legend,
    },
    margin: { t: 45, r: 25, b: 55, l: 60 },
    height: 280,
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

  // Remap trace colors to Claude palette
  const themedData = (plot.data || []).map((trace, i) => {
    const colors = ['#4A7FC4', '#D97757', '#3D8C6F', '#8B7EC8', '#D4943A', '#C75450'];
    const newTrace = { ...trace };
    if (!trace.line?.color && !trace.marker?.color) {
      newTrace.line = { ...trace.line, color: colors[i % colors.length] };
      newTrace.marker = { ...trace.marker, color: colors[i % colors.length] };
    }
    return newTrace;
  });

  return (
    <div className="rc-plot-card">
      <Plot
        data={themedData}
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
    PASSING: '#3D8C6F',
    TRANSITIONING: '#D4943A',
    FILTERING: '#C75450',
  };

  const statusColor = statusColors[filterInfo.status] || '#9B9590';

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
          />
        ))}
      </div>
    </div>
  );
}

export default RCLowpassViewer;
