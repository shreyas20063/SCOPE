/**
 * MassSpringViewer Component
 *
 * Custom viewer for Mass-Spring System simulation.
 * Left: Canvas 2D spring-mass animation driven by pre-computed trajectory.
 * Right: Time-domain response + phase portrait plots.
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import Plot from 'react-plotly.js';
import './MassSpringViewer.css';

/* ------------------------------------------------------------------ */
/*  Theme hook (same pattern as RCLowpassViewer)                      */
/* ------------------------------------------------------------------ */

function useTheme() {
  const [theme, setTheme] = React.useState(() => {
    return document.documentElement.getAttribute('data-theme') || 'dark';
  });

  React.useEffect(() => {
    const observer = new MutationObserver(() => {
      const newTheme = document.documentElement.getAttribute('data-theme') || 'dark';
      setTheme(newTheme);
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
/*  Canvas spring-mass animation                                      */
/* ------------------------------------------------------------------ */

function SpringAnimation({ visualization2D, theme }) {
  const canvasRef = useRef(null);
  const frameRef = useRef(0);
  const lastTimeRef = useRef(0);
  const playingRef = useRef(true);
  const [isPlaying, setIsPlaying] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);

  const isDark = theme === 'dark';

  // Sync ref with state
  useEffect(() => { playingRef.current = isPlaying; }, [isPlaying]);

  // Reset frame when trajectory data changes
  useEffect(() => {
    frameRef.current = 0;
    setCurrentTime(0);
  }, [visualization2D]);

  const drawFrame = useCallback((ctx, w, h, frameIndex, viz) => {
    const {
      input_position, mass_position, time, num_frames,
    } = viz;

    const idx = Math.min(frameIndex, num_frames - 1);
    const baseY = input_position[idx] || 0;   // ceiling displacement
    const massY = mass_position[idx] || 0;     // mass displacement

    // --- coordinate mapping ---
    // Find max displacement for scaling
    const allPos = [...input_position, ...mass_position];
    const maxAbs = Math.max(0.5, Math.max(...allPos.map(Math.abs)));
    const scale = (h * 0.3) / maxAbs;  // 30% of canvas height per maxAbs

    const cx = w / 2;                     // horizontal center
    const ceilingRest = h * 0.12;         // resting ceiling y
    const massRest = h * 0.72;            // resting mass y

    const ceilingY = ceilingRest + baseY * scale;
    const massBlockY = massRest + massY * scale;

    // --- clear ---
    ctx.clearRect(0, 0, w, h);

    // --- colors ---
    const textColor = isDark ? '#e2e8f0' : '#1e293b';
    const mutedColor = isDark ? '#64748b' : '#94a3b8';
    const springColor = isDark ? '#3b82f6' : '#2563eb';
    const damperColor = isDark ? '#f59e0b' : '#d97706';
    const massColor = isDark ? '#ef4444' : '#dc2626';
    const ceilingColor = isDark ? '#64748b' : '#94a3b8';

    // --- ceiling / base ---
    ctx.save();
    ctx.fillStyle = ceilingColor;
    ctx.fillRect(cx - 60, ceilingY - 4, 120, 4);
    // hatching
    ctx.strokeStyle = ceilingColor;
    ctx.lineWidth = 1;
    for (let xi = cx - 60; xi < cx + 60; xi += 8) {
      ctx.beginPath();
      ctx.moveTo(xi, ceilingY - 4);
      ctx.lineTo(xi - 6, ceilingY - 12);
      ctx.stroke();
    }
    ctx.restore();

    // Label: "Base x(t)"
    ctx.save();
    ctx.font = '11px Inter, sans-serif';
    ctx.fillStyle = '#3b82f6';
    ctx.textAlign = 'right';
    ctx.fillText(`x(t) = ${baseY.toFixed(3)} m`, cx - 68, ceilingY - 2);
    ctx.restore();

    // --- spring (left side) ---
    const springX = cx - 20;
    const springTop = ceilingY;
    const springBot = massBlockY;
    drawSpring(ctx, springX, springTop, springBot, 14, springColor);

    // --- damper (right side) ---
    const damperX = cx + 20;
    drawDamper(ctx, damperX, springTop, springBot, damperColor);

    // --- mass block ---
    const blockW = 70;
    const blockH = 30;
    ctx.save();
    ctx.fillStyle = massColor;
    ctx.shadowColor = 'rgba(239, 68, 68, 0.4)';
    ctx.shadowBlur = 12;
    ctx.beginPath();
    ctx.roundRect(cx - blockW / 2, massBlockY, blockW, blockH, 4);
    ctx.fill();
    ctx.shadowBlur = 0;
    // "m" label on block
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 13px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('m', cx, massBlockY + blockH / 2);
    ctx.restore();

    // Label: "y(t)"
    ctx.save();
    ctx.font = '11px Inter, sans-serif';
    ctx.fillStyle = '#ef4444';
    ctx.textAlign = 'left';
    ctx.fillText(`y(t) = ${massY.toFixed(3)} m`, cx + blockW / 2 + 8, massBlockY + blockH / 2 + 1);
    ctx.restore();

    // --- equilibrium reference line (dashed) ---
    ctx.save();
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = mutedColor;
    ctx.lineWidth = 1;
    ctx.globalAlpha = 0.4;
    ctx.beginPath();
    ctx.moveTo(cx - 80, massRest);
    ctx.lineTo(cx + 80, massRest);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.globalAlpha = 1.0;
    ctx.restore();

    // --- time display ---
    const t = time[idx] || 0;
    ctx.save();
    ctx.font = '12px "Fira Code", monospace';
    ctx.fillStyle = textColor;
    ctx.textAlign = 'center';
    ctx.fillText(`t = ${t.toFixed(2)} s`, cx, h - 16);
    ctx.restore();

    // --- progress bar ---
    const barY = h - 6;
    const barW = w - 40;
    const barX = 20;
    const progress = idx / Math.max(1, num_frames - 1);
    ctx.save();
    ctx.fillStyle = isDark ? 'rgba(148,163,184,0.15)' : 'rgba(100,116,139,0.15)';
    ctx.fillRect(barX, barY, barW, 3);
    ctx.fillStyle = '#14b8a6';
    ctx.fillRect(barX, barY, barW * progress, 3);
    ctx.restore();
  }, [isDark]);

  // Animation loop
  useEffect(() => {
    if (!visualization2D || visualization2D.num_frames < 2) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    const frameDt = visualization2D.dt * 1000; // ms between frames

    let animId;

    const loop = (timestamp) => {
      if (playingRef.current) {
        const elapsed = timestamp - lastTimeRef.current;
        if (elapsed >= frameDt) {
          lastTimeRef.current = timestamp;
          frameRef.current = (frameRef.current + 1) % visualization2D.num_frames;
          setCurrentTime(visualization2D.time[frameRef.current] || 0);
        }
      }
      drawFrame(ctx, w, h, frameRef.current, visualization2D);
      animId = requestAnimationFrame(loop);
    };

    lastTimeRef.current = performance.now();
    animId = requestAnimationFrame(loop);

    return () => cancelAnimationFrame(animId);
  }, [visualization2D, drawFrame]);

  const togglePlay = () => setIsPlaying(p => !p);
  const restart = () => {
    frameRef.current = 0;
    setCurrentTime(0);
  };

  return (
    <div className="ms-animation-panel">
      <canvas
        ref={canvasRef}
        className="ms-canvas"
        style={{ width: '100%', height: '100%' }}
      />
      <div className="ms-animation-controls">
        <button className="ms-btn" onClick={togglePlay}>
          {isPlaying ? '\u23F8' : '\u25B6'}
        </button>
        <button className="ms-btn" onClick={restart}>
          \u21BA
        </button>
        <span className="ms-time-label">
          {currentTime.toFixed(2)} / {visualization2D?.total_time?.toFixed(1) ?? '?'} s
        </span>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Canvas drawing helpers                                            */
/* ------------------------------------------------------------------ */

function drawSpring(ctx, x, y1, y2, coils, color) {
  const len = y2 - y1;
  if (Math.abs(len) < 2) return;

  const segH = len / (coils * 2 + 2); // height per half-coil
  const amplitude = 10;

  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.lineJoin = 'round';
  ctx.beginPath();
  ctx.moveTo(x, y1);

  // straight leader
  ctx.lineTo(x, y1 + segH);

  // zigzag
  for (let i = 0; i < coils * 2; i++) {
    const yy = y1 + segH + (i + 1) * segH;
    const dx = (i % 2 === 0) ? amplitude : -amplitude;
    ctx.lineTo(x + dx, yy);
  }

  // straight trailer
  ctx.lineTo(x, y2);
  ctx.stroke();
  ctx.restore();
}

function drawDamper(ctx, x, y1, y2, color) {
  const len = y2 - y1;
  if (Math.abs(len) < 10) return;

  const midY = (y1 + y2) / 2;
  const pistonH = Math.min(Math.abs(len) * 0.3, 20);
  const cylW = 14;
  const cylH = Math.abs(len) * 0.35;

  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;

  // rod top (from ceiling to cylinder)
  ctx.beginPath();
  ctx.moveTo(x, y1);
  ctx.lineTo(x, midY - cylH / 2);
  ctx.stroke();

  // cylinder body
  ctx.strokeRect(x - cylW / 2, midY - cylH / 2, cylW, cylH);

  // piston rod (from inside cylinder down to mass)
  ctx.beginPath();
  ctx.moveTo(x, midY + cylH / 2);
  ctx.lineTo(x, y2);
  ctx.stroke();

  // piston head inside cylinder
  ctx.lineWidth = 3;
  ctx.beginPath();
  const pistonY = midY - cylH / 2 + (len > 0 ? cylH * 0.7 : cylH * 0.3);
  ctx.moveTo(x - cylW / 2 + 2, Math.min(pistonY, midY + cylH / 2 - 2));
  ctx.lineTo(x + cylW / 2 - 2, Math.min(pistonY, midY + cylH / 2 - 2));
  ctx.stroke();

  ctx.restore();
}

/* ------------------------------------------------------------------ */
/*  System info badge                                                 */
/* ------------------------------------------------------------------ */

function SystemInfoBadge({ metadata }) {
  const info = metadata?.system_info;
  if (!info) return null;

  const typeColors = {
    underdamped: '#3b82f6',
    critically_damped: '#10b981',
    overdamped: '#f59e0b',
  };
  const color = typeColors[info.damping_type] || '#6b7280';
  const label = info.damping_type?.replace('_', ' ') || '';

  return (
    <div className="ms-info-badge">
      <div className="ms-info-row">
        <span className="ms-type-pill" style={{ backgroundColor: color }}>
          {label}
        </span>
        <span className="ms-info-detail">
          \u03b6 = {info.damping_ratio}
        </span>
        <span className="ms-sep">|</span>
        <span className="ms-info-detail">
          f<sub>n</sub> = {info.natural_frequency_hz} Hz
        </span>
        {info.damped_frequency_hz != null && (
          <>
            <span className="ms-sep">|</span>
            <span className="ms-info-detail">
              f<sub>d</sub> = {info.damped_frequency_hz} Hz
            </span>
          </>
        )}
        {info.period != null && (
          <>
            <span className="ms-sep">|</span>
            <span className="ms-info-detail">
              T = {info.period} s
            </span>
          </>
        )}
      </div>
      <div className="ms-info-row ms-info-secondary">
        <span>peak |y| = {info.peak_output} m</span>
        <span className="ms-sep">|</span>
        <span>steady state = {info.steady_state} m</span>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Plot component (same pattern as RCLowpassViewer)                  */
/* ------------------------------------------------------------------ */

function MSPlot({ plot, theme, height = 280 }) {
  const isDark = theme === 'dark';

  const layout = {
    title: {
      text: plot.title || 'Plot',
      font: { color: isDark ? '#f1f5f9' : '#1e293b', size: 15 },
      x: 0.5,
      xanchor: 'center',
    },
    paper_bgcolor: isDark ? '#0f172a' : 'rgba(255, 255, 255, 0.98)',
    plot_bgcolor: isDark ? '#1e293b' : '#f8fafc',
    font: {
      color: isDark ? '#e2e8f0' : '#1e293b',
      family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      size: 12,
    },
    xaxis: {
      ...plot.layout?.xaxis,
      gridcolor: isDark ? 'rgba(71, 85, 105, 0.4)' : 'rgba(100, 116, 139, 0.2)',
      gridwidth: 1,
      zerolinecolor: isDark ? 'rgba(148, 163, 184, 0.5)' : 'rgba(100, 116, 139, 0.5)',
      zerolinewidth: 1.5,
      tickfont: { color: isDark ? '#94a3b8' : '#475569', size: 11 },
      title: {
        text: plot.layout?.xaxis?.title || '',
        font: { color: isDark ? '#94a3b8' : '#334155', size: 12 },
      },
      showline: true,
      linecolor: isDark ? '#475569' : '#cbd5e1',
      linewidth: 1,
    },
    yaxis: {
      ...plot.layout?.yaxis,
      gridcolor: isDark ? 'rgba(71, 85, 105, 0.4)' : 'rgba(100, 116, 139, 0.2)',
      gridwidth: 1,
      zerolinecolor: isDark ? 'rgba(148, 163, 184, 0.5)' : 'rgba(100, 116, 139, 0.5)',
      zerolinewidth: 1.5,
      tickfont: { color: isDark ? '#94a3b8' : '#475569', size: 11 },
      title: {
        text: plot.layout?.yaxis?.title || '',
        font: { color: isDark ? '#94a3b8' : '#334155', size: 12 },
      },
      showline: true,
      linecolor: isDark ? '#475569' : '#cbd5e1',
      linewidth: 1,
    },
    legend: {
      font: { color: isDark ? '#e2e8f0' : '#1e293b', size: 11 },
      bgcolor: isDark ? 'rgba(30, 41, 59, 0.9)' : 'rgba(255, 255, 255, 0.9)',
      bordercolor: isDark ? '#334155' : '#e2e8f0',
      borderwidth: 1,
      ...plot.layout?.legend,
    },
    margin: { t: 45, r: 25, b: 55, l: 60 },
    height,
    autosize: true,
    showlegend: true,
    datarevision: `${plot.id}-${plot.title}-${Date.now()}`,
    uirevision: plot.id,
  };

  const config = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    displaylogo: false,
  };

  return (
    <div className="ms-plot-card">
      <Plot
        data={plot.data || []}
        layout={layout}
        config={config}
        useResizeHandler={true}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main viewer                                                       */
/* ------------------------------------------------------------------ */

function MassSpringViewer({ metadata, plots }) {
  const theme = useTheme();

  if (!plots || plots.length === 0) {
    return (
      <div className="ms-viewer">
        <div className="ms-viewer-empty">
          <p>Loading Mass-Spring System simulation...</p>
        </div>
      </div>
    );
  }

  const responsePlot = plots.find(p => p.id === 'response');
  const phasePlot = plots.find(p => p.id === 'phase_portrait');

  return (
    <div className="ms-viewer">
      <SystemInfoBadge metadata={metadata} />

      <div className="ms-split-layout">
        {/* Left: animated spring-mass */}
        <SpringAnimation
          visualization2D={metadata?.visualization_2d}
          theme={theme}
        />

        {/* Right: plots stacked */}
        <div className="ms-plots-panel">
          {responsePlot && <MSPlot plot={responsePlot} theme={theme} />}
          {phasePlot && <MSPlot plot={phasePlot} theme={theme} height={260} />}
        </div>
      </div>
    </div>
  );
}

export default MassSpringViewer;
