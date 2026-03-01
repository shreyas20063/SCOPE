/**
 * SignalOperationsViewer
 *
 * Custom viewer for the Signal Operations Playground simulation.
 * Features: operation badges, overlay/separate toggle, signal metrics,
 * preset buttons, even/odd decomposition, and direct Plotly rendering.
 */

import React, { useState, useMemo, useCallback, useEffect, memo } from 'react';
import Plot from 'react-plotly.js';
import '../styles/SignalOperationsViewer.css';

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

/* ── Sub-components ──────────────────────────────────────────── */

const OperationChainBar = memo(function OperationChainBar({ operations }) {
  if (!operations || operations.length === 0) {
    return (
      <div className="sig-ops-chain-bar sig-ops-chain-identity">
        <span className="sig-ops-chain-label">Identity:</span>
        <span className="sig-ops-chain-formula">g(t) = f(t)</span>
      </div>
    );
  }

  return (
    <div className="sig-ops-chain-bar">
      <span className="sig-ops-chain-label">Active:</span>
      <div className="sig-ops-badges">
        {operations.map((op, idx) => (
          <span
            key={idx}
            className="sig-ops-badge"
            style={{
              '--badge-color': op.color,
            }}
          >
            {op.symbol}
          </span>
        ))}
      </div>
    </div>
  );
});

const FormulaDisplay = memo(function FormulaDisplay({ formula }) {
  if (!formula) return null;
  return (
    <div className="sig-ops-formula-display">
      <span className="sig-ops-formula-eq">g(t) =</span>
      <span className="sig-ops-formula-expr">{formula}</span>
    </div>
  );
});

const MetricCard = memo(function MetricCard({ label, value, unit, color }) {
  const displayVal = typeof value === 'number'
    ? (Math.abs(value) >= 100 ? value.toFixed(1) : value.toFixed(4))
    : '—';

  return (
    <div className="sig-ops-metric-card">
      <div className="sig-ops-metric-label">{label}</div>
      <div className="sig-ops-metric-value" style={{ color }}>
        {displayVal}
        {unit && <span className="sig-ops-metric-unit">{unit}</span>}
      </div>
    </div>
  );
});

const MetricsPanel = memo(function MetricsPanel({ metrics }) {
  if (!metrics) return null;

  return (
    <div className="sig-ops-metrics">
      <div className="sig-ops-metrics-title">Signal Properties</div>
      <div className="sig-ops-metrics-grid">
        <MetricCard label="Original Energy" value={metrics.original?.energy} color="#3b82f6" />
        <MetricCard label="Transformed Energy" value={metrics.transformed?.energy} color="#ef4444" />
        <MetricCard label="Energy Ratio" value={metrics.energy_ratio} unit="x" color="#10b981" />
        <MetricCard label="Original Peak" value={metrics.original?.peak_amplitude} color="#3b82f6" />
        <MetricCard label="Transformed Peak" value={metrics.transformed?.peak_amplitude} color="#ef4444" />
        <MetricCard label="Transformed DC" value={metrics.transformed?.dc_component} color="#f59e0b" />
      </div>
    </div>
  );
});

const PresetButtons = memo(function PresetButtons({ presets, onPresetClick }) {
  if (!presets || presets.length === 0) return null;

  return (
    <div className="sig-ops-presets">
      <span className="sig-ops-presets-label">Presets:</span>
      <div className="sig-ops-presets-row">
        {presets.map((preset, idx) => (
          <button
            key={idx}
            className="sig-ops-preset-btn"
            onClick={() => onPresetClick(preset.params)}
          >
            {preset.label}
          </button>
        ))}
      </div>
    </div>
  );
});

/* ── Plot component ──────────────────────────────────────────── */

const plotConfig = {
  responsive: true,
  displayModeBar: true,
  modeBarButtonsToRemove: ['lasso2d', 'select2d'],
  displaylogo: false,
  toImageButtonOptions: {
    format: 'png',
    filename: 'signal_operations',
    height: 600,
    width: 800,
    scale: 2,
  },
};

/**
 * Helper: build a themed axis config
 */
function themedAxis(backendAxis, isDark) {
  return {
    ...backendAxis,
    gridcolor: isDark ? 'rgba(71,85,105,0.4)' : 'rgba(100,116,139,0.2)',
    gridwidth: 1,
    zerolinecolor: isDark ? 'rgba(148,163,184,0.5)' : 'rgba(100,116,139,0.5)',
    zerolinewidth: 1.5,
    tickfont: { color: isDark ? '#94a3b8' : '#475569', size: 11 },
    showline: true,
    linecolor: isDark ? '#475569' : '#cbd5e1',
    linewidth: 1,
    title: {
      text: backendAxis.title?.text || backendAxis.title || '',
      font: { color: isDark ? '#94a3b8' : '#334155', size: 12 },
    },
  };
}

function themedLegend(isDark) {
  return {
    font: { color: isDark ? '#e2e8f0' : '#1e293b', size: 11 },
    bgcolor: isDark ? 'rgba(15,23,42,0.85)' : 'rgba(255,255,255,0.85)',
    bordercolor: isDark ? '#334155' : '#e2e8f0',
    borderwidth: 1,
    orientation: 'h',
    yanchor: 'bottom',
    y: 0.01,
    xanchor: 'center',
    x: 0.5,
  };
}

/**
 * DualSignalPlot — renders two plots stacked as Plotly subplots
 * with shared x-axis and matched y-axis so zoom/pan syncs on both.
 */
function DualSignalPlot({ topPlot, bottomPlot, theme }) {
  const isDark = theme === 'dark';

  const { data, layout } = useMemo(() => {
    const topLayout = topPlot?.layout || {};
    const botLayout = bottomPlot?.layout || {};

    // Top traces → xaxis/yaxis (row 1)
    const topTraces = (topPlot?.data || []).map(t => ({
      ...t,
      line: { width: 2, ...t.line },
      xaxis: 'x',
      yaxis: 'y',
    }));

    // Bottom traces → xaxis2/yaxis2 (row 2)
    const botTraces = (bottomPlot?.data || []).map(t => ({
      ...t,
      line: { width: 2, ...t.line },
      xaxis: 'x2',
      yaxis: 'y2',
    }));

    const topX = topLayout.xaxis || {};
    const topY = topLayout.yaxis || {};
    const botX = botLayout.xaxis || {};
    const botY = botLayout.yaxis || {};

    const mergedLayout = {
      paper_bgcolor: isDark ? '#0f172a' : 'rgba(255,255,255,0.98)',
      plot_bgcolor: isDark ? '#1e293b' : '#f8fafc',
      font: {
        color: isDark ? '#e2e8f0' : '#1e293b',
        family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        size: 12,
      },
      // Row 1: top half
      xaxis: {
        ...themedAxis(topX, isDark),
        domain: [0, 1],
        anchor: 'y',
        showticklabels: false,
        title: { text: '' },
      },
      yaxis: {
        ...themedAxis(topY, isDark),
        autorange: topY.autorange !== undefined ? topY.autorange : true,
        domain: [0.55, 1],
        anchor: 'x',
      },
      // Row 2: bottom half — shares x-range with row 1
      xaxis2: {
        ...themedAxis(botX, isDark),
        domain: [0, 1],
        anchor: 'y2',
        matches: 'x',
      },
      yaxis2: {
        ...themedAxis(botY, isDark),
        autorange: botY.autorange !== undefined ? botY.autorange : true,
        domain: [0, 0.45],
        anchor: 'x2',
        matches: 'y',
      },
      margin: { t: 10, r: 20, b: 40, l: 55 },
      height: 440,
      autosize: true,
      showlegend: false,
      hoverlabel: {
        bgcolor: isDark ? '#1e293b' : '#ffffff',
        bordercolor: isDark ? '#475569' : '#e2e8f0',
        font: { color: isDark ? '#f1f5f9' : '#1e293b', size: 12 },
      },
      // Subplot title annotations — inside each subplot using paper coords
      annotations: [
        {
          text: `<b>${topPlot?.title || 'Original'}</b>`,
          xref: 'paper', yref: 'paper',
          x: 0.01, y: 0.98,
          xanchor: 'left', yanchor: 'top',
          showarrow: false,
          font: { color: isDark ? '#94a3b8' : '#475569', size: 12 },
        },
        {
          text: `<b>${bottomPlot?.title || 'Transformed'}</b>`,
          xref: 'paper', yref: 'paper',
          x: 0.01, y: 0.43,
          xanchor: 'left', yanchor: 'top',
          showarrow: false,
          font: { color: isDark ? '#94a3b8' : '#475569', size: 12 },
        },
      ],
      datarevision: `dual-${topPlot?.title}-${bottomPlot?.title}-${JSON.stringify(
        topTraces.concat(botTraces).map(t => t.y?.slice(0, 3))
      )}`,
      uirevision: 'dual-plot',
      transition: { duration: 0 },
    };

    return { data: [...topTraces, ...botTraces], layout: mergedLayout };
  }, [topPlot, bottomPlot, isDark]);

  return (
    <div className="sig-ops-plot-card">
      <Plot
        data={data}
        layout={layout}
        config={plotConfig}
        useResizeHandler={true}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
}

/**
 * SingleSignalPlot — renders one plot (overlay mode, decomposition)
 */
function SingleSignalPlot({ plot, theme, height = 380 }) {
  const isDark = theme === 'dark';

  const layout = useMemo(() => {
    const backendX = plot?.layout?.xaxis || {};
    const backendY = plot?.layout?.yaxis || {};

    return {
      paper_bgcolor: isDark ? '#0f172a' : 'rgba(255,255,255,0.98)',
      plot_bgcolor: isDark ? '#1e293b' : '#f8fafc',
      font: {
        color: isDark ? '#e2e8f0' : '#1e293b',
        family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        size: 12,
      },
      xaxis: themedAxis(backendX, isDark),
      yaxis: {
        ...themedAxis(backendY, isDark),
        autorange: backendY.autorange !== undefined ? backendY.autorange : true,
      },
      margin: { t: 10, r: 20, b: 40, l: 55 },
      height,
      autosize: true,
      showlegend: true,
      legend: themedLegend(isDark),
      hoverlabel: {
        bgcolor: isDark ? '#1e293b' : '#ffffff',
        bordercolor: isDark ? '#475569' : '#e2e8f0',
        font: { color: isDark ? '#f1f5f9' : '#1e293b', size: 12 },
      },
      datarevision: `${plot.id}-${plot.title}-${JSON.stringify(plot.data?.map(t => t.y?.slice(0, 3)))}`,
      uirevision: plot.id,
      transition: { duration: 0 },
    };
  }, [plot, isDark, height]);

  const data = useMemo(() => {
    if (!plot?.data) return [];
    return plot.data.map(t => ({ ...t, line: { width: 2, ...t.line } }));
  }, [plot?.data]);

  return (
    <div className="sig-ops-plot-card">
      <div className="sig-ops-plot-title">{plot.title || 'Plot'}</div>
      <Plot
        data={data}
        layout={layout}
        config={plotConfig}
        useResizeHandler={true}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
}

/* ── Main viewer ─────────────────────────────────────────────── */

function SignalOperationsViewer({ metadata, plots, currentParams, onParamChange, onButtonClick, isUpdating }) {
  const theme = useTheme();
  const [viewMode, setViewMode] = useState('separate');

  const activeOps = metadata?.active_operations;
  const formula = metadata?.formula_display;
  const metrics = metadata?.signal_metrics;
  const presets = metadata?.presets;

  // Separate plots by ID
  const originalPlot = useMemo(() => plots?.find(p => p.id === 'original'), [plots]);
  const transformedPlot = useMemo(() => plots?.find(p => p.id === 'transformed'), [plots]);
  const decompositionPlot = useMemo(() => plots?.find(p => p.id === 'decomposition'), [plots]);

  // Overlay: merge original + transformed into single plot
  const overlayPlot = useMemo(() => {
    if (!originalPlot || !transformedPlot) return null;

    // Use the transformed plot's layout (has shared y-range) and merge data
    const originalTraces = (originalPlot.data || []).map(trace => ({
      ...trace,
      name: trace.name || 'f(t)',
      line: { ...trace.line, color: '#3b82f6', width: 2.5 },
      opacity: 1,
    }));
    const transformedTraces = (transformedPlot.data || []).filter(
      // skip the ghost overlay trace (it duplicates the original)
      trace => !(trace.opacity && trace.opacity < 1)
    );

    return {
      id: 'overlay',
      title: `f(t) vs ${formula || 'g(t)'}`,
      data: [...originalTraces, ...transformedTraces],
      layout: transformedPlot.layout,
    };
  }, [originalPlot, transformedPlot, formula]);

  const handlePresetClick = useCallback((params) => {
    if (!onParamChange) return;
    Object.entries(params).forEach(([name, value]) => {
      onParamChange(name, value);
    });
  }, [onParamChange]);

  return (
    <div className="signal-operations-viewer">
      {/* Operation badges */}
      <OperationChainBar operations={activeOps} />

      {/* Presets (top, for quick access) */}
      <PresetButtons presets={presets} onPresetClick={handlePresetClick} />

      {/* Formula */}
      <FormulaDisplay formula={formula} />

      {/* View mode toggle + plots */}
      <div className="sig-ops-plots-section">
        <div className="sig-ops-view-controls">
          <div className="sig-ops-view-toggle">
            <button
              className={`sig-ops-toggle-btn ${viewMode === 'separate' ? 'active' : ''}`}
              onClick={() => setViewMode('separate')}
            >
              Separate
            </button>
            <button
              className={`sig-ops-toggle-btn ${viewMode === 'overlay' ? 'active' : ''}`}
              onClick={() => setViewMode('overlay')}
            >
              Overlay
            </button>
          </div>
        </div>

        {viewMode === 'separate' ? (
          originalPlot && transformedPlot && (
            <DualSignalPlot topPlot={originalPlot} bottomPlot={transformedPlot} theme={theme} />
          )
        ) : (
          overlayPlot && <SingleSignalPlot plot={overlayPlot} theme={theme} height={300} />
        )}

        {/* Decomposition plot (below, when active) */}
        {decompositionPlot && (
          <SingleSignalPlot plot={decompositionPlot} theme={theme} height={260} />
        )}
      </div>

      {/* Metrics */}
      <MetricsPanel metrics={metrics} />
    </div>
  );
}

export default SignalOperationsViewer;
