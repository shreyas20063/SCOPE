/**
 * MassSpringViewer Component
 *
 * Premium viewer for Mass-Spring-Damper simulation.
 * Left: Full-height canvas 2D animation with physics-reactive visuals,
 *       motion trail, velocity arrow, glow effects, and smooth coil spring.
 * Right: Stacked Plotly plots (response, phase portrait, energy).
 */

import React, { useState, useEffect, useRef, useCallback, Suspense, lazy } from 'react';
import Plot from 'react-plotly.js';
import './MassSpringViewer.css';

const MassSpring3D = lazy(() => import('./MassSpring3D'));

/* ------------------------------------------------------------------ */
/*  Theme hook                                                        */
/* ------------------------------------------------------------------ */

function useTheme() {
  const [theme, setTheme] = React.useState(() =>
    document.documentElement.getAttribute('data-theme') || 'dark'
  );

  React.useEffect(() => {
    const obs = new MutationObserver(() => {
      setTheme(document.documentElement.getAttribute('data-theme') || 'dark');
    });
    obs.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme'],
    });
    return () => obs.disconnect();
  }, []);

  return theme;
}

/* ------------------------------------------------------------------ */
/*  Constants                                                         */
/* ------------------------------------------------------------------ */

const SPEED_OPTIONS = [0.5, 1, 2, 4];
const TRAIL_LENGTH = 25;

/* ------------------------------------------------------------------ */
/*  Canvas drawing helpers                                            */
/* ------------------------------------------------------------------ */

function drawWall(ctx, w, wallY, wallH, isDark) {
  const grad = ctx.createLinearGradient(0, wallY, 0, wallY + wallH);
  if (isDark) {
    grad.addColorStop(0, '#1e293b');
    grad.addColorStop(1, '#334155');
  } else {
    grad.addColorStop(0, '#d1d5db');
    grad.addColorStop(1, '#9ca3af');
  }
  ctx.fillStyle = grad;
  ctx.fillRect(0, wallY, w, wallH);

  // Hatching
  ctx.save();
  ctx.strokeStyle = isDark ? 'rgba(148,163,184,0.25)' : 'rgba(75,85,99,0.3)';
  ctx.lineWidth = 1;
  for (let x = 0; x < w + wallH; x += 8) {
    ctx.beginPath();
    ctx.moveTo(x, wallY + wallH);
    ctx.lineTo(x - wallH, wallY);
    ctx.stroke();
  }
  ctx.restore();

  // Bottom edge
  ctx.strokeStyle = isDark ? '#475569' : '#6b7280';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(0, wallY + wallH);
  ctx.lineTo(w, wallY + wallH);
  ctx.stroke();
}

function drawSpringCoil(ctx, x, y1, y2, numCoils, color, amplitude) {
  const len = y2 - y1;
  if (Math.abs(len) < 8) return;

  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineWidth = 2.5;
  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';

  const leaderLen = Math.abs(len) * 0.07;
  const coilLen = Math.abs(len) - 2 * leaderLen;
  const dir = Math.sign(len);

  ctx.beginPath();
  ctx.moveTo(x, y1);
  ctx.lineTo(x, y1 + dir * leaderLen);

  const pts = numCoils * 24;
  for (let i = 0; i <= pts; i++) {
    const t = i / pts;
    const yy = y1 + dir * leaderLen + t * dir * coilLen;
    const dx = amplitude * Math.sin(t * numCoils * 2 * Math.PI);
    ctx.lineTo(x + dx, yy);
  }

  ctx.lineTo(x, y2);
  ctx.stroke();
  ctx.restore();
}

function drawDamperUnit(ctx, x, y1, y2, color, isDark) {
  const len = y2 - y1;
  if (Math.abs(len) < 15) return;

  const cylW = 20;
  const cylH = Math.min(Math.abs(len) * 0.32, 50);
  const midY = (y1 + y2) / 2;
  const cylTopY = midY - cylH * 0.3;

  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineCap = 'round';

  // Rod from top to piston
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(x, y1);
  ctx.lineTo(x, cylTopY + 2);
  ctx.stroke();

  // Piston head
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(x - cylW / 2 + 2, cylTopY + 5);
  ctx.lineTo(x + cylW / 2 - 2, cylTopY + 5);
  ctx.stroke();

  // Cylinder body with fill
  ctx.lineWidth = 2;
  ctx.fillStyle = isDark
    ? 'rgba(245, 158, 11, 0.06)'
    : 'rgba(217, 119, 6, 0.06)';
  const cylBodyTop = cylTopY + 10;
  ctx.fillRect(x - cylW / 2, cylBodyTop, cylW, cylH);
  ctx.strokeRect(x - cylW / 2, cylBodyTop, cylW, cylH);

  // Rod from cylinder to mass
  ctx.beginPath();
  ctx.moveTo(x, cylBodyTop + cylH);
  ctx.lineTo(x, y2);
  ctx.stroke();

  ctx.restore();
}

/* ------------------------------------------------------------------ */
/*  Spring Animation Component                                        */
/* ------------------------------------------------------------------ */

function SpringAnimation({ visualization2D, theme, systemInfo }) {
  const canvasRef = useRef(null);
  const frameRef = useRef(0);
  const lastTimeRef = useRef(0);
  const playingRef = useRef(true);
  const speedRef = useRef(1);
  const trailRef = useRef([]);

  const [isPlaying, setIsPlaying] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);
  const [speed, setSpeed] = useState(1);

  const isDark = theme === 'dark';

  useEffect(() => { playingRef.current = isPlaying; }, [isPlaying]);
  useEffect(() => { speedRef.current = speed; }, [speed]);

  // Reset on data change
  useEffect(() => {
    frameRef.current = 0;
    lastTimeRef.current = performance.now();
    trailRef.current = [];
    setCurrentTime(0);
    setIsPlaying(true);
  }, [visualization2D]);

  /* ---------- main draw ---------- */

  const drawFrame = useCallback((ctx, w, h, frameIndex, viz) => {
    const { input_position, mass_position, velocity, time, num_frames } = viz;
    const idx = Math.min(frameIndex, num_frames - 1);
    const baseDisp = input_position[idx] || 0;
    const massDisp = mass_position[idx] || 0;
    const vel = velocity?.[idx] || 0;

    // --- coordinate mapping (shared scale preserves amplitude ratio) ---
    // The wall/ceiling MOVES with x(t). Spring/damper hang from its bottom.
    // Mass moves with y(t). Both use the same px-per-unit scale so
    // resonance magnification is visible (output >> input at resonance).
    const cx = w / 2;
    const wallH = h * 0.045;
    const wallRestY = h * 0.08;
    const massRestY = h * 0.58;

    const wallMaxTravel = h * 0.07;
    const massMaxTravel = h * 0.17;

    const inputMaxAbs = Math.max(0.1, Math.max(...input_position.map(Math.abs)));
    const massMaxAbs = Math.max(0.1, Math.max(...mass_position.map(Math.abs)));
    const globalMaxAbs = Math.max(inputMaxAbs, massMaxAbs);

    // Shared scale based on the larger signal; wall uses a tighter cap
    const sharedScale = massMaxTravel / globalMaxAbs;
    const wallScale = Math.min(sharedScale, wallMaxTravel / inputMaxAbs);

    // Wall moves with input — its bottom edge is where spring/damper attach
    const wallDisp = baseDisp * wallScale;
    const wallY = Math.max(0.005 * h, Math.min(h * 0.18, wallRestY + wallDisp));
    const wallBottom = wallY + wallH;       // spring/damper anchor point

    const massTopY = Math.max(h * 0.36, Math.min(h * 0.78, massRestY + massDisp * sharedScale));

    const maxVel = Math.max(0.1, ...velocity.map(Math.abs));
    const velNorm = Math.min(1, Math.abs(vel) / maxVel);

    const blockH = 36;

    // Update trail
    trailRef.current.push({ y: massTopY + blockH / 2 });
    if (trailRef.current.length > TRAIL_LENGTH) trailRef.current.shift();

    // === DRAW ===

    // Background gradient
    const bg = ctx.createLinearGradient(0, 0, 0, h);
    if (isDark) {
      bg.addColorStop(0, '#0a0e27');
      bg.addColorStop(0.5, '#0f1629');
      bg.addColorStop(1, '#131b2e');
    } else {
      bg.addColorStop(0, '#f8fafc');
      bg.addColorStop(1, '#e2e8f0');
    }
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, w, h);

    // Subtle grid
    ctx.save();
    ctx.strokeStyle = isDark ? 'rgba(148,163,184,0.035)' : 'rgba(100,116,139,0.07)';
    ctx.lineWidth = 0.5;
    const gridSize = 25;
    for (let gy = 0; gy < h; gy += gridSize) {
      ctx.beginPath(); ctx.moveTo(0, gy); ctx.lineTo(w, gy); ctx.stroke();
    }
    for (let gx = 0; gx < w; gx += gridSize) {
      ctx.beginPath(); ctx.moveTo(gx, 0); ctx.lineTo(gx, h); ctx.stroke();
    }
    ctx.restore();

    // Rest-position reference line (faint, so you can see the wall moved)
    const wallRestBottom = wallRestY + wallH;
    if (Math.abs(wallDisp) > 1) {
      ctx.save();
      ctx.setLineDash([3, 3]);
      ctx.strokeStyle = isDark ? 'rgba(59,130,246,0.2)' : 'rgba(37,99,235,0.2)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, wallRestBottom);
      ctx.lineTo(w, wallRestBottom);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.restore();
    }

    // Moving wall/ceiling — this IS the base that x(t) displaces
    drawWall(ctx, w, wallY, wallH, isDark);

    // x(t) displacement arrow beside the wall
    if (Math.abs(wallDisp) > 2) {
      const arrowX = 10;
      const arrowFrom = wallRestBottom;
      const arrowTo = wallBottom;
      ctx.save();
      ctx.strokeStyle = '#3b82f6';
      ctx.lineWidth = 2;
      ctx.lineCap = 'round';
      ctx.beginPath();
      ctx.moveTo(arrowX, arrowFrom);
      ctx.lineTo(arrowX, arrowTo);
      ctx.stroke();
      // arrowhead
      const dir = Math.sign(arrowTo - arrowFrom);
      ctx.fillStyle = '#3b82f6';
      ctx.beginPath();
      ctx.moveTo(arrowX, arrowTo);
      ctx.lineTo(arrowX - 3, arrowTo - dir * 6);
      ctx.lineTo(arrowX + 3, arrowTo - dir * 6);
      ctx.closePath();
      ctx.fill();
      ctx.font = '600 9px "Fira Code", monospace';
      ctx.textAlign = 'left';
      ctx.fillText('x(t)', arrowX + 6, (arrowFrom + arrowTo) / 2 + 3);
      ctx.restore();
    }

    // Attachment bar at wall bottom (spring/damper hang from here)
    const barHalfW = Math.min(w * 0.16, 34);
    const springX = cx - barHalfW;
    const damperX = cx + barHalfW;

    ctx.save();
    ctx.strokeStyle = isDark ? '#64748b' : '#94a3b8';
    ctx.lineWidth = 2.5;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(springX, wallBottom);
    ctx.lineTo(damperX, wallBottom);
    ctx.stroke();
    ctx.fillStyle = isDark ? '#475569' : '#9ca3af';
    ctx.beginPath();
    ctx.arc(cx, wallBottom, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    // Spring (from wall bottom to mass)
    const springAmp = Math.min(barHalfW * 0.55, 13);
    drawSpringCoil(ctx, springX, wallBottom, massTopY, 10, isDark ? '#3b82f6' : '#2563eb', springAmp);

    // Damper (from wall bottom to mass)
    drawDamperUnit(ctx, damperX, wallBottom, massTopY, isDark ? '#f59e0b' : '#d97706', isDark);

    // Labels for k and b
    ctx.save();
    ctx.font = '600 11px "Fira Code", monospace';
    const labelMidY = (wallBottom + massTopY) / 2;
    ctx.fillStyle = isDark ? '#60a5fa' : '#2563eb';
    ctx.textAlign = 'center';
    ctx.fillText('k', springX - springAmp - 10, labelMidY);
    ctx.fillStyle = isDark ? '#fbbf24' : '#d97706';
    ctx.fillText('b', damperX + 14, labelMidY);
    ctx.restore();

    // Motion trail
    ctx.save();
    for (let i = 0; i < trailRef.current.length; i++) {
      const pt = trailRef.current[i];
      const age = 1 - i / trailRef.current.length;
      const alpha = (1 - age) * 0.35 * (0.3 + velNorm * 0.7);
      const radius = (1 - age) * 3.5 + 0.5;
      ctx.fillStyle = `rgba(20, 184, 166, ${alpha})`;
      ctx.beginPath();
      ctx.arc(cx, pt.y, radius, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();

    // Mass block with glow
    const blockW = Math.min(w * 0.30, 76);
    const massLeft = cx - blockW / 2;

    ctx.save();
    const glowColor = velNorm > 0.5
      ? `rgba(239, 68, 68, ${0.3 + velNorm * 0.4})`
      : `rgba(20, 184, 166, ${0.15 + velNorm * 0.2})`;
    ctx.shadowColor = glowColor;
    ctx.shadowBlur = 10 + velNorm * 20;

    const mGrad = ctx.createLinearGradient(0, massTopY, 0, massTopY + blockH);
    mGrad.addColorStop(0, velNorm > 0.5 ? '#f87171' : '#ef4444');
    mGrad.addColorStop(1, velNorm > 0.5 ? '#dc2626' : '#b91c1c');
    ctx.fillStyle = mGrad;
    ctx.beginPath();
    ctx.roundRect(massLeft, massTopY, blockW, blockH, 6);
    ctx.fill();

    ctx.shadowBlur = 0;
    ctx.strokeStyle = `rgba(255,255,255,${0.15 + velNorm * 0.15})`;
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.restore();

    // "m" on mass
    ctx.save();
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 15px Inter, -apple-system, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('m', cx, massTopY + blockH / 2);
    ctx.restore();

    // Connection lines (spring/damper endpoints to mass edges)
    ctx.save();
    ctx.strokeStyle = isDark ? '#64748b' : '#94a3b8';
    ctx.lineWidth = 2;
    // Left: spring to mass left
    ctx.beginPath();
    ctx.moveTo(springX, massTopY);
    ctx.lineTo(massLeft, massTopY);
    ctx.stroke();
    // Right: damper to mass right
    ctx.beginPath();
    ctx.moveTo(damperX, massTopY);
    ctx.lineTo(massLeft + blockW, massTopY);
    ctx.stroke();
    ctx.restore();

    // Velocity arrow
    if (Math.abs(vel) > maxVel * 0.04) {
      const arrowLen = velNorm * 35;
      const arrowDir = vel > 0 ? 1 : -1;
      const arrowX = massLeft + blockW + 10;
      const arrowBaseY = massTopY + blockH / 2;
      const arrowTipY = arrowBaseY + arrowDir * arrowLen;

      ctx.save();
      ctx.strokeStyle = '#14b8a6';
      ctx.lineWidth = 2;
      ctx.lineCap = 'round';
      ctx.beginPath();
      ctx.moveTo(arrowX, arrowBaseY);
      ctx.lineTo(arrowX, arrowTipY);
      ctx.stroke();

      ctx.fillStyle = '#14b8a6';
      ctx.beginPath();
      ctx.moveTo(arrowX, arrowTipY);
      ctx.lineTo(arrowX - 3.5, arrowTipY - arrowDir * 7);
      ctx.lineTo(arrowX + 3.5, arrowTipY - arrowDir * 7);
      ctx.closePath();
      ctx.fill();

      ctx.font = '600 9px "Fira Code", monospace';
      ctx.textAlign = 'left';
      ctx.fillText('v', arrowX + 6, arrowBaseY);
      ctx.restore();
    }

    // Equilibrium reference line
    ctx.save();
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = isDark ? 'rgba(148,163,184,0.2)' : 'rgba(100,116,139,0.25)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(cx - blockW / 2 - 15, massRestY);
    ctx.lineTo(cx + blockW / 2 + 15, massRestY);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.font = '9px "Fira Code", monospace';
    ctx.fillStyle = isDark ? '#475569' : '#94a3b8';
    ctx.textAlign = 'left';
    ctx.fillText('eq', cx + blockW / 2 + 18, massRestY + 3);
    ctx.restore();

    // Displacement readouts
    const readY = h * 0.78;
    const readX = 14;
    const lineH = 18;

    ctx.save();
    ctx.font = '12px "Fira Code", monospace';
    ctx.textAlign = 'left';

    ctx.fillStyle = '#3b82f6';
    ctx.fillText(`x(t) = ${baseDisp >= 0 ? ' ' : ''}${baseDisp.toFixed(3)} m`, readX, readY);

    ctx.fillStyle = '#ef4444';
    ctx.fillText(`y(t) = ${massDisp >= 0 ? ' ' : ''}${massDisp.toFixed(3)} m`, readX, readY + lineH);

    ctx.fillStyle = '#14b8a6';
    ctx.fillText(`v(t) = ${vel >= 0 ? ' ' : ''}${vel.toFixed(3)} m/s`, readX, readY + lineH * 2);
    ctx.restore();

    // Paused indicator
    if (!playingRef.current) {
      ctx.save();
      ctx.fillStyle = isDark ? 'rgba(148,163,184,0.5)' : 'rgba(100,116,139,0.5)';
      ctx.font = '600 11px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('PAUSED', cx, h * 0.92);
      ctx.restore();
    }

    // Progress bar
    const progress = idx / Math.max(1, num_frames - 1);
    const barX = 14;
    const barW = w - 28;
    const barY = h - 10;
    const barH = 3;

    ctx.save();
    ctx.fillStyle = isDark ? 'rgba(148,163,184,0.08)' : 'rgba(100,116,139,0.1)';
    ctx.beginPath();
    ctx.roundRect(barX, barY, barW, barH, 1.5);
    ctx.fill();

    const progGrad = ctx.createLinearGradient(barX, 0, barX + barW, 0);
    progGrad.addColorStop(0, '#14b8a6');
    progGrad.addColorStop(1, '#06b6d4');
    ctx.fillStyle = progGrad;
    ctx.beginPath();
    ctx.roundRect(barX, barY, Math.max(barH, barW * progress), barH, 1.5);
    ctx.fill();
    ctx.restore();
  }, [isDark]);

  /* ---------- animation loop ---------- */

  useEffect(() => {
    if (!visualization2D || visualization2D.num_frames < 2) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    let w, h;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      w = rect.width;
      h = rect.height;
    };

    resize();

    const resizeObs = new ResizeObserver(resize);
    resizeObs.observe(canvas);

    const frameDt = visualization2D.dt * 1000;
    let animId;

    const loop = (ts) => {
      if (playingRef.current) {
        const elapsed = ts - lastTimeRef.current;
        const adjusted = frameDt / speedRef.current;
        if (elapsed >= adjusted) {
          lastTimeRef.current = ts;
          frameRef.current = (frameRef.current + 1) % visualization2D.num_frames;
          setCurrentTime(visualization2D.time[frameRef.current] || 0);
        }
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      drawFrame(ctx, w, h, frameRef.current, visualization2D);
      animId = requestAnimationFrame(loop);
    };

    lastTimeRef.current = performance.now();
    animId = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(animId);
      resizeObs.disconnect();
    };
  }, [visualization2D, drawFrame]);

  /* ---------- controls ---------- */

  const togglePlay = () => setIsPlaying((p) => !p);

  const restart = () => {
    frameRef.current = 0;
    lastTimeRef.current = performance.now();
    trailRef.current = [];
    setCurrentTime(0);
  };

  const cycleSpeed = () => {
    setSpeed((s) => {
      const i = SPEED_OPTIONS.indexOf(s);
      return SPEED_OPTIONS[(i + 1) % SPEED_OPTIONS.length];
    });
  };

  return (
    <div className="ms-animation-panel">
      <canvas ref={canvasRef} className="ms-canvas" />

      <div className="ms-animation-controls">
        <button className="ms-ctrl-btn" onClick={togglePlay} title={isPlaying ? 'Pause' : 'Play'}>
          {isPlaying ? '\u23F8' : '\u25B6'}
        </button>
        <button className="ms-ctrl-btn" onClick={restart} title="Restart">
          {'\u21BA'}
        </button>
        <button className="ms-ctrl-btn ms-speed-btn" onClick={cycleSpeed} title="Playback speed">
          {speed}&times;
        </button>
        <span className="ms-time-label">
          {currentTime.toFixed(2)} / {visualization2D?.total_time?.toFixed(1) ?? '?'} s
        </span>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Plot component                                                     */
/* ------------------------------------------------------------------ */

function MSPlot({ plot, theme }) {
  const isDark = theme === 'dark';

  const layout = {
    ...plot.layout,
    title: {
      text: plot.title || 'Plot',
      font: { color: isDark ? '#f1f5f9' : '#1e293b', size: 14 },
      x: 0.5,
      xanchor: 'center',
    },
    paper_bgcolor: isDark ? '#0f172a' : 'rgba(255,255,255,0.98)',
    plot_bgcolor: isDark ? '#1e293b' : '#f8fafc',
    font: {
      color: isDark ? '#e2e8f0' : '#1e293b',
      family: 'Inter, -apple-system, sans-serif',
      size: 11,
    },
    xaxis: {
      ...plot.layout?.xaxis,
      gridcolor: isDark ? 'rgba(71,85,105,0.35)' : 'rgba(100,116,139,0.18)',
      zerolinecolor: isDark ? 'rgba(148,163,184,0.4)' : 'rgba(100,116,139,0.4)',
      zerolinewidth: 1.5,
      tickfont: { color: isDark ? '#94a3b8' : '#475569', size: 10 },
      title: {
        text: plot.layout?.xaxis?.title || '',
        font: { color: isDark ? '#94a3b8' : '#334155', size: 11 },
      },
      showline: true,
      linecolor: isDark ? '#334155' : '#cbd5e1',
    },
    yaxis: {
      ...plot.layout?.yaxis,
      gridcolor: isDark ? 'rgba(71,85,105,0.35)' : 'rgba(100,116,139,0.18)',
      zerolinecolor: isDark ? 'rgba(148,163,184,0.4)' : 'rgba(100,116,139,0.4)',
      zerolinewidth: 1.5,
      tickfont: { color: isDark ? '#94a3b8' : '#475569', size: 10 },
      title: {
        text: plot.layout?.yaxis?.title || '',
        font: { color: isDark ? '#94a3b8' : '#334155', size: 11 },
      },
      showline: true,
      linecolor: isDark ? '#334155' : '#cbd5e1',
    },
    legend: {
      ...plot.layout?.legend,
      font: { color: isDark ? '#e2e8f0' : '#1e293b', size: 10 },
      bgcolor: isDark ? 'rgba(15,23,42,0.85)' : 'rgba(255,255,255,0.9)',
      bordercolor: isDark ? '#334155' : '#e2e8f0',
      borderwidth: 1,
      x: 1,
      y: 1,
      xanchor: 'right',
      yanchor: 'top',
      orientation: 'v',
    },
    margin: { t: 35, r: 20, b: 40, l: 55 },
    autosize: true,
    showlegend: true,
    datarevision: `${plot.id}-${Date.now()}`,
    uirevision: plot.id,
  };

  return (
    <div className="ms-plot-card">
      <Plot
        data={plot.data || []}
        layout={layout}
        config={{
          responsive: true,
          displayModeBar: true,
          modeBarButtonsToRemove: ['lasso2d', 'select2d'],
          displaylogo: false,
        }}
        useResizeHandler
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main viewer                                                        */
/* ------------------------------------------------------------------ */

function MassSpringViewer({ metadata, plots }) {
  const theme = useTheme();
  const [viewMode, setViewMode] = useState('3d');

  if (!plots || plots.length === 0) {
    return (
      <div className="ms-viewer">
        <div className="ms-viewer-empty">
          <div className="ms-loading-spinner" />
          <p>Loading simulation...</p>
        </div>
      </div>
    );
  }

  const responsePlot = plots.find((p) => p.id === 'response');
  const phasePlot = plots.find((p) => p.id === 'phase_portrait');
  const energyPlot = plots.find((p) => p.id === 'energy');
  const systemInfo = metadata?.system_info;
  const isDark = theme === 'dark';

  const dampingType = systemInfo?.damping_type?.replace('_', ' ') || '';
  const typeColors = {
    underdamped: '#3b82f6',
    critically_damped: '#10b981',
    overdamped: '#f59e0b',
  };
  const typeColor = typeColors[systemInfo?.damping_type] || '#6b7280';

  return (
    <div className="ms-viewer">
      <div className="ms-split-layout">
        {/* Left: animation panel with view toggle */}
        <div className="ms-left-panel">
          {/* System info + view toggle bar */}
          <div className="ms-top-bar">
            {systemInfo && (
              <div className="ms-system-overlay">
                <span className="ms-type-pill" style={{ backgroundColor: typeColor }}>
                  {dampingType}
                </span>
                <span className="ms-overlay-stat">&zeta; = {systemInfo.damping_ratio}</span>
                <span className="ms-overlay-sep">&middot;</span>
                <span className="ms-overlay-stat">f<sub>n</sub> = {systemInfo.natural_frequency_hz} Hz</span>
                {systemInfo.damped_frequency_hz != null && (
                  <>
                    <span className="ms-overlay-sep">&middot;</span>
                    <span className="ms-overlay-stat">f<sub>d</sub> = {systemInfo.damped_frequency_hz} Hz</span>
                  </>
                )}
                {systemInfo.period != null && (
                  <>
                    <span className="ms-overlay-sep">&middot;</span>
                    <span className="ms-overlay-stat">T = {systemInfo.period} s</span>
                  </>
                )}
              </div>
            )}
            <div className="ms-view-toggle">
              <button
                className={`ms-view-btn ${viewMode === '2d' ? 'active' : ''}`}
                onClick={() => setViewMode('2d')}
              >
                2D
              </button>
              <button
                className={`ms-view-btn ${viewMode === '3d' ? 'active' : ''}`}
                onClick={() => setViewMode('3d')}
              >
                3D
              </button>
            </div>
          </div>

          {viewMode === '2d' ? (
            <SpringAnimation
              visualization2D={metadata?.visualization_2d}
              theme={theme}
              systemInfo={null}
            />
          ) : (
            <Suspense fallback={
              <div className="ms-animation-panel">
                <div className="ms-viewer-empty">
                  <div className="ms-loading-spinner" />
                  <p>Loading 3D view...</p>
                </div>
              </div>
            }>
              <MassSpring3D
                visualization2D={metadata?.visualization_2d}
                systemInfo={systemInfo}
              />
            </Suspense>
          )}
        </div>

        {/* Right: plots fill available height */}
        <div className="ms-plots-panel">
          {responsePlot && <MSPlot plot={responsePlot} theme={theme} />}
          {phasePlot && <MSPlot plot={phasePlot} theme={theme} />}
          {energyPlot && <MSPlot plot={energyPlot} theme={theme} />}
        </div>
      </div>
    </div>
  );
}

export default MassSpringViewer;
