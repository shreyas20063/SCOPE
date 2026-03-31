/**
 * NonlinearControlLabViewer
 *
 * Custom viewer for the Nonlinear Control Lab simulation.
 * Layout: Canvas phase portrait (left) + stacked Plotly plots (right),
 * metrics strip, collapsible KaTeX derivation chain, and optional ROA heatmap.
 */

import React, { useState, useCallback, useMemo, useRef, useEffect, memo } from 'react';
import Plot from 'react-plotly.js';
import '../styles/NonlinearControlLab.css';

// ============================================================================
// KaTeX rendering helper (same pattern as SteadyStateErrorViewer)
// ============================================================================

let katexModule = null;
let katexLoading = false;
const katexCallbacks = [];

function loadKatex(cb) {
  if (katexModule) { cb(katexModule); return; }
  katexCallbacks.push(cb);
  if (katexLoading) return;
  katexLoading = true;
  import('katex').then(mod => {
    katexModule = mod.default || mod;
    import('katex/dist/katex.min.css');
    katexCallbacks.forEach(fn => fn(katexModule));
    katexCallbacks.length = 0;
  }).catch(() => { katexLoading = false; });
}

function renderLatex(latex, displayMode = false) {
  if (!katexModule || !latex) return latex || '';
  try {
    return katexModule.renderToString(latex, { throwOnError: false, displayMode });
  } catch {
    return latex;
  }
}

// ============================================================================
// Theme detection hook
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
// Canvas Phase Portrait
// ============================================================================

const PhasePortraitCanvas = memo(function PhasePortraitCanvas({
  metadata, isDark, onCanvasClick
}) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const [canvasSize, setCanvasSize] = useState({ width: 500, height: 500 });

  // Observe container size
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const ro = new ResizeObserver(entries => {
      for (const entry of entries) {
        const w = entry.contentRect.width;
        if (w > 0) {
          setCanvasSize({ width: w, height: w }); // square
        }
      }
    });
    ro.observe(container);
    return () => ro.disconnect();
  }, []);

  // Build coordinate transform
  const transform = useMemo(() => {
    const vf = metadata?.vector_field;
    if (!vf?.x_grid?.length || !vf?.y_grid?.length) return null;
    const xMin = vf.x_grid[0], xMax = vf.x_grid[vf.x_grid.length - 1];
    const yMin = vf.y_grid[0], yMax = vf.y_grid[vf.y_grid.length - 1];
    const { width: cw, height: ch } = canvasSize;
    return {
      toCanvas: (sx, sy) => [
        (sx - xMin) / (xMax - xMin) * cw,
        (1 - (sy - yMin) / (yMax - yMin)) * ch,
      ],
      toState: (cx, cy) => [
        xMin + cx / cw * (xMax - xMin),
        yMax - cy / ch * (yMax - yMin),
      ],
      xMin, xMax, yMin, yMax,
    };
  }, [metadata?.vector_field, canvasSize]);

  // Draw everything
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !transform) return;

    const dpr = window.devicePixelRatio || 1;
    const { width: cw, height: ch } = canvasSize;
    canvas.width = cw * dpr;
    canvas.height = ch * dpr;
    canvas.style.width = cw + 'px';
    canvas.style.height = ch + 'px';

    const ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    // Background
    ctx.fillStyle = isDark ? '#131b2e' : '#f8fafc';
    ctx.fillRect(0, 0, cw, ch);

    // Grid lines
    drawGrid(ctx, transform, cw, ch, isDark);

    // Vector field
    if (metadata?.vector_field) {
      drawVectorField(ctx, metadata.vector_field, transform, cw, ch, isDark);
    }

    // Streamlines
    if (metadata?.streamlines?.length) {
      drawStreamlines(ctx, metadata.streamlines, transform);
    }

    // ROA overlay (if available and canvas-renderable)
    if (metadata?.roa_result) {
      drawROAOverlay(ctx, metadata.roa_result, transform, cw, ch);
    }

    // Linear trajectory (dashed, behind nonlinear)
    if (metadata?.trajectory_data?.x_linear) {
      drawTrajectory(ctx, metadata.trajectory_data.x_linear, transform, {
        color: 'rgba(59, 130, 246, 0.4)',
        lineWidth: 1.5,
        dash: [6, 4],
        projX: metadata.projection_x || 0,
        projY: metadata.projection_y || 2,
      });
    }

    // Nonlinear trajectory (solid, on top)
    if (metadata?.trajectory_data?.x_nonlinear) {
      drawTrajectory(ctx, metadata.trajectory_data.x_nonlinear, transform, {
        color: '#ef4444',
        lineWidth: 2.5,
        dash: null,
        projX: metadata.projection_x || 0,
        projY: metadata.projection_y || 2,
        gradient: true,
        gradientEnd: '#f59e0b',
      });
    }

    // Equilibrium marker
    if (metadata?.x_eq) {
      const pX = metadata.projection_x || 0;
      const pY = metadata.projection_y || 2;
      drawEquilibrium(ctx, metadata.x_eq[pX], metadata.x_eq[pY], transform, metadata.is_stable);
    }

    // Axis labels
    drawAxisLabels(ctx, transform, cw, ch, isDark);
  }, [metadata, transform, canvasSize, isDark]);

  // Click handler
  const handleClick = useCallback((e) => {
    if (!transform || !onCanvasClick) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const cx = e.clientX - rect.left;
    const cy = e.clientY - rect.top;
    const [sx, sy] = transform.toState(cx, cy);
    onCanvasClick(sx, sy);
  }, [transform, onCanvasClick]);

  // State names for axis label overlay
  const stateNames = metadata?.state_names || [];
  const projX = metadata?.projection_x ?? 0;
  const projY = metadata?.projection_y ?? 2;
  const xLabel = stateNames[projX] || ('x' + (projX + 1));
  const yLabel = stateNames[projY] || ('x' + (projY + 1));

  return (
    <div className="ncl-canvas-container" ref={containerRef}>
      <div className="ncl-canvas-title">Phase Portrait</div>
      <canvas
        ref={canvasRef}
        className="ncl-canvas"
        onClick={handleClick}
        role="img"
        aria-label="Phase portrait canvas — click to set initial condition"
      />
      <div className="ncl-canvas-axes-label">{xLabel} vs {yLabel}</div>
      <div className="ncl-canvas-hint">Click to set initial condition</div>
    </div>
  );
});

// --- Canvas drawing helpers ---

function drawGrid(ctx, transform, cw, ch, isDark) {
  const { xMin, xMax, yMin, yMax } = transform;
  const gridColor = isDark ? 'rgba(148, 163, 184, 0.08)' : 'rgba(148, 163, 184, 0.15)';
  const axisColor = isDark ? 'rgba(148, 163, 184, 0.25)' : 'rgba(148, 163, 184, 0.35)';
  const tickColor = isDark ? 'rgba(148, 163, 184, 0.5)' : 'rgba(100, 116, 139, 0.7)';

  // Compute nice grid spacing
  const xRange = xMax - xMin;
  const yRange = yMax - yMin;
  const xStep = niceStep(xRange, 8);
  const yStep = niceStep(yRange, 8);

  ctx.lineWidth = 0.5;
  ctx.strokeStyle = gridColor;
  ctx.font = '10px "Fira Code", monospace';
  ctx.fillStyle = tickColor;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';

  // Vertical grid lines + x ticks
  for (let x = Math.ceil(xMin / xStep) * xStep; x <= xMax; x += xStep) {
    const [cx] = transform.toCanvas(x, 0);
    ctx.beginPath();
    ctx.moveTo(cx, 0);
    ctx.lineTo(cx, ch);
    ctx.stroke();
    // tick label
    if (Math.abs(x) > xStep * 0.1) {
      ctx.fillText(formatTick(x), cx, ch - 14);
    }
  }

  // Horizontal grid lines + y ticks
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  for (let y = Math.ceil(yMin / yStep) * yStep; y <= yMax; y += yStep) {
    const [, cy] = transform.toCanvas(0, y);
    ctx.beginPath();
    ctx.moveTo(0, cy);
    ctx.lineTo(cw, cy);
    ctx.stroke();
    if (Math.abs(y) > yStep * 0.1) {
      ctx.fillText(formatTick(y), 4, cy);
    }
  }

  // Zero axes (thicker)
  ctx.strokeStyle = axisColor;
  ctx.lineWidth = 1;
  // x-axis
  if (yMin <= 0 && yMax >= 0) {
    const [, cy0] = transform.toCanvas(0, 0);
    ctx.beginPath();
    ctx.moveTo(0, cy0);
    ctx.lineTo(cw, cy0);
    ctx.stroke();
  }
  // y-axis
  if (xMin <= 0 && xMax >= 0) {
    const [cx0] = transform.toCanvas(0, 0);
    ctx.beginPath();
    ctx.moveTo(cx0, 0);
    ctx.lineTo(cx0, ch);
    ctx.stroke();
  }
}

function niceStep(range, targetTicks) {
  const rough = range / targetTicks;
  const pow = Math.pow(10, Math.floor(Math.log10(rough)));
  const frac = rough / pow;
  if (frac <= 1.5) return pow;
  if (frac <= 3.5) return 2 * pow;
  if (frac <= 7.5) return 5 * pow;
  return 10 * pow;
}

function formatTick(v) {
  if (Math.abs(v) >= 100) return v.toFixed(0);
  if (Math.abs(v) >= 1) return v.toFixed(1);
  return v.toFixed(2);
}

function drawVectorField(ctx, vfData, transform, cw, ch, isDark) {
  const { x_grid, y_grid, dx, dy, magnitudes } = vfData;
  if (!x_grid || !y_grid || !dx || !dy) return;

  // Find max magnitude for normalization
  let maxMag = 0;
  for (let i = 0; i < magnitudes.length; i++) {
    for (let j = 0; j < magnitudes[i].length; j++) {
      if (magnitudes[i][j] > maxMag) maxMag = magnitudes[i][j];
    }
  }
  if (maxMag === 0) return;

  const nx = x_grid.length;
  const ny = y_grid.length;
  // Arrow spacing in canvas pixels
  const spacingX = cw / nx;
  const spacingY = ch / ny;
  const maxArrowLen = Math.min(spacingX, spacingY) * 0.45;
  const minMagThreshold = maxMag * 0.01;

  for (let i = 0; i < ny; i++) {
    for (let j = 0; j < nx; j++) {
      const mag = magnitudes[i]?.[j];
      if (mag == null || mag < minMagThreshold) continue;

      const dxVal = dx[i]?.[j] || 0;
      const dyVal = dy[i]?.[j] || 0;
      if (dxVal === 0 && dyVal === 0) continue;

      const [cx, cy] = transform.toCanvas(x_grid[j], y_grid[i]);

      // Normalize
      const norm = Math.sqrt(dxVal * dxVal + dyVal * dyVal);
      const scale = (mag / maxMag) * maxArrowLen;
      const ux = (dxVal / norm) * scale;
      const uy = -(dyVal / norm) * scale; // flip y for canvas

      // Color: HSL blue(240) -> red(0) based on magnitude
      const hue = 240 - (mag / maxMag) * 240;
      const alpha = 0.3 + 0.5 * (mag / maxMag);
      ctx.strokeStyle = 'hsla(' + hue + ', 80%, 55%, ' + alpha + ')';
      ctx.lineWidth = 0.8 + 0.7 * (mag / maxMag);

      // Draw arrow shaft
      const x0 = cx - ux * 0.5;
      const y0 = cy - uy * 0.5;
      const x1 = cx + ux * 0.5;
      const y1 = cy + uy * 0.5;

      ctx.beginPath();
      ctx.moveTo(x0, y0);
      ctx.lineTo(x1, y1);
      ctx.stroke();

      // Arrowhead
      const headLen = Math.min(scale * 0.35, 5);
      const angle = Math.atan2(uy, ux);
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(
        x1 - headLen * Math.cos(angle - 0.5),
        y1 - headLen * Math.sin(angle - 0.5)
      );
      ctx.moveTo(x1, y1);
      ctx.lineTo(
        x1 - headLen * Math.cos(angle + 0.5),
        y1 - headLen * Math.sin(angle + 0.5)
      );
      ctx.stroke();
    }
  }
}

function drawStreamlines(ctx, streamlines, transform) {
  ctx.strokeStyle = 'rgba(20, 184, 166, 0.25)';
  ctx.lineWidth = 1;
  ctx.setLineDash([]);

  for (const sl of streamlines) {
    if (!sl.x || !sl.y || sl.x.length < 2) continue;
    ctx.beginPath();
    const [cx0, cy0] = transform.toCanvas(sl.x[0], sl.y[0]);
    ctx.moveTo(cx0, cy0);
    for (let k = 1; k < sl.x.length; k++) {
      const [cx, cy] = transform.toCanvas(sl.x[k], sl.y[k]);
      ctx.lineTo(cx, cy);
    }
    ctx.stroke();

    // Add arrowhead at midpoint
    const mid = Math.floor(sl.x.length / 2);
    if (mid > 0 && mid < sl.x.length - 1) {
      const [mx, my] = transform.toCanvas(sl.x[mid], sl.y[mid]);
      const [nx, ny] = transform.toCanvas(sl.x[mid + 1], sl.y[mid + 1]);
      const angle = Math.atan2(ny - my, nx - mx);
      const headLen = 5;
      ctx.beginPath();
      ctx.moveTo(mx, my);
      ctx.lineTo(
        mx - headLen * Math.cos(angle - 0.5),
        my - headLen * Math.sin(angle - 0.5)
      );
      ctx.moveTo(mx, my);
      ctx.lineTo(
        mx - headLen * Math.cos(angle + 0.5),
        my - headLen * Math.sin(angle + 0.5)
      );
      ctx.stroke();
    }
  }
}

function drawTrajectory(ctx, stateData, transform, opts) {
  const { color, lineWidth, dash, projX, projY, gradient, gradientEnd } = opts;
  if (!stateData || !stateData[projX] || !stateData[projY]) return;
  const xs = stateData[projX];
  const ys = stateData[projY];
  if (xs.length < 2) return;

  ctx.lineWidth = lineWidth;
  ctx.setLineDash(dash || []);

  if (gradient && gradientEnd) {
    // Draw with gradient segments
    const n = xs.length;
    for (let k = 0; k < n - 1; k++) {
      const frac = k / (n - 1);
      const r = Math.round(lerpColor(parseInt(color.slice(1, 3), 16), parseInt(gradientEnd.slice(1, 3), 16), frac));
      const g = Math.round(lerpColor(parseInt(color.slice(3, 5), 16), parseInt(gradientEnd.slice(3, 5), 16), frac));
      const b = Math.round(lerpColor(parseInt(color.slice(5, 7), 16), parseInt(gradientEnd.slice(5, 7), 16), frac));
      ctx.strokeStyle = 'rgb(' + r + ', ' + g + ', ' + b + ')';
      const [cx0, cy0] = transform.toCanvas(xs[k], ys[k]);
      const [cx1, cy1] = transform.toCanvas(xs[k + 1], ys[k + 1]);
      ctx.beginPath();
      ctx.moveTo(cx0, cy0);
      ctx.lineTo(cx1, cy1);
      ctx.stroke();
    }
  } else {
    ctx.strokeStyle = color;
    ctx.beginPath();
    const [cx0, cy0] = transform.toCanvas(xs[0], ys[0]);
    ctx.moveTo(cx0, cy0);
    for (let k = 1; k < xs.length; k++) {
      const [cx, cy] = transform.toCanvas(xs[k], ys[k]);
      ctx.lineTo(cx, cy);
    }
    ctx.stroke();
  }

  ctx.setLineDash([]);

  // Start marker (circle)
  const [sx, sy] = transform.toCanvas(xs[0], ys[0]);
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(sx, sy, 4, 0, Math.PI * 2);
  ctx.fill();

  // End marker (small diamond)
  const [ex, ey] = transform.toCanvas(xs[xs.length - 1], ys[ys.length - 1]);
  ctx.fillStyle = gradientEnd || color;
  ctx.beginPath();
  ctx.moveTo(ex, ey - 4);
  ctx.lineTo(ex + 4, ey);
  ctx.lineTo(ex, ey + 4);
  ctx.lineTo(ex - 4, ey);
  ctx.closePath();
  ctx.fill();
}

function lerpColor(a, b, t) {
  return a + (b - a) * t;
}

function drawEquilibrium(ctx, eqX, eqY, transform, isStable) {
  const [cx, cy] = transform.toCanvas(eqX, eqY);
  const r = 7;

  if (isStable) {
    // Filled green circle
    ctx.fillStyle = 'rgba(16, 185, 129, 0.8)';
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 1.5;
    ctx.stroke();
  } else {
    // Open red circle with X
    ctx.strokeStyle = '#ef4444';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.stroke();
    // X through it
    const d = r * 0.6;
    ctx.beginPath();
    ctx.moveTo(cx - d, cy - d);
    ctx.lineTo(cx + d, cy + d);
    ctx.moveTo(cx + d, cy - d);
    ctx.lineTo(cx - d, cy + d);
    ctx.stroke();
  }
}

function drawROAOverlay(ctx, roaData, transform, cw, ch) {
  if (!roaData?.x_vals || !roaData?.y_vals || !roaData?.result) return;

  const { x_vals, y_vals, result } = roaData;
  const nx = x_vals.length;
  const ny = y_vals.length;

  for (let i = 0; i < ny - 1; i++) {
    for (let j = 0; j < nx - 1; j++) {
      const val = result[i]?.[j];
      if (val == null) continue;
      const [cx0, cy0] = transform.toCanvas(x_vals[j], y_vals[i + 1]);
      const [cx1, cy1] = transform.toCanvas(x_vals[j + 1], y_vals[i]);
      const w = cx1 - cx0;
      const h = cy1 - cy0;

      if (val === 1) {
        ctx.fillStyle = 'rgba(16, 185, 129, 0.08)';
      } else if (val === -1) {
        ctx.fillStyle = 'rgba(239, 68, 68, 0.08)';
      } else {
        ctx.fillStyle = 'rgba(245, 158, 11, 0.06)';
      }
      ctx.fillRect(cx0, cy0, w, h);
    }
  }
}

function drawAxisLabels(ctx, transform, cw, ch, isDark) {
  // Origin label
  if (transform.xMin <= 0 && transform.xMax >= 0 && transform.yMin <= 0 && transform.yMax >= 0) {
    const [ox, oy] = transform.toCanvas(0, 0);
    ctx.fillStyle = isDark ? 'rgba(148, 163, 184, 0.4)' : 'rgba(100, 116, 139, 0.5)';
    ctx.font = '10px "Fira Code", monospace';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillText('0', ox + 4, oy + 3);
  }
}

// ============================================================================
// Metrics Strip
// ============================================================================

const MetricsStrip = memo(function MetricsStrip({ metadata }) {
  if (!metadata) return null;

  const isStable = metadata.is_stable;
  const isControllable = metadata.is_controllable;
  const perf = metadata.performance || {};
  const diverged = metadata.diverged || perf.diverged;
  const nStates = metadata.n_states || 0;
  const ctrlRank = metadata.controllability_rank;

  // Compute K norm
  let kNorm = null;
  if (metadata.K_matrix) {
    let sum = 0;
    for (const row of metadata.K_matrix) {
      for (const v of row) {
        sum += v * v;
      }
    }
    kNorm = Math.sqrt(sum);
  }

  return (
    <div className="ncl-metrics-strip">
      {/* Stability */}
      <div className={'ncl-metric-badge ' + (isStable ? 'stable' : 'unstable')}>
        {isStable ? '\u2713 Stable' : '\u2717 Unstable'}
      </div>

      {/* Controllability */}
      <div className={'ncl-metric-badge ' + (isControllable ? 'controllable' : 'not-controllable')}>
        {isControllable
          ? 'Controllable (rank ' + ctrlRank + '/' + nStates + ')'
          : 'Not Controllable (rank ' + ctrlRank + '/' + nStates + ')'
        }
      </div>

      {/* Diverged warning */}
      {diverged && (
        <div className="ncl-metric-badge diverged">
          Diverged
        </div>
      )}

      {/* CL Eigenvalues */}
      {metadata.cl_eigenvalue_strings?.length > 0 && (
        <div className="ncl-metric-badge">
          <span className="ncl-metric-label">CL Eigs:</span>
          <span className="ncl-metric-value">
            {metadata.cl_eigenvalue_strings.slice(0, 4).join(', ')}
            {metadata.cl_eigenvalue_strings.length > 4 ? ', ...' : ''}
          </span>
        </div>
      )}

      {/* Convergence time */}
      {perf.convergence_time != null && !diverged && (
        <div className="ncl-metric-badge">
          <span className="ncl-metric-label">T_conv</span>
          <span className="ncl-metric-value">
            {perf.convergence_time.toFixed(2)}s
          </span>
        </div>
      )}

      {/* K norm */}
      {kNorm != null && (
        <div className="ncl-metric-badge">
          <span className="ncl-metric-label">||K||</span>
          <span className="ncl-metric-value">
            {kNorm.toFixed(2)}
          </span>
        </div>
      )}

      {/* Final error */}
      {perf.final_error != null && !diverged && (
        <div className="ncl-metric-badge">
          <span className="ncl-metric-label">e_final</span>
          <span className="ncl-metric-value">
            {perf.final_error < 0.001 ? '< 0.001' : perf.final_error.toFixed(3)}
          </span>
        </div>
      )}
    </div>
  );
});

// ============================================================================
// Derivation Chain (Collapsible)
// ============================================================================

const DerivationChain = memo(function DerivationChain({ metadata, isDark }) {
  const [isOpen, setIsOpen] = useState(false);
  const [katexReady, setKatexReady] = useState(!!katexModule);

  useEffect(() => {
    loadKatex(() => setKatexReady(true));
  }, []);

  if (!metadata) return null;

  const steps = [];

  // 1. Nonlinear ODE
  if (metadata.ode_latex) {
    steps.push({
      label: 'Nonlinear Dynamics',
      latex: metadata.ode_latex,
      display: true,
    });
  }

  // 2. Linearized A matrix
  if (metadata.A_latex) {
    const pointLabel = metadata.is_operating_point
      ? 'at operating point' : 'at equilibrium';
    steps.push({
      label: 'Linearized A Matrix (' + pointLabel + ')',
      latex: metadata.A_latex,
      display: true,
    });
  }

  // 3. Linearized B matrix
  if (metadata.B_latex) {
    steps.push({
      label: 'Input B Matrix',
      latex: metadata.B_latex,
      display: true,
    });
  }

  // 4. Controller gain K
  if (metadata.K_latex) {
    steps.push({
      label: 'Controller Gain (' + (metadata.controller_method || 'unknown') + ')',
      latex: metadata.K_latex,
      display: true,
    });
  }

  // 5. CL eigenvalues
  if (metadata.cl_eigenvalue_strings?.length > 0) {
    steps.push({
      label: 'Closed-Loop Eigenvalues',
      eigenvalues: metadata.cl_eigenvalue_strings,
      olEigenvalues: metadata.ol_eigenvalue_strings,
    });
  }

  return (
    <div className="ncl-derivation">
      <button className="ncl-derivation-toggle" onClick={() => setIsOpen(!isOpen)}>
        <span>Linearization and Controller Design</span>
        <span className="ncl-derivation-chevron">{isOpen ? '\u25BE' : '\u25B8'}</span>
      </button>
      {isOpen && (
        <div className="ncl-derivation-content">
          {steps.map((step, idx) => (
            <React.Fragment key={idx}>
              {idx > 0 && <div className="ncl-derivation-arrow">{'\u2193'}</div>}
              <div className="ncl-derivation-step">
                <div className="ncl-derivation-label">{step.label}</div>
                {step.latex && katexReady ? (
                  <div
                    className="ncl-derivation-math"
                    dangerouslySetInnerHTML={{ __html: renderLatex(step.latex, step.display) }}
                  />
                ) : step.latex ? (
                  <div className="ncl-derivation-math">{step.latex}</div>
                ) : null}
                {step.eigenvalues && (
                  <React.Fragment>
                    {step.olEigenvalues && (
                      <React.Fragment>
                        <div className="ncl-derivation-label ncl-derivation-label--spaced">
                          Open-Loop Eigenvalues
                        </div>
                        <div className="ncl-eigenvalue-list">
                          {step.olEigenvalues.map((ev, k) => (
                            <span
                              key={'ol-' + k}
                              className={'ncl-eigenvalue-chip ' + getEigenvalueClass(ev)}
                            >
                              {ev}
                            </span>
                          ))}
                        </div>
                      </React.Fragment>
                    )}
                    <div className="ncl-derivation-label ncl-derivation-label--spaced">
                      Closed-Loop Eigenvalues
                    </div>
                    <div className="ncl-eigenvalue-list">
                      {step.eigenvalues.map((ev, k) => (
                        <span
                          key={'cl-' + k}
                          className={'ncl-eigenvalue-chip ' + getEigenvalueClass(ev)}
                        >
                          {ev}
                        </span>
                      ))}
                    </div>
                  </React.Fragment>
                )}
              </div>
            </React.Fragment>
          ))}
        </div>
      )}
    </div>
  );
});

function getEigenvalueClass(evStr) {
  // Parse real part from eigenvalue string to determine color
  if (!evStr) return 'zero';
  const s = evStr.trim();
  // Match patterns like "-2.1", "-2.1 + 1.3j", "0", "4.43"
  const realMatch = s.match(/^(-?[\d.]+)/);
  if (!realMatch) return 'zero';
  const realPart = parseFloat(realMatch[1]);
  if (realPart < -1e-10) return 'negative';
  if (realPart > 1e-10) return 'positive';
  return 'zero';
}

// ============================================================================
// Main Viewer
// ============================================================================

function NonlinearControlLabViewer({ metadata, plots, currentParams, onParamChange, onButtonClick }) {
  const isDark = useIsDark();

  // Find plots by ID
  const findPlot = useCallback((id) => plots?.find(p => p.id === id), [plots]);
  const timeResponsePlot = findPlot('time_response');
  const controlEffortPlot = findPlot('control_effort');
  const eigenvalueMapPlot = findPlot('eigenvalue_map');
  const roaHeatmapPlot = findPlot('roa_heatmap');

  // Theme-aware Plotly layout
  const themeLayout = useMemo(() => ({
    paper_bgcolor: isDark ? '#0a0e27' : 'rgba(255,255,255,0.98)',
    plot_bgcolor: isDark ? '#131b2e' : '#f8fafc',
    font: {
      family: 'Inter, sans-serif',
      size: 12,
      color: isDark ? '#f1f5f9' : '#1e293b',
    },
    xaxis: {
      gridcolor: isDark ? 'rgba(148,163,184,0.1)' : 'rgba(148,163,184,0.2)',
      zerolinecolor: isDark ? 'rgba(148,163,184,0.3)' : 'rgba(148,163,184,0.4)',
    },
    yaxis: {
      gridcolor: isDark ? 'rgba(148,163,184,0.1)' : 'rgba(148,163,184,0.2)',
      zerolinecolor: isDark ? 'rgba(148,163,184,0.3)' : 'rgba(148,163,184,0.4)',
    },
  }), [isDark]);

  // Render a Plotly plot with theme overrides
  const renderPlot = useCallback((plotData, height) => {
    if (!plotData) return null;
    const layout = {
      ...plotData.layout,
      ...themeLayout,
      xaxis: { ...plotData.layout?.xaxis, ...themeLayout.xaxis },
      yaxis: { ...plotData.layout?.yaxis, ...themeLayout.yaxis },
      legend: {
        ...plotData.layout?.legend,
        font: { color: isDark ? '#94a3b8' : '#64748b', size: 11 },
        bgcolor: 'rgba(0,0,0,0)',
      },
      autosize: true,
      height: height || undefined,
      datarevision: plotData.id + '-' + Date.now(),
      uirevision: plotData.id,
    };
    return (
      <div className="ncl-plot-card" key={plotData.id} style={height ? { height: height + 'px' } : undefined}>
        <Plot
          data={plotData.data || []}
          layout={layout}
          config={{
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['select2d', 'lasso2d'],
            displaylogo: false,
          }}
          useResizeHandler
          style={{ width: '100%', height: '100%' }}
        />
      </div>
    );
  }, [themeLayout, isDark]);

  // Canvas click -> set initial condition offsets
  const handleCanvasClick = useCallback((sx, sy) => {
    if (!metadata || !onParamChange) return;
    const projX = metadata.projection_x ?? 0;
    const projY = metadata.projection_y ?? 2;
    const xEq = metadata.x_eq || [];

    // Compute offsets from equilibrium
    const offsetX = sx - (xEq[projX] || 0);
    const offsetY = sy - (xEq[projY] || 0);

    // Map projection indices to ic_offset parameters (1-indexed)
    onParamChange('ic_offset_' + (projX + 1), offsetX);
    // Small delay so the backend processes sequentially
    setTimeout(() => {
      onParamChange('ic_offset_' + (projY + 1), offsetY);
    }, 50);
  }, [metadata, onParamChange]);

  // Loading state
  if (!metadata) {
    return (
      <div className="ncl-viewer" style={{ padding: '40px', color: 'var(--text-muted)', textAlign: 'center' }}>
        Loading simulation...
      </div>
    );
  }

  return (
    <div className="ncl-viewer">
      {/* Error banner */}
      {metadata.error && (
        <div className="ncl-error-banner">{metadata.error}</div>
      )}

      {/* Design error (controller) */}
      {metadata.design_error && (
        <div className="ncl-design-error">{metadata.design_error}</div>
      )}

      {/* Plant description */}
      {metadata.plant_description && (
        <div className="ncl-plant-desc">{metadata.plant_description}</div>
      )}

      {/* Equilibrium / operating point info */}
      {metadata.x_eq?.length > 0 && (
        <div className="ncl-eq-info">
          <span className="ncl-eq-label">
            {metadata.is_operating_point ? 'Operating Point' : 'Equilibrium'}:
          </span>
          <span className="ncl-eq-value">
            x* = [{metadata.x_eq.map(v => v.toFixed(4)).join(', ')}]
          </span>
          {metadata.is_operating_point && metadata.u_eq?.length > 0 && (
            <span className="ncl-eq-value">
              u* = [{metadata.u_eq.map(v => v.toFixed(4)).join(', ')}]
            </span>
          )}
        </div>
      )}

      {/* Equilibrium validation warning */}
      {metadata.eq_warning && (
        <div className="ncl-eq-warning">{metadata.eq_warning}</div>
      )}

      {/* Main layout: Phase Portrait (left) + Plots (right) */}
      <div className="ncl-main-layout">
        {/* Left: Canvas Phase Portrait */}
        <div className="ncl-phase-column">
          <PhasePortraitCanvas
            metadata={metadata}
            isDark={isDark}
            onCanvasClick={handleCanvasClick}
          />
        </div>

        {/* Right: Stacked Plotly plots */}
        <div className="ncl-plots-column">
          {renderPlot(timeResponsePlot, 220)}
          {renderPlot(controlEffortPlot, 200)}
          {renderPlot(eigenvalueMapPlot, 220)}
        </div>
      </div>

      {/* Metrics Strip */}
      <MetricsStrip metadata={metadata} />

      {/* KaTeX Derivation Chain */}
      <DerivationChain metadata={metadata} isDark={isDark} />

      {/* ROA Heatmap (full width, only when computed) */}
      {metadata.has_roa && roaHeatmapPlot && (
        <div className="ncl-roa-section">
          <div className="ncl-roa-header">Region of Attraction Estimate</div>
          {renderPlot(roaHeatmapPlot, 350)}
        </div>
      )}
    </div>
  );
}

export default memo(NonlinearControlLabViewer);
