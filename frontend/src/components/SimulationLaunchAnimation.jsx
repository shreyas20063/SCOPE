/**
 * SimulationLaunchAnimation
 *
 * Realistic oscilloscope boot-up animation with:
 * - Tektronix/Keysight-style device (screen left, controls right)
 * - 10×8 graticule grid on CRT screen
 * - 5-phase waveform narrative: flat→sine→escalation→chaos→collapse
 * - 3-layer neon glow rendering
 * - Safety timeout for guaranteed completion
 */

import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import '../styles/SimulationLaunchAnimation.css';

/* ── Neon color mapping ── */
const NEON_MAP = {
  '#06b6d4': '#00ffff',   // Signal Processing → electric cyan
  '#8b5cf6': '#bf7fff',   // Circuits → vivid purple
  '#f59e0b': '#ff8c00',   // Control Systems → vivid orange
  '#10b981': '#00ff88',   // Transforms → mint green
  '#ec4899': '#ff006e',   // Optics → hot pink
};

function getNeonColor(categoryColor) {
  if (!categoryColor) return '#00ffff';
  const key = categoryColor.toLowerCase();
  return NEON_MAP[key] || '#00ffff';
}

/* ── Smooth interpolation (no hard phase boundaries) ── */
// 5th-order smootherstep: C2 continuous, zero velocity at endpoints
function smootherstep(t) {
  const c = Math.max(0, Math.min(1, t));
  return c * c * c * (c * (c * 6 - 15) + 10);
}

// Smooth ramp from 0→1 between [lo, hi]
function sramp(t, lo, hi) {
  return smootherstep((t - lo) / (hi - lo));
}

// Smooth bell curve: peaks at `center`, width controls falloff
function sbell(t, center, width) {
  return Math.exp(-Math.pow((t - center) / width, 2));
}

const T_ANIM_END = 3.45;  // animation complete (includes CRT shutdown)
const T_SAFETY = 4800;    // hard safety timeout ms

// Soft wave folding: wraps signal back when it exceeds ±1 (organic chaos)
function softFold(x) {
  const p = ((x % 4) + 4) % 4;
  return p < 1 ? p : p < 3 ? 2 - p : p - 4;
}

// Magenta color for ghost CH2
const CH2_COLOR = { r: 255, g: 111, b: 255 };

/* ── Grid / graticule ── */
const GRID_DIVS_X = 10;
const GRID_DIVS_Y = 8;
const GRID_SUBDIVS = 5;

function SimulationLaunchAnimation({
  simulationName,
  category,
  categoryColor,
  isDataReady,
  onComplete,
}) {
  const canvasRef = useRef(null);
  const animFrameRef = useRef(null);
  const startTimeRef = useRef(null);
  const completedRef = useRef(false);
  const safetyTimerRef = useRef(null);
  const dataReadyTimeRef = useRef(null);

  const [fadeOut, setFadeOut] = useState(false);
  const [screenOn, setScreenOn] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [typedName, setTypedName] = useState('');

  const neonColor = useMemo(() => getNeonColor(categoryColor), [categoryColor]);

  // Parse neon color to RGB
  const neonRGB = useMemo(() => {
    const hex = neonColor.replace('#', '');
    return {
      r: parseInt(hex.substring(0, 2), 16),
      g: parseInt(hex.substring(2, 4), 16),
      b: parseInt(hex.substring(4, 6), 16),
    };
  }, [neonColor]);

  /* ── Finish animation ── */
  const finishAnimation = useCallback(() => {
    if (completedRef.current) return;
    completedRef.current = true;
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
    if (safetyTimerRef.current) {
      clearTimeout(safetyTimerRef.current);
      safetyTimerRef.current = null;
    }
    setIsReady(true);
    setFadeOut(true);
    setTimeout(() => {
      onComplete?.();
    }, 320);
  }, [onComplete]);

  /* ── Track data ready ── */
  useEffect(() => {
    if (isDataReady && !dataReadyTimeRef.current) {
      dataReadyTimeRef.current = performance.now();
    }
  }, [isDataReady]);

  /* ── Type simulation name ── */
  useEffect(() => {
    if (!simulationName) return;
    let idx = 0;
    setTypedName('');
    const interval = setInterval(() => {
      idx++;
      if (idx <= simulationName.length) {
        setTypedName(simulationName.slice(0, idx));
      } else {
        clearInterval(interval);
      }
    }, 35);
    return () => clearInterval(interval);
  }, [simulationName]);

  /* ── Screen on after brief delay ── */
  useEffect(() => {
    const t = setTimeout(() => setScreenOn(true), 200);
    return () => clearTimeout(t);
  }, []);

  /* ── Safety timeout ── */
  useEffect(() => {
    safetyTimerRef.current = setTimeout(() => {
      finishAnimation();
    }, T_SAFETY);
    return () => {
      if (safetyTimerRef.current) clearTimeout(safetyTimerRef.current);
    };
  }, [finishAnimation]);

  /* ── Draw graticule ── */
  const drawGraticule = useCallback((ctx, w, h) => {
    const gw = w;
    const gh = h;
    const divW = gw / GRID_DIVS_X;
    const divH = gh / GRID_DIVS_Y;

    // Major grid lines
    ctx.strokeStyle = 'rgba(0, 229, 255, 0.08)';
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    for (let i = 0; i <= GRID_DIVS_X; i++) {
      const x = i * divW;
      ctx.moveTo(x, 0);
      ctx.lineTo(x, gh);
    }
    for (let j = 0; j <= GRID_DIVS_Y; j++) {
      const y = j * divH;
      ctx.moveTo(0, y);
      ctx.lineTo(gw, y);
    }
    ctx.stroke();

    // Center crosshair (brighter)
    const cx = gw / 2;
    const cy = gh / 2;
    ctx.strokeStyle = 'rgba(0, 229, 255, 0.18)';
    ctx.lineWidth = 0.8;
    ctx.beginPath();
    ctx.moveTo(0, cy);
    ctx.lineTo(gw, cy);
    ctx.moveTo(cx, 0);
    ctx.lineTo(cx, gh);
    ctx.stroke();

    // Minor subdivision ticks along center axes
    ctx.strokeStyle = 'rgba(0, 229, 255, 0.12)';
    ctx.lineWidth = 0.5;
    const tickLen = 3;
    ctx.beginPath();
    for (let i = 0; i <= GRID_DIVS_X; i++) {
      for (let s = 1; s < GRID_SUBDIVS; s++) {
        const x = i * divW + s * (divW / GRID_SUBDIVS);
        if (x <= gw) {
          ctx.moveTo(x, cy - tickLen);
          ctx.lineTo(x, cy + tickLen);
        }
      }
    }
    for (let j = 0; j <= GRID_DIVS_Y; j++) {
      for (let s = 1; s < GRID_SUBDIVS; s++) {
        const y = j * divH + s * (divH / GRID_SUBDIVS);
        if (y <= gh) {
          ctx.moveTo(cx - tickLen, y);
          ctx.lineTo(cx + tickLen, y);
        }
      }
    }
    ctx.stroke();
  }, []);

  /* ── Draw waveform with 3-layer glow ── */
  const drawWaveform = useCallback((ctx, points, color, intensity = 1.0, widthScale = 1.0) => {
    if (points.length < 2) return;

    const { r, g, b } = color;
    const ws = widthScale;

    // Layer 1: Wide outer glow
    ctx.save();
    ctx.shadowColor = `rgba(${r}, ${g}, ${b}, ${0.5 * intensity})`;
    ctx.shadowBlur = 70 * ws;
    ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${0.35 * intensity})`;
    ctx.lineWidth = 8 * ws;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(points[i].x, points[i].y);
    }
    ctx.stroke();
    ctx.restore();

    // Layer 2: Medium glow
    ctx.save();
    ctx.shadowColor = `rgba(${r}, ${g}, ${b}, ${0.6 * intensity})`;
    ctx.shadowBlur = 30 * ws;
    ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${0.65 * intensity})`;
    ctx.lineWidth = 3.5 * ws;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(points[i].x, points[i].y);
    }
    ctx.stroke();
    ctx.restore();

    // Layer 3: Sharp bright core
    ctx.save();
    ctx.shadowColor = `rgba(${r}, ${g}, ${b}, ${0.4 * intensity})`;
    ctx.shadowBlur = 8 * ws;
    ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${1.0 * intensity})`;
    ctx.lineWidth = 1.8 * ws;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(points[i].x, points[i].y);
    }
    ctx.stroke();
    ctx.restore();
  }, []);

  /* ── Main animation loop (continuous envelopes + CRT shutdown) ── */
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const resizeCanvas = () => {
      const rect = canvas.parentElement?.getBoundingClientRect();
      if (!rect) return;
      const dpr = window.devicePixelRatio || 1;
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      canvas.style.width = rect.width + 'px';
      canvas.style.height = rect.height + 'px';
    };

    resizeCanvas();
    const observer = new ResizeObserver(resizeCanvas);
    if (canvas.parentElement) observer.observe(canvas.parentElement);

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Phase accumulator for smooth frequency changes
    let phaseAccum = 0;
    let lastElapsed = 0;

    const animate = (timestamp) => {
      if (completedRef.current) return;

      if (!startTimeRef.current) {
        startTimeRef.current = timestamp;
      }

      const elapsed = (timestamp - startTimeRef.current) / 1000;
      const dt = Math.min(elapsed - lastElapsed, 0.05);
      lastElapsed = elapsed;

      const dpr = window.devicePixelRatio || 1;
      const w = canvas.width;
      const h = canvas.height;

      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.scale(dpr, dpr);
      const dispW = w / dpr;
      const dispH = h / dpr;

      // ════════════════════════════════════════════
      //  CONTINUOUS ENVELOPES — all smooth, no phase boundaries
      // ════════════════════════════════════════════

      // Line reveal: draws left→right over 0–0.5s
      const reveal    = sramp(elapsed, 0.0, 0.5);

      // Initial pulse: brief blip at ~0.25s
      const pulse     = sbell(elapsed, 0.28, 0.12);

      // Main amplitude: rises 0.2–0.9s, holds, collapses 2.1–2.65s
      const ampRise   = sramp(elapsed, 0.2, 0.9);
      const ampFall   = 1 - sramp(elapsed, 2.1, 2.65);
      const ampEnv    = ampRise * ampFall;

      // Frequency: 2 cycles at rest, peaks at ~10 around t=1.8
      const freqEnv   = 2 + 8 * sbell(elapsed, 1.8, 0.65);

      // Harmonics: fade in 0.8–1.4s, fade out 2.0–2.5s
      const harmEnv   = sramp(elapsed, 0.8, 1.4) * (1 - sramp(elapsed, 2.0, 2.5));

      // Chaos/noise: builds 1.3–1.8s, decays 2.1–2.5s
      const noiseEnv  = sramp(elapsed, 1.3, 1.8) * (1 - sramp(elapsed, 2.1, 2.5));

      // Ghost CH2 envelope: faint during escalation/chaos
      const ch2Env    = sramp(elapsed, 1.0, 1.4) * (1 - sramp(elapsed, 2.1, 2.4));

      // Screen glow intensity
      const glowEnv   = sramp(elapsed, 0.6, 1.2) * (1 - sramp(elapsed, 2.2, 2.7));

      // Resonance bursts: periodic brightness peaks during escalation
      const resonanceGate = sramp(elapsed, 0.9, 1.2) * (1 - sramp(elapsed, 2.1, 2.3));
      const resonancePulse = Math.pow(Math.max(0, Math.sin(elapsed * 8)), 12);
      const resonance = resonanceGate * resonancePulse;

      // CRT SHUTDOWN envelopes (tightened timing)
      const vSqueeze      = sramp(elapsed, 2.65, 2.82);   // vertical crush
      const hSqueeze      = sramp(elapsed, 2.82, 3.05);   // horizontal pinch
      const dotPhase      = sramp(elapsed, 2.95, 3.05);   // becomes dot
      const dotFade       = 1 - sramp(elapsed, 3.05, 3.35); // dot fades out
      const squeezeBright = sbell(elapsed, 2.82, 0.1);     // brightness peak during squeeze

      // Dynamic width: thicker at high energy
      const energy = ampEnv + noiseEnv * 0.5 + resonance * 0.3;
      const widthScale = 0.8 + energy * 0.8 + squeezeBright * 1.5;

      // Overall brightness
      const intensity = Math.max(0.08, ampEnv + pulse * 0.5 + resonance * 0.6 + squeezeBright * 2);

      // Is the CRT dot phase (post-squeeze)?
      const inDotPhase = dotPhase > 0.9;
      const isDone = elapsed > T_ANIM_END;
      // Trigger exit early if dot is nearly gone and data is ready
      const dotAlmostGone = dotFade < 0.08;

      // Accumulate phase for smooth traveling wave
      phaseAccum += dt * freqEnv * 2.5;

      // ── PHOSPHOR PERSISTENCE CLEAR ──
      // Semi-transparent clear: 82% opacity leaves subtle ghost trail
      ctx.fillStyle = 'rgba(2, 5, 8, 0.82)';
      ctx.fillRect(0, 0, dispW, dispH);

      // Re-draw graticule (fades during CRT shutdown)
      const gratAlpha = 1 - sramp(elapsed, 2.7, 2.9);
      if (gratAlpha > 0.01) {
        ctx.globalAlpha = gratAlpha;
        drawGraticule(ctx, dispW, dispH);
        ctx.globalAlpha = 1;
      }

      // ── CRT DOT PHASE (after squeeze completes) ──
      if (inDotPhase) {
        if (dotFade > 0.01) {
          const cx = dispW / 2;
          const cy = dispH / 2;
          const dotSize = 3 * dotFade;
          const { r, g, b } = neonRGB;

          // Outer bloom
          ctx.save();
          ctx.shadowColor = `rgba(${r}, ${g}, ${b}, ${0.8 * dotFade})`;
          ctx.shadowBlur = 80 * dotFade;
          ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${0.3 * dotFade})`;
          ctx.beginPath();
          ctx.arc(cx, cy, dotSize * 4, 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();

          // Inner bright dot
          ctx.save();
          ctx.shadowColor = `rgba(${r}, ${g}, ${b}, ${dotFade})`;
          ctx.shadowBlur = 40 * dotFade;
          ctx.fillStyle = `rgba(255, 255, 255, ${0.9 * dotFade})`;
          ctx.beginPath();
          ctx.arc(cx, cy, dotSize, 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();

          // Core white-hot point
          ctx.save();
          ctx.shadowColor = `rgba(255, 255, 255, ${0.6 * dotFade})`;
          ctx.shadowBlur = 15;
          ctx.fillStyle = `rgba(255, 255, 255, ${dotFade})`;
          ctx.beginPath();
          ctx.arc(cx, cy, Math.max(0.5, dotSize * 0.4), 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();
        }

        if ((dotAlmostGone || isDone) && isDataReady) {
          finishAnimation();
        }
        animFrameRef.current = requestAnimationFrame(animate);
        return;
      }

      // ── GENERATE CH1 WAVEFORM ──
      const numPoints = 500;
      const ch1Points = [];
      const ch2Points = [];
      const cy = dispH / 2;
      const maxAmp = dispH * 0.38;

      // Horizontal extent (shrinks during h-squeeze)
      const hExtent = 1 - hSqueeze * 0.97;
      const hStart = 0.5 - hExtent / 2;
      const hEnd = 0.5 + hExtent / 2;

      for (let i = 0; i < numPoints; i++) {
        const xn = i / (numPoints - 1);

        // Skip points outside horizontal squeeze range
        if (xn < hStart || xn > hEnd) continue;

        // Reveal mask
        const maskEdge = reveal * 1.15;
        const mask = smootherstep(Math.min(1, (maskEdge - xn) * 12));
        if (mask < 0.001) continue;

        const x = xn * dispW;

        // ── Base sine (traveling wave) ──
        const basePhase = 2 * Math.PI * freqEnv * xn + phaseAccum;
        let signal = Math.sin(basePhase);

        // ── Harmonics ──
        signal += harmEnv * 0.35 * Math.sin(basePhase * 2 + elapsed * 1.7);
        signal += harmEnv * 0.18 * Math.sin(basePhase * 3 - elapsed * 0.9);
        signal += harmEnv * 0.08 * Math.sin(basePhase * 5 + elapsed * 2.3);

        // ── Chaos noise ──
        const nx = xn * 2 * Math.PI;
        signal += noiseEnv * 0.45 * Math.sin(nx * 15.7 + elapsed * 31.3);
        signal += noiseEnv * 0.30 * Math.sin(nx * 23.1 + elapsed * 47.7);
        signal += noiseEnv * 0.20 * Math.cos(nx * 37.3 + elapsed * 19.1);
        signal += noiseEnv * 0.15 * Math.sin(nx * 53.9 + elapsed * 67.3);
        const spikeRaw = Math.sin(nx * 7.3 + elapsed * 11.7);
        signal += noiseEnv * 0.35 * Math.pow(Math.max(0, spikeRaw), 4);

        // ── Wave folding during chaos (organic wrap instead of hard clamp) ──
        if (noiseEnv > 0.3) {
          const foldAmount = noiseEnv * 0.6;
          signal = signal * (1 - foldAmount) + softFold(signal) * foldAmount;
        }

        // ── Apply amplitude envelope ──
        let yOffset = signal * ampEnv * maxAmp;

        // ── Initial pulse (gaussian blip) ──
        const pulseSig = pulse * maxAmp * 0.55 * Math.exp(-Math.pow((xn - 0.5) * 8, 2));
        yOffset -= pulseSig;

        // ── Apply reveal mask ──
        yOffset *= mask;

        // ── Vertical squeeze: crush y toward center ──
        yOffset *= (1 - vSqueeze);

        const yFinal = Math.max(dispH * 0.02, Math.min(dispH * 0.98, cy + yOffset));
        ch1Points.push({ x, y: yFinal });

        // ── Ghost CH2 (phase-shifted, lower amplitude, magenta) ──
        if (ch2Env > 0.02) {
          const ch2Phase = basePhase + Math.PI / 3;
          let ch2Signal = Math.sin(ch2Phase);
          ch2Signal += harmEnv * 0.2 * Math.sin(ch2Phase * 2 + elapsed * 2.1);
          let ch2Y = ch2Signal * ampEnv * maxAmp * 0.4 * ch2Env;
          ch2Y *= mask;
          ch2Y *= (1 - vSqueeze);
          const ch2Final = Math.max(dispH * 0.02, Math.min(dispH * 0.98, cy + ch2Y));
          ch2Points.push({ x, y: ch2Final });
        }
      }

      // ── Draw ghost CH2 first (behind CH1) ──
      if (ch2Points.length > 1) {
        drawWaveform(ctx, ch2Points, CH2_COLOR, ch2Env * 0.3, widthScale * 0.6);
      }

      // ── Draw main CH1 waveform ──
      if (ch1Points.length > 1) {
        drawWaveform(ctx, ch1Points, neonRGB, intensity, widthScale);
      }

      // ── Screen glow (radial, pulses with energy) ──
      if (glowEnv > 0.01) {
        const glowPulse = 0.7 + 0.3 * Math.sin(elapsed * 5);
        const glowAlpha = glowEnv * 0.06 * glowPulse + resonance * 0.04;
        const grad = ctx.createRadialGradient(
          dispW / 2, dispH / 2, 0,
          dispW / 2, dispH / 2, dispW * 0.5
        );
        grad.addColorStop(0, `rgba(${neonRGB.r}, ${neonRGB.g}, ${neonRGB.b}, ${glowAlpha})`);
        grad.addColorStop(0.6, `rgba(${neonRGB.r}, ${neonRGB.g}, ${neonRGB.b}, ${glowAlpha * 0.3})`);
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, dispW, dispH);
      }

      // ── Resonance flash (brief bright pulse during escalation) ──
      if (resonance > 0.3) {
        ctx.fillStyle = `rgba(${neonRGB.r}, ${neonRGB.g}, ${neonRGB.b}, ${resonance * 0.03})`;
        ctx.fillRect(0, 0, dispW, dispH);
      }

      // ── Chaos flashes ──
      if (noiseEnv > 0.5 && Math.random() < noiseEnv * 0.06) {
        ctx.fillStyle = `rgba(255, 255, 255, ${0.02 + noiseEnv * 0.03})`;
        ctx.fillRect(0, 0, dispW, dispH);
      }

      // ── CRT crush flash (white burst when vertical squeeze hits) ──
      const crushFlash = sbell(elapsed, 2.78, 0.04);
      if (crushFlash > 0.05) {
        ctx.fillStyle = `rgba(255, 255, 255, ${crushFlash * 0.12})`;
        ctx.fillRect(0, 0, dispW, dispH);
      }

      // ── Squeeze brightness boost (CRT phosphor concentrates) ──
      if (squeezeBright > 0.1) {
        const { r, g, b } = neonRGB;
        ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${squeezeBright * 0.06})`;
        ctx.fillRect(0, 0, dispW, dispH);
      }

      animFrameRef.current = requestAnimationFrame(animate);
    };

    animFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
      observer.disconnect();
    };
  }, [drawGraticule, drawWaveform, neonRGB, isDataReady, finishAnimation]);

  return (
    <div className={`launch-overlay ${fadeOut ? 'fade-out' : ''}`}>
      <div className="scope-device">
        {/* Header */}
        <div className="scope-header">
          <span className="scope-brand">DSO-2100 Digital Oscilloscope</span>
          <span className="scope-model">SIG-SYSTEMS</span>
        </div>

        {/* Main body: screen left, controls right */}
        <div className="scope-body">
          {/* Screen area */}
          <div className="scope-screen-area">
            <div className={`scope-screen ${screenOn ? 'scope-screen-flicker' : ''}`}>
              {/* Channel readouts on screen */}
              <div className="scope-screen-readout">
                <span className="scope-screen-ch scope-screen-ch-1">CH1 1.00V</span>
                <span className="scope-screen-ch scope-screen-ch-2">500μs/div</span>
              </div>
              <canvas ref={canvasRef} className="scope-canvas" />
            </div>

            {/* Info bar below screen */}
            <div className="scope-info">
              {category && (
                <span
                  className="scope-category"
                  style={{
                    backgroundColor: neonColor,
                    boxShadow: `0 0 10px ${neonColor}60, 0 0 20px ${neonColor}20`,
                  }}
                >
                  {category}
                </span>
              )}
              <p className="scope-sim-name">
                {typedName}
                <span className="scope-cursor">▎</span>
              </p>
            </div>
          </div>

          {/* Control panel (right side) */}
          <div className="scope-controls-panel">
            {/* RUN section */}
            <div className="ctrl-section">
              <span className="ctrl-section-label">Run</span>
              <div className="ctrl-btn-row">
                <span className="ctrl-btn ctrl-btn-active">Auto</span>
                <span className={`ctrl-btn ${isReady ? 'ctrl-btn-stop' : 'ctrl-btn-run'}`}>
                  {isReady ? 'Stop' : 'Run'}
                </span>
                <span className="ctrl-btn">Single</span>
              </div>
            </div>

            {/* HORIZONTAL section */}
            <div className="ctrl-section">
              <span className="ctrl-section-label">Horizontal</span>
              <div className="ctrl-knob-row">
                <div className="ctrl-knob-group">
                  <div className="ctrl-knob ctrl-knob-cyan" />
                  <span className="ctrl-knob-label">Time/Div</span>
                </div>
                <div className="ctrl-knob-group">
                  <div className="ctrl-knob ctrl-knob-cyan" />
                  <span className="ctrl-knob-label">H-Pos</span>
                </div>
              </div>
            </div>

            {/* VERTICAL section */}
            <div className="ctrl-section">
              <span className="ctrl-section-label">Vertical</span>
              <div className="ctrl-ch-row">
                <div className="ctrl-ch-indicator">
                  <div className="ctrl-ch-led ctrl-ch-led-cyan" />
                  <span className="ctrl-ch-label">CH1</span>
                </div>
                <div className="ctrl-ch-indicator">
                  <div className="ctrl-ch-led ctrl-ch-led-magenta" />
                  <span className="ctrl-ch-label">CH2</span>
                </div>
              </div>
              <div className="ctrl-knob-row">
                <div className="ctrl-knob-group">
                  <div className="ctrl-knob ctrl-knob-cyan" />
                  <span className="ctrl-knob-label">V/Div</span>
                </div>
                <div className="ctrl-knob-group">
                  <div className="ctrl-knob ctrl-knob-magenta" />
                  <span className="ctrl-knob-label">V/Div</span>
                </div>
              </div>
            </div>

            {/* TRIGGER section */}
            <div className="ctrl-section">
              <span className="ctrl-section-label">Trigger</span>
              <div className="ctrl-knob-row">
                <div className="ctrl-knob-group">
                  <div className="ctrl-knob ctrl-knob-cyan" />
                  <span className="ctrl-knob-label">Level</span>
                </div>
              </div>
              <div className="ctrl-btn-row">
                <span className="ctrl-btn ctrl-btn-active">Edge</span>
                <span className="ctrl-btn">Source</span>
              </div>
            </div>

            {/* PORTS section */}
            <div className="ctrl-section">
              <span className="ctrl-section-label">Ports</span>
              <div className="ctrl-ports-row">
                <div className="ctrl-port">
                  <div className="ctrl-port-circle" />
                  <span className="ctrl-port-label">CH1</span>
                </div>
                <div className="ctrl-port">
                  <div className="ctrl-port-circle" />
                  <span className="ctrl-port-label">CH2</span>
                </div>
                <div className="ctrl-port">
                  <div className="ctrl-port-circle" />
                  <span className="ctrl-port-label">Ext</span>
                </div>
                <div className="ctrl-port">
                  <div className="ctrl-port-circle" />
                  <span className="ctrl-port-label">Cal</span>
                </div>
              </div>
            </div>

            {/* Status */}
            <div className="ctrl-status">
              <div
                className={`ctrl-power-led ${isReady ? 'ctrl-power-led-on' : 'ctrl-power-led-loading'}`}
              />
              <span
                className={`ctrl-status-label ${isReady ? 'ctrl-status-ready' : 'ctrl-status-loading'}`}
              >
                {isReady ? 'Ready' : 'Loading'}
              </span>
            </div>
          </div>
        </div>

        {/* Progress bar */}
        <div className="scope-progress">
          <div
            className={`scope-progress-bar ${isReady ? 'ready' : ''}`}
            style={{ background: neonColor }}
          />
        </div>
      </div>
    </div>
  );
}

export default SimulationLaunchAnimation;
