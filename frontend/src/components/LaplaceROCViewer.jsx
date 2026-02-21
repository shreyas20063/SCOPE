/**
 * LaplaceROCViewer
 *
 * Custom viewer for the Laplace Transform & s-Plane ROC Explorer simulation.
 * Shows H(s) expression, ROC/causality/stability info cards,
 * split s-plane + time-domain plots, and optional convergence plot.
 * CT twin of ZTransformROCViewer.
 */

import React, { useMemo } from 'react';
import PlotDisplay from './PlotDisplay';
import '../styles/LaplaceROCViewer.css';

function LaplaceROCViewer({ metadata, plots, currentParams, onParamChange, onButtonClick, isUpdating }) {
  // Filter plots by ID for custom layout
  const sPlanePlot = useMemo(() => plots?.filter(p => p.id === 's_plane') || [], [plots]);
  const timeDomainPlot = useMemo(() => plots?.filter(p => p.id === 'time_domain') || [], [plots]);
  const convergencePlot = useMemo(() => plots?.filter(p => p.id === 'convergence') || [], [plots]);

  const showConvergence = convergencePlot.length > 0 && convergencePlot[0]?.data?.length > 0;

  const causalityColor = useMemo(() => {
    const colors = {
      'Causal': 'var(--success-color)',
      'Anti-causal': 'var(--error-color)',
      'Two-sided': 'var(--warning-color)',
    };
    return colors[metadata?.causality] || 'var(--text-secondary)';
  }, [metadata?.causality]);

  const stabilityColor = metadata?.is_stable ? 'var(--success-color)' : 'var(--error-color)';

  return (
    <div className="lt-roc-viewer">
      {/* H(s) expression banner */}
      {metadata?.hs_expression && (
        <div className="lt-equation-banner">
          <div className="lt-hs-expression">
            <span className="lt-label">H(s) =</span>
            <span className="lt-expression">{metadata.hs_expression}</span>
          </div>
          <div className="lt-roc-text">
            <span className="lt-label">ROC:</span>
            <span className="lt-expression">{metadata.roc_description}</span>
          </div>
        </div>
      )}

      {/* Info cards row */}
      <div className="lt-info-row">
        <div className="lt-info-cards">
          {/* Causality card */}
          <div className="lt-info-card" style={{ borderLeftColor: causalityColor }}>
            <span className="lt-card-label">Causality</span>
            <span className="lt-card-value" style={{ color: causalityColor }}>
              {metadata?.causality || '\u2014'}
            </span>
          </div>

          {/* Stability card */}
          <div className="lt-info-card" style={{ borderLeftColor: stabilityColor }}>
            <span className="lt-card-label">Stability</span>
            <span className="lt-card-value" style={{ color: stabilityColor }}>
              {metadata?.stability_text || '\u2014'}
            </span>
          </div>

          {/* Poles card */}
          <div className="lt-info-card" style={{ borderLeftColor: '#ef4444' }}>
            <span className="lt-card-label">Poles</span>
            <span className="lt-card-value">
              {metadata?.poles?.map((p, i) => (
                <span key={i} className="lt-pole-value">
                  s = {Math.abs(p.imag) < 1e-6
                    ? p.real.toFixed(3)
                    : `${p.real.toFixed(2)} ${p.imag >= 0 ? '+' : '\u2212'} ${Math.abs(p.imag).toFixed(2)}j`}
                  {i < metadata.poles.length - 1 ? ',  ' : ''}
                </span>
              )) || '\u2014'}
            </span>
          </div>
        </div>
      </div>

      {/* Split view: s-plane (left) + x(t) waveform (right) */}
      <div className="lt-plots-row">
        <div className="lt-plot-splane">
          <PlotDisplay plots={sPlanePlot} isLoading={false} />
        </div>
        <div className="lt-plot-time">
          <PlotDisplay plots={timeDomainPlot} isLoading={false} />
        </div>
      </div>

      {/* Convergence plot (full width, conditional) */}
      {showConvergence && (
        <div className="lt-plot-convergence">
          <PlotDisplay plots={convergencePlot} isLoading={false} />
        </div>
      )}
    </div>
  );
}

export default LaplaceROCViewer;
