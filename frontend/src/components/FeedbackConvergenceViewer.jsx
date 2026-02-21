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
  const [pulseClass, setPulseClass] = useState('');
  const prevStepRef = useRef(0);

  // Trigger pulse animation when animation_step changes
  useEffect(() => {
    if (animationActive && animationStep > prevStepRef.current) {
      if (animationStep === 1) {
        setPulseClass('active path-input');
      } else {
        setPulseClass('active path-loop');
      }
      const timer = setTimeout(() => setPulseClass(''), 1300);
      prevStepRef.current = animationStep;
      return () => clearTimeout(timer);
    }
    if (!animationActive) {
      prevStepRef.current = 0;
      setPulseClass('');
    }
  }, [animationStep, animationActive]);

  const statusColor = convergence === 'converging' ? '#10b981'
    : convergence === 'diverging' ? '#ef4444'
    : '#f59e0b';

  const p0Display = p0 % 1 === 0 ? p0.toFixed(0) : p0.toFixed(2);

  return (
    <div className="fc-svg-container">
      <svg viewBox="0 0 300 130" width="300" height="130" aria-label="Feedback loop block diagram">
        {/* Arrow markers */}
        <defs>
          <marker id="fc-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" className="arrow-head" />
          </marker>
        </defs>

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

        {/* Arrow from Y-down into Delay */}
        <line x1="245" y1="94" x2="245" y2="94" className="arrow-line" />

        {/* Feedback path: Delay → p₀ gain */}
        <line x1="195" y1="94" x2="145" y2="94" className="arrow-line" markerEnd="url(#fc-arrow)" />

        {/* p₀ Gain block (triangle/trapezoid) */}
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

        {/* Signal pulse dot */}
        <circle className={`fc-signal-pulse ${pulseClass}`} cx="20" cy="50" />
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
 * Main FeedbackConvergenceViewer component
 */
function FeedbackConvergenceViewer({ metadata, plots, onButtonClick, isUpdating }) {
  const handleAnimateCycle = useCallback(() => {
    if (onButtonClick) onButtonClick('animate_cycles', {});
  }, [onButtonClick]);

  const handleResetAnimation = useCallback(() => {
    if (onButtonClick) onButtonClick('reset_animation', {});
  }, [onButtonClick]);

  const handleStepBack = useCallback(() => {
    if (onButtonClick) onButtonClick('step_backward', {});
  }, [onButtonClick]);

  const p0 = metadata?.p0 ?? 0.5;
  const convergence = metadata?.convergence ?? 'converging';
  const animationStep = metadata?.animation_step ?? 0;
  const animationActive = metadata?.animation_active ?? false;
  const numSamples = metadata?.num_samples ?? 15;

  return (
    <div className="feedback-convergence-viewer">
      {/* Info Panel */}
      <InfoPanel metadata={metadata} />

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
              disabled={isUpdating || !animationActive || animationStep <= 0}
              aria-label="Step backward"
            >
              ◀
            </button>
            <button
              className="fc-animate-btn primary"
              onClick={handleAnimateCycle}
              disabled={isUpdating}
              aria-label="Animate one cycle"
            >
              ▶ Cycle
            </button>
            <span className="fc-step-counter">
              {animationActive ? `${animationStep} / ${numSamples}` : '— / —'}
            </span>
            <button
              className="fc-animate-btn"
              onClick={handleResetAnimation}
              disabled={isUpdating || !animationActive}
              aria-label="Reset animation"
            >
              ↺ Reset
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
