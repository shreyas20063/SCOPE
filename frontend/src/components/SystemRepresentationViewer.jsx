/**
 * SystemRepresentationViewer Component
 *
 * Custom viewer for the DT System Representation Navigator.
 * Shows five equivalent representations of a discrete-time LTI system
 * connected by an animated SVG concept map with conversion arrows.
 */

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import Plot from 'react-plotly.js';
import '../styles/SystemRepresentationViewer.css';

// ── Theme hook ──────────────────────────────────────────────────────────────

function useTheme() {
  const [theme, setTheme] = useState(() =>
    document.documentElement.getAttribute('data-theme') || 'dark'
  );
  useEffect(() => {
    const observer = new MutationObserver(() => {
      setTheme(document.documentElement.getAttribute('data-theme') || 'dark');
    });
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme'],
    });
    return () => observer.disconnect();
  }, []);
  return theme;
}

// ── Constants ───────────────────────────────────────────────────────────────

const NODE_COLORS = {
  block_diagram:    { main: '#8b5cf6', light: 'rgba(139,92,246,0.15)', text: '#c4b5fd' },
  diff_eq:          { main: '#3b82f6', light: 'rgba(59,130,246,0.15)', text: '#93c5fd' },
  h_r:              { main: '#14b8a6', light: 'rgba(20,184,166,0.15)', text: '#5eead4' },
  h_z:              { main: '#f59e0b', light: 'rgba(245,158,11,0.15)', text: '#fcd34d' },
  impulse_response: { main: '#ec4899', light: 'rgba(236,72,153,0.15)', text: '#f9a8d4' },
};

const NODE_LABELS = {
  block_diagram:    'Block Diagram',
  diff_eq:          'Difference Eq.',
  h_r:              'H(R)',
  h_z:              'H(z)',
  impulse_response: 'h[n]',
};

const EDGE_DEFS = [
  { id: 'de_to_bd', from: 'diff_eq', to: 'block_diagram', label: 'Realize' },
  { id: 'de_to_hr', from: 'diff_eq', to: 'h_r', label: 'R subst.' },
  { id: 'de_to_hn', from: 'diff_eq', to: 'impulse_response', label: 'δ[n] input' },
  { id: 'hr_to_hz', from: 'h_r', to: 'h_z', label: 'R → z⁻¹' },
  { id: 'hn_to_hz', from: 'impulse_response', to: 'h_z', label: 'Z-transform' },
];

// Node positions in SVG viewBox (520 x 340)
const NODE_POS = {
  block_diagram:    { x: 260, y: 42 },
  diff_eq:          { x: 260, y: 142 },
  h_r:              { x: 420, y: 242 },
  impulse_response: { x: 100, y: 242 },
  h_z:              { x: 260, y: 310 },
};

const NODE_W = 130;
const NODE_H = 44;

// ── SystemInfoBadge ─────────────────────────────────────────────────────────

function SystemInfoBadge({ metadata }) {
  if (!metadata) return null;
  const { preset_name, system_order, is_fir, is_stable, is_marginally_stable } = metadata;

  let stabilityLabel, stabilityColor;
  if (is_stable) {
    stabilityLabel = 'STABLE';
    stabilityColor = '#10b981';
  } else if (is_marginally_stable) {
    stabilityLabel = 'MARGINALLY STABLE';
    stabilityColor = '#f59e0b';
  } else {
    stabilityLabel = 'UNSTABLE';
    stabilityColor = '#ef4444';
  }

  return (
    <div className="sr-info-badge">
      <div className="sr-badge-row">
        <span className="sr-badge-label">System</span>
        <span className="sr-badge-value">{preset_name}</span>
      </div>
      <div className="sr-badge-row">
        <span className="sr-badge-label">Order</span>
        <span className="sr-badge-value">{system_order}</span>
      </div>
      <div className="sr-badge-row">
        <span className="sr-badge-pill" style={{
          background: is_fir ? 'rgba(20,184,166,0.2)' : 'rgba(124,58,237,0.2)',
          color: is_fir ? '#14b8a6' : '#a78bfa',
        }}>
          {is_fir ? 'FIR' : 'IIR'}
        </span>
        <span className="sr-badge-pill" style={{
          background: `${stabilityColor}33`,
          color: stabilityColor,
        }}>
          {stabilityLabel}
        </span>
      </div>
    </div>
  );
}

// ── ConceptMapSVG ───────────────────────────────────────────────────────────

function ConceptMapSVG({ metadata, activeEdge, onEdgeClick, animKey, challengeHidden }) {
  const theme = useTheme();
  const isDark = theme === 'dark';
  const textColor = isDark ? '#f1f5f9' : '#1e293b';
  const mutedColor = isDark ? '#64748b' : '#94a3b8';
  const bgColor = isDark ? '#131b2e' : '#f8fafc';

  // Compute edge paths
  const edges = useMemo(() => EDGE_DEFS.map(e => {
    const from = NODE_POS[e.from];
    const to = NODE_POS[e.to];
    // Calculate edge start/end at node border
    const dx = to.x - from.x;
    const dy = to.y - from.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const nx = dx / dist;
    const ny = dy / dist;
    const x1 = from.x + nx * (NODE_H / 2 + 4);
    const y1 = from.y + ny * (NODE_H / 2 + 4);
    const x2 = to.x - nx * (NODE_H / 2 + 8);
    const y2 = to.y - ny * (NODE_H / 2 + 8);
    // Control point for curve
    const mx = (x1 + x2) / 2;
    const my = (y1 + y2) / 2;
    const perpX = -ny * 20;
    const perpY = nx * 20;
    const path = `M ${x1} ${y1} Q ${mx + perpX} ${my + perpY} ${x2} ${y2}`;
    // Label position
    const lx = mx + perpX * 0.7;
    const ly = my + perpY * 0.7;
    return { ...e, path, x1, y1, x2, y2, lx, ly };
  }), []);

  // Get summary text for each node
  const getSummary = useCallback((nodeId) => {
    if (!metadata) return '';
    switch (nodeId) {
      case 'diff_eq': return metadata.diff_eq?.text?.substring(0, 30) + (metadata.diff_eq?.text?.length > 30 ? '…' : '') || '';
      case 'h_r': {
        const n = metadata.h_r?.numerator || '';
        const d = metadata.h_r?.denominator || '';
        return d === '1' ? n.substring(0, 20) : `(${n.substring(0,12)})/(${d.substring(0,12)})`;
      }
      case 'h_z': {
        const n = metadata.h_z?.numerator || '';
        const d = metadata.h_z?.denominator || '';
        return d === '1' ? n.substring(0, 20) : `(${n.substring(0,12)})/(${d.substring(0,12)})`;
      }
      case 'impulse_response': {
        const h = metadata.impulse_response?.h || [];
        return `{${h.slice(0, 4).map(v => v % 1 === 0 ? v : v.toFixed(2)).join(', ')}…}`;
      }
      case 'block_diagram': {
        const bd = metadata.block_diagram;
        return bd ? `DF-II, ${bd.delay_count} delay${bd.delay_count !== 1 ? 's' : ''}` : '';
      }
      default: return '';
    }
  }, [metadata]);

  return (
    <svg viewBox="0 0 520 340" className="sr-concept-map-svg" aria-label="System representation concept map">
      <defs>
        {edges.map(e => (
          <marker
            key={`arrow-${e.id}`}
            id={`sr-arrow-${e.id}`}
            markerWidth="8"
            markerHeight="6"
            refX="7"
            refY="3"
            orient="auto"
          >
            <polygon
              points="0 0, 8 3, 0 6"
              fill={activeEdge === e.id ? '#00d9ff' : mutedColor}
            />
          </marker>
        ))}
      </defs>

      {/* Edges */}
      {edges.map((e, i) => {
        const isActive = activeEdge === e.id;
        return (
          <g key={e.id} className="sr-edge-group" onClick={() => onEdgeClick(e.id)} style={{ cursor: 'pointer' }}>
            <path
              d={e.path}
              fill="none"
              stroke={isActive ? '#00d9ff' : (isDark ? 'rgba(148,163,184,0.25)' : 'rgba(100,116,139,0.3)')}
              strokeWidth={isActive ? 2.5 : 1.5}
              markerEnd={`url(#sr-arrow-${e.id})`}
              className={`sr-edge-path ${isActive ? 'sr-edge-active' : ''}`}
              style={{ animationDelay: `${i * 0.15}s` }}
            />
            {/* Edge label */}
            <text
              x={e.lx}
              y={e.ly}
              textAnchor="middle"
              fontSize="9"
              fontWeight={isActive ? 700 : 500}
              fill={isActive ? '#00d9ff' : mutedColor}
              className="sr-edge-label"
            >
              {e.label}
            </text>
            {/* Invisible wider hit area */}
            <path
              d={e.path}
              fill="none"
              stroke="transparent"
              strokeWidth="16"
            />
          </g>
        );
      })}

      {/* Nodes */}
      {Object.entries(NODE_POS).map(([nodeId, pos], i) => {
        const color = NODE_COLORS[nodeId];
        const isHidden = challengeHidden?.includes(nodeId);
        return (
          <g
            key={nodeId}
            className={`sr-node-group ${isHidden ? 'sr-node-hidden' : ''}`}
            style={{ '--node-color': color.main, '--anim-delay': `${i * 0.1}s`, animationDelay: `${i * 0.1}s` }}
          >
            <rect
              x={pos.x - NODE_W / 2}
              y={pos.y - NODE_H / 2}
              width={NODE_W}
              height={NODE_H}
              rx="8"
              fill={isHidden ? (isDark ? '#1e293b' : '#e2e8f0') : (isDark ? color.light : `${color.main}15`)}
              stroke={isHidden ? (isDark ? '#334155' : '#cbd5e1') : color.main}
              strokeWidth="1.5"
              className="sr-node-rect"
            />
            <text
              x={pos.x}
              y={pos.y - 5}
              textAnchor="middle"
              fontSize="11"
              fontWeight="700"
              fill={isHidden ? mutedColor : (isDark ? color.text : color.main)}
              fontFamily="'Fira Code', monospace"
            >
              {isHidden ? '?' : NODE_LABELS[nodeId]}
            </text>
            {!isHidden && (
              <text
                x={pos.x}
                y={pos.y + 11}
                textAnchor="middle"
                fontSize="8"
                fill={mutedColor}
                fontFamily="'Fira Code', monospace"
              >
                {getSummary(nodeId)}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}

// ── FractionDisplay ─────────────────────────────────────────────────────────

function FractionDisplay({ numerator, denominator, label }) {
  if (denominator === '1' || !denominator) {
    return (
      <div className="sr-fraction">
        <span className="sr-fraction-label">{label} =</span>
        <span className="sr-fraction-num">{numerator}</span>
      </div>
    );
  }
  return (
    <div className="sr-fraction">
      <span className="sr-fraction-label">{label} =</span>
      <div className="sr-fraction-stack">
        <span className="sr-fraction-num">{numerator}</span>
        <span className="sr-fraction-line" />
        <span className="sr-fraction-den">{denominator}</span>
      </div>
    </div>
  );
}

// ── BlockDiagramSVG ─────────────────────────────────────────────────────────

function BlockDiagramSVG({ blockDiagram, isDark }) {
  if (!blockDiagram) return null;
  const { b_gains, a_gains, delay_count } = blockDiagram;
  const textColor = isDark ? '#f1f5f9' : '#1e293b';
  const lineColor = '#14b8a6';
  const fbColor = '#00d9ff';
  const blockFill = isDark ? '#1e293b' : '#f1f5f9';
  const blockStroke = isDark ? '#334155' : '#cbd5e1';
  const hasFeedback = a_gains && a_gains.length > 0;

  const numDelays = delay_count || 1;
  const svgH = 70 + numDelays * 50;
  const svgW = hasFeedback ? 340 : 280;

  const fmtGain = (g) => {
    if (g === 1) return '1';
    if (g === -1) return '-1';
    if (g === Math.round(g)) return String(g);
    // Try fraction
    for (const d of [2, 3, 4, 5, 6, 8, 10]) {
      const n = g * d;
      if (Math.abs(n - Math.round(n)) < 1e-9) return `${Math.round(n)}/${d}`;
    }
    return g.toFixed(3);
  };

  return (
    <svg viewBox={`0 0 ${svgW} ${svgH}`} className="sr-block-diagram-svg" aria-label="Direct Form II block diagram">
      <defs>
        <marker id="sr-bd-arrow" markerWidth="7" markerHeight="5" refX="6" refY="2.5" orient="auto">
          <polygon points="0 0, 7 2.5, 0 5" fill={lineColor} />
        </marker>
        <marker id="sr-bd-arrow-fb" markerWidth="7" markerHeight="5" refX="6" refY="2.5" orient="auto">
          <polygon points="0 0, 7 2.5, 0 5" fill={fbColor} />
        </marker>
      </defs>

      {/* Input */}
      <text x="5" y="34" fill={textColor} fontSize="11" fontFamily="'Fira Code', monospace">x[n]</text>
      <line x1="38" y1="30" x2="56" y2="30" stroke={lineColor} strokeWidth="1.5" markerEnd="url(#sr-bd-arrow)" />

      {/* Top adder (if feedback) */}
      {hasFeedback && (
        <>
          <circle cx="68" cy="30" r="10" fill={blockFill} stroke={lineColor} strokeWidth="1.5" />
          <text x="68" y="34" textAnchor="middle" fill={textColor} fontSize="12" fontWeight="bold">+</text>
          <line x1="78" y1="30" x2="96" y2="30" stroke={lineColor} strokeWidth="1.5" />
        </>
      )}

      {/* w[n] node (center tap point) */}
      <circle cx={hasFeedback ? 104 : 68} cy="30" r="3" fill={lineColor} />
      <text x={hasFeedback ? 104 : 68} y="20" textAnchor="middle" fill={isDark ? '#94a3b8' : '#64748b'} fontSize="8">w[n]</text>

      {/* Feedforward branch going right → output adder */}
      {(() => {
        const wX = hasFeedback ? 104 : 68;
        const outAdderX = svgW - 60;
        // b₀ gain at the top
        return (
          <>
            <line x1={wX} y1="30" x2={wX + 30} y2="30" stroke={lineColor} strokeWidth="1.5" />
            <rect x={wX + 30} y="20" width="28" height="20" rx="3" fill={blockFill} stroke={blockStroke} strokeWidth="1" />
            <text x={wX + 44} y="34" textAnchor="middle" fill={lineColor} fontSize="9" fontWeight="bold">{fmtGain(b_gains[0])}</text>
            <line x1={wX + 58} y1="30" x2={outAdderX - 12} y2="30" stroke={lineColor} strokeWidth="1.5" markerEnd="url(#sr-bd-arrow)" />
            {/* Output adder */}
            <circle cx={outAdderX} cy="30" r="10" fill={blockFill} stroke={lineColor} strokeWidth="1.5" />
            <text x={outAdderX} y="34" textAnchor="middle" fill={textColor} fontSize="12" fontWeight="bold">+</text>
            <line x1={outAdderX + 10} y1="30" x2={outAdderX + 30} y2="30" stroke={lineColor} strokeWidth="1.5" markerEnd="url(#sr-bd-arrow)" />
            <text x={outAdderX + 34} y="34" fill={textColor} fontSize="11" fontFamily="'Fira Code', monospace">y[n]</text>
          </>
        );
      })()}

      {/* Delay chain + feedforward/feedback taps */}
      {Array.from({ length: numDelays }, (_, i) => {
        const wX = hasFeedback ? 104 : 68;
        const outAdderX = svgW - 60;
        const yTop = 30 + i * 50;
        const yDel = yTop + 30;
        const bGain = i + 1 < b_gains.length ? b_gains[i + 1] : null;
        const aGain = i < a_gains.length ? a_gains[i] : null;

        return (
          <g key={`delay-${i}`}>
            {/* Delay block */}
            <line x1={wX} y1={yTop} x2={wX} y2={yDel - 10} stroke={lineColor} strokeWidth="1.5" />
            <rect x={wX - 18} y={yDel - 10} width="36" height="20" rx="3" fill={blockFill} stroke={blockStroke} strokeWidth="1" />
            <text x={wX} y={yDel + 4} textAnchor="middle" fill={textColor} fontSize="9" fontFamily="'Fira Code', monospace">z⁻¹</text>
            {/* Tap point below delay */}
            <line x1={wX} y1={yDel + 10} x2={wX} y2={yDel + 20} stroke={lineColor} strokeWidth="1" />
            <circle cx={wX} cy={yDel + 20} r="2.5" fill={lineColor} />

            {/* Feedforward tap (b gain) going right */}
            {bGain !== null && Math.abs(bGain) > 1e-12 && (
              <>
                <line x1={wX} y1={yDel + 20} x2={wX + 30} y2={yDel + 20} stroke={lineColor} strokeWidth="1" />
                <rect x={wX + 30} y={yDel + 10} width="28" height="20" rx="3" fill={blockFill} stroke={blockStroke} strokeWidth="1" />
                <text x={wX + 44} y={yDel + 24} textAnchor="middle" fill={lineColor} fontSize="9" fontWeight="bold">{fmtGain(bGain)}</text>
                <line x1={wX + 58} y1={yDel + 20} x2={outAdderX} y2={yDel + 20} stroke={lineColor} strokeWidth="1" />
                <line x1={outAdderX} y1={yDel + 20} x2={outAdderX} y2={30 + 10} stroke={lineColor} strokeWidth="1" markerEnd="url(#sr-bd-arrow)" />
              </>
            )}

            {/* Feedback tap (a gain) going left */}
            {hasFeedback && aGain !== null && Math.abs(aGain) > 1e-12 && (
              <>
                <line x1={wX} y1={yDel + 20} x2={wX - 30} y2={yDel + 20} stroke={fbColor} strokeWidth="1" />
                <rect x={wX - 58} y={yDel + 10} width="28" height="20" rx="3" fill={blockFill} stroke={blockStroke} strokeWidth="1" />
                <text x={wX - 44} y={yDel + 24} textAnchor="middle" fill={fbColor} fontSize="9" fontWeight="bold">{fmtGain(-aGain)}</text>
                <line x1={wX - 58} y1={yDel + 20} x2={68} y2={yDel + 20} stroke={fbColor} strokeWidth="1" />
                <line x1={68} y1={yDel + 20} x2={68} y2={40} stroke={fbColor} strokeWidth="1" markerEnd="url(#sr-bd-arrow-fb)" />
              </>
            )}
          </g>
        );
      })}
    </svg>
  );
}

// ── RepresentationCard ──────────────────────────────────────────────────────

function RepresentationCard({ nodeId, metadata, isDark, isHidden }) {
  const color = NODE_COLORS[nodeId];

  const renderContent = () => {
    if (isHidden) {
      return <div className="sr-card-hidden">?</div>;
    }

    switch (nodeId) {
      case 'diff_eq':
        return (
          <div className="sr-card-equation">
            {metadata?.diff_eq?.text || ''}
          </div>
        );

      case 'h_r':
        return (
          <FractionDisplay
            numerator={metadata?.h_r?.numerator}
            denominator={metadata?.h_r?.denominator}
            label="H(R)"
          />
        );

      case 'h_z':
        return (
          <FractionDisplay
            numerator={metadata?.h_z?.numerator}
            denominator={metadata?.h_z?.denominator}
            label="H(z)"
          />
        );

      case 'impulse_response': {
        const h = metadata?.impulse_response?.h || [];
        const n = metadata?.impulse_response?.n || [];
        const closedForm = metadata?.impulse_response?.closed_form || '';
        return (
          <div className="sr-card-impulse">
            <div className="sr-card-sequence">
              {h.slice(0, 8).map((val, i) => (
                <div key={i} className="sr-card-sample">
                  <span className="sr-card-sample-n">n={n[i]}</span>
                  <span className="sr-card-sample-val">{val % 1 === 0 ? val : val.toFixed(4)}</span>
                </div>
              ))}
              {h.length > 8 && <span className="sr-card-ellipsis">…</span>}
            </div>
            {closedForm && (
              <div className="sr-card-closed-form">{closedForm}</div>
            )}
          </div>
        );
      }

      case 'block_diagram':
        return (
          <BlockDiagramSVG blockDiagram={metadata?.block_diagram} isDark={isDark} />
        );

      default:
        return null;
    }
  };

  return (
    <div
      className={`sr-card ${isHidden ? 'sr-card--hidden' : ''}`}
      style={{ '--card-accent': color.main }}
    >
      <div className="sr-card-header">
        <div className="sr-card-dot" style={{ background: color.main }} />
        <span className="sr-card-title">{NODE_LABELS[nodeId]}</span>
      </div>
      <div className="sr-card-body">
        {renderContent()}
      </div>
    </div>
  );
}

// ── ConversionPanel ─────────────────────────────────────────────────────────

function ConversionPanel({ edgeId, conversions, onClose }) {
  if (!edgeId || !conversions) return null;

  // Try both directions
  const conv = conversions[edgeId];
  if (!conv) return null;

  return (
    <div className="sr-conversion-panel">
      <div className="sr-conversion-header">
        <div>
          <div className="sr-conversion-title">{conv.title}</div>
          <div className="sr-conversion-subtitle">{conv.subtitle}</div>
        </div>
        <button className="sr-conversion-close" onClick={onClose} aria-label="Close">×</button>
      </div>
      <div className="sr-conversion-steps">
        {conv.steps?.map((step, i) => (
          <div key={i} className={`sr-conversion-step ${step.startsWith('  ') ? 'sr-conversion-step--math' : ''}`}>
            {!step.startsWith('  ') && <span className="sr-conversion-step-num">{i + 1}</span>}
            <span>{step}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── ChallengePanel ──────────────────────────────────────────────────────────

function ChallengePanel({ challenge, metadata, onNewChallenge, onReveal }) {
  if (!challenge?.active) return null;

  const sourceLabel = NODE_LABELS[challenge.source_rep] || '?';
  const targetLabel = NODE_LABELS[challenge.target_rep] || '?';

  return (
    <div className="sr-challenge-panel">
      <div className="sr-challenge-header">
        <span className="sr-challenge-icon">🧩</span>
        <span className="sr-challenge-title">Challenge Mode</span>
      </div>
      <div className="sr-challenge-prompt">
        Given the <strong style={{ color: NODE_COLORS[challenge.source_rep]?.main }}>{sourceLabel}</strong> representation,
        derive the <strong style={{ color: NODE_COLORS[challenge.target_rep]?.main }}>{targetLabel}</strong>.
      </div>
      <div className="sr-challenge-actions">
        <button className="sr-btn sr-btn-primary" onClick={onReveal} disabled={challenge.revealed}>
          {challenge.revealed ? 'Revealed!' : 'Reveal Answer'}
        </button>
        <button className="sr-btn sr-btn-secondary" onClick={onNewChallenge}>
          New Challenge
        </button>
      </div>
    </div>
  );
}

// ── StemPlot (Plotly wrapper) ───────────────────────────────────────────────

function StemPlot({ plotData, theme, height = 220 }) {
  if (!plotData) return null;
  const isDark = theme === 'dark';

  // Build yaxis: use autorange when backend says so, otherwise spread backend range
  const backendY = plotData.layout?.yaxis || {};
  const yaxis = {
    ...backendY,
    gridcolor: isDark ? 'rgba(148,163,184,0.08)' : 'rgba(148,163,184,0.15)',
    zerolinecolor: isDark ? 'rgba(148,163,184,0.2)' : 'rgba(148,163,184,0.3)',
    color: isDark ? '#94a3b8' : '#475569',
  };

  const layout = {
    ...plotData.layout,
    paper_bgcolor: isDark ? '#0a0e27' : 'rgba(255,255,255,0.98)',
    plot_bgcolor: isDark ? '#131b2e' : '#f8fafc',
    font: {
      family: 'Inter, sans-serif',
      size: 11,
      color: isDark ? '#94a3b8' : '#475569',
    },
    title: {
      text: plotData.title,
      font: { size: 13, color: isDark ? '#f1f5f9' : '#1e293b' },
    },
    xaxis: {
      ...plotData.layout?.xaxis,
      gridcolor: isDark ? 'rgba(148,163,184,0.08)' : 'rgba(148,163,184,0.15)',
      zerolinecolor: isDark ? 'rgba(148,163,184,0.2)' : 'rgba(148,163,184,0.3)',
      color: isDark ? '#94a3b8' : '#475569',
    },
    yaxis,
    legend: {
      ...plotData.layout?.legend,
      bgcolor: isDark ? 'rgba(0,0,0,0.4)' : 'rgba(255,255,255,0.9)',
      font: { size: 10, color: isDark ? '#f1f5f9' : '#1e293b' },
    },
    margin: { t: 40, r: 20, b: 45, l: 50 },
    height,
    datarevision: `${plotData.id}-${plotData.title}-${Date.now()}`,
    uirevision: plotData.layout?.uirevision || plotData.id,
  };

  return (
    <div className="sr-stem-plot">
      <Plot
        data={plotData.data}
        layout={layout}
        config={{
          responsive: true,
          displayModeBar: true,
          modeBarButtonsToRemove: ['lasso2d', 'select2d'],
          displaylogo: false,
        }}
        style={{ width: '100%', height: `${height}px` }}
        useResizeHandler
      />
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────────────

export default function SystemRepresentationViewer({
  metadata,
  plots,
  currentParams,
  onParamChange,
  onButtonClick,
  isUpdating,
}) {
  const theme = useTheme();
  const isDark = theme === 'dark';

  const [activeEdge, setActiveEdge] = useState(null);
  const [animKey, setAnimKey] = useState(0);

  // Build a fingerprint that changes whenever the system changes
  // (preset, coefficients, mode, challenge state, num_samples)
  const systemFingerprint = useMemo(() => {
    if (!metadata) return '';
    const b = metadata.b_coeffs?.join(',') || '';
    const a = metadata.a_coeffs?.join(',') || '';
    const ch = metadata.challenge?.active ? `${metadata.challenge.source_rep}-${metadata.challenge.target_rep}-${metadata.challenge.revealed}` : 'none';
    return `${metadata.preset_name}|${b}|${a}|${metadata.mode}|${ch}`;
  }, [metadata]);

  // Trigger animation + clear activeEdge on any system change
  const prevFingerprintRef = useRef(systemFingerprint);
  useEffect(() => {
    if (systemFingerprint && systemFingerprint !== prevFingerprintRef.current) {
      prevFingerprintRef.current = systemFingerprint;
      setAnimKey(k => k + 1);
      setActiveEdge(null);
    }
  }, [systemFingerprint]);

  const handleEdgeClick = useCallback((edgeId) => {
    setActiveEdge(prev => prev === edgeId ? null : edgeId);
  }, []);

  const handleNewChallenge = useCallback(() => {
    onButtonClick?.('new_challenge');
    setActiveEdge(null);
  }, [onButtonClick]);

  const handleReveal = useCallback(() => {
    onButtonClick?.('reveal_all');
  }, [onButtonClick]);

  const findPlot = useCallback((id) => {
    return plots?.find(p => p.id === id) || null;
  }, [plots]);

  // Challenge mode: determine which nodes to hide
  const challenge = metadata?.challenge;
  const mode = metadata?.mode || 'explore';
  const challengeHidden = useMemo(() => {
    if (mode !== 'challenge' || !challenge?.active || challenge?.revealed) return [];
    // Hide everything except the source
    const allNodes = Object.keys(NODE_LABELS);
    return allNodes.filter(n => n !== challenge.source_rep);
  }, [mode, challenge]);

  if (!metadata) {
    return <div className="sr-viewer sr-loading">Loading representations…</div>;
  }

  return (
    <div className="sr-viewer" data-theme={theme} key={animKey}>
      {/* System Info Badge */}
      <SystemInfoBadge metadata={metadata} />

      {/* Challenge panel */}
      {mode === 'challenge' && (
        <ChallengePanel
          challenge={challenge}
          metadata={metadata}
          onNewChallenge={handleNewChallenge}
          onReveal={handleReveal}
        />
      )}

      {/* Concept Map */}
      <div className="sr-concept-map">
        <div className="sr-concept-map-label">Conversion Map — click an arrow for details</div>
        <ConceptMapSVG
          metadata={metadata}
          activeEdge={activeEdge}
          onEdgeClick={handleEdgeClick}
          animKey={animKey}
          challengeHidden={challengeHidden}
        />
      </div>

      {/* Conversion Detail Panel (conditionally shown) */}
      {activeEdge && (
        <ConversionPanel
          edgeId={activeEdge}
          conversions={metadata.conversions}
          onClose={() => setActiveEdge(null)}
        />
      )}

      {/* 5 Representation Cards */}
      <div className="sr-cards">
        {['diff_eq', 'h_r', 'h_z', 'impulse_response', 'block_diagram'].map(nodeId => (
          <RepresentationCard
            key={nodeId}
            nodeId={nodeId}
            metadata={metadata}
            isDark={isDark}
            isHidden={challengeHidden.includes(nodeId)}
          />
        ))}
      </div>

      {/* Plots Row */}
      <div className="sr-plots-row">
        <StemPlot plotData={findPlot('impulse_response')} theme={theme} height={240} />
        <StemPlot plotData={findPlot('pole_zero')} theme={theme} height={240} />
      </div>
    </div>
  );
}
