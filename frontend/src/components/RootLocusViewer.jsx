/**
 * RootLocusViewer
 *
 * Custom viewer for the Root Locus Analyzer simulation.
 * Full vertical layout: s-plane (full width), animation controls,
 * metrics strip, step response + stability analysis side by side,
 * collapsible construction rules, performance sweep.
 *
 * Features:
 * - Inline TF expression input with live KaTeX preview
 * - K-sweep animation with trail and step response sync
 * - Routh-Hurwitz stability table
 * - Stability ranges visualization
 * - Click on s-plane to select K at that point
 * - Import TF from Block Diagram Builder
 */

import React, { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import Plot from 'react-plotly.js';
import PlotDisplay from './PlotDisplay';
import katex from 'katex';
import 'katex/dist/katex.min.css';
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
   TF Expression to LaTeX
   ====================================================================== */
function tfExprToLatex(expression) {
  if (!expression) return '';
  const expr = expression.trim();
  // Handle (num)/(den) or num/den
  const ratioMatch = expr.match(/^\(([^)]+)\)\s*\/\s*\(([^)]+)\)$/) ||
                     expr.match(/^([^/]+)\/(.+)$/);
  if (ratioMatch) {
    const num = ratioMatch[1].trim();
    const den = ratioMatch[2].trim();
    return `G(s) = \\frac{${num}}{${den}}`;
  }
  return `G(s) = ${expr}`;
}

/* ======================================================================
   Sub-components
   ====================================================================== */

function TransferFunctionBanner({ metadata, onImport, onParseExpression }) {
  const tf = metadata?.transfer_function;
  const stability = metadata?.stability;
  const error = metadata?.error;

  const [tfInput, setTfInput] = useState('');
  const [tfError, setTfError] = useState(null);
  const inputRef = useRef(null);

  const stabilityStyles = {
    stable: { bg: 'rgba(16, 185, 129, 0.15)', color: '#10b981', label: 'Stable' },
    marginally_stable: { bg: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', label: 'Marginal' },
    unstable: { bg: 'rgba(239, 68, 68, 0.15)', color: '#ef4444', label: 'Unstable' },
  };
  const stab = stabilityStyles[stability] || stabilityStyles.stable;

  // KaTeX preview
  const latexPreview = useMemo(() => {
    if (tfInput.trim()) {
      const latex = tfExprToLatex(tfInput);
      try {
        return katex.renderToString(latex, { throwOnError: false, displayMode: false });
      } catch {
        return null;
      }
    }
    // Show current TF from metadata
    if (tf?.num_display && tf?.den_display) {
      const latex = `G(s) = \\frac{${tf.num_display}}{${tf.den_display}}`;
      try {
        return katex.renderToString(latex, { throwOnError: false, displayMode: false });
      } catch {
        return null;
      }
    }
    return null;
  }, [tfInput, tf?.num_display, tf?.den_display]);

  const handleSubmit = useCallback(() => {
    const expr = tfInput.trim();
    if (!expr) return;
    setTfError(null);
    if (onParseExpression) {
      onParseExpression(expr);
    }
  }, [tfInput, onParseExpression]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  }, [handleSubmit]);

  return (
    <div className="rl-tf-banner">
      <div className="rl-tf-input-area">
        <div className="rl-tf-input-row">
          <label className="rl-tf-input-label">G(s)</label>
          <input
            ref={inputRef}
            className="rl-tf-input"
            type="text"
            value={tfInput}
            onChange={(e) => setTfInput(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={handleSubmit}
            placeholder="e.g. (s+1)/(s^2+2s+1)"
            spellCheck={false}
          />
          <button className="rl-tf-apply-btn" onClick={handleSubmit}>Apply</button>
        </div>
        {latexPreview && (
          <div
            className="rl-tf-preview"
            dangerouslySetInnerHTML={{ __html: latexPreview }}
          />
        )}
        {(tfError || error) && (
          <div className="rl-error-banner">{tfError || error}</div>
        )}
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
          Import BDB
        </button>
      </div>
    </div>
  );
}

function MetricsStrip({ metrics, currentK }) {
  const fmt = (val, dec = 3) => {
    if (val == null) return '—';
    if (typeof val !== 'number' || !isFinite(val)) return '∞';
    return val.toFixed(dec);
  };

  const cards = [
    { label: 'K', value: fmt(currentK, 2), color: '#f59e0b' },
    { label: 'ζ', value: fmt(metrics?.damping_ratio), color: '#3b82f6' },
    { label: 'ωₙ', value: fmt(metrics?.natural_freq), unit: 'rad/s', color: '#10b981' },
    { label: 'OS%', value: fmt(metrics?.percent_overshoot, 1), color: '#ef4444' },
    { label: 'tₛ', value: fmt(metrics?.settling_time, 2), unit: 's', color: '#8b5cf6' },
    { label: 'tᵣ', value: fmt(metrics?.rise_time, 2), unit: 's', color: '#06b6d4' },
    { label: 'GM', value: fmt(metrics?.gain_margin_db, 1), unit: 'dB', color: '#14b8a6' },
    { label: 'PM', value: fmt(metrics?.phase_margin_deg, 1), unit: '°', color: '#ec4899' },
  ];

  return (
    <div className="rl-metrics-strip">
      {cards.map((card, i) => (
        <div key={i} className="rl-metric-chip" style={{ borderColor: card.color }}>
          <span className="rl-metric-chip-value">{card.value}</span>
          {card.unit && <span className="rl-metric-chip-unit">{card.unit}</span>}
          <span className="rl-metric-chip-label">{card.label}</span>
        </div>
      ))}
    </div>
  );
}

function AnimationControlBar({
  isPlaying, onPlayPause, onReset, speed, onSpeedChange,
  currentK, progress, kMax,
}) {
  return (
    <div className="rl-animation-bar">
      <div className="rl-anim-controls">
        <button className="rl-anim-btn" onClick={onPlayPause} title={isPlaying ? 'Pause' : 'Play'}>
          {isPlaying ? '⏸' : '▶'}
        </button>
        <button className="rl-anim-btn rl-anim-reset" onClick={onReset} title="Reset">
          ↺
        </button>
      </div>

      <div className="rl-anim-speed">
        {[0.5, 1, 2, 4].map(s => (
          <button
            key={s}
            className={`rl-speed-btn ${speed === s ? 'active' : ''}`}
            onClick={() => onSpeedChange(s)}
          >
            {s}x
          </button>
        ))}
      </div>

      <div className="rl-anim-progress-area">
        <div className="rl-anim-progress-bar">
          <div
            className="rl-anim-progress-fill"
            style={{ width: `${(progress || 0) * 100}%` }}
          />
        </div>
        <span className="rl-anim-k-display">K = {(currentK ?? 0).toFixed(2)}</span>
      </div>
    </div>
  );
}

function RouthTablePanel({ routhTable }) {
  const [isOpen, setIsOpen] = useState(true);
  if (!routhTable || !routhTable.rows || routhTable.rows.length === 0) return null;

  const { rows, powers, first_column, sign_changes, flags, stable } = routhTable;
  const flagMap = {};
  (flags || []).forEach(f => { flagMap[f.row] = f; });

  return (
    <div className="rl-routh-panel">
      <button className="rl-section-toggle" onClick={() => setIsOpen(!isOpen)}>
        <span>{isOpen ? '▾' : '▸'} Routh-Hurwitz Table</span>
        <span className={`rl-routh-result ${stable ? 'stable' : 'unstable'}`}>
          {stable ? 'Stable' : `${sign_changes} RHP pole${sign_changes !== 1 ? 's' : ''}`}
        </span>
      </button>
      {isOpen && (
        <div className="rl-routh-content">
          <table className="rl-routh-table">
            <tbody>
              {rows.map((row, i) => {
                const prevSign = i > 0 ? Math.sign(first_column[i - 1]) : Math.sign(first_column[0]);
                const currSign = Math.sign(first_column[i]);
                const signChange = i > 0 && prevSign !== 0 && currSign !== 0 && prevSign !== currSign;
                const flag = flagMap[i];

                return (
                  <tr key={i} className={flag ? 'rl-routh-flagged' : ''}>
                    <td className="rl-routh-power">{powers[i]}</td>
                    {row.map((val, j) => (
                      <td
                        key={j}
                        className={`rl-routh-cell ${j === 0 && signChange ? 'sign-change' : ''}`}
                      >
                        {Math.abs(val) < 1e-10 ? '0' : val.toFixed(3)}
                      </td>
                    ))}
                    {flag && (
                      <td className="rl-routh-flag">
                        {flag.type === 'epsilon' ? 'ε' : 'aux'}
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
          <div className="rl-routh-summary">
            {sign_changes} sign change{sign_changes !== 1 ? 's' : ''} in first column
            → {sign_changes} RHP pole{sign_changes !== 1 ? 's' : ''}
          </div>
        </div>
      )}
    </div>
  );
}

function StabilityRangesBar({ stabilityRanges, currentK, kMax }) {
  if (!stabilityRanges || !stabilityRanges.ranges || stabilityRanges.ranges.length === 0) return null;

  const { ranges, crossings } = stabilityRanges;
  const maxK = kMax || (ranges.length > 0 ? ranges[ranges.length - 1].end : 100);

  return (
    <div className="rl-stability-ranges">
      <div className="rl-section-heading">Stability Ranges</div>
      <div className="rl-stability-bar-container">
        <div className="rl-stability-bar">
          {ranges.map((r, i) => {
            const width = ((r.end - r.start) / maxK) * 100;
            return (
              <div
                key={i}
                className={`rl-stability-segment ${r.stable ? 'stable' : 'unstable'}`}
                style={{ width: `${width}%` }}
                title={`K ∈ [${r.start.toFixed(1)}, ${r.end.toFixed(1)}] — ${r.stable ? 'Stable' : 'Unstable'}`}
              />
            );
          })}
          {currentK != null && maxK > 0 && (
            <div
              className="rl-stability-k-marker"
              style={{ left: `${Math.min((currentK / maxK) * 100, 100)}%` }}
            />
          )}
        </div>
        <div className="rl-stability-labels">
          <span>K = 0</span>
          <span>K = {maxK}</span>
        </div>
      </div>
      <div className="rl-stability-ranges-text">
        {ranges.map((r, i) => (
          <div key={i} className={`rl-stability-range-item ${r.stable ? 'stable' : 'unstable'}`}>
            {r.stable ? '●' : '●'} K ∈ [{r.start.toFixed(1)}, {r.end >= kMax * 0.99 ? '∞' : r.end.toFixed(1)}]
            — {r.stable ? 'Stable' : 'Unstable'}
          </div>
        ))}
      </div>
      {crossings && crossings.length > 0 && (
        <div className="rl-stability-crossings">
          {crossings.map((c, i) => (
            <div key={i} className="rl-crossing-item">
              jω crossing at K = {c.k.toFixed(2)}, ω = ±{c.omega.toFixed(3)} rad/s
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function CLPolesReadout({ clPoles }) {
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

function SpecialPointsPanel({ specialPoints }) {
  if (!specialPoints) return null;

  const { breakaway, jw_crossings, asymptotes, departure_angles, arrival_angles } = specialPoints;
  const hasContent = (breakaway?.length > 0) || (jw_crossings?.length > 0) ||
                     (asymptotes?.angles?.length > 0) || (departure_angles?.length > 0) ||
                     (arrival_angles?.length > 0);

  if (!hasContent) return null;

  return (
    <div className="rl-special-content">
      {breakaway?.length > 0 && (
        <div className="rl-special-section">
          <div className="rl-special-heading">Breakaway / Break-in</div>
          {breakaway.map((bp, i) => (
            <div key={i} className="rl-special-item">
              s = {bp.s?.real?.toFixed(3)} &nbsp; K = {bp.K?.toFixed(3)}
            </div>
          ))}
        </div>
      )}
      {jw_crossings?.length > 0 && (
        <div className="rl-special-section">
          <div className="rl-special-heading">jω-Axis Crossings</div>
          {jw_crossings.map((jw, i) => (
            <div key={i} className="rl-special-item">
              ω = ±{jw.omega?.toFixed(3)} rad/s &nbsp; K = {jw.K?.toFixed(2)}
            </div>
          ))}
        </div>
      )}
      {asymptotes?.angles?.length > 0 && (
        <div className="rl-special-section">
          <div className="rl-special-heading">Asymptotes ({asymptotes.n} branches)</div>
          <div className="rl-special-item">Centroid: σ = {asymptotes.centroid?.toFixed(3)}</div>
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

  // Animation state
  const [isPlaying, setIsPlaying] = useState(false);
  const [animSpeed, setAnimSpeed] = useState(1);
  const [animIndex, setAnimIndex] = useState(0);
  const animRef = useRef(null);
  const lastStepUpdate = useRef(0);

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
  const routhTable = metadata?.routh_table;
  const stabilityRanges = metadata?.stability_ranges;
  const locusData = metadata?.locus_data;
  const kMax = currentParams?.k_max || 100;

  // ====================================================================
  // Animation logic
  // ====================================================================
  const totalFrames = locusData?.k_values?.length || 0;

  const animatedK = useMemo(() => {
    if (!locusData || !locusData.k_values || animIndex >= locusData.k_values.length) return currentK;
    return locusData.k_values[animIndex];
  }, [locusData, animIndex, currentK]);

  const animatedPoles = useMemo(() => {
    if (!locusData || !locusData.branches || animIndex >= totalFrames) return null;
    return locusData.branches.map(branch => branch[animIndex]).filter(p => p != null);
  }, [locusData, animIndex, totalFrames]);

  // Trail: last 20 positions
  const trailRef = useRef([]);
  useEffect(() => {
    if (animatedPoles && isPlaying) {
      trailRef.current = [...trailRef.current, animatedPoles].slice(-20);
    }
  }, [animatedPoles, isPlaying]);

  useEffect(() => {
    if (!isPlaying || totalFrames === 0) {
      if (animRef.current) cancelAnimationFrame(animRef.current);
      return;
    }

    let lastTime = 0;
    const stepsPerSecond = 25 * animSpeed; // base ~25 steps/sec at 1x

    const animate = (timestamp) => {
      if (!lastTime) lastTime = timestamp;
      const dt = timestamp - lastTime;

      if (dt > 1000 / stepsPerSecond) {
        lastTime = timestamp;
        setAnimIndex(prev => {
          const next = prev + 1;
          if (next >= totalFrames) {
            setIsPlaying(false);
            return prev;
          }

          // Throttled step response update (~5 fps)
          const now = Date.now();
          if (now - lastStepUpdate.current > 200 && locusData?.k_values) {
            lastStepUpdate.current = now;
            const newK = locusData.k_values[next];
            if (onParamChange && newK != null) {
              onParamChange('gain_K', Math.abs(newK));
            }
          }

          return next;
        });
      }

      animRef.current = requestAnimationFrame(animate);
    };

    animRef.current = requestAnimationFrame(animate);
    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, [isPlaying, animSpeed, totalFrames, locusData, onParamChange]);

  const handlePlayPause = useCallback(() => {
    if (!isPlaying && animIndex >= totalFrames - 1) {
      setAnimIndex(0);
      trailRef.current = [];
    }
    setIsPlaying(prev => !prev);
  }, [isPlaying, animIndex, totalFrames]);

  const handleReset = useCallback(() => {
    setIsPlaying(false);
    setAnimIndex(0);
    trailRef.current = [];
  }, []);

  // ====================================================================
  // Click-to-select-K on s-plane
  // ====================================================================
  const handleSplaneClick = useCallback((event) => {
    if (isUpdating) return;
    if (!event?.points?.[0]) return;

    const { x, y } = event.points[0];
    if (isPlaying) {
      setIsPlaying(false);
    }
    if (onButtonClick) {
      onButtonClick('click_select_k', { sigma: x, omega: y });
    }
  }, [onButtonClick, isUpdating, isPlaying]);

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
  // Parse expression
  // ====================================================================
  const handleParseExpression = useCallback((expr) => {
    if (onButtonClick) {
      onButtonClick('parse_expression', { expression: expr });
    }
  }, [onButtonClick]);

  // ====================================================================
  // S-plane plot with animation overlay
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
      if (layout.shapes) {
        layout.shapes = layout.shapes.map(s => {
          if (s.fillcolor?.includes('239, 68, 68')) {
            return { ...s, fillcolor: 'rgba(239, 68, 68, 0.03)' };
          }
          return s;
        });
      }
    }

    // Add animated pole markers if animation is active
    if (isPlaying && animatedPoles && animatedPoles.length > 0) {
      // Trail dots
      const trail = trailRef.current;
      if (trail.length > 0) {
        const trailX = [];
        const trailY = [];
        const trailOpacity = [];
        trail.forEach((poles, ti) => {
          const opacity = 0.1 + 0.6 * (ti / trail.length);
          poles.forEach(p => {
            trailX.push(p.re);
            trailY.push(p.im);
            trailOpacity.push(opacity);
          });
        });

        data.push({
          x: trailX,
          y: trailY,
          type: 'scatter',
          mode: 'markers',
          marker: {
            symbol: 'circle',
            size: 5,
            color: '#00d9ff',
            opacity: trailOpacity,
          },
          name: 'Trail',
          showlegend: false,
          hoverinfo: 'skip',
        });
      }

      // Current animated poles
      data.push({
        x: animatedPoles.map(p => p.re),
        y: animatedPoles.map(p => p.im),
        type: 'scatter',
        mode: 'markers',
        marker: {
          symbol: 'diamond',
          size: 16,
          color: '#00d9ff',
          line: { width: 2, color: '#ffffff' },
        },
        name: `Animated (K=${(animatedK ?? 0).toFixed(2)})`,
        showlegend: false,
        hovertemplate: 'σ = %{x:.3f}<br>jω = %{y:.3f}<extra>Animated</extra>',
      });

      // Update datarevision to force re-render
      layout.datarevision = `anim-${Date.now()}`;
    }

    return { data, layout };
  }, [splanePlot, isDark, isPlaying, animatedPoles, animatedK]);

  const splaneConfig = useMemo(() => ({
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d'],
    displaylogo: false,
    toImageButtonOptions: { format: 'png', filename: 'root_locus', height: 800, width: 1200 },
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
      {/* 1. TF Banner with inline expression input */}
      <TransferFunctionBanner
        metadata={metadata}
        onImport={handleImport}
        onParseExpression={handleParseExpression}
      />

      {toastMessage && <div className="rl-toast">{toastMessage}</div>}
      {isUpdating && <div className="rl-updating-bar" />}

      {/* Desktop layout */}
      <div className="rl-desktop-only">
        {/* 2. S-plane — full width, tall */}
        {splanePlotComponent(600)}
        <div className="rl-splane-hint">Click on a branch to select K at that point</div>

        {/* 3. Animation controls */}
        <AnimationControlBar
          isPlaying={isPlaying}
          onPlayPause={handlePlayPause}
          onReset={handleReset}
          speed={animSpeed}
          onSpeedChange={setAnimSpeed}
          currentK={isPlaying ? animatedK : currentK}
          progress={totalFrames > 0 ? animIndex / totalFrames : 0}
          kMax={kMax}
        />

        {/* 4. Horizontal metrics strip */}
        <MetricsStrip metrics={metrics} currentK={currentK} />

        {/* 5. Step Response + Stability Analysis side by side */}
        <div className="rl-analysis-row">
          <div className="rl-step-section">
            <PlotDisplay plots={stepPlot} />
          </div>
          <div className="rl-stability-section">
            <RouthTablePanel routhTable={routhTable} />
            <StabilityRangesBar
              stabilityRanges={stabilityRanges}
              currentK={currentK}
              kMax={kMax}
            />
          </div>
        </div>

        {/* 6. Collapsible CL Poles + Special Points */}
        <details className="rl-details-collapsible">
          <summary className="rl-details-summary">
            Closed-Loop Poles & Construction Rules
          </summary>
          <div className="rl-details-content">
            <CLPolesReadout clPoles={clPoles} />
            <SpecialPointsPanel specialPoints={specialPoints} />
          </div>
        </details>

        {/* 7. Performance vs K sweep (full width) */}
        <div className="rl-perf-section">
          <PlotDisplay plots={perfPlot} />
        </div>
      </div>

      {/* Mobile layout */}
      <div className="rl-mobile-only">
        <div className="rl-mobile-tabs">
          {[
            { key: 'splane', label: 'S-Plane' },
            { key: 'response', label: 'Response' },
            { key: 'stability', label: 'Stability' },
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

        {activeTab === 'splane' && (
          <>
            {splanePlotComponent(400)}
            <AnimationControlBar
              isPlaying={isPlaying}
              onPlayPause={handlePlayPause}
              onReset={handleReset}
              speed={animSpeed}
              onSpeedChange={setAnimSpeed}
              currentK={isPlaying ? animatedK : currentK}
              progress={totalFrames > 0 ? animIndex / totalFrames : 0}
              kMax={kMax}
            />
            <MetricsStrip metrics={metrics} currentK={currentK} />
          </>
        )}
        {activeTab === 'response' && (
          <div className="rl-mobile-response">
            <PlotDisplay plots={stepPlot} />
            <PlotDisplay plots={perfPlot} />
          </div>
        )}
        {activeTab === 'stability' && (
          <div className="rl-mobile-stability">
            <RouthTablePanel routhTable={routhTable} />
            <StabilityRangesBar stabilityRanges={stabilityRanges} currentK={currentK} kMax={kMax} />
          </div>
        )}
        {activeTab === 'analysis' && (
          <div className="rl-mobile-analysis">
            <CLPolesReadout clPoles={clPoles} />
            <SpecialPointsPanel specialPoints={specialPoints} />
          </div>
        )}
      </div>
    </div>
  );
}
