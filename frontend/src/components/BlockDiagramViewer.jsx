/**
 * BlockDiagramViewer Component — Full Rewrite
 *
 * Interactive SVG-based block diagram builder with A* wire routing.
 * Two modes:
 *   1. Build Mode — drag/drop blocks, draw wires → compute transfer function
 *   2. Parse Mode — enter transfer function → generate block diagram
 *
 * Block types: Input, Output, Gain, Constant, Adder, Delay (DT), Integrator (CT), Junction
 */

import React, { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import api from '../services/api';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import '../styles/BlockDiagramViewer.css';

// ============================================================================
// LaTeX rendering helper
// ============================================================================

function LaTeX({ math, display = false, className = '' }) {
  const ref = useRef(null);
  useEffect(() => {
    if (ref.current && math) {
      try {
        katex.render(math, ref.current, { throwOnError: false, displayMode: display });
      } catch { /* fallback handled by throwOnError: false */ }
    }
  }, [math, display]);
  return <span ref={ref} className={className} />;
}

// ============================================================================
// Constants
// ============================================================================

const GRID_SIZE = 24;
const CANVAS_WIDTH = 1400;
const CANVAS_HEIGHT = 800;
const MIN_ZOOM = 0.5;
const MAX_ZOOM = 3.0;
const ZOOM_STEP = 0.15;
const PORT_RADIUS = 10;
const COLLISION_PAD = 48; // 2 grid cells clearance around blocks
const RELAXED_PAD = 12;  // Reduced padding for adaptive routing (feedback wires)

const BLOCK_SIZES = {
  input:      { width: 80, height: 60 },
  output:     { width: 80, height: 60 },
  gain:       { width: 80, height: 60 },
  constant:   { width: 80, height: 60 },
  adder:      { radius: 30 },
  delay:      { width: 80, height: 60 },
  integrator: { width: 80, height: 60 },
  junction:   { radius: 6 },
};

// Port offsets — all multiples of GRID_SIZE for grid alignment
const PORT_OFFSETS = {
  input:      { output: 48 },
  output:     { input: 48 },
  gain:       { left: 48, right: 48 },
  constant:   { output: 48 },
  delay:      { left: 48, right: 48 },
  integrator: { left: 48, right: 48 },
  adder:      { left: 48, bottom: 48, right: 48 },
  junction:   { d: 24 },
};

function snapToGrid(val) {
  return Math.round(val / GRID_SIZE) * GRID_SIZE;
}

// ============================================================================
// A* Wire Router — THE CRITICAL FIX
// ============================================================================

function getInflatedBounds(block) {
  const { x, y } = block.position;
  const type = block.type;
  const pad = arguments.length > 1 ? arguments[1] : COLLISION_PAD;
  if (type === 'adder') {
    const r = BLOCK_SIZES.adder.radius;
    return { left: x - r - pad, right: x + r + pad,
             top: y - r - pad, bottom: y + r + pad };
  }
  if (type === 'junction') {
    const r = BLOCK_SIZES.junction.radius;
    return { left: x - r - pad, right: x + r + pad,
             top: y - r - pad, bottom: y + r + pad };
  }
  const size = BLOCK_SIZES[type] || { width: 80, height: 60 };
  const hw = size.width / 2, hh = size.height / 2;
  return { left: x - hw - pad, right: x + hw + pad,
           top: y - hh - pad, bottom: y + hh + pad };
}

function buildObstacleSet(blocks, excludeIds = [], pad = COLLISION_PAD) {
  const blocked = new Set();
  Object.values(blocks).forEach(block => {
    if (excludeIds.includes(block.id)) return;
    const bounds = getInflatedBounds(block, pad);
    const left = Math.floor(bounds.left / GRID_SIZE) * GRID_SIZE;
    const right = Math.ceil(bounds.right / GRID_SIZE) * GRID_SIZE;
    const top = Math.floor(bounds.top / GRID_SIZE) * GRID_SIZE;
    const bottom = Math.ceil(bounds.bottom / GRID_SIZE) * GRID_SIZE;
    for (let gx = left; gx <= right; gx += GRID_SIZE) {
      for (let gy = top; gy <= bottom; gy += GRID_SIZE) {
        blocked.add(`${gx},${gy}`);
      }
    }
  });
  return blocked;
}

function pathLength(pts) {
  let len = 0;
  for (let i = 0; i < pts.length - 1; i++) {
    len += Math.abs(pts[i+1][0] - pts[i][0]) + Math.abs(pts[i+1][1] - pts[i][1]);
  }
  return len;
}

function routeWire(fromPort, toPort, blocks, excludeIds = []) {
  // Build obstacles WITHOUT excluding source/target — prevents wires cutting through blocks
  const obstacles = buildObstacleSet(blocks);                         // strict, no exclusions
  const relaxedObs = buildObstacleSet(blocks, [], RELAXED_PAD);       // relaxed, no exclusions
  const sx = snapToGrid(fromPort.x), sy = snapToGrid(fromPort.y);
  const ex = snapToGrid(toPort.x), ey = snapToGrid(toPort.y);
  const startDir = fromPort.dir || 'right';
  const endDir = toPort.dir || 'left';
  const G = GRID_SIZE;

  // Build bypass set: port positions + exit/entrance corridors
  // Corridors allow A* to reach ports through block obstacle zones
  const bypassKeys = new Set([`${sx},${sy}`, `${ex},${ey}`]);

  // Helper to add corridor cells in a direction
  const addCorridor = (px, py, dir, steps) => {
    for (let i = 1; i <= steps; i++) {
      let cx = px, cy = py;
      switch (dir) {
        case 'right': cx += G * i; break;
        case 'left':  cx -= G * i; break;
        case 'down':  cy += G * i; break;
        case 'up':    cy -= G * i; break;
      }
      bypassKeys.add(`${cx},${cy}`);
    }
  };

  // Add exit corridor from start port (3 cells in port direction)
  addCorridor(sx, sy, startDir, 3);
  // Add entrance corridor to end port (3 cells from port direction)
  addCorridor(ex, ey, endDir, 3);

  // Compute departure point (one grid cell in start direction)
  let dx = sx + (startDir === 'right' ? G : startDir === 'left' ? -G : 0);
  let dy = sy + (startDir === 'down' ? G : startDir === 'up' ? -G : 0);

  // Compute approach point (one grid cell in end direction)
  let ax = ex + (endDir === 'right' ? G : endDir === 'left' ? -G : 0);
  let ay = ey + (endDir === 'down' ? G : endDir === 'up' ? -G : 0);

  // Compute adaptive directions based on relative positions (for feedback wires)
  const relDx = ex - sx, relDy = ey - sy;
  const adaptStart = Math.abs(relDx) >= Math.abs(relDy)
    ? (relDx >= 0 ? 'right' : 'left')
    : (relDy >= 0 ? 'down' : 'up');
  const adaptEnd = Math.abs(relDx) >= Math.abs(relDy)
    ? (relDx >= 0 ? 'left' : 'right')
    : (relDy >= 0 ? 'up' : 'down');

  // Add adaptive corridors
  addCorridor(sx, sy, adaptStart, 3);
  addCorridor(ex, ey, adaptEnd, 3);

  // Adaptive departure/approach points
  let adx = sx + (adaptStart === 'right' ? G : adaptStart === 'left' ? -G : 0);
  let ady = sy + (adaptStart === 'down' ? G : adaptStart === 'up' ? -G : 0);
  let aax = ex + (adaptEnd === 'right' ? G : adaptEnd === 'left' ? -G : 0);
  let aay = ey + (adaptEnd === 'down' ? G : adaptEnd === 'up' ? -G : 0);

  // Try multiple routing strategies and pick the SHORTEST path
  const candidates = [];

  // Strategies 1-3: strict obstacles (full clearance from blocks)

  // Strategy 1: departure → approach (enforces port directions)
  const p1 = astar(dx, dy, ax, ay, obstacles, startDir, bypassKeys);
  if (p1 && p1.length > 0) {
    const route1 = simplifyPath([[sx, sy], ...p1, [ex, ey]]);
    candidates.push(route1);
  }

  // Strategy 2: direct port → port (no stubs, more flexible)
  const p2 = astar(sx, sy, ex, ey, obstacles, startDir, bypassKeys);
  if (p2 && p2.length > 0) {
    candidates.push(p2);
  }

  // Strategy 3: departure → direct end (start enforced, end flexible)
  const p3 = astar(dx, dy, ex, ey, obstacles, startDir, bypassKeys);
  if (p3 && p3.length > 0) {
    const route3 = simplifyPath([[sx, sy], ...p3]);
    candidates.push(route3);
  }

  // Strategies 4-5: relaxed obstacles + adaptive direction (for feedback wires)
  // These can pass through gaps between blocks with reduced clearance

  // Strategy 4: adaptive departure → adaptive approach (relaxed, no initial penalty)
  const p4 = astar(adx, ady, aax, aay, relaxedObs, adaptStart, bypassKeys, false);
  if (p4 && p4.length > 0) {
    const route4 = simplifyPath([[sx, sy], ...p4, [ex, ey]]);
    candidates.push(route4);
  }

  // Strategy 5: adaptive direct port → port (relaxed, no initial penalty)
  const p5 = astar(sx, sy, ex, ey, relaxedObs, adaptStart, bypassKeys, false);
  if (p5 && p5.length > 0) {
    candidates.push(p5);
  }

  // Pick shortest valid route
  if (candidates.length > 0) {
    candidates.sort((a, b) => pathLength(a) - pathLength(b));
    return candidates[0];
  }

  // Last resort: route around ALL blocks
  return fallbackRoute(sx, sy, ex, ey, startDir, endDir, blocks, excludeIds);
}

function astar(sx, sy, ex, ey, obstacles, startDir, bypassKeys, penalizeInitial = true) {
  const G = GRID_SIZE;
  const MAX_ITER = 10000;
  const endKey = `${ex},${ey}`;

  if (sx === ex && sy === ey) return [[sx, sy]];

  const heuristic = (x, y) => Math.abs(ex - x) + Math.abs(ey - y);

  const openMap = new Map();
  const closedSet = new Set();
  const h0 = heuristic(sx, sy);
  const startNode = { x: sx, y: sy, g: 0, h: h0, f: h0, parent: null, dir: startDir };
  const startKey = `${sx},${sy}`;
  openMap.set(startKey, startNode);
  const open = [startNode];

  const dirs = [
    [G, 0, 'right'],
    [-G, 0, 'left'],
    [0, G, 'down'],
    [0, -G, 'up'],
  ];

  let iter = 0;
  while (open.length > 0 && iter < MAX_ITER) {
    iter++;
    const current = open.shift();
    const key = `${current.x},${current.y}`;

    if (current.x === ex && current.y === ey) {
      return reconstructPath(current);
    }

    closedSet.add(key);
    openMap.delete(key);

    for (const [ddx, ddy, dirName] of dirs) {
      const nx = current.x + ddx;
      const ny = current.y + ddy;
      const nKey = `${nx},${ny}`;

      if (closedSet.has(nKey)) continue;
      // Allow bypass cells through obstacles (start, end, departure, approach points)
      if (obstacles.has(nKey) && !bypassKeys.has(nKey)) continue;

      let stepCost = G;
      // Strongly prefer continuing same direction (fewer bends)
      if (dirName === current.dir) stepCost *= 0.75;
      else stepCost *= 1.3; // Turn penalty
      // Prefer right/down for natural signal flow
      if (dirName === 'right' || dirName === 'down') stepCost *= 0.95;
      // Penalize initial turn (first move should go in port's exit direction)
      if (penalizeInitial && current.parent === null && dirName !== startDir) stepCost *= 3.0;

      const ng = current.g + stepCost;
      const nh = heuristic(nx, ny);

      const existing = openMap.get(nKey);
      if (existing && existing.g <= ng) continue;

      const newNode = { x: nx, y: ny, g: ng, h: nh, f: ng + nh, parent: current, dir: dirName };
      openMap.set(nKey, newNode);

      // Insert sorted by f
      let inserted = false;
      for (let i = 0; i < open.length; i++) {
        if (newNode.f < open[i].f) {
          open.splice(i, 0, newNode);
          inserted = true;
          break;
        }
      }
      if (!inserted) open.push(newNode);
    }
  }

  return null;
}

function reconstructPath(node) {
  const path = [];
  let current = node;
  while (current) {
    path.unshift([current.x, current.y]);
    current = current.parent;
  }
  return simplifyPath(path);
}

function simplifyPath(points) {
  if (points.length <= 2) return points;
  const result = [points[0]];
  for (let i = 1; i < points.length - 1; i++) {
    const [px, py] = points[i - 1];
    const [cx, cy] = points[i];
    const [nx, ny] = points[i + 1];
    const sameH = (Math.abs(py - cy) < 1 && Math.abs(cy - ny) < 1);
    const sameV = (Math.abs(px - cx) < 1 && Math.abs(cx - nx) < 1);
    if (!sameH && !sameV) result.push(points[i]);
  }
  result.push(points[points.length - 1]);
  return result;
}

function fallbackRoute(sx, sy, ex, ey, startDir, endDir, blocks, excludeIds) {
  const G = GRID_SIZE;
  // Compute bounding box of ALL blocks (including excluded), route well outside it
  const allBlocks = Object.values(blocks || {});
  let minX = sx, maxX = ex, minY = sy, maxY = ey;
  allBlocks.forEach(b => {
    const bounds = getInflatedBounds(b);
    minX = Math.min(minX, bounds.left);
    maxX = Math.max(maxX, bounds.right);
    minY = Math.min(minY, bounds.top);
    maxY = Math.max(maxY, bounds.bottom);
  });
  // Route 96px (4 grid cells) outside the bounding box
  const detourY = snapToGrid(maxY + G * 4);
  const detourRight = snapToGrid(maxX + G * 4);

  if (startDir === 'right' && endDir === 'left') {
    if (ex > sx && Math.abs(ey - sy) < G) {
      // Straight forward — just L-route (no blocks in between since A* didn't fail for this case)
      const mx = snapToGrid((sx + ex) / 2);
      return [[sx, sy], [mx, sy], [mx, ey], [ex, ey]];
    }
    // Route below all blocks
    return [[sx, sy], [sx + G, sy], [sx + G, detourY], [ex - G, detourY], [ex - G, ey], [ex, ey]];
  }
  if (startDir === 'right' && endDir === 'down') {
    return [[sx, sy], [ex, sy], [ex, ey]];
  }
  if (startDir === 'down') {
    return [[sx, sy], [sx, detourY], [ex, detourY], [ex, ey]];
  }
  // Default: route below
  return [[sx, sy], [sx, detourY], [ex, detourY], [ex, ey]];
}

function pointsToPath(pts) {
  if (!pts || pts.length === 0) return '';
  const clean = [pts[0]];
  for (let i = 1; i < pts.length; i++) {
    const [px, py] = pts[i], [cx, cy] = clean[clean.length - 1];
    if (Math.abs(px - cx) > 0.5 || Math.abs(py - cy) > 0.5) clean.push(pts[i]);
  }
  let d = `M ${clean[0][0]} ${clean[0][1]}`;
  for (let i = 1; i < clean.length; i++) d += ` L ${clean[i][0]} ${clean[i][1]}`;
  return d;
}

// ============================================================================
// Port position computation
// ============================================================================

function getPortPosition(block, portType, portIndex, _unused, adderPortMap) {
  const { x, y } = block.position;
  const type = block.type;

  if (type === 'input') {
    return { x: x + PORT_OFFSETS.input.output, y, dir: 'right' };
  }
  if (type === 'output') {
    return { x: x - PORT_OFFSETS.output.input, y, dir: 'left' };
  }
  if (type === 'constant') {
    return { x: x + PORT_OFFSETS.constant.output, y, dir: 'right' };
  }

  // For gain/delay/integrator: port positions are ALWAYS the same physically
  // (port 0 = LEFT, port 1 = RIGHT). RTL only changes the visual appearance
  // (triangle/arrow direction, port colors) — NOT the physical positions.
  // This is because the backend's RTL convention uses port 0 as output (left)
  // and port 1 as input (right), which already matches the physical positions.
  if (type === 'gain' || type === 'delay' || type === 'integrator') {
    const off = PORT_OFFSETS[type];
    if (portIndex === 0) return { x: x - off.left, y, dir: 'left' };
    return { x: x + off.right, y, dir: 'right' };
  }

  // For adder: use dynamic port positions if available
  if (type === 'adder') {
    const dynPorts = adderPortMap && adderPortMap[block.id];
    if (dynPorts && dynPorts[portIndex]) {
      const dp = dynPorts[portIndex];
      return { x: x + dp.dx, y: y + dp.dy, dir: dp.dir };
    }
    // Fallback to fixed positions
    if (portIndex === 0) return { x: x - PORT_OFFSETS.adder.left, y, dir: 'left' };
    if (portIndex === 1) return { x, y: y + PORT_OFFSETS.adder.bottom, dir: 'down' };
    return { x: x + PORT_OFFSETS.adder.right, y, dir: 'right' };
  }

  if (type === 'junction') {
    const d = PORT_OFFSETS.junction.d;
    if (portIndex === 0) return { x: x - d, y, dir: 'left' };
    if (portIndex === 1) return { x: x + d, y, dir: 'right' };
    if (portIndex === 2) return { x, y: y - d, dir: 'up' };
    if (portIndex === 3) return { x, y: y + d, dir: 'down' };
    return { x: x + d, y: y + (portIndex - 3) * GRID_SIZE, dir: 'right' };
  }
  return { x, y, dir: 'right' };
}

// ============================================================================
// SVG Block Components
// ============================================================================

function InputBlock({ block, isSelected, onMouseDown, onPortMouseDown, systemType }) {
  const { x, y } = block.position;
  const w = BLOCK_SIZES.input.width, h = BLOCK_SIZES.input.height;
  const po = PORT_OFFSETS.input.output;
  const label = systemType === 'ct' ? 'x(t)' : 'x[n]';
  return (
    <g
      className={`bd-block ${isSelected ? 'bd-block-selected' : ''}`}
      onMouseDown={(e) => onMouseDown(e, block.id)}
      transform={`translate(${x}, ${y})`}
    >
      <rect x={-w/2} y={-h/2} width={w} height={h} rx={12} className="bd-block-shape bd-block-io" />
      <text x={-4} y={1} textAnchor="middle" dominantBaseline="middle" className="bd-block-label">{label}</text>
      <polygon points={`${w/2-10},-8 ${w/2},0 ${w/2-10},8`} className="bd-block-arrow" />
      <circle
        cx={po} cy={0} r={PORT_RADIUS}
        className="bd-port bd-port-output"
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'output', 0, x + po, y, 'right'); }}
      />
    </g>
  );
}

function OutputBlock({ block, isSelected, onMouseDown, onPortMouseUp, systemType }) {
  const { x, y } = block.position;
  const w = BLOCK_SIZES.output.width, h = BLOCK_SIZES.output.height;
  const pi = PORT_OFFSETS.output.input;
  const label = systemType === 'ct' ? 'y(t)' : 'y[n]';
  return (
    <g
      className={`bd-block ${isSelected ? 'bd-block-selected' : ''}`}
      onMouseDown={(e) => onMouseDown(e, block.id)}
      transform={`translate(${x}, ${y})`}
    >
      <rect x={-w/2} y={-h/2} width={w} height={h} rx={12} className="bd-block-shape bd-block-io" />
      <polygon points={`${-w/2+10},-8 ${-w/2},0 ${-w/2+10},8`} className="bd-block-arrow bd-block-arrow-in" />
      <text x={4} y={1} textAnchor="middle" dominantBaseline="middle" className="bd-block-label">{label}</text>
      <circle
        cx={-pi} cy={0} r={PORT_RADIUS}
        className="bd-port bd-port-input"
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'input', 0); }}
      />
    </g>
  );
}

function GainBlock({ block, isSelected, onMouseDown, onPortMouseDown, onPortMouseUp, onGainDoubleClick, flowDir = 'ltr' }) {
  const { x, y } = block.position;
  const value = block.value ?? 1;
  const flipped = flowDir === 'rtl';
  const pL = PORT_OFFSETS.gain.left, pR = PORT_OFFSETS.gain.right;
  const hw = BLOCK_SIZES.gain.width / 2, hh = BLOCK_SIZES.gain.height / 2;
  // Triangle shape — flipped for RTL
  const triPoints = flipped
    ? `${hw-4},-${hh-6} ${-hw+4},0 ${hw-4},${hh-6}`
    : `${-hw+4},-${hh-6} ${hw-4},0 ${-hw+4},${hh-6}`;
  const textX = flipped ? 6 : -6;
  // Port positions are ALWAYS fixed (port 0 = left, port 1 = right)
  // Only the CSS class (color) swaps for RTL to show correct semantic role
  // RTL: port 0 at left = output (blue), port 1 at right = input (red)
  return (
    <g
      className={`bd-block ${isSelected ? 'bd-block-selected' : ''}`}
      onMouseDown={(e) => onMouseDown(e, block.id)}
      onDoubleClick={(e) => { e.stopPropagation(); onGainDoubleClick(block.id); }}
      transform={`translate(${x}, ${y})`}
    >
      <polygon points={triPoints} className="bd-block-shape bd-block-gain" />
      <text x={textX} y={2} textAnchor="middle" dominantBaseline="middle" className="bd-block-value">
        {typeof value === 'number' ? (Number.isInteger(value) ? value : value.toFixed(2)) : value}
      </text>
      <g className="bd-gain-edit-hint" transform={`translate(${flipped ? -28 : 28}, -24)`}>
        <rect x={-10} y={-10} width={20} height={20} rx={5} className="bd-gain-hint-bg" />
        <text x={0} y={1} textAnchor="middle" dominantBaseline="middle" className="bd-gain-hint-icon">&#9998;</text>
      </g>
      <circle
        cx={-pL} cy={0} r={PORT_RADIUS}
        className={`bd-port ${flipped ? 'bd-port-output' : 'bd-port-input'}`}
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 0, x - pL, y, 'left'); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 0); }}
      />
      <circle
        cx={pR} cy={0} r={PORT_RADIUS}
        className={`bd-port ${flipped ? 'bd-port-input' : 'bd-port-output'}`}
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 1, x + pR, y, 'right'); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 1); }}
      />
    </g>
  );
}

function ConstantBlock({ block, isSelected, onMouseDown, onPortMouseDown, onGainDoubleClick }) {
  const { x, y } = block.position;
  const value = block.value ?? 1;
  const w = BLOCK_SIZES.constant.width, h = BLOCK_SIZES.constant.height;
  const po = PORT_OFFSETS.constant.output;
  return (
    <g
      className={`bd-block ${isSelected ? 'bd-block-selected' : ''}`}
      onMouseDown={(e) => onMouseDown(e, block.id)}
      onDoubleClick={(e) => { e.stopPropagation(); onGainDoubleClick(block.id); }}
      transform={`translate(${x}, ${y})`}
    >
      <rect x={-w/2} y={-h/2} width={w} height={h} rx={12} className="bd-block-shape bd-block-constant" />
      <text x={-4} y={-8} textAnchor="middle" dominantBaseline="middle" className="bd-block-sublabel">K</text>
      <text x={0} y={12} textAnchor="middle" dominantBaseline="middle" className="bd-block-value">
        {typeof value === 'number' ? (Number.isInteger(value) ? value : value.toFixed(2)) : value}
      </text>
      <g className="bd-gain-edit-hint" transform="translate(28, -24)">
        <rect x={-10} y={-10} width={20} height={20} rx={5} className="bd-gain-hint-bg" />
        <text x={0} y={1} textAnchor="middle" dominantBaseline="middle" className="bd-gain-hint-icon">&#9998;</text>
      </g>
      <circle
        cx={po} cy={0} r={PORT_RADIUS}
        className="bd-port bd-port-output"
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'output', 0, x + po, y, 'right'); }}
      />
    </g>
  );
}

function AdderBlock({ block, isSelected, onMouseDown, onPortMouseDown, onPortMouseUp, onToggleSign, dynamicPorts }) {
  const { x, y } = block.position;
  const rawSigns = block.signs || ['+', '+', '+'];
  const signs = [rawSigns[0] || '+', rawSigns[1] || '+', rawSigns[2] || '+'];
  const r = BLOCK_SIZES.adder.radius;
  const pL = PORT_OFFSETS.adder.left, pB = PORT_OFFSETS.adder.bottom, pR = PORT_OFFSETS.adder.right;

  // Use dynamic port positions if available, otherwise fallback to defaults
  const dp = dynamicPorts || {};
  const p0 = dp[0] || { dx: -pL, dy: 0, dir: 'left' };
  const p1 = dp[1] || { dx: 0, dy: pB, dir: 'down' };
  const p2 = dp[2] || { dx: pR, dy: 0, dir: 'right' };

  // Sign label offset: place sign label adjacent to port, offset perpendicular to port direction
  const signOffset = (port) => {
    const so = 16;
    switch (port.dir) {
      case 'left': return { x: port.dx, y: port.dy - so };
      case 'right': return { x: port.dx, y: port.dy - so };
      case 'up': return { x: port.dx + so, y: port.dy };
      case 'down': return { x: port.dx + so, y: port.dy + 4 };
      default: return { x: port.dx, y: port.dy - so };
    }
  };
  const s0 = signOffset(p0);
  const s1 = signOffset(p1);

  return (
    <g
      className={`bd-block ${isSelected ? 'bd-block-selected' : ''}`}
      onMouseDown={(e) => onMouseDown(e, block.id)}
      transform={`translate(${x}, ${y})`}
    >
      <circle cx={0} cy={0} r={r} className="bd-block-shape bd-block-adder" />
      <line x1={-10} y1={0} x2={10} y2={0} className="bd-adder-cross" />
      <line x1={0} y1={-10} x2={0} y2={10} className="bd-adder-cross" />
      <circle
        cx={p0.dx} cy={p0.dy} r={PORT_RADIUS}
        className="bd-port bd-port-input"
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 0, x + p0.dx, y + p0.dy, p0.dir); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 0); }}
      />
      <text
        x={s0.x} y={s0.y}
        textAnchor="middle" className="bd-sign-label"
        onClick={(e) => { e.stopPropagation(); onToggleSign(block.id, 0); }}
        style={{ cursor: 'pointer' }}
      >{signs[0]}</text>
      <circle
        cx={p1.dx} cy={p1.dy} r={PORT_RADIUS}
        className="bd-port bd-port-input"
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 1, x + p1.dx, y + p1.dy, p1.dir); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 1); }}
      />
      <text
        x={s1.x} y={s1.y}
        textAnchor="middle" className="bd-sign-label"
        onClick={(e) => { e.stopPropagation(); onToggleSign(block.id, 1); }}
        style={{ cursor: 'pointer' }}
      >{signs[1]}</text>
      <circle
        cx={p2.dx} cy={p2.dy} r={PORT_RADIUS}
        className="bd-port bd-port-output"
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'output', 2, x + p2.dx, y + p2.dy, p2.dir); }}
      />
    </g>
  );
}

function DelayBlock({ block, isSelected, onMouseDown, onPortMouseDown, onPortMouseUp, flowDir = 'ltr' }) {
  const { x, y } = block.position;
  const flipped = flowDir === 'rtl';
  const hw = BLOCK_SIZES.delay.width / 2, hh = BLOCK_SIZES.delay.height / 2;
  const pL = PORT_OFFSETS.delay.left, pR = PORT_OFFSETS.delay.right;
  const arrowX = flipped ? -20 : 20;
  const arrowPoints = flipped
    ? `${arrowX+6},-6 ${arrowX-2},0 ${arrowX+6},6`
    : `${arrowX-6},-6 ${arrowX+2},0 ${arrowX-6},6`;
  // Port positions ALWAYS fixed. Only CSS class swaps for RTL.
  return (
    <g
      className={`bd-block ${isSelected ? 'bd-block-selected' : ''}`}
      onMouseDown={(e) => onMouseDown(e, block.id)}
      transform={`translate(${x}, ${y})`}
    >
      <rect x={-hw} y={-hh} width={hw*2} height={hh*2} rx={12} className="bd-block-shape bd-block-delay" />
      <text x={0} y={-8} textAnchor="middle" dominantBaseline="middle" className="bd-block-label">R</text>
      <text x={0} y={14} textAnchor="middle" dominantBaseline="middle" className="bd-block-sublabel">
        z<tspan dy="-6" fontSize="9">-1</tspan>
      </text>
      <polygon points={arrowPoints} className="bd-block-arrow" opacity="0.5" />
      <circle
        cx={-pL} cy={0} r={PORT_RADIUS}
        className={`bd-port ${flipped ? 'bd-port-output' : 'bd-port-input'}`}
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 0, x - pL, y, 'left'); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 0); }}
      />
      <circle
        cx={pR} cy={0} r={PORT_RADIUS}
        className={`bd-port ${flipped ? 'bd-port-input' : 'bd-port-output'}`}
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 1, x + pR, y, 'right'); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 1); }}
      />
    </g>
  );
}

function IntegratorBlock({ block, isSelected, onMouseDown, onPortMouseDown, onPortMouseUp, flowDir = 'ltr' }) {
  const { x, y } = block.position;
  const flipped = flowDir === 'rtl';
  const hw = BLOCK_SIZES.integrator.width / 2, hh = BLOCK_SIZES.integrator.height / 2;
  const pL = PORT_OFFSETS.integrator.left, pR = PORT_OFFSETS.integrator.right;
  const arrowX = flipped ? -20 : 20;
  const arrowPoints = flipped
    ? `${arrowX+6},-6 ${arrowX-2},0 ${arrowX+6},6`
    : `${arrowX-6},-6 ${arrowX+2},0 ${arrowX-6},6`;
  // Port positions ALWAYS fixed. Only CSS class swaps for RTL.
  return (
    <g
      className={`bd-block ${isSelected ? 'bd-block-selected' : ''}`}
      onMouseDown={(e) => onMouseDown(e, block.id)}
      transform={`translate(${x}, ${y})`}
    >
      <rect x={-hw} y={-hh} width={hw*2} height={hh*2} rx={12} className="bd-block-shape bd-block-integrator" />
      <text x={0} y={-8} textAnchor="middle" dominantBaseline="middle" className="bd-block-label" style={{ fontSize: '22px' }}>&int;</text>
      <text x={0} y={14} textAnchor="middle" dominantBaseline="middle" className="bd-block-sublabel">
        1<tspan>/s</tspan>
      </text>
      <polygon points={arrowPoints} className="bd-block-arrow" opacity="0.5" />
      <circle
        cx={-pL} cy={0} r={PORT_RADIUS}
        className={`bd-port ${flipped ? 'bd-port-output' : 'bd-port-input'}`}
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 0, x - pL, y, 'left'); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 0); }}
      />
      <circle
        cx={pR} cy={0} r={PORT_RADIUS}
        className={`bd-port ${flipped ? 'bd-port-input' : 'bd-port-output'}`}
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 1, x + pR, y, 'right'); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 1); }}
      />
    </g>
  );
}

function JunctionBlock({ block, isSelected, onMouseDown, onPortMouseDown, onPortMouseUp, connections = [] }) {
  const { x, y } = block.position;
  const r = BLOCK_SIZES.junction.radius;
  const d = PORT_OFFSETS.junction.d;
  const usedOutputPorts = new Set();
  connections.forEach(c => {
    if (c.from_block === block.id) usedOutputPorts.add(c.from_port);
  });
  const nextPort = Math.max(1, ...Array.from(usedOutputPorts)) + 1;
  const outputPorts = Array.from(usedOutputPorts).concat([nextPort]);

  return (
    <g
      className={`bd-block ${isSelected ? 'bd-block-selected' : ''}`}
      onMouseDown={(e) => onMouseDown(e, block.id)}
      transform={`translate(${x}, ${y})`}
    >
      <circle cx={0} cy={0} r={r} className="bd-junction-dot" />
      <circle
        cx={-d} cy={0} r={PORT_RADIUS}
        className="bd-port bd-port-input"
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 0); }}
      />
      {outputPorts.map(pIdx => {
        let px, py, dir;
        if (pIdx === 1) { px = d; py = 0; dir = 'right'; }
        else if (pIdx === 2) { px = 0; py = -d; dir = 'up'; }
        else if (pIdx === 3) { px = 0; py = d; dir = 'down'; }
        else { px = d; py = (pIdx - 3) * GRID_SIZE; dir = 'right'; }
        return (
          <circle
            key={`jp-${pIdx}`}
            cx={px} cy={py} r={PORT_RADIUS}
            className="bd-port bd-port-output"
            onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'output', pIdx, x + px, y + py, dir); }}
          />
        );
      })}
    </g>
  );
}

// ============================================================================
// Wire Component — uses A* router
// ============================================================================

function Wire({ connection, blocks, autoBranch, isNew, isSelected, onWireClick, onWireMouseDown, onWireDoubleClick, flowDirMap, adderPortMap }) {
  const fromBlock = blocks[connection.from_block];
  const toBlock = blocks[connection.to_block];
  if (!fromBlock || !toBlock) return null;

  const portStart = getPortPosition(fromBlock, 'output', connection.from_port, flowDirMap, adderPortMap);
  const endPos = getPortPosition(toBlock, 'input', connection.to_port, flowDirMap, adderPortMap);

  // Use auto-computed branch point if this wire branches from another
  const bp = autoBranch;
  const startPos = bp ? { x: bp.x, y: bp.y, dir: bp.dir || portStart.dir } : portStart;

  // Route wire using A* pathfinding — no collisions guaranteed
  const points = routeWire(startPos, endPos, blocks, [connection.from_block, connection.to_block]);
  const d = pointsToPath(points);

  return (
    <g className={`bd-wire-group ${isNew ? 'bd-wire-new' : ''} ${isSelected ? 'bd-wire-selected' : ''}`}>
      <path d={d} className="bd-wire-hit" onClick={onWireClick} onMouseDown={onWireMouseDown} onDoubleClick={onWireDoubleClick} />
      <path d={d} className="bd-wire" markerEnd="url(#arrowhead)" />
    </g>
  );
}

function WireInProgress({ startPos, mousePos }) {
  if (!startPos || !mousePos) return null;
  // Simple L-route for in-progress wire (no A* needed)
  const sx = startPos.x, sy = startPos.y;
  const ex = mousePos.x, ey = mousePos.y;
  const mx = snapToGrid((sx + ex) / 2);
  const pts = [[sx, sy], [mx, sy], [mx, ey], [ex, ey]];
  const d = pointsToPath(pts);
  return <path d={d} className="bd-wire-in-progress" />;
}

function ConnectionFlash({ position, success }) {
  if (!position) return null;
  return (
    <g className={`bd-connection-flash ${success ? 'success' : 'fail'}`}>
      <circle cx={position.x} cy={position.y} r={16} className="bd-flash-ring" />
      <text x={position.x} y={position.y + 1} textAnchor="middle" dominantBaseline="middle" className="bd-flash-icon">
        {success ? '\u2713' : '\u2717'}
      </text>
    </g>
  );
}

// ============================================================================
// Export utilities
// ============================================================================

function exportSVG(svgElement) {
  if (!svgElement) return;
  const clone = svgElement.cloneNode(true);
  // Remove UI-only elements
  clone.querySelectorAll('.bd-wire-hit, .bd-zoom-controls, .bd-instructions-overlay, .bd-gain-edit-hint').forEach(el => el.remove());
  const serializer = new XMLSerializer();
  const svgString = '<?xml version="1.0" encoding="UTF-8"?>\n' + serializer.serializeToString(clone);
  const blob = new Blob([svgString], { type: 'image/svg+xml' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'block-diagram.svg';
  a.click();
  URL.revokeObjectURL(url);
}

function exportPNG(svgElement) {
  if (!svgElement) return;
  const clone = svgElement.cloneNode(true);
  clone.querySelectorAll('.bd-wire-hit, .bd-zoom-controls, .bd-instructions-overlay, .bd-gain-edit-hint').forEach(el => el.remove());
  const serializer = new XMLSerializer();
  const svgString = serializer.serializeToString(clone);
  const canvas = document.createElement('canvas');
  const scale = 2;
  canvas.width = CANVAS_WIDTH * scale;
  canvas.height = CANVAS_HEIGHT * scale;
  const ctx = canvas.getContext('2d');
  const img = new Image();
  img.onload = () => {
    ctx.fillStyle = '#0a0e27';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(blob => {
      if (!blob) return;
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'block-diagram.png';
      a.click();
      URL.revokeObjectURL(url);
    }, 'image/png');
  };
  img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgString)));
}

// ============================================================================
// Main BlockDiagramViewer Component
// ============================================================================

function BlockDiagramViewer({ metadata, plots, currentParams, onParamChange, onMetadataChange, simId }) {
  // State
  const [blocks, setBlocks] = useState({});
  const [connections, setConnections] = useState([]);
  const [selectedBlock, setSelectedBlock] = useState(null);
  const [dragging, setDragging] = useState(null);
  const [wireStart, setWireStart] = useState(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [tfResult, setTfResult] = useState(null);
  const [error, setError] = useState(null);
  const [mode, setMode] = useState('build');
  const [systemType, setSystemType] = useState('dt');
  const [tfInput, setTfInput] = useState('');
  const [gainEditBlock, setGainEditBlock] = useState(null);
  const [gainEditValue, setGainEditValue] = useState('');
  const [presets, setPresets] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [presetOpen, setPresetOpen] = useState(false);
  const [connectionFlash, setConnectionFlash] = useState(null);
  const [newWireIndex, setNewWireIndex] = useState(null);
  const [selectedWire, setSelectedWire] = useState(null);
  const [zoom, setZoom] = useState(1.0);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [ctrlHeld, setCtrlHeld] = useState(false);
  const panStart = useRef({ x: 0, y: 0, ox: 0, oy: 0 });

  const svgRef = useRef(null);
  const dragOffset = useRef({ x: 0, y: 0 });
  const presetRef = useRef(null);
  const draggingRef = useRef(null);
  const blocksRef = useRef(blocks);

  // Undo/Redo stacks (frontend-side, max 10)
  const undoStack = useRef([]);
  const redoStack = useRef([]);
  const MAX_UNDO = 10;

  // Track Ctrl key for free drag
  useEffect(() => {
    const down = (e) => { if (e.ctrlKey || e.metaKey) setCtrlHeld(true); };
    const up = (e) => { if (!e.ctrlKey && !e.metaKey) setCtrlHeld(false); };
    window.addEventListener('keydown', down);
    window.addEventListener('keyup', up);
    return () => { window.removeEventListener('keydown', down); window.removeEventListener('keyup', up); };
  }, []);

  // Keep refs in sync
  useEffect(() => { draggingRef.current = dragging; }, [dragging]);
  useEffect(() => { blocksRef.current = blocks; }, [blocks]);

  // Sync state from metadata
  useEffect(() => {
    if (metadata) {
      if (metadata.blocks !== undefined) setBlocks(metadata.blocks);
      if (metadata.connections !== undefined) setConnections(metadata.connections);
      if (metadata.transfer_function !== undefined) setTfResult(metadata.transfer_function);
      if (metadata.error !== undefined) setError(metadata.error);
      if (metadata.mode) setMode(metadata.mode);
      if (metadata.system_type) setSystemType(metadata.system_type);
      if (metadata.presets) setPresets(metadata.presets);
      if (metadata.tf_input !== undefined) setTfInput(metadata.tf_input);
    }
  }, [metadata]);

  // Close preset dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (presetRef.current && !presetRef.current.contains(e.target)) setPresetOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Clear new wire animation
  useEffect(() => {
    if (newWireIndex !== null) {
      const timer = setTimeout(() => setNewWireIndex(null), 600);
      return () => clearTimeout(timer);
    }
  }, [newWireIndex]);

  // Clear connection flash
  useEffect(() => {
    if (connectionFlash) {
      const timer = setTimeout(() => setConnectionFlash(null), 800);
      return () => clearTimeout(timer);
    }
  }, [connectionFlash]);

  // ========================================================================
  // SVG coordinate conversion
  // ========================================================================

  const getSvgCoords = useCallback((clientX, clientY) => {
    const svg = svgRef.current;
    if (!svg) return { x: 0, y: 0 };
    const pt = svg.createSVGPoint();
    pt.x = clientX;
    pt.y = clientY;
    const ctm = svg.getScreenCTM();
    if (!ctm) return { x: 0, y: 0 };
    const svgPt = pt.matrixTransform(ctm.inverse());
    return { x: svgPt.x, y: svgPt.y };
  }, []);

  // ========================================================================
  // Backend API calls with undo snapshot
  // ========================================================================

  const saveUndoSnapshot = useCallback(() => {
    undoStack.current.push({
      blocks: JSON.parse(JSON.stringify(blocks)),
      connections: JSON.parse(JSON.stringify(connections)),
    });
    if (undoStack.current.length > MAX_UNDO) undoStack.current.shift();
    redoStack.current = [];
  }, [blocks, connections]);

  const callAction = useCallback(async (action, params = {}) => {
    setIsLoading(true);
    try {
      const result = await api.executeSimulation(simId, action, params);
      if (result.success && result.data) {
        const meta = result.data.metadata || result.metadata;
        if (meta) {
          if (meta.blocks !== undefined) setBlocks(meta.blocks);
          if (meta.connections !== undefined) setConnections(meta.connections);
          if (meta.transfer_function !== undefined) setTfResult(meta.transfer_function);
          if (meta.error !== undefined) {
            setError(meta.error);
            if (meta.error) setTimeout(() => setError(null), 5000);
          }
          if (meta.mode) setMode(meta.mode);
          if (meta.system_type) setSystemType(meta.system_type);
          if (onMetadataChange) onMetadataChange(meta);
        }
      } else if (result.error) {
        setError(result.error);
        setTimeout(() => setError(null), 5000);
      }
    } catch (err) {
      setError(err.message);
      setTimeout(() => setError(null), 5000);
    } finally {
      setIsLoading(false);
    }
  }, [simId, onMetadataChange]);

  // Mutating action: saves undo snapshot first
  const mutatingAction = useCallback(async (action, params = {}) => {
    saveUndoSnapshot();
    return callAction(action, params);
  }, [saveUndoSnapshot, callAction]);

  // Global mouseup
  useEffect(() => {
    const handleGlobalMouseUp = () => {
      if (draggingRef.current) {
        const block = blocksRef.current[draggingRef.current];
        if (block) callAction('move_block', { block_id: draggingRef.current, position: block.position });
        setDragging(null);
      }
      setWireStart(null);
    };
    window.addEventListener('mouseup', handleGlobalMouseUp);
    return () => window.removeEventListener('mouseup', handleGlobalMouseUp);
  }, [callAction]);

  // ========================================================================
  // Block interactions
  // ========================================================================

  const handleAddBlock = useCallback((blockType) => {
    const existingPositions = Object.values(blocks).map(b => b.position);
    const cx = CANVAS_WIDTH / 2, cy = CANVAS_HEIGHT / 2;
    const hClearance = 100, vClearance = 80;
    const step = 140;
    const noOverlap = (px, py) =>
      !existingPositions.some(p => Math.abs(p.x - px) < hClearance && Math.abs(p.y - py) < vClearance);

    const scx = snapToGrid(cx), scy = snapToGrid(cy);
    if (noOverlap(scx, scy)) {
      mutatingAction('add_block', { block_type: blockType, position: { x: scx, y: scy } });
      return;
    }
    for (let ring = 1; ring <= 12; ring++) {
      const r = ring * step;
      const points = Math.max(8, ring * 6);
      for (let i = 0; i < points; i++) {
        const angle = (2 * Math.PI * i) / points;
        const px = snapToGrid(cx + r * Math.cos(angle));
        const py = snapToGrid(cy + r * Math.sin(angle));
        if (noOverlap(px, py)) {
          mutatingAction('add_block', { block_type: blockType, position: { x: px, y: py } });
          return;
        }
      }
    }
    mutatingAction('add_block', { block_type: blockType, position: { x: cx + 20, y: cy + 20 } });
  }, [blocks, mutatingAction]);

  const handleBlockMouseDown = useCallback((e, blockId) => {
    if (e.button !== 0) return;
    e.stopPropagation();
    const { x: svgX, y: svgY } = getSvgCoords(e.clientX, e.clientY);
    const block = blocks[blockId];
    if (!block) return;
    dragOffset.current = { x: svgX - block.position.x, y: svgY - block.position.y };
    setDragging(blockId);
    setSelectedBlock(blockId);
    setSelectedWire(null);
    setGainEditBlock(null);
  }, [blocks, getSvgCoords]);

  const handleSvgMouseMove = useCallback((e) => {
    const { x: svgX, y: svgY } = getSvgCoords(e.clientX, e.clientY);
    if (dragging) {
      const rawX = svgX - dragOffset.current.x;
      const rawY = svgY - dragOffset.current.y;
      // Ctrl held = free positioning, otherwise snap to grid
      const newX = ctrlHeld ? rawX : snapToGrid(rawX);
      const newY = ctrlHeld ? rawY : snapToGrid(rawY);
      setBlocks(prev => ({
        ...prev,
        [dragging]: { ...prev[dragging], position: { x: newX, y: newY } },
      }));
    }
    if (wireStart) setMousePos({ x: svgX, y: svgY });
  }, [dragging, wireStart, getSvgCoords, ctrlHeld]);

  const handleSvgMouseUp = useCallback(() => {
    if (wireStart) setConnectionFlash({ position: mousePos, success: false });
  }, [wireStart, mousePos]);

  const didPanRef = useRef(false);
  const handleCanvasClick = useCallback((e) => {
    if (didPanRef.current) { didPanRef.current = false; return; }
    if (e.target === svgRef.current || e.target.classList.contains('bd-grid-bg')) {
      setSelectedBlock(null);
      setSelectedWire(null);
      setGainEditBlock(null);
    }
  }, []);

  // Port interactions
  const handlePortMouseDown = useCallback((e, blockId, portType, portIndex, portX, portY, portDir) => {
    e.preventDefault();
    e.stopPropagation();
    if (wireStart) return;
    setWireStart({ blockId, portIndex, x: portX, y: portY, dir: portDir || 'right' });
  }, [wireStart]);

  const handlePortMouseUp = useCallback((e, blockId, portType, portIndex) => {
    e.preventDefault();
    e.stopPropagation();
    if (wireStart && wireStart.blockId !== blockId) {
      const targetBlock = blocks[blockId];
      const targetPos = targetBlock ? getPortPosition(targetBlock, 'input', portIndex) : null;
      const sourceBlock = blocks[wireStart.blockId];
      if (wireStart.blockId === blockId) {
        if (targetPos) setConnectionFlash({ position: targetPos, success: false });
        setWireStart(null); return;
      }
      const isDuplicate = connections.some(c =>
        c.from_block === wireStart.blockId && c.from_port === wireStart.portIndex &&
        c.to_block === blockId && c.to_port === portIndex
      );
      const isReverse = connections.some(c =>
        c.from_block === blockId && c.from_port === portIndex &&
        c.to_block === wireStart.blockId && c.to_port === wireStart.portIndex
      );
      if (isDuplicate || isReverse) {
        if (targetPos) setConnectionFlash({ position: targetPos, success: false });
        setWireStart(null); return;
      }
      if (sourceBlock?.type === 'output' || targetBlock?.type === 'input' || targetBlock?.type === 'constant') {
        if (targetPos) setConnectionFlash({ position: targetPos, success: false });
        setWireStart(null); return;
      }

      const connParams = {
        from_block: wireStart.blockId, from_port: wireStart.portIndex,
        to_block: blockId, to_port: portIndex,
      };
      if (wireStart.branchPoint) connParams.branch_point = wireStart.branchPoint;
      mutatingAction('add_connection', connParams);
      if (targetPos) setConnectionFlash({ position: targetPos, success: true });
      setNewWireIndex(connections.length);
    }
    setWireStart(null);
  }, [wireStart, mutatingAction, blocks, connections]);

  // Undo/Redo
  const handleUndo = useCallback(() => {
    callAction('undo', {});
    setSelectedBlock(null);
    setSelectedWire(null);
  }, [callAction]);

  const handleRedo = useCallback(() => {
    callAction('redo', {});
    setSelectedBlock(null);
    setSelectedWire(null);
  }, [callAction]);

  // Keyboard shortcuts
  const handleKeyDown = useCallback((e) => {
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'z') {
      e.preventDefault(); handleRedo(); return;
    }
    if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
      e.preventDefault(); handleUndo(); return;
    }
    const isTyping = document.activeElement?.tagName === 'INPUT' || document.activeElement?.tagName === 'TEXTAREA';
    if ((e.key === 'Delete' || e.key === 'Backspace') && !gainEditBlock && !isTyping) {
      e.preventDefault();
      if (selectedWire !== null) {
        mutatingAction('remove_connection', { conn_index: selectedWire });
        setSelectedWire(null);
      } else if (selectedBlock) {
        mutatingAction('remove_block', { block_id: selectedBlock });
        setSelectedBlock(null);
      }
    }
  }, [selectedBlock, selectedWire, gainEditBlock, mutatingAction, handleUndo, handleRedo]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Toggle adder sign
  const handleToggleSign = useCallback((blockId, portIndex) => {
    mutatingAction('toggle_adder_sign', { block_id: blockId, port_index: portIndex });
  }, [mutatingAction]);

  // Gain/constant value editing (double-click)
  const handleGainDoubleClick = useCallback((blockId) => {
    const block = blocks[blockId];
    if (block?.type === 'gain' || block?.type === 'constant') {
      setGainEditBlock(blockId);
      setGainEditValue(String(block.value ?? 1));
      setSelectedBlock(blockId);
    }
  }, [blocks]);

  const handleGainEditSubmit = useCallback(() => {
    if (gainEditBlock) {
      const val = parseFloat(gainEditValue);
      if (!isNaN(val)) mutatingAction('update_block_value', { block_id: gainEditBlock, value: val });
      setGainEditBlock(null);
    }
  }, [gainEditBlock, gainEditValue, mutatingAction]);

  // Mode/system type
  const handleModeChange = useCallback((newMode) => {
    setMode(newMode);
    callAction('set_mode', { mode: newMode });
    if (onParamChange) onParamChange('mode', newMode);
  }, [callAction, onParamChange]);

  const handleSystemTypeChange = useCallback((newType) => {
    setSystemType(newType);
    callAction('set_system_type', { system_type: newType });
    setBlocks({}); setConnections([]); setSelectedBlock(null); setSelectedWire(null);
    setTfResult(null); setError(null); setZoom(1.0); setPanOffset({ x: 0, y: 0 });
    if (onParamChange) onParamChange('system_type', newType);
  }, [callAction, onParamChange]);

  const handleClear = useCallback(() => {
    mutatingAction('clear', {});
    setZoom(1.0); setPanOffset({ x: 0, y: 0 }); setSelectedBlock(null);
    setSelectedWire(null); setTfResult(null); setError(null); setTfInput('');
  }, [mutatingAction]);

  const handleLoadPreset = useCallback((presetName) => {
    callAction('load_preset', { preset: presetName });
    setZoom(1.0); setPanOffset({ x: 0, y: 0 }); setPresetOpen(false);
    setSelectedBlock(null); setSelectedWire(null); setError(null);
  }, [callAction]);

  const handleParseTf = useCallback(() => {
    if (tfInput.trim()) callAction('parse_tf', { tf_string: tfInput });
  }, [tfInput, callAction]);

  const handleAutoArrange = useCallback(() => {
    mutatingAction('auto_arrange', {});
  }, [mutatingAction]);

  // Wire interactions
  const handleWireClick = useCallback((e, connIndex) => {
    e.stopPropagation();
    setSelectedWire(connIndex); setSelectedBlock(null); setGainEditBlock(null);
  }, []);

  const handleWireBranch = useCallback((e, connIndex) => {
    e.stopPropagation(); e.preventDefault();
    const conn = connections[connIndex];
    if (!conn) return;
    const sourceBlock = blocks[conn.from_block];
    const targetBlock = blocks[conn.to_block];
    if (!sourceBlock || !targetBlock) return;
    const { x: clickX, y: clickY } = getSvgCoords(e.clientX, e.clientY);
    const startPos = getPortPosition(sourceBlock, 'output', conn.from_port);
    const endPos = getPortPosition(targetBlock, 'input', conn.to_port);
    const pts = routeWire(startPos, endPos, blocks, [conn.from_block, conn.to_block]);
    let bestDist = Infinity, bestX = clickX, bestY = clickY, bestDir = 'right';
    for (let i = 0; i < pts.length - 1; i++) {
      const [ax, ay] = pts[i], [bx, by] = pts[i + 1];
      const dx = bx - ax, dy = by - ay;
      const len2 = dx * dx + dy * dy;
      if (len2 < 1) continue;
      const t = Math.max(0, Math.min(1, ((clickX - ax) * dx + (clickY - ay) * dy) / len2));
      const px = ax + t * dx, py = ay + t * dy;
      const dist = (clickX - px) ** 2 + (clickY - py) ** 2;
      if (dist < bestDist) {
        bestDist = dist; bestX = px; bestY = py;
        const isHorizontal = Math.abs(dy) < Math.abs(dx);
        if (isHorizontal) bestDir = clickY < py ? 'up' : 'down';
        else bestDir = clickX > px ? 'right' : 'left';
      }
    }
    setWireStart({
      blockId: conn.from_block, portIndex: conn.from_port,
      x: bestX, y: bestY, dir: bestDir,
      branchPoint: { x: Math.round(bestX), y: Math.round(bestY), dir: bestDir },
    });
    setSelectedWire(null);
  }, [connections, blocks, getSvgCoords]);

  const handleWireMouseDown = useCallback((e, connIndex) => {
    if (e.ctrlKey || e.metaKey) handleWireBranch(e, connIndex);
  }, [handleWireBranch]);

  // Zoom
  const handleZoomIn = useCallback(() => setZoom(z => Math.min(MAX_ZOOM, z + ZOOM_STEP)), []);
  const handleZoomOut = useCallback(() => setZoom(z => Math.max(MIN_ZOOM, z - ZOOM_STEP)), []);
  const handleZoomReset = useCallback(() => { setZoom(1.0); setPanOffset({ x: 0, y: 0 }); }, []);

  const handleWheel = useCallback((e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -ZOOM_STEP : ZOOM_STEP;
    setZoom(prevZoom => Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, prevZoom + delta)));
  }, []);

  useEffect(() => {
    const svg = svgRef.current;
    if (svg) {
      svg.addEventListener('wheel', handleWheel, { passive: false });
      return () => svg.removeEventListener('wheel', handleWheel);
    }
  }, [handleWheel]);

  // Pan
  const handlePanStart = useCallback((e) => {
    const isCanvasBg = e.target === svgRef.current || e.target.classList.contains('bd-grid-bg');
    if (e.button === 1 || (e.altKey && e.button === 0) || (e.button === 0 && isCanvasBg)) {
      e.preventDefault();
      setIsPanning(true);
      panStart.current = { x: e.clientX, y: e.clientY, ox: panOffset.x, oy: panOffset.y };
    }
  }, [panOffset]);

  const handlePanMove = useCallback((e) => {
    if (isPanning) {
      const dx = (e.clientX - panStart.current.x) / zoom;
      const dy = (e.clientY - panStart.current.y) / zoom;
      if (Math.abs(dx) > 2 || Math.abs(dy) > 2) didPanRef.current = true;
      setPanOffset({ x: panStart.current.ox + dx, y: panStart.current.oy + dy });
    }
  }, [isPanning, zoom]);

  const handlePanEnd = useCallback(() => setIsPanning(false), []);

  // Computed viewBox
  const { viewBox, visibleRect } = useMemo(() => {
    const vw = CANVAS_WIDTH / zoom;
    const vh = CANVAS_HEIGHT / zoom;
    const vx = (CANVAS_WIDTH - vw) / 2 - panOffset.x;
    const vy = (CANVAS_HEIGHT - vh) / 2 - panOffset.y;
    const pad = GRID_SIZE * 4;
    const gx = Math.floor((vx - pad) / GRID_SIZE) * GRID_SIZE;
    const gy = Math.floor((vy - pad) / GRID_SIZE) * GRID_SIZE;
    const gw = Math.ceil((vw + pad * 2) / GRID_SIZE) * GRID_SIZE;
    const gh = Math.ceil((vh + pad * 2) / GRID_SIZE) * GRID_SIZE;
    return { viewBox: `${vx} ${vy} ${vw} ${vh}`, visibleRect: { x: gx, y: gy, width: gw, height: gh } };
  }, [zoom, panOffset]);

  // Dynamic adder port positions — compute optimal port placement based on connected blocks
  const adderPortMap = useMemo(() => {
    const map = {};
    const portDist = PORT_OFFSETS.adder.left; // 48px from center

    Object.values(blocks).forEach(block => {
      if (block.type !== 'adder') return;

      // Gather all connections to this adder
      const portConnections = {}; // portIndex → { dx, dy, blockId, isOutput }
      connections.forEach(conn => {
        if (conn.to_block === block.id) {
          const srcBlock = blocks[conn.from_block];
          if (srcBlock) {
            portConnections[conn.to_port] = {
              dx: srcBlock.position.x - block.position.x,
              dy: srcBlock.position.y - block.position.y,
              blockId: conn.from_block,
              isOutput: false
            };
          }
        }
        if (conn.from_block === block.id) {
          const tgtBlock = blocks[conn.to_block];
          if (tgtBlock) {
            portConnections[conn.from_port] = {
              dx: tgtBlock.position.x - block.position.x,
              dy: tgtBlock.position.y - block.position.y,
              blockId: conn.to_block,
              isOutput: true
            };
          }
        }
      });

      // If no connections, keep defaults
      if (Object.keys(portConnections).length === 0) return;

      // Assign each port to the best cardinal direction based on angle to connected block
      const usedDirs = new Set();
      const portEntries = Object.entries(portConnections);
      const portPositions = {};

      // Cardinal direction vectors: { dir, dx, dy }
      const cardinals = [
        { dir: 'left', dx: -portDist, dy: 0 },
        { dir: 'right', dx: portDist, dy: 0 },
        { dir: 'up', dx: 0, dy: -portDist },
        { dir: 'down', dx: 0, dy: portDist },
      ];

      // Sort ports: output port first (it gets priority), then inputs
      portEntries.sort((a, b) => {
        if (a[1].isOutput && !b[1].isOutput) return -1;
        if (!a[1].isOutput && b[1].isOutput) return 1;
        return 0;
      });

      for (const [portIdx, info] of portEntries) {
        const angle = Math.atan2(info.dy, info.dx);
        // Score each cardinal direction — lower is better (closer angle match)
        let bestCard = null;
        let bestScore = Infinity;
        for (const card of cardinals) {
          if (usedDirs.has(card.dir)) continue;
          const cardAngle = Math.atan2(card.dy, card.dx);
          let angleDiff = Math.abs(angle - cardAngle);
          if (angleDiff > Math.PI) angleDiff = 2 * Math.PI - angleDiff;
          if (angleDiff < bestScore) {
            bestScore = angleDiff;
            bestCard = card;
          }
        }
        if (bestCard) {
          usedDirs.add(bestCard.dir);
          portPositions[portIdx] = {
            dx: bestCard.dx,
            dy: bestCard.dy,
            dir: bestCard.dir
          };
        }
      }

      if (Object.keys(portPositions).length > 0) {
        map[block.id] = portPositions;
      }
    });

    return map;
  }, [blocks, connections]);

  // Per-block flow direction: port-based signal flow analysis
  // RTL = signal enters on port 1 (right side) and exits from port 0 (left side)
  // This is the standard convention for feedback blocks in direct-form realizations
  const blockFlowDir = useMemo(() => {
    const dirs = {};
    Object.keys(blocks).forEach(blockId => {
      const block = blocks[blockId];
      // Fixed-direction blocks
      if (['input', 'output', 'adder', 'junction', 'constant'].includes(block.type)) {
        dirs[blockId] = 'ltr'; return;
      }

      // For gain/delay/integrator: check port usage pattern
      // LTR: input on port 0 (left), output on port 1 (right) — standard forward path
      // RTL: input on port 1 (right), output on port 0 (left) — feedback path convention
      let hasInputOnPort1 = false;
      let hasOutputOnPort0 = false;
      let hasInputOnPort0 = false;
      let hasOutputOnPort1 = false;

      connections.forEach(conn => {
        if (conn.to_block === blockId) {
          if (conn.to_port === 1) hasInputOnPort1 = true;
          if (conn.to_port === 0) hasInputOnPort0 = true;
        }
        if (conn.from_block === blockId) {
          if (conn.from_port === 0) hasOutputOnPort0 = true;
          if (conn.from_port === 1) hasOutputOnPort1 = true;
        }
      });

      // RTL when input arrives on port 1 AND output leaves from port 0
      if (hasInputOnPort1 && hasOutputOnPort0) {
        dirs[blockId] = 'rtl';
      } else if (hasInputOnPort1 && !hasOutputOnPort1) {
        // Input only on port 1 (no through-path output known yet) — likely RTL
        dirs[blockId] = 'rtl';
      } else {
        dirs[blockId] = 'ltr';
      }
    });
    return dirs;
  }, [blocks, connections]);

  // Branch points — must come AFTER adderPortMap and blockFlowDir for correct port positions
  const { branchPoints, autoBranchMap } = useMemo(() => {
    const points = [];
    const autoMap = {};
    const portGroups = {};
    connections.forEach((conn, idx) => {
      const key = `${conn.from_block}:${conn.from_port}`;
      if (!portGroups[key]) portGroups[key] = [];
      portGroups[key].push(idx);
    });

    Object.entries(portGroups).forEach(([key, indices]) => {
      if (indices.length < 2) return;
      const mainConn = connections[indices[0]];
      const [blockId, portIdx] = key.split(':');
      const block = blocks[blockId];
      if (!block) return;
      const portPos = getPortPosition(block, 'output', parseInt(portIdx), blockFlowDir, adderPortMap);
      const mainTarget = blocks[mainConn.to_block];
      if (!mainTarget) return;
      const mainEnd = getPortPosition(mainTarget, 'input', mainConn.to_port, blockFlowDir, adderPortMap);
      const mainPts = routeWire(portPos, mainEnd, blocks, [mainConn.from_block, mainConn.to_block]);

      // OPTIMAL branch point: sample all grid points along main wire,
      // choose the one that minimizes total Manhattan distance to all branch target PORTS
      const branchTargetPortPositions = [];
      for (let i = 1; i < indices.length; i++) {
        const bConn = connections[indices[i]];
        const bTarget = blocks[bConn.to_block];
        if (bTarget) {
          const targetPortPos = getPortPosition(bTarget, 'input', bConn.to_port, blockFlowDir, adderPortMap);
          branchTargetPortPositions.push(targetPortPos);
        }
      }

      // Build candidate points along the main wire at grid intervals
      const candidates = [];
      if (mainPts.length >= 2) {
        let accumulated = 0;
        for (let s = 0; s < mainPts.length - 1; s++) {
          const [ax, ay] = mainPts[s], [bx, by] = mainPts[s + 1];
          const segLen = Math.abs(bx - ax) + Math.abs(by - ay);
          if (segLen < 1) continue;
          const steps = Math.max(1, Math.round(segLen / GRID_SIZE));
          for (let step = 0; step <= steps; step++) {
            const t = step / steps;
            const cx = snapToGrid(ax + t * (bx - ax));
            const cy = snapToGrid(ay + t * (by - ay));
            const dist = accumulated + segLen * t;
            if (dist < GRID_SIZE || dist > accumulated + segLen - GRID_SIZE * 0.5) continue;
            candidates.push({ x: cx, y: cy, dist });
          }
          accumulated += segLen;
        }
      }

      let bpX = portPos.x + GRID_SIZE, bpY = portPos.y;
      if (candidates.length > 0 && branchTargetPortPositions.length > 0) {
        let bestScore = Infinity;
        for (const cand of candidates) {
          let totalDist = 0;
          for (const tp of branchTargetPortPositions) {
            totalDist += Math.abs(cand.x - tp.x) + Math.abs(cand.y - tp.y);
          }
          if (totalDist < bestScore) {
            bestScore = totalDist;
            bpX = cand.x;
            bpY = cand.y;
          }
        }
      } else if (candidates.length > 0) {
        const mid = candidates[Math.floor(candidates.length / 2)];
        bpX = mid.x;
        bpY = mid.y;
      }
      points.push({ x: bpX, y: bpY });

      for (let i = 1; i < indices.length; i++) {
        const conn = connections[indices[i]];
        const target = blocks[conn.to_block];
        let branchDir = 'down';
        if (target) {
          const targetPort = getPortPosition(target, 'input', conn.to_port, blockFlowDir, adderPortMap);
          const tdx = targetPort.x - bpX;
          const tdy = targetPort.y - bpY;
          if (Math.abs(tdy) > Math.abs(tdx)) {
            branchDir = tdy > 0 ? 'down' : 'up';
          } else {
            branchDir = tdx > 0 ? 'right' : 'left';
          }
        }
        autoMap[indices[i]] = { x: bpX, y: bpY, dir: branchDir };
      }
    });
    return { branchPoints: points, autoBranchMap: autoMap };
  }, [connections, blocks, blockFlowDir, adderPortMap]);

  // Available block types
  const availableBlocks = useMemo(() => {
    const base = ['input', 'output', 'gain', 'constant', 'adder'];
    if (systemType === 'dt') base.push('delay');
    else base.push('integrator');
    return base;
  }, [systemType]);

  const blockLabels = {
    input: 'Input', output: 'Output', gain: 'Gain', constant: 'Const',
    adder: 'Adder', delay: 'Delay', integrator: 'Integ', junction: 'Junct',
  };

  const blockIcons = {
    input: '\u2192', output: '\u2190', gain: '\u25B7', constant: 'K',
    adder: '\u2295', delay: '\u25FB', integrator: '\u222B', junction: '\u25CF',
  };

  // Gain edit position
  const gainEditPos = useMemo(() => {
    if (!gainEditBlock || !blocks[gainEditBlock] || !svgRef.current) return null;
    const block = blocks[gainEditBlock];
    const svg = svgRef.current;
    const svgRect = svg.getBoundingClientRect();
    const ctm = svg.getScreenCTM();
    if (!ctm) return null;
    const screenX = block.position.x * ctm.a + ctm.e - svgRect.left;
    const screenY = (block.position.y - 35) * ctm.d + ctm.f - svgRect.top;
    return { left: screenX, top: screenY };
  }, [gainEditBlock, blocks]);

  // Export handlers
  const handleExportSVG = useCallback(() => exportSVG(svgRef.current), []);
  const handleExportPNG = useCallback(() => exportPNG(svgRef.current), []);

  // ========================================================================
  // Render
  // ========================================================================

  return (
    <div className="block-diagram-viewer">
      {isLoading && (
        <div className="bd-loading-bar"><div className="bd-loading-bar-inner" /></div>
      )}

      {/* Toolbar */}
      <div className="bd-toolbar">
        <div className="bd-toolbar-section bd-toolbar-palette">
          <span className="bd-toolbar-label">Blocks</span>
          {availableBlocks.map(type => (
            <button key={type} className="bd-palette-btn" onClick={() => handleAddBlock(type)} title={`Add ${type} block`}>
              <span className="bd-palette-icon">{blockIcons[type]}</span>
              <span className="bd-palette-text">{blockLabels[type]}</span>
            </button>
          ))}
        </div>

        <div className="bd-toolbar-divider" />

        <div className="bd-toolbar-section">
          <span className="bd-toolbar-label">Mode</span>
          <div className="bd-toggle-group">
            <button className={`bd-toggle-btn ${mode === 'build' ? 'active' : ''}`} onClick={() => handleModeChange('build')}>Build</button>
            <button className={`bd-toggle-btn ${mode === 'parse' ? 'active' : ''}`} onClick={() => handleModeChange('parse')}>Parse TF</button>
          </div>
        </div>

        <div className="bd-toolbar-section">
          <span className="bd-toolbar-label">Type</span>
          <div className="bd-toggle-group">
            <button className={`bd-toggle-btn ${systemType === 'dt' ? 'active' : ''}`} onClick={() => handleSystemTypeChange('dt')}>DT</button>
            <button className={`bd-toggle-btn ${systemType === 'ct' ? 'active' : ''}`} onClick={() => handleSystemTypeChange('ct')}>CT</button>
          </div>
        </div>

        <div className="bd-toolbar-divider" />

        <div className="bd-toolbar-section bd-toolbar-actions">
          <button className="bd-action-btn bd-undo-btn" onClick={handleUndo} title="Undo (Ctrl+Z)">
            <span className="bd-btn-icon">&#x21A9;</span> Undo
          </button>
          <button className="bd-action-btn bd-redo-btn" onClick={handleRedo} title="Redo (Ctrl+Shift+Z)">
            <span className="bd-btn-icon">&#x21AA;</span> Redo
          </button>
          <button className="bd-action-btn" onClick={handleAutoArrange} title="Auto Arrange">
            <span className="bd-btn-icon">&#x2630;</span> Arrange
          </button>
          <button className="bd-action-btn bd-clear-btn" onClick={handleClear}>
            <span className="bd-btn-icon">&times;</span> Clear
          </button>
          <div className="bd-preset-dropdown" ref={presetRef}>
            <button className={`bd-action-btn bd-preset-toggle ${presetOpen ? 'open' : ''}`} onClick={() => setPresetOpen(!presetOpen)}>
              Presets {presetOpen ? '\u25B4' : '\u25BE'}
            </button>
            {presetOpen && (
              <div className="bd-preset-menu">
                {Object.keys(presets).length === 0 && <div className="bd-preset-empty">No presets available</div>}
                {Object.entries(presets).map(([key, preset]) => (
                  <button key={key} className="bd-preset-item" onClick={() => handleLoadPreset(key)}>
                    <span className="bd-preset-name">{preset.name}</span>
                    <span className="bd-preset-eq">{preset.equation}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
          <div className="bd-toolbar-divider" />
          <button className="bd-action-btn" onClick={handleExportSVG} title="Export SVG">SVG</button>
          <button className="bd-action-btn" onClick={handleExportPNG} title="Export PNG">PNG</button>
        </div>
      </div>

      {/* Parse mode input */}
      {mode === 'parse' && (
        <div className="bd-parse-bar">
          <span className="bd-parse-label">Transfer Function:</span>
          <input
            type="text" className="bd-tf-input" value={tfInput}
            onChange={(e) => setTfInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleParseTf(); }}
            placeholder={systemType === 'dt' ? 'e.g. (1 - R) / (1 - 0.5R)' : 'e.g. 1 / (s + 2)'}
          />
          <button className="bd-parse-btn" onClick={handleParseTf} disabled={isLoading}>
            {isLoading ? 'Generating...' : 'Generate Diagram'}
          </button>
        </div>
      )}

      {/* Transfer Function display */}
      {(tfResult || error || Object.keys(blocks).length > 0) && (
        <div className="bd-tf-bar">
          {error ? (
            <span className="bd-tf-bar-error">{error}</span>
          ) : tfResult ? (
            <>
              <LaTeX math={tfResult.latex || tfResult.expression} className="bd-tf-bar-expr" />
              {tfResult.domain_latex && (
                <>
                  <span className="bd-tf-bar-eq">=</span>
                  <LaTeX math={`H(${systemType === 'dt' ? 'z' : 's'}) = ${tfResult.domain_latex}`} className="bd-tf-bar-expr" />
                </>
              )}
              <span className={`bd-tf-bar-stability ${tfResult.stability}`}>
                {tfResult.stability === 'stable' ? '\u2713 Stable'
                 : tfResult.stability === 'marginally_stable' ? '\u25CB Marginal'
                 : '\u2717 Unstable'}
              </span>
              {tfResult.poles && tfResult.poles.length > 0 && (
                <span className="bd-tf-bar-poles" title={tfResult.poles.map(p => p.imag !== 0 ? `${p.real.toFixed(3)} \u00B1 ${Math.abs(p.imag).toFixed(3)}j` : p.real.toFixed(3)).join(', ')}>
                  Poles: {tfResult.poles.length}
                </span>
              )}
              {tfResult.algebraic_loop_warning && (
                <span className="bd-tf-bar-warning" title={tfResult.algebraic_loop_warning}>{'\u26A0'} Algebraic Loop</span>
              )}
            </>
          ) : (
            <span className="bd-tf-bar-hint">Connect Input \u2192 blocks \u2192 Output to compute TF</span>
          )}
        </div>
      )}

      <div className="bd-main-area">
        <div className="bd-canvas-container">
          <svg
            ref={svgRef} width="100%" height="100%" viewBox={viewBox}
            preserveAspectRatio="xMidYMid meet"
            className={`bd-canvas ${isPanning ? 'bd-panning' : ''}`}
            onMouseMove={(e) => { handleSvgMouseMove(e); handlePanMove(e); }}
            onMouseUp={(e) => { handleSvgMouseUp(e); handlePanEnd(); }}
            onMouseDown={handlePanStart}
            onClick={handleCanvasClick}
          >
            <defs>
              <marker id="arrowhead" markerWidth="10" markerHeight="8" refX="10" refY="4" orient="auto">
                <polygon points="0 0, 10 4, 0 8" fill="var(--bd-wire-color, #007acc)" />
              </marker>
              <filter id="blockShadow" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="4" stdDeviation="6" floodColor="rgba(0,0,0,0.15)" />
              </filter>
              <pattern id="grid" width={GRID_SIZE} height={GRID_SIZE} patternUnits="userSpaceOnUse">
                <line x1={GRID_SIZE} y1="0" x2={GRID_SIZE} y2={GRID_SIZE} stroke="var(--bd-grid-color, #e5e5e5)" strokeWidth="0.5" opacity="0.3" />
                <line x1="0" y1={GRID_SIZE} x2={GRID_SIZE} y2={GRID_SIZE} stroke="var(--bd-grid-color, #e5e5e5)" strokeWidth="0.5" opacity="0.3" />
              </pattern>
            </defs>

            <rect x={visibleRect.x} y={visibleRect.y} width={visibleRect.width} height={visibleRect.height} fill="url(#grid)" className="bd-grid-bg" />

            {/* Wires */}
            {connections.map((conn, i) => (
              <Wire
                key={`${conn.from_block}-${conn.to_block}-${conn.to_port}-${i}`}
                connection={conn} blocks={blocks} autoBranch={autoBranchMap[i]}
                isNew={i === newWireIndex} isSelected={i === selectedWire}
                onWireClick={(e) => handleWireClick(e, i)}
                onWireMouseDown={(e) => handleWireMouseDown(e, i)}
                onWireDoubleClick={(e) => handleWireBranch(e, i)}
                flowDirMap={blockFlowDir} adderPortMap={adderPortMap}
              />
            ))}

            {branchPoints.map((pt, i) => (
              <circle key={`branch-${i}`} cx={pt.x} cy={pt.y} r={5} className="bd-branch-dot" />
            ))}

            {wireStart && <WireInProgress startPos={wireStart} mousePos={mousePos} />}
            {connectionFlash && <ConnectionFlash position={connectionFlash.position} success={connectionFlash.success} />}

            {/* Blocks */}
            {Object.values(blocks).map(block => {
              const commonProps = {
                block, isSelected: selectedBlock === block.id,
                onMouseDown: handleBlockMouseDown,
                onPortMouseDown: handlePortMouseDown,
                onPortMouseUp: handlePortMouseUp,
              };
              const flowDir = blockFlowDir[block.id] || 'ltr';
              switch (block.type) {
                case 'input':
                  return <InputBlock key={block.id} {...commonProps} systemType={systemType} />;
                case 'output':
                  return <OutputBlock key={block.id} {...commonProps} systemType={systemType} />;
                case 'gain':
                  return <GainBlock key={block.id} {...commonProps} flowDir={flowDir} onGainDoubleClick={handleGainDoubleClick} />;
                case 'constant':
                  return <ConstantBlock key={block.id} {...commonProps} onGainDoubleClick={handleGainDoubleClick} />;
                case 'adder':
                  return <AdderBlock key={block.id} {...commonProps} onToggleSign={handleToggleSign} dynamicPorts={adderPortMap[block.id]} />;
                case 'delay':
                  return <DelayBlock key={block.id} {...commonProps} flowDir={flowDir} />;
                case 'integrator':
                  return <IntegratorBlock key={block.id} {...commonProps} flowDir={flowDir} />;
                case 'junction':
                  return <JunctionBlock key={block.id} {...commonProps} connections={connections} />;
                default: return null;
              }
            })}
          </svg>

          {/* Gain/constant edit overlay */}
          {gainEditBlock && blocks[gainEditBlock] && gainEditPos && (
            <div className="bd-gain-edit-overlay" style={{ left: `${gainEditPos.left}px`, top: `${gainEditPos.top}px` }}>
              <label className="bd-gain-edit-label">{blocks[gainEditBlock]?.type === 'constant' ? 'Constant' : 'Gain'} value</label>
              <input
                type="number" className="bd-gain-edit-input"
                value={gainEditValue}
                onChange={(e) => setGainEditValue(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') handleGainEditSubmit(); if (e.key === 'Escape') setGainEditBlock(null); }}
                onBlur={handleGainEditSubmit} autoFocus step="0.1"
              />
            </div>
          )}

          {/* Instructions */}
          {Object.keys(blocks).length === 0 && mode === 'build' && (
            <div className="bd-instructions-overlay">
              <div className="bd-instructions-icon">&#9881;</div>
              <p className="bd-instructions-title">Block Diagram Builder</p>
              <p>Click a block type above to add it, or load a preset.</p>
              <p>Drag from ports to connect blocks. Double-click gain/constant blocks to edit values.</p>
              <p>Click a wire to select it. Press <kbd>Delete</kbd> to remove. <kbd>Ctrl</kbd>+click a wire to branch.</p>
              <p className="bd-instructions-hint"><kbd>Ctrl+Z</kbd> undo, <kbd>Ctrl+Shift+Z</kbd> redo. Hold <kbd>Ctrl</kbd> while dragging for free positioning.</p>
            </div>
          )}

          {/* Zoom controls */}
          <div className="bd-zoom-controls">
            <button className="bd-zoom-btn" onClick={handleZoomIn} title="Zoom In">+</button>
            <span className="bd-zoom-level">{Math.round(zoom * 100)}%</span>
            <button className="bd-zoom-btn" onClick={handleZoomOut} title="Zoom Out">&minus;</button>
            <button className="bd-zoom-btn bd-zoom-reset" onClick={handleZoomReset} title="Reset View">&#8634;</button>
          </div>

          {error && <div className="bd-canvas-error">{error}</div>}
        </div>
      </div>
    </div>
  );
}

export default BlockDiagramViewer;
