/**
 * PhasePortraitViewer
 *
 * Custom viewer for the Nonlinear Phase Portrait Analyzer.
 * - Main phase plane with vector field, trajectories, equilibria
 * - Click-to-add initial conditions
 * - Equilibrium info panel with Jacobian/eigenvalue details
 * - Trajectory list with remove buttons
 * - Time series plot for latest trajectory
 */

import React, { useState, useMemo, useCallback, useEffect, memo } from 'react';
import Plot from 'react-plotly.js';
import '../styles/PhasePortrait.css';

// ============================================================================
// Theme hook
// ============================================================================

function useIsDark() {
  const [isDark, setIsDark] = useState(
    () => document.documentElement.getAttribute('data-theme') !== 'light'
  );
  useEffect(() => {
    const check = () => setIsDark(document.documentElement.getAttribute('data-theme') !== 'light');
    const obs = new MutationObserver(check);
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => obs.disconnect();
  }, []);
  return isDark;
}

// ============================================================================
// Equilibrium type display helpers
// ============================================================================

const EQ_LABELS = {
  stable_node: 'Stable Node',
  unstable_node: 'Unstable Node',
  saddle: 'Saddle',
  stable_spiral: 'Stable Spiral',
  unstable_spiral: 'Unstable Spiral',
  center: 'Center',
  degenerate: 'Degenerate',
};

const EQ_COLORS = {
  stable_node: '#10b981',
  unstable_node: '#ef4444',
  saddle: '#f59e0b',
  stable_spiral: '#06b6d4',
  unstable_spiral: '#f97316',
  center: '#8b5cf6',
  degenerate: '#64748b',
};

function formatComplex(ev) {
  const re = ev.real.toFixed(3);
  const im = ev.imag;
  if (Math.abs(im) < 1e-8) return re;
  const sign = im >= 0 ? '+' : '-';
  return `${re} ${sign} ${Math.abs(im).toFixed(3)}j`;
}

// ============================================================================
// Equilibrium Detail Panel
// ============================================================================

const EquilibriumPanel = memo(function EquilibriumPanel({ equilibria, selectedIdx, onSelect }) {
  if (!equilibria || equilibria.length === 0) {
    return (
      <div className="pp-eq-panel pp-eq-empty">
        <div className="pp-eq-panel-title">Equilibria</div>
        <p className="pp-eq-none">No equilibria found in view</p>
      </div>
    );
  }

  const selected = selectedIdx !== null ? equilibria[selectedIdx] : null;

  return (
    <div className="pp-eq-panel">
      <div className="pp-eq-panel-title">
        Equilibria <span className="pp-eq-count">{equilibria.length}</span>
      </div>

      <div className="pp-eq-list">
        {equilibria.map((eq, i) => (
          <button
            key={i}
            className={`pp-eq-item ${selectedIdx === i ? 'selected' : ''}`}
            onClick={() => onSelect(selectedIdx === i ? null : i)}
          >
            <span
              className="pp-eq-dot"
              style={{ backgroundColor: EQ_COLORS[eq.type] || '#64748b' }}
            />
            <span className="pp-eq-coords">
              ({eq.x1.toFixed(2)}, {eq.x2.toFixed(2)})
            </span>
            <span className="pp-eq-type-badge" style={{ color: EQ_COLORS[eq.type] }}>
              {EQ_LABELS[eq.type] || eq.type}
            </span>
          </button>
        ))}
      </div>

      {selected && (
        <div className="pp-eq-detail">
          <div className="pp-eq-detail-header">
            <span style={{ color: EQ_COLORS[selected.type] }}>
              {EQ_LABELS[selected.type]}
            </span>
            {' at '}({selected.x1.toFixed(4)}, {selected.x2.toFixed(4)})
          </div>

          <div className="pp-eq-section">
            <div className="pp-eq-section-label">Eigenvalues</div>
            <div className="pp-eq-eigenvalues">
              {selected.eigenvalues.map((ev, i) => (
                <div key={i} className="pp-eq-ev">
                  λ{i + 1} = {formatComplex(ev)}
                </div>
              ))}
            </div>
          </div>

          <div className="pp-eq-section">
            <div className="pp-eq-section-label">Jacobian</div>
            <div className="pp-eq-jacobian">
              <div className="pp-eq-matrix">
                <span className="pp-eq-bracket">[</span>
                <div className="pp-eq-matrix-inner">
                  <div className="pp-eq-row">
                    <span>{selected.jacobian[0][0].toFixed(3)}</span>
                    <span>{selected.jacobian[0][1].toFixed(3)}</span>
                  </div>
                  <div className="pp-eq-row">
                    <span>{selected.jacobian[1][0].toFixed(3)}</span>
                    <span>{selected.jacobian[1][1].toFixed(3)}</span>
                  </div>
                </div>
                <span className="pp-eq-bracket">]</span>
              </div>
            </div>
          </div>

          <div className="pp-eq-metrics">
            <span>tr(J) = {selected.trace.toFixed(4)}</span>
            <span>det(J) = {selected.determinant.toFixed(4)}</span>
          </div>
        </div>
      )}
    </div>
  );
});

// ============================================================================
// Trajectory List
// ============================================================================

const TrajectoryList = memo(function TrajectoryList({ trajectories, onRemove, onClear }) {
  if (!trajectories || trajectories.length === 0) {
    return (
      <div className="pp-traj-panel">
        <div className="pp-traj-title">Trajectories</div>
        <p className="pp-traj-hint">Click on the phase portrait to add initial conditions</p>
      </div>
    );
  }

  const COLORS = [
    '#3b82f6', '#ef4444', '#10b981', '#f59e0b',
    '#8b5cf6', '#ec4899', '#06b6d4', '#f97316',
    '#84cc16', '#6366f1',
  ];

  return (
    <div className="pp-traj-panel">
      <div className="pp-traj-header">
        <span className="pp-traj-title">
          Trajectories <span className="pp-traj-count">{trajectories.length}</span>
        </span>
        <button className="pp-traj-clear" onClick={onClear}>Clear All</button>
      </div>
      <div className="pp-traj-list">
        {trajectories.map((t, i) => (
          <div key={t.id} className="pp-traj-item">
            <span
              className="pp-traj-color"
              style={{ backgroundColor: COLORS[i % COLORS.length] }}
            />
            <span className="pp-traj-ic">
              IC: ({t.x0.toFixed(2)}, {t.y0.toFixed(2)})
            </span>
            <button
              className="pp-traj-remove"
              onClick={() => onRemove(t.id)}
              title="Remove trajectory"
              aria-label="Remove trajectory"
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </div>
  );
});

// ============================================================================
// System Info Strip
// ============================================================================

const SystemInfo = memo(function SystemInfo({ metadata }) {
  if (!metadata) return null;
  const { f_expr, g_expr, preset_label, error } = metadata;

  return (
    <div className="pp-system-info">
      <div className="pp-system-name">{preset_label || 'Custom System'}</div>
      <div className="pp-system-eqs">
        <span className="pp-eq-label">ẋ₁ =</span>
        <code className="pp-eq-code">{f_expr}</code>
        <span className="pp-eq-sep">│</span>
        <span className="pp-eq-label">ẋ₂ =</span>
        <code className="pp-eq-code">{g_expr}</code>
      </div>
      {error && <div className="pp-error-banner">{error}</div>}
    </div>
  );
});

// ============================================================================
// Main Viewer
// ============================================================================

function PhasePortraitViewer({ metadata, plots, onButtonClick, isUpdating }) {
  const isDark = useIsDark();
  const [selectedEqIdx, setSelectedEqIdx] = useState(null);

  const equilibria = metadata?.equilibria || [];
  const trajectories = metadata?.trajectories || [];

  // Reset selected eq when equilibria change (including preset switches)
  const eqKey = useMemo(() => {
    return equilibria.map(e => `${e.x1.toFixed(3)},${e.x2.toFixed(3)}`).join('|');
  }, [equilibria]);
  useEffect(() => {
    setSelectedEqIdx(null);
  }, [eqKey]);

  // --- Click handler for adding trajectories ---
  const handlePlotClick = useCallback((event) => {
    if (!event?.points?.[0]) return;
    const pt = event.points[0];
    // Skip clicks on existing trajectory/equilibrium traces — only use empty-area clicks
    // Trace indices 0..N are vector field arrows, equilibria markers, and trajectory lines.
    // Use the plotly event's xaxis/yaxis coordinates for background clicks.
    const x1 = pt.x;
    const x2 = pt.y;
    if (typeof x1 !== 'number' || typeof x2 !== 'number') return;
    if (!isFinite(x1) || !isFinite(x2)) return;
    // Filter: ignore clicks on scatter markers (equilibria, IC dots) to prevent
    // accidentally adding trajectories on top of existing points
    if (pt.data?.mode === 'markers' || pt.data?.mode === 'markers+text') return;
    if (onButtonClick) {
      onButtonClick('add_trajectory', { x1, x2 });
    }
  }, [onButtonClick]);

  const handleRemoveTrajectory = useCallback((trajId) => {
    if (onButtonClick) {
      onButtonClick('remove_trajectory', { trajectory_id: trajId });
    }
  }, [onButtonClick]);

  const handleClearTrajectories = useCallback(() => {
    if (onButtonClick) {
      onButtonClick('clear_trajectories', {});
    }
  }, [onButtonClick]);

  // --- Build plot configs ---
  const phasePlot = useMemo(() => {
    const plot = plots?.find(p => p.id === 'phase_portrait');
    if (!plot) return null;
    return {
      ...plot,
      layout: {
        ...plot.layout,
        paper_bgcolor: isDark ? '#0a0e27' : 'rgba(255,255,255,0.98)',
        plot_bgcolor: isDark ? '#131b2e' : '#f8fafc',
        font: { family: 'Inter, sans-serif', size: 12, color: isDark ? '#f1f5f9' : '#1e293b' },
        datarevision: `phase_portrait-${plot.title}-${Date.now()}`,
        uirevision: 'phase_portrait',
      },
    };
  }, [plots, isDark]);

  const timePlot = useMemo(() => {
    const plot = plots?.find(p => p.id === 'time_series');
    if (!plot) return null;
    return {
      ...plot,
      layout: {
        ...plot.layout,
        paper_bgcolor: isDark ? '#0a0e27' : 'rgba(255,255,255,0.98)',
        plot_bgcolor: isDark ? '#131b2e' : '#f8fafc',
        font: { family: 'Inter, sans-serif', size: 12, color: isDark ? '#f1f5f9' : '#1e293b' },
        datarevision: `time_series-${plot.title}-${Date.now()}`,
        uirevision: 'time_series',
      },
    };
  }, [plots, isDark]);

  return (
    <div className="pp-viewer">
      <SystemInfo metadata={metadata} />

      <div className="pp-main-layout">
        {/* Left: Phase portrait */}
        <div className="pp-phase-container">
          {phasePlot && (
            <Plot
              data={phasePlot.data || []}
              layout={phasePlot.layout}
              config={{
                responsive: true,
                displayModeBar: true,
                modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d'],
                displaylogo: false,
              }}
              onClick={handlePlotClick}
              style={{ width: '100%', height: '100%' }}
              useResizeHandler
            />
          )}
          {isUpdating && <div className="pp-updating-overlay">Updating...</div>}
        </div>

        {/* Right: Info panels */}
        <div className="pp-side-panels">
          <EquilibriumPanel
            equilibria={equilibria}
            selectedIdx={selectedEqIdx}
            onSelect={setSelectedEqIdx}
          />
          <TrajectoryList
            trajectories={trajectories}
            onRemove={handleRemoveTrajectory}
            onClear={handleClearTrajectories}
          />
        </div>
      </div>

      {/* Time series plot */}
      {timePlot && timePlot.data && timePlot.data.length > 0 && (
        <div className="pp-time-container">
          <Plot
            data={timePlot.data}
            layout={timePlot.layout}
            config={{
              responsive: true,
              displayModeBar: false,
              displaylogo: false,
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
          />
        </div>
      )}
    </div>
  );
}

export default memo(PhasePortraitViewer);
