/**
 * WebsiteLaunchAnimation
 *
 * Full-viewport brand intro animation for first website visit.
 * Neon waveform sweeps across the screen behind "Signals & Systems" title,
 * builds to chaos, then CRT shutdown collapse.
 * Same visual language as SimulationLaunchAnimation but no device chrome.
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import '../styles/WebsiteLaunchAnimation.css';

/* ── Smooth interpolation (shared math with SimulationLaunchAnimation) ── */
function smootherstep(t) {
  const c = Math.max(0, Math.min(1, t));
  return c * c * c * (c * (c * 6 - 15) + 10);
}
function sramp(t, lo, hi) {
  return smootherstep((t - lo) / (hi - lo));
}
function sbell(t, center, width) {
  return Math.exp(-Math.pow((t - center) / width, 2));
}
function softFold(x) {
  const p = ((x % 4) + 4) % 4;
  return p < 1 ? p : p < 3 ? 2 - p : p - 4;
}

/* ── Colors ── */
const CYAN  = { r: 0, g: 255, b: 255 };
const MAGENTA = { r: 255, g: 111, b: 255 };
const TEAL  = { r: 20, g: 184, b: 166 };

/* ── Timing ── */
const T_ANIM_END = 3.6;
const T_SAFETY = 5000;

function WebsiteLaunchAnimation({ onComplete }) {
  const canvasRef = useRef(null);
  const animFrameRef = useRef(null);
  const startTimeRef = useRef(null);
  const completedRef = useRef(false);
  const safetyTimerRef = useRef(null);

  const [fadeOut, setFadeOut] = useState(false);
  const [showText, setShowText] = useState(false);
  const [showSubtext, setShowSubtext] = useState(false);
  const [textFadeOut, setTextFadeOut] = useState(false);

  /* ── Finish ── */
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
    setFadeOut(true);
    setTimeout(() => onComplete?.(), 400);
  }, [onComplete]);

  /* ── Safety timeout ── */
  useEffect(() => {
    safetyTimerRef.current = setTimeout(finishAnimation, T_SAFETY);
    return () => {
      if (safetyTimerRef.current) clearTimeout(safetyTimerRef.current);
    };
  }, [finishAnimation]);

  /* ── Text timing ── */
  useEffect(() => {
    const t1 = setTimeout(() => setShowText(true), 300);
    const t2 = setTimeout(() => setShowSubtext(true), 700);
    const t3 = setTimeout(() => setTextFadeOut(true), 2500);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); };
  }, []);

  /* ── Draw helpers ── */
  const drawWaveform = useCallback((ctx, points, color, intensity, widthScale = 1.0) => {
    if (points.length < 2) return;
    const { r, g, b } = color;
    const ws = widthScale;

    // Outer glow
    ctx.save();
    ctx.shadowColor = `rgba(${r},${g},${b},${0.5 * intensity})`;
    ctx.shadowBlur = 65 * ws;
    ctx.strokeStyle = `rgba(${r},${g},${b},${0.3 * intensity})`;
    ctx.lineWidth = 7 * ws;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) ctx.lineTo(points[i].x, points[i].y);
    ctx.stroke();
    ctx.restore();

    // Medium glow
    ctx.save();
    ctx.shadowColor = `rgba(${r},${g},${b},${0.6 * intensity})`;
    ctx.shadowBlur = 28 * ws;
    ctx.strokeStyle = `rgba(${r},${g},${b},${0.6 * intensity})`;
    ctx.lineWidth = 3.2 * ws;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) ctx.lineTo(points[i].x, points[i].y);
    ctx.stroke();
    ctx.restore();

    // Sharp core
    ctx.save();
    ctx.shadowColor = `rgba(${r},${g},${b},${0.4 * intensity})`;
    ctx.shadowBlur = 8 * ws;
    ctx.strokeStyle = `rgba(${r},${g},${b},${1.0 * intensity})`;
    ctx.lineWidth = 1.6 * ws;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) ctx.lineTo(points[i].x, points[i].y);
    ctx.stroke();
    ctx.restore();
  }, []);

  const drawGraticule = useCallback((ctx, w, h) => {
    // Faint 10×8 grid
    ctx.strokeStyle = 'rgba(0, 229, 255, 0.035)';
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    for (let i = 0; i <= 10; i++) {
      const x = (i / 10) * w;
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
    }
    for (let j = 0; j <= 8; j++) {
      const y = (j / 8) * h;
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
    }
    ctx.stroke();

    // Center cross (brighter)
    ctx.strokeStyle = 'rgba(0, 229, 255, 0.07)';
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    ctx.moveTo(0, h / 2);
    ctx.lineTo(w, h / 2);
    ctx.moveTo(w / 2, 0);
    ctx.lineTo(w / 2, h);
    ctx.stroke();
  }, []);

  /* ── Main animation loop ── */
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Respect reduced motion
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setTimeout(() => finishAnimation(), 300);
      return;
    }

    const resize = () => {
      const dpr = window.devicePixelRatio || 1;
      canvas.width = window.innerWidth * dpr;
      canvas.height = window.innerHeight * dpr;
      canvas.style.width = window.innerWidth + 'px';
      canvas.style.height = window.innerHeight + 'px';
    };
    resize();
    window.addEventListener('resize', resize);

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let phaseAccum = 0;
    let lastElapsed = 0;

    const animate = (timestamp) => {
      if (completedRef.current) return;
      if (!startTimeRef.current) startTimeRef.current = timestamp;

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

      // ═══════════════════════════════════════
      //  CONTINUOUS ENVELOPES
      // ═══════════════════════════════════════

      // Reveal: waveform sweeps L→R
      const reveal = sramp(elapsed, 0.15, 0.7);

      // Initial pulse
      const pulse = sbell(elapsed, 0.4, 0.14);

      // Amplitude: rises, holds, collapses
      const ampRise = sramp(elapsed, 0.3, 1.1);
      const ampFall = 1 - sramp(elapsed, 2.3, 2.85);
      const ampEnv = ampRise * ampFall;

      // Frequency: 2 at rest, peaks at ~9 around t=1.9
      const freqEnv = 2 + 7 * sbell(elapsed, 1.9, 0.7);

      // Harmonics
      const harmEnv = sramp(elapsed, 0.9, 1.5) * (1 - sramp(elapsed, 2.2, 2.7));

      // Chaos/noise
      const noiseEnv = sramp(elapsed, 1.4, 1.9) * (1 - sramp(elapsed, 2.3, 2.7));

      // Ghost CH2
      const ch2Env = sramp(elapsed, 1.1, 1.5) * (1 - sramp(elapsed, 2.2, 2.6));

      // Screen glow
      const glowEnv = sramp(elapsed, 0.5, 1.2) * (1 - sramp(elapsed, 2.4, 2.9));

      // Resonance bursts
      const resonanceGate = sramp(elapsed, 1.0, 1.3) * (1 - sramp(elapsed, 2.2, 2.4));
      const resonancePulse = Math.pow(Math.max(0, Math.sin(elapsed * 8)), 12);
      const resonance = resonanceGate * resonancePulse;

      // ── CRT SHUTDOWN ──
      const vSqueeze = sramp(elapsed, 2.85, 3.0);
      const hSqueeze = sramp(elapsed, 3.0, 3.2);
      const dotPhase = sramp(elapsed, 3.12, 3.22);
      const dotFade  = 1 - sramp(elapsed, 3.22, 3.5);
      const squeezeBright = sbell(elapsed, 3.0, 0.08);

      // Dynamic width
      const energy = ampEnv + noiseEnv * 0.5 + resonance * 0.3;
      const widthScale = 0.8 + energy * 0.8 + squeezeBright * 1.5;

      // Intensity
      const intensity = Math.max(0.08, ampEnv + pulse * 0.5 + resonance * 0.6 + squeezeBright * 2);

      const inDotPhase = dotPhase > 0.9;
      const isDone = elapsed > T_ANIM_END;
      const dotAlmostGone = dotFade < 0.08;

      phaseAccum += dt * freqEnv * 2.5;

      // ── PHOSPHOR PERSISTENCE ──
      ctx.fillStyle = 'rgba(2, 5, 8, 0.82)';
      ctx.fillRect(0, 0, dispW, dispH);

      // Graticule (fades during shutdown)
      const gratAlpha = 1 - sramp(elapsed, 2.9, 3.05);
      if (gratAlpha > 0.01) {
        ctx.globalAlpha = gratAlpha;
        drawGraticule(ctx, dispW, dispH);
        ctx.globalAlpha = 1;
      }

      // ── CRT DOT PHASE ──
      if (inDotPhase) {
        if (dotFade > 0.01) {
          const cx = dispW / 2;
          const cy = dispH / 2;
          const dotSize = 3.5 * dotFade;

          // Outer bloom
          ctx.save();
          ctx.shadowColor = `rgba(0,255,255,${0.8 * dotFade})`;
          ctx.shadowBlur = 80 * dotFade;
          ctx.fillStyle = `rgba(0,255,255,${0.3 * dotFade})`;
          ctx.beginPath();
          ctx.arc(cx, cy, dotSize * 5, 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();

          // Bright dot
          ctx.save();
          ctx.shadowColor = `rgba(0,255,255,${dotFade})`;
          ctx.shadowBlur = 40 * dotFade;
          ctx.fillStyle = `rgba(255,255,255,${0.9 * dotFade})`;
          ctx.beginPath();
          ctx.arc(cx, cy, dotSize, 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();

          // White-hot core
          ctx.save();
          ctx.shadowColor = `rgba(255,255,255,${0.6 * dotFade})`;
          ctx.shadowBlur = 15;
          ctx.fillStyle = `rgba(255,255,255,${dotFade})`;
          ctx.beginPath();
          ctx.arc(cx, cy, Math.max(0.5, dotSize * 0.35), 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();
        }

        if (dotAlmostGone || isDone) {
          finishAnimation();
        }
        animFrameRef.current = requestAnimationFrame(animate);
        return;
      }

      // ── GENERATE WAVEFORMS ──
      // Waveform centered vertically — no clamping, let it fly off-screen
      const numPoints = 600;
      const ch1Points = [];
      const ch2Points = [];
      const waveCY = dispH * 0.52;
      const maxAmp = dispH * 0.38;

      // Horizontal squeeze
      const hExtent = 1 - hSqueeze * 0.97;
      const hStart = 0.5 - hExtent / 2;
      const hEnd = 0.5 + hExtent / 2;

      for (let i = 0; i < numPoints; i++) {
        const xn = i / (numPoints - 1);
        if (xn < hStart || xn > hEnd) continue;

        const maskEdge = reveal * 1.15;
        const mask = smootherstep(Math.min(1, (maskEdge - xn) * 12));
        if (mask < 0.001) continue;

        const x = xn * dispW;

        // Base sine (traveling wave)
        const basePhase = 2 * Math.PI * freqEnv * xn + phaseAccum;
        let signal = Math.sin(basePhase);

        // Harmonics
        signal += harmEnv * 0.35 * Math.sin(basePhase * 2 + elapsed * 1.7);
        signal += harmEnv * 0.18 * Math.sin(basePhase * 3 - elapsed * 0.9);
        signal += harmEnv * 0.08 * Math.sin(basePhase * 5 + elapsed * 2.3);

        // Chaos noise
        const nx = xn * 2 * Math.PI;
        signal += noiseEnv * 0.45 * Math.sin(nx * 15.7 + elapsed * 31.3);
        signal += noiseEnv * 0.30 * Math.sin(nx * 23.1 + elapsed * 47.7);
        signal += noiseEnv * 0.20 * Math.cos(nx * 37.3 + elapsed * 19.1);
        signal += noiseEnv * 0.15 * Math.sin(nx * 53.9 + elapsed * 67.3);
        const spikeRaw = Math.sin(nx * 7.3 + elapsed * 11.7);
        signal += noiseEnv * 0.35 * Math.pow(Math.max(0, spikeRaw), 4);

        // Wave folding
        if (noiseEnv > 0.3) {
          const foldAmt = noiseEnv * 0.6;
          signal = signal * (1 - foldAmt) + softFold(signal) * foldAmt;
        }

        // Apply envelopes
        let yOff = signal * ampEnv * maxAmp;
        yOff -= pulse * maxAmp * 0.55 * Math.exp(-Math.pow((xn - 0.5) * 8, 2));
        yOff *= mask;
        yOff *= (1 - vSqueeze);

        ch1Points.push({ x, y: waveCY + yOff });

        // Ghost CH2 (magenta)
        if (ch2Env > 0.02) {
          const ch2Phase = basePhase + Math.PI / 3;
          let ch2Sig = Math.sin(ch2Phase);
          ch2Sig += harmEnv * 0.2 * Math.sin(ch2Phase * 2 + elapsed * 2.1);
          let ch2Y = ch2Sig * ampEnv * maxAmp * 0.4 * ch2Env * mask * (1 - vSqueeze);
          ch2Points.push({ x, y: waveCY + ch2Y });
        }
      }

      // Draw CH2 behind CH1
      if (ch2Points.length > 1) {
        drawWaveform(ctx, ch2Points, MAGENTA, ch2Env * 0.3, widthScale * 0.6);
      }
      if (ch1Points.length > 1) {
        drawWaveform(ctx, ch1Points, CYAN, intensity, widthScale);
      }

      // ── Second trace: faint teal echo at different y ──
      // A subtle second wave higher up, gives depth
      const echoEnv = sramp(elapsed, 0.8, 1.3) * (1 - sramp(elapsed, 2.0, 2.5));
      if (echoEnv > 0.02) {
        const echoPoints = [];
        const echoCY = dispH * 0.38;
        const echoAmp = dispH * 0.08;
        for (let i = 0; i < numPoints; i += 2) {
          const xn = i / (numPoints - 1);
          if (xn < hStart || xn > hEnd) continue;
          const maskEdge = reveal * 1.15;
          const mask = smootherstep(Math.min(1, (maskEdge - xn) * 12));
          if (mask < 0.001) continue;
          const x = xn * dispW;
          const phase = 2 * Math.PI * (freqEnv * 0.7) * xn + phaseAccum * 0.6 + Math.PI * 0.7;
          let sig = Math.sin(phase) + harmEnv * 0.3 * Math.sin(phase * 2.5 + elapsed);
          let y = echoCY + sig * echoAmp * echoEnv * mask * (1 - vSqueeze);
          echoPoints.push({ x, y });
        }
        if (echoPoints.length > 1) {
          drawWaveform(ctx, echoPoints, TEAL, echoEnv * 0.2, widthScale * 0.4);
        }
      }

      // ── Screen glow ──
      if (glowEnv > 0.01) {
        const gp = 0.7 + 0.3 * Math.sin(elapsed * 5);
        const ga = glowEnv * 0.035 * gp + resonance * 0.025;
        const grad = ctx.createRadialGradient(
          dispW / 2, dispH * 0.52, 0,
          dispW / 2, dispH * 0.52, dispW * 0.55
        );
        grad.addColorStop(0, `rgba(0,255,255,${ga})`);
        grad.addColorStop(0.5, `rgba(0,255,255,${ga * 0.3})`);
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, dispW, dispH);
      }

      // Resonance flash
      if (resonance > 0.3) {
        ctx.fillStyle = `rgba(0,255,255,${resonance * 0.02})`;
        ctx.fillRect(0, 0, dispW, dispH);
      }

      // CRT crush flash
      const crushFlash = sbell(elapsed, 2.93, 0.04);
      if (crushFlash > 0.05) {
        ctx.fillStyle = `rgba(255,255,255,${crushFlash * 0.1})`;
        ctx.fillRect(0, 0, dispW, dispH);
      }

      // Squeeze brightness
      if (squeezeBright > 0.1) {
        ctx.fillStyle = `rgba(0,255,255,${squeezeBright * 0.05})`;
        ctx.fillRect(0, 0, dispW, dispH);
      }

      animFrameRef.current = requestAnimationFrame(animate);
    };

    animFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      window.removeEventListener('resize', resize);
    };
  }, [drawGraticule, drawWaveform, finishAnimation]);

  const titleClasses = `website-launch-title${showText ? ' visible' : ''}${textFadeOut ? ' fade-out-text' : ''}`;
  const subClasses = `website-launch-subtitle${showSubtext ? ' visible' : ''}${textFadeOut ? ' fade-out-text' : ''}`;

  return (
    <div className={`website-launch-overlay ${fadeOut ? 'fade-out' : ''}`} onClick={finishAnimation}>
      <canvas ref={canvasRef} className="website-launch-canvas" />

      <div className="website-launch-content">
        <h1 className={titleClasses}>
          Signals &amp; Systems
        </h1>
        <p className={subClasses}>
          Interactive Learning Platform
        </p>
      </div>

      <div className="website-launch-scanlines" />
      <div className="website-launch-vignette" />

      <div className={`website-launch-skip ${showSubtext ? 'visible' : ''}`}>
        click anywhere to skip
      </div>
    </div>
  );
}

export default WebsiteLaunchAnimation;
