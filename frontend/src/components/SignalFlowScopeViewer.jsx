import React, { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import api from '../services/api';
import PlotDisplay from './PlotDisplay';

// Probe colors
const PROBE_COLORS = ['#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899'];
const MAX_PROBES = 6;

// SFG node sizing
const NODE_RADIUS = 18;
const BRANCH_RADIUS = 6;
const ARROW_SIZE = 8;

// ============================================================================
// SFG Node Component
// ============================================================================
function SFGNode({ node, onToggleProbe, isProbed, probeColor }) {
  const { id, type, label, position, probeable } = node;
  const x = position?.x || 0;
  const y = position?.y || 0;

  const radius = type === 'branch' ? BRANCH_RADIUS : NODE_RADIUS;

  // Color by type
  let fill, stroke;
  if (isProbed) {
    fill = `${probeColor}22`;
    stroke = probeColor;
  } else {
    switch (type) {
      case 'source':
      case 'sink':
        fill = 'rgba(20, 184, 166, 0.12)';
        stroke = 'rgba(20, 184, 166, 0.7)';
        break;
      case 'sum':
        fill = 'rgba(245, 158, 11, 0.1)';
        stroke = 'rgba(245, 158, 11, 0.6)';
        break;
      case 'branch':
        fill = 'rgba(148, 163, 184, 0.5)';
        stroke = 'rgba(148, 163, 184, 0.6)';
        break;
      default:
        fill = 'rgba(59, 130, 246, 0.08)';
        stroke = 'rgba(59, 130, 246, 0.5)';
    }
  }

  return (
    <g
      className={`sfs-node ${probeable ? 'sfs-node-probeable' : ''} ${isProbed ? 'sfs-node-probed' : ''}`}
      transform={`translate(${x}, ${y})`}
      onClick={probeable ? () => onToggleProbe(id) : undefined}
      style={{ cursor: probeable ? 'pointer' : 'default' }}
    >
      {/* Probe glow ring */}
      {isProbed && (
        <circle
          r={radius + 6}
          fill="none"
          stroke={probeColor}
          strokeWidth={2}
          opacity={0.4}
          className="sfs-probe-ring"
        />
      )}
      {/* Main circle */}
      <circle
        r={radius}
        fill={fill}
        stroke={stroke}
        strokeWidth={type === 'branch' ? 1.5 : 2}
      />
      {/* Sum symbol */}
      {type === 'sum' && (
        <text
          textAnchor="middle"
          dominantBaseline="central"
          fill="rgba(245, 158, 11, 0.8)"
          fontSize="16"
          fontWeight="bold"
        >+</text>
      )}
      {/* Label */}
      {type !== 'branch' && (
        <text
          y={radius + 16}
          textAnchor="middle"
          fill="var(--text-secondary, #94a3b8)"
          fontSize="11"
          fontFamily="Inter, sans-serif"
          fontWeight="500"
        >
          {label?.length > 12 ? label.slice(0, 10) + '…' : label}
        </text>
      )}
      {/* Probeable indicator */}
      {probeable && !isProbed && (
        <circle
          r={3}
          cx={radius - 2}
          cy={-radius + 2}
          fill="var(--accent-color, #00d9ff)"
          opacity={0.6}
        />
      )}
    </g>
  );
}

// ============================================================================
// SFG Edge Component
// ============================================================================
function SFGEdge({ edge, nodes }) {
  const fromNode = nodes.find(n => n.id === edge.from);
  const toNode = nodes.find(n => n.id === edge.to);
  if (!fromNode || !toNode) return null;

  const x1 = fromNode.position?.x || 0;
  const y1 = fromNode.position?.y || 0;
  const x2 = toNode.position?.x || 0;
  const y2 = toNode.position?.y || 0;

  const dx = x2 - x1;
  const dy = y2 - y1;
  const dist = Math.sqrt(dx * dx + dy * dy);

  // Curve offset
  const curvature = edge.is_feedback
    ? Math.max(40, Math.min(80, dist * 0.25))
    : Math.max(20, Math.min(50, dist * 0.12));
  const curveDir = edge.is_feedback ? 1 : -1;

  // Control point for quadratic bezier
  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;
  // Perpendicular offset
  const nx = -dy / (dist || 1);
  const ny = dx / (dist || 1);
  const cx = mx + nx * curvature * curveDir;
  const cy = my + ny * curvature * curveDir;

  // Shorten path to stop at node edge
  const fromR = fromNode.type === 'branch' ? BRANCH_RADIUS : NODE_RADIUS;
  const toR = toNode.type === 'branch' ? BRANCH_RADIUS : NODE_RADIUS;

  const angle1 = Math.atan2(cy - y1, cx - x1);
  const sx = x1 + Math.cos(angle1) * fromR;
  const sy = y1 + Math.sin(angle1) * fromR;
  const angle2 = Math.atan2(cy - y2, cx - x2);
  const ex = x2 + Math.cos(angle2) * toR;
  const ey = y2 + Math.sin(angle2) * toR;

  const path = `M ${sx} ${sy} Q ${cx} ${cy} ${ex} ${ey}`;

  const edgeColor = edge.is_feedback
    ? 'var(--warning-color, #f59e0b)'
    : 'var(--accent-color, #00d9ff)';

  const isUnity = edge.gain_label === '1';
  const isNegative = edge.gain_label?.startsWith('-');

  // Label position at bezier midpoint (t=0.5)
  const lx = 0.25 * sx + 0.5 * cx + 0.25 * ex;
  const ly = 0.25 * sy + 0.5 * cy + 0.25 * ey;

  return (
    <g className={`sfs-edge ${isUnity ? 'sfs-edge-unity' : ''}`}>
      <path
        d={path}
        fill="none"
        stroke={edgeColor}
        strokeWidth={2}
        strokeLinecap="round"
        opacity={isUnity ? 0.3 : 0.7}
        markerEnd="url(#sfs-arrowhead)"
      />
      {/* Gain label */}
      {!isUnity && (
        <g transform={`translate(${lx}, ${ly})`}>
          <rect
            x={-20}
            y={-10}
            width={40}
            height={20}
            rx={6}
            fill="var(--surface-color, #131b2e)"
            stroke="var(--border-color, #1e293b)"
            strokeWidth={1}
            opacity={0.9}
          />
          <text
            textAnchor="middle"
            dominantBaseline="central"
            fill={isNegative ? 'var(--error-color, #ef4444)' : edgeColor}
            fontSize="11"
            fontFamily="'Fira Code', monospace"
            fontWeight="600"
          >
            {edge.gain_label?.length > 8 ? edge.gain_label.slice(0, 6) + '…' : edge.gain_label}
          </text>
        </g>
      )}
    </g>
  );
}

// ============================================================================
// Main Signal Flow Scope Viewer
// ============================================================================
function SignalFlowScopeViewer({ metadata, plots, currentParams, onParamChange, onMetadataChange, simId }) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);
  const [zoom, setZoom] = useState(1.0);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const svgRef = useRef(null);
  const panStart = useRef(null);

  // Extract data from metadata
  const sfgNodes = metadata?.sfg_nodes || [];
  const sfgEdges = metadata?.sfg_edges || [];
  const probes = metadata?.probes || [];
  const nodeTfs = metadata?.node_tfs || {};
  const diagramLoaded = metadata?.diagram_loaded || false;
  const systemType = metadata?.system_type || 'dt';
  const metaError = metadata?.error;

  // Build probe lookup
  const probedNodeIds = useMemo(() => {
    const set = new Set();
    probes.forEach(p => set.add(p.node_id));
    return set;
  }, [probes]);

  const probeColorMap = useMemo(() => {
    const map = {};
    probes.forEach(p => { map[p.node_id] = p.color; });
    return map;
  }, [probes]);

  // ========================================================================
  // API call helper
  // ========================================================================
  const callAction = useCallback(async (action, params = {}) => {
    setIsLoading(true);
    try {
      const result = await api.executeSimulation(simId, action, params);
      if (result.success && result.data) {
        const meta = result.data.metadata || result.metadata;
        if (meta && onMetadataChange) {
          onMetadataChange(meta);
        }
      } else if (result.error) {
        setError(result.error);
        setTimeout(() => setError(null), 5000);
      }
    } catch (e) {
      setError(e.message || 'Action failed');
      setTimeout(() => setError(null), 5000);
    } finally {
      setIsLoading(false);
    }
  }, [simId, onMetadataChange]);

  // ========================================================================
  // Import diagram
  // ========================================================================
  const handleImport = useCallback(() => {
    try {
      const stored = localStorage.getItem('sfs_diagram');
      if (!stored) {
        setToastMessage('No diagram found. Export from Block Diagram Builder first.');
        setTimeout(() => setToastMessage(null), 3000);
        return;
      }
      const diagramData = JSON.parse(stored);
      if (!diagramData.blocks || Object.keys(diagramData.blocks).length === 0) {
        setToastMessage('Exported diagram is empty.');
        setTimeout(() => setToastMessage(null), 3000);
        return;
      }
      callAction('import_diagram', diagramData);
      setToastMessage('Diagram imported successfully');
      setTimeout(() => setToastMessage(null), 2000);
    } catch (e) {
      setToastMessage('Failed to parse diagram data');
      setTimeout(() => setToastMessage(null), 3000);
    }
  }, [callAction]);

  // ========================================================================
  // Probe toggling
  // ========================================================================
  const handleToggleProbe = useCallback((nodeId) => {
    if (probedNodeIds.has(nodeId)) {
      callAction('remove_probe', { node_id: nodeId });
    } else if (probes.length < MAX_PROBES) {
      callAction('add_probe', { node_id: nodeId });
    }
  }, [callAction, probedNodeIds, probes.length]);

  const handleClearProbes = useCallback(() => {
    callAction('clear_probes', {});
  }, [callAction]);

  // ========================================================================
  // Zoom and pan
  // ========================================================================
  const handleWheel = useCallback((e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom(prev => Math.max(0.3, Math.min(3.0, prev * delta)));
  }, []);

  const handleMouseDown = useCallback((e) => {
    if (e.button === 1 || (e.button === 0 && e.ctrlKey)) {
      setIsPanning(true);
      panStart.current = { x: e.clientX - panOffset.x, y: e.clientY - panOffset.y };
      e.preventDefault();
    }
  }, [panOffset]);

  const handleMouseMove = useCallback((e) => {
    if (isPanning && panStart.current) {
      setPanOffset({
        x: e.clientX - panStart.current.x,
        y: e.clientY - panStart.current.y,
      });
    }
  }, [isPanning]);

  const handleMouseUp = useCallback(() => {
    setIsPanning(false);
    panStart.current = null;
  }, []);

  // Auto-fit viewport when diagram is loaded
  useEffect(() => {
    if (sfgNodes.length > 0) {
      const xs = sfgNodes.map(n => n.position?.x || 0);
      const ys = sfgNodes.map(n => n.position?.y || 0);
      const minX = Math.min(...xs) - 60;
      const maxX = Math.max(...xs) + 60;
      const minY = Math.min(...ys) - 60;
      const maxY = Math.max(...ys) + 60;
      const svgEl = svgRef.current;
      if (svgEl) {
        const rect = svgEl.getBoundingClientRect();
        const scaleX = rect.width / (maxX - minX);
        const scaleY = rect.height / (maxY - minY);
        const newZoom = Math.min(scaleX, scaleY, 1.5) * 0.85;
        setZoom(newZoom);
        const cx = (minX + maxX) / 2;
        const cy = (minY + maxY) / 2;
        setPanOffset({
          x: rect.width / 2 - cx * newZoom,
          y: rect.height / 2 - cy * newZoom,
        });
      }
    }
  }, [sfgNodes.length]); // Only re-fit when node count changes (new diagram)

  // Find scope and input plots
  const scopePlot = plots?.find(p => p.id === 'scope');
  const inputPlot = plots?.find(p => p.id === 'input_signal');

  // ========================================================================
  // Render
  // ========================================================================
  return (
    <div className="sfs-viewer">
      {/* Toolbar */}
      <div className="sfs-toolbar">
        <button
          className="sfs-import-btn"
          onClick={handleImport}
          disabled={isLoading}
        >
          Import Diagram
        </button>

        {diagramLoaded && (
          <>
            <div className="sfs-toolbar-divider" />
            <span className="sfs-toolbar-label">
              {systemType === 'dt' ? 'Discrete-Time' : 'Continuous-Time'}
            </span>
            <div className="sfs-toolbar-divider" />
            <span className="sfs-toolbar-label">
              Probes: {probes.length}/{MAX_PROBES}
            </span>
            {probes.length > 0 && (
              <button className="sfs-clear-btn" onClick={handleClearProbes}>
                Clear Probes
              </button>
            )}
          </>
        )}

        {isLoading && <span className="sfs-loading">Computing...</span>}
      </div>

      {/* Error display */}
      {(error || metaError) && (
        <div className="sfs-error">
          {error || metaError}
        </div>
      )}

      {/* Main content */}
      <div className="sfs-content">
        {!diagramLoaded ? (
          /* Empty state */
          <div className="sfs-empty-state">
            <div className="sfs-empty-icon">📡</div>
            <h3>Signal Flow Scope</h3>
            <p>Import a block diagram to get started.</p>
            <ol className="sfs-instructions">
              <li>Go to <strong>Block Diagram Builder</strong></li>
              <li>Build or load a diagram</li>
              <li>Click <strong>JSON</strong> to export</li>
              <li>Come back here and click <strong>Import Diagram</strong></li>
            </ol>
            <button className="sfs-import-btn sfs-import-btn-large" onClick={handleImport}>
              Import Diagram
            </button>
          </div>
        ) : (
          /* Loaded state: SFG + Plots */
          <div className="sfs-split-layout">
            {/* Left: Signal Flow Graph */}
            <div className="sfs-sfg-panel">
              <div className="sfs-sfg-header">
                <span>Signal Flow Graph</span>
                <span className="sfs-sfg-hint">Click a node to probe</span>
              </div>
              <svg
                ref={svgRef}
                className="sfs-sfg-canvas"
                width="100%"
                height="100%"
                onWheel={handleWheel}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
              >
                <defs>
                  <marker
                    id="sfs-arrowhead"
                    markerWidth={ARROW_SIZE}
                    markerHeight={ARROW_SIZE * 0.75}
                    refX={ARROW_SIZE}
                    refY={ARROW_SIZE * 0.375}
                    orient="auto"
                  >
                    <polygon
                      points={`0 0, ${ARROW_SIZE} ${ARROW_SIZE * 0.375}, 0 ${ARROW_SIZE * 0.75}`}
                      fill="var(--accent-color, #00d9ff)"
                      opacity="0.7"
                    />
                  </marker>
                </defs>

                {/* Grid */}
                <rect width="100%" height="100%" fill="var(--surface-color, #131b2e)" />

                <g transform={`translate(${panOffset.x}, ${panOffset.y}) scale(${zoom})`}>
                  {/* Edges */}
                  {sfgEdges.map((edge) => (
                    <SFGEdge key={edge.id} edge={edge} nodes={sfgNodes} />
                  ))}
                  {/* Nodes */}
                  {sfgNodes.map((node) => (
                    <SFGNode
                      key={node.id}
                      node={node}
                      onToggleProbe={handleToggleProbe}
                      isProbed={probedNodeIds.has(node.id)}
                      probeColor={probeColorMap[node.id]}
                    />
                  ))}
                </g>
              </svg>
            </div>

            {/* Right: Plots */}
            <div className="sfs-plots-panel">
              {/* Scope plot */}
              {scopePlot ? (
                <div className="sfs-plot-container">
                  <PlotDisplay
                    plots={[scopePlot]}
                    isDark={true}
                  />
                </div>
              ) : (
                <div className="sfs-plot-empty">
                  <p>Click nodes on the SFG to add probes</p>
                </div>
              )}

              {/* Input signal plot */}
              {inputPlot && (
                <div className="sfs-plot-container sfs-input-plot">
                  <PlotDisplay
                    plots={[inputPlot]}
                    isDark={true}
                  />
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Probe legend bar */}
      {probes.length > 0 && (
        <div className="sfs-probe-legend">
          {probes.map((probe) => {
            const tf = nodeTfs[probe.node_id];
            return (
              <div
                key={probe.id}
                className="sfs-probe-item"
                onClick={() => handleToggleProbe(probe.node_id)}
                title="Click to remove probe"
              >
                <span
                  className="sfs-probe-dot"
                  style={{ backgroundColor: probe.color }}
                />
                <span className="sfs-probe-label">{probe.label}</span>
                {tf?.expression?.operator && (
                  <span className="sfs-probe-tf">
                    H = {tf.expression.operator}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Toast */}
      {toastMessage && (
        <div className="sfs-toast">
          {toastMessage}
        </div>
      )}

      <style>{`
        .sfs-viewer {
          display: flex;
          flex-direction: column;
          height: 100%;
          min-height: 500px;
          position: relative;
          background: var(--background-color, #0a0e27);
          border-radius: var(--radius-lg, 12px);
          overflow: hidden;
        }

        .sfs-toolbar {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 8px 14px;
          background: var(--surface-color, #131b2e);
          border-bottom: 1px solid var(--border-color, #1e293b);
          flex-shrink: 0;
        }

        .sfs-toolbar-divider {
          width: 1px;
          height: 20px;
          background: var(--border-color, #1e293b);
        }

        .sfs-toolbar-label {
          font-size: 12px;
          color: var(--text-secondary, #94a3b8);
          font-weight: 500;
        }

        .sfs-import-btn {
          padding: 6px 14px;
          border: 1px solid var(--primary-color, #14b8a6);
          background: var(--primary-light, rgba(20, 184, 166, 0.1));
          color: var(--primary-color, #14b8a6);
          border-radius: var(--radius-md, 8px);
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
          transition: all var(--transition-fast, 150ms);
        }
        .sfs-import-btn:hover {
          background: var(--primary-color, #14b8a6);
          color: #fff;
        }
        .sfs-import-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .sfs-import-btn-large {
          padding: 10px 24px;
          font-size: 14px;
        }

        .sfs-clear-btn {
          padding: 4px 10px;
          border: 1px solid var(--border-color, #1e293b);
          background: transparent;
          color: var(--text-muted, #64748b);
          border-radius: var(--radius-sm, 6px);
          font-size: 11px;
          cursor: pointer;
          transition: all var(--transition-fast, 150ms);
        }
        .sfs-clear-btn:hover {
          border-color: var(--error-color, #ef4444);
          color: var(--error-color, #ef4444);
        }

        .sfs-loading {
          font-size: 12px;
          color: var(--primary-color, #14b8a6);
          animation: sfs-pulse 1.5s ease-in-out infinite;
        }
        @keyframes sfs-pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }

        .sfs-error {
          padding: 8px 14px;
          background: rgba(239, 68, 68, 0.1);
          border-bottom: 1px solid rgba(239, 68, 68, 0.3);
          color: var(--error-color, #ef4444);
          font-size: 12px;
        }

        .sfs-content {
          flex: 1;
          overflow: hidden;
        }

        .sfs-empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100%;
          padding: 40px;
          text-align: center;
          color: var(--text-secondary, #94a3b8);
        }
        .sfs-empty-icon {
          font-size: 48px;
          margin-bottom: 16px;
        }
        .sfs-empty-state h3 {
          font-size: 20px;
          color: var(--text-primary, #f1f5f9);
          margin: 0 0 8px 0;
        }
        .sfs-empty-state p {
          margin: 0 0 20px 0;
          font-size: 14px;
        }
        .sfs-instructions {
          text-align: left;
          margin: 0 0 24px 0;
          padding-left: 20px;
          font-size: 13px;
          line-height: 1.8;
          color: var(--text-muted, #64748b);
        }
        .sfs-instructions strong {
          color: var(--text-secondary, #94a3b8);
        }

        .sfs-split-layout {
          display: grid;
          grid-template-columns: 1fr 1fr;
          height: 100%;
          gap: 0;
        }

        .sfs-sfg-panel {
          display: flex;
          flex-direction: column;
          border-right: 1px solid var(--border-color, #1e293b);
          overflow: hidden;
        }

        .sfs-sfg-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 6px 12px;
          background: var(--surface-color, #131b2e);
          border-bottom: 1px solid var(--border-color, #1e293b);
          font-size: 12px;
          font-weight: 600;
          color: var(--text-primary, #f1f5f9);
        }
        .sfs-sfg-hint {
          font-size: 11px;
          font-weight: 400;
          color: var(--text-muted, #64748b);
        }

        .sfs-sfg-canvas {
          flex: 1;
          cursor: grab;
        }
        .sfs-sfg-canvas:active {
          cursor: grabbing;
        }

        .sfs-node-probeable:hover circle:first-of-type {
          filter: brightness(1.3);
        }
        .sfs-probe-ring {
          animation: sfs-probe-glow 2s ease-in-out infinite;
        }
        @keyframes sfs-probe-glow {
          0%, 100% { opacity: 0.4; }
          50% { opacity: 0.7; }
        }

        .sfs-edge-unity {
          opacity: 0.3;
        }

        .sfs-plots-panel {
          display: flex;
          flex-direction: column;
          overflow-y: auto;
        }

        .sfs-plot-container {
          flex: 1;
          min-height: 200px;
          padding: 8px;
        }
        .sfs-input-plot {
          flex: 0.6;
          border-top: 1px solid var(--border-color, #1e293b);
        }

        .sfs-plot-empty {
          display: flex;
          align-items: center;
          justify-content: center;
          flex: 1;
          color: var(--text-muted, #64748b);
          font-size: 14px;
        }

        .sfs-probe-legend {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          padding: 8px 14px;
          background: var(--surface-color, #131b2e);
          border-top: 1px solid var(--border-color, #1e293b);
          flex-shrink: 0;
        }

        .sfs-probe-item {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 4px 10px;
          border: 1px solid var(--border-color, #1e293b);
          border-radius: var(--radius-full, 9999px);
          cursor: pointer;
          transition: all var(--transition-fast, 150ms);
          font-size: 11px;
        }
        .sfs-probe-item:hover {
          border-color: var(--error-color, #ef4444);
          background: rgba(239, 68, 68, 0.05);
        }

        .sfs-probe-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          flex-shrink: 0;
        }

        .sfs-probe-label {
          color: var(--text-primary, #f1f5f9);
          font-weight: 500;
        }

        .sfs-probe-tf {
          color: var(--text-muted, #64748b);
          font-family: 'Fira Code', monospace;
          font-size: 10px;
          max-width: 200px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .sfs-toast {
          position: absolute;
          bottom: 60px;
          left: 50%;
          transform: translateX(-50%);
          background: var(--surface-color, #131b2e);
          border: 1px solid var(--primary-color, #14b8a6);
          border-radius: var(--radius-md, 8px);
          padding: 8px 16px;
          color: var(--text-primary, #f1f5f9);
          font-size: 13px;
          z-index: 100;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
          pointer-events: none;
        }

        @media (max-width: 768px) {
          .sfs-split-layout {
            grid-template-columns: 1fr;
            grid-template-rows: 1fr 1fr;
          }
          .sfs-sfg-panel {
            border-right: none;
            border-bottom: 1px solid var(--border-color, #1e293b);
          }
        }
      `}</style>
    </div>
  );
}

export default SignalFlowScopeViewer;
