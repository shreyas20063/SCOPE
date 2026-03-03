/**
 * FeedbackConvergenceViewer Component
 *
 * Custom viewer for the Feedback & Convergence Explorer simulation.
 * Renders an SVG block diagram with animated signal path tracing,
 * info panel with convergence status, and Plotly stem plots.
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import PlotDisplay from './PlotDisplay';
import '../styles/FeedbackConvergenceViewer.css';

/**
 * SVG Block Diagram: X → (+) → Y with feedback Y → Delay → p₀ → (+)
 */
function BlockDiagram({ p0, convergence, animationStep, animationActive }) {
  const [pathMode, setPathMode] = useState(''); // 'forward' | 'loop' | ''
  const prevStepRef = useRef(0);

  // Trigger path highlight + pulse when animation_step changes
  useEffect(() => {
    if (animationActive && animationStep > prevStepRef.current) {
      const mode = animationStep === 1 ? 'forward' : 'loop';
      setPathMode(mode);
      const timer = setTimeout(() => setPathMode(''), 1400);
      prevStepRef.current = animationStep;
      return () => clearTimeout(timer);
    }
    // Also handle loopback (step went from num_samples back to 1)
    if (animationActive && animationStep === 1 && prevStepRef.current > 1) {
      setPathMode('loop');
      const timer = setTimeout(() => setPathMode(''), 1400);
      prevStepRef.current = animationStep;
      return () => clearTimeout(timer);
    }
    if (!animationActive) {
      prevStepRef.current = 0;
      setPathMode('');
    }
  }, [animationStep, animationActive]);

  const statusColor = convergence === 'converging' ? '#10b981'
    : convergence === 'diverging' ? '#ef4444'
    : '#f59e0b';

  const p0Display = p0 % 1 === 0 ? p0.toFixed(0) : p0.toFixed(2);
  const isForward = pathMode === 'forward';
  const isLoop = pathMode === 'loop';

  return (
    <div className="fc-svg-container">
      <svg viewBox="0 0 300 130" width="300" height="130" aria-label="Feedback loop block diagram">
        {/* Defs: arrow markers + glow filter */}
        <defs>
          <marker id="fc-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" className="arrow-head" />
          </marker>
          <marker id="fc-arrow-glow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill={statusColor} />
          </marker>
          <filter id="fc-glow">
            <feGaussianBlur stdDeviation="2.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* ── Base diagram lines (always visible, dim) ── */}

        {/* Input X label */}
        <text x="8" y="54" className="signal-label">X</text>

        {/* Input arrow → Adder */}
        <line x1="24" y1="50" x2="50" y2="50" className="arrow-line" markerEnd="url(#fc-arrow)" />

        {/* Adder circle (⊕) */}
        <circle cx="62" cy="50" r="11" className="adder-circle" />
        <line x1="56" y1="50" x2="68" y2="50" stroke="var(--primary-color)" strokeWidth="1.5" />
        <line x1="62" y1="44" x2="62" y2="56" stroke="var(--primary-color)" strokeWidth="1.5" />

        {/* Adder → Output Y */}
        <line x1="73" y1="50" x2="260" y2="50" className="arrow-line" markerEnd="url(#fc-arrow)" />

        {/* Output Y label */}
        <text x="270" y="54" className="signal-label">Y</text>

        {/* Y node down to feedback path */}
        <line x1="240" y1="50" x2="240" y2="95" className="arrow-line" />

        {/* Delay block */}
        <rect x="195" y="80" width="50" height="28" className="block-rect" />
        <text x="220" y="98" textAnchor="middle" className="block-label">Delay</text>

        {/* Feedback path: Delay → p₀ gain */}
        <line x1="195" y1="94" x2="145" y2="94" className="arrow-line" markerEnd="url(#fc-arrow)" />

        {/* p₀ Gain block (triangle) */}
        <polygon points="135,82 100,94 135,106" className="gain-triangle" />
        <text x="122" y="98" textAnchor="middle"
          style={{ fontSize: '11px', fontFamily: "'Fira Code', monospace", fill: statusColor, fontWeight: 600 }}>
          p₀
        </text>

        {/* p₀ value annotation */}
        <text x="118" y="118" textAnchor="middle"
          style={{ fontSize: '9px', fontFamily: "'Fira Code', monospace", fill: statusColor, opacity: 0.8 }}>
          ={p0Display}
        </text>

        {/* Gain → Adder feedback */}
        <line x1="100" y1="94" x2="62" y2="94" className="arrow-line" />
        <line x1="62" y1="94" x2="62" y2="61" className="arrow-line" markerEnd="url(#fc-arrow)" />

        {/* ── Glow overlay: Forward path (X → Adder → Y) ── */}
        <g className={`fc-path-overlay${isForward ? ' active' : ''}`} filter="url(#fc-glow)">
          <line x1="24" y1="50" x2="50" y2="50" stroke={statusColor} strokeWidth="3" markerEnd="url(#fc-arrow-glow)" />
          <line x1="73" y1="50" x2="260" y2="50" stroke={statusColor} strokeWidth="3" markerEnd="url(#fc-arrow-glow)" />
        </g>

        {/* ── Glow overlay: Feedback loop (Y → Delay → p₀ → Adder) ── */}
        <g className={`fc-path-overlay${isLoop ? ' active' : ''}`} filter="url(#fc-glow)">
          {/* Y down to feedback rail */}
          <line x1="240" y1="50" x2="240" y2="95" stroke={statusColor} strokeWidth="3" />
          {/* Through Delay */}
          <line x1="245" y1="94" x2="195" y2="94" stroke={statusColor} strokeWidth="3" />
          {/* Delay → Gain */}
          <line x1="195" y1="94" x2="145" y2="94" stroke={statusColor} strokeWidth="3" markerEnd="url(#fc-arrow-glow)" />
          {/* Gain → Adder up */}
          <line x1="100" y1="94" x2="62" y2="94" stroke={statusColor} strokeWidth="3" />
          <line x1="62" y1="94" x2="62" y2="61" stroke={statusColor} strokeWidth="3" markerEnd="url(#fc-arrow-glow)" />
          {/* Then through adder to output */}
          <line x1="73" y1="50" x2="260" y2="50" stroke={statusColor} strokeWidth="3" markerEnd="url(#fc-arrow-glow)" />
        </g>

        {/* Signal pulse dot */}
        <circle
          className={`fc-signal-pulse${isForward ? ' active path-input' : isLoop ? ' active path-loop' : ''}`}
          cx="20" cy="50"
        />
      </svg>
    </div>
  );
}

/**
 * Info panel showing convergence status and equation
 */
function InfoPanel({ metadata }) {
  if (!metadata) return null;

  const { p0, convergence, abs_p0, geometric_sum_limit, animation_step, animation_active } = metadata;
  const p0Display = p0 % 1 === 0 ? p0.toFixed(0) : p0.toFixed(2);

  const statusLabels = {
    converging: 'Converging',
    diverging: 'Diverging',
    marginal: 'Marginal',
  };

  // Current sample value
  let currentVal = '';
  if (animation_active && animation_step > 0) {
    const val = Math.pow(p0, animation_step - 1);
    currentVal = ` = ${Math.abs(val) < 0.001 && val !== 0 ? val.toExponential(2) : val.toFixed(4)}`;
  }

  return (
    <div className="fc-info-panel">
      <div className="fc-equation">
        <span className="fc-equation-label">System:</span>
        y[n] = x[n] + p₀·y[n-1]
        <span style={{ color: 'var(--text-muted)', margin: '0 0.3rem' }}>→</span>
        <span style={{ color: 'var(--accent-color)' }}>
          y[n] = ({p0Display})ⁿ{currentVal}
        </span>
      </div>
      <div className="fc-status-group">
        <span className={`fc-status-badge ${convergence}`} role="status" aria-live="polite">
          <span style={{ fontSize: '0.65rem' }}>
            {convergence === 'converging' ? '●' : convergence === 'diverging' ? '▲' : '◆'}
          </span>
          {statusLabels[convergence] || convergence}
        </span>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: "'Fira Code', monospace" }}>
          |p₀| = {abs_p0.toFixed(2)}
        </span>
        {geometric_sum_limit != null && (
          <span className="fc-sum-info">
            Σ → {geometric_sum_limit.toFixed(3)}
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * Cycle description text during animation
 */
function CycleDescription({ metadata }) {
  if (!metadata?.animation_active || metadata.animation_step === 0) return null;

  const step = metadata.animation_step;
  const p0 = metadata.p0;
  const p0Display = p0 % 1 === 0 ? p0.toFixed(0) : p0.toFixed(2);

  let description;
  if (step === 1) {
    description = (
      <>
        <span className="highlight">Cycle 1:</span> Input impulse δ[0] = 1 enters the adder → output y[0] = <span className="highlight">1</span>
      </>
    );
  } else {
    const prevVal = Math.pow(p0, step - 2);
    const newVal = Math.pow(p0, step - 1);
    const prevDisplay = Math.abs(prevVal) < 0.001 ? prevVal.toExponential(2) : prevVal.toFixed(3);
    const newDisplay = Math.abs(newVal) < 0.001 ? newVal.toExponential(2) : newVal.toFixed(3);
    description = (
      <>
        <span className="highlight">Cycle {step}:</span> y[{step - 2}] = {prevDisplay} → Delay → × p₀ = × {p0Display} → Adder → y[{step - 1}] = <span className="highlight">{newDisplay}</span>
      </>
    );
  }

  return (
    <div className="fc-cycle-description" aria-live="polite">
      {description}
    </div>
  );
}

/**
 * Preset selector for common p₀ values
 */
function PresetSelector({ presets, currentP0, onApplyPreset, isUpdating }) {
  if (!presets || presets.length === 0) return null;

  return (
    <div className="fc-presets">
      <span className="fc-presets-label">Presets:</span>
      <div className="fc-presets-list">
        {presets.map((preset, i) => {
          const isActive = Math.abs(currentP0 - preset.params.p0) < 0.005;
          return (
            <button
              key={i}
              className={`fc-preset-btn${isActive ? ' active' : ''}`}
              onClick={() => onApplyPreset(preset.params)}
              disabled={isUpdating}
              title={preset.label}
            >
              {preset.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Main FeedbackConvergenceViewer component
 */
function FeedbackConvergenceViewer({ metadata, plots, onButtonClick, isUpdating, isRunning }) {
  const handlePlayPause = useCallback(() => {
    if (onButtonClick) onButtonClick('play_pause', {});
  }, [onButtonClick]);

  const handleStepForward = useCallback(() => {
    if (onButtonClick) onButtonClick('step_forward', {});
  }, [onButtonClick]);

  const handleStepBack = useCallback(() => {
    if (onButtonClick) onButtonClick('step_backward', {});
  }, [onButtonClick]);

  const handleResetAnimation = useCallback(() => {
    if (onButtonClick) onButtonClick('reset_animation', {});
  }, [onButtonClick]);

  const handleApplyPreset = useCallback((params) => {
    if (onButtonClick) onButtonClick('apply_preset', params);
  }, [onButtonClick]);

  const p0 = metadata?.p0 ?? 0.5;
  const convergence = metadata?.convergence ?? 'converging';
  const animationStep = metadata?.animation_step ?? 0;
  const animationActive = metadata?.animation_active ?? false;
  const numSamples = metadata?.num_samples ?? 15;
  const presets = metadata?.presets ?? [];

  return (
    <div className="feedback-convergence-viewer">
      {/* Info Panel */}
      <InfoPanel metadata={metadata} />

      {/* Preset Selector */}
      <PresetSelector
        presets={presets}
        currentP0={p0}
        onApplyPreset={handleApplyPreset}
        isUpdating={isUpdating}
      />

      {/* Block Diagram Section */}
      <div className="fc-block-diagram-section">
        <div className="fc-diagram-header">
          <span className="fc-diagram-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
              <path d="M3 9h18M9 3v18" />
            </svg>
            Feedback Loop Block Diagram
          </span>
          <div className="fc-animation-controls">
            <button
              className="fc-animate-btn"
              onClick={handleStepBack}
              disabled={isUpdating || isRunning || animationStep <= 0}
              aria-label="Step backward"
              title="Step backward"
            >
              ◀
            </button>
            <button
              className={`fc-animate-btn primary${isRunning ? ' running' : ''}`}
              onClick={handlePlayPause}
              disabled={isUpdating && !isRunning}
              aria-label={isRunning ? 'Pause animation' : 'Play animation'}
              title={isRunning ? 'Pause' : 'Auto-play all cycles'}
            >
              {isRunning ? '⏸ Pause' : '▶ Play'}
            </button>
            <button
              className="fc-animate-btn"
              onClick={handleStepForward}
              disabled={isUpdating || isRunning || animationStep >= numSamples}
              aria-label="Step forward"
              title="Step forward one cycle"
            >
              ▶▏
            </button>
            <span className="fc-step-counter">
              {animationActive || isRunning ? `${animationStep} / ${numSamples}` : '— / —'}
            </span>
            <button
              className="fc-animate-btn"
              onClick={handleResetAnimation}
              disabled={isUpdating || (!animationActive && !isRunning)}
              aria-label="Reset animation"
              title="Reset to start"
            >
              ↺
            </button>
          </div>
        </div>

        <BlockDiagram
          p0={p0}
          convergence={convergence}
          animationStep={animationStep}
          animationActive={animationActive}
        />

        <CycleDescription metadata={metadata} />
      </div>

      {/* Plots */}
      <PlotDisplay
        plots={plots}
        isLoading={false}
        emptyMessage="Adjust p₀ to generate plots."
      />
    </div>
  );
}

export default FeedbackConvergenceViewer;
