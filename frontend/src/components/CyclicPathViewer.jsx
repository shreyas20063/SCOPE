/**
 * CyclicPathViewer — Custom viewer for Cyclic Path Detector simulation.
 *
 * Renders SVG block diagrams from backend node/edge data,
 * highlights cyclic signal paths in distinct colors, and provides
 * a quiz mode for testing student understanding.
 */

import React, { useMemo, useCallback } from 'react';
import PlotDisplay from './PlotDisplay';
import '../styles/CyclicPathViewer.css';

// ── SVG Constants ──────────────────────────────────────────────

const SVG_WIDTH = 700;
const SVG_HEIGHT = 300;

const NODE_STYLES = {
  adder: { r: 18 },
  delay: { width: 50, height: 35 },
  gain:  { width: 50, height: 35 },
};

// ── SVG Sub-Components ─────────────────────────────────────────

/** Arrow marker definition for SVG edges */
function ArrowDefs() {
  return (
    <defs>
      <marker
        id="arrow-default"
        viewBox="0 0 10 7"
        refX="9"
        refY="3.5"
        markerWidth="8"
        markerHeight="6"
        orient="auto-start-reverse"
      >
        <polygon points="0 0, 10 3.5, 0 7" fill="var(--text-secondary)" />
      </marker>
      {/* Colored arrow markers for cycle highlighting */}
      {['#ef4444', '#10b981', '#8b5cf6', '#f59e0b'].map((color, i) => (
        <marker
          key={`arrow-cycle-${i}`}
          id={`arrow-cycle-${i}`}
          viewBox="0 0 10 7"
          refX="9"
          refY="3.5"
          markerWidth="8"
          markerHeight="6"
          orient="auto-start-reverse"
        >
          <polygon points="0 0, 10 3.5, 0 7" fill={color} />
        </marker>
      ))}
    </defs>
  );
}

/** Render a single node (adder, delay, gain, input, output) */
function BlockNode({ node }) {
  const { id, type, label, x, y } = node;

  if (type === 'input' || type === 'output') {
    return (
      <g key={id}>
        <text
          x={x}
          y={y + 5}
          textAnchor="middle"
          className="cpv-node-label cpv-io-label"
        >
          {label}
        </text>
      </g>
    );
  }

  if (type === 'adder') {
    const r = NODE_STYLES.adder.r;
    return (
      <g key={id}>
        <circle
          cx={x}
          cy={y}
          r={r}
          className="cpv-node cpv-adder"
        />
        {/* Plus sign */}
        <line x1={x - 8} y1={y} x2={x + 8} y2={y} className="cpv-adder-sign" />
        <line x1={x} y1={y - 8} x2={x} y2={y + 8} className="cpv-adder-sign" />
      </g>
    );
  }

  // delay or gain
  const w = NODE_STYLES[type]?.width || 50;
  const h = NODE_STYLES[type]?.height || 35;
  return (
    <g key={id}>
      <rect
        x={x - w / 2}
        y={y - h / 2}
        width={w}
        height={h}
        rx={4}
        className={`cpv-node cpv-${type}`}
      />
      <text
        x={x}
        y={y + 5}
        textAnchor="middle"
        className="cpv-node-label"
      >
        {label}
      </text>
    </g>
  );
}

/** Render a single edge as an SVG polyline with arrowhead */
function BlockEdge({ edge, cycleColorIndex }) {
  const { waypoints } = edge;
  if (!waypoints || waypoints.length < 2) return null;

  const points = waypoints.map(p => `${p[0]},${p[1]}`).join(' ');
  const isCycle = cycleColorIndex !== null && cycleColorIndex !== undefined;
  const markerId = isCycle ? `arrow-cycle-${cycleColorIndex}` : 'arrow-default';

  return (
    <polyline
      points={points}
      className={`cpv-edge ${isCycle ? 'cpv-edge-cycle' : ''}`}
      style={isCycle ? {
        stroke: ['#ef4444', '#10b981', '#8b5cf6', '#f59e0b'][cycleColorIndex] || '#ef4444',
      } : undefined}
      markerEnd={`url(#${markerId})`}
    />
  );
}

// ── Main Block Diagram SVG ─────────────────────────────────────

function BlockDiagramSVG({ nodes, edges, cycles, showCycles }) {
  // Build edge-to-cycle-color mapping
  const edgeCycleMap = useMemo(() => {
    const map = {};
    if (showCycles && cycles) {
      cycles.forEach((cycle, i) => {
        cycle.edge_ids.forEach(edgeId => {
          map[edgeId] = i;
        });
      });
    }
    return map;
  }, [cycles, showCycles]);

  if (!nodes || !edges) return null;

  return (
    <svg
      viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
      className="cpv-svg"
      role="img"
      aria-label="Block diagram"
    >
      <ArrowDefs />

      {/* Render edges first (below nodes) */}
      {edges.map(edge => (
        <BlockEdge
          key={edge.id}
          edge={edge}
          cycleColorIndex={edgeCycleMap[edge.id] ?? null}
        />
      ))}

      {/* Render nodes on top */}
      {nodes.map(node => (
        <BlockNode key={node.id} node={node} />
      ))}
    </svg>
  );
}

// ── Info Panel (Explore Mode) ──────────────────────────────────

function InfoPanel({ metadata }) {
  const { preset_name, equation, operator_form, num_cycles, classification, is_cyclic, cycles } = metadata;

  return (
    <div className="cpv-info-panel">
      <div className="cpv-info-row">
        <span className="cpv-info-label">System</span>
        <span className="cpv-info-value">{preset_name}</span>
      </div>
      <div className="cpv-info-row">
        <span className="cpv-info-label">Equation</span>
        <span className="cpv-info-value cpv-mono">{equation}</span>
      </div>
      <div className="cpv-info-row">
        <span className="cpv-info-label">Operator</span>
        <span className="cpv-info-value cpv-mono">{operator_form}</span>
      </div>
      <div className="cpv-info-row">
        <span className="cpv-info-label">Cyclic Paths</span>
        <span className="cpv-info-value">
          {num_cycles}
          {cycles && cycles.length > 0 && (
            <span className="cpv-cycle-legend">
              {cycles.map((c, i) => (
                <span
                  key={i}
                  className="cpv-cycle-dot"
                  style={{ backgroundColor: c.color }}
                  title={`Cycle ${i + 1}`}
                />
              ))}
            </span>
          )}
        </span>
      </div>
      <div className="cpv-info-row">
        <span className="cpv-info-label">Classification</span>
        <span className={`cpv-badge ${is_cyclic ? 'cpv-badge-iir' : 'cpv-badge-fir'}`}>
          {classification} {is_cyclic ? '(cyclic)' : '(acyclic)'}
        </span>
      </div>
    </div>
  );
}

// ── Quiz Panel ─────────────────────────────────────────────────

function QuizPanel({ quiz, onButtonClick, isUpdating }) {
  const handleAnswerClick = useCallback((index) => {
    if (quiz?.answered || isUpdating) return;
    onButtonClick('check_answer', { answer_index: index });
  }, [onButtonClick, quiz?.answered, isUpdating]);

  if (!quiz) return null;

  const { options, answered, correct, correct_answer } = quiz;

  return (
    <div className="cpv-quiz-panel">
      {!answered ? (
        <p className="cpv-quiz-prompt">
          How many cyclic signal paths does this system have?
        </p>
      ) : correct ? (
        <p className="cpv-quiz-result cpv-quiz-correct">
          Correct! This system has <strong>{correct_answer}</strong> cyclic path{correct_answer !== 1 ? 's' : ''}.
        </p>
      ) : (
        <p className="cpv-quiz-result cpv-quiz-incorrect">
          Incorrect. The answer is <strong>{correct_answer}</strong> cyclic path{correct_answer !== 1 ? 's' : ''}.
        </p>
      )}

      <div className="cpv-quiz-options">
        {options.map((opt) => {
          let btnClass = 'cpv-quiz-btn';
          if (answered) {
            if (opt === correct_answer) {
              btnClass += ' cpv-quiz-btn-correct';
            } else {
              btnClass += ' cpv-quiz-btn-disabled';
            }
          }
          return (
            <button
              key={opt}
              className={btnClass}
              onClick={() => handleAnswerClick(opt)}
              disabled={answered || isUpdating}
              aria-label={`${opt} cyclic paths`}
            >
              {opt}
            </button>
          );
        })}
      </div>

      {answered && (
        <button
          className="cpv-new-quiz-btn"
          onClick={() => onButtonClick('new_quiz')}
          disabled={isUpdating}
        >
          New Question
        </button>
      )}
    </div>
  );
}

// ── Main CyclicPathViewer Component ────────────────────────────

function CyclicPathViewer({ metadata, plots, onButtonClick, isUpdating }) {
  if (!metadata) return null;

  const {
    mode,
    nodes,
    edges,
    cycles,
    show_cycles,
    num_cycles,
    classification,
    is_cyclic,
    quiz,
  } = metadata;

  const isQuizMode = mode === 'quiz';

  // In explore mode, show cycles if checkbox is on
  // In quiz mode, show cycles only after answering
  const shouldShowCycles = isQuizMode
    ? (quiz?.answered === true)
    : (show_cycles !== false);

  return (
    <div className="cyclic-path-viewer">
      {/* SVG Block Diagram */}
      <div className="cpv-diagram-container">
        <BlockDiagramSVG
          nodes={nodes}
          edges={edges}
          cycles={cycles}
          showCycles={shouldShowCycles}
        />
      </div>

      {/* Info or Quiz Panel */}
      {isQuizMode ? (
        <QuizPanel
          quiz={quiz}
          onButtonClick={onButtonClick}
          isUpdating={isUpdating}
        />
      ) : (
        <InfoPanel metadata={metadata} />
      )}

      {/* Impulse Response Plot */}
      <PlotDisplay plots={plots} />
    </div>
  );
}

export default CyclicPathViewer;
