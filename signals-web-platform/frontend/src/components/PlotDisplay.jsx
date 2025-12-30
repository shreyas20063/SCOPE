/**
 * PlotDisplay Component
 *
 * Renders Plotly charts from plot data provided by the backend.
 * Supports multiple plots, responsive sizing, and interactivity.
 * Includes theme-aware styling for dark/light modes.
 */

import React, { useMemo, memo, useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import '../styles/PlotDisplay.css';

/**
 * Get current theme
 */
function useTheme() {
  const [theme, setTheme] = useState(() => {
    return document.documentElement.getAttribute('data-theme') || 'dark';
  });

  useEffect(() => {
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
 * Theme-aware Plotly layout
 */
function getDefaultLayout(theme) {
  const isDark = theme === 'dark';

  return {
    paper_bgcolor: isDark ? '#0f172a' : 'rgba(255, 255, 255, 0.98)',
    plot_bgcolor: isDark ? '#1e293b' : '#f8fafc',
    font: {
      color: isDark ? '#e2e8f0' : '#1e293b',
      family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      size: 12,
    },
    xaxis: {
      gridcolor: isDark ? 'rgba(71, 85, 105, 0.4)' : 'rgba(100, 116, 139, 0.2)',
      gridwidth: 1,
      zerolinecolor: isDark ? 'rgba(148, 163, 184, 0.5)' : 'rgba(100, 116, 139, 0.5)',
      zerolinewidth: 1.5,
      tickfont: { color: isDark ? '#94a3b8' : '#475569', size: 11 },
      titlefont: { color: isDark ? '#cbd5e1' : '#334155', size: 12 },
      autorange: false,
      showline: true,
      linecolor: isDark ? '#475569' : '#cbd5e1',
      linewidth: 1,
    },
    yaxis: {
      gridcolor: isDark ? 'rgba(71, 85, 105, 0.4)' : 'rgba(100, 116, 139, 0.2)',
      gridwidth: 1,
      zerolinecolor: isDark ? 'rgba(148, 163, 184, 0.5)' : 'rgba(100, 116, 139, 0.5)',
      zerolinewidth: 1.5,
      tickfont: { color: isDark ? '#94a3b8' : '#475569', size: 11 },
      titlefont: { color: isDark ? '#cbd5e1' : '#334155', size: 12 },
      autorange: false,
      showline: true,
      linecolor: isDark ? '#475569' : '#cbd5e1',
      linewidth: 1,
    },
    margin: { t: 40, r: 25, b: 50, l: 55 },
    height: 300,  /* Explicit height to constrain Plotly chart */
    autosize: true,
    showlegend: true,
    legend: {
      font: { color: isDark ? '#e2e8f0' : '#1e293b', size: 11 },
      bgcolor: isDark ? 'rgba(15, 23, 42, 0.95)' : 'rgba(255, 255, 255, 0.95)',
      bordercolor: isDark ? '#334155' : '#e2e8f0',
      borderwidth: 1,
      orientation: 'h',
      yanchor: 'top',
      y: -0.12,
      xanchor: 'center',
      x: 0.5,
    },
    hoverlabel: {
      bgcolor: isDark ? '#1e293b' : '#ffffff',
      bordercolor: isDark ? '#475569' : '#e2e8f0',
      font: { color: isDark ? '#f1f5f9' : '#1e293b', size: 12 },
    },
  };
}

/**
 * Plotly config options
 */
const plotConfig = {
  responsive: true,
  displayModeBar: true,
  modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d'],  // Remove autoScale to keep fixed axes
  displaylogo: false,
  toImageButtonOptions: {
    format: 'png',
    filename: 'simulation_plot',
    height: 600,
    width: 800,
    scale: 2,
  },
};

/**
 * Text Panel component for displaying theory/learning content
 */
const TextPanel = memo(function TextPanel({ plot }) {
  const theme = useTheme();
  const isDark = theme === 'dark';
  const content = plot.content || {};

  return (
    <div className="plot-card text-panel-card">
      <div className="text-panel-header">
        <h3>{plot.title || 'Information Panel'}</h3>
      </div>
      <div
        className="text-panel-content"
        style={{
          backgroundColor: isDark
            ? 'rgba(30, 41, 59, 0.8)'
            : (content.backgroundColor || 'rgba(255, 255, 255, 0.95)'),
          borderColor: content.borderColor || (isDark ? '#475569' : '#e2e8f0'),
        }}
      >
        {/* Guided scenario message if present */}
        {content.guidedMessage && (
          <div className="guided-message" style={{
            backgroundColor: isDark ? 'rgba(251, 191, 36, 0.2)' : 'rgba(251, 191, 36, 0.3)',
            borderLeft: '4px solid #f59e0b',
            padding: '12px',
            marginBottom: '16px',
            borderRadius: '4px',
          }}>
            <strong>🎯 Guided Mode:</strong> {content.guidedMessage}
          </div>
        )}

        {/* Main explanation content */}
        {content.explanation && (
          <div
            className="explanation-text"
            dangerouslySetInnerHTML={{ __html: content.explanation }}
            style={{
              fontFamily: 'monospace',
              fontSize: '13px',
              lineHeight: '1.6',
              color: isDark ? '#e2e8f0' : '#1e293b',
            }}
          />
        )}

        {/* Current status display */}
        {content.currentStatus && (
          <div className="status-display" style={{
            marginTop: '16px',
            padding: '12px',
            backgroundColor: content.currentStatus.is_stable
              ? (isDark ? 'rgba(39, 174, 96, 0.2)' : 'rgba(39, 174, 96, 0.1)')
              : (isDark ? 'rgba(231, 76, 60, 0.2)' : 'rgba(231, 76, 60, 0.1)'),
            borderRadius: '6px',
            border: `1px solid ${content.currentStatus.is_stable ? '#27ae60' : '#e74c3c'}`,
          }}>
            <div style={{
              fontSize: '14px',
              fontWeight: 'bold',
              color: content.currentStatus.is_stable ? '#27ae60' : '#e74c3c',
              marginBottom: '8px',
            }}>
              {content.currentStatus.is_stable ? '✓ STABLE' : '✗ UNSTABLE'}
            </div>
            <div style={{ fontSize: '12px', color: isDark ? '#94a3b8' : '#64748b' }}>
              <div>T/τ: {content.currentStatus.t_tau_ratio?.toFixed(3)}</div>
              <div>|z|: {content.currentStatus.z_magnitude?.toFixed(3)}</div>
              <div>RMS Error: {content.currentStatus.rms_error?.toFixed(4)}</div>
              <div>Quality: {content.currentStatus.performance_rating}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
});

/**
 * Single plot card component
 * Note: Not using React.memo to ensure dynamic title/label updates work correctly
 */
function PlotCard({ plot, index }) {
  const theme = useTheme();
  const defaultLayout = useMemo(() => getDefaultLayout(theme), [theme]);

  // Handle text panels (like Theory Panel)
  if (plot.isTextPanel) {
    return <TextPanel plot={plot} />;
  }

  // Extract values for explicit dependency tracking
  const plotTitle = plot.title;
  const plotData = plot.data;
  const plotLayout = plot.layout || {};
  const plotId = plot.id;

  // Create a comprehensive revision key (used for datarevision)
  // NOT memoized - must recalculate every render to catch all changes
  // This includes: title, trace names, and sampled data values
  const computeRevision = () => {
    const traceInfo = plotData?.map((trace, i) => {
      const len = trace.y?.length || 0;
      // Sample multiple points for better change detection
      const y0 = trace.y?.[0];
      const yMid = trace.y?.[Math.floor(len / 2)];
      const yQuarter = trace.y?.[Math.floor(len / 4)];
      const x0 = trace.x?.[0];
      const xLast = trace.x?.[len - 1];

      const fmt = (v) => typeof v === 'number' ? v.toFixed(4) : (v ?? 'na');
      return `${i}:${trace.name || ''}:${len}:${fmt(x0)}:${fmt(xLast)}:${fmt(y0)}:${fmt(yQuarter)}:${fmt(yMid)}`;
    }).join('|') || 'empty';
    return `${plotId}-${plotTitle}-${traceInfo}`;
  };
  const revision = computeRevision();

  // Merge default layout with plot-specific layout
  // NOT memoized - ensures title updates are always reflected
  const isDark = theme === 'dark';
  const layout = {
    ...defaultLayout,
    ...plotLayout,
    // Title: Use plot.title directly (dynamic from backend)
    title: {
      text: plotTitle || `Plot ${index + 1}`,
      font: { color: isDark ? '#f1f5f9' : '#1e293b', size: 16 },
    },
    xaxis: {
      ...defaultLayout.xaxis,
      ...plotLayout.xaxis,
      autorange: false,
      fixedrange: false,
      title: {
        text: plotLayout.xaxis?.title || '',
        font: { color: isDark ? '#94a3b8' : '#334155' },
      },
    },
    yaxis: {
      ...defaultLayout.yaxis,
      ...plotLayout.yaxis,
      autorange: false,
      fixedrange: false,
      title: {
        text: plotLayout.yaxis?.title || '',
        font: { color: isDark ? '#94a3b8' : '#334155' },
      },
    },
    // Merge legend with theme-aware defaults
    legend: {
      ...defaultLayout.legend,
      ...plotLayout.legend,
      font: {
        ...defaultLayout.legend?.font,
        ...plotLayout.legend?.font,
        color: isDark ? '#e2e8f0' : '#1e293b',
      },
      bgcolor: isDark ? 'rgba(30, 41, 59, 0.9)' : 'rgba(255, 255, 255, 0.9)',
    },
    // Explicitly pass shapes and annotations from backend
    shapes: plotLayout.shapes || [],
    annotations: plotLayout.annotations || [],
    // datarevision changes when data/title changes, triggering Plotly update
    datarevision: revision,
    // uirevision: use plotId to preserve zoom/pan per-plot
    uirevision: plotId || 'stable',
    transition: {
      duration: 0,
    },
  };

  // Process plot data (add default styling)
  const data = useMemo(() => {
    if (!plotData) return [];

    return plotData.map((trace, i) => ({
      ...trace,
      // Add default line colors if not specified
      line: {
        width: 2,
        ...trace.line,
        color: trace.line?.color || getDefaultColor(i),
      },
      marker: {
        ...trace.marker,
        color: trace.marker?.color || getDefaultColor(i),
      },
    }));
  }, [plotData]);

  return (
    <div className="plot-card">
      {plot.description && (
        <p className="plot-description">{plot.description}</p>
      )}
      <div className="plot-wrapper">
        <Plot
          data={data}
          layout={layout}
          config={plotConfig}
          useResizeHandler={true}
          style={{ width: '100%', height: '100%' }}
          revision={revision}
        />
      </div>
    </div>
  );
}

/**
 * Get default color for trace by index
 * Modern vibrant palette optimized for dark mode
 */
function getDefaultColor(index) {
  const colors = [
    '#60a5fa', // sky blue
    '#34d399', // emerald
    '#fbbf24', // amber
    '#f87171', // coral
    '#a78bfa', // violet
    '#2dd4bf', // teal
    '#fb923c', // orange
    '#f472b6', // pink
    '#38bdf8', // light blue
    '#4ade80', // green
  ];
  return colors[index % colors.length];
}

/**
 * Loading skeleton for plots
 */
function PlotSkeleton() {
  return (
    <div className="plot-card plot-skeleton">
      <div className="skeleton-title"></div>
      <div className="skeleton-chart"></div>
    </div>
  );
}

/**
 * Main PlotDisplay component
 * Note: Not memoized to ensure dynamic updates propagate correctly
 */
function PlotDisplay({ plots = [], isLoading = false, emptyMessage = null }) {
  if (isLoading) {
    return (
      <div className="plots-container">
        <PlotSkeleton />
        <PlotSkeleton />
      </div>
    );
  }

  if (!plots || plots.length === 0) {
    return (
      <div className="plots-container">
        <div className="plots-empty">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="18" y1="20" x2="18" y2="10" />
            <line x1="12" y1="20" x2="12" y2="4" />
            <line x1="6" y1="20" x2="6" y2="14" />
          </svg>
          <p>{emptyMessage || 'No plots to display. Adjust parameters to see results.'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="plots-container">
      {plots.map((plot, index) => (
        <PlotCard
          key={plot.id || `plot-${index}`}
          plot={plot}
          index={index}
        />
      ))}
    </div>
  );
}

export default PlotDisplay;
