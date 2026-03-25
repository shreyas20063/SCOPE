/**
 * BallBeam3DViewer — Full viewer with 3D animation + analysis plots.
 *
 * Layout: 3D viewport on top, analysis plots below in a grid.
 * Receives metadata from backend containing animation data, controller info, and metrics.
 */

import React, { useMemo, lazy, Suspense } from 'react';
import Plot from 'react-plotly.js';
import '../styles/BallBeam3D.css';

const BallBeam3D = lazy(() => import('./BallBeam3D'));

function BallBeam3DViewer({ metadata, plots }) {
  const animation = metadata?.animation;
  const controllerInfo = metadata?.controller_info || {};
  const metrics = metadata?.metrics || {};
  const isStable = metrics.is_stable ?? false;

  const isDark = useMemo(() => {
    return document.documentElement.getAttribute('data-theme') !== 'light';
  }, []);

  // Format eigenvalues for display
  const formatEig = (eig) => {
    if (!eig) return '\u2014';
    const re = typeof eig === 'object' ? eig.re ?? eig[0] : (typeof eig === 'number' ? eig : parseFloat(eig));
    const im = typeof eig === 'object' ? eig.im ?? eig[1] : 0;
    if (typeof re !== 'number' || isNaN(re)) return String(eig);
    const reStr = re.toFixed(2);
    if (Math.abs(im) < 0.001) return reStr;
    const imStr = Math.abs(im).toFixed(2);
    return `${reStr} ${im >= 0 ? '+' : '\u2212'} ${imStr}j`;
  };

  const formatComplexArray = (arr) => {
    if (!arr || !Array.isArray(arr)) return '\u2014';
    return arr.map(formatEig).join(', ');
  };

  // Enrich plots with dark theme
  const enrichedPlots = useMemo(() => {
    if (!plots) return [];
    return plots.map(plot => ({
      ...plot,
      layout: {
        ...plot.layout,
        paper_bgcolor: isDark ? '#0a0e27' : 'rgba(255,255,255,0.98)',
        plot_bgcolor: isDark ? '#131b2e' : '#f8fafc',
      },
    }));
  }, [plots, isDark]);

  return (
    <div className="bb3d-viewer">
      {/* 3D Viewport */}
      <div className="bb3d-viewport-section">
        <Suspense fallback={<div className="bb3d-loading">Loading 3D...</div>}>
          {animation && (
            <BallBeam3D
              animation={animation}
              isStable={isStable}
            />
          )}
        </Suspense>
      </div>

      {/* Metrics Strip */}
      <div className="bb3d-metrics-strip">
        <div className="bb3d-metric">
          <span className="bb3d-metric-label">Controller</span>
          <span className="bb3d-metric-value">{controllerInfo.type?.toUpperCase() || '\u2014'}</span>
        </div>
        <div className="bb3d-metric">
          <span className="bb3d-metric-label">Stability</span>
          <span className={`bb3d-metric-value ${isStable ? 'stable' : 'unstable'}`}>
            {isStable ? 'Stable' : 'Unstable'}
          </span>
        </div>
        {metrics.rise_time != null && metrics.rise_time !== Infinity && (
          <div className="bb3d-metric">
            <span className="bb3d-metric-label">Rise Time</span>
            <span className="bb3d-metric-value">{metrics.rise_time.toFixed(3)}s</span>
          </div>
        )}
        {metrics.settling_time != null && metrics.settling_time !== Infinity && (
          <div className="bb3d-metric">
            <span className="bb3d-metric-label">Settling</span>
            <span className="bb3d-metric-value">{metrics.settling_time.toFixed(3)}s</span>
          </div>
        )}
        {metrics.overshoot != null && (
          <div className="bb3d-metric">
            <span className="bb3d-metric-label">Overshoot</span>
            <span className="bb3d-metric-value">{metrics.overshoot.toFixed(1)}%</span>
          </div>
        )}
        {metrics.control_energy != null && (
          <div className="bb3d-metric">
            <span className="bb3d-metric-label">Energy</span>
            <span className="bb3d-metric-value">{metrics.control_energy.toFixed(1)}</span>
          </div>
        )}
        {controllerInfo.controllability_rank != null && (
          <div className="bb3d-metric">
            <span className="bb3d-metric-label">Controllability</span>
            <span className={`bb3d-metric-value ${controllerInfo.is_controllable ? 'stable' : 'unstable'}`}>
              rank {controllerInfo.controllability_rank}/4
            </span>
          </div>
        )}
      </div>

      {/* Controller Details (collapsible) */}
      {controllerInfo.K && (
        <details className="bb3d-controller-details">
          <summary>Controller Details</summary>
          <div className="bb3d-details-content">
            {controllerInfo.K && (
              <div className="bb3d-detail-row">
                <span className="bb3d-detail-label">K =</span>
                <span className="bb3d-detail-value bb3d-mono">
                  [{controllerInfo.K.flat().map(v => v.toFixed(3)).join(', ')}]
                </span>
              </div>
            )}
            {controllerInfo.cl_eigenvalues && (
              <div className="bb3d-detail-row">
                <span className="bb3d-detail-label">CL Eigenvalues</span>
                <span className="bb3d-detail-value bb3d-mono">
                  {formatComplexArray(controllerInfo.cl_eigenvalues)}
                </span>
              </div>
            )}
            {controllerInfo.L && (
              <div className="bb3d-detail-row">
                <span className="bb3d-detail-label">L (observer) =</span>
                <span className="bb3d-detail-value bb3d-mono">
                  [{controllerInfo.L.flat().map(v => v.toFixed(3)).join(', ')}]
                </span>
              </div>
            )}
            {controllerInfo.est_eigenvalues && (
              <div className="bb3d-detail-row">
                <span className="bb3d-detail-label">Estimator Eigs</span>
                <span className="bb3d-detail-value bb3d-mono">
                  {formatComplexArray(controllerInfo.est_eigenvalues)}
                </span>
              </div>
            )}
            {controllerInfo.desired_poles && (
              <div className="bb3d-detail-row">
                <span className="bb3d-detail-label">Desired Poles</span>
                <span className="bb3d-detail-value bb3d-mono">
                  {controllerInfo.desired_poles.map(v => v.toFixed(2)).join(', ')}
                </span>
              </div>
            )}
          </div>
        </details>
      )}

      {/* Analysis Plots Grid */}
      <div className="bb3d-plots-grid">
        {enrichedPlots.map(plot => (
          <div key={plot.id} className="bb3d-plot-cell">
            <Plot
              data={plot.data || []}
              layout={{
                ...plot.layout,
                autosize: true,
                datarevision: plot.layout?.datarevision || `${plot.id}-${Date.now()}`,
                uirevision: plot.layout?.uirevision || plot.id,
              }}
              config={{ responsive: true, displayModeBar: false }}
              useResizeHandler
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

export default BallBeam3DViewer;
