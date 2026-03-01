/**
 * BlockDiagramViewer Component
 *
 * Interactive SVG-based block diagram builder.
 * Two modes:
 *   1. Build Mode — drag/drop blocks, draw wires → compute transfer function
 *   2. Parse Mode — enter transfer function → generate block diagram
 *
 * Block types: Input, Output, Gain, Adder, Delay (DT), Integrator (CT)
 */

import React, { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import api from '../services/api';
import '../styles/BlockDiagramViewer.css';

// ============================================================================
// Constants
// ============================================================================

const BLOCK_SIZES = {
  input: { width: 110, height: 54 },
  output: { width: 110, height: 54 },
  gain: { width: 100, height: 68 },
  adder: { radius: 34 },
  delay: { width: 82, height: 54 },
  integrator: { width: 82, height: 54 },
  junction: { radius: 6 },
};

const COLLISION_PAD = 12; // px clearance around blocks for collision avoidance

// ============================================================================
// Wire Routing Utilities
// ============================================================================

function pointsToPath(pts) {
  // Deduplicate consecutive identical points, then build SVG path
  const clean = [pts[0]];
  for (let i = 1; i < pts.length; i++) {
    const [px, py] = pts[i], [cx, cy] = clean[clean.length - 1];
    if (Math.abs(px - cx) > 0.5 || Math.abs(py - cy) > 0.5) clean.push(pts[i]);
  }
  let d = `M ${clean[0][0]} ${clean[0][1]}`;
  for (let i = 1; i < clean.length; i++) d += ` L ${clean[i][0]} ${clean[i][1]}`;
  return d;
}

function getBlockBounds(block) {
  const { x, y } = block.position;
  const type = block.type;
  if (type === 'adder') {
    const r = BLOCK_SIZES.adder.radius;
    return { left: x - r - COLLISION_PAD, right: x + r + COLLISION_PAD,
             top: y - r - COLLISION_PAD, bottom: y + r + COLLISION_PAD };
  }
  if (type === 'junction') {
    const r = BLOCK_SIZES.junction.radius;
    return { left: x - r - COLLISION_PAD, right: x + r + COLLISION_PAD,
             top: y - r - COLLISION_PAD, bottom: y + r + COLLISION_PAD };
  }
  const size = BLOCK_SIZES[type] || { width: 100, height: 54 };
  const hw = size.width / 2, hh = size.height / 2;
  return { left: x - hw - COLLISION_PAD, right: x + hw + COLLISION_PAD,
           top: y - hh - COLLISION_PAD, bottom: y + hh + COLLISION_PAD };
}

function hSegIntersectsRect(x1, x2, y, rect) {
  const minX = Math.min(x1, x2), maxX = Math.max(x1, x2);
  return y >= rect.top && y <= rect.bottom && maxX > rect.left && minX < rect.right;
}

function vSegIntersectsRect(x, y1, y2, rect) {
  const minY = Math.min(y1, y2), maxY = Math.max(y1, y2);
  return x >= rect.left && x <= rect.right && maxY > rect.top && minY < rect.bottom;
}

function avoidCollisions(points, allBlocks, excludeIds) {
  // Post-process wire points to route around block bounding boxes
  if (!allBlocks || Object.keys(allBlocks).length === 0) return points;

  // Build list of bounding boxes to check against (exclude source/target blocks)
  const obstacles = [];
  Object.values(allBlocks).forEach(block => {
    if (excludeIds.includes(block.id)) return;
    obstacles.push({ id: block.id, bounds: getBlockBounds(block), center: block.position });
  });
  if (obstacles.length === 0) return points;

  let result = [...points.map(p => [...p])];
  // Iterate segments and check for collisions — up to 3 passes to handle cascading fixes
  for (let pass = 0; pass < 3; pass++) {
    let changed = false;
    const newResult = [result[0]];

    for (let i = 0; i < result.length - 1; i++) {
      const [x1, y1] = result[i];
      const [x2, y2] = result[i + 1];
      const isHoriz = Math.abs(y1 - y2) < 0.5;
      const isVert = Math.abs(x1 - x2) < 0.5;

      let collisionFound = false;

      if (isHoriz) {
        // Check horizontal segment against all obstacles
        for (const obs of obstacles) {
          if (hSegIntersectsRect(x1, x2, y1, obs.bounds)) {
            // Route around: go above or below the block
            const blockCenterY = obs.center.y;
            const newY = y1 <= blockCenterY ? obs.bounds.top - 2 : obs.bounds.bottom + 2;
            // Clamp detour to just the block's X range
            const segMinX = Math.min(x1, x2), segMaxX = Math.max(x1, x2);
            const detourLeft = Math.max(segMinX, obs.bounds.left - 2);
            const detourRight = Math.min(segMaxX, obs.bounds.right + 2);
            // Insert detour points: approach block, shift Y, cross over, shift back
            newResult.push([detourLeft, y1]);
            newResult.push([detourLeft, newY]);
            newResult.push([detourRight, newY]);
            newResult.push([detourRight, y2]);
            collisionFound = true;
            changed = true;
            break; // Handle one collision per segment per pass
          }
        }
      } else if (isVert) {
        // Check vertical segment against all obstacles
        for (const obs of obstacles) {
          if (vSegIntersectsRect(x1, y1, y2, obs.bounds)) {
            // Route around: go left or right of the block
            const blockCenterX = obs.center.x;
            const newX = x1 <= blockCenterX ? obs.bounds.left - 2 : obs.bounds.right + 2;
            const segMinY = Math.min(y1, y2), segMaxY = Math.max(y1, y2);
            const detourTop = Math.max(segMinY, obs.bounds.top - 2);
            const detourBot = Math.min(segMaxY, obs.bounds.bottom + 2);
            newResult.push([x1, detourTop]);
            newResult.push([newX, detourTop]);
            newResult.push([newX, detourBot]);
            newResult.push([x1, detourBot]);
            collisionFound = true;
            changed = true;
            break;
          }
        }
      }

      if (!collisionFound) {
        newResult.push([x2, y2]);
      } else {
        newResult.push([x2, y2]);
      }
    }

    result = newResult;
    if (!changed) break;
  }

  return result;
}

const PORT_RADIUS = 8;
const CANVAS_WIDTH = 900;
const CANVAS_HEIGHT = 650;
const MIN_ZOOM = 0.5;
const MAX_ZOOM = 3.0;
const ZOOM_STEP = 0.15;
const GRID_SIZE = 24;

function snapToGrid(val) {
  return Math.round(val / GRID_SIZE) * GRID_SIZE;
}

// ============================================================================
// SVG Block Components
// ============================================================================

function InputBlock({ block, isSelected, onMouseDown, onPortMouseDown, systemType }) {
  const { x, y } = block.position;
  const w = BLOCK_SIZES.input.width, h = BLOCK_SIZES.input.height;
  const label = systemType === 'ct' ? 'x(t)' : 'x[n]';
  return (
    <g
      className={`bd-block ${isSelected ? 'bd-block-selected' : ''}`}
      onMouseDown={(e) => onMouseDown(e, block.id)}
      transform={`translate(${x}, ${y})`}
    >
      <rect x={-w/2} y={-h/2} width={w} height={h} rx={8} className="bd-block-shape bd-block-io" />
      <text x={-4} y={1} textAnchor="middle" dominantBaseline="middle" className="bd-block-label">{label}</text>
      {/* Arrow indicator */}
      <polygon points={`${w/2-10},-8 ${w/2},0 ${w/2-10},8`} className="bd-block-arrow" />
      {/* Output port */}
      <circle
        cx={w/2+13} cy={0} r={PORT_RADIUS}
        className="bd-port bd-port-output"
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'output', 0, x + w/2+13, y); }}
      />
    </g>
  );
}

function OutputBlock({ block, isSelected, onMouseDown, onPortMouseUp, systemType }) {
  const { x, y } = block.position;
  const w = BLOCK_SIZES.output.width, h = BLOCK_SIZES.output.height;
  const label = systemType === 'ct' ? 'y(t)' : 'y[n]';
  return (
    <g
      className={`bd-block ${isSelected ? 'bd-block-selected' : ''}`}
      onMouseDown={(e) => onMouseDown(e, block.id)}
      transform={`translate(${x}, ${y})`}
    >
      <rect x={-w/2} y={-h/2} width={w} height={h} rx={8} className="bd-block-shape bd-block-io" />
      {/* Arrow indicator */}
      <polygon points={`${-w/2+10},-8 ${-w/2},0 ${-w/2+10},8`} className="bd-block-arrow bd-block-arrow-in" />
      <text x={4} y={1} textAnchor="middle" dominantBaseline="middle" className="bd-block-label">{label}</text>
      {/* Input port */}
      <circle
        cx={-(w/2+13)} cy={0} r={PORT_RADIUS}
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
  // Triangle points right when ltr, left when rtl
  const triPoints = flipped ? "50,-34 -50,0 50,34" : "-50,-34 50,0 -50,34";
  const textX = flipped ? 10 : -10;
  const hintX = flipped ? -36 : 36;
  return (
    <g
      className={`bd-block ${isSelected ? 'bd-block-selected' : ''}`}
      onMouseDown={(e) => onMouseDown(e, block.id)}
      onDoubleClick={(e) => { e.stopPropagation(); onGainDoubleClick(block.id); }}
      transform={`translate(${x}, ${y})`}
    >
      <polygon points={triPoints} className="bd-block-shape bd-block-gain" />
      {/* Gain value */}
      <text x={textX} y={2} textAnchor="middle" dominantBaseline="middle" className="bd-block-value">
        {typeof value === 'number' ? (Number.isInteger(value) ? value : value.toFixed(2)) : value}
      </text>
      {/* Edit hint icon (pencil) */}
      <g className="bd-gain-edit-hint" transform={`translate(${hintX}, -28)`}>
        <rect x={-10} y={-10} width={20} height={20} rx={5} className="bd-gain-hint-bg" />
        <text x={0} y={1} textAnchor="middle" dominantBaseline="middle" className="bd-gain-hint-icon">&#9998;</text>
      </g>
      {/* Left port — bidirectional */}
      <circle
        cx={-58} cy={0} r={PORT_RADIUS}
        className="bd-port"
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 0, x - 58, y, 'left'); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 0); }}
      />
      {/* Right port — bidirectional */}
      <circle
        cx={58} cy={0} r={PORT_RADIUS}
        className="bd-port"
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 1, x + 58, y, 'right'); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 1); }}
      />
    </g>
  );
}

function AdderBlock({ block, isSelected, onMouseDown, onPortMouseDown, onPortMouseUp, onToggleSign }) {
  const { x, y } = block.position;
  // 3 signs — one per port (left, bottom, right)
  const rawSigns = block.signs || ['+', '+', '+'];
  const signs = [rawSigns[0] || '+', rawSigns[1] || '+', rawSigns[2] || '+'];
  const r = BLOCK_SIZES.adder.radius;

  return (
    <g
      className={`bd-block ${isSelected ? 'bd-block-selected' : ''}`}
      onMouseDown={(e) => onMouseDown(e, block.id)}
      transform={`translate(${x}, ${y})`}
    >
      <circle cx={0} cy={0} r={r} className="bd-block-shape bd-block-adder" />
      {/* Cross lines inside adder */}
      <line x1={-10} y1={0} x2={10} y2={0} className="bd-adder-cross" />
      <line x1={0} y1={-10} x2={0} y2={10} className="bd-adder-cross" />

      {/* Port 0 (left) — bidirectional */}
      <circle
        cx={-(r + 13)} cy={0} r={PORT_RADIUS}
        className="bd-port"
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 0, x - (r + 13), y, 'left'); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 0); }}
      />
      <text
        x={-(r + 13)} y={-14}
        textAnchor="middle" className="bd-sign-label"
        onClick={(e) => { e.stopPropagation(); onToggleSign(block.id, 0); }}
        style={{ cursor: 'pointer' }}
      >
        {signs[0]}
      </text>

      {/* Port 1 (bottom) — bidirectional */}
      <circle
        cx={0} cy={r + 13} r={PORT_RADIUS}
        className="bd-port"
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 1, x, y + r + 13, 'down'); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 1); }}
      />
      <text
        x={14} y={r + 17}
        textAnchor="middle" className="bd-sign-label"
        onClick={(e) => { e.stopPropagation(); onToggleSign(block.id, 1); }}
        style={{ cursor: 'pointer' }}
      >
        {signs[1]}
      </text>

      {/* Port 2 (right) — output only */}
      <circle
        cx={r + 13} cy={0} r={PORT_RADIUS}
        className="bd-port bd-port-output"
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'output', 2, x + r + 13, y, 'right'); }}
      />
      {/* No sign label on output port (port 2) */}
    </g>
  );
}

function DelayBlock({ block, isSelected, onMouseDown, onPortMouseDown, onPortMouseUp, flowDir = 'ltr' }) {
  const { x, y } = block.position;
  const flipped = flowDir === 'rtl';
  // Small arrow inside block showing signal flow direction
  const arrowX = flipped ? -22 : 22;
  const arrowPoints = flipped
    ? `${arrowX+6},-6 ${arrowX-2},0 ${arrowX+6},6`
    : `${arrowX-6},-6 ${arrowX+2},0 ${arrowX-6},6`;
  return (
    <g
      className={`bd-block ${isSelected ? 'bd-block-selected' : ''}`}
      onMouseDown={(e) => onMouseDown(e, block.id)}
      transform={`translate(${x}, ${y})`}
    >
      <rect x={-41} y={-27} width={82} height={54} rx={6} className="bd-block-shape bd-block-delay" />
      <text x={0} y={-5} textAnchor="middle" dominantBaseline="middle" className="bd-block-label">R</text>
      <text x={0} y={15} textAnchor="middle" dominantBaseline="middle" className="bd-block-sublabel">z&#x207B;&#xB9;</text>
      {/* Flow direction arrow */}
      <polygon points={arrowPoints} className="bd-block-arrow" opacity="0.5" />
      {/* Left port — bidirectional */}
      <circle
        cx={-50} cy={0} r={PORT_RADIUS}
        className="bd-port"
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 0, x - 50, y, 'left'); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 0); }}
      />
      {/* Right port — bidirectional */}
      <circle
        cx={50} cy={0} r={PORT_RADIUS}
        className="bd-port"
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 1, x + 50, y, 'right'); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 1); }}
      />
    </g>
  );
}

function IntegratorBlock({ block, isSelected, onMouseDown, onPortMouseDown, onPortMouseUp, flowDir = 'ltr' }) {
  const { x, y } = block.position;
  const flipped = flowDir === 'rtl';
  const arrowX = flipped ? -22 : 22;
  const arrowPoints = flipped
    ? `${arrowX+6},-6 ${arrowX-2},0 ${arrowX+6},6`
    : `${arrowX-6},-6 ${arrowX+2},0 ${arrowX-6},6`;
  return (
    <g
      className={`bd-block ${isSelected ? 'bd-block-selected' : ''}`}
      onMouseDown={(e) => onMouseDown(e, block.id)}
      transform={`translate(${x}, ${y})`}
    >
      <rect x={-41} y={-27} width={82} height={54} rx={6} className="bd-block-shape bd-block-integrator" />
      <text x={0} y={-5} textAnchor="middle" dominantBaseline="middle" className="bd-block-label" style={{ fontSize: '22px' }}>&int;</text>
      <text x={0} y={15} textAnchor="middle" dominantBaseline="middle" className="bd-block-sublabel">1/s</text>
      {/* Flow direction arrow */}
      <polygon points={arrowPoints} className="bd-block-arrow" opacity="0.5" />
      {/* Left port — bidirectional */}
      <circle
        cx={-50} cy={0} r={PORT_RADIUS}
        className="bd-port"
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 0, x - 50, y, 'left'); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 0); }}
      />
      {/* Right port — bidirectional */}
      <circle
        cx={50} cy={0} r={PORT_RADIUS}
        className="bd-port"
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 1, x + 50, y, 'right'); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 1); }}
      />
    </g>
  );
}

function JunctionBlock({ block, isSelected, onMouseDown, onPortMouseDown, onPortMouseUp, connections = [] }) {
  const { x, y } = block.position;
  const r = BLOCK_SIZES.junction.radius;

  // Find which output ports are in use
  const usedOutputPorts = new Set();
  connections.forEach(c => {
    if (c.from_block === block.id) usedOutputPorts.add(c.from_port);
  });
  // Next available output port
  const nextPort = Math.max(1, ...Array.from(usedOutputPorts)) + 1;

  // Port positions: port 0 = input (left), ports 1+ = outputs (radially arranged)
  const outputPorts = Array.from(usedOutputPorts).concat([nextPort]);
  const portAngles = { 1: 0, 2: -Math.PI / 2, 3: Math.PI / 2, 4: Math.PI };
  // Fallback: distribute evenly on right semicircle

  return (
    <g
      className={`bd-block ${isSelected ? 'bd-block-selected' : ''}`}
      onMouseDown={(e) => onMouseDown(e, block.id)}
      transform={`translate(${x}, ${y})`}
    >
      <circle cx={0} cy={0} r={r} className="bd-junction-dot" />

      {/* Port 0 (input) */}
      <circle
        cx={-(r + 8)} cy={0} r={PORT_RADIUS}
        className="bd-port"
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 0); }}
      />

      {/* Output ports */}
      {outputPorts.map(pIdx => {
        // Position: port 1 = right, port 2 = up, port 3 = down
        let px, py, dir;
        if (pIdx === 1) { px = r + 8; py = 0; dir = 'right'; }
        else if (pIdx === 2) { px = 0; py = -(r + 8); dir = 'up'; }
        else if (pIdx === 3) { px = 0; py = r + 8; dir = 'down'; }
        else { px = r + 8; py = (pIdx - 3) * 16; dir = 'right'; }
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
// Wire Component — adaptive Bezier curves
// ============================================================================

function Wire({ connection, blocks, isNew, isSelected, onWireClick, onWireDoubleClick }) {
  const fromBlock = blocks[connection.from_block];
  const toBlock = blocks[connection.to_block];
  if (!fromBlock || !toBlock) return null;

  const startPos = getPortPosition(fromBlock, 'output', connection.from_port);
  const endPos = getPortPosition(toBlock, 'input', connection.to_port);

  // Compute wire points, run collision avoidance, convert to SVG path
  const points = computeWirePoints(startPos, endPos, startPos.dir, endPos.dir);
  const safePoints = avoidCollisions(points, blocks, [connection.from_block, connection.to_block]);
  const d = pointsToPath(safePoints);

  return (
    <g className={`bd-wire-group ${isNew ? 'bd-wire-new' : ''} ${isSelected ? 'bd-wire-selected' : ''}`}>
      {/* Invisible wider hit area for clicking */}
      <path
        d={d}
        className="bd-wire-hit"
        onClick={onWireClick}
        onDoubleClick={onWireDoubleClick}
      />
      {/* Visible wire */}
      <path
        d={d}
        className="bd-wire"
        markerEnd="url(#arrowhead)"
      />
    </g>
  );
}

function computeWirePoints(startPos, endPos, startDir, endDir) {
  // Textbook-quality orthogonal wire routing.
  // Returns array of [x,y] points (NOT SVG path string).
  // Callers should run avoidCollisions() then pointsToPath() on the result.
  const sd = startDir || 'right';
  const ed = endDir || 'left';
  const G = 20; // stub distance — wire goes straight this far before first turn

  const sx = startPos.x, sy = startPos.y;
  const ex = endPos.x, ey = endPos.y;
  const dx = ex - sx, dy = ey - sy;

  // ── right → left (most common: forward path) ──
  if (sd === 'right' && ed === 'left') {
    if (Math.abs(dy) < 1 && dx > 0) return [[sx,sy],[ex,ey]];
    if (dx > 0) {
      const mx = (sx + ex) / 2;
      return [[sx,sy],[mx,sy],[mx,ey],[ex,ey]];
    }
    // Backward with large vertical offset: route via midpoint Y (avoids blocks at both rows)
    if (Math.abs(dy) > 40) {
      const midY = (sy + ey) / 2;
      return [[sx,sy],[sx+G,sy],[sx+G,midY],[ex-G,midY],[ex-G,ey],[ex,ey]];
    }
    // Backward same-row: detour above
    const detour = Math.min(sy, ey) - 80;
    return [[sx,sy],[sx+G,sy],[sx+G,detour],[ex-G,detour],[ex-G,ey],[ex,ey]];
  }

  // ── right → down ──
  if (sd === 'right' && ed === 'down') {
    if (sy < ey - G && ex > sx) return [[sx,sy],[ex,sy],[ex,ey]];
    if (sy < ey - G) return [[sx,sy],[sx+G,sy],[sx+G,ey-G],[ex,ey-G],[ex,ey]];
    const approachY = ey + G;
    return [[sx,sy],[sx+G,sy],[sx+G,approachY],[ex,approachY],[ex,ey]];
  }

  // ── right → up ──
  if (sd === 'right' && ed === 'up') {
    if (sy > ey + G && ex > sx) return [[sx,sy],[ex,sy],[ex,ey]];
    if (sy > ey + G && ex <= sx) return [[sx,sy],[sx+G,sy],[sx+G,ey+G],[ex,ey+G],[ex,ey]];
    const topY = Math.min(sy, ey) - 60;
    return [[sx,sy],[sx+G,sy],[sx+G,topY],[ex,topY],[ex,ey]];
  }

  // ── right → right ──
  if (sd === 'right' && ed === 'right') {
    if (dx < 0 && Math.abs(dy) > 40) return [[sx,sy],[sx+G,sy],[sx+G,ey],[ex+G,ey],[ex,ey]];
    if (dx < 0) {
      const detourY = Math.min(sy, ey) - 60;
      return [[sx,sy],[sx+G,sy],[sx+G,detourY],[ex+G,detourY],[ex+G,ey],[ex,ey]];
    }
    const rx = Math.max(sx + G, ex + G);
    return [[sx,sy],[rx,sy],[rx,ey],[ex,ey]];
  }

  // ── down → left ──
  if (sd === 'down' && ed === 'left') {
    if (sx >= ex && sy < ey) return [[sx,sy],[sx,ey],[ex,ey]];
    if (sx < ex && sy < ey) return [[sx,sy],[sx,ey],[ex,ey]];
    const botY = Math.max(sy + G, ey + G);
    return [[sx,sy],[sx,botY],[ex-G,botY],[ex-G,ey],[ex,ey]];
  }

  // ── down → right ──
  if (sd === 'down' && ed === 'right') {
    if (sx <= ex && sy < ey) return [[sx,sy],[sx,ey],[ex,ey]];
    if (sx > ex && sy < ey) return [[sx,sy],[sx,ey],[ex,ey]];
    const botY = Math.max(sy + G, ey + G);
    return [[sx,sy],[sx,botY],[ex+G,botY],[ex+G,ey],[ex,ey]];
  }

  // ── down → down ──
  if (sd === 'down' && ed === 'down') {
    if (Math.abs(dx) < 1) return [[sx,sy],[ex,ey]];
    const by = Math.max(sy, ey) + 40;
    return [[sx,sy],[sx,by],[ex,by],[ex,ey]];
  }

  // ── left → right (backward: feedback path) ──
  if (sd === 'left' && ed === 'right') {
    if (Math.abs(dy) < 1 && dx < 0) return [[sx,sy],[ex,ey]];
    if (dx < 0) {
      const mx = (sx + ex) / 2;
      return [[sx,sy],[mx,sy],[mx,ey],[ex,ey]];
    }
    // Forward with large vertical offset: route via midpoint Y
    if (Math.abs(dy) > 40) {
      const midY = (sy + ey) / 2;
      return [[sx,sy],[sx-G,sy],[sx-G,midY],[ex+G,midY],[ex+G,ey],[ex,ey]];
    }
    const detour = Math.min(sy, ey) - 80;
    return [[sx,sy],[sx-G,sy],[sx-G,detour],[ex+G,detour],[ex+G,ey],[ex,ey]];
  }

  // ── left → left ──
  if (sd === 'left' && ed === 'left') {
    if (Math.abs(dy) < 1 && dx < 0) return [[sx,sy],[ex,ey]];
    const lx = Math.min(sx - G, ex - G);
    return [[sx,sy],[lx,sy],[lx,ey],[ex,ey]];
  }

  // ── left → down ──
  if (sd === 'left' && ed === 'down') {
    if (sy < ey && sx > ex) return [[sx,sy],[ex,sy],[ex,ey]];
    if (sy < ey) return [[sx,sy],[sx-G,sy],[sx-G,ey-G],[ex,ey-G],[ex,ey]];
    const approachY = ey + G;
    return [[sx,sy],[sx-G,sy],[sx-G,approachY],[ex,approachY],[ex,ey]];
  }

  // ── left → up ──
  if (sd === 'left' && ed === 'up') {
    if (sy > ey && sx > ex) return [[sx,sy],[ex,sy],[ex,ey]];
    const topY = Math.min(sy, ey) - 40;
    return [[sx,sy],[sx-G,sy],[sx-G,topY],[ex,topY],[ex,ey]];
  }

  // ── up → left ──
  if (sd === 'up' && ed === 'left') {
    if (sy > ey) return [[sx,sy],[sx,ey],[ex,ey]];
    const topY = Math.min(sy - G, ey);
    return [[sx,sy],[sx,topY],[ex-G,topY],[ex-G,ey],[ex,ey]];
  }

  // ── up → right ──
  if (sd === 'up' && ed === 'right') {
    if (sy > ey) return [[sx,sy],[sx,ey],[ex,ey]];
    const topY = Math.min(sy - G, ey);
    return [[sx,sy],[sx,topY],[ex+G,topY],[ex+G,ey],[ex,ey]];
  }

  // ── up → down ──
  if (sd === 'up' && ed === 'down') {
    if (Math.abs(dx) < 1) return [[sx,sy],[ex,ey]];
    const topY = Math.min(sy, ey) - 40;
    return [[sx,sy],[sx,topY],[ex,topY],[ex,ey]];
  }

  // ── up → up ──
  if (sd === 'up' && ed === 'up') {
    if (Math.abs(dx) < 1) return [[sx,sy],[ex,ey]];
    const topY = Math.min(sy, ey) - 40;
    return [[sx,sy],[sx,topY],[ex,topY],[ex,ey]];
  }

  // ── Fallback ──
  if (Math.abs(dy) < 1) return [[sx,sy],[ex,ey]];
  const mx = (sx + ex) / 2;
  return [[sx,sy],[mx,sy],[mx,ey],[ex,ey]];
}

function getPortPosition(block, portType, portIndex) {
  const { x, y } = block.position;
  const type = block.type;

  // Returns { x, y, dir } where dir is the direction the wire exits/enters
  // Input/Output blocks keep fixed roles
  if (type === 'input') {
    return { x: x + BLOCK_SIZES.input.width / 2 + 13, y, dir: 'right' };
  }
  if (type === 'output') {
    return { x: x - (BLOCK_SIZES.output.width / 2 + 13), y, dir: 'left' };
  }

  // Gain: port 0 = left, port 1 = right (bidirectional)
  if (type === 'gain') {
    if (portIndex === 0) return { x: x - 58, y, dir: 'left' };
    return { x: x + 58, y, dir: 'right' };
  }

  // Delay / Integrator: port 0 = left, port 1 = right (bidirectional)
  if (type === 'delay' || type === 'integrator') {
    if (portIndex === 0) return { x: x - 50, y, dir: 'left' };
    return { x: x + 50, y, dir: 'right' };
  }

  // Adder: port 0 = left, port 1 = bottom, port 2 = right (all bidirectional)
  if (type === 'adder') {
    const r = BLOCK_SIZES.adder.radius;
    if (portIndex === 0) return { x: x - (r + 13), y, dir: 'left' };
    if (portIndex === 1) return { x, y: y + r + 13, dir: 'down' };
    return { x: x + r + 13, y, dir: 'right' };
  }

  // Junction: port 0 = input (left), port 1 = right, port 2 = up, port 3 = down
  if (type === 'junction') {
    const r = BLOCK_SIZES.junction.radius;
    if (portIndex === 0) return { x: x - (r + 8), y, dir: 'left' };
    if (portIndex === 1) return { x: x + r + 8, y, dir: 'right' };
    if (portIndex === 2) return { x, y: y - (r + 8), dir: 'up' };
    if (portIndex === 3) return { x, y: y + r + 8, dir: 'down' };
    return { x: x + r + 8, y: y + (portIndex - 3) * 16, dir: 'right' };
  }

  return { x, y, dir: 'right' };
}

// ============================================================================
// WireInProgress Component
// ============================================================================

function WireInProgress({ startPos, mousePos }) {
  if (!startPos || !mousePos) return null;
  const points = computeWirePoints(startPos, mousePos, startPos.dir || 'right', 'left');
  const d = pointsToPath(points);
  return <path d={d} className="bd-wire-in-progress" />;
}

// ============================================================================
// Connection Flash Feedback
// ============================================================================

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
  const panStart = useRef({ x: 0, y: 0, ox: 0, oy: 0 });

  const svgRef = useRef(null);
  const dragOffset = useRef({ x: 0, y: 0 });
  const presetRef = useRef(null);
  const draggingRef = useRef(null);
  const blocksRef = useRef(blocks);

  // Keep refs in sync with state for global event handlers
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
      if (metadata.tf_input) setTfInput(metadata.tf_input);
    }
  }, [metadata]);

  // Close preset dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (presetRef.current && !presetRef.current.contains(e.target)) {
        setPresetOpen(false);
      }
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
  // SVG coordinate conversion (handles viewBox scaling)
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
  // Backend API calls
  // ========================================================================

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
          // Propagate metadata to parent so TF panel updates
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
  }, [simId]);

  // Global mouseup listener — prevents block sticking to cursor when mouse leaves SVG
  useEffect(() => {
    const handleGlobalMouseUp = () => {
      if (draggingRef.current) {
        const block = blocksRef.current[draggingRef.current];
        if (block) {
          callAction('move_block', { block_id: draggingRef.current, position: block.position });
        }
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
    // Spiral-from-center placement — spreads blocks across the canvas
    const existingPositions = Object.values(blocks).map(b => b.position);
    const cx = CANVAS_WIDTH / 2, cy = CANVAS_HEIGHT / 2;
    const hClearance = 130, vClearance = 80;
    const step = 140;

    const noOverlap = (px, py) =>
      !existingPositions.some(p => Math.abs(p.x - px) < hClearance && Math.abs(p.y - py) < vClearance);

    // Try center first (snapped)
    const scx = snapToGrid(cx), scy = snapToGrid(cy);
    if (noOverlap(scx, scy)) {
      callAction('add_block', { block_type: blockType, position: { x: scx, y: scy } });
      return;
    }

    // Spiral outward in concentric rings
    for (let ring = 1; ring <= 8; ring++) {
      const r = ring * step;
      const points = Math.max(8, ring * 6);
      for (let i = 0; i < points; i++) {
        const angle = (2 * Math.PI * i) / points;
        const px = snapToGrid(cx + r * Math.cos(angle));
        const py = snapToGrid(cy + r * Math.sin(angle));
        // Keep within canvas bounds
        if (px < 80 || px > CANVAS_WIDTH - 80 || py < 60 || py > CANVAS_HEIGHT - 60) continue;
        if (noOverlap(px, py)) {
          callAction('add_block', { block_type: blockType, position: { x: px, y: py } });
          return;
        }
      }
    }

    // Fallback: offset from center
    callAction('add_block', { block_type: blockType, position: { x: cx + 20, y: cy + 20 } });
  }, [blocks, callAction]);

  const handleBlockMouseDown = useCallback((e, blockId) => {
    if (e.button !== 0) return;
    e.stopPropagation();
    const { x: svgX, y: svgY } = getSvgCoords(e.clientX, e.clientY);
    const block = blocks[blockId];
    if (!block) return;

    dragOffset.current = {
      x: svgX - block.position.x,
      y: svgY - block.position.y,
    };
    setDragging(blockId);
    setSelectedBlock(blockId);
    setSelectedWire(null);
    setGainEditBlock(null);
  }, [blocks, getSvgCoords]);

  const handleSvgMouseMove = useCallback((e) => {
    const { x: svgX, y: svgY } = getSvgCoords(e.clientX, e.clientY);

    if (dragging) {
      const rawX = Math.max(60, Math.min(CANVAS_WIDTH - 60, svgX - dragOffset.current.x));
      const rawY = Math.max(40, Math.min(CANVAS_HEIGHT - 40, svgY - dragOffset.current.y));
      const newX = snapToGrid(rawX);
      const newY = snapToGrid(rawY);
      setBlocks(prev => ({
        ...prev,
        [dragging]: {
          ...prev[dragging],
          position: { x: newX, y: newY },
        },
      }));
    }

    if (wireStart) {
      setMousePos({ x: svgX, y: svgY });
    }
  }, [dragging, wireStart, getSvgCoords]);

  const handleSvgMouseUp = useCallback(() => {
    if (wireStart) {
      // Wire not connected to a port — show failure flash
      setConnectionFlash({ position: mousePos, success: false });
    }
    // Actual cleanup (setDragging(null), setWireStart(null)) handled by global mouseup listener
  }, [wireStart, mousePos]);

  const handleCanvasClick = useCallback((e) => {
    if (e.target === svgRef.current || e.target.classList.contains('bd-grid-bg')) {
      setSelectedBlock(null);
      setSelectedWire(null);
      setGainEditBlock(null);
    }
  }, []);

  // Port interactions for wiring — generic bidirectional ports
  const handlePortMouseDown = useCallback((e, blockId, portType, portIndex, portX, portY, portDir) => {
    e.preventDefault();
    e.stopPropagation();
    // Any port can be a wire source (output)
    setWireStart({ blockId, portIndex, x: portX, y: portY, dir: portDir || 'right' });
  }, []);

  const handlePortMouseUp = useCallback((e, blockId, portType, portIndex) => {
    e.preventDefault();
    e.stopPropagation();
    if (wireStart && wireStart.blockId !== blockId) {
      const targetBlock = blocks[blockId];
      const targetPos = targetBlock ? getPortPosition(targetBlock, 'input', portIndex) : null;

      // --- Frontend early-reject validation ---
      // Same block (shouldn't happen since we check above, but guard)
      const sourceBlock = blocks[wireStart.blockId];
      if (wireStart.blockId === blockId) {
        if (targetPos) setConnectionFlash({ position: targetPos, success: false });
        setWireStart(null);
        return;
      }
      // Already connected (exact duplicate or reverse)
      const isDuplicate = connections.some(c =>
        (c.from_block === wireStart.blockId && c.from_port === wireStart.portIndex &&
         c.to_block === blockId && c.to_port === portIndex)
      );
      const isReverse = connections.some(c =>
        c.from_block === blockId && c.from_port === portIndex &&
        c.to_block === wireStart.blockId && c.to_port === wireStart.portIndex
      );
      if (isDuplicate || isReverse) {
        if (targetPos) setConnectionFlash({ position: targetPos, success: false });
        setWireStart(null);
        return;
      }
      // Role enforcement
      if (sourceBlock?.type === 'output' || targetBlock?.type === 'input') {
        if (targetPos) setConnectionFlash({ position: targetPos, success: false });
        setWireStart(null);
        return;
      }

      callAction('add_connection', {
        from_block: wireStart.blockId,
        from_port: wireStart.portIndex,
        to_block: blockId,
        to_port: portIndex,
      });

      // Show success flash
      if (targetPos) {
        setConnectionFlash({ position: targetPos, success: true });
      }
      setNewWireIndex(connections.length);
    }
    setWireStart(null);
  }, [wireStart, callAction, blocks, connections]);

  // Undo
  const handleUndo = useCallback(() => {
    callAction('undo', {});
    setSelectedBlock(null);
    setSelectedWire(null);
  }, [callAction]);

  // Delete selected block or wire + Ctrl/Cmd+Z undo
  const handleKeyDown = useCallback((e) => {
    // Undo: Ctrl+Z / Cmd+Z
    if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
      e.preventDefault();
      handleUndo();
      return;
    }
    if ((e.key === 'Delete' || e.key === 'Backspace') && !gainEditBlock) {
      e.preventDefault();
      if (selectedWire !== null) {
        callAction('remove_connection', { conn_index: selectedWire });
        setSelectedWire(null);
      } else if (selectedBlock) {
        callAction('remove_block', { block_id: selectedBlock });
        setSelectedBlock(null);
      }
    }
  }, [selectedBlock, selectedWire, gainEditBlock, callAction, handleUndo]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Toggle adder sign
  const handleToggleSign = useCallback((blockId, portIndex) => {
    callAction('toggle_adder_sign', { block_id: blockId, port_index: portIndex });
  }, [callAction]);

  // Gain value editing
  const handleGainDoubleClick = useCallback((blockId) => {
    const block = blocks[blockId];
    if (block?.type === 'gain') {
      setGainEditBlock(blockId);
      setGainEditValue(String(block.value ?? 1));
      setSelectedBlock(blockId);
    }
  }, [blocks]);

  const handleGainEditSubmit = useCallback(() => {
    if (gainEditBlock) {
      const val = parseFloat(gainEditValue);
      if (!isNaN(val)) {
        callAction('update_block_value', { block_id: gainEditBlock, value: val });
      }
      setGainEditBlock(null);
    }
  }, [gainEditBlock, gainEditValue, callAction]);

  // Mode/system type changes
  const handleModeChange = useCallback((newMode) => {
    setMode(newMode);
    callAction('set_mode', { mode: newMode });
    if (onParamChange) onParamChange('mode', newMode);
  }, [callAction, onParamChange]);

  const handleSystemTypeChange = useCallback((newType) => {
    setSystemType(newType);
    // Clear canvas when switching system type (DT↔CT) since block types differ
    callAction('set_system_type', { system_type: newType });
    setBlocks({});
    setConnections([]);
    setSelectedBlock(null);
    setSelectedWire(null);
    setTfResult(null);
    setError(null);
    setZoom(1.0);
    setPanOffset({ x: 0, y: 0 });
    if (onParamChange) onParamChange('system_type', newType);
  }, [callAction, onParamChange]);

  // Clear canvas
  const handleClear = useCallback(() => {
    callAction('clear', {});
    setZoom(1.0);
    setPanOffset({ x: 0, y: 0 });
    setSelectedBlock(null);
    setSelectedWire(null);
    setTfResult(null);
    setError(null);
  }, [callAction]);

  // Load preset
  const handleLoadPreset = useCallback((presetName) => {
    callAction('load_preset', { preset: presetName });
    setZoom(1.0);
    setPanOffset({ x: 0, y: 0 });
    setPresetOpen(false);
    setSelectedBlock(null);
    setSelectedWire(null);
    setError(null);
  }, [callAction]);

  // Parse TF
  const handleParseTf = useCallback(() => {
    if (tfInput.trim()) {
      callAction('parse_tf', { tf_string: tfInput });
    }
  }, [tfInput, callAction]);

  // Remove a connection
  const handleRemoveConnection = useCallback((index) => {
    callAction('remove_connection', { conn_index: index });
  }, [callAction]);

  // Wire selection — single click selects, shows info in side panel
  const handleWireClick = useCallback((e, connIndex) => {
    e.stopPropagation();
    setSelectedWire(connIndex);
    setSelectedBlock(null);
    setGainEditBlock(null);
  }, []);

  // Wire branching — double-click to start a new connection from the same source
  const handleWireDoubleClick = useCallback((e, connIndex) => {
    e.stopPropagation();
    e.preventDefault();
    const { x: svgX, y: svgY } = getSvgCoords(e.clientX, e.clientY);
    // Split wire: insert junction node at click position
    callAction('split_wire', {
      conn_index: connIndex,
      position: { x: Math.round(svgX), y: Math.round(svgY) },
    });
    setSelectedWire(null);
  }, [getSvgCoords, callAction]);

  // Zoom handlers
  const handleZoomIn = useCallback(() => {
    setZoom(z => Math.min(MAX_ZOOM, z + ZOOM_STEP));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoom(z => Math.max(MIN_ZOOM, z - ZOOM_STEP));
  }, []);

  const handleZoomReset = useCallback(() => {
    setZoom(1.0);
    setPanOffset({ x: 0, y: 0 });
  }, []);

  // Mouse wheel zoom — simple center-based zoom (reliable, no drift)
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

  // Middle-mouse or space+drag pan
  const handlePanStart = useCallback((e) => {
    // Middle mouse button (button=1) or Alt+left-click to pan
    if (e.button === 1 || (e.altKey && e.button === 0)) {
      e.preventDefault();
      setIsPanning(true);
      panStart.current = { x: e.clientX, y: e.clientY, ox: panOffset.x, oy: panOffset.y };
    }
  }, [panOffset]);

  const handlePanMove = useCallback((e) => {
    if (isPanning) {
      const dx = (e.clientX - panStart.current.x) / zoom;
      const dy = (e.clientY - panStart.current.y) / zoom;
      // Tight pan limits — never lose the diagram
      const maxPanX = 200;
      const maxPanY = 150;
      const newX = Math.max(-maxPanX, Math.min(maxPanX, panStart.current.ox + dx));
      const newY = Math.max(-maxPanY, Math.min(maxPanY, panStart.current.oy + dy));
      setPanOffset({ x: newX, y: newY });
    }
  }, [isPanning, zoom]);

  const handlePanEnd = useCallback(() => {
    setIsPanning(false);
  }, []);

  // Computed viewBox with zoom and pan
  const viewBox = useMemo(() => {
    const vw = CANVAS_WIDTH / zoom;
    const vh = CANVAS_HEIGHT / zoom;
    const vx = (CANVAS_WIDTH - vw) / 2 - panOffset.x;
    const vy = (CANVAS_HEIGHT - vh) / 2 - panOffset.y;
    return `${vx} ${vy} ${vw} ${vh}`;
  }, [zoom, panOffset]);

  // Compute branch points — output ports with multiple connections
  // Offset dot 16px along wire direction (away from port, not sitting on it)
  const branchPoints = useMemo(() => {
    const portCounts = {};
    connections.forEach(conn => {
      const key = `${conn.from_block}:${conn.from_port}`;
      portCounts[key] = (portCounts[key] || 0) + 1;
    });
    const points = [];
    Object.entries(portCounts).forEach(([key, count]) => {
      if (count > 1) {
        const [blockId, portIdx] = key.split(':');
        const block = blocks[blockId];
        if (block) {
          const pos = getPortPosition(block, 'output', parseInt(portIdx));
          // Offset 16px along the port's outgoing direction
          const dir = pos.dir || 'right';
          let ox = 0, oy = 0;
          if (dir === 'right') ox = 16;
          else if (dir === 'left') ox = -16;
          else if (dir === 'down') oy = 16;
          else if (dir === 'up') oy = -16;
          points.push({ x: pos.x + ox, y: pos.y + oy });
        }
      }
    });
    return points;
  }, [connections, blocks]);

  // ========================================================================
  // Compute signal flow direction per block (for visual flipping)
  // For gain/delay/integrator: determine if signal flows left→right or right→left
  // ========================================================================

  const blockFlowDir = useMemo(() => {
    // Returns map: blockId → 'ltr' | 'rtl' | 'ltr' (default)
    // 'ltr' = signal enters from left (port 0), exits right (port 1)
    // 'rtl' = signal enters from right (port 1), exits left (port 0)
    const dirs = {};
    Object.keys(blocks).forEach(blockId => {
      const block = blocks[blockId];
      if (block.type === 'input' || block.type === 'output' || block.type === 'adder' || block.type === 'junction') {
        dirs[blockId] = 'ltr'; // fixed direction
        return;
      }
      // For gain/delay/integrator: check which ports are inputs vs outputs
      let inputPorts = new Set();
      let outputPorts = new Set();
      connections.forEach(conn => {
        if (conn.to_block === blockId) inputPorts.add(conn.to_port);
        if (conn.from_block === blockId) outputPorts.add(conn.from_port);
      });
      // If port 1 (right) is input and port 0 (left) is output → rtl
      if (inputPorts.has(1) && outputPorts.has(0)) {
        dirs[blockId] = 'rtl';
      } else {
        dirs[blockId] = 'ltr';
      }
    });
    return dirs;
  }, [blocks, connections]);

  // ========================================================================
  // Determine which blocks are available
  // ========================================================================

  const availableBlocks = useMemo(() => {
    const base = ['input', 'output', 'gain', 'adder'];
    if (systemType === 'dt') base.push('delay');
    else base.push('integrator');
    base.push('junction');
    return base;
  }, [systemType]);

  const blockLabels = {
    input: 'Input',
    output: 'Output',
    gain: 'Gain',
    adder: 'Adder',
    delay: 'Delay',
    integrator: 'Integrator',
    junction: 'Junction',
  };

  const blockIcons = {
    input: '\u2192',
    output: '\u2190',
    gain: '\u25B7',
    adder: '\u2295',
    delay: '\u25FB',
    integrator: '\u222B',
    junction: '\u25CF',
  };

  // ========================================================================
  // Gain edit position — use SVG coordinate transform
  // ========================================================================

  const gainEditPos = useMemo(() => {
    if (!gainEditBlock || !blocks[gainEditBlock] || !svgRef.current) return null;
    const block = blocks[gainEditBlock];
    const svg = svgRef.current;
    const svgRect = svg.getBoundingClientRect();
    const ctm = svg.getScreenCTM();
    if (!ctm) return null;
    // Transform SVG coords to screen coords
    const screenX = block.position.x * ctm.a + ctm.e - svgRect.left;
    const screenY = (block.position.y - 35) * ctm.d + ctm.f - svgRect.top;
    return { left: screenX, top: screenY };
  }, [gainEditBlock, blocks]);

  // ========================================================================
  // Get response plot from plots + compute connection count
  // ========================================================================

  // connectionCount exposed for potential external use
  const connectionCount = connections.length;

  // ========================================================================
  // Render
  // ========================================================================

  return (
    <div className="block-diagram-viewer">
      {/* Loading overlay */}
      {isLoading && (
        <div className="bd-loading-bar">
          <div className="bd-loading-bar-inner" />
        </div>
      )}

      {/* Toolbar */}
      <div className="bd-toolbar">
        <div className="bd-toolbar-section bd-toolbar-palette">
          <span className="bd-toolbar-label">Blocks</span>
          {availableBlocks.map(type => (
            <button
              key={type}
              className="bd-palette-btn"
              onClick={() => handleAddBlock(type)}
              title={`Add ${type} block`}
            >
              <span className="bd-palette-icon">{blockIcons[type]}</span>
              <span className="bd-palette-text">{blockLabels[type]}</span>
            </button>
          ))}
        </div>

        <div className="bd-toolbar-divider" />

        <div className="bd-toolbar-section">
          <span className="bd-toolbar-label">Mode</span>
          <div className="bd-toggle-group">
            <button
              className={`bd-toggle-btn ${mode === 'build' ? 'active' : ''}`}
              onClick={() => handleModeChange('build')}
            >
              Build
            </button>
            <button
              className={`bd-toggle-btn ${mode === 'parse' ? 'active' : ''}`}
              onClick={() => handleModeChange('parse')}
            >
              Parse TF
            </button>
          </div>
        </div>

        <div className="bd-toolbar-section">
          <span className="bd-toolbar-label">Type</span>
          <div className="bd-toggle-group">
            <button
              className={`bd-toggle-btn ${systemType === 'dt' ? 'active' : ''}`}
              onClick={() => handleSystemTypeChange('dt')}
            >
              DT
            </button>
            <button
              className={`bd-toggle-btn ${systemType === 'ct' ? 'active' : ''}`}
              onClick={() => handleSystemTypeChange('ct')}
            >
              CT
            </button>
          </div>
        </div>

        <div className="bd-toolbar-divider" />

        <div className="bd-toolbar-section bd-toolbar-actions">
          <button className="bd-action-btn bd-undo-btn" onClick={handleUndo} title="Undo (Ctrl+Z)">
            <span className="bd-btn-icon">&#x21A9;</span> Undo
          </button>
          <button className="bd-action-btn bd-clear-btn" onClick={handleClear}>
            <span className="bd-btn-icon">&times;</span> Clear
          </button>
          <div className="bd-preset-dropdown" ref={presetRef}>
            <button
              className={`bd-action-btn bd-preset-toggle ${presetOpen ? 'open' : ''}`}
              onClick={() => setPresetOpen(!presetOpen)}
            >
              Presets {presetOpen ? '\u25B4' : '\u25BE'}
            </button>
            {presetOpen && (
              <div className="bd-preset-menu">
                {Object.keys(presets).length === 0 && (
                  <div className="bd-preset-empty">No presets available</div>
                )}
                {Object.entries(presets).map(([key, preset]) => (
                  <button
                    key={key}
                    className="bd-preset-item"
                    onClick={() => handleLoadPreset(key)}
                  >
                    <span className="bd-preset-name">{preset.name}</span>
                    <span className="bd-preset-eq">{preset.equation}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Parse mode input */}
      {mode === 'parse' && (
        <div className="bd-parse-bar">
          <span className="bd-parse-label">Transfer Function:</span>
          <input
            type="text"
            className="bd-tf-input"
            value={tfInput}
            onChange={(e) => setTfInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleParseTf(); }}
            placeholder={systemType === 'dt' ? 'e.g. (1 - R) / (1 - 0.5R)' : 'e.g. 1 / (s + 2)'}
          />
          <button className="bd-parse-btn" onClick={handleParseTf} disabled={isLoading}>
            {isLoading ? 'Generating...' : 'Generate Diagram'}
          </button>
        </div>
      )}

      <div className="bd-main-area">
        {/* SVG Canvas */}
        <div className="bd-canvas-container">
          <svg
            ref={svgRef}
            width="100%"
            height="100%"
            viewBox={viewBox}
            preserveAspectRatio="xMidYMid meet"
            className={`bd-canvas ${isPanning ? 'bd-panning' : ''}`}
            onMouseMove={(e) => { handleSvgMouseMove(e); handlePanMove(e); }}
            onMouseUp={(e) => { handleSvgMouseUp(e); handlePanEnd(); }}
            onMouseDown={handlePanStart}
            onClick={handleCanvasClick}
          >
            {/* Defs */}
            <defs>
              <marker
                id="arrowhead"
                markerWidth="10"
                markerHeight="8"
                refX="12"
                refY="4"
                orient="auto"
              >
                <polygon points="0 0, 10 4, 0 8" fill="var(--accent-color, #00d9ff)" />
              </marker>
              <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">
                <circle cx="12" cy="12" r="1" fill="rgba(148, 163, 184, 0.22)" />
              </pattern>
            </defs>

            {/* Grid background */}
            <rect
              width={CANVAS_WIDTH}
              height={CANVAS_HEIGHT}
              fill="url(#grid)"
              className="bd-grid-bg"
            />

            {/* Wires */}
            {connections.map((conn, i) => (
              <Wire
                key={`${conn.from_block}-${conn.to_block}-${conn.to_port}`}
                connection={conn}
                blocks={blocks}
                isNew={i === newWireIndex}
                isSelected={i === selectedWire}
                onWireClick={(e) => handleWireClick(e, i)}
                onWireDoubleClick={(e) => handleWireDoubleClick(e, i)}
              />
            ))}

            {/* Branch point dots */}
            {branchPoints.map((pt, i) => (
              <circle key={`branch-${i}`} cx={pt.x} cy={pt.y} r={5} className="bd-branch-dot" />
            ))}

            {/* Wire in progress */}
            {wireStart && (
              <WireInProgress startPos={wireStart} mousePos={mousePos} />
            )}

            {/* Connection flash feedback */}
            {connectionFlash && (
              <ConnectionFlash position={connectionFlash.position} success={connectionFlash.success} />
            )}

            {/* Blocks */}
            {Object.values(blocks).map(block => {
              const commonProps = {
                block,
                isSelected: selectedBlock === block.id,
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
                  return (
                    <GainBlock
                      key={block.id}
                      {...commonProps}
                      flowDir={flowDir}
                      onValueChange={handleGainEditSubmit}
                      onGainDoubleClick={handleGainDoubleClick}
                    />
                  );
                case 'adder':
                  return <AdderBlock key={block.id} {...commonProps} onToggleSign={handleToggleSign} />;
                case 'delay':
                  return <DelayBlock key={block.id} {...commonProps} flowDir={flowDir} />;
                case 'integrator':
                  return <IntegratorBlock key={block.id} {...commonProps} flowDir={flowDir} />;
                case 'junction':
                  return <JunctionBlock key={block.id} {...commonProps} connections={connections} />;
                default:
                  return null;
              }
            })}
          </svg>

          {/* Gain edit overlay — positioned using screen-space transform */}
          {gainEditBlock && blocks[gainEditBlock] && gainEditPos && (
            <div
              className="bd-gain-edit-overlay"
              style={{
                left: `${gainEditPos.left}px`,
                top: `${gainEditPos.top}px`,
              }}
            >
              <label className="bd-gain-edit-label">Gain value</label>
              <input
                type="number"
                className="bd-gain-edit-input"
                value={gainEditValue}
                onChange={(e) => setGainEditValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleGainEditSubmit();
                  if (e.key === 'Escape') setGainEditBlock(null);
                }}
                onBlur={handleGainEditSubmit}
                autoFocus
                step="0.1"
              />
            </div>
          )}

          {/* Instructions overlay */}
          {Object.keys(blocks).length === 0 && mode === 'build' && (
            <div className="bd-instructions-overlay">
              <div className="bd-instructions-icon">&#9881;</div>
              <p className="bd-instructions-title">Block Diagram Builder</p>
              <p>Click a block type above to add it, or load a preset.</p>
              <p>Drag from ports to connect blocks. Double-click gain blocks to edit values.</p>
              <p>Click a wire to select it. Press <kbd>Delete</kbd> to remove. Double-click a wire to branch.</p>
              <p className="bd-instructions-hint"><kbd>Ctrl+Z</kbd> to undo. Click &plusmn; on adders to toggle sign.</p>
            </div>
          )}
          {/* Zoom controls overlay */}
          <div className="bd-zoom-controls">
            <button className="bd-zoom-btn" onClick={handleZoomIn} title="Zoom In">+</button>
            <span className="bd-zoom-level">{Math.round(zoom * 100)}%</span>
            <button className="bd-zoom-btn" onClick={handleZoomOut} title="Zoom Out">&minus;</button>
            <button className="bd-zoom-btn bd-zoom-reset" onClick={handleZoomReset} title="Reset View">&#8634;</button>
          </div>

          {/* Error display on canvas */}
          {error && (
            <div className="bd-canvas-error">{error}</div>
          )}
        </div>
      </div>
    </div>
  );
}

export default BlockDiagramViewer;
