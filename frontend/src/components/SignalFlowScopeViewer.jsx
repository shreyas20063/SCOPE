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
// Helpers
// ============================================================================
function friendlyNodeType(type, blockType) {
  const typeMap = { source: 'Input Signal', sink: 'Output Signal', sum: 'Adder', branch: 'Junction' };
  if (typeMap[type]) return typeMap[type];
  const btMap = { gain: 'Gain Block', delay: 'Delay', integrator: 'Integrator', custom_tf: 'Transfer Function' };
  return btMap[blockType] || 'Signal Node';
}

// ============================================================================
// SFG Node Component
// ============================================================================
function SFGNode({ node, onToggleProbe, isProbed, probeColor, onNodeHover }) {
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
      onMouseEnter={probeable && onNodeHover ? () => onNodeHover(node) : undefined}
      onMouseLeave={onNodeHover ? () => onNodeHover(null) : undefined}
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
  const [hoveredNode, setHoveredNode] = useState(null);
  const svgRef = useRef(null);
  const sfgPanelRef = useRef(null);
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

  const handleZoomIn = useCallback(() => {
    setZoom(prev => Math.min(3.0, prev * 1.2));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoom(prev => Math.max(0.3, prev / 1.2));
  }, []);

  const handleResetView = useCallback(() => {
    setZoom(1.0);
    setPanOffset({ x: 0, y: 0 });
  }, []);

  const handleNodeHover = useCallback((node) => {
    if (!node) {
      setHoveredNode(null);
      return;
    }
    const panel = sfgPanelRef.current;
    if (!panel) return;
    const rect = panel.getBoundingClientRect();
    const x = (node.position?.x || 0) * zoom + panOffset.x;
    const y = (node.position?.y || 0) * zoom + panOffset.y;
    // Offset for the SFG header height (~33px)
    const headerOffset = 33;
    setHoveredNode({ node, x, y: y + headerOffset });
  }, [zoom, panOffset]);

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
            <span className="sfs-system-badge" data-type={systemType}>
              {systemType === 'dt' ? 'Discrete-Time' : 'Continuous-Time'}
            </span>
            <div className="sfs-toolbar-divider" />
            <span className="sfs-toolbar-stats">
              {sfgNodes.length} nodes &middot; {sfgEdges.length} edges
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
            <div className="sfs-sfg-panel" ref={sfgPanelRef}>
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
                      onNodeHover={handleNodeHover}
                    />
                  ))}
                </g>
              </svg>

              {/* Node tooltip */}
              {hoveredNode && (() => {
                const tf = nodeTfs[hoveredNode.node.id];
                const showAbove = hoveredNode.y > 100;
                return (
                  <div
                    className="sfs-node-tooltip"
                    style={{
                      left: hoveredNode.x,
                      top: showAbove ? hoveredNode.y - 10 : hoveredNode.y + 30,
                      transform: showAbove ? 'translate(-50%, -100%)' : 'translateX(-50%)',
                    }}
                  >
                    <div className="sfs-tooltip-label">{hoveredNode.node.label}</div>
                    <div className="sfs-tooltip-type">
                      {friendlyNodeType(hoveredNode.node.type, hoveredNode.node.block_type)}
                    </div>
                    {tf?.expression && (
                      <>
                        <div className="sfs-tooltip-tf-header">Transfer Function</div>
                        <div className="sfs-tooltip-tf">{tf.expression.operator}</div>
                        <div className="sfs-tooltip-tf sfs-tooltip-tf-domain">{tf.expression.domain}</div>
                      </>
                    )}
                  </div>
                );
              })()}

              {/* Zoom/Pan controls */}
              <div className="sfs-view-controls">
                <button className="sfs-view-btn" onClick={handleZoomIn} title="Zoom in">+</button>
                <button className="sfs-view-btn" onClick={handleZoomOut} title="Zoom out">&minus;</button>
                <button className="sfs-view-btn sfs-view-btn-reset" onClick={handleResetView} title="Reset view">&#x27F2;</button>
                <span className="sfs-view-hint">Scroll: Zoom &middot; Ctrl+Drag: Pan</span>
              </div>
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
            const domainVar = systemType === 'dt' ? 'z' : 's';
            const domainExpr = tf?.expression?.domain;
            const fullExpr = domainExpr ? `H(${domainVar}) = ${domainExpr}` : null;
            return (
              <div key={probe.id} className="sfs-probe-item">
                <span
                  className="sfs-probe-dot"
                  style={{ backgroundColor: probe.color }}
                />
                <span className="sfs-probe-label">{probe.label}</span>
                {fullExpr && (
                  <span className="sfs-probe-tf" title={fullExpr}>
                    {fullExpr}
                  </span>
                )}
                {fullExpr && (
                  <button
                    className="sfs-probe-copy-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigator.clipboard.writeText(fullExpr);
                      setToastMessage('TF copied to clipboard');
                      setTimeout(() => setToastMessage(null), 1500);
                    }}
                    title="Copy transfer function"
                  >&#x2398;</button>
                )}
                <button
                  className="sfs-probe-remove-btn"
                  onClick={() => handleToggleProbe(probe.node_id)}
                  title="Remove probe"
                >&times;</button>
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

        .sfs-system-badge {
          display: inline-flex;
          align-items: center;
          padding: 2px 10px;
          border-radius: var(--radius-full, 9999px);
          font-size: 11px;
          font-weight: 600;
          letter-spacing: 0.3px;
        }
        .sfs-system-badge[data-type="dt"] {
          background: rgba(59, 130, 246, 0.12);
          color: var(--secondary-color, #3b82f6);
          border: 1px solid rgba(59, 130, 246, 0.25);
        }
        .sfs-system-badge[data-type="ct"] {
          background: rgba(16, 185, 129, 0.12);
          color: var(--success-color, #10b981);
          border: 1px solid rgba(16, 185, 129, 0.25);
        }

        .sfs-toolbar-stats {
          font-size: 11px;
          color: var(--text-muted, #64748b);
          font-family: 'Fira Code', monospace;
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
          position: relative;
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
          transition: all var(--transition-fast, 150ms);
          font-size: 11px;
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
          max-width: 280px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .sfs-probe-copy-btn {
          background: none;
          border: 1px solid var(--border-color, #1e293b);
          color: var(--text-muted, #64748b);
          border-radius: var(--radius-sm, 6px);
          cursor: pointer;
          padding: 1px 5px;
          font-size: 12px;
          line-height: 1;
          transition: all var(--transition-fast, 150ms);
          flex-shrink: 0;
        }
        .sfs-probe-copy-btn:hover {
          border-color: var(--primary-color, #14b8a6);
          color: var(--primary-color, #14b8a6);
        }

        .sfs-probe-remove-btn {
          background: none;
          border: none;
          color: var(--text-muted, #64748b);
          cursor: pointer;
          font-size: 14px;
          line-height: 1;
          padding: 0 2px;
          flex-shrink: 0;
          transition: color var(--transition-fast, 150ms);
        }
        .sfs-probe-remove-btn:hover {
          color: var(--error-color, #ef4444);
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

        .sfs-node-tooltip {
          position: absolute;
          z-index: 50;
          background: rgba(19, 27, 46, 0.92);
          backdrop-filter: blur(12px);
          border: 1px solid var(--border-hover, #334155);
          border-radius: var(--radius-md, 8px);
          padding: 10px 14px;
          pointer-events: none;
          min-width: 180px;
          max-width: 320px;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        }
        .sfs-tooltip-label {
          font-size: 13px;
          font-weight: 600;
          color: var(--text-primary, #f1f5f9);
          margin-bottom: 2px;
        }
        .sfs-tooltip-type {
          font-size: 11px;
          color: var(--text-muted, #64748b);
          margin-bottom: 8px;
        }
        .sfs-tooltip-tf-header {
          font-size: 10px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          color: var(--text-muted, #64748b);
          margin-bottom: 4px;
        }
        .sfs-tooltip-tf {
          font-family: 'Fira Code', monospace;
          font-size: 11px;
          color: var(--accent-color, #00d9ff);
          word-break: break-all;
          line-height: 1.5;
        }
        .sfs-tooltip-tf-domain {
          color: var(--text-secondary, #94a3b8);
        }

        .sfs-view-controls {
          position: absolute;
          bottom: 10px;
          right: 10px;
          display: flex;
          align-items: center;
          gap: 4px;
          z-index: 10;
        }
        .sfs-view-btn {
          width: 28px;
          height: 28px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(19, 27, 46, 0.85);
          backdrop-filter: blur(8px);
          border: 1px solid var(--border-color, #1e293b);
          border-radius: var(--radius-sm, 6px);
          color: var(--text-secondary, #94a3b8);
          font-size: 16px;
          cursor: pointer;
          transition: all var(--transition-fast, 150ms);
        }
        .sfs-view-btn:hover {
          border-color: var(--primary-color, #14b8a6);
          color: var(--primary-color, #14b8a6);
          background: rgba(19, 27, 46, 0.95);
        }
        .sfs-view-btn-reset {
          font-size: 14px;
        }
        .sfs-view-hint {
          font-size: 10px;
          color: var(--text-muted, #64748b);
          background: rgba(19, 27, 46, 0.7);
          padding: 4px 8px;
          border-radius: var(--radius-sm, 6px);
          margin-left: 4px;
          white-space: nowrap;
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
