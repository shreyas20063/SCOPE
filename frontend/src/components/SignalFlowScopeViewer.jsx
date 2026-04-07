import React, { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import api from '../services/api';
import Plot from 'react-plotly.js';
import useHub from '../hooks/useHub';

// ============================================================================
// Constants
// ============================================================================
const PROBE_COLORS = ['#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899'];
const MAX_PROBES = 6;
const NODE_RADIUS = 18;
const BRANCH_RADIUS = 6;
const ARROW_SIZE = 8;
const PAN_THRESHOLD = 4; // px — must drag this far before it counts as pan

const SIGNAL_OPTIONS = [
  { value: 'impulse', label: 'Impulse' },
  { value: 'step', label: 'Step' },
  { value: 'sinusoid', label: 'Sinusoid' },
  { value: 'ramp', label: 'Ramp' },
  { value: 'square', label: 'Square' },
  { value: 'sawtooth', label: 'Sawtooth' },
  { value: 'triangle', label: 'Triangle' },
  { value: 'chirp', label: 'Chirp' },
  { value: 'white_noise', label: 'Noise' },
];

const FREQ_SIGNALS = new Set(['sinusoid', 'square', 'sawtooth', 'triangle', 'chirp']);

// Theme-aware plot colors
function usePlotTheme() {
  const [isDark, setIsDark] = React.useState(
    () => document.documentElement.getAttribute('data-theme') !== 'light'
  );
  React.useEffect(() => {
    const obs = new MutationObserver(() =>
      setIsDark(document.documentElement.getAttribute('data-theme') !== 'light')
    );
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => obs.disconnect();
  }, []);
  return isDark ? {
    PLOT_BG: '#131b2e', PLOT_PAPER: '#0a0e27',
    PLOT_GRID: 'rgba(148,163,184,0.08)', PLOT_ZERO: 'rgba(148,163,184,0.2)',
    PLOT_TEXT: '#94a3b8', BORDER: '#1e293b', SHADOW: 'rgba(0,0,0,0.5)',
    TEXT_PRIMARY: '#e2e8f0', TEXT_MUTED: '#475569',
  } : {
    PLOT_BG: '#eaf0f8', PLOT_PAPER: '#f0f4fa',
    PLOT_GRID: 'rgba(37,99,235,0.08)', PLOT_ZERO: 'rgba(37,99,235,0.15)',
    PLOT_TEXT: '#3b4963', BORDER: '#bec9db', SHADOW: 'rgba(15,23,42,0.12)',
    TEXT_PRIMARY: '#0c1425', TEXT_MUTED: '#4a5d78',
  };
}

// Legacy constants (used by sub-components that don't have theme access)
const PLOT_BG = '#131b2e';
const PLOT_PAPER = '#0a0e27';
const PLOT_GRID = 'rgba(148,163,184,0.08)';
const PLOT_ZERO = 'rgba(148,163,184,0.2)';
const PLOT_TEXT = '#94a3b8';

// ============================================================================
// SFG Node Component
// ============================================================================
function SFGNode({ node, onToggleProbe, isProbed, probeColor, theme }) {
  const { id, type, label, position, probeable } = node;
  const x = position?.x || 0;
  const y = position?.y || 0;
  const radius = type === 'branch' ? BRANCH_RADIUS : NODE_RADIUS;

  let fill, stroke;
  if (isProbed) {
    fill = `${probeColor}22`;
    stroke = probeColor;
  } else {
    switch (type) {
      case 'source': case 'sink':
        fill = 'rgba(20, 184, 166, 0.15)'; stroke = '#14b8a6'; break;
      case 'sum':
        fill = 'rgba(245, 158, 11, 0.12)'; stroke = '#f59e0b'; break;
      case 'branch':
        fill = 'rgba(148, 163, 184, 0.5)'; stroke = '#94a3b8'; break;
      default:
        fill = 'rgba(59, 130, 246, 0.1)'; stroke = '#3b82f6';
    }
  }

  const handleClick = useCallback((e) => {
    e.stopPropagation(); // prevent pan from eating this
    if (probeable) onToggleProbe(id);
  }, [probeable, onToggleProbe, id]);

  return (
    <g
      className={`sfs-node ${probeable ? 'sfs-node-probeable' : ''}`}
      transform={`translate(${x}, ${y})`}
      onMouseDown={(e) => e.stopPropagation()} // don't let SVG pan start
      onClick={handleClick}
      style={{ cursor: probeable ? 'pointer' : 'default' }}
    >
      {isProbed && (
        <circle r={radius + 7} fill="none" stroke={probeColor} strokeWidth={2} opacity={0.35}
          style={{ animation: 'sfs-glow 2s ease-in-out infinite' }} />
      )}
      <circle r={radius} fill={fill} stroke={stroke} strokeWidth={type === 'branch' ? 1.5 : 2} />
      {type === 'sum' && (
        <text textAnchor="middle" dominantBaseline="central" fill="#f59e0b" fontSize="16" fontWeight="bold">+</text>
      )}
      {type !== 'branch' && (
        <text y={radius + 15} textAnchor="middle" fill={theme?.TEXT_PRIMARY || '#94a3b8'} fontSize="10" fontFamily="Inter, sans-serif" fontWeight="500">
          {label?.length > 14 ? label.slice(0, 12) + '…' : label}
        </text>
      )}
      {probeable && !isProbed && (
        <circle r={3} cx={radius - 2} cy={-radius + 2} fill={theme?.PLOT_TEXT || '#00d9ff'} opacity={0.7} />
      )}
    </g>
  );
}

// ============================================================================
// SFG Edge Component
// ============================================================================
function SFGEdge({ edge, nodes, theme }) {
  const fromNode = nodes.find(n => n.id === edge.from);
  const toNode = nodes.find(n => n.id === edge.to);
  if (!fromNode || !toNode) return null;

  const x1 = fromNode.position?.x || 0, y1 = fromNode.position?.y || 0;
  const x2 = toNode.position?.x || 0, y2 = toNode.position?.y || 0;
  const isSelfLoop = edge.from === edge.to;

  const edgeColor = edge.is_feedback ? '#f59e0b' : (theme?.PLOT_TEXT === '#3b4963' ? '#0284c7' : '#00d9ff');
  const isUnity = edge.gain_label === '1';
  const isNegative = edge.gain_label?.startsWith('-');
  const labelBg = theme?.PLOT_PAPER || PLOT_BG;
  const labelBorder = theme?.BORDER || '#1e293b';
  const displayLabel = edge.gain_label || '1';
  const labelLen = displayLabel.length;
  const boxW = Math.max(44, labelLen * 7 + 16);

  // Self-loop: draw a circle above the node
  if (isSelfLoop) {
    const r = fromNode.type === 'branch' ? BRANCH_RADIUS : NODE_RADIUS;
    const loopR = 30;
    const loopCy = y1 - r - loopR - 5;
    // Cubic bezier that forms a loop above the node
    const path = `M ${x1 - r} ${y1 - 2} C ${x1 - r - loopR} ${loopCy - loopR}, ${x1 + r + loopR} ${loopCy - loopR}, ${x1 + r} ${y1 - 2}`;
    const labelY = loopCy - loopR + 5;

    return (
      <g>
        <path d={path} fill="none" stroke={edgeColor} strokeWidth={2} strokeLinecap="round"
          opacity={0.8} markerEnd="url(#sfs-arrow)" />
        {!isUnity && (
          <g transform={`translate(${x1}, ${labelY})`}>
            <rect x={-boxW / 2} y={-12} width={boxW} height={24} rx={6}
              fill={labelBg} stroke={labelBorder} strokeWidth={1} opacity={0.95} />
            <text textAnchor="middle" dominantBaseline="central"
              fill={isNegative ? '#ef4444' : edgeColor}
              fontSize="11" fontFamily="'Fira Code', monospace" fontWeight="600">
              {displayLabel}
            </text>
          </g>
        )}
      </g>
    );
  }

  // Normal edge
  const dx = x2 - x1, dy = y2 - y1;
  const dist = Math.sqrt(dx * dx + dy * dy);

  const curvature = edge.is_feedback
    ? Math.max(40, Math.min(80, dist * 0.25))
    : Math.max(15, Math.min(45, dist * 0.1));
  const curveDir = edge.is_feedback ? 1 : -1;

  const mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
  const nx = -dy / (dist || 1), ny = dx / (dist || 1);
  const cx = mx + nx * curvature * curveDir;
  const cy = my + ny * curvature * curveDir;

  const fromR = fromNode.type === 'branch' ? BRANCH_RADIUS : NODE_RADIUS;
  const toR = toNode.type === 'branch' ? BRANCH_RADIUS : NODE_RADIUS;
  const angle1 = Math.atan2(cy - y1, cx - x1);
  const sx = x1 + Math.cos(angle1) * fromR, sy = y1 + Math.sin(angle1) * fromR;
  const angle2 = Math.atan2(cy - y2, cx - x2);
  const ex = x2 + Math.cos(angle2) * toR, ey = y2 + Math.sin(angle2) * toR;

  const path = `M ${sx} ${sy} Q ${cx} ${cy} ${ex} ${ey}`;
  const lx = 0.25 * sx + 0.5 * cx + 0.25 * ex;
  const ly = 0.25 * sy + 0.5 * cy + 0.25 * ey;

  return (
    <g>
      <path d={path} fill="none" stroke={edgeColor} strokeWidth={2} strokeLinecap="round"
        opacity={isUnity ? 0.3 : 0.8} markerEnd="url(#sfs-arrow)" />
      {!isUnity && (
        <g transform={`translate(${lx}, ${ly})`}>
          <rect x={-boxW / 2} y={-12} width={boxW} height={24} rx={6}
            fill={labelBg} stroke={labelBorder} strokeWidth={1} opacity={0.95} />
          <text textAnchor="middle" dominantBaseline="central"
            fill={isNegative ? '#ef4444' : edgeColor}
            fontSize="11" fontFamily="'Fira Code', monospace" fontWeight="600">
            {displayLabel}
          </text>
        </g>
      )}
    </g>
  );
}

// ============================================================================
// Signal Plot Card — uses raw hex colors for Plotly
// ============================================================================
function SignalPlotCard({ title, color, time, values, stats, systemType, xLabel, theme }) {
  if (!time || !values || values.length === 0) return null;
  const P = theme || { PLOT_BG, PLOT_PAPER, PLOT_GRID, PLOT_ZERO, PLOT_TEXT };

  const mode = systemType === 'dt' ? 'markers+lines' : 'lines';
  const data = useMemo(() => [{
    x: time, y: values, type: 'scatter', mode, name: title,
    line: { color, width: 2 },
    ...(systemType === 'dt' ? { marker: { color, size: 3 } } : {}),
  }], [time, values, mode, title, color, systemType]);

  const layout = useMemo(() => ({
    paper_bgcolor: P.PLOT_PAPER,
    plot_bgcolor: P.PLOT_BG,
    font: { family: 'Inter, sans-serif', size: 11, color: P.PLOT_TEXT },
    margin: { t: 6, r: 10, b: 32, l: 44 },
    xaxis: { title: { text: xLabel, font: { size: 10 }, standoff: 4 }, gridcolor: P.PLOT_GRID, zerolinecolor: P.PLOT_ZERO, color: P.PLOT_TEXT },
    yaxis: { gridcolor: P.PLOT_GRID, zerolinecolor: P.PLOT_ZERO, color: P.PLOT_TEXT, autorange: true },
    showlegend: false,
    autosize: true,
    datarevision: `${title}-${values.length}-${values[0]?.toFixed?.(6) ?? 0}-${values[Math.floor(values.length / 2)]?.toFixed?.(6) ?? 0}-${values[values.length - 1]?.toFixed?.(6) ?? 0}`,
    uirevision: title,
  }), [title, xLabel, values, P]);

  return (
    <div className="sfs-plot-card">
      <div className="sfs-plot-card-hdr">
        <span className="sfs-plot-dot" style={{ backgroundColor: color }} />
        <span className="sfs-plot-title">{title}</span>
        {stats && (
          <span className="sfs-plot-stats">
            RMS {stats.rms?.toFixed(3)} | Peak {stats.peak?.toFixed(3)} | Mean {stats.mean?.toFixed(3)}
          </span>
        )}
      </div>
      <div className="sfs-plot-body">
        <Plot data={data} layout={layout}
          config={{ responsive: true, displayModeBar: false, scrollZoom: true }}
          useResizeHandler style={{ width: '100%', height: '100%' }} />
      </div>
    </div>
  );
}

// ============================================================================
// Overlay Plot
// ============================================================================
function OverlayPlot({ signals, systemType, xLabel, theme }) {
  if (!signals || signals.length === 0) return null;
  const time = signals[0]?.time;
  if (!time) return null;
  const P = theme || { PLOT_BG, PLOT_PAPER, PLOT_GRID, PLOT_ZERO, PLOT_TEXT, TEXT_PRIMARY: '#e2e8f0' };

  const data = useMemo(() => signals.map(s => ({
    x: time, y: s.values, type: 'scatter',
    mode: systemType === 'dt' ? 'markers+lines' : 'lines',
    name: s.label, line: { color: s.color, width: 2 },
    ...(systemType === 'dt' ? { marker: { color: s.color, size: 3 } } : {}),
  })), [signals, time, systemType]);

  const layout = useMemo(() => ({
    paper_bgcolor: P.PLOT_PAPER, plot_bgcolor: P.PLOT_BG,
    font: { family: 'Inter, sans-serif', size: 11, color: P.PLOT_TEXT },
    margin: { t: 6, r: 10, b: 32, l: 44 },
    xaxis: { title: { text: xLabel, font: { size: 10 } }, gridcolor: P.PLOT_GRID, zerolinecolor: P.PLOT_ZERO, color: P.PLOT_TEXT },
    yaxis: { gridcolor: P.PLOT_GRID, zerolinecolor: P.PLOT_ZERO, color: P.PLOT_TEXT, autorange: true },
    legend: { x: 0.01, y: 0.99, bgcolor: P.PLOT_BG, font: { size: 10, color: P.TEXT_PRIMARY } },
    showlegend: true, autosize: true,
    datarevision: `overlay-${signals.length}-${signals.map(s => `${s.values?.[0]?.toFixed?.(6) ?? 0}_${s.values?.[Math.floor((s.values?.length || 0) / 2)]?.toFixed?.(6) ?? 0}`).join(',')}`,
    uirevision: 'overlay',
  }), [signals, xLabel, P]);

  return (
    <div className="sfs-plot-card sfs-plot-overlay">
      <div className="sfs-plot-card-hdr">
        <span className="sfs-plot-title">All Signals (Overlay)</span>
      </div>
      <div className="sfs-plot-body sfs-plot-body-tall">
        <Plot data={data} layout={layout}
          config={{ responsive: true, displayModeBar: false, scrollZoom: true }}
          useResizeHandler style={{ width: '100%', height: '100%' }} />
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================
function SignalFlowScopeViewer({ metadata, plots, currentParams, onParamChange, onMetadataChange, simId }) {
  const T = usePlotTheme();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);
  const [zoom, setZoom] = useState(1.0);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [showPresets, setShowPresets] = useState(false);
  const [overlayMode, setOverlayMode] = useState(false);
  const [visiblePlots, setVisiblePlots] = useState({ input: true, output: true });

  const svgRef = useRef(null);
  const dragRef = useRef(null);       // { startX, startY, panX, panY, dragging }
  const presetsRef = useRef(null);
  const autoImportDone = useRef(false);
  const lastHubTimestampRef = useRef(0);

  // Hub subscription — SFS pulls block_diagram payloads from the control slot.
  const { slotData: hubSlotData, hubUpdated } = useHub('control');

  // Extract metadata
  const sfgNodes = metadata?.sfg_nodes || [];
  const sfgEdges = metadata?.sfg_edges || [];
  const probes = metadata?.probes || [];
  const nodeTfs = metadata?.node_tfs || {};
  const diagramLoaded = metadata?.diagram_loaded || false;
  const systemType = metadata?.system_type || 'dt';
  const metaError = metadata?.error;
  const signals = metadata?.signals || {};
  const presetList = metadata?.presets || [];

  // Current params
  const inputType = currentParams?.input_type || 'impulse';
  const inputFreq = currentParams?.input_freq ?? 1.0;
  const inputAmplitude = currentParams?.input_amplitude ?? 1.0;
  const numSamples = currentParams?.num_samples ?? 100;
  const dutyCycle = currentParams?.duty_cycle ?? 0.5;
  const chirpEndFreq = currentParams?.chirp_end_freq ?? 20.0;
  const xLabel = systemType === 'dt' ? 'n (samples)' : 'Time (s)';

  // Stagger nodes vertically when layout is nearly flat (all same y)
  // Also add horizontal breathing room between nodes that are too close
  const layoutNodes = useMemo(() => {
    if (sfgNodes.length < 2) return sfgNodes;
    const ys = sfgNodes.map(n => n.position?.y || 0);
    const yRange = Math.max(...ys) - Math.min(...ys);

    if (yRange >= 60) return sfgNodes;

    const centerY = (Math.max(...ys) + Math.min(...ys)) / 2;
    // Sort by x to get left-to-right order
    const sorted = [...sfgNodes].sort((a, b) => (a.position?.x || 0) - (b.position?.x || 0));

    // Ensure minimum horizontal spacing between consecutive nodes
    const minGap = 160;
    const stagger = 80;
    const adjusted = [];
    for (let i = 0; i < sorted.length; i++) {
      const n = sorted[i];
      const prevX = i > 0 ? adjusted[i - 1].position.x : -Infinity;
      const rawX = n.position?.x || 0;
      adjusted.push({
        ...n,
        position: {
          x: Math.max(rawX, prevX + minGap),
          y: centerY + (i % 2 === 0 ? -stagger : stagger),
        },
      });
    }

    return adjusted;
  }, [sfgNodes]);

  // Probe lookup
  const probedNodeIds = useMemo(() => new Set(probes.map(p => p.node_id)), [probes]);
  const probeColorMap = useMemo(() => {
    const m = {};
    probes.forEach(p => { m[p.node_id] = p.color; });
    return m;
  }, [probes]);

  // Track visible plots for probes
  useEffect(() => {
    setVisiblePlots(prev => {
      const next = { input: prev.input ?? true, output: prev.output ?? true };
      probes.forEach(p => { next[p.id] = p.id in prev ? prev[p.id] : true; });
      return next;
    });
  }, [probes]);

  // Toast helper
  const showToast = useCallback((msg, ms = 2500) => {
    setToast(msg);
    setTimeout(() => setToast(null), ms);
  }, []);

  // ========================================================================
  // API
  // ========================================================================
  const callAction = useCallback(async (action, params = {}) => {
    setIsLoading(true);
    try {
      const result = await api.executeSimulation(simId, action, params);
      if (result.success && result.data) {
        const meta = result.data.metadata || result.metadata;
        if (meta && onMetadataChange) onMetadataChange(meta);
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
  // Import & presets
  // ========================================================================

  // Extract a {blocks, connections, system_type} payload from hub slot data,
  // or null if the slot has no usable block_diagram. Falls back to the legacy
  // localStorage 'sfs_diagram' channel for diagrams exported via BDB's
  // "Export to Signal Scope" button (kept for backward compatibility).
  const readDiagramSource = useCallback(() => {
    if (hubSlotData && hubSlotData.block_diagram) {
      const bd = hubSlotData.block_diagram;
      if (bd.blocks && Object.keys(bd.blocks).length > 0) {
        return {
          blocks: bd.blocks,
          connections: bd.connections || [],
          system_type: hubSlotData.domain === 'dt' ? 'dt' : 'ct',
          source: 'hub',
        };
      }
    }
    const stored = localStorage.getItem('sfs_diagram');
    if (!stored) return null;
    try {
      const d = JSON.parse(stored);
      if (!d.blocks || Object.keys(d.blocks).length === 0) return null;
      return { ...d, source: 'localStorage' };
    } catch {
      return null;
    }
  }, [hubSlotData]);

  const handleImport = useCallback(() => {
    const d = readDiagramSource();
    if (!d) {
      showToast('No diagram in hub or localStorage — push from Block Diagram Builder first.', 3000);
      return;
    }
    callAction('import_diagram', { blocks: d.blocks, connections: d.connections, system_type: d.system_type });
    showToast(d.source === 'hub' ? 'Imported from System Hub!' : 'Imported from local export!');
  }, [readDiagramSource, callAction, showToast]);

  // Auto-import on mount (prefer hub) and on subsequent hub updates
  // (cross-tab pushes or in-app pushes from BDB while SFS stays mounted).
  useEffect(() => {
    // Re-import only when the hub timestamp actually advances. Without this
    // guard the effect would re-run on every render that touches hubSlotData.
    const ts = hubSlotData?._meta?.timestamp || 0;
    const isHubFresh = ts > lastHubTimestampRef.current;

    if (autoImportDone.current && !isHubFresh) return;
    autoImportDone.current = true;

    const d = readDiagramSource();
    if (!d) return;

    if (d.source === 'hub') {
      lastHubTimestampRef.current = ts;
    }

    callAction('import_diagram', {
      blocks: d.blocks,
      connections: d.connections,
      system_type: d.system_type,
    });
  }, [hubSlotData, hubUpdated, readDiagramSource, callAction]);

  const handleLoadPreset = useCallback((id) => {
    callAction('load_preset', { preset_id: id });
    setShowPresets(false);
    showToast('Preset loaded!');
  }, [callAction, showToast]);

  // ========================================================================
  // Probes
  // ========================================================================
  const handleToggleProbe = useCallback((nodeId) => {
    if (probedNodeIds.has(nodeId)) callAction('remove_probe', { node_id: nodeId });
    else if (probes.length < MAX_PROBES) callAction('add_probe', { node_id: nodeId });
  }, [callAction, probedNodeIds, probes.length]);

  const handleClearProbes = useCallback(() => callAction('clear_probes', {}), [callAction]);
  const handleProbeAll = useCallback(() => callAction('probe_all', {}), [callAction]);

  // ========================================================================
  // Inline params
  // ========================================================================
  const setParam = useCallback((name, val) => onParamChange?.(name, val), [onParamChange]);

  // ========================================================================
  // Canvas pan & zoom (drag-threshold approach)
  // ========================================================================
  const handleCanvasMouseDown = useCallback((e) => {
    if (e.button !== 0) return;
    dragRef.current = {
      startX: e.clientX, startY: e.clientY,
      panX: pan.x, panY: pan.y,
      dragging: false,
    };
  }, [pan]);

  const handleCanvasMouseMove = useCallback((e) => {
    const d = dragRef.current;
    if (!d) return;
    const dx = e.clientX - d.startX;
    const dy = e.clientY - d.startY;
    if (!d.dragging && Math.abs(dx) + Math.abs(dy) > PAN_THRESHOLD) {
      d.dragging = true;
    }
    if (d.dragging) {
      setPan({ x: d.panX + dx, y: d.panY + dy });
    }
  }, []);

  const handleCanvasMouseUp = useCallback(() => { dragRef.current = null; }, []);

  const handleWheel = useCallback((e) => {
    e.preventDefault();
    setZoom(prev => Math.max(0.2, Math.min(4.0, prev * (e.deltaY > 0 ? 0.9 : 1.1))));
  }, []);

  // Auto-fit viewport when diagram changes
  useEffect(() => {
    if (layoutNodes.length === 0) return;
    const xs = layoutNodes.map(n => n.position?.x || 0);
    const ys = layoutNodes.map(n => n.position?.y || 0);
    const pad = 80;
    const minX = Math.min(...xs) - pad, maxX = Math.max(...xs) + pad;
    const minY = Math.min(...ys) - pad, maxY = Math.max(...ys) + pad;
    const el = svgRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;
    // Use a minimum span for Y to avoid squishing nearly-collinear layouts
    const ySpan = Math.max(maxY - minY, 250);
    const sx = rect.width / (maxX - minX);
    const sy = rect.height / ySpan;
    const z = Math.min(sx, sy, 1.8) * 0.85;
    setZoom(z);
    setPan({
      x: rect.width / 2 - ((minX + maxX) / 2) * z,
      y: rect.height / 2 - ((minY + maxY) / 2) * z,
    });
  }, [layoutNodes]);

  // Close presets dropdown on outside click
  useEffect(() => {
    const h = (e) => { if (presetsRef.current && !presetsRef.current.contains(e.target)) setShowPresets(false); };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);

  const togglePlotVis = useCallback((key) => {
    setVisiblePlots(prev => ({ ...prev, [key]: !prev[key] }));
  }, []);

  // ========================================================================
  // Build signals list for overlay
  // ========================================================================
  const allSignals = useMemo(() => {
    const list = [];
    if (signals.input) list.push({ key: 'input', ...signals.input, time: signals.time });
    if (signals.output) list.push({ key: 'output', ...signals.output, time: signals.time });
    if (signals.probes) {
      Object.entries(signals.probes).forEach(([pid, ps]) => {
        list.push({ key: pid, ...ps, time: signals.time });
      });
    }
    return list;
  }, [signals]);

  // ========================================================================
  // Render
  // ========================================================================
  return (
    <div className="sfs-root">
      {/* ===== TOOLBAR ===== */}
      <div className="sfs-toolbar">
        <button
          className="sfs-btn sfs-btn-accent"
          onClick={handleImport}
          disabled={isLoading}
          title="Reimport diagram from System Hub (or fall back to local export)"
        >Import</button>

        <div className="sfs-dropdown-wrap" ref={presetsRef}>
          <button className="sfs-btn" onClick={() => setShowPresets(!showPresets)}>Presets ▾</button>
          {showPresets && (
            <div className="sfs-dropdown">
              {(presetList.length > 0 ? presetList : [
                { id: 'unity_feedback', name: 'Unity Feedback', description: '' },
                { id: 'cascade', name: 'Cascade', description: '' },
                { id: 'second_order_dt', name: 'Second-Order DT', description: '' },
                { id: 'first_order_lowpass', name: 'First-Order Lowpass', description: '' },
              ]).map(p => (
                <button key={p.id} className="sfs-dropdown-item" onClick={() => handleLoadPreset(p.id)}>
                  <strong>{p.name}</strong>
                  {p.description && <small>{p.description}</small>}
                </button>
              ))}
            </div>
          )}
        </div>

        <span className="sfs-sep" />

        <label className="sfs-lbl">Signal</label>
        <select className="sfs-sel" value={inputType} onChange={e => setParam('input_type', e.target.value)}>
          {SIGNAL_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>

        {FREQ_SIGNALS.has(inputType) && (
          <>
            <label className="sfs-lbl sfs-lbl-dim">Freq</label>
            <input type="range" className="sfs-slider" min="0.01" max="50" step="0.01"
              value={inputFreq} onChange={e => setParam('input_freq', +e.target.value)} />
            <span className="sfs-val">{inputFreq.toFixed(1)}</span>
          </>
        )}

        {inputType === 'square' && (
          <>
            <label className="sfs-lbl sfs-lbl-dim">Duty</label>
            <input type="range" className="sfs-slider sfs-slider-sm" min="0.1" max="0.9" step="0.05"
              value={dutyCycle} onChange={e => setParam('duty_cycle', +e.target.value)} />
            <span className="sfs-val">{(dutyCycle * 100).toFixed(0)}%</span>
          </>
        )}

        {inputType === 'chirp' && (
          <>
            <label className="sfs-lbl sfs-lbl-dim">End</label>
            <input type="range" className="sfs-slider sfs-slider-sm" min="1" max="100" step="1"
              value={chirpEndFreq} onChange={e => setParam('chirp_end_freq', +e.target.value)} />
            <span className="sfs-val">{chirpEndFreq}Hz</span>
          </>
        )}

        <span className="sfs-sep" />

        <label className="sfs-lbl sfs-lbl-dim">Amp</label>
        <input type="range" className="sfs-slider sfs-slider-sm" min="0.1" max="10" step="0.1"
          value={inputAmplitude} onChange={e => setParam('input_amplitude', +e.target.value)} />
        <span className="sfs-val">{inputAmplitude.toFixed(1)}</span>

        <label className="sfs-lbl sfs-lbl-dim">N</label>
        <input type="range" className="sfs-slider sfs-slider-sm" min="20" max="500" step="10"
          value={numSamples} onChange={e => setParam('num_samples', +e.target.value)} />
        <span className="sfs-val">{numSamples}</span>

        <span className="sfs-sep" />
        <span className="sfs-badge">{systemType === 'dt' ? 'DT' : 'CT'}</span>

        {diagramLoaded && (
          <>
            <button className="sfs-btn sfs-btn-xs" onClick={handleProbeAll}>Probe All</button>
            {probes.length > 0 && (
              <button className="sfs-btn sfs-btn-xs sfs-btn-ghost" onClick={handleClearProbes}>Clear</button>
            )}
          </>
        )}
        {isLoading && <span className="sfs-spin" />}
      </div>

      {/* Error */}
      {(error || metaError) && <div className="sfs-err">{error || metaError}</div>}

      {/* ===== CONTENT ===== */}
      {!diagramLoaded ? (
        /* Empty state */
        <div className="sfs-empty">
          <div style={{ fontSize: 18, marginBottom: 8, color: 'var(--text-muted)' }}>Signal Scope</div>
          <h3>Signal Scope</h3>
          <p>Import a diagram or select a preset to get started.</p>
          <div className="sfs-empty-row">
            <button className="sfs-btn sfs-btn-accent sfs-btn-lg" onClick={handleImport}>Import Diagram</button>
          </div>
          <div className="sfs-empty-row" style={{ marginTop: 12 }}>
            {['unity_feedback', 'cascade', 'second_order_dt', 'first_order_lowpass'].map(id => (
              <button key={id} className="sfs-btn" onClick={() => handleLoadPreset(id)}
                style={{ textTransform: 'capitalize' }}>
                {id.replace(/_/g, ' ')}
              </button>
            ))}
          </div>
        </div>
      ) : (
        /* Main view: canvas + plots */
        <div className="sfs-body">
          {/* ---- Canvas ---- */}
          <div className="sfs-canvas-wrap">
            <div className="sfs-canvas-hdr">
              <span className="sfs-canvas-label">Signal Flow Graph</span>
              <span className="sfs-canvas-hint">Click nodes to probe &middot; Drag to pan &middot; Scroll to zoom</span>
              <span className="sfs-canvas-probes">Probes {probes.length}/{MAX_PROBES}</span>
            </div>
            <svg ref={svgRef} className="sfs-svg"
              onWheel={handleWheel}
              onMouseDown={handleCanvasMouseDown}
              onMouseMove={handleCanvasMouseMove}
              onMouseUp={handleCanvasMouseUp}
              onMouseLeave={handleCanvasMouseUp}>
              <defs>
                <marker id="sfs-arrow" markerWidth={ARROW_SIZE} markerHeight={ARROW_SIZE * 0.75}
                  refX={ARROW_SIZE} refY={ARROW_SIZE * 0.375} orient="auto">
                  <polygon points={`0 0, ${ARROW_SIZE} ${ARROW_SIZE * 0.375}, 0 ${ARROW_SIZE * 0.75}`}
                    fill="#00d9ff" opacity="0.7" />
                </marker>
              </defs>
              <rect width="100%" height="100%" fill={T.PLOT_BG} />
              <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
                {sfgEdges.map(e => <SFGEdge key={e.id} edge={e} nodes={layoutNodes} theme={T} />)}
                {layoutNodes.map(n => (
                  <SFGNode key={n.id} node={n}
                    onToggleProbe={handleToggleProbe}
                    isProbed={probedNodeIds.has(n.id)}
                    probeColor={probeColorMap[n.id]} theme={T} />
                ))}
              </g>
            </svg>

            {/* Probe chips */}
            {probes.length > 0 && (
              <div className="sfs-probe-bar">
                {probes.map(p => {
                  const tf = nodeTfs[p.node_id];
                  return (
                    <div key={p.id} className="sfs-chip" onClick={() => handleToggleProbe(p.node_id)}>
                      <span className="sfs-chip-dot" style={{ background: p.color }} />
                      <span className="sfs-chip-name">{p.label}</span>
                      {tf?.expression?.domain && <span className="sfs-chip-tf">H={tf.expression.domain}</span>}
                      <span className="sfs-chip-x">&times;</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* ---- Plots ---- */}
          <div className="sfs-plots-wrap">
            <div className="sfs-plots-bar">
              <span className="sfs-plots-lbl">Plots</span>
              <button className={`sfs-pill ${visiblePlots.input ? 'on' : ''}`} onClick={() => togglePlotVis('input')}>
                <i style={{ background: '#14b8a6' }} /> Input
              </button>
              <button className={`sfs-pill ${visiblePlots.output ? 'on' : ''}`} onClick={() => togglePlotVis('output')}>
                <i style={{ background: '#f59e0b' }} /> Output
              </button>
              {probes.map(p => (
                <button key={p.id} className={`sfs-pill ${visiblePlots[p.id] ? 'on' : ''}`} onClick={() => togglePlotVis(p.id)}>
                  <i style={{ background: p.color }} /> {p.label}
                </button>
              ))}
              <span style={{ flex: 1 }} />
              <button className={`sfs-pill sfs-pill-ov ${overlayMode ? 'on' : ''}`} onClick={() => setOverlayMode(!overlayMode)}>
                Overlay
              </button>
            </div>

            <div className="sfs-plots-grid">
              {overlayMode ? (
                <OverlayPlot signals={allSignals.filter(s => visiblePlots[s.key])} systemType={systemType} xLabel={xLabel} theme={T} />
              ) : (
                <>
                  {visiblePlots.input && signals.input && (
                    <SignalPlotCard title={signals.input.label || 'Input'} color={signals.input.color || '#14b8a6'}
                      time={signals.time} values={signals.input.values} stats={signals.input.stats}
                      systemType={systemType} xLabel={xLabel} theme={T} />
                  )}
                  {visiblePlots.output && signals.output && (
                    <SignalPlotCard title={signals.output.label || 'Output'} color={signals.output.color || '#f59e0b'}
                      time={signals.time} values={signals.output.values} stats={signals.output.stats}
                      systemType={systemType} xLabel={xLabel} theme={T} />
                  )}
                  {probes.map(p => {
                    const ps = signals.probes?.[p.id];
                    if (!visiblePlots[p.id] || !ps) return null;
                    return (
                      <SignalPlotCard key={p.id} title={ps.label} color={ps.color}
                        time={signals.time} values={ps.values} stats={ps.stats}
                        systemType={systemType} xLabel={xLabel} theme={T} />
                    );
                  })}
                  {!signals.time && (
                    <div className="sfs-plots-empty">Click nodes on the graph to probe signals</div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {toast && <div className="sfs-toast">{toast}</div>}

      {/* ===== STYLES ===== */}
      <style>{`
/* Root */
.sfs-root {
  display: flex; flex-direction: column;
  height: 100%; min-height: 550px;
  position: relative;
  background: ${T.PLOT_PAPER};
  border-radius: 12px;
  overflow: hidden;
}

/* --- Toolbar --- */
.sfs-toolbar {
  display: flex; align-items: center; gap: 7px;
  padding: 5px 10px; flex-shrink: 0; flex-wrap: wrap;
  background: ${T.PLOT_BG}; border-bottom: 1px solid ${T.BORDER};
}
.sfs-sep { width: 1px; height: 18px; background: ${T.BORDER}; flex-shrink: 0; }
.sfs-lbl { font-size: 11px; color: ${T.PLOT_TEXT}; font-weight: 600; white-space: nowrap; }
.sfs-lbl-dim { font-weight: 400; color: ${T.TEXT_MUTED}; }
.sfs-val { font-size: 11px; color: var(--accent-color); font-family: 'Fira Code', monospace; min-width: 32px; text-align: right; }

/* Buttons */
.sfs-btn {
  padding: 4px 10px; border: 1px solid ${T.BORDER}; background: transparent;
  color: ${T.PLOT_TEXT}; border-radius: 6px; font-size: 11px; font-weight: 500;
  cursor: pointer; transition: all 150ms; white-space: nowrap;
}
.sfs-btn:hover { border-color: #14b8a6; color: #14b8a6; background: rgba(20,184,166,0.08); }
.sfs-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.sfs-btn-accent { border-color: #14b8a6; color: #14b8a6; background: rgba(20,184,166,0.08); }
.sfs-btn-accent:hover { background: #14b8a6; color: #fff; }
.sfs-btn-xs { padding: 2px 7px; font-size: 10px; }
.sfs-btn-ghost:hover { border-color: #ef4444; color: #ef4444; background: rgba(239,68,68,0.08); }
.sfs-btn-lg { padding: 10px 24px; font-size: 14px; border-radius: 8px; }

/* Select / slider */
.sfs-sel {
  padding: 3px 6px; border: 1px solid ${T.BORDER}; background: ${T.PLOT_BG};
  color: ${T.TEXT_PRIMARY}; border-radius: 5px; font-size: 11px; outline: none; cursor: pointer;
}
.sfs-sel:focus { border-color: #14b8a6; }
.sfs-slider { width: 70px; height: 3px; accent-color: #14b8a6; cursor: pointer; }
.sfs-slider-sm { width: 52px; }

/* Badge */
.sfs-badge {
  padding: 1px 7px; border-radius: 999px; font-size: 10px; font-weight: 700;
  letter-spacing: 0.5px; background: rgba(59,130,246,0.15);
  color: #3b82f6; border: 1px solid rgba(59,130,246,0.3);
}

/* Spinner */
.sfs-spin {
  width: 12px; height: 12px; border: 2px solid #14b8a6; border-top-color: transparent;
  border-radius: 50%; animation: sfs-sp 0.6s linear infinite;
}
@keyframes sfs-sp { to { transform: rotate(360deg); } }

/* Dropdown */
.sfs-dropdown-wrap { position: relative; }
.sfs-dropdown {
  position: absolute; top: calc(100% + 4px); left: 0; z-index: 50;
  min-width: 260px; padding: 4px;
  background: ${T.PLOT_BG}; border: 1px solid ${T.BORDER}; border-radius: 8px;
  box-shadow: 0 8px 32px ${T.SHADOW};
}
.sfs-dropdown-item {
  display: flex; flex-direction: column; width: 100%; padding: 8px 12px;
  border: none; background: transparent; color: ${T.TEXT_PRIMARY}; cursor: pointer;
  border-radius: 5px; text-align: left;
}
.sfs-dropdown-item:hover { background: rgba(20,184,166,0.1); }
.sfs-dropdown-item strong { font-size: 12px; }
.sfs-dropdown-item small { font-size: 10px; color: ${T.TEXT_MUTED}; margin-top: 2px; }

/* Error */
.sfs-err {
  padding: 5px 12px; background: rgba(239,68,68,0.1);
  border-bottom: 1px solid rgba(239,68,68,0.3);
  color: #ef4444; font-size: 12px; flex-shrink: 0;
}

/* --- Empty state --- */
.sfs-empty {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 32px; text-align: center; color: ${T.PLOT_TEXT};
}
.sfs-empty h3 { font-size: 22px; color: ${T.TEXT_PRIMARY}; margin: 0 0 6px; }
.sfs-empty p { font-size: 14px; color: ${T.TEXT_MUTED}; margin: 0 0 20px; }
.sfs-empty-row { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; }

/* --- Main body --- */
.sfs-body { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

/* Canvas */
.sfs-canvas-wrap {
  flex: 1 1 0; min-height: 250px;
  display: flex; flex-direction: column;
  position: relative; border-bottom: 1px solid ${T.BORDER};
}
.sfs-canvas-hdr {
  display: flex; align-items: center; gap: 10px;
  padding: 3px 10px; background: ${T.PLOT_BG};
  border-bottom: 1px solid ${T.BORDER}; flex-shrink: 0;
}
.sfs-canvas-label { font-size: 11px; font-weight: 600; color: ${T.TEXT_PRIMARY}; }
.sfs-canvas-hint { font-size: 10px; color: ${T.TEXT_MUTED}; }
.sfs-canvas-probes { margin-left: auto; font-size: 10px; color: ${T.TEXT_MUTED}; }
.sfs-svg { flex: 1; cursor: grab; display: block; }
.sfs-svg:active { cursor: grabbing; }

/* Node hover */
.sfs-node-probeable:hover circle { filter: brightness(1.4); }
@keyframes sfs-glow { 0%,100% { opacity: 0.35; } 50% { opacity: 0.65; } }

/* Probe bar */
.sfs-probe-bar {
  position: absolute; bottom: 6px; left: 6px; right: 6px;
  display: flex; gap: 5px; flex-wrap: wrap; pointer-events: none;
}
.sfs-chip {
  display: flex; align-items: center; gap: 4px;
  padding: 3px 8px; background: ${T.PLOT_PAPER};
  border: 1px solid ${T.BORDER}; border-radius: 999px;
  cursor: pointer; pointer-events: all; backdrop-filter: blur(6px);
  transition: border-color 150ms;
}
.sfs-chip:hover { border-color: #ef4444; }
.sfs-chip-dot { width: 7px; height: 7px; border-radius: 50%; }
.sfs-chip-name { font-size: 10px; font-weight: 500; color: ${T.TEXT_PRIMARY}; }
.sfs-chip-tf { font-size: 9px; font-family: 'Fira Code', monospace; color: ${T.TEXT_MUTED}; max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sfs-chip-x { font-size: 11px; color: ${T.TEXT_MUTED}; margin-left: 2px; }

/* --- Plots section --- */
.sfs-plots-wrap {
  flex: 0 0 auto; display: flex; flex-direction: column;
  max-height: 45vh; overflow: hidden;
}

/* Plot toggle bar */
.sfs-plots-bar {
  display: flex; align-items: center; gap: 5px;
  padding: 4px 10px; background: ${T.PLOT_BG};
  border-bottom: 1px solid ${T.BORDER}; flex-shrink: 0; flex-wrap: wrap;
}
.sfs-plots-lbl { font-size: 11px; font-weight: 600; color: ${T.TEXT_PRIMARY}; margin-right: 2px; }
.sfs-pill {
  display: inline-flex; align-items: center; gap: 3px;
  padding: 2px 8px; border: 1px solid ${T.BORDER}; background: transparent;
  color: ${T.TEXT_MUTED}; border-radius: 999px; font-size: 10px;
  cursor: pointer; transition: all 150ms;
}
.sfs-pill i { display: inline-block; width: 6px; height: 6px; border-radius: 50%; }
.sfs-pill:hover { border-color: #14b8a6; }
.sfs-pill.on { border-color: #14b8a680; color: ${T.TEXT_PRIMARY}; background: rgba(20,184,166,0.08); }
.sfs-pill-ov { font-weight: 600; }

/* Plot grid */
.sfs-plots-grid {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 1px; background: ${T.BORDER};
  overflow-y: auto; flex: 1;
}

.sfs-plot-card { background: ${T.PLOT_PAPER}; display: flex; flex-direction: column; }
.sfs-plot-overlay { grid-column: 1 / -1; }
.sfs-plot-card-hdr {
  display: flex; align-items: center; gap: 5px;
  padding: 3px 8px; flex-shrink: 0;
}
.sfs-plot-dot { width: 7px; height: 7px; border-radius: 50%; }
.sfs-plot-title { font-size: 11px; font-weight: 600; color: ${T.TEXT_PRIMARY}; }
.sfs-plot-stats { font-size: 9px; font-family: 'Fira Code', monospace; color: ${T.TEXT_MUTED}; margin-left: auto; }
.sfs-plot-body { height: 170px; }
.sfs-plot-body-tall { height: 240px; }
.sfs-plots-empty {
  grid-column: 1 / -1; display: flex; align-items: center;
  justify-content: center; padding: 24px;
  color: ${T.TEXT_MUTED}; font-size: 13px; background: ${T.PLOT_PAPER};
}

/* Toast */
.sfs-toast {
  position: absolute; bottom: 14px; left: 50%; transform: translateX(-50%);
  background: ${T.PLOT_BG}; border: 1px solid #14b8a6; border-radius: 8px;
  padding: 7px 16px; color: ${T.TEXT_PRIMARY}; font-size: 12px;
  z-index: 100; box-shadow: 0 4px 16px ${T.SHADOW}; pointer-events: none;
}

/* Responsive */
@media (max-width: 1024px) {
  .sfs-slider { width: 48px; }
  .sfs-slider-sm { width: 36px; }
}
@media (max-width: 768px) {
  .sfs-plots-grid { grid-template-columns: 1fr; }
  .sfs-lbl-dim, .sfs-val { display: none; }
  .sfs-canvas-wrap { min-height: 180px; }
}
      `}</style>
    </div>
  );
}

export default SignalFlowScopeViewer;
