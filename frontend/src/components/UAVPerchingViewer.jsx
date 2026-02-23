/**
 * UAVPerchingViewer Component
 *
 * Custom viewer for the UAV Perching Trajectory simulation.
 * Left: Canvas 2D trajectory animation with glider and perch.
 * Right: Wing close-up with animated streamlines showing flow separation.
 * Bottom: Animation controls + overlay Plotly plots.
 */

import React, { useState, useEffect, useRef, useCallback, Suspense } from 'react';
import Plot from 'react-plotly.js';
import '../styles/UAVPerchingViewer.css';

/* ------------------------------------------------------------------ */
/*  Theme hook                                                         */
/* ------------------------------------------------------------------ */

function useTheme() {
  const [theme, setTheme] = useState(() => {
    return document.documentElement.getAttribute('data-theme') || 'dark';
  });

  useEffect(() => {
    const observer = new MutationObserver(() => {
      const t = document.documentElement.getAttribute('data-theme') || 'dark';
      setTheme(t);
    });
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme'],
    });
    return () => observer.disconnect();
  }, []);

  return theme;
}

/* ------------------------------------------------------------------ */
/*  Drawing helpers                                                    */
/* ------------------------------------------------------------------ */

/** Draw a simple glider shape at (cx, cy) rotated by theta radians */
function drawGlider(ctx, cx, cy, theta, scale, colors) {
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(-theta); // canvas y flipped, so negate theta

  const s = scale;

  // Fuselage
  ctx.beginPath();
  ctx.moveTo(-s * 1.2, 0);
  ctx.lineTo(s * 1.2, 0);
  ctx.strokeStyle = colors.fuselage;
  ctx.lineWidth = 2.5;
  ctx.stroke();

  // Main wing
  ctx.beginPath();
  ctx.moveTo(-s * 0.2, -s * 1.5);
  ctx.lineTo(s * 0.3, 0);
  ctx.lineTo(-s * 0.2, s * 1.5);
  ctx.strokeStyle = colors.wing;
  ctx.lineWidth = 2;
  ctx.stroke();

  // Tail
  ctx.beginPath();
  ctx.moveTo(-s * 1.2, -s * 0.6);
  ctx.lineTo(-s * 0.9, 0);
  ctx.lineTo(-s * 1.2, s * 0.6);
  ctx.strokeStyle = colors.tail;
  ctx.lineWidth = 1.5;
  ctx.stroke();

  // Nose dot
  ctx.beginPath();
  ctx.arc(s * 1.2, 0, 2.5, 0, Math.PI * 2);
  ctx.fillStyle = colors.nose;
  ctx.fill();

  ctx.restore();
}

/** Draw the perch: vertical pole + horizontal platform */
function drawPerch(ctx, px, py, scale, colors) {
  const poleH = 40 * scale;
  const platW = 20 * scale;

  // Pole
  ctx.beginPath();
  ctx.moveTo(px, py);
  ctx.lineTo(px, py + poleH);
  ctx.strokeStyle = colors.pole;
  ctx.lineWidth = 3;
  ctx.stroke();

  // Platform
  ctx.beginPath();
  ctx.moveTo(px - platW / 2, py);
  ctx.lineTo(px + platW / 2, py);
  ctx.strokeStyle = colors.platform;
  ctx.lineWidth = 4;
  ctx.lineCap = 'round';
  ctx.stroke();
  ctx.lineCap = 'butt';
}

/** Draw animated streamlines around a flat plate wing */
function drawStreamlines(ctx, w, h, alphaDeg, animPhase, isDark) {
  const numLines = 9;
  const plateLen = w * 0.35;
  const cx = w * 0.5;
  const cy = h * 0.5;
  const alphaRad = (alphaDeg * Math.PI) / 180;

  const attached = isDark ? '#14b8a6' : '#0d9488';
  const separated = isDark ? '#f97316' : '#ea580c';
  const separatedHigh = isDark ? '#ef4444' : '#dc2626';
  const absAlpha = Math.abs(alphaDeg);

  ctx.save();
  ctx.translate(cx, cy);

  // Draw flat plate wing
  ctx.save();
  ctx.rotate(-alphaRad);
  ctx.beginPath();
  ctx.moveTo(-plateLen / 2, 0);
  ctx.lineTo(plateLen / 2, 0);
  ctx.strokeStyle = isDark ? '#e2e8f0' : '#1e293b';
  ctx.lineWidth = 3;
  ctx.stroke();
  // Leading edge dot
  ctx.beginPath();
  ctx.arc(plateLen / 2, 0, 3, 0, Math.PI * 2);
  ctx.fillStyle = isDark ? '#f1f5f9' : '#334155';
  ctx.fill();
  ctx.restore();

  // Streamlines: horizontal lines that deflect around the plate
  for (let i = 0; i < numLines; i++) {
    const yOff = ((i - (numLines - 1) / 2) / ((numLines - 1) / 2)) * (h * 0.38);
    const isUpper = yOff < 0; // above the plate (upper surface = low pressure side)

    // Determine separation
    let isSeparated = false;
    let isFullSep = false;
    if (isUpper && absAlpha > 20 && Math.abs(yOff) < h * 0.22) {
      isSeparated = true;
      if (absAlpha > 45) isFullSep = true;
    }

    const color = isFullSep ? separatedHigh : (isSeparated ? separated : attached);

    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.globalAlpha = 0.8;

    const steps = 40;
    const xStart = -w * 0.45;
    const xEnd = w * 0.45;
    const dx = (xEnd - xStart) / steps;

    // Animated dash offset
    const dashOffset = animPhase * 12;

    for (let s = 0; s <= steps; s++) {
      const xp = xStart + s * dx + dashOffset;
      let yp = yOff;

      // Deflection near the plate
      const distToCenter = Math.sqrt(xp * xp + yOff * yOff);
      const plateInfluence = Math.max(0, 1 - distToCenter / (plateLen * 1.2));

      if (plateInfluence > 0.05) {
        // Attached flow follows the plate angle
        const deflection = plateInfluence * Math.sin(alphaRad) * plateLen * 0.3;
        if (isUpper) {
          yp -= Math.abs(deflection) * 0.5;
        } else {
          yp += deflection;
        }

        // Separation effect for upper surface
        if (isSeparated && xp > 0) {
          const sepFactor = (xp / (w * 0.45)) * plateInfluence;
          if (isFullSep) {
            // Full separation: chaotic wiggles
            yp += Math.sin(xp * 8 + animPhase * 15) * sepFactor * 25;
            yp += Math.cos(xp * 12 + animPhase * 20) * sepFactor * 15;
          } else {
            // Partial separation: mild wiggles near trailing edge
            yp += Math.sin(xp * 6 + animPhase * 10) * sepFactor * 12;
          }
        }
      }

      if (s === 0) {
        ctx.moveTo(xp, yp);
      } else {
        ctx.lineTo(xp, yp);
      }
    }
    ctx.stroke();
    ctx.globalAlpha = 1.0;
  }

  ctx.restore();
}

/* ------------------------------------------------------------------ */
/*  Trajectory Canvas                                                  */
/* ------------------------------------------------------------------ */

function TrajectoryCanvas({ trajectory, perch, result, frameIndex, theme }) {
  const canvasRef = useRef(null);
  const isDark = theme === 'dark';

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !trajectory?.x?.length) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    const idx = Math.min(frameIndex, trajectory.x.length - 1);

    // Colors
    const bg = isDark ? '#0f172a' : '#f8fafc';
    const groundColor = isDark ? '#22c55e' : '#16a34a';
    const groundFill = isDark ? 'rgba(34, 197, 94, 0.08)' : 'rgba(22, 163, 74, 0.06)';
    const gridColor = isDark ? 'rgba(148, 163, 184, 0.08)' : 'rgba(100, 116, 139, 0.08)';
    const textColor = isDark ? '#94a3b8' : '#64748b';
    const trailDim = isDark ? 'rgba(59, 130, 246, 0.25)' : 'rgba(37, 99, 235, 0.2)';
    const trailBright = isDark ? '#3b82f6' : '#2563eb';
    const perchCol = isDark ? '#10b981' : '#059669';
    const captureCircle = isDark ? 'rgba(16, 185, 129, 0.15)' : 'rgba(5, 150, 105, 0.1)';

    // Scene bounds
    const xMin = -0.3, xMax = 5.3;
    const zMin = -0.3, zMax = 4.3;
    const padding = 20;

    const scaleX = (w - 2 * padding) / (xMax - xMin);
    const scaleZ = (h - 2 * padding) / (zMax - zMin);
    const sc = Math.min(scaleX, scaleZ);

    const toCanvasX = (x) => padding + (x - xMin) * sc;
    const toCanvasY = (z) => h - padding - (z - zMin) * sc;

    // Clear
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, w, h);

    // Grid
    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 1;
    for (let x = 0; x <= 5; x++) {
      const cx = toCanvasX(x);
      ctx.beginPath();
      ctx.moveTo(cx, 0);
      ctx.lineTo(cx, h);
      ctx.stroke();
    }
    for (let z = 0; z <= 4; z++) {
      const cy = toCanvasY(z);
      ctx.beginPath();
      ctx.moveTo(0, cy);
      ctx.lineTo(w, cy);
      ctx.stroke();
    }

    // Axis labels
    ctx.font = '10px "Fira Code", monospace';
    ctx.fillStyle = textColor;
    ctx.textAlign = 'center';
    for (let x = 0; x <= 5; x++) {
      ctx.fillText(`${x}m`, toCanvasX(x), toCanvasY(-0.15));
    }
    ctx.textAlign = 'right';
    for (let z = 0; z <= 4; z++) {
      ctx.fillText(`${z}m`, toCanvasX(-0.1), toCanvasY(z) + 4);
    }

    // Ground
    const groundY = toCanvasY(0);
    ctx.fillStyle = groundFill;
    ctx.fillRect(0, groundY, w, h - groundY);
    ctx.beginPath();
    ctx.moveTo(0, groundY);
    ctx.lineTo(w, groundY);
    ctx.strokeStyle = groundColor;
    ctx.lineWidth = 2;
    ctx.stroke();

    // Perch capture radius
    if (perch) {
      const pcx = toCanvasX(perch.x);
      const pcy = toCanvasY(perch.z);
      const captureR = 0.5 * sc; // bronze radius visual

      ctx.beginPath();
      ctx.arc(pcx, pcy, captureR, 0, Math.PI * 2);
      ctx.fillStyle = captureCircle;
      ctx.fill();

      // Gold radius
      ctx.beginPath();
      ctx.arc(pcx, pcy, 0.05 * sc, 0, Math.PI * 2);
      ctx.strokeStyle = isDark ? 'rgba(245, 158, 11, 0.3)' : 'rgba(217, 119, 6, 0.3)';
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 3]);
      ctx.stroke();
      ctx.setLineDash([]);

      // Draw perch
      drawPerch(ctx, pcx, pcy, 1, {
        pole: isDark ? '#64748b' : '#94a3b8',
        platform: perchCol,
      });
    }

    // Trajectory trail
    if (trajectory.x.length > 1) {
      // Past trail (dimmed)
      ctx.beginPath();
      ctx.strokeStyle = trailDim;
      ctx.lineWidth = 2;
      for (let i = 0; i <= idx; i++) {
        const tx = toCanvasX(trajectory.x[i]);
        const ty = toCanvasY(trajectory.z[i]);
        if (i === 0) ctx.moveTo(tx, ty);
        else ctx.lineTo(tx, ty);
      }
      ctx.stroke();

      // Future trail (bright, dashed)
      if (idx < trajectory.x.length - 1) {
        ctx.beginPath();
        ctx.strokeStyle = trailBright;
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);
        ctx.globalAlpha = 0.3;
        ctx.moveTo(toCanvasX(trajectory.x[idx]), toCanvasY(trajectory.z[idx]));
        for (let i = idx + 1; i < trajectory.x.length; i++) {
          ctx.lineTo(toCanvasX(trajectory.x[i]), toCanvasY(trajectory.z[i]));
        }
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.globalAlpha = 1.0;
      }
    }

    // Start marker
    if (trajectory.x.length > 0) {
      const sx = toCanvasX(trajectory.x[0]);
      const sy = toCanvasY(trajectory.z[0]);
      ctx.beginPath();
      ctx.arc(sx, sy, 5, 0, Math.PI * 2);
      ctx.fillStyle = '#f59e0b';
      ctx.fill();
    }

    // UAV at current frame
    if (trajectory.x.length > 0) {
      const ux = toCanvasX(trajectory.x[idx]);
      const uy = toCanvasY(trajectory.z[idx]);
      const thetaRad = (trajectory.theta[idx] * Math.PI) / 180;

      drawGlider(ctx, ux, uy, thetaRad, 12, {
        fuselage: isDark ? '#f1f5f9' : '#1e293b',
        wing: trailBright,
        tail: isDark ? '#94a3b8' : '#64748b',
        nose: '#ef4444',
      });
    }

    // Success flash at closest frame
    if (result?.grade === 'gold' && idx === result.closest_frame) {
      ctx.fillStyle = 'rgba(16, 185, 129, 0.25)';
      ctx.fillRect(0, 0, w, h);
      ctx.font = 'bold 28px Inter, sans-serif';
      ctx.fillStyle = '#10b981';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('PERCHED!', w / 2, h * 0.15);
    }

  }, [trajectory, perch, result, frameIndex, isDark]);

  useEffect(() => {
    draw();
  }, [draw]);

  // Redraw on resize
  useEffect(() => {
    const onResize = () => draw();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [draw]);

  return <canvas ref={canvasRef} style={{ width: '100%', height: '100%' }} />;
}

/* ------------------------------------------------------------------ */
/*  Wing Close-up Canvas                                               */
/* ------------------------------------------------------------------ */

function WingCanvas({ alphaDeg, theme }) {
  const canvasRef = useRef(null);
  const animRef = useRef(0);
  const rafRef = useRef(null);
  const isDark = theme === 'dark';

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;

    const loop = () => {
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      const w = rect.width;
      const h = rect.height;

      // Clear
      ctx.fillStyle = isDark ? '#0f172a' : '#f8fafc';
      ctx.fillRect(0, 0, w, h);

      animRef.current += 0.02;
      drawStreamlines(ctx, w, h, alphaDeg, animRef.current, isDark);

      rafRef.current = requestAnimationFrame(loop);
    };

    rafRef.current = requestAnimationFrame(loop);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [alphaDeg, isDark]);

  return <canvas ref={canvasRef} style={{ width: '100%', height: '100%' }} />;
}

/* ------------------------------------------------------------------ */
/*  Status Badge                                                       */
/* ------------------------------------------------------------------ */

function StatusBadge({ result, trajectory, frameIndex }) {
  if (!result || !trajectory?.time?.length) return null;

  const idx = Math.min(frameIndex, trajectory.time.length - 1);
  const speed = trajectory.speed[idx]?.toFixed(2) ?? '—';
  const alpha = trajectory.alpha[idx]?.toFixed(1) ?? '—';
  const alt = trajectory.z[idx]?.toFixed(2) ?? '—';
  const dist = Math.sqrt(
    (trajectory.x[idx] - 3.5) ** 2 + (trajectory.z[idx] - 1.5) ** 2
  ).toFixed(3);

  const gradeClass = result.grade || 'fail';
  const gradeLabels = { gold: 'PERCHED!', silver: 'Good Landing', bronze: 'Close Pass', fail: 'Missed' };

  return (
    <div className="uav-status-bar">
      <span className={`uav-grade-badge ${gradeClass}`}>
        {gradeLabels[gradeClass] || result.message}
      </span>
      <div className="uav-stats">
        <span><span className="uav-stat-label">V</span>{speed} m/s</span>
        <span><span className="uav-stat-label">&alpha;</span>{alpha}&deg;</span>
        <span><span className="uav-stat-label">Alt</span>{alt} m</span>
        <span><span className="uav-stat-label">d</span>{dist} m</span>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Overlay Plot                                                       */
/* ------------------------------------------------------------------ */

function OverlayPlot({ plot, theme, height = 220 }) {
  const isDark = theme === 'dark';

  const layout = {
    title: {
      text: plot.title || '',
      font: { color: isDark ? '#f1f5f9' : '#1e293b', size: 13 },
      x: 0.5,
      xanchor: 'center',
    },
    paper_bgcolor: isDark ? '#0f172a' : 'rgba(255,255,255,0.98)',
    plot_bgcolor: isDark ? '#1e293b' : '#f8fafc',
    font: {
      color: isDark ? '#e2e8f0' : '#1e293b',
      family: 'Inter, sans-serif',
      size: 11,
    },
    xaxis: {
      ...plot.layout?.xaxis,
      gridcolor: isDark ? 'rgba(71,85,105,0.4)' : 'rgba(100,116,139,0.2)',
      zerolinecolor: isDark ? 'rgba(148,163,184,0.5)' : 'rgba(100,116,139,0.5)',
      tickfont: { color: isDark ? '#94a3b8' : '#475569', size: 10 },
      title: {
        text: plot.layout?.xaxis?.title || '',
        font: { color: isDark ? '#94a3b8' : '#334155', size: 11 },
      },
    },
    yaxis: {
      ...plot.layout?.yaxis,
      gridcolor: isDark ? 'rgba(71,85,105,0.4)' : 'rgba(100,116,139,0.2)',
      zerolinecolor: isDark ? 'rgba(148,163,184,0.5)' : 'rgba(100,116,139,0.5)',
      tickfont: { color: isDark ? '#94a3b8' : '#475569', size: 10 },
      title: {
        text: plot.layout?.yaxis?.title || '',
        font: { color: isDark ? '#94a3b8' : '#334155', size: 11 },
      },
    },
    legend: {
      font: { color: isDark ? '#e2e8f0' : '#1e293b', size: 10 },
      bgcolor: isDark ? 'rgba(30,41,59,0.9)' : 'rgba(255,255,255,0.9)',
      ...plot.layout?.legend,
    },
    margin: { t: 35, r: 15, b: 40, l: 50 },
    height,
    autosize: true,
    showlegend: true,
    datarevision: `${plot.id}-${Date.now()}`,
    uirevision: plot.layout?.uirevision || plot.id,
  };

  const config = {
    responsive: true,
    displayModeBar: false,
    displaylogo: false,
  };

  return (
    <Plot
      data={plot.data || []}
      layout={layout}
      config={config}
      useResizeHandler
      style={{ width: '100%', height: '100%' }}
    />
  );
}

/* ------------------------------------------------------------------ */
/*  Animation Controls                                                 */
/* ------------------------------------------------------------------ */

function AnimControls({
  isPlaying, onTogglePlay, onStepBack, onStepForward, onReset,
  frameIndex, totalFrames, onFrameChange, currentTime, totalTime,
  speed, onSpeedChange,
}) {
  return (
    <div className="uav-anim-controls">
      <button className="uav-anim-btn" onClick={onReset} aria-label="Reset">
        &#x21BA;
      </button>
      <button className="uav-anim-btn" onClick={onStepBack} aria-label="Step backward">
        &#x23EE;
      </button>
      <button
        className={`uav-anim-btn ${isPlaying ? 'active' : ''}`}
        onClick={onTogglePlay}
        aria-label={isPlaying ? 'Pause' : 'Play'}
      >
        {isPlaying ? '\u23F8' : '\u25B6'}
      </button>
      <button className="uav-anim-btn" onClick={onStepForward} aria-label="Step forward">
        &#x23ED;
      </button>
      <input
        className="uav-frame-slider"
        type="range"
        min={0}
        max={Math.max(0, totalFrames - 1)}
        value={frameIndex}
        onChange={(e) => onFrameChange(Number(e.target.value))}
        aria-label="Frame position"
      />
      <span className="uav-time-display">
        {currentTime.toFixed(3)}s / {totalTime.toFixed(1)}s
      </span>
      <select
        className="uav-speed-select"
        value={speed}
        onChange={(e) => onSpeedChange(Number(e.target.value))}
        aria-label="Playback speed"
      >
        <option value={0.25}>0.25x</option>
        <option value={0.5}>0.5x</option>
        <option value={1}>1x</option>
        <option value={2}>2x</option>
      </select>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main Viewer                                                        */
/* ------------------------------------------------------------------ */

function UAVPerchingViewer({ metadata, plots }) {
  const theme = useTheme();

  const trajectory = metadata?.trajectory;
  const perch = metadata?.perch;
  const result = metadata?.result;
  const systemInfo = metadata?.system_info;

  // Animation state
  const [frameIndex, setFrameIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [showOverlay, setShowOverlay] = useState(false);

  const playingRef = useRef(false);
  const frameRef = useRef(0);
  const lastTimeRef = useRef(0);
  const speedRef = useRef(1);
  const rafRef = useRef(null);

  // System fingerprint — reset local state when trajectory changes
  const fingerprint = trajectory?.x?.length
    ? `${trajectory.x.length}-${trajectory.x[0]?.toFixed(3)}-${trajectory.z[0]?.toFixed(3)}`
    : '';
  const prevFingerprintRef = useRef(fingerprint);

  useEffect(() => {
    if (prevFingerprintRef.current !== fingerprint) {
      prevFingerprintRef.current = fingerprint;
      setFrameIndex(0);
      setIsPlaying(false);
      frameRef.current = 0;
      playingRef.current = false;
    }
  }, [fingerprint]);

  // Sync refs
  useEffect(() => { playingRef.current = isPlaying; }, [isPlaying]);
  useEffect(() => { speedRef.current = playbackSpeed; }, [playbackSpeed]);

  // Animation loop
  useEffect(() => {
    if (!trajectory?.time?.length) return;

    const frameDt = (trajectory.dt || 0.005) * 1000; // ms between animation frames
    const totalFrames = trajectory.time.length;

    const loop = (timestamp) => {
      if (playingRef.current) {
        const elapsed = timestamp - lastTimeRef.current;
        const adjustedDt = frameDt / speedRef.current;
        if (elapsed >= adjustedDt) {
          lastTimeRef.current = timestamp;
          const next = frameRef.current + 1;
          if (next >= totalFrames) {
            // Stop at end
            playingRef.current = false;
            setIsPlaying(false);
          } else {
            frameRef.current = next;
            setFrameIndex(next);
          }
        }
      }
      rafRef.current = requestAnimationFrame(loop);
    };

    lastTimeRef.current = performance.now();
    rafRef.current = requestAnimationFrame(loop);

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [trajectory]);

  // Controls
  const togglePlay = useCallback(() => {
    if (!trajectory?.time?.length) return;
    // If at end, restart
    if (frameRef.current >= trajectory.time.length - 1) {
      frameRef.current = 0;
      setFrameIndex(0);
    }
    setIsPlaying((p) => !p);
  }, [trajectory]);

  const stepForward = useCallback(() => {
    if (!trajectory?.time?.length) return;
    setIsPlaying(false);
    const next = Math.min(frameRef.current + 1, trajectory.time.length - 1);
    frameRef.current = next;
    setFrameIndex(next);
  }, [trajectory]);

  const stepBackward = useCallback(() => {
    if (!trajectory?.time?.length) return;
    setIsPlaying(false);
    const prev = Math.max(frameRef.current - 1, 0);
    frameRef.current = prev;
    setFrameIndex(prev);
  }, [trajectory]);

  const resetAnim = useCallback(() => {
    setIsPlaying(false);
    frameRef.current = 0;
    setFrameIndex(0);
  }, []);

  const onFrameChange = useCallback((val) => {
    setIsPlaying(false);
    frameRef.current = val;
    setFrameIndex(val);
  }, []);

  // Derived values
  const totalFrames = trajectory?.time?.length || 0;
  const currentTime = trajectory?.time?.[frameIndex] ?? 0;
  const totalTime = trajectory?.time?.[totalFrames - 1] ?? 0;
  const currentAlpha = trajectory?.alpha?.[frameIndex] ?? 0;

  // Find overlay plots
  const alphaPlot = plots?.find((p) => p.id === 'alpha_vs_time');
  const forcesPlot = plots?.find((p) => p.id === 'forces_vs_time');
  const speedPlot = plots?.find((p) => p.id === 'speed_vs_time');

  if (!trajectory || !trajectory.x?.length) {
    return (
      <div className="uav-perching-viewer">
        <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading UAV Perching simulation...
        </div>
      </div>
    );
  }

  return (
    <div className="uav-perching-viewer">
      {/* Status bar */}
      <StatusBadge result={result} trajectory={trajectory} frameIndex={frameIndex} />

      {/* Canvas section */}
      <div className="uav-canvas-section">
        <div className="uav-trajectory-panel">
          <TrajectoryCanvas
            trajectory={trajectory}
            perch={perch}
            result={result}
            frameIndex={frameIndex}
            theme={theme}
          />
        </div>

        <div className="uav-wing-panel">
          <div className="uav-wing-title">Wing &amp; Airflow</div>
          <div className="uav-wing-canvas-wrap">
            <WingCanvas alphaDeg={currentAlpha} theme={theme} />
          </div>
          <div className="uav-wing-info">
            <span>&alpha; = {currentAlpha.toFixed(1)}&deg;</span>
            <span>{Math.abs(currentAlpha) > 45 ? 'Full stall' : Math.abs(currentAlpha) > 20 ? 'Partial sep.' : 'Attached'}</span>
          </div>
        </div>
      </div>

      {/* Animation controls */}
      <AnimControls
        isPlaying={isPlaying}
        onTogglePlay={togglePlay}
        onStepBack={stepBackward}
        onStepForward={stepForward}
        onReset={resetAnim}
        frameIndex={frameIndex}
        totalFrames={totalFrames}
        onFrameChange={onFrameChange}
        currentTime={currentTime}
        totalTime={totalTime}
        speed={playbackSpeed}
        onSpeedChange={setPlaybackSpeed}
      />

      {/* Overlay toggle + plots */}
      <button
        className={`uav-overlay-toggle ${showOverlay ? 'active' : ''}`}
        onClick={() => setShowOverlay((s) => !s)}
        aria-label="Toggle overlay plots"
      >
        {showOverlay ? '\u25BC' : '\u25B6'} Detail Plots
      </button>

      {showOverlay && (
        <div className="uav-overlay-plots">
          {alphaPlot && <OverlayPlot plot={alphaPlot} theme={theme} />}
          {forcesPlot && <OverlayPlot plot={forcesPlot} theme={theme} />}
          {speedPlot && <OverlayPlot plot={speedPlot} theme={theme} />}
        </div>
      )}
    </div>
  );
}

export default UAVPerchingViewer;
