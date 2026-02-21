import React, { useMemo } from 'react';
import PlotDisplay from './PlotDisplay';
import '../styles/ResonanceAnatomyViewer.css';

const COLORS = {
  omega0: '#f59e0b',
  omegaD: '#3b82f6',
  omegaPeak: '#ef4444',
  zeta: '#14b8a6',
  underdamped: '#3b82f6',
  undamped: '#06b6d4',
  critically_damped: '#f59e0b',
  overdamped: '#ef4444',
};

function ResonanceAnatomyViewer({ metadata, plots }) {
  const systemInfo = metadata?.system_info || {};
  const equations = metadata?.equations || {};

  const omega0 = systemInfo.omega_0;
  const omegaD = systemInfo.omega_d;
  const omegaPeak = systemInfo.omega_peak;
  const zeta = systemInfo.zeta;
  const dampingType = systemInfo.damping_type;

  const magnitudePlot = useMemo(
    () => plots?.filter(p => p.id === 'magnitude_response') || [],
    [plots]
  );
  const sPlanePlot = useMemo(
    () => plots?.filter(p => p.id === 's_plane') || [],
    [plots]
  );
  const impulsePlot = useMemo(
    () => plots?.filter(p => p.id === 'impulse_response') || [],
    [plots]
  );

  const dampingColor = COLORS[dampingType] || 'var(--text-secondary)';
  const dampingLabel = useMemo(() => {
    const labels = {
      undamped: 'Undamped',
      underdamped: 'Underdamped',
      critically_damped: 'Critically Damped',
      overdamped: 'Overdamped',
    };
    return labels[dampingType] || dampingType || '--';
  }, [dampingType]);

  const isOscillatory = dampingType === 'undamped' || dampingType === 'underdamped';
  const hasPeak = omegaPeak != null;

  return (
    <div className="ra-viewer">
      {/* Equation Banner */}
      <div className="ra-equation-banner">
        <div className="ra-hs-expression">
          <span className="ra-label">H(s) =</span>
          <span className="ra-expression">{equations.transfer_function || '--'}</span>
        </div>
        <div className="ra-param-values">
          <span>Poles: {equations.poles_str || '--'}</span>
        </div>
      </div>

      {/* Info Cards */}
      <div className="ra-info-row">
        <div className="ra-info-card" style={{ borderLeftColor: COLORS.omega0 }}>
          <span className="ra-card-label">{'\u03c9\u2080'} (natural)</span>
          <span className="ra-card-value" style={{ color: COLORS.omega0 }}>
            {omega0 != null ? `${omega0.toFixed(3)} rad/s` : '--'}
          </span>
          <span className="ra-card-note">{'\u221a'}(K/M)</span>
        </div>

        <div
          className={`ra-info-card ${!isOscillatory ? 'ra-info-card--inactive' : ''}`}
          style={{ borderLeftColor: isOscillatory ? COLORS.omegaD : 'var(--border-color)' }}
        >
          <span className="ra-card-label">{'\u03c9_d'} (damped)</span>
          <span className="ra-card-value" style={{ color: isOscillatory ? COLORS.omegaD : 'var(--text-muted)' }}>
            {omegaD != null ? `${omegaD.toFixed(3)} rad/s` : '--'}
          </span>
          <span className="ra-card-note">
            {isOscillatory ? '\u221a(\u03c9\u2080\u00b2 \u2212 \u03c3\u00b2)' : '\u03b6 \u2265 1'}
          </span>
        </div>

        <div
          className={`ra-info-card ${!hasPeak ? 'ra-info-card--inactive' : ''}`}
          style={{ borderLeftColor: hasPeak ? COLORS.omegaPeak : 'var(--border-color)' }}
        >
          <span className="ra-card-label">{'\u03c9_peak'} (resonance)</span>
          <span className="ra-card-value" style={{ color: hasPeak ? COLORS.omegaPeak : 'var(--text-muted)' }}>
            {omegaPeak != null ? `${omegaPeak.toFixed(3)} rad/s` : '--'}
          </span>
          <span className="ra-card-note">
            {hasPeak ? '\u221a(\u03c9\u2080\u00b2 \u2212 2\u03c3\u00b2)' : '\u03b6 \u2265 1/\u221a2'}
          </span>
        </div>

        <div className="ra-info-card" style={{ borderLeftColor: COLORS.zeta }}>
          <span className="ra-card-label">{'\u03b6'} (damping ratio)</span>
          <span className="ra-card-value" style={{ color: COLORS.zeta }}>
            {zeta != null ? zeta.toFixed(4) : '--'}
          </span>
          <span className="ra-card-note">B / (2{'\u221a'}(MK))</span>
        </div>

        <div className="ra-info-card" style={{ borderLeftColor: dampingColor }}>
          <span className="ra-card-label">Damping Type</span>
          <span className="ra-card-value">
            <span className="ra-damping-badge" style={{ background: dampingColor + '22', color: dampingColor }}>
              {dampingLabel}
            </span>
          </span>
        </div>
      </div>

      {/* Frequency Relationship Bar */}
      {dampingType === 'overdamped' || dampingType === 'critically_damped' ? (
        <div className="ra-frequency-bar ra-frequency-bar--overdamped">
          <span className="ra-freq-status">
            System {dampingLabel.toLowerCase()} {'\u2014'} no oscillation frequencies
          </span>
        </div>
      ) : (
        <div className="ra-frequency-bar">
          {hasPeak ? (
            <>
              <span className="ra-freq-value" style={{ color: COLORS.omegaPeak }}>
                {'\u03c9_peak'} = {omegaPeak?.toFixed(3)}
              </span>
              <span className="ra-freq-lte">{'\u2264'}</span>
            </>
          ) : (
            <span className="ra-freq-absent">
              {'\u03c9_peak'} DNE ({'\u03b6'} {'\u2265'} 1/{'\u221a'}2)
            </span>
          )}
          <span className="ra-freq-value" style={{ color: COLORS.omegaD }}>
            {'\u03c9_d'} = {omegaD?.toFixed(3) || '--'}
          </span>
          <span className="ra-freq-lte">{'\u2264'}</span>
          <span className="ra-freq-value" style={{ color: COLORS.omega0 }}>
            {'\u03c9\u2080'} = {omega0?.toFixed(3) || '--'}
          </span>
        </div>
      )}

      {/* Magnitude Response (full width, main plot) */}
      <div className="ra-plot-magnitude">
        <PlotDisplay plots={magnitudePlot} isLoading={false} />
      </div>

      {/* S-Plane and Impulse Response side-by-side */}
      <div className="ra-plots-row">
        <div className="ra-plot-splane">
          <PlotDisplay plots={sPlanePlot} isLoading={false} />
        </div>
        <div className="ra-plot-impulse">
          <PlotDisplay plots={impulsePlot} isLoading={false} />
        </div>
      </div>
    </div>
  );
}

export default ResonanceAnatomyViewer;
