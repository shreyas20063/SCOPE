/**
 * ConvolutionViewer Component
 *
 * Custom viewer for Convolution Simulator visualization.
 * Controls are handled by the ControlPanel.
 * This component displays:
 * - Signal info panel (x, h expressions and current y value)
 * - 4 vertically stacked plots showing convolution steps
 * - Formula display footer
 */

import React, { memo } from 'react';
import Plot from 'react-plotly.js';
import '../styles/ConvolutionViewer.css';

/**
 * Formula Display Footer
 */
const FormulaFooter = memo(function FormulaFooter({ mode, formula }) {
  const defaultFormula = mode === 'continuous'
    ? 'y(t) = ∫ x(τ)h(t-τ)dτ'
    : 'y[n] = Σ x[k]h[n-k]';

  return (
    <div className="conv-formula-footer">
      <span className="conv-formula">{formula || defaultFormula}</span>
      <span className="conv-credit">Signals & Systems - Convolution Simulator</span>
    </div>
  );
});

/**
 * Plot Stack - Shows 4 convolution steps
 */
const PlotStack = memo(function PlotStack({ plots }) {
  if (!plots || plots.length === 0) {
    return (
      <div className="conv-loading">
        <div className="conv-loading-spinner"></div>
        <p>Loading plots...</p>
      </div>
    );
  }

  // Plot IDs in order for convolution visualization
  const plotOrder = ['signal_x', 'signal_h', 'product', 'result'];
  const orderedPlots = plotOrder
    .map(id => plots.find(p => p.id === id))
    .filter(Boolean);

  return (
    <div className="conv-plot-stack">
      {orderedPlots.map((plot) => (
        <div key={plot.id} className={`conv-plot-row ${plot.id}`}>
          <Plot
            data={plot.data}
            layout={{
              ...plot.layout,
              autosize: true,
              height: 160,
              margin: { l: 50, r: 20, t: 35, b: 30 },
            }}
            config={{
              responsive: true,
              displayModeBar: false,
              staticPlot: false
            }}
            style={{ width: '100%', height: '100%' }}
          />
        </div>
      ))}
    </div>
  );
});

/**
 * Signal Info Panel
 */
const SignalInfo = memo(function SignalInfo({ metadata, currentParams }) {
  const mode = currentParams?.mode || metadata?.mode || 'continuous';
  const varName = mode === 'continuous' ? 't' : 'n';
  const timeLabel = mode === 'continuous' ? 't₀' : 'n₀';
  const timeValue = currentParams?.time_shift ?? 0;

  return (
    <div className="conv-signal-info">
      <div className="conv-info-item">
        <span className="conv-info-label">x({varName}):</span>
        <span className="conv-info-value x">{metadata?.x_expr || '—'}</span>
      </div>
      <div className="conv-info-item">
        <span className="conv-info-label">h({varName}):</span>
        <span className="conv-info-value h">{metadata?.h_expr || '—'}</span>
      </div>
      <div className="conv-info-item time">
        <span className="conv-info-label">{timeLabel}:</span>
        <span className="conv-info-value">{mode === 'continuous' ? timeValue.toFixed(2) : Math.round(timeValue)}</span>
      </div>
      {metadata?.current_value !== undefined && (
        <div className="conv-info-item result">
          <span className="conv-info-label">y({timeLabel}):</span>
          <span className="conv-info-value y">{metadata.current_value?.toFixed(4) || '—'}</span>
        </div>
      )}
    </div>
  );
});

/**
 * Main ConvolutionViewer Component
 */
function ConvolutionViewer({ metadata, plots, currentParams }) {
  const mode = currentParams?.mode || metadata?.mode || 'continuous';

  // Empty state
  if (!metadata && !plots) {
    return (
      <div className="conv-viewer-empty">
        <div className="conv-loading-spinner"></div>
        <p>Loading Convolution Simulator...</p>
      </div>
    );
  }

  return (
    <div className="convolution-viewer">
      {/* Signal info */}
      <SignalInfo metadata={metadata} currentParams={currentParams} />

      {/* Plot stack */}
      <PlotStack plots={plots} />

      {/* Formula footer */}
      <FormulaFooter mode={mode} formula={metadata?.formula} />
    </div>
  );
}

export default memo(ConvolutionViewer);
