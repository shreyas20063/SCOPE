/**
 * ComplexPolesModesViewer
 *
 * Custom viewer for the Complex Poles & Sinusoidal Modes simulation.
 * Shows system info banner, pole cards, s-plane, mode decomposition,
 * Taylor series convergence, and a 3D helix of the complex exponential.
 *
 * The 3D helix uses Plotly scatter3d directly (not PlotDisplay) because
 * PlotDisplay's layout merge doesn't support the `scene` property.
 */

import React, { useMemo, useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import PlotDisplay from './PlotDisplay';
import '../styles/ComplexPolesModesViewer.css';

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

function ComplexPolesModesViewer({ metadata, plots, isUpdating }) {
  const theme = useTheme();
  const isDark = theme === 'dark';

  const systemInfo = metadata?.system_info;
  const equations = metadata?.equations;
  const dampingType = systemInfo?.damping_type || 'undamped';
  const isOscillatory = dampingType === 'undamped' || dampingType === 'underdamped';

  // Separate plots by ID
  const splanePlot = useMemo(() => plots?.filter(p => p.id === 's_plane') || [], [plots]);
  const modesPlot = useMemo(() => plots?.filter(p => p.id === 'mode_decomposition') || [], [plots]);
  const taylorPlot = useMemo(() => plots?.filter(p => p.id === 'taylor_convergence') || [], [plots]);
  const helixPlot = useMemo(() => plots?.find(p => p.id === 'helix_3d'), [plots]);

  // Format pole for display
  const formatPole = (pole) => {
    if (!pole) return '—';
    const r = pole.real;
    const i = pole.imag;
    if (Math.abs(i) < 0.0001) return `${r.toFixed(3)}`;
    const sign = i >= 0 ? '+' : '−';
    return `${r.toFixed(3)} ${sign} j${Math.abs(i).toFixed(3)}`;
  };

  // Damping label
  const dampingLabel = {
    undamped: 'Undamped',
    underdamped: 'Underdamped',
    critically_damped: 'Critically Damped',
    overdamped: 'Overdamped',
  }[dampingType] || dampingType;

  return (
    <div className="complex-poles-modes-viewer">
      {/* Equation Banner */}
      {equations && (
        <div className="cpm-equation-banner" role="status" aria-live="polite">
          <span className="cpm-equation-text">{equations.ode}</span>
          <span className="cpm-equation-divider" />
          <span className="cpm-equation-impulse">{equations.impulse_response}</span>
        </div>
      )}

      {/* System Values + Damping Badge */}
      {systemInfo && (
        <div className="cpm-system-values">
          <div className="cpm-value-item">
            <span className="cpm-value-label">&#969;&#8320;</span>
            <span className="cpm-value-number">{systemInfo.omega_0} rad/s</span>
          </div>
          <div className="cpm-value-item">
            <span className="cpm-value-label">&#963;</span>
            <span className="cpm-value-number">{systemInfo.sigma}</span>
          </div>
          {systemInfo.omega_d != null && (
            <div className="cpm-value-item">
              <span className="cpm-value-label">&#969;d</span>
              <span className="cpm-value-number">{systemInfo.omega_d} rad/s</span>
            </div>
          )}
          <div className="cpm-value-item">
            <span className="cpm-value-label">&#950;</span>
            <span className="cpm-value-number">{systemInfo.zeta}</span>
          </div>
          {systemInfo.period != null && (
            <div className="cpm-value-item">
              <span className="cpm-value-label">T</span>
              <span className="cpm-value-number">{systemInfo.period} s</span>
            </div>
          )}
          <span className={`cpm-damping-badge ${dampingType}`}>{dampingLabel}</span>
        </div>
      )}

      {/* Pole Cards */}
      {systemInfo && (
        <div className="cpm-pole-cards" role="list" aria-label="System poles">
          <div className="cpm-pole-card pole-s1" role="listitem">
            <div className="cpm-pole-header">
              <span className="cpm-pole-dot" style={{ backgroundColor: '#3b82f6' }} />
              <span className="cpm-pole-label">Pole s&#8321;</span>
            </div>
            <span className="cpm-pole-value">{formatPole(systemInfo.pole_s1)}</span>
          </div>
          <div className="cpm-pole-card pole-s2" role="listitem">
            <div className="cpm-pole-header">
              <span className="cpm-pole-dot" style={{ backgroundColor: '#ef4444' }} />
              <span className="cpm-pole-label">Pole s&#8322;</span>
            </div>
            <span className="cpm-pole-value">{formatPole(systemInfo.pole_s2)}</span>
          </div>
        </div>
      )}

      {/* Top Row: S-Plane + Mode Decomposition */}
      <div className="cpm-plots-row">
        <div className="cpm-plot-splane">
          <PlotDisplay plots={splanePlot} isLoading={false} />
        </div>
        <div className="cpm-plot-modes">
          <PlotDisplay plots={modesPlot} isLoading={false} />
        </div>
      </div>

      {/* Bottom Row: Taylor + 3D Helix (only for oscillatory systems) */}
      {isOscillatory ? (
        <div className="cpm-plots-row">
          <div className="cpm-plot-taylor">
            <PlotDisplay plots={taylorPlot} isLoading={false} />
          </div>
          <div className="cpm-plot-helix">
            {helixPlot && (
              <Plot
                data={helixPlot.data || []}
                layout={{
                  ...helixPlot.layout,
                  paper_bgcolor: isDark ? 'rgba(0,0,0,0)' : 'rgba(255,255,255,0.98)',
                  font: {
                    family: 'Inter, sans-serif',
                    size: 12,
                    color: isDark ? '#e2e8f0' : '#1e293b',
                  },
                  title: {
                    text: helixPlot.title || '3D Helix',
                    font: { color: isDark ? '#f1f5f9' : '#1e293b', size: 14 },
                    x: 0.5,
                    xanchor: 'center',
                  },
                  scene: {
                    ...helixPlot.layout?.scene,
                    xaxis: {
                      ...helixPlot.layout?.scene?.xaxis,
                      titlefont: { color: isDark ? '#94a3b8' : '#475569', size: 11 },
                      tickfont: { color: isDark ? '#94a3b8' : '#475569', size: 10 },
                    },
                    yaxis: {
                      ...helixPlot.layout?.scene?.yaxis,
                      titlefont: { color: isDark ? '#94a3b8' : '#475569', size: 11 },
                      tickfont: { color: isDark ? '#94a3b8' : '#475569', size: 10 },
                    },
                    zaxis: {
                      ...helixPlot.layout?.scene?.zaxis,
                      titlefont: { color: isDark ? '#94a3b8' : '#475569', size: 11 },
                      tickfont: { color: isDark ? '#94a3b8' : '#475569', size: 10 },
                    },
                  },
                  legend: {
                    ...helixPlot.layout?.legend,
                    font: {
                      size: 11,
                      color: isDark ? '#94a3b8' : '#475569',
                    },
                  },
                  height: 380,
                  uirevision: helixPlot.layout?.uirevision || `helix_${metadata?.system_info?.damping_type}`,
                  datarevision: `helix-${helixPlot.title}-${Date.now()}`,
                }}
                config={{
                  responsive: true,
                  displayModeBar: true,
                  modeBarButtonsToRemove: ['lasso2d', 'select2d'],
                  displaylogo: false,
                }}
                useResizeHandler={true}
                style={{ width: '100%', height: '380px' }}
              />
            )}
          </div>
        </div>
      ) : (
        <div className="cpm-plots-row">
          <div className="cpm-no-oscillation" style={{ flex: 1 }}>
            <div className="cpm-no-oscillation-content">
              <span className="cpm-no-oscillation-icon">
                {dampingType === 'critically_damped' ? '&#9878;' : '&#128680;'}
              </span>
              <strong>{dampingLabel}</strong>
              <span className="cpm-no-oscillation-text">
                {dampingType === 'critically_damped'
                  ? 'Repeated real pole — no sinusoidal oscillation. Taylor series and 3D helix are not applicable.'
                  : 'Two distinct real poles — no sinusoidal oscillation. Reduce damping (b) to see complex conjugate poles.'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ComplexPolesModesViewer;
