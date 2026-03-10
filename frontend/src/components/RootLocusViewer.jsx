/**
 * RootLocusViewer
 *
 * Custom viewer for the Root Locus Analyzer simulation.
 * Multi-panel layout: s-plane root locus (main), step response,
 * performance metrics, special points, and performance-vs-K sweep.
 *
 * Features:
 * - Click on s-plane to select K at that point
 * - Import TF from Block Diagram Builder (localStorage bridge)
 * - Full metrics panel with stability, damping, margins
 * - Closed-loop pole readout
 * - Responsive: grid on desktop, tabs on mobile
 */

import React, { useState, useCallback, useMemo, useEffect } from 'react';
import Plot from 'react-plotly.js';
import PlotDisplay from './PlotDisplay';
import '../styles/RootLocusViewer.css';

/* ======================================================================
   Theme hook
   ====================================================================== */
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

/* ======================================================================
   Sub-components
   ====================================================================== */

function TransferFunctionBanner({ metadata, onImport }) {
  const tf = metadata?.transfer_function;
  const stability = metadata?.stability;
  const error = metadata?.error;

  const stabilityStyles = {
    stable: { bg: 'rgba(16, 185, 129, 0.15)', color: '#10b981', label: 'Stable' },
    marginally_stable: { bg: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', label: 'Marginal' },
    unstable: { bg: 'rgba(239, 68, 68, 0.15)', color: '#ef4444', label: 'Unstable' },
  };
  const stab = stabilityStyles[stability] || stabilityStyles.stable;

  return (
    <div className="rl-tf-banner">
      <div className="rl-tf-display">
        <span className="rl-tf-label">G(s) =</span>
        <div className="rl-tf-fraction">
          <span className="rl-tf-num">{tf?.num_display || '1'}</span>
          <span className="rl-tf-line" />
          <span className="rl-tf-den">{tf?.den_display || '1'}</span>
        </div>
      </div>

      <div className="rl-tf-badges">
        <span className="rl-stability-badge" style={{ background: stab.bg, color: stab.color }}>
          {stab.label}
        </span>
        {tf?.system_type != null && (
          <span className="rl-type-badge">Type {tf.system_type}</span>
        )}
        {tf?.order != null && (
          <span className="rl-order-badge">Order {tf.order}</span>
        )}
        <button className="rl-import-btn" onClick={onImport} title="Import TF from Block Diagram Builder">
          Import from BDB
        </button>
      </div>

      {error && <div className="rl-error-banner">{error}</div>}
    </div>
  );
}

function CLPolesReadout({ clPoles, stability }) {
  if (!clPoles || clPoles.length === 0) return null;

  const formatPole = (p) => {
    const re = p.real?.toFixed(3);
    const im = p.imag;
    if (Math.abs(im) < 0.001) return `${re}`;
    const sign = im >= 0 ? '+' : '-';
    return `${re} ${sign} ${Math.abs(im).toFixed(3)}j`;
  };

  return (
    <div className="rl-cl-poles">
      <div className="rl-cl-poles-heading">Closed-Loop Poles</div>
      <div className="rl-cl-poles-list">
        {clPoles.map((p, i) => {
          const isUnstable = p.real > 0.001;
          return (
            <span key={i} className={`rl-cl-pole-chip ${isUnstable ? 'unstable' : 'stable'}`}>
              {formatPole(p)}
            </span>
          );
        })}
      </div>
    </div>
  );
}

function MetricsPanel({ metrics, currentK, stability }) {
  const fmt = (val, dec = 3) => {
    if (val == null) return '—';
    if (typeof val !== 'number' || !isFinite(val)) return val == null ? '—' : '∞';
    return val.toFixed(dec);
  };

  const cards = [
    { label: 'Gain K', value: fmt(currentK, 2), unit: '', color: '#f59e0b' },
    { label: 'Damping ζ', value: fmt(metrics?.damping_ratio), unit: '', color: '#3b82f6' },
    { label: 'Nat. Freq ωₙ', value: fmt(metrics?.natural_freq), unit: 'rad/s', color: '#10b981' },
    { label: 'Overshoot', value: fmt(metrics?.percent_overshoot, 1), unit: '%', color: '#ef4444' },
    { label: 'Settling', value: fmt(metrics?.settling_time, 2), unit: 's', color: '#8b5cf6' },
    { label: 'Rise Time', value: fmt(metrics?.rise_time, 2), unit: 's', color: '#06b6d4' },
    { label: 'Gain Margin', value: fmt(metrics?.gain_margin_db, 1), unit: 'dB', color: '#14b8a6' },
    { label: 'Phase Margin', value: fmt(metrics?.phase_margin_deg, 1), unit: '°', color: '#ec4899' },
  ];

  // Add SS error if present
  if (metrics?.steady_state_error != null) {
    cards.push({ label: 'SS Error', value: fmt(metrics.steady_state_error, 4), unit: '', color: '#94a3b8' });
  }

  return (
    <div className="rl-metrics-grid">
      {cards.map((card, i) => (
        <div key={i} className="rl-metric-card" style={{ borderLeftColor: card.color }}>
          <div className="rl-metric-value">
            {card.value}
            {card.unit && <span className="rl-metric-unit"> {card.unit}</span>}
          </div>
          <div className="rl-metric-label">{card.label}</div>
        </div>
      ))}
    </div>
  );
}

function SpecialPointsPanel({ specialPoints }) {
  const [isOpen, setIsOpen] = useState(true);
  if (!specialPoints) return null;

  const { breakaway, jw_crossings, asymptotes, departure_angles, arrival_angles } = specialPoints;
  const hasContent = (breakaway?.length > 0) || (jw_crossings?.length > 0) ||
                     (asymptotes?.angles?.length > 0) || (departure_angles?.length > 0) ||
                     (arrival_angles?.length > 0);

  if (!hasContent) return null;

  return (
    <div className="rl-special-points">
      <button className="rl-special-toggle" onClick={() => setIsOpen(!isOpen)}>
        <span>{isOpen ? '▾' : '▸'} Construction Rules</span>
      </button>
      {isOpen && (
        <div className="rl-special-content">
          {breakaway?.length > 0 && (
            <div className="rl-special-section">
              <div className="rl-special-heading">Breakaway / Break-in</div>
              {breakaway.map((bp, i) => (
                <div key={i} className="rl-special-item">
                  s = {bp.s?.real?.toFixed(3)} &nbsp;&nbsp; K = {bp.K?.toFixed(3)}
                </div>
              ))}
            </div>
          )}
          {jw_crossings?.length > 0 && (
            <div className="rl-special-section">
              <div className="rl-special-heading">jω-Axis Crossings</div>
              {jw_crossings.map((jw, i) => (
                <div key={i} className="rl-special-item">
                  ω = ±{jw.omega?.toFixed(3)} rad/s &nbsp;&nbsp; K = {jw.K?.toFixed(2)}
                </div>
              ))}
            </div>
          )}
          {asymptotes?.angles?.length > 0 && (
            <div className="rl-special-section">
              <div className="rl-special-heading">Asymptotes ({asymptotes.n} branches)</div>
              <div className="rl-special-item">
                Centroid: σ = {asymptotes.centroid?.toFixed(3)}
              </div>
              <div className="rl-special-item">
                Angles: {asymptotes.angles.map(a => `${a.toFixed(0)}°`).join(', ')}
              </div>
            </div>
          )}
          {departure_angles?.length > 0 && (
            <div className="rl-special-section">
              <div className="rl-special-heading">Departure Angles</div>
              {departure_angles.map((da, i) => (
                <div key={i} className="rl-special-item">
                  at ({da.pole?.real?.toFixed(2)} + {da.pole?.imag?.toFixed(2)}j): {da.angle_deg?.toFixed(1)}°
                </div>
              ))}
            </div>
          )}
          {arrival_angles?.length > 0 && (
            <div className="rl-special-section">
              <div className="rl-special-heading">Arrival Angles</div>
              {arrival_angles.map((aa, i) => (
                <div key={i} className="rl-special-item">
                  at ({aa.zero?.real?.toFixed(2)} + {aa.zero?.imag?.toFixed(2)}j): {aa.angle_deg?.toFixed(1)}°
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ======================================================================
   Main Component
   ====================================================================== */

export default function RootLocusViewer({
  metadata,
  plots,
  currentParams,
  onParamChange,
  onButtonClick,
  onMetadataChange,
  simId,
  isUpdating,
}) {
  const theme = useTheme();
  const isDark = theme === 'dark';
  const [activeTab, setActiveTab] = useState('splane');
  const [toastMessage, setToastMessage] = useState(null);

  // Separate plots by ID
  const splanePlot = useMemo(() => plots?.find(p => p.id === 'root_locus'), [plots]);
  const stepPlot = useMemo(() => plots?.filter(p => p.id === 'step_response') || [], [plots]);
  const perfPlot = useMemo(() => plots?.filter(p => p.id === 'performance_vs_k') || [], [plots]);

  // Extract metadata
  const metrics = metadata?.metrics;
  const specialPoints = metadata?.special_points;
  const currentK = metadata?.current_K;
  const stability = metadata?.stability;
  const clPoles = metadata?.cl_poles;

  // ====================================================================
  // Click-to-select-K on s-plane
  // ====================================================================
  const handleSplaneClick = useCallback((event) => {
    if (isUpdating) return;
    if (!event?.points?.[0]) return;

    const { x, y } = event.points[0];
    if (onButtonClick) {
      onButtonClick('click_select_k', { sigma: x, omega: y });
    }
  }, [onButtonClick, isUpdating]);

  // ====================================================================
  // Import from Block Diagram Builder
  // ====================================================================
  const handleImport = useCallback(() => {
    try {
      const stored = localStorage.getItem('blockDiagram_export');
      if (!stored) {
        setToastMessage('No diagram found. Export from Block Diagram Builder first.');
        setTimeout(() => setToastMessage(null), 3000);
        return;
      }

      const data = JSON.parse(stored);
      let num = data.numerator || data.overall_tf?.numerator;
      let den = data.denominator || data.overall_tf?.denominator;

      if (!num || !den) {
        setToastMessage('No transfer function found in exported diagram.');
        setTimeout(() => setToastMessage(null), 3000);
        return;
      }

      if (onButtonClick) {
        onButtonClick('import_tf', { numerator: num, denominator: den });
        setToastMessage('Transfer function imported!');
        setTimeout(() => setToastMessage(null), 2000);
      }
    } catch (e) {
      setToastMessage('Import failed: ' + e.message);
      setTimeout(() => setToastMessage(null), 3000);
    }
  }, [onButtonClick]);

  // ====================================================================
  // S-plane plot data with theme support
  // ====================================================================
  const splanePlotData = useMemo(() => {
    if (!splanePlot) return { data: [], layout: {} };

    const data = [...(splanePlot.data || [])];
    const layout = {
      ...(splanePlot.layout || {}),
      autosize: true,
    };

    // Light theme overrides
    if (!isDark) {
      layout.paper_bgcolor = 'rgba(255, 255, 255, 0.98)';
      layout.plot_bgcolor = '#f8fafc';
      layout.font = { ...layout.font, color: '#1e293b' };
      if (layout.xaxis) {
        layout.xaxis = {
          ...layout.xaxis,
          gridcolor: 'rgba(100, 116, 139, 0.2)',
          zerolinecolor: 'rgba(100, 116, 139, 0.5)',
        };
      }
      if (layout.yaxis) {
        layout.yaxis = {
          ...layout.yaxis,
          gridcolor: 'rgba(100, 116, 139, 0.2)',
          zerolinecolor: 'rgba(100, 116, 139, 0.5)',
        };
      }
      // Fix shapes for light theme
      if (layout.shapes) {
        layout.shapes = layout.shapes.map(s => {
          if (s.fillcolor?.includes('239, 68, 68')) {
            return { ...s, fillcolor: 'rgba(239, 68, 68, 0.03)' };
          }
          return s;
        });
      }
    }

    return { data, layout };
  }, [splanePlot, isDark]);

  const splaneConfig = useMemo(() => ({
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d'],
    displaylogo: false,
    toImageButtonOptions: {
      format: 'png',
      filename: 'root_locus',
      height: 800,
      width: 1000,
    },
  }), []);

  // ====================================================================
  // Render
  // ====================================================================

  const splanePlotComponent = (height) => (
    <div className="rl-splane-container" style={height ? { minHeight: height } : undefined}>
      {splanePlotData.data.length > 0 ? (
        <Plot
          data={splanePlotData.data}
          layout={{ ...splanePlotData.layout, ...(height ? { height } : {}) }}
          config={splaneConfig}
          onClick={handleSplaneClick}
          useResizeHandler
          style={{ width: '100%', height: '100%' }}
        />
      ) : (
        <div className="rl-empty-plot">
          {metadata?.error ? metadata.error : 'No root locus data'}
        </div>
      )}
    </div>
  );

  return (
    <div className={`root-locus-viewer ${isDark ? 'dark' : 'light'}`}>
      <TransferFunctionBanner metadata={metadata} onImport={handleImport} />

      {toastMessage && <div className="rl-toast">{toastMessage}</div>}

      {isUpdating && <div className="rl-updating-bar" />}

      {/* Desktop layout */}
      <div className="rl-desktop-only">
        <div className="rl-main-grid">
          {/* Left: S-plane */}
          <div className="rl-splane-section">
            {splanePlotComponent(500)}
            <div className="rl-splane-hint">Click on a branch to select K at that point</div>
          </div>

          {/* Right: Analysis */}
          <div className="rl-side-panel">
            <CLPolesReadout clPoles={clPoles} stability={stability} />
            <MetricsPanel metrics={metrics} currentK={currentK} stability={stability} />
            <div className="rl-step-section">
              <PlotDisplay plots={stepPlot} />
            </div>
            <SpecialPointsPanel specialPoints={specialPoints} />
          </div>
        </div>
      </div>

      {/* Mobile layout */}
      <div className="rl-mobile-only">
        <div className="rl-mobile-tabs">
          {[
            { key: 'splane', label: 'S-Plane' },
            { key: 'response', label: 'Response' },
            { key: 'analysis', label: 'Analysis' },
          ].map(tab => (
            <button
              key={tab.key}
              className={`rl-mobile-tab ${activeTab === tab.key ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.key)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === 'splane' && splanePlotComponent(380)}
        {activeTab === 'response' && (
          <div className="rl-mobile-response">
            <PlotDisplay plots={stepPlot} />
          </div>
        )}
        {activeTab === 'analysis' && (
          <div className="rl-mobile-analysis">
            <CLPolesReadout clPoles={clPoles} stability={stability} />
            <MetricsPanel metrics={metrics} currentK={currentK} stability={stability} />
            <SpecialPointsPanel specialPoints={specialPoints} />
          </div>
        )}
      </div>

      {/* Performance sweep plot (full width) */}
      <div className="rl-perf-section">
        <PlotDisplay plots={perfPlot} />
      </div>
    </div>
  );
}
