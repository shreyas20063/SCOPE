/**
 * DifferenceEquationViewer
 *
 * Custom viewer for the DT Difference Equation Step-by-Step Solver.
 * Renders:
 * - Step controls (forward, back, reset, play/pause)
 * - Equation substitution panel with highlighted current step
 * - SVG block diagram with wire values
 * - Growing stem plots for x[n] and y[n]
 */

import React, { useCallback, useMemo, useRef, useEffect } from 'react';
import PlotDisplay from './PlotDisplay';
import '../styles/DifferenceEquationViewer.css';

// ============================================================
// Value formatting helper
// ============================================================
function fmtVal(v) {
  if (v === undefined || v === null) return '0';
  if (Number.isInteger(v) || v === Math.floor(v)) return String(Math.round(v));
  return v.toFixed(3).replace(/0+$/, '').replace(/\.$/, '');
}

// ============================================================
// SVG Block Diagram Components
// ============================================================

/** Arrowhead marker definition */
function ArrowDefs() {
  return (
    <defs>
      <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
        <polygon points="0 0, 8 3, 0 6" className="arrowhead" />
      </marker>
      <marker id="arrowhead-active" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
        <polygon points="0 0, 8 3, 0 6" className="arrowhead--active" />
      </marker>
    </defs>
  );
}

/** Wire value badge (number on a wire) */
function WireValue({ x, y, value, type = 'internal' }) {
  const text = fmtVal(value);
  const w = Math.max(28, text.length * 8 + 12);
  return (
    <g>
      <rect className="wire-value-bg" x={x - w / 2} y={y - 10} width={w} height={20} />
      <text className={`wire-value wire-value--${type}`} x={x} y={y}>{text}</text>
    </g>
  );
}

/** Gain block (triangle) */
function GainBlock({ x, y, label, size = 30 }) {
  const half = size / 2;
  const points = `${x - half},${y - half} ${x + half},${y} ${x - half},${y + half}`;
  return (
    <g>
      <polygon points={points} className="block block--gain" />
      <text className="block-label" x={x - 3} y={y}>{label}</text>
    </g>
  );
}

/** Delay block (rectangle) */
function DelayBlock({ x, y, width = 56, height = 30 }) {
  return (
    <g>
      <rect className="block block--delay" x={x - width / 2} y={y - height / 2} width={width} height={height} rx="4" />
      <text className="block-label" x={x} y={y}>Delay</text>
    </g>
  );
}

/** Adder block (circle with +) */
function AdderBlock({ x, y, r = 16 }) {
  return (
    <g>
      <circle className="block block--adder" cx={x} cy={y} r={r} />
      <text className="block-label" x={x} y={y} style={{ fontSize: '16px', fontWeight: 700 }}>+</text>
    </g>
  );
}

/** Wire line with optional arrow */
function Wire({ points, arrow = true }) {
  const d = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0]},${p[1]}`).join(' ');
  return (
    <path
      className="wire"
      d={d}
      markerEnd={arrow ? 'url(#arrowhead)' : undefined}
    />
  );
}

/** Signal label (x[n] or y[n]) */
function SignalLabel({ x, y, text }) {
  return <text className="signal-label" x={x} y={y}>{text}</text>;
}

// ============================================================
// Diagram Layouts (one per preset)
// ============================================================

/**
 * Difference Machine: y[n] = x[n] - x[n-1]
 *
 *  x[n] ────────────────────→ (+) ──→ y[n]
 *    │                         ↑
 *    └──→ [×(-1)] ──→ [Delay] ─┘
 */
function DifferenceMachineDiagram({ wireValues }) {
  const w = wireValues || {};
  return (
    <svg className="diff-eq-diagram-svg" viewBox="0 0 440 170" preserveAspectRatio="xMidYMid meet">
      <ArrowDefs />
      {/* Wires */}
      {/* x[n] → adder (top path) */}
      <Wire points={[[60, 45], [300, 45]]} />
      {/* x[n] → gain (fork down) */}
      <Wire points={[[80, 45], [80, 120]]} arrow={false} />
      <Wire points={[[80, 120], [130, 120]]} />
      {/* gain → delay */}
      <Wire points={[[160, 120], [220, 120]]} />
      {/* delay → adder (up) */}
      <Wire points={[[250, 120], [316, 120]]} arrow={false} />
      <Wire points={[[316, 120], [316, 61]]} />

      {/* Blocks */}
      <GainBlock x={145} y={120} label="×(−1)" size={30} />
      <DelayBlock x={235} y={120} />
      <AdderBlock x={316} y={45} />

      {/* Labels */}
      <SignalLabel x={15} y={49} text="x[n]" />
      <SignalLabel x={370} y={49} text="y[n]" />

      {/* Output arrow from adder */}
      <Wire points={[[332, 45], [365, 45]]} />

      {/* Wire values */}
      <WireValue x={180} y={45} value={w.x_in} type="input" />
      <WireValue x={145} y={98} value={w.gain_out} type="internal" />
      <WireValue x={290} y={120} value={w.delay_out} type="internal" />
      <WireValue x={385} y={45} value={w.adder_out} type="output" />

      {/* Fork dot */}
      <circle cx={80} cy={45} r={3} fill="var(--text-muted)" />
    </svg>
  );
}

/**
 * Accumulator: y[n] = x[n] + y[n-1]
 *
 *  x[n] ──→ (+) ──→ y[n]
 *             ↑
 *             └── [Delay] ←─┘
 */
function AccumulatorDiagram({ wireValues }) {
  const w = wireValues || {};
  return (
    <svg className="diff-eq-diagram-svg" viewBox="0 0 440 170" preserveAspectRatio="xMidYMid meet">
      <ArrowDefs />
      {/* x[n] → adder */}
      <Wire points={[[60, 45], [184, 45]]} />
      {/* adder → y[n] */}
      <Wire points={[[216, 45], [365, 45]]} />
      {/* Fork down from output */}
      <Wire points={[[320, 45], [320, 120]]} arrow={false} />
      {/* to delay */}
      <Wire points={[[320, 120], [260, 120]]} />
      {/* delay → back up to adder */}
      <Wire points={[[225, 120], [200, 120]]} arrow={false} />
      <Wire points={[[200, 120], [200, 61]]} />

      {/* Blocks */}
      <AdderBlock x={200} y={45} />
      <DelayBlock x={243} y={120} />

      {/* Labels */}
      <SignalLabel x={15} y={49} text="x[n]" />
      <SignalLabel x={375} y={49} text="y[n]" />

      {/* Wire values */}
      <WireValue x={120} y={45} value={w.x_in} type="input" />
      <WireValue x={290} y={45} value={w.adder_out} type="output" />
      <WireValue x={200} y={145} value={w.delay_out} type="internal" />

      {/* Fork dot */}
      <circle cx={320} cy={45} r={3} fill="var(--text-muted)" />
    </svg>
  );
}

/**
 * Moving Average: y[n] = (x[n] + x[n-1]) / 2
 *
 *  x[n] ──→ [×0.5] ──────→ (+) ──→ y[n]
 *    │                       ↑
 *    └──→ [Delay] ──→ [×0.5] ┘
 */
function MovingAverageDiagram({ wireValues }) {
  const w = wireValues || {};
  return (
    <svg className="diff-eq-diagram-svg" viewBox="0 0 440 170" preserveAspectRatio="xMidYMid meet">
      <ArrowDefs />
      {/* Top path: x → gain0.5 → adder */}
      <Wire points={[[60, 45], [115, 45]]} />
      <Wire points={[[145, 45], [290, 45]]} />
      {/* Fork down */}
      <Wire points={[[80, 45], [80, 120]]} arrow={false} />
      {/* Bottom path: x → delay → gain0.5 → adder */}
      <Wire points={[[80, 120], [145, 120]]} />
      <Wire points={[[175, 120], [230, 120]]} />
      <Wire points={[[260, 120], [306, 120]]} arrow={false} />
      <Wire points={[[306, 120], [306, 61]]} />

      {/* Blocks */}
      <GainBlock x={130} y={45} label="×0.5" size={28} />
      <DelayBlock x={160} y={120} />
      <GainBlock x={245} y={120} label="×0.5" size={28} />
      <AdderBlock x={306} y={45} />

      {/* adder → output */}
      <Wire points={[[322, 45], [365, 45]]} />

      {/* Labels */}
      <SignalLabel x={15} y={49} text="x[n]" />
      <SignalLabel x={375} y={49} text="y[n]" />

      {/* Wire values */}
      <WireValue x={90} y={25} value={w.x_in} type="input" />
      <WireValue x={220} y={45} value={w.gain1_out} type="internal" />
      <WireValue x={205} y={120} value={w.delay_out} type="internal" />
      <WireValue x={290} y={120} value={w.gain2_out} type="internal" />
      <WireValue x={385} y={45} value={w.adder_out} type="output" />

      {/* Fork dot */}
      <circle cx={80} cy={45} r={3} fill="var(--text-muted)" />
    </svg>
  );
}

/**
 * Leaky Integrator: y[n] = 0.9·y[n-1] + 0.1·x[n]
 *
 *  x[n] ──→ [×0.1] ──→ (+) ──→ y[n]
 *                        ↑
 *                        └── [×0.9] ←── [Delay] ←─┘
 */
function LeakyIntegratorDiagram({ wireValues }) {
  const w = wireValues || {};
  return (
    <svg className="diff-eq-diagram-svg" viewBox="0 0 440 170" preserveAspectRatio="xMidYMid meet">
      <ArrowDefs />
      {/* x[n] → gain(0.1) */}
      <Wire points={[[60, 45], [115, 45]]} />
      {/* gain(0.1) → adder */}
      <Wire points={[[145, 45], [224, 45]]} />
      {/* adder → y[n] output */}
      <Wire points={[[256, 45], [365, 45]]} />

      {/* Feedback path: fork down from output wire */}
      <Wire points={[[320, 45], [320, 120]]} arrow={false} />
      {/* → delay (right to left flow in feedback) */}
      <Wire points={[[320, 120], [315, 120]]} />
      {/* delay → gain(0.9) */}
      <Wire points={[[255, 120], [192, 120]]} />
      {/* gain(0.9) → up to adder */}
      <Wire points={[[158, 120], [158, 85]]} arrow={false} />
      <Wire points={[[158, 85], [240, 85]]} arrow={false} />
      <Wire points={[[240, 85], [240, 61]]} />

      {/* Blocks */}
      <GainBlock x={130} y={45} label="×0.1" size={28} />
      <AdderBlock x={240} y={45} />
      <DelayBlock x={285} y={120} />
      <GainBlock x={175} y={120} label="×0.9" size={28} />

      {/* Labels */}
      <SignalLabel x={15} y={49} text="x[n]" />
      <SignalLabel x={375} y={49} text="y[n]" />

      {/* Wire values */}
      <WireValue x={90} y={25} value={w.x_in} type="input" />
      <WireValue x={185} y={45} value={w.gain_x_out} type="internal" />
      <WireValue x={340} y={80} value={w.delay_out} type="internal" />
      <WireValue x={120} y={100} value={w.gain_fb_out} type="internal" />
      <WireValue x={385} y={45} value={w.adder_out} type="output" />

      {/* Fork dot */}
      <circle cx={320} cy={45} r={3} fill="var(--text-muted)" />
    </svg>
  );
}

// Map diagram type to component
const DIAGRAM_COMPONENTS = {
  difference_machine: DifferenceMachineDiagram,
  accumulator: AccumulatorDiagram,
  moving_average: MovingAverageDiagram,
  leaky_integrator: LeakyIntegratorDiagram,
};

// ============================================================
// Main Viewer Component
// ============================================================

export default function DifferenceEquationViewer({ metadata, plots, onButtonClick, isUpdating }) {
  const stepsEndRef = useRef(null);

  const currentN = metadata?.current_n ?? -3;
  const isAtRest = metadata?.is_at_rest ?? true;
  const canStepBack = metadata?.can_step_back ?? false;
  const canStepForward = metadata?.can_step_forward ?? true;
  const equationText = metadata?.equation_text ?? '';
  const diagramType = metadata?.diagram_type ?? 'difference_machine';
  const wireValues = metadata?.wire_values ?? {};
  const substitutionHistory = metadata?.substitution_history ?? [];
  const inputSignalType = metadata?.input_signal_type ?? 'impulse';

  // Input signal display name
  const inputLabel = useMemo(() => {
    const labels = { impulse: 'x[n] = \u03b4[n]', step: 'x[n] = u[n]', ramp: 'x[n] = n\u00b7u[n]' };
    return labels[inputSignalType] || inputSignalType;
  }, [inputSignalType]);

  // Auto-scroll equation panel to bottom on new step
  useEffect(() => {
    if (stepsEndRef.current) {
      stepsEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [substitutionHistory.length]);

  // Button handlers
  const handleStepForward = useCallback(() => {
    onButtonClick?.('step_forward');
  }, [onButtonClick]);

  const handleStepBackward = useCallback(() => {
    onButtonClick?.('step_backward');
  }, [onButtonClick]);

  const handleReset = useCallback(() => {
    onButtonClick?.('reset');
  }, [onButtonClick]);

  const handlePlayPause = useCallback(() => {
    onButtonClick?.('play_pause');
  }, [onButtonClick]);

  // Get the right diagram component
  const DiagramComponent = DIAGRAM_COMPONENTS[diagramType] || DifferenceMachineDiagram;

  // Split plots for the two stem plot areas
  const inputPlot = plots?.find(p => p.id === 'input_signal');
  const outputPlot = plots?.find(p => p.id === 'output_signal');

  return (
    <div className="diff-eq-viewer">
      {/* Step Controls */}
      <div className="diff-eq-controls" role="toolbar" aria-label="Step controls">
        <button
          className="diff-eq-controls__btn"
          onClick={handleReset}
          disabled={isUpdating || isAtRest}
          aria-label="Reset to start"
          title="Reset"
        >
          &#x21BA; Reset
        </button>
        <button
          className="diff-eq-controls__btn"
          onClick={handleStepBackward}
          disabled={isUpdating || !canStepBack}
          aria-label="Step backward"
          title="Step Back"
        >
          &#x25C0; Back
        </button>
        <button
          className="diff-eq-controls__btn diff-eq-controls__btn--primary"
          onClick={handleStepForward}
          disabled={isUpdating || !canStepForward}
          aria-label="Step forward"
          title="Step Forward"
        >
          Next &#x25B6;
        </button>
        <button
          className="diff-eq-controls__btn"
          onClick={handlePlayPause}
          disabled={isUpdating}
          aria-label="Play or pause animation"
          title="Auto-play"
        >
          &#x25B6;&#x25B6; Play
        </button>

        <div className="diff-eq-controls__spacer" />

        <div
          className={`diff-eq-controls__step-info ${isAtRest ? 'diff-eq-controls__step-info--at-rest' : ''}`}
          aria-live="polite"
        >
          {isAtRest ? 'At Rest' : `n = ${currentN}`}
        </div>
      </div>

      {/* Top Panels: Equation + Block Diagram */}
      <div className="diff-eq-panels">
        {/* Equation Panel */}
        <div className="diff-eq-equation-panel">
          <div className="diff-eq-equation-panel__header">
            {equationText} &nbsp;&nbsp;|&nbsp;&nbsp; {inputLabel}
          </div>
          {substitutionHistory.length > 0 ? (
            <div className="diff-eq-equation-panel__steps" role="log" aria-label="Step history">
              {substitutionHistory.map((step, idx) => {
                const isCurrent = idx === substitutionHistory.length - 1;
                const isZero = step.result === 0;
                return (
                  <div
                    key={step.n}
                    className={`diff-eq-step ${isCurrent ? 'diff-eq-step--current' : ''} ${isZero && !isCurrent ? 'diff-eq-step--zero' : ''}`}
                  >
                    {step.text}
                  </div>
                );
              })}
              <div ref={stepsEndRef} />
            </div>
          ) : (
            <div className="diff-eq-equation-panel__empty">
              Click "Next" to start stepping through the equation
            </div>
          )}
        </div>

        {/* Block Diagram Panel */}
        <div className="diff-eq-diagram-panel">
          <div className="diff-eq-diagram-panel__title">
            Block Diagram {isAtRest ? '(at rest)' : `\u2014 n = ${currentN}`}
          </div>
          <DiagramComponent wireValues={wireValues} />
        </div>
      </div>

      {/* Stem Plots */}
      <div className="diff-eq-plots">
        <div className="diff-eq-plot-wrapper">
          {inputPlot ? (
            <PlotDisplay plots={[inputPlot]} isLoading={false} />
          ) : (
            <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '40px' }}>
              Input signal plot
            </div>
          )}
        </div>
        <div className="diff-eq-plot-wrapper">
          {outputPlot ? (
            <PlotDisplay plots={[outputPlot]} isLoading={false} />
          ) : (
            <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '40px' }}>
              Output signal plot
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
