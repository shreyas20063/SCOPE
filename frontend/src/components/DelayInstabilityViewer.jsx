/**
 * DelayInstabilityViewer Component
 *
 * Custom viewer for the "Delay Effect: The Domino of Instability" simulation.
 * Shows three side-by-side robot panels with animated approach to a wall,
 * stem plots, pole-zero map, and a takeaway message.
 */

import React, { useState, useCallback, useEffect, useRef, useMemo } from 'react';
import PlotDisplay from './PlotDisplay';
import '../styles/DelayInstabilityViewer.css';

const DELAY_CASES = [
  { key: 'no_delay', label: 'No Delay', sublabel: 'dₛ[n] = dₒ[n]', color: '#10b981', statusIcon: '●' },
  { key: 'one_step', label: '1-Step Delay', sublabel: 'dₛ[n] = dₒ[n−1]', color: '#f59e0b', statusIcon: '◆' },
  { key: 'two_step', label: '2-Step Delay', sublabel: 'dₛ[n] = dₒ[n−2]', color: '#ef4444', statusIcon: '▲' },
];

/**
 * Single robot panel showing the robot approaching a wall
 */
function RobotPanel({ caseInfo, position, targetDistance, initialDistance, stability, crashed, animStep, isActive }) {
  // Map distance to SVG x-position: wall is at right edge, robot moves left-to-right
  // position = distance to wall. Higher = further from wall (left). 0 = at wall.
  const svgWidth = 280;
  const svgHeight = 100;
  const wallX = svgWidth - 20;
  const groundY = 70;

  // Scale: initial_distance maps to left area, 0 maps to wall
  const maxDist = Math.max(initialDistance * 1.2, Math.abs(position) + 0.5);
  const scale = (wallX - 40) / maxDist;
  const robotX = wallX - position * scale;
  // Clamp robot position to SVG bounds
  const clampedRobotX = Math.max(10, Math.min(wallX + 15, robotX));

  const targetX = wallX - targetDistance * scale;
  const hasCrashed = crashed && isActive;

  return (
    <div className={`di-robot-panel ${stability?.status || ''} ${hasCrashed ? 'crashed' : ''}`}>
      <div className="di-panel-header">
        <span className="di-panel-label" style={{ color: caseInfo.color }}>
          {caseInfo.statusIcon} {caseInfo.label}
        </span>
        <span className={`di-stability-badge ${stability?.status || ''}`}>
          {stability?.label || '—'}
        </span>
      </div>
      <div className="di-panel-equation">
        {caseInfo.sublabel}
      </div>

      <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="di-robot-svg" aria-label={`${caseInfo.label} robot animation`}>
        {/* Ground line */}
        <line x1="5" y1={groundY} x2={svgWidth - 5} y2={groundY}
          stroke="var(--text-muted)" strokeWidth="1" strokeDasharray="4,4" />

        {/* Wall */}
        <rect x={wallX} y={20} width={8} height={groundY - 20}
          fill="var(--text-secondary)" rx="1"
          className={hasCrashed ? 'di-wall-crack' : ''} />

        {/* Target position marker */}
        <line x1={targetX} y1={30} x2={targetX} y2={groundY}
          stroke="#3b82f6" strokeWidth="1.5" strokeDasharray="3,3" opacity="0.6" />
        <text x={targetX} y={25} textAnchor="middle"
          style={{ fontSize: '8px', fill: '#3b82f6', fontFamily: "'Fira Code', monospace" }}>
          target
        </text>

        {/* Robot body */}
        <g transform={`translate(${clampedRobotX - 18}, ${groundY - 22})`}
          className={isActive ? 'di-robot-active' : ''}>
          {/* Body */}
          <rect x="0" y="4" width="28" height="14" rx="3"
            fill={caseInfo.color} opacity="0.9" />
          {/* Sensor antenna */}
          <line x1="24" y1="4" x2="28" y2="-2"
            stroke={caseInfo.color} strokeWidth="1.5" />
          <circle cx="28" cy="-2" r="2" fill={caseInfo.color} />
          {/* Wheels */}
          <circle cx="6" cy="20" r="4" fill="var(--surface-color)"
            stroke={caseInfo.color} strokeWidth="1.5" />
          <circle cx="22" cy="20" r="4" fill="var(--surface-color)"
            stroke={caseInfo.color} strokeWidth="1.5" />
        </g>

        {/* Crash particles */}
        {hasCrashed && (
          <g className="di-particles">
            {[...Array(8)].map((_, i) => (
              <circle
                key={i}
                cx={wallX}
                cy={groundY - 15}
                r="2"
                fill={caseInfo.color}
                className={`di-particle di-particle-${i}`}
              />
            ))}
          </g>
        )}

        {/* Wall crack lines */}
        {hasCrashed && (
          <g className="di-crack-lines">
            <line x1={wallX + 2} y1={35} x2={wallX + 7} y2={30}
              stroke="var(--text-primary)" strokeWidth="1" />
            <line x1={wallX + 2} y1={40} x2={wallX - 3} y2={35}
              stroke="var(--text-primary)" strokeWidth="1" />
            <line x1={wallX + 3} y1={50} x2={wallX + 8} y2={55}
              stroke="var(--text-primary)" strokeWidth="1" />
          </g>
        )}

        {/* Position readout */}
        <text x={svgWidth / 2} y={svgHeight - 5} textAnchor="middle"
          style={{ fontSize: '9px', fill: 'var(--text-secondary)', fontFamily: "'Fira Code', monospace" }}>
          {isActive ? `d = ${position.toFixed(2)} m` : '—'}
        </text>
      </svg>
    </div>
  );
}

/**
 * Info panel showing system equations and KT value
 */
function InfoPanel({ metadata }) {
  if (!metadata) return null;
  const kt = metadata.kt_product;
  const ktDisplay = kt % 1 === 0 ? kt.toFixed(0) : kt.toFixed(2);

  return (
    <div className="di-info-panel">
      <div className="di-equation">
        <span className="di-equation-label">Controller:</span>
        v[n] = K·(d_i − d_s[n])
        <span style={{ color: 'var(--text-muted)', margin: '0 0.5rem' }}>|</span>
        <span className="di-equation-label">Locomotion:</span>
        d_o[n] = d_o[n−1] − T·v[n−1]
      </div>
      <div className="di-kt-display">
        <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>KT =</span>
        <span style={{
          color: kt === -1 ? 'var(--accent-color)' : 'var(--text-primary)',
          fontWeight: 600,
          fontFamily: "'Fira Code', monospace",
        }}>
          {ktDisplay}
        </span>
        {Math.abs(kt + 1) < 0.01 && (
          <span className="di-deadbeat-tag">dead-beat</span>
        )}
      </div>
    </div>
  );
}

/**
 * Animation controls bar
 */
function AnimationControls({ animStep, numSteps, isActive, crashStep, onStepForward, onStepBack, onReset, onPlay, isPlaying, isUpdating }) {
  return (
    <div className="di-controls-bar">
      <div className="di-anim-buttons">
        <button
          className="di-btn"
          onClick={onStepBack}
          disabled={isUpdating || !isActive || animStep <= 0}
          aria-label="Step backward"
        >
          ◀
        </button>
        <button
          className={`di-btn primary ${isPlaying ? 'playing' : ''}`}
          onClick={onPlay}
          disabled={isUpdating || animStep >= numSteps - 1}
          aria-label={isPlaying ? 'Pause' : 'Play animation'}
        >
          {isPlaying ? '⏸ Pause' : '▶ Play'}
        </button>
        <button
          className="di-btn"
          onClick={onStepForward}
          disabled={isUpdating || animStep >= numSteps - 1}
          aria-label="Step forward"
        >
          ▶
        </button>
        <button
          className="di-btn"
          onClick={onReset}
          disabled={isUpdating || !isActive}
          aria-label="Reset animation"
        >
          ↺ Reset
        </button>
      </div>
      <div className="di-step-info">
        <span className="di-step-counter">
          n = {isActive ? animStep : '—'} / {numSteps - 1}
        </span>
        {crashStep != null && (
          <span className="di-crash-counter" aria-live="polite">
            Steps to crash: <strong>{crashStep}</strong>
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * Takeaway text that fades in after crash
 */
function TakeawayText({ visible }) {
  if (!visible) return null;

  return (
    <div className="di-takeaway" role="alert" aria-live="polite">
      <div className="di-takeaway-icon">💡</div>
      <p className="di-takeaway-text">
        Adding one sample of sensor delay converted a perfect 1-step controller into a
        system that <strong>never settles</strong>. Adding two samples made it{' '}
        <strong>explode</strong>. In real systems (aircraft, robots, power grids),
        latency kills controllers. This is why 5G matters for autonomous vehicles.
      </p>
    </div>
  );
}

/**
 * Main DelayInstabilityViewer component
 */
function DelayInstabilityViewer({ metadata, plots, onButtonClick, isUpdating }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const playIntervalRef = useRef(null);
  const prevFingerprintRef = useRef('');

  const animStep = metadata?.animation_step ?? 0;
  const isActive = metadata?.animation_active ?? false;
  const numSteps = metadata?.num_steps ?? 25;
  const crashStep = metadata?.crash_step ?? null;
  const positions = metadata?.positions ?? {};
  const stability = metadata?.stability ?? {};
  const targetDist = metadata?.target_distance ?? 1.0;
  const initialDist = metadata?.initial_distance ?? 2.0;
  const kt = metadata?.kt_product ?? -1;

  // System fingerprint for cleanup
  const fingerprint = `${kt}-${initialDist}-${targetDist}-${numSteps}`;
  useEffect(() => {
    if (prevFingerprintRef.current && prevFingerprintRef.current !== fingerprint) {
      setIsPlaying(false);
      if (playIntervalRef.current) {
        clearInterval(playIntervalRef.current);
        playIntervalRef.current = null;
      }
    }
    prevFingerprintRef.current = fingerprint;
  }, [fingerprint]);

  // Determine playback interval from speed setting
  const playbackSpeed = useMemo(() => {
    const speed = metadata?.playback_speed || 'normal';
    if (speed === 'slow') return 800;
    if (speed === 'fast') return 200;
    return 450; // normal
  }, [metadata?.playback_speed]);

  // Auto-play interval
  useEffect(() => {
    if (isPlaying) {
      playIntervalRef.current = setInterval(() => {
        if (onButtonClick) onButtonClick('step_forward', {});
      }, playbackSpeed);
    } else {
      if (playIntervalRef.current) {
        clearInterval(playIntervalRef.current);
        playIntervalRef.current = null;
      }
    }
    return () => {
      if (playIntervalRef.current) clearInterval(playIntervalRef.current);
    };
  }, [isPlaying, playbackSpeed, onButtonClick]);

  // Stop playing when we reach the end
  useEffect(() => {
    if (animStep >= numSteps - 1) {
      setIsPlaying(false);
    }
  }, [animStep, numSteps]);

  const handleStepForward = useCallback(() => {
    if (onButtonClick) onButtonClick('step_forward', {});
  }, [onButtonClick]);

  const handleStepBack = useCallback(() => {
    if (onButtonClick) onButtonClick('step_backward', {});
  }, [onButtonClick]);

  const handleReset = useCallback(() => {
    setIsPlaying(false);
    if (onButtonClick) onButtonClick('reset_animation', {});
  }, [onButtonClick]);

  const handlePlay = useCallback(() => {
    if (animStep >= numSteps - 1) {
      // At end, reset first then play
      if (onButtonClick) onButtonClick('reset_animation', {});
      setTimeout(() => setIsPlaying(true), 100);
    } else {
      setIsPlaying(prev => !prev);
    }
  }, [animStep, numSteps, onButtonClick]);

  // Show takeaway when 2-step delay robot has crashed and animation is past crash point
  const showTakeaway = isActive && crashStep != null && animStep >= crashStep;

  // Get current positions for robot panels
  const getCurrentPos = useCallback((key) => {
    const posArr = positions[key];
    if (!posArr || !isActive) return initialDist;
    const idx = Math.min(animStep, posArr.length - 1);
    return posArr[idx];
  }, [positions, isActive, animStep, initialDist]);

  // Determine if 2-step delay robot has crashed at current step
  const twoStepCrashed = isActive && crashStep != null && animStep >= crashStep;

  return (
    <div className="delay-instability-viewer">
      {/* Info Panel */}
      <InfoPanel metadata={metadata} />

      {/* Three robot panels */}
      <div className="di-robots-container">
        {DELAY_CASES.map((caseInfo) => (
          <RobotPanel
            key={caseInfo.key}
            caseInfo={caseInfo}
            position={getCurrentPos(caseInfo.key)}
            targetDistance={targetDist}
            initialDistance={initialDist}
            stability={stability[caseInfo.key]}
            crashed={caseInfo.key === 'two_step' && twoStepCrashed}
            animStep={animStep}
            isActive={isActive}
          />
        ))}
      </div>

      {/* Animation Controls */}
      <AnimationControls
        animStep={animStep}
        numSteps={numSteps}
        isActive={isActive}
        crashStep={crashStep}
        onStepForward={handleStepForward}
        onStepBack={handleStepBack}
        onReset={handleReset}
        onPlay={handlePlay}
        isPlaying={isPlaying}
        isUpdating={isUpdating}
      />

      {/* Takeaway Text */}
      <TakeawayText visible={showTakeaway} />

      {/* Plots */}
      <PlotDisplay
        plots={plots}
        isLoading={false}
        emptyMessage="Adjust parameters to generate plots."
      />
    </div>
  );
}

export default DelayInstabilityViewer;
