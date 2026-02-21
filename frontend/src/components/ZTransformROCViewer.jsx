/**
 * ZTransformROCViewer
 *
 * Custom viewer for the Z Transform & ROC Explorer simulation.
 * Shows H(z) expression, ROC/causality/stability info cards,
 * split z-plane + time-domain plots, and optional convergence plot.
 */

import React, { useMemo } from 'react';
import PlotDisplay from './PlotDisplay';
import '../styles/ZTransformROCViewer.css';

function ZTransformROCViewer({ metadata, plots, currentParams, onParamChange, onButtonClick, isUpdating }) {
  // Filter plots by ID for custom layout
  const zPlanePlot = useMemo(() => plots?.filter(p => p.id === 'z_plane') || [], [plots]);
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
    <div className="zt-roc-viewer">
      {/* H(z) expression banner */}
      {metadata?.hz_expression && (
        <div className="zt-equation-banner">
          <div className="zt-hz-expression">
            <span className="zt-label">H(z) =</span>
            <span className="zt-expression">{metadata.hz_expression}</span>
          </div>
          <div className="zt-roc-text">
            <span className="zt-label">ROC:</span>
            <span className="zt-expression">{metadata.roc_description}</span>
          </div>
        </div>
      )}

      {/* Info cards row */}
      <div className="zt-info-row">
        <div className="zt-info-cards">
          {/* Causality card */}
          <div className="zt-info-card" style={{ borderLeftColor: causalityColor }}>
            <span className="zt-card-label">Causality</span>
            <span className="zt-card-value" style={{ color: causalityColor }}>
              {metadata?.causality || '—'}
            </span>
          </div>

          {/* Stability card */}
          <div className="zt-info-card" style={{ borderLeftColor: stabilityColor }}>
            <span className="zt-card-label">Stability</span>
            <span className="zt-card-value" style={{ color: stabilityColor }}>
              {metadata?.stability_text || '—'}
            </span>
          </div>

          {/* Poles card */}
          <div className="zt-info-card" style={{ borderLeftColor: '#ef4444' }}>
            <span className="zt-card-label">Poles</span>
            <span className="zt-card-value">
              {metadata?.poles?.map((p, i) => (
                <span key={i} className="zt-pole-value">
                  {Math.abs(p.imag) < 1e-6
                    ? p.real.toFixed(3)
                    : `${p.real.toFixed(2)} ${p.imag >= 0 ? '+' : '-'} ${Math.abs(p.imag).toFixed(2)}j`}
                  {i < metadata.poles.length - 1 ? ',  ' : ''}
                </span>
              )) || '—'}
            </span>
          </div>
        </div>
      </div>

      {/* Split view: Z-plane (left) + Stem plot (right) */}
      <div className="zt-plots-row">
        <div className="zt-plot-zplane">
          <PlotDisplay plots={zPlanePlot} isLoading={false} />
        </div>
        <div className="zt-plot-time">
          <PlotDisplay plots={timeDomainPlot} isLoading={false} />
        </div>
      </div>

      {/* Convergence plot (full width, conditional) */}
      {showConvergence && (
        <div className="zt-plot-convergence">
          <PlotDisplay plots={convergencePlot} isLoading={false} />
        </div>
      )}
    </div>
  );
}

export default ZTransformROCViewer;
