/**
 * OperatorAlgebraViewer
 *
 * Custom viewer for the Operator Algebra Visualizer simulation.
 * Shows four representations of an R-operator polynomial:
 *   1. Expanded polynomial form
 *   2. Factored form
 *   3. Difference equation
 *   4. Block diagram (SVG tapped delay line)
 * Plus an impulse response stem plot via PlotDisplay.
 */

import React, { useCallback, useMemo } from 'react';
import PlotDisplay from './PlotDisplay';
import '../styles/OperatorAlgebraViewer.css';

// ============================================================
// SVG Block Diagram — Tapped Delay Line
// ============================================================

function BlockDiagram({ coefficients }) {
  if (!coefficients || coefficients.length === 0) return null;

  // Filter out NaN/undefined values
  const safeCoeffs = coefficients.map(c =>
    (c === null || c === undefined || isNaN(c)) ? 0 : c
  );

  const numTaps = safeCoeffs.length;
  const numDelays = numTaps - 1;

  // Layout constants — scale spacing for large polynomials
  const tapSpacing = numTaps > 8 ? 70 : 100;
  const topY = 40;
  const delayY = topY;
  const gainY = 130;
  const sumY = 190;
  const padX = 70;
  const totalWidth = Math.max(400, padX * 2 + numTaps * tapSpacing);
  const totalHeight = 240;

  const tapX = (i) => padX + i * tapSpacing;

  const fmtCoeff = (c) => {
    if (c === 0) return '0';
    if (c === Math.floor(c)) return String(Math.round(c));
    return c.toFixed(3).replace(/0+$/, '').replace(/\.$/, '');
  };

  return (
    <svg
      className="oa-block-diagram-svg"
      viewBox={`0 0 ${totalWidth} ${totalHeight}`}
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label={`Block diagram: tapped delay line with ${numTaps} coefficients`}
    >
      <defs>
        <marker id="oa-arrow" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
          <polygon points="0 0, 8 3, 0 6" className="oa-arrowhead" />
        </marker>
      </defs>

      {/* Input label */}
      <text className="oa-signal-label" x={tapX(0) - 30} y={delayY + 4}>x[n]</text>

      {/* Main horizontal line (delay chain) */}
      <line
        className="oa-wire"
        x1={tapX(0) - 5}
        y1={delayY}
        x2={tapX(Math.max(0, numDelays)) + (numDelays > 0 ? 0 : 20)}
        y2={delayY}
        markerEnd="url(#oa-arrow)"
      />

      {/* Delay blocks between taps */}
      {Array.from({ length: numDelays }, (_, i) => {
        const x1 = tapX(i) + 15;
        const x2 = tapX(i + 1) - 15;
        const cx = (x1 + x2) / 2;
        return (
          <g key={`delay-${i}`}>
            <rect
              className="oa-delay-block"
              x={cx - 20}
              y={delayY - 14}
              width={40}
              height={28}
              rx={4}
            />
            <text className="oa-block-text" x={cx} y={delayY + 4}>R</text>
          </g>
        );
      })}

      {/* Tap nodes (circles) on the delay chain */}
      {Array.from({ length: numTaps }, (_, i) => (
        <circle
          key={`tap-${i}`}
          className="oa-tap-node"
          cx={tapX(i)}
          cy={delayY}
          r={4}
        />
      ))}

      {/* Vertical wires from taps to gain blocks */}
      {safeCoeffs.map((c, i) => (
        <g key={`gain-path-${i}`}>
          <line
            className="oa-wire"
            x1={tapX(i)}
            y1={delayY + 4}
            x2={tapX(i)}
            y2={gainY - 14}
          />
          <rect
            className={`oa-gain-block ${c === 0 ? 'oa-gain-zero' : ''}`}
            x={tapX(i) - 22}
            y={gainY - 14}
            width={44}
            height={28}
            rx={4}
          />
          <text className="oa-block-text" x={tapX(i)} y={gainY + 4}>
            {fmtCoeff(c)}
          </text>
          <line
            className="oa-wire"
            x1={tapX(i)}
            y1={gainY + 14}
            x2={tapX(i)}
            y2={sumY}
          />
        </g>
      ))}

      {/* Summation line (horizontal) */}
      {numTaps > 1 && (
        <line
          className="oa-wire oa-sum-wire"
          x1={tapX(0)}
          y1={sumY}
          x2={tapX(numTaps - 1)}
          y2={sumY}
        />
      )}

      {/* Adder circle */}
      <circle
        className="oa-adder"
        cx={tapX(numTaps - 1)}
        cy={sumY}
        r={12}
      />
      <text className="oa-adder-text" x={tapX(numTaps - 1)} y={sumY + 5}>+</text>

      {/* Output arrow */}
      <line
        className="oa-wire"
        x1={tapX(numTaps - 1) + 12}
        y1={sumY}
        x2={tapX(numTaps - 1) + 45}
        y2={sumY}
        markerEnd="url(#oa-arrow)"
      />
      <text className="oa-signal-label" x={tapX(numTaps - 1) + 50} y={sumY + 4}>y[n]</text>
    </svg>
  );
}

// ============================================================
// Impulse response sequence formatter
// ============================================================
function formatImpulseSequence(coefficients) {
  if (!coefficients || coefficients.length === 0) return 'h[n] = {0}';

  // Only show non-zero trailing portion (trim trailing zeros)
  let lastNonZero = coefficients.length - 1;
  while (lastNonZero > 0 && Math.abs(coefficients[lastNonZero]) < 1e-12) {
    lastNonZero--;
  }

  const trimmed = coefficients.slice(0, lastNonZero + 1);
  const vals = trimmed.map(c => {
    if (c === null || c === undefined || isNaN(c)) return '0';
    if (Number.isInteger(c)) return String(c);
    return c.toFixed(4).replace(/0+$/, '').replace(/\.$/, '');
  });

  return `h[n] = {${vals.join(', ')}}`;
}

// ============================================================
// Main Viewer Component
// ============================================================

function OperatorAlgebraViewer({ metadata, plots, onButtonClick }) {
  const {
    expanded = '',
    factored = '',
    difference_eq: differenceEq = '',
    coefficients = [],
    degree = 0,
    error = null,
    presets = {},
  } = metadata || {};

  const handlePresetClick = useCallback(
    (presetId) => {
      if (onButtonClick) {
        onButtonClick('load_preset', { preset_id: presetId });
      }
    },
    [onButtonClick]
  );

  const presetList = useMemo(
    () => Object.entries(presets),
    [presets]
  );

  const showFactored = factored && factored !== expanded;

  // Build a stable key from the expression data so PlotDisplay
  // fully re-mounts when the expression fundamentally changes
  const plotKey = useMemo(
    () => `oa-plot-${expanded}-${degree}-${coefficients.length}`,
    [expanded, degree, coefficients.length]
  );

  const impulseLabel = useMemo(
    () => formatImpulseSequence(coefficients),
    [coefficients]
  );

  return (
    <div className="oa-viewer">
      {/* Preset buttons */}
      <div className="oa-presets" role="group" aria-label="Preset expressions">
        <span className="oa-presets-label">Presets</span>
        <div className="oa-presets-buttons">
          {presetList.map(([id, preset]) => (
            <button
              key={id}
              className="oa-preset-btn"
              onClick={() => handlePresetClick(id)}
              title={`Load ${preset.expression}`}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="oa-error" role="alert">
          <span className="oa-error-icon">!</span>
          <span>{error}</span>
        </div>
      )}

      {/* Two-column layout: Representations + Block Diagram */}
      {!error && expanded && (
        <div className="oa-main-grid">
          {/* Left: Math representations */}
          <div className="oa-representations">
            <h3 className="oa-section-title">Representations</h3>

            <div className="oa-rep-card">
              <span className="oa-rep-label">Expanded</span>
              <span className="oa-rep-value oa-mono">{expanded}</span>
            </div>

            {showFactored && (
              <div className="oa-rep-card">
                <span className="oa-rep-label">Factored</span>
                <span className="oa-rep-value oa-mono">{factored}</span>
              </div>
            )}

            <div className="oa-rep-card">
              <span className="oa-rep-label">Difference Equation</span>
              <span className="oa-rep-value oa-mono">{differenceEq}</span>
            </div>

            <div className="oa-rep-card">
              <span className="oa-rep-label">Impulse Response</span>
              <span className="oa-rep-value oa-mono">{impulseLabel}</span>
            </div>
          </div>

          {/* Right: Block diagram */}
          <div className="oa-block-diagram">
            <h3 className="oa-section-title">Block Diagram</h3>
            <div className="oa-diagram-container">
              <BlockDiagram coefficients={coefficients} />
            </div>
          </div>
        </div>
      )}

      {/* Impulse response plot */}
      <div className="oa-plot-section" key={plotKey}>
        <PlotDisplay
          plots={plots}
          isLoading={false}
          emptyMessage={error ? 'Fix expression to see impulse response.' : 'Loading...'}
        />
      </div>
    </div>
  );
}

export default OperatorAlgebraViewer;
