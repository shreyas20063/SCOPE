/**
 * PerchingGliderViewer Component
 *
 * Custom viewer for the 2D Perching Glider simulation (MIT 6.003 Lecture 10).
 * Canvas-based trajectory animation with glider, perch, force/velocity overlays,
 * and particle-based streamlines using potential flow model.
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import Plot from 'react-plotly.js';
import '../styles/PerchingGliderViewer.css';

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
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const NUM_PARTICLES = 60;
const PARTICLE_SPAWN_SPREAD = 0.8; // fraction of canvas height for spawn spread

/* ------------------------------------------------------------------ */
/*  Drawing helpers                                                    */
/* ------------------------------------------------------------------ */

/** Draw the glider body: fuselage + wing + elevator, rotated by theta */
function drawGlider(ctx, cx, cy, theta, phi, scale, colors) {
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(-theta); // canvas y is flipped

  const s = scale;

  // Fuselage
  ctx.beginPath();
  ctx.moveTo(-s * 1.2, 0);
  ctx.lineTo(s * 1.2, 0);
  ctx.strokeStyle = colors.fuselage;
  ctx.lineWidth = 2.5;
  ctx.stroke();

  // Main wing (symmetric airfoil shape)
  ctx.beginPath();
  ctx.moveTo(-s * 0.1, -s * 1.4);
  ctx.lineTo(s * 0.3, 0);
  ctx.lineTo(-s * 0.1, s * 1.4);
  ctx.strokeStyle = colors.wing;
  ctx.lineWidth = 2;
  ctx.stroke();

  // Elevator (tail surface, deflected by phi relative to body)
  ctx.save();
  ctx.translate(-s * 1.0, 0);
  ctx.rotate(phi); // elevator deflection relative to body
  ctx.beginPath();
  ctx.moveTo(0, -s * 0.5);
  ctx.lineTo(s * 0.15, 0);
  ctx.lineTo(0, s * 0.5);
  ctx.strokeStyle = colors.elevator;
  ctx.lineWidth = 1.8;
  ctx.stroke();
  ctx.restore();

  // Nose dot
  ctx.beginPath();
  ctx.arc(s * 1.2, 0, 2.5, 0, Math.PI * 2);
  ctx.fillStyle = colors.nose;
  ctx.fill();

  ctx.restore();
}

/** Draw perch: vertical pole + platform at (px, py) */
function drawPerch(ctx, px, py, scale, colors) {
  const poleH = 35 * scale;
  const platW = 18 * scale;

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

/** Draw an arrow from (x0,y0) to (x1,y1) */
function drawArrow(ctx, x0, y0, x1, y1, color, lineWidth) {
  const dx = x1 - x0;
  const dy = y1 - y0;
  const len = Math.sqrt(dx * dx + dy * dy);
  if (len < 2) return;

  const headLen = Math.min(8, len * 0.3);
  const angle = Math.atan2(dy, dx);

  ctx.beginPath();
  ctx.moveTo(x0, y0);
  ctx.lineTo(x1, y1);
  ctx.strokeStyle = color;
  ctx.lineWidth = lineWidth;
  ctx.stroke();

  // Arrowhead
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(
    x1 - headLen * Math.cos(angle - 0.35),
    y1 - headLen * Math.sin(angle - 0.35)
  );
  ctx.lineTo(
    x1 - headLen * Math.cos(angle + 0.35),
    y1 - headLen * Math.sin(angle + 0.35)
  );
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();
}

/* ------------------------------------------------------------------ */
/*  Streamline particle system                                         */
/* ------------------------------------------------------------------ */

/** Initialize particles with random positions along right spawn edge */
function initParticles(count) {
  const particles = new Float32Array(count * 2); // [x0, y0, x1, y1, ...]
  for (let i = 0; i < count; i++) {
    particles[i * 2] = 1.0; // x: right edge (normalized 0-1)
    particles[i * 2 + 1] = Math.random(); // y: random vertical
  }
  return particles;
}

/**
 * Compute flow velocity at a point using uniform flow + point vortex.
 * Kutta condition for flat plate: Γ = π · V · c · sin(α)
 */
function flowVelocity(px, py, gliderX, gliderY, theta, V, alpha, chord) {
  // Transform to glider body frame
  const dx = px - gliderX;
  const dy = py - gliderY;

  // Distance from glider center
  const r2 = dx * dx + dy * dy;
  const r = Math.sqrt(r2);

  // Vortex strength (Kutta condition)
  const gamma = Math.PI * V * chord * Math.sin(alpha);

  // Uniform flow (leftward in world frame since glider flies right)
  let ux = -V * 0.3; // reduced for visual effect
  let uy = 0;

  // Point vortex contribution (only if not too close to center)
  if (r > chord * 0.3) {
    const vortexScale = gamma / (2 * Math.PI * r2);
    ux += vortexScale * (-dy);
    uy += vortexScale * dx;
  }

  return { ux, uy };
}

/** Advect particles one step and recycle off-screen ones */
function advectParticles(particles, count, dt, gliderX, gliderY, theta, V, alpha, chord, bounds) {
  const { xMin, xMax, yMin, yMax } = bounds;
  const range = xMax - xMin;

  for (let i = 0; i < count; i++) {
    const px = particles[i * 2];
    const py = particles[i * 2 + 1];

    // World coordinates
    const wx = xMin + px * range;
    const wy = yMin + py * (yMax - yMin);

    const { ux, uy } = flowVelocity(wx, wy, gliderX, gliderY, theta, V, alpha, chord);

    // Advect (in normalized coords)
    const newPx = px + (ux * dt) / range;
    const newPy = py + (uy * dt) / (yMax - yMin);

    // Recycle if off-screen
    if (newPx < -0.05 || newPx > 1.05 || newPy < -0.05 || newPy > 1.05) {
      // Respawn at right edge with slight randomization
      particles[i * 2] = 0.98 + Math.random() * 0.04;
      particles[i * 2 + 1] = Math.random() * PARTICLE_SPAWN_SPREAD + (1 - PARTICLE_SPAWN_SPREAD) / 2;
    } else {
      particles[i * 2] = newPx;
      particles[i * 2 + 1] = newPy;
    }
  }
}

/* ------------------------------------------------------------------ */
/*  Main Canvas Component                                              */
/* ------------------------------------------------------------------ */

function GliderCanvas({ viz, outcome, frameIndex, showForces, showVelocity, showAoA, theme }) {
  const canvasRef = useRef(null);
  const particlesRef = useRef(initParticles(NUM_PARTICLES));
  const isDark = theme === 'dark';

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !viz?.x?.length) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    const idx = Math.min(frameIndex, viz.x.length - 1);

    // Colors
    const bg = isDark ? '#0f172a' : '#f8fafc';
    const groundColor = isDark ? '#22c55e' : '#16a34a';
    const groundFill = isDark ? 'rgba(34, 197, 94, 0.06)' : 'rgba(22, 163, 74, 0.04)';
    const gridColor = isDark ? 'rgba(148, 163, 184, 0.08)' : 'rgba(100, 116, 139, 0.08)';
    const textColor = isDark ? '#94a3b8' : '#64748b';
    const trailDim = isDark ? 'rgba(59, 130, 246, 0.2)' : 'rgba(37, 99, 235, 0.15)';
    const trailBright = isDark ? '#3b82f6' : '#2563eb';
    const particleColor = isDark ? 'rgba(0, 217, 255, 0.35)' : 'rgba(0, 180, 220, 0.25)';

    // Scene bounds (x: -4.5 to 2, z: -0.5 to 3.5)
    const xMin = -4.5, xMax = 2.0;
    const zMin = -0.5, zMax = 3.5;
    const padding = 25;

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
    ctx.lineWidth = 0.5;
    for (let x = -4; x <= 2; x++) {
      const cx = toCanvasX(x);
      ctx.beginPath();
      ctx.moveTo(cx, 0);
      ctx.lineTo(cx, h);
      ctx.stroke();
    }
    for (let z = 0; z <= 3; z++) {
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
    for (let x = -4; x <= 2; x++) {
      ctx.fillText(`${x}m`, toCanvasX(x), toCanvasY(-0.35));
    }
    ctx.textAlign = 'right';
    for (let z = 0; z <= 3; z++) {
      ctx.fillText(`${z}m`, toCanvasX(-4.35), toCanvasY(z) + 4);
    }

    // Ground
    const groundY = toCanvasY(0);
    ctx.fillStyle = groundFill;
    ctx.fillRect(0, groundY, w, h - groundY);
    ctx.beginPath();
    ctx.moveTo(0, groundY);
    ctx.lineTo(w, groundY);
    ctx.strokeStyle = groundColor;
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Perch (at x=0, z=perch_z from outcome, defaults to z of first frame)
    const perchZ = outcome?.perch_z ?? viz.z[0];
    const perchPx = toCanvasX(0);
    const perchPy = toCanvasY(perchZ);
    drawPerch(ctx, perchPx, perchPy, 1.0, {
      pole: isDark ? '#94a3b8' : '#64748b',
      platform: isDark ? '#f59e0b' : '#d97706',
    });

    // Capture zone circle
    ctx.beginPath();
    ctx.arc(perchPx, perchPy, 0.5 * sc, 0, Math.PI * 2);
    ctx.strokeStyle = isDark ? 'rgba(16, 185, 129, 0.15)' : 'rgba(5, 150, 105, 0.1)';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.stroke();
    ctx.setLineDash([]);

    // Trail (fading dots from start to current frame)
    const trailStep = Math.max(1, Math.floor(idx / 80));
    for (let i = 0; i <= idx; i += trailStep) {
      const frac = i / Math.max(idx, 1);
      const alpha = 0.1 + frac * 0.6;
      ctx.beginPath();
      ctx.arc(toCanvasX(viz.x[i]), toCanvasY(viz.z[i]), 2, 0, Math.PI * 2);
      ctx.fillStyle = isDark
        ? `rgba(59, 130, 246, ${alpha})`
        : `rgba(37, 99, 235, ${alpha})`;
      ctx.fill();
    }

    // Recent trail (solid line for last ~20 frames)
    const trailStart = Math.max(0, idx - 20);
    if (idx > 0) {
      ctx.beginPath();
      ctx.moveTo(toCanvasX(viz.x[trailStart]), toCanvasY(viz.z[trailStart]));
      for (let i = trailStart + 1; i <= idx; i++) {
        ctx.lineTo(toCanvasX(viz.x[i]), toCanvasY(viz.z[i]));
      }
      ctx.strokeStyle = trailBright;
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    // Streamline particles
    if (showVelocity && idx < viz.x.length) {
      const gx = viz.x[idx];
      const gz = viz.z[idx];
      const gth = viz.theta[idx];
      const gV = viz.speed[idx];
      const gAlpha = viz.alpha_w[idx];

      // Advect particles
      advectParticles(
        particlesRef.current, NUM_PARTICLES, 0.15,
        gx, gz, gth, gV, gAlpha, 0.15,
        { xMin, xMax, yMin: zMin, yMax: zMax }
      );

      // Draw particles
      ctx.globalAlpha = 1.0;
      for (let i = 0; i < NUM_PARTICLES; i++) {
        const px = particlesRef.current[i * 2];
        const py = particlesRef.current[i * 2 + 1];
        const canvX = padding + px * (w - 2 * padding);
        const canvY = h - padding - py * (h - 2 * padding);

        ctx.beginPath();
        ctx.arc(canvX, canvY, 1.8, 0, Math.PI * 2);
        ctx.fillStyle = particleColor;
        ctx.fill();
      }
    }

    // Current glider position
    const gx = viz.x[idx];
    const gz = viz.z[idx];
    const gth = viz.theta[idx];
    const gPhi = viz.phi[idx];
    const gcx = toCanvasX(gx);
    const gcy = toCanvasY(gz);

    // Force vectors (if enabled)
    if (showForces && idx < viz.lift_x.length) {
      const forceScale = sc * 0.15; // scale forces for visibility
      const lx = viz.lift_x[idx] * forceScale;
      const lz = viz.lift_z[idx] * forceScale;
      const dx = viz.drag_x[idx] * forceScale;
      const dz = viz.drag_z[idx] * forceScale;

      // Lift arrow (blue)
      drawArrow(ctx, gcx, gcy, gcx + lx, gcy - lz, '#3b82f6', 2);
      // Drag arrow (red)
      drawArrow(ctx, gcx, gcy, gcx + dx, gcy - dz, '#ef4444', 2);
    }

    // Velocity vector (if enabled)
    if (showVelocity && idx < viz.xdot.length) {
      const velScale = sc * 0.06;
      const vx = viz.xdot[idx] * velScale;
      const vz = viz.zdot[idx] * velScale;
      drawArrow(ctx, gcx, gcy, gcx + vx, gcy - vz, '#10b981', 2);
    }

    // Angle of attack arc (if enabled)
    if (showAoA && idx < viz.alpha_w.length) {
      const alpha_w = viz.alpha_w[idx];
      const xdot = viz.xdot[idx];
      const zdot = viz.zdot[idx];
      const gamma = Math.atan2(zdot, xdot);
      const arcRadius = 25;

      ctx.beginPath();
      // Arc from velocity direction to body axis
      const startAngle = -gamma; // canvas coords
      const endAngle = -gth;
      ctx.arc(gcx, gcy, arcRadius, startAngle, endAngle, alpha_w > 0);
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Label
      const midAngle = (startAngle + endAngle) / 2;
      const labelR = arcRadius + 12;
      ctx.font = '10px "Fira Code", monospace';
      ctx.fillStyle = '#f59e0b';
      ctx.textAlign = 'center';
      ctx.fillText(
        `α=${Math.abs(alpha_w * 180 / Math.PI).toFixed(0)}°`,
        gcx + labelR * Math.cos(midAngle),
        gcy + labelR * Math.sin(midAngle)
      );
    }

    // Draw glider
    drawGlider(ctx, gcx, gcy, gth, gPhi, 15, {
      fuselage: isDark ? '#e2e8f0' : '#1e293b',
      wing: isDark ? '#3b82f6' : '#2563eb',
      elevator: isDark ? '#14b8a6' : '#0d9488',
      nose: isDark ? '#f1f5f9' : '#334155',
    });

    // Success flash on last frame if perched
    if (idx === viz.x.length - 1 && outcome?.success) {
      ctx.fillStyle = 'rgba(16, 185, 129, 0.08)';
      ctx.fillRect(0, 0, w, h);
    }
  }, [frameIndex, viz, outcome, showForces, showVelocity, showAoA, isDark]);

  useEffect(() => {
    draw();
  }, [draw]);

  // Resize handler
  useEffect(() => {
    const handleResize = () => draw();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [draw]);

  return <canvas ref={canvasRef} style={{ width: '100%', height: '100%' }} />;
}

/* ------------------------------------------------------------------ */
/*  Main Component                                                     */
/* ------------------------------------------------------------------ */

export default function PerchingGliderViewer({ metadata, plots }) {
  const theme = useTheme();
  const isDark = theme === 'dark';
  const viz = metadata?.visualization_2d;
  const outcome = metadata?.outcome;
  const controlInfo = metadata?.control_info;

  // Animation state
  const [playing, setPlaying] = useState(false);
  const [frameIndex, setFrameIndex] = useState(0);
  const animRef = useRef(null);
  const lastTimeRef = useRef(0);

  const numFrames = viz?.num_frames || 0;
  const dt = viz?.dt || 0.01;
  const animSpeed = 1.0; // Could be tied to metadata param

  // Reset animation when trajectory changes
  const trajFingerprint = useRef('');
  useEffect(() => {
    const fp = `${viz?.x?.[0]}-${viz?.z?.[0]}-${viz?.num_frames}-${outcome?.reason}`;
    if (fp !== trajFingerprint.current) {
      trajFingerprint.current = fp;
      setFrameIndex(0);
      setPlaying(false);
    }
  }, [viz, outcome]);

  // Animation loop
  useEffect(() => {
    if (!playing || numFrames === 0) return;

    const step = (timestamp) => {
      if (!lastTimeRef.current) lastTimeRef.current = timestamp;
      const elapsed = timestamp - lastTimeRef.current;
      const frameDuration = (dt * 1000) / animSpeed;

      if (elapsed >= frameDuration) {
        lastTimeRef.current = timestamp;
        setFrameIndex((prev) => {
          if (prev >= numFrames - 1) {
            setPlaying(false);
            return numFrames - 1;
          }
          return prev + 1;
        });
      }
      animRef.current = requestAnimationFrame(step);
    };

    lastTimeRef.current = 0;
    animRef.current = requestAnimationFrame(step);
    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, [playing, numFrames, dt, animSpeed]);

  const handlePlayPause = useCallback(() => {
    if (frameIndex >= numFrames - 1) {
      setFrameIndex(0);
    }
    setPlaying((p) => !p);
  }, [frameIndex, numFrames]);

  const handleRestart = useCallback(() => {
    setFrameIndex(0);
    setPlaying(false);
  }, []);

  const handleSlider = useCallback((e) => {
    setFrameIndex(parseInt(e.target.value, 10));
    setPlaying(false);
  }, []);

  // Overlay toggles from metadata params
  const showForces = metadata?.visualization_2d ? true : false; // Will check currentParams
  // Read from the parent's currentParams via metadata
  // Since we only get metadata, we check the control_info or use defaults

  // Current frame time
  const currentTime = viz?.time?.[frameIndex] ?? 0;
  const currentSpeed = viz?.speed?.[frameIndex] ?? 0;
  const currentTheta = viz?.theta?.[frameIndex] ?? 0;
  const currentZ = viz?.z?.[frameIndex] ?? 0;

  // Determine which overlays to show based on the data being present
  // (the parent component sends currentParams through the metadata)
  const [localShowForces, setLocalShowForces] = useState(false);
  const [localShowVelocity, setLocalShowVelocity] = useState(true);
  const [localShowAoA, setLocalShowAoA] = useState(false);

  if (!viz || !viz.x || viz.x.length === 0) {
    return <div className="pg-viewer">Loading trajectory data...</div>;
  }

  return (
    <div className="pg-viewer">
      {/* Outcome Banner */}
      <div className="pg-outcome-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span className={`pg-outcome-badge ${outcome?.reason || 'timeout'}`}>
            {outcome?.reason === 'perched' ? '✓ PERCHED' :
             outcome?.reason === 'crashed' ? '✗ CRASHED' :
             outcome?.reason === 'overshot' ? '→ OVERSHOT' :
             '⏱ TIMEOUT'}
          </span>
          {controlInfo && (
            <span className="pg-control-tag">
              {controlInfo.mode === 'open_loop' ? 'Open-Loop' :
               controlInfo.mode === 'p_controller' ? `P-Control (Kp=${controlInfo.gains?.Kp})` :
               `Optimal (Kp=${controlInfo.gains?.Kp}, Kd=${controlInfo.gains?.Kd})`}
            </span>
          )}
        </div>
        <div className="pg-stats">
          <span>
            <span className="pg-stat-label">dist:</span>
            {outcome?.final_distance?.toFixed(2)}m
          </span>
          <span>
            <span className="pg-stat-label">V:</span>
            {outcome?.final_speed?.toFixed(1)}m/s
          </span>
          <span>
            <span className="pg-stat-label">θ:</span>
            {outcome?.final_theta_deg?.toFixed(0)}°
          </span>
        </div>
      </div>

      {/* Canvas */}
      <div className="pg-canvas-section">
        <GliderCanvas
          viz={viz}
          outcome={outcome}
          frameIndex={frameIndex}
          showForces={localShowForces}
          showVelocity={localShowVelocity}
          showAoA={localShowAoA}
          theme={theme}
        />
        <div className="pg-hud">
          <span>t = <span className="pg-hud-val">{currentTime.toFixed(2)}s</span></span>
          <span>V = <span className="pg-hud-val">{currentSpeed.toFixed(1)} m/s</span></span>
          <span>θ = <span className="pg-hud-val">{(currentTheta * 180 / Math.PI).toFixed(1)}°</span></span>
          <span>z = <span className="pg-hud-val">{currentZ.toFixed(2)} m</span></span>
        </div>
      </div>

      {/* Animation Controls */}
      <div className="pg-anim-controls">
        <button
          className={`pg-anim-btn ${playing ? 'active' : ''}`}
          onClick={handlePlayPause}
          aria-label={playing ? 'Pause' : 'Play'}
        >
          {playing ? '⏸' : '▶'}
        </button>
        <button
          className="pg-anim-btn"
          onClick={handleRestart}
          aria-label="Restart"
        >
          ⏮
        </button>
        <input
          type="range"
          className="pg-frame-slider"
          min={0}
          max={numFrames - 1}
          value={frameIndex}
          onChange={handleSlider}
          aria-label="Animation frame"
        />
        <span className="pg-time-display">
          {currentTime.toFixed(2)}s / {(viz?.total_time || 0).toFixed(2)}s
        </span>

        {/* Overlay toggles */}
        <button
          className={`pg-anim-btn ${localShowForces ? 'active' : ''}`}
          onClick={() => setLocalShowForces(v => !v)}
          aria-label="Toggle forces"
          title="Show forces"
          style={{ fontSize: '0.7rem', width: 'auto', padding: '0 6px' }}
        >
          F
        </button>
        <button
          className={`pg-anim-btn ${localShowVelocity ? 'active' : ''}`}
          onClick={() => setLocalShowVelocity(v => !v)}
          aria-label="Toggle velocity"
          title="Show velocity & streamlines"
          style={{ fontSize: '0.7rem', width: 'auto', padding: '0 6px' }}
        >
          V
        </button>
        <button
          className={`pg-anim-btn ${localShowAoA ? 'active' : ''}`}
          onClick={() => setLocalShowAoA(v => !v)}
          aria-label="Toggle angle of attack"
          title="Show angle of attack"
          style={{ fontSize: '0.7rem', width: 'auto', padding: '0 6px' }}
        >
          α
        </button>
      </div>

      {/* Plots */}
      <div className="pg-plots">
        {plots?.map((plot) => (
          <div key={plot.id} className="pg-plot-wrap">
            <Plot
              data={plot.data}
              layout={{
                ...plot.layout,
                paper_bgcolor: isDark ? '#0a0e27' : 'rgba(255,255,255,0.98)',
                plot_bgcolor: isDark ? '#131b2e' : '#f8fafc',
                font: {
                  ...plot.layout?.font,
                  color: isDark ? '#e2e8f0' : '#1e293b',
                },
                autosize: true,
                datarevision: `${plot.id}-${Date.now()}`,
              }}
              config={{
                responsive: true,
                displayModeBar: false,
              }}
              useResizeHandler
              style={{ width: '100%', height: 280 }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
