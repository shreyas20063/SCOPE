/**
 * BlockDiagramViewer Component — Clean Rewrite
 *
 * Interactive SVG-based block diagram builder with Manhattan wire routing.
 * Two modes:
 *   1. Build Mode — drag/drop blocks, draw wires → compute transfer function
 *   2. Parse Mode — enter transfer function → generate block diagram
 *
 * Rendering Pipeline:
 *   1. analyzeSignalFlow() — determine LTR/RTL per block via incoming port number
 *   2. computeAdderPorts() — dynamic port placement based on connection angles
 *   3. getPortPosition() — port coords (invariant: port 0=LEFT, port 1=RIGHT)
 *   4. routeWire() — geometric-first Manhattan routing with A* fallback
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
const CANVAS_WIDTH = 1800;
const CANVAS_HEIGHT = 1100;
const MIN_ZOOM = 0.5;
const MAX_ZOOM = 3.0;
const ZOOM_STEP = 0.15;
const PORT_RADIUS = 10;
const COLLISION_PAD = 36; // 1.5 grid cells clearance around blocks

const BLOCK_SIZES = {
  input:      { width: 80, height: 60 },
  output:     { width: 80, height: 60 },
  gain:       { width: 80, height: 60 },
  adder:      { radius: 30 },
  delay:      { width: 80, height: 60 },
  integrator: { width: 80, height: 60 },
  junction:   { radius: 6 },
  custom_tf:  { width: 120, height: 65 },
};

// Max INCOMING wires per block type (synced with backend BLOCK_TYPES inputs).
// Outgoing (fan-out) is unlimited for all types — signal splitting is always valid.
const MAX_WIRES = {
  input:      { in: 0 },
  output:     { in: 1 },
  gain:       { in: 1 },
  adder:      { in: 2 },
  delay:      { in: 1 },
  integrator: { in: 1 },
  junction:   { in: 1 },
  custom_tf:  { in: 1 },
};

// Port distance from block center (all multiples of GRID_SIZE)
const PORT_DIST = 48;

function snapToGrid(val) {
  return Math.round(val / GRID_SIZE) * GRID_SIZE;
}

// ============================================================================
// Signal Flow Analysis — graph topology, not heuristics
// ============================================================================

/**
 * For each gain/delay/integrator, determine signal flow direction.
 * LTR: block on forward path (input→output) — triangle points RIGHT
 * RTL: block on feedback path (not on forward path) — triangle points LEFT
 *
 * Algorithm: port-based direction detection.
 * For gain/delay/integrator blocks, the incoming connection's to_port
 * determines the direction:
 *   - to_port 0 (left side) → LTR (signal enters from left, triangle points right)
 *   - to_port 1 (right side) → RTL (signal enters from right, triangle points left)
 * This matches the backend's port convention where port 0 = left, port 1 = right.
 */
function analyzeSignalFlow(blocks, connections) {
  const dirs = {};
  const blockIds = Object.keys(blocks);
  if (blockIds.length === 0) return dirs;

  // Assign directions
  for (const blockId of blockIds) {
    const block = blocks[blockId];
    if (!['gain', 'delay', 'integrator', 'custom_tf'].includes(block.type)) {
      dirs[blockId] = 'ltr';
      continue;
    }

    // Port-based direction: if signal arrives at port 1 (right side) → RTL,
    // if signal arrives at port 0 (left side) → LTR.
    // This matches the backend's port convention for gain/delay/integrator blocks.
    let inputPort = null;
    for (const conn of connections) {
      if (conn.to_block === blockId) {
        inputPort = conn.to_port;
        break;
      }
    }
    dirs[blockId] = (inputPort === 1) ? 'rtl' : 'ltr';
  }

  return dirs;
}

// ============================================================================
// Block bounding box for obstacle detection
// ============================================================================

function getBlockBounds(block, padding = COLLISION_PAD) {
  // Wire zone blocks have pre-computed bounds (padding already baked in)
  if (block._bounds) return block._bounds;

  const { x, y } = block.position;
  const type = block.type;

  if (type === 'adder') {
    const r = BLOCK_SIZES.adder.radius;
    return { left: x - r - padding, right: x + r + padding,
             top: y - r - padding, bottom: y + r + padding };
  }
  if (type === 'junction') {
    const r = BLOCK_SIZES.junction.radius + 4;
    return { left: x - r - padding, right: x + r + padding,
             top: y - r - padding, bottom: y + r + padding };
  }
  const size = BLOCK_SIZES[type] || { width: 80, height: 60 };
  const hw = size.width / 2, hh = size.height / 2;
  return { left: x - hw - padding, right: x + hw + padding,
           top: y - hh - padding, bottom: y + hh + padding };
}

// ============================================================================
// Port position computation
// ============================================================================

/**
 * Get the physical position and wire direction for a port.
 * INVARIANT: port 0 = LEFT side, port 1 = RIGHT side (gain/delay/integrator).
 * The backend reverses input/output semantics for RTL blocks, but
 * physical positions NEVER change. This is the critical rule.
 */
function getPortPosition(block, portType, portIndex, _flowDirMap, adderPortMap) {
  const { x, y } = block.position;
  const type = block.type;

  if (type === 'input') {
    return { x: x + PORT_DIST, y, dir: 'right' };
  }
  if (type === 'output') {
    return { x: x - PORT_DIST, y, dir: 'left' };
  }
  // Gain / Delay / Integrator: port 0 = LEFT, port 1 = RIGHT (always)
  if (type === 'gain' || type === 'delay' || type === 'integrator' || type === 'custom_tf') {
    if (portIndex === 0) return { x: x - PORT_DIST, y, dir: 'left' };
    return { x: x + PORT_DIST, y, dir: 'right' };
  }

  // Adder: use dynamic port map if available
  if (type === 'adder') {
    const dynPorts = adderPortMap && adderPortMap[block.id];
    if (dynPorts && dynPorts[portIndex]) {
      const dp = dynPorts[portIndex];
      return { x: x + dp.dx, y: y + dp.dy, dir: dp.dir };
    }
    // Fallback: port 0=left, port 1=bottom, port 2=right
    if (portIndex === 0) return { x: x - PORT_DIST, y, dir: 'left' };
    if (portIndex === 1) return { x, y: y + PORT_DIST, dir: 'down' };
    return { x: x + PORT_DIST, y, dir: 'right' };
  }

  // Junction: multi-port branch point
  if (type === 'junction') {
    const d = GRID_SIZE;
    if (portIndex === 0) return { x: x - d, y, dir: 'left' };
    if (portIndex === 1) return { x: x + d, y, dir: 'right' };
    if (portIndex === 2) return { x, y: y - d, dir: 'up' };
    if (portIndex === 3) return { x, y: y + d, dir: 'down' };
    return { x: x + d, y: y + (portIndex - 3) * GRID_SIZE, dir: 'right' };
  }

  return { x, y, dir: 'right' };
}

// ============================================================================
// Dynamic adder port computation
// ============================================================================

/**
 * For each adder, compute optimal port positions based on connected block angles.
 * Output port (port 2) gets priority placement, then input ports.
 */
function computeAdderPorts(blocks, connections) {
  const map = {};

  for (const block of Object.values(blocks)) {
    if (block.type !== 'adder') continue;

    // Gather port→connected block info
    const portInfo = {};
    for (const conn of connections) {
      if (conn.to_block === block.id) {
        const src = blocks[conn.from_block];
        if (src) {
          portInfo[conn.to_port] = {
            dx: src.position.x - block.position.x,
            dy: src.position.y - block.position.y,
            isOutput: false,
          };
        }
      }
      if (conn.from_block === block.id) {
        const tgt = blocks[conn.to_block];
        if (tgt) {
          const tdx = tgt.position.x - block.position.x;
          const tdy = tgt.position.y - block.position.y;
          if (portInfo[conn.from_port] && portInfo[conn.from_port].isOutput) {
            // Multiple targets: keep the most horizontal one (forward path priority)
            const curHoriz = Math.abs(portInfo[conn.from_port].dy) <= Math.abs(portInfo[conn.from_port].dx);
            const newHoriz = Math.abs(tdy) <= Math.abs(tdx);
            if (newHoriz && !curHoriz) {
              portInfo[conn.from_port].dx = tdx;
              portInfo[conn.from_port].dy = tdy;
            }
          } else {
            portInfo[conn.from_port] = { dx: tdx, dy: tdy, isOutput: true };
          }
        }
      }
    }

    if (Object.keys(portInfo).length === 0) continue;

    // Cardinal directions
    const cardinals = [
      { dir: 'left',  dx: -PORT_DIST, dy: 0 },
      { dir: 'right', dx: PORT_DIST,  dy: 0 },
      { dir: 'up',    dx: 0, dy: -PORT_DIST },
      { dir: 'down',  dx: 0, dy: PORT_DIST },
    ];

    // Sort: output port first (priority), then inputs
    const entries = Object.entries(portInfo).sort((a, b) => {
      if (a[1].isOutput && !b[1].isOutput) return -1;
      if (!a[1].isOutput && b[1].isOutput) return 1;
      return 0;
    });

    const usedDirs = new Set();
    const portPositions = {};

    for (const [portIdx, info] of entries) {
      const angle = Math.atan2(info.dy, info.dx);
      let bestCard = null;
      let bestScore = Infinity;

      for (const card of cardinals) {
        if (usedDirs.has(card.dir)) continue;
        const cardAngle = Math.atan2(card.dy, card.dx);
        let diff = Math.abs(angle - cardAngle);
        if (diff > Math.PI) diff = 2 * Math.PI - diff;
        if (diff < bestScore) {
          bestScore = diff;
          bestCard = card;
        }
      }

      if (bestCard) {
        usedDirs.add(bestCard.dir);
        portPositions[portIdx] = {
          dx: bestCard.dx,
          dy: bestCard.dy,
          dir: bestCard.dir,
        };
      }
    }

    if (Object.keys(portPositions).length > 0) {
      map[block.id] = portPositions;
    }
  }

  return map;
}

// ============================================================================
// Wire Routing — Geometric-first Manhattan routing with A* fallback
// ============================================================================

/**
 * Check if a Manhattan segment (horizontal or vertical) is clear of obstacles.
 */
function segmentClear(x1, y1, x2, y2, obsBlocks, padding = COLLISION_PAD) {
  for (const block of obsBlocks) {
    const b = getBlockBounds(block, padding);
    // Horizontal segment
    if (Math.abs(y1 - y2) < 1) {
      const yy = y1;
      const xMin = Math.min(x1, x2), xMax = Math.max(x1, x2);
      if (yy >= b.top && yy <= b.bottom && xMax >= b.left && xMin <= b.right) {
        return false;
      }
    }
    // Vertical segment
    else if (Math.abs(x1 - x2) < 1) {
      const xx = x1;
      const yMin = Math.min(y1, y2), yMax = Math.max(y1, y2);
      if (xx >= b.left && xx <= b.right && yMax >= b.top && yMin <= b.bottom) {
        return false;
      }
    }
  }
  return true;
}

/**
 * Check if an entire route (array of [x,y] points) is clear of obstacles.
 */
function routeClear(points, obsBlocks, padding = COLLISION_PAD) {
  for (let i = 0; i < points.length - 1; i++) {
    if (!segmentClear(points[i][0], points[i][1], points[i+1][0], points[i+1][1], obsBlocks, padding)) {
      return false;
    }
  }
  return true;
}

/**
 * Check that a route doesn't cut through excluded (source/target) block bodies.
 * Uses minimal padding (just the physical block, not full airspace) so ports
 * at PORT_DIST from center remain accessible while the body is blocked.
 */
function routeClearBody(route, bodyBlocks) {
  if (bodyBlocks.length === 0 || route.length < 2) return true;
  const BODY_PAD = 2; // Minimal padding: just the block body
  for (let i = 0; i < route.length - 1; i++) {
    if (!segmentClear(route[i][0], route[i][1], route[i+1][0], route[i+1][1], bodyBlocks, BODY_PAD)) {
      return false;
    }
  }
  return true;
}

/**
 * Compute total Manhattan length of a route.
 */
function routeLength(pts) {
  let len = 0;
  for (let i = 0; i < pts.length - 1; i++) {
    len += Math.abs(pts[i+1][0] - pts[i][0]) + Math.abs(pts[i+1][1] - pts[i][1]);
  }
  return len;
}

/**
 * Count the number of bends (direction changes) in a route.
 */
function routeBends(pts) {
  let bends = 0;
  for (let i = 1; i < pts.length - 1; i++) {
    const dx1 = pts[i][0] - pts[i-1][0], dy1 = pts[i][1] - pts[i-1][1];
    const dx2 = pts[i+1][0] - pts[i][0], dy2 = pts[i+1][1] - pts[i][1];
    if (Math.abs(dx1) > 0.5 && Math.abs(dy2) > 0.5) bends++;
    else if (Math.abs(dy1) > 0.5 && Math.abs(dx2) > 0.5) bends++;
  }
  return bends;
}

/**
 * Remove collinear intermediate points from a path.
 */
function simplifyPath(points) {
  if (points.length <= 2) return points;
  const result = [points[0]];
  for (let i = 1; i < points.length - 1; i++) {
    const [px, py] = result[result.length - 1]; // Use last KEPT point, not original neighbor
    const [cx, cy] = points[i];
    const [nx, ny] = points[i + 1];
    const sameH = Math.abs(py - cy) < 1 && Math.abs(cy - ny) < 1;
    const sameV = Math.abs(px - cx) < 1 && Math.abs(cx - nx) < 1;
    if (!sameH && !sameV) result.push(points[i]);
  }
  result.push(points[points.length - 1]);
  return result;
}

/**
 * Convert a list of [x,y] points to an SVG path string.
 */
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
// Blocked Airspace Architecture
// ============================================================================
// Each block defines an exclusion zone (padded bounding box) on the canvas.
// Wires CANNOT enter these zones — only designated ports on the boundary
// are valid entry/exit points. This prevents wires from cutting through blocks.

/**
 * Build blocked airspace zones for all non-excluded blocks.
 * Returns array of {left, right, top, bottom, blockId} exclusion rectangles.
 */
function buildBlockedAirspace(blocks, excludeIds = [], padding = COLLISION_PAD) {
  const zones = [];
  for (const block of Object.values(blocks)) {
    if (excludeIds.includes(block.id)) continue;
    zones.push({ ...getBlockBounds(block, padding), blockId: block.id });
  }
  return zones;
}

/**
 * Find Y-coordinate bypass lanes that clear all obstacles in the corridor
 * between two endpoints. Scans the horizontal corridor for obstacle airspaces
 * and returns Y-coordinates above and below where wires can safely route.
 */
function findBypassLanes(sx, sy, ex, ey, airspaces) {
  const xMin = Math.min(sx, ex), xMax = Math.max(sx, ex);
  const G = GRID_SIZE;

  // Find ALL obstacles whose X range overlaps the wire corridor (wider search)
  const corridorObs = airspaces.filter(z =>
    z.right >= xMin - G * 2 && z.left <= xMax + G * 2
  );

  if (corridorObs.length === 0) return [];

  // Collect all Y boundaries and find global extents
  const yBounds = [];
  for (const obs of corridorObs) {
    yBounds.push(obs.top);
    yBounds.push(obs.bottom);
  }
  yBounds.sort((a, b) => a - b);

  const lanes = new Set();
  const topExtent = yBounds[0];
  const bottomExtent = yBounds[yBounds.length - 1];

  // Bypass above and below all obstacles
  for (const mult of [2, 3]) {
    lanes.add(snapToGrid(topExtent - G * mult));
    lanes.add(snapToGrid(bottomExtent + G * mult));
  }

  // Detect GAPS between obstacle Y boundaries — route through them
  for (let i = 0; i < yBounds.length - 1; i++) {
    const gap = yBounds[i + 1] - yBounds[i];
    if (gap > G) {
      lanes.add(snapToGrid((yBounds[i] + yBounds[i + 1]) / 2));
    }
  }

  return [...lanes];
}

/**
 * Check that a route's first segment exits in the port departure direction.
 * Prevents wires from going backwards into source/target blocks.
 */
function respectsPortDirections(route, sd) {
  if (route.length < 2) return true;
  const fdx = route[1][0] - route[0][0];
  const fdy = route[1][1] - route[0][1];
  if (sd === 'right' && fdx < -0.5) return false;
  if (sd === 'left' && fdx > 0.5) return false;
  if (sd === 'down' && fdy < -0.5) return false;
  if (sd === 'up' && fdy > 0.5) return false;
  return true;
}

/**
 * Try geometric routes (straight, L, Z patterns) plus obstacle-aware
 * bypass routes using the Blocked Airspace model.
 * Returns the best clear route, or null if all hit obstacles.
 */
function tryGeometricRoutes(sx, sy, sd, ex, ey, ed, obsBlocks, bodyBlocks = []) {
  const G = GRID_SIZE;
  const candidates = [];

  // Departure stub: one cell in start direction
  const depX = sx + (sd === 'right' ? G : sd === 'left' ? -G : 0);
  const depY = sy + (sd === 'down' ? G : sd === 'up' ? -G : 0);

  // Approach stub: one cell in end direction (toward the wire, away from block)
  const appX = ex + (ed === 'right' ? G : ed === 'left' ? -G : 0);
  const appY = ey + (ed === 'down' ? G : ed === 'up' ? -G : 0);

  // === Route candidates (all include start and end points) ===

  // 1. Straight line: start→end (if roughly aligned)
  if (Math.abs(sy - ey) < 1) {
    candidates.push([[sx, sy], [ex, ey]]);
  }
  if (Math.abs(sx - ex) < 1) {
    candidates.push([[sx, sy], [ex, ey]]);
  }

  // 2. L-routes via departure/approach (2 segments + stubs)
  // Horizontal-first: start → dep → (appX, depY) → (appX, appY) → end
  candidates.push([[sx, sy], [depX, depY], [appX, depY], [appX, appY], [ex, ey]]);
  // Vertical-first: start → dep → (depX, appY) → (appX, appY) → end
  candidates.push([[sx, sy], [depX, depY], [depX, appY], [appX, appY], [ex, ey]]);

  // 3. L-routes without stubs (simpler, fewer bends)
  // Horizontal-first: start → (ex, sy) → end
  candidates.push([[sx, sy], [ex, sy], [ex, ey]]);
  // Vertical-first: start → (sx, ey) → end
  candidates.push([[sx, sy], [sx, ey], [ex, ey]]);

  // 4. Z-routes with midpoints
  for (const frac of [0.5, 0.35, 0.65, 0.2, 0.8]) {
    const mx = snapToGrid(sx + (ex - sx) * frac);
    const my = snapToGrid(sy + (ey - sy) * frac);
    // H-V-H: start → (mx, sy) → (mx, ey) → end
    candidates.push([[sx, sy], [mx, sy], [mx, ey], [ex, ey]]);
    // V-H-V: start → (sx, my) → (ex, my) → end
    candidates.push([[sx, sy], [sx, my], [ex, my], [ex, ey]]);
  }

  // 5. Z-routes via departure/approach with midpoints
  for (const frac of [0.5, 0.3, 0.7]) {
    const mx = snapToGrid(depX + (appX - depX) * frac);
    candidates.push([[sx, sy], [depX, depY], [mx, depY], [mx, appY], [appX, appY], [ex, ey]]);
  }

  // 6. U-routes (for going backward: right exit but target is to the left)
  if ((sd === 'right' && ex < sx) || (sd === 'left' && ex > sx)) {
    const exitX = sd === 'right' ? sx + G * 2 : sx - G * 2;
    const enterX = ed === 'left' ? ex - G * 2 : ed === 'right' ? ex + G * 2 : ex;
    // Try tight detours first (G*3), then wider (G*5)
    for (const mult of [3, 5]) {
      const detourY = snapToGrid(Math.max(sy, ey) + G * mult);
      candidates.push([[sx, sy], [exitX, sy], [exitX, detourY], [enterX, detourY], [enterX, ey], [ex, ey]]);
      const detourYUp = snapToGrid(Math.min(sy, ey) - G * mult);
      candidates.push([[sx, sy], [exitX, sy], [exitX, detourYUp], [enterX, detourYUp], [enterX, ey], [ex, ey]]);
    }
  }

  // === 7. OBSTACLE-AWARE BYPASS ROUTES (Blocked Airspace) ===
  // When endpoints are at similar Y-levels, Z-route midpoints collapse to
  // the same Y as endpoints, producing straight lines that hit obstacles.
  // Scan for actual obstacle positions and generate routes above/below them.
  // Include bodyBlocks so bypass lanes account for source/target bodies too.
  const airspaces = [
    ...obsBlocks.map(b => getBlockBounds(b, COLLISION_PAD)),
    ...bodyBlocks.map(b => getBlockBounds(b, COLLISION_PAD)),
  ];
  const bypassLanes = findBypassLanes(sx, sy, ex, ey, airspaces);
  for (const byY of bypassLanes) {
    // V-H-V: vertical departure, horizontal bypass, vertical approach
    candidates.push([[sx, sy], [sx, byY], [ex, byY], [ex, ey]]);
    // With departure/approach stubs for clean port exit
    candidates.push([[sx, sy], [depX, depY], [depX, byY], [appX, byY], [appX, appY], [ex, ey]]);
    // H-V-H via midpoints at different fractions
    for (const frac of [0.5, 0.35, 0.65]) {
      const mx = snapToGrid(sx + (ex - sx) * frac);
      candidates.push([[sx, sy], [mx, sy], [mx, byY], [ex, byY], [ex, ey]]);
      candidates.push([[sx, sy], [sx, byY], [mx, byY], [mx, ey], [ex, ey]]);
    }
  }

  // Score and filter candidates
  // TWO-LAYER collision detection:
  //   1. Other blocks: full airspace padding (COLLISION_PAD * 0.6)
  //   2. Source/target blocks: body-only padding (BODY_PAD=2) — blocks the physical
  //      block body while keeping ports accessible (ports are at PORT_DIST=48 from
  //      center, body half-width=40, so ports are 8px outside body edge)
  // Split obsBlocks: real blocks are hard obstacles, wire zones are soft (prefer to avoid)
  const realObs = obsBlocks.filter(b => !b._bounds);
  const wireObs = obsBlocks.filter(b => b._bounds);

  const valid = [];
  for (const route of candidates) {
    const simplified = simplifyPath(route);
    if (simplified.length < 2) continue;
    // Hard-reject routes that hit real blocks
    if (!routeClear(simplified, realObs, COLLISION_PAD * 0.6)) continue;
    if (!routeClearBody(simplified, bodyBlocks)) continue;
    valid.push(simplified);
  }

  if (valid.length === 0) return null;

  // Count collinear wire overlaps (parallel segments sharing the same channel).
  // Perpendicular crossings are fine (bridge arcs handle those visually).
  const wireHitCount = (route) => {
    let hits = 0;
    for (let i = 0; i < route.length - 1; i++) {
      const [x1, y1] = route[i], [x2, y2] = route[i + 1];
      const segIsH = Math.abs(y1 - y2) < 1;
      const segIsV = Math.abs(x1 - x2) < 1;
      for (const wb of wireObs) {
        const b = wb._bounds;
        if (segIsH) {
          // Horizontal segment — only count if wire zone is also roughly horizontal
          // (zone height ≤ zone width means it's a horizontal wire zone)
          const zoneW = b.right - b.left, zoneH = b.bottom - b.top;
          if (zoneH <= zoneW && y1 >= b.top && y1 <= b.bottom &&
              Math.max(x1, x2) >= b.left && Math.min(x1, x2) <= b.right) hits++;
        } else if (segIsV) {
          // Vertical segment — only count if wire zone is also roughly vertical
          const zoneW = b.right - b.left, zoneH = b.bottom - b.top;
          if (zoneW <= zoneH && x1 >= b.left && x1 <= b.right &&
              Math.max(y1, y2) >= b.top && Math.min(y1, y2) <= b.bottom) hits++;
        }
      }
    }
    return hits;
  };

  // Score how well a route's first segment follows the port exit direction.
  // When target is opposite to exit direction, don't heavily penalize going toward target.
  const targetAligned = (sd === 'right' && ex >= sx) || (sd === 'left' && ex <= sx) ||
                        (sd === 'down' && ey >= sy) || (sd === 'up' && ey <= sy);
  const exitScore = (route) => {
    if (route.length < 2) return 0;
    const dx = route[1][0] - route[0][0], dy = route[1][1] - route[0][1];
    // When exit direction opposes target, use mild preference instead of strong penalty
    const penalty = targetAligned ? -10 : -1;
    if (sd === 'right' && dx < -0.5) return penalty;
    if (sd === 'left' && dx > 0.5) return penalty;
    if (sd === 'down' && dy < -0.5) return penalty;
    if (sd === 'up' && dy > 0.5) return penalty;
    if (sd === 'right' && dx > 0.5) return 1;
    if (sd === 'left' && dx < -0.5) return 1;
    if (sd === 'down' && dy > 0.5) return 1;
    if (sd === 'up' && dy < -0.5) return 1;
    return 0;
  };

  // Prefer routes with zero collinear wire overlaps
  // If clean routes exist (no collinear overlaps), use them
  // Otherwise fall through to A* which can search for offset grid paths
  const clean = valid.filter(route => wireHitCount(route) === 0);
  const pool = clean.length > 0 ? clean : null;

  if (!pool) return null; // Force A* to find an offset path

  pool.sort((a, b) => {
    const ba = routeBends(a), bb = routeBends(b);
    if (ba !== bb) return ba - bb;
    const la = routeLength(a), lb = routeLength(b);
    if (Math.abs(la - lb) > 1) return la - lb;
    return exitScore(b) - exitScore(a);
  });

  return pool[0];
}

/**
 * Binary min-heap for efficient A* priority queue — O(log n) push/pop.
 */
class MinHeap {
  constructor() { this.data = []; }
  get size() { return this.data.length; }
  push(node) {
    this.data.push(node);
    this._bubbleUp(this.data.length - 1);
  }
  pop() {
    const top = this.data[0];
    const last = this.data.pop();
    if (this.data.length > 0) {
      this.data[0] = last;
      this._sinkDown(0);
    }
    return top;
  }
  _bubbleUp(i) {
    while (i > 0) {
      const parent = (i - 1) >> 1;
      if (this.data[i].f < this.data[parent].f) {
        [this.data[i], this.data[parent]] = [this.data[parent], this.data[i]];
        i = parent;
      } else break;
    }
  }
  _sinkDown(i) {
    const n = this.data.length;
    while (true) {
      let smallest = i;
      const l = 2 * i + 1, r = 2 * i + 2;
      if (l < n && this.data[l].f < this.data[smallest].f) smallest = l;
      if (r < n && this.data[r].f < this.data[smallest].f) smallest = r;
      if (smallest !== i) {
        [this.data[i], this.data[smallest]] = [this.data[smallest], this.data[i]];
        i = smallest;
      } else break;
    }
  }
}

/**
 * A* Manhattan router — fallback when geometric routes fail.
 * Uses binary min-heap for O(n log n) performance.
 * Strong turn penalty produces clean textbook-quality right-angled wires.
 */
function astarRoute(sx, sy, sd, ex, ey, ed, allBlocks, excludeIds) {
  const G = GRID_SIZE;
  const MAX_ITER = 10000;

  // Snap start/end
  const startX = snapToGrid(sx), startY = snapToGrid(sy);
  const endX = snapToGrid(ex), endY = snapToGrid(ey);

  if (startX === endX && startY === endY) return [[startX, startY]];

  // Build obstacle grid:
  //   - Real blocks: fully blocked (cannot route through)
  //   - Wire zones: soft penalty only (wires can freely cross other wires)
  // Wires should NEVER be hard-blocked — only real blocks are walls.
  // The crossing bridge arcs handle visual wire-over-wire intersections.
  const blocked = new Set();
  const wirePenalty = new Set();
  for (const block of Object.values(allBlocks)) {
    if (block._bounds) {
      // Wire zones: mild penalty to prefer spacing, but never block
      const b = block._bounds;
      const left = Math.floor(b.left / G) * G;
      const right = Math.ceil(b.right / G) * G;
      const top = Math.floor(b.top / G) * G;
      const bottom = Math.ceil(b.bottom / G) * G;
      for (let gx = left; gx <= right; gx += G) {
        for (let gy = top; gy <= bottom; gy += G) {
          wirePenalty.add(`${gx},${gy}`);
        }
      }
      continue;
    }
    const padding = excludeIds.includes(block.id) ? 2 : COLLISION_PAD;
    const bounds = getBlockBounds(block, padding);
    const left = Math.floor(bounds.left / G) * G;
    const right = Math.ceil(bounds.right / G) * G;
    const top = Math.floor(bounds.top / G) * G;
    const bottom = Math.ceil(bounds.bottom / G) * G;
    for (let gx = left; gx <= right; gx += G) {
      for (let gy = top; gy <= bottom; gy += G) {
        blocked.add(`${gx},${gy}`);
      }
    }
  }

  // Bypass: allow start, end, and their immediate corridors (port exits)
  const bypass = new Set([`${startX},${startY}`, `${endX},${endY}`]);
  const addCorridor = (px, py, dir, steps) => {
    for (let i = 1; i <= steps; i++) {
      let cx = px, cy = py;
      if (dir === 'right') cx += G * i;
      else if (dir === 'left') cx -= G * i;
      else if (dir === 'down') cy += G * i;
      else if (dir === 'up') cy -= G * i;
      bypass.add(`${cx},${cy}`);
    }
  };
  addCorridor(startX, startY, sd, 3);
  addCorridor(endX, endY, ed, 3);

  // A* search with binary min-heap
  const heuristic = (x, y) => Math.abs(endX - x) + Math.abs(endY - y);
  const bestG = new Map(); // key → best g-score seen
  const heap = new MinHeap();
  const h0 = heuristic(startX, startY);
  const startNode = { x: startX, y: startY, g: 0, h: h0, f: h0, parent: null, dir: sd };
  heap.push(startNode);
  bestG.set(`${startX},${startY}`, 0);

  const dirMoves = [[G, 0, 'right'], [-G, 0, 'left'], [0, G, 'down'], [0, -G, 'up']];
  let iter = 0;

  while (heap.size > 0 && iter < MAX_ITER) {
    iter++;
    const current = heap.pop();
    const key = `${current.x},${current.y}`;

    // Skip if we've already found a better path to this node
    const recordedG = bestG.get(key);
    if (recordedG !== undefined && recordedG < current.g) continue;

    if (current.x === endX && current.y === endY) {
      // Reconstruct path
      const path = [];
      let node = current;
      while (node) { path.unshift([node.x, node.y]); node = node.parent; }
      return simplifyPath(path);
    }

    for (const [ddx, ddy, dirName] of dirMoves) {
      const nx = current.x + ddx, ny = current.y + ddy;
      const nKey = `${nx},${ny}`;

      if (blocked.has(nKey) && !bypass.has(nKey)) continue;

      let stepCost = G;
      // Very strong turn penalty: prefer straight segments (textbook quality)
      if (dirName === current.dir) stepCost *= 0.6;
      else stepCost *= 2.5;
      // Prefer forward/down flow (natural signal direction)
      if (dirName === 'right' || dirName === 'down') stepCost *= 0.90;
      // First move: prefer port exit direction, but only when target is roughly in that direction.
      // When exit direction is OPPOSITE to target (e.g., exit left but target is right),
      // allow the router freedom to pick the shortest path without heavy penalty.
      if (current.parent === null && dirName !== sd) {
        const targetAligned = (sd === 'right' && ex >= sx) || (sd === 'left' && ex <= sx) ||
                              (sd === 'down' && ey >= sy) || (sd === 'up' && ey <= sy);
        stepCost *= targetAligned ? 5.0 : 1.5;
      }
      // Heavy penalty near existing wires — push wires to find offset paths
      if (wirePenalty.has(nKey)) stepCost *= 6.0;

      const ng = current.g + stepCost;

      // Skip if we already have a better path to this neighbor
      const existingG = bestG.get(nKey);
      if (existingG !== undefined && existingG <= ng) continue;
      bestG.set(nKey, ng);

      const nh = heuristic(nx, ny);
      const newNode = { x: nx, y: ny, g: ng, h: nh, f: ng + nh, parent: current, dir: dirName };
      heap.push(newNode);
    }
  }

  return null; // A* failed
}

/**
 * Detect all crossing points between routed wires.
 * Only checks horizontal-vs-vertical segment intersections (Manhattan routing).
 * Returns array of { wireIdx, x, y } where wireIdx is the wire that gets the bridge.
 */
function detectWireCrossings(allRoutes, siblingSets) {
  const crossingMap = {}; // wireIdx → [{x, y}]

  for (let i = 0; i < allRoutes.length; i++) {
    if (!allRoutes[i] || allRoutes[i].length < 2) continue;
    for (let j = i + 1; j < allRoutes.length; j++) {
      if (!allRoutes[j] || allRoutes[j].length < 2) continue;
      // Skip sibling wires (same source port — they share a branch point)
      if (siblingSets[i] && siblingSets[i].has(j)) continue;

      const routeA = allRoutes[i];
      const routeB = allRoutes[j];

      for (let si = 0; si < routeA.length - 1; si++) {
        const [ax1, ay1] = routeA[si];
        const [ax2, ay2] = routeA[si + 1];

        for (let sj = 0; sj < routeB.length - 1; sj++) {
          const [bx1, by1] = routeB[sj];
          const [bx2, by2] = routeB[sj + 1];

          // Check H-V or V-H crossing
          const aIsH = Math.abs(ay1 - ay2) < 1;
          const aIsV = Math.abs(ax1 - ax2) < 1;
          const bIsH = Math.abs(by1 - by2) < 1;
          const bIsV = Math.abs(bx1 - bx2) < 1;

          let crossX, crossY;
          if (aIsH && bIsV) {
            crossY = ay1;
            crossX = bx1;
            const aMinX = Math.min(ax1, ax2), aMaxX = Math.max(ax1, ax2);
            const bMinY = Math.min(by1, by2), bMaxY = Math.max(by1, by2);
            if (crossX > aMinX && crossX < aMaxX && crossY > bMinY && crossY < bMaxY) {
              // Wire drawn later (higher index) gets the bridge
              const bridgeWire = j;
              if (!crossingMap[bridgeWire]) crossingMap[bridgeWire] = [];
              crossingMap[bridgeWire].push({ x: crossX, y: crossY });
            }
          } else if (aIsV && bIsH) {
            crossX = ax1;
            crossY = by1;
            const bMinX = Math.min(bx1, bx2), bMaxX = Math.max(bx1, bx2);
            const aMinY = Math.min(ay1, ay2), aMaxY = Math.max(ay1, ay2);
            if (crossX > bMinX && crossX < bMaxX && crossY > aMinY && crossY < aMaxY) {
              const bridgeWire = j;
              if (!crossingMap[bridgeWire]) crossingMap[bridgeWire] = [];
              crossingMap[bridgeWire].push({ x: crossX, y: crossY });
            }
          }
        }
      }
    }
  }
  return crossingMap;
}

/**
 * Build an SVG path string with bridge arcs at wire crossing points.
 * At each crossing, inserts a small semicircular arc (bump) to indicate no junction.
 */
function buildPathWithBridges(points, crossings) {
  if (!points || points.length === 0) return '';
  if (!crossings || crossings.length === 0) return pointsToPath(points);

  const BRIDGE_R = 7; // Bridge arc radius in pixels
  let d = `M ${points[0][0]} ${points[0][1]}`;

  for (let i = 0; i < points.length - 1; i++) {
    const [x1, y1] = points[i];
    const [x2, y2] = points[i + 1];

    // Find crossings on this segment
    const isH = Math.abs(y1 - y2) < 1;
    const isV = Math.abs(x1 - x2) < 1;

    // Filter crossings that fall on this segment
    const segCrossings = crossings.filter(c => {
      if (isH) {
        const minX = Math.min(x1, x2), maxX = Math.max(x1, x2);
        return Math.abs(c.y - y1) < 1 && c.x > minX + BRIDGE_R && c.x < maxX - BRIDGE_R;
      }
      if (isV) {
        const minY = Math.min(y1, y2), maxY = Math.max(y1, y2);
        return Math.abs(c.x - x1) < 1 && c.y > minY + BRIDGE_R && c.y < maxY - BRIDGE_R;
      }
      return false;
    });

    if (segCrossings.length === 0) {
      d += ` L ${x2} ${y2}`;
      continue;
    }

    // Sort crossings along segment direction
    if (isH) {
      const dir = x2 > x1 ? 1 : -1;
      segCrossings.sort((a, b) => (a.x - b.x) * dir);
      let cx = x1;
      for (const c of segCrossings) {
        // Draw line to just before the crossing, then arc over it
        d += ` L ${c.x - BRIDGE_R * dir} ${y1}`;
        // Semicircular arc: sweep direction depends on wire direction
        d += ` A ${BRIDGE_R} ${BRIDGE_R} 0 0 ${dir > 0 ? 1 : 0} ${c.x + BRIDGE_R * dir} ${y1}`;
        cx = c.x + BRIDGE_R * dir;
      }
      d += ` L ${x2} ${y2}`;
    } else if (isV) {
      const dir = y2 > y1 ? 1 : -1;
      segCrossings.sort((a, b) => (a.y - b.y) * dir);
      let cy = y1;
      for (const c of segCrossings) {
        d += ` L ${x1} ${c.y - BRIDGE_R * dir}`;
        d += ` A ${BRIDGE_R} ${BRIDGE_R} 0 0 ${dir > 0 ? 0 : 1} ${x1} ${c.y + BRIDGE_R * dir}`;
        cy = c.y + BRIDGE_R * dir;
      }
      d += ` L ${x2} ${y2}`;
    } else {
      d += ` L ${x2} ${y2}`;
    }
  }

  return d;
}

/**
 * Emergency fallback: route around ALL blocks via detour.
 */
function emergencyRoute(sx, sy, sd, ex, ey, ed, allBlocks) {
  const G = GRID_SIZE;
  const blocks = Object.values(allBlocks).filter(b => !b._bounds);
  let maxY = Math.max(sy, ey);
  for (const b of blocks) {
    const bounds = getBlockBounds(b, G);
    maxY = Math.max(maxY, bounds.bottom);
  }
  const detourY = snapToGrid(maxY + G * 4);

  if (sd === 'right' && ed === 'left' && ex > sx && Math.abs(ey - sy) < G) {
    const mx = snapToGrid((sx + ex) / 2);
    return [[sx, sy], [mx, sy], [mx, ey], [ex, ey]];
  }

  return simplifyPath([
    [sx, sy],
    [sx + (sd === 'right' ? G : sd === 'left' ? -G : 0), sy + (sd === 'down' ? G : sd === 'up' ? -G : 0)],
    [sx + (sd === 'right' ? G : -G), detourY],
    [ex + (ed === 'left' ? -G : G), detourY],
    [ex + (ed === 'left' ? -G : G), ey],
    [ex, ey],
  ]);
}

/**
 * Main wire routing entry point.
 * Tries geometric routes first (clean results), falls back to A* then emergency.
 */
function routeWire(fromPort, toPort, blocks, excludeIds = []) {
  const sx = snapToGrid(fromPort.x), sy = snapToGrid(fromPort.y);
  const ex = snapToGrid(toPort.x), ey = snapToGrid(toPort.y);
  const sd = fromPort.dir || 'right';
  const ed = toPort.dir || 'left';

  if (sx === ex && sy === ey) return [[sx, sy]];

  // Other blocks: full airspace collision detection
  const obsBlocks = Object.values(blocks).filter(b => !excludeIds.includes(b.id));
  // Source/target blocks: body-only collision (ports accessible, body blocked)
  const bodyBlocks = Object.values(blocks).filter(b => excludeIds.includes(b.id));

  // Phase 1: Geometric routes (cleanest results)
  const geoRoute = tryGeometricRoutes(sx, sy, sd, ex, ey, ed, obsBlocks, bodyBlocks);
  if (geoRoute) return geoRoute;

  // Phase 2: A* pathfinding (handles complex obstacle scenarios)
  const aRoute = astarRoute(sx, sy, sd, ex, ey, ed, blocks, excludeIds);
  if (aRoute) return aRoute;

  // Phase 3: Emergency fallback
  return emergencyRoute(sx, sy, sd, ex, ey, ed, blocks);
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
      <rect x={-w/2} y={-h/2} width={w} height={h} rx={12} className="bd-block-shape bd-block-io" />
      <text x={-4} y={1} textAnchor="middle" dominantBaseline="middle" className="bd-block-label">{label}</text>
      <polygon points={`${w/2-10},-8 ${w/2},0 ${w/2-10},8`} className="bd-block-arrow" />
      <circle
        cx={PORT_DIST} cy={0} r={PORT_RADIUS}
        className="bd-port bd-port-output"
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'output', 0, x + PORT_DIST, y, 'right'); }}
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
      <rect x={-w/2} y={-h/2} width={w} height={h} rx={12} className="bd-block-shape bd-block-io" />
      <polygon points={`${-w/2+10},-8 ${-w/2},0 ${-w/2+10},8`} className="bd-block-arrow bd-block-arrow-in" />
      <text x={4} y={1} textAnchor="middle" dominantBaseline="middle" className="bd-block-label">{label}</text>
      <circle
        cx={-PORT_DIST} cy={0} r={PORT_RADIUS}
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
  const hw = BLOCK_SIZES.gain.width / 2, hh = BLOCK_SIZES.gain.height / 2;

  // Triangle points in signal flow direction
  const triPoints = flipped
    ? `${hw-4},-${hh-6} ${-hw+4},0 ${hw-4},${hh-6}`
    : `${-hw+4},-${hh-6} ${hw-4},0 ${-hw+4},${hh-6}`;
  const textX = flipped ? 6 : -6;

  // Port colors: based on signal flow direction
  // LTR: port 0 (left) = input (red), port 1 (right) = output (blue)
  // RTL: port 0 (left) = output (blue), port 1 (right) = input (red)
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
        cx={-PORT_DIST} cy={0} r={PORT_RADIUS}
        className={`bd-port ${flipped ? 'bd-port-output' : 'bd-port-input'}`}
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 0, x - PORT_DIST, y, 'left'); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 0); }}
      />
      <circle
        cx={PORT_DIST} cy={0} r={PORT_RADIUS}
        className={`bd-port ${flipped ? 'bd-port-input' : 'bd-port-output'}`}
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 1, x + PORT_DIST, y, 'right'); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 1); }}
      />
    </g>
  );
}

function AdderBlock({ block, isSelected, onMouseDown, onPortMouseDown, onPortMouseUp, onToggleSign, dynamicPorts }) {
  const { x, y } = block.position;
  const rawSigns = block.signs || ['+', '+', '+'];
  const signs = [rawSigns[0] || '+', rawSigns[1] || '+', rawSigns[2] || '+'];
  const r = BLOCK_SIZES.adder.radius;

  // Dynamic or default port positions
  const dp = dynamicPorts || {};
  const p0 = dp[0] || { dx: -PORT_DIST, dy: 0, dir: 'left' };
  const p1 = dp[1] || { dx: 0, dy: PORT_DIST, dir: 'down' };
  const p2 = dp[2] || { dx: PORT_DIST, dy: 0, dir: 'right' };

  // Sign label position: offset from port perpendicular to port direction
  const signPos = (port) => {
    const so = 16;
    switch (port.dir) {
      case 'left': return { x: port.dx, y: port.dy - so };
      case 'right': return { x: port.dx, y: port.dy - so };
      case 'up': return { x: port.dx + so, y: port.dy };
      case 'down': return { x: port.dx + so, y: port.dy + 4 };
      default: return { x: port.dx, y: port.dy - so };
    }
  };
  const s0 = signPos(p0);
  const s1 = signPos(p1);

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
      <text x={s0.x} y={s0.y} textAnchor="middle" className="bd-sign-label"
        onClick={(e) => { e.stopPropagation(); onToggleSign(block.id, 0); }}
        style={{ cursor: 'pointer' }}
      >{signs[0]}</text>
      <circle
        cx={p1.dx} cy={p1.dy} r={PORT_RADIUS}
        className="bd-port bd-port-input"
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 1, x + p1.dx, y + p1.dy, p1.dir); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 1); }}
      />
      <text x={s1.x} y={s1.y} textAnchor="middle" className="bd-sign-label"
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

  // Arrow in signal flow direction
  const arrowX = flipped ? -20 : 20;
  const arrowPoints = flipped
    ? `${arrowX+6},-6 ${arrowX-2},0 ${arrowX+6},6`
    : `${arrowX-6},-6 ${arrowX+2},0 ${arrowX-6},6`;

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
        cx={-PORT_DIST} cy={0} r={PORT_RADIUS}
        className={`bd-port ${flipped ? 'bd-port-output' : 'bd-port-input'}`}
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 0, x - PORT_DIST, y, 'left'); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 0); }}
      />
      <circle
        cx={PORT_DIST} cy={0} r={PORT_RADIUS}
        className={`bd-port ${flipped ? 'bd-port-input' : 'bd-port-output'}`}
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 1, x + PORT_DIST, y, 'right'); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 1); }}
      />
    </g>
  );
}

function IntegratorBlock({ block, isSelected, onMouseDown, onPortMouseDown, onPortMouseUp, flowDir = 'ltr' }) {
  const { x, y } = block.position;
  const flipped = flowDir === 'rtl';
  const hw = BLOCK_SIZES.integrator.width / 2, hh = BLOCK_SIZES.integrator.height / 2;

  const arrowX = flipped ? -20 : 20;
  const arrowPoints = flipped
    ? `${arrowX+6},-6 ${arrowX-2},0 ${arrowX+6},6`
    : `${arrowX-6},-6 ${arrowX+2},0 ${arrowX-6},6`;

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
        cx={-PORT_DIST} cy={0} r={PORT_RADIUS}
        className={`bd-port ${flipped ? 'bd-port-output' : 'bd-port-input'}`}
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 0, x - PORT_DIST, y, 'left'); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 0); }}
      />
      <circle
        cx={PORT_DIST} cy={0} r={PORT_RADIUS}
        className={`bd-port ${flipped ? 'bd-port-input' : 'bd-port-output'}`}
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 1, x + PORT_DIST, y, 'right'); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 1); }}
      />
    </g>
  );
}

/**
 * Convert a TF expression string to LaTeX for display on blocks.
 * e.g. "(1+2R)/(1-0.5R)" → "\\frac{1+2R}{1-0.5R}"
 */
function tfExprToLatex(expression, systemType) {
  if (!expression || expression === '1') {
    return systemType === 'ct' ? 'H(s)' : 'H(z)';
  }
  const expr = expression.trim();
  // Try to split on "/" that separates numerator/denominator
  // Handle parenthesized form: (num)/(den) or num/den
  const ratioMatch = expr.match(/^\(([^)]+)\)\s*\/\s*\(([^)]+)\)$/) ||
                     expr.match(/^([^/]+)\/(.+)$/);
  if (ratioMatch) {
    const num = ratioMatch[1].trim();
    const den = ratioMatch[2].trim();
    return `\\frac{${num}}{${den}}`;
  }
  return expr;
}

// ============================================================================
// Signal Flow Graph (SFG) conversion
// ============================================================================
// In a proper Mason's SFG:
//   - Every node is a summing point (implicit addition of all incoming edges)
//   - Edges carry gains (transfer functions)
//   - No separate "adder" blocks — adders, junctions, input, output all become nodes
//   - Gain/delay/integrator/custom_tf blocks become edges with gain between nodes
// ============================================================================

// Iterative repulsion to resolve overlapping SFG nodes while preserving spatial layout
function resolveNodeOverlaps(nodes) {
  if (nodes.length < 2) return;
  const MIN_SPACING = 80;
  const MAX_ITER = 30;
  const DAMPING = 0.7;
  const ANCHOR = 0.15;

  for (let iter = 0; iter < MAX_ITER; iter++) {
    let maxDisp = 0;
    // Pairwise repulsion
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        let dx = nodes[j].x - nodes[i].x;
        let dy = nodes[j].y - nodes[i].y;
        let dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < MIN_SPACING) {
          if (dist < 1) { dx = (Math.random() - 0.5) * 2; dy = (Math.random() - 0.5) * 2; dist = Math.sqrt(dx * dx + dy * dy) || 1; }
          const overlap = MIN_SPACING - dist;
          const fx = (dx / dist) * overlap * 0.5 * DAMPING;
          const fy = (dy / dist) * overlap * 0.5 * DAMPING;
          nodes[i].x -= fx; nodes[i].y -= fy;
          nodes[j].x += fx; nodes[j].y += fy;
          maxDisp = Math.max(maxDisp, Math.abs(fx), Math.abs(fy));
        }
      }
    }
    // Anchor spring back to original positions
    for (const n of nodes) {
      n.x += (n.originalX - n.x) * ANCHOR;
      n.y += (n.originalY - n.y) * ANCHOR;
    }
    if (maxDisp < 0.5) break;
  }
}

function convertToSFG(blocks, connections, systemType) {
  const nodes = [];
  const edges = [];
  const nodeMap = {};

  // ALL transfer-function block types: these become edge gains, NOT nodes
  const TF_TYPES = new Set(['gain', 'delay', 'integrator', 'custom_tf']);

  const addNode = (id, label, x, y, type) => {
    if (nodeMap[id]) return;
    const node = { id, label, x, y, type, originalX: x, originalY: y };
    nodes.push(node);
    nodeMap[id] = node;
  };

  // 1. Create SFG nodes — only signal points (input, output, adder, junction)
  //    All TF blocks (gain, delay, integrator, custom_tf) become edge gains
  let varIdx = 0;
  const subscriptDigit = (n) => {
    const subs = '₀₁₂₃₄₅₆₇₈₉';
    return String(n).split('').map(d => subs[parseInt(d)] || d).join('');
  };

  for (const block of Object.values(blocks)) {
    const { x, y } = block.position;
    const type = block.type;

    if (type === 'input') {
      const lbl = systemType === 'ct' ? 'x(t)' : 'x[n]';
      addNode(block.id, lbl, x, y, 'source');
    } else if (type === 'output') {
      const lbl = systemType === 'ct' ? 'y(t)' : 'y[n]';
      addNode(block.id, lbl, x, y, 'sink');
    } else if (type === 'adder') {
      varIdx++;
      addNode(block.id, 'e' + subscriptDigit(varIdx), x, y, 'sum');
    } else if (type === 'junction') {
      varIdx++;
      addNode(block.id, 's' + subscriptDigit(varIdx), x, y, 'branch');
    }
    // gain, delay, integrator, custom_tf — no node created
  }

  // 2. Get gain label for a TF block
  const getBlockGain = (block) => {
    const type = block.type;
    if (type === 'gain') {
      const v = block.value ?? 1;
      const s = (v === Math.floor(v)) ? String(Math.floor(v)) : String(v);
      return { gain: s, gainLatex: s };
    } else if (type === 'delay') {
      return { gain: 'R', gainLatex: 'R' };
    } else if (type === 'integrator') {
      return { gain: 'A', gainLatex: 'A' };
    } else if (type === 'custom_tf') {
      const expr = block.expression || '1';
      let gainLatex = tfExprToLatex(expr, systemType);
      let gain = expr;
      if (gainLatex === (systemType === 'ct' ? 'H(s)' : 'H(z)')) {
        gainLatex = '1';
        gain = '1';
      }
      return { gain, gainLatex };
    }
    return { gain: '1', gainLatex: '1' };
  };

  // 3. Build connection lookup per block
  const outgoing = {}; // blockId -> [conn]
  const incoming = {}; // blockId -> [conn]
  for (const conn of connections) {
    if (!blocks[conn.from_block] || !blocks[conn.to_block]) continue;
    if (!outgoing[conn.from_block]) outgoing[conn.from_block] = [];
    outgoing[conn.from_block].push(conn);
    if (!incoming[conn.to_block]) incoming[conn.to_block] = [];
    incoming[conn.to_block].push(conn);
  }

  // 4. Trace forward from a TF block through chains of TF blocks
  //    to find the destination signal-node and accumulated gain
  const traceForward = (blockId, gains, gainsLatex, visited) => {
    if (visited.has(blockId)) return [];
    visited.add(blockId);
    const results = [];
    const outConns = outgoing[blockId] || [];
    for (const conn of outConns) {
      const targetBlock = blocks[conn.to_block];
      if (!targetBlock) continue;
      if (TF_TYPES.has(targetBlock.type)) {
        // Chain through another TF block — multiply gains
        const { gain, gainLatex } = getBlockGain(targetBlock);
        results.push(...traceForward(conn.to_block, [...gains, gain], [...gainsLatex, gainLatex], visited));
      } else {
        // Reached a signal node — record destination with accumulated gains
        results.push({ nodeId: conn.to_block, conn, gains, gainsLatex });
      }
    }
    return results;
  };

  // Multiply gain strings for display
  const multiplyGains = (gainArr) => {
    if (gainArr.length === 0) return '1';
    if (gainArr.length === 1) return gainArr[0];
    return gainArr.join(' \\cdot ');
  };
  const multiplyGainsPlain = (gainArr) => {
    if (gainArr.length === 0) return '1';
    if (gainArr.length === 1) return gainArr[0];
    return gainArr.join('·');
  };

  // 5. Create SFG edges by tracing connections from signal-node sources
  for (const block of Object.values(blocks)) {
    if (TF_TYPES.has(block.type)) continue; // TF blocks are not sources
    const outConns = outgoing[block.id] || [];

    for (const conn of outConns) {
      const targetBlock = blocks[conn.to_block];
      if (!targetBlock) continue;

      // Get adder sign for the target port
      let signNeg = false;
      if (targetBlock.type === 'adder' && targetBlock.signs) {
        if (targetBlock.signs[conn.to_port] === '-') signNeg = true;
      }

      if (TF_TYPES.has(targetBlock.type)) {
        // Source signal-node → TF block chain → destination signal-node(s)
        const { gain: firstGain, gainLatex: firstGainLatex } = getBlockGain(targetBlock);
        const destinations = traceForward(conn.to_block, [firstGain], [firstGainLatex], new Set());

        for (const dest of destinations) {
          if (!nodeMap[block.id] || !nodeMap[dest.nodeId]) continue;

          // Check adder sign at destination
          const destBlock = blocks[dest.nodeId];
          let destNeg = false;
          if (destBlock?.type === 'adder' && destBlock.signs) {
            if (destBlock.signs[dest.conn.to_port] === '-') destNeg = true;
          }

          let gainLatex = multiplyGains(dest.gainsLatex);
          let gain = multiplyGainsPlain(dest.gains);
          if (destNeg) {
            gainLatex = gain === '1' ? '-1' : '-(' + gainLatex + ')';
            gain = gain === '1' ? '-1' : '-(' + gain + ')';
          }

          edges.push({ from: block.id, to: dest.nodeId, gain, gainLatex });
        }
      } else {
        // Direct signal-node to signal-node (unity gain or -1 for negative adder port)
        if (!nodeMap[block.id] || !nodeMap[conn.to_block]) continue;

        let gain = '1', gainLatex = '1';
        if (signNeg) { gain = '-1'; gainLatex = '-1'; }

        edges.push({ from: block.id, to: conn.to_block, gain, gainLatex });
      }
    }
  }

  // Layout: spread overlapping nodes apart while preserving spatial correspondence
  resolveNodeOverlaps(nodes);

  return { nodes, edges };
}

// ============================================================================
// SFG rendering components
// ============================================================================

// SFG node radii — all circles (textbook convention: nodes = signals)
const SFG_NODE_RADIUS = { source: 18, sink: 18, sum: 14, branch: 8 };

function SFGNode({ node }) {
  const { x, y, label, type } = node;
  const isIO = type === 'source' || type === 'sink';
  const isBranch = type === 'branch';
  const r = SFG_NODE_RADIUS[type] || 14;

  // Colors: teal for input/output, blue for sum, gray for branch
  let fillColor, strokeColor, labelColor;
  if (isIO) {
    fillColor = 'rgba(20, 184, 166, 0.12)';
    strokeColor = '#14b8a6';
    labelColor = '#5eead4';
  } else if (isBranch) {
    fillColor = 'rgba(148, 163, 184, 0.35)';
    strokeColor = '#94a3b8';
    labelColor = '#94a3b8';
  } else {
    // sum node
    fillColor = 'rgba(59, 130, 246, 0.08)';
    strokeColor = '#3b82f6';
    labelColor = '#93c5fd';
  }

  return (
    <g className="sfg-node" transform={`translate(${x}, ${y})`} style={{ pointerEvents: 'none' }}>
      {/* Outer glow ring (not for branch points) */}
      {!isBranch && (
        <circle r={r + 5} fill="none" stroke={strokeColor} strokeWidth={1} opacity={0.2} />
      )}
      {/* Main circle */}
      <circle r={r} fill={fillColor} stroke={strokeColor} strokeWidth={isBranch ? 1.5 : 2} />
      {/* Label: inside for source/sink/sum, above for branch */}
      {label && !isBranch && (
        <text x={0} y={1} textAnchor="middle" dominantBaseline="central"
          fill={labelColor} fontSize={isIO ? 11 : 12} fontWeight={600}
          fontFamily="'Fira Code', monospace" style={{ pointerEvents: 'none', userSelect: 'none' }}>
          {label}
        </text>
      )}
      {label && isBranch && (
        <text x={0} y={-r - 6} textAnchor="middle" dominantBaseline="auto"
          fill={labelColor} fontSize={10} fontWeight={500}
          fontFamily="'Fira Code', monospace" style={{ pointerEvents: 'none', userSelect: 'none' }}>
          {label}
        </text>
      )}
      {/* "Input" / "Output" label below I/O nodes */}
      {isIO && (
        <text x={0} y={r + 16} textAnchor="middle" fill={strokeColor}
          fontSize={12} fontWeight={700} fontFamily="'Inter', sans-serif"
          style={{ pointerEvents: 'none', userSelect: 'none' }}>
          {type === 'source' ? 'Input' : 'Output'}
        </text>
      )}
    </g>
  );
}

function SFGEdge({ edge, nodesMap, edgeIndex, parallelOffset, allNodes }) {
  const fromNode = nodesMap[edge.from];
  const toNode = nodesMap[edge.to];
  if (!fromNode || !toNode) return null;

  const x1 = fromNode.x, y1 = fromNode.y;
  const x2 = toNode.x, y2 = toNode.y;
  const dx = x2 - x1, dy = y2 - y1;
  const dist = Math.sqrt(dx * dx + dy * dy);

  const isUnity = edge.gain === '1';
  const isNegative = edge.gain === '-1' || edge.gain?.startsWith('-');
  const isSelfLoop = edge.from === edge.to;
  // Feedback detection: right-to-left (dx < -10) OR negative gain edges
  // that go roughly horizontal (small vertical displacement relative to horizontal)
  const isFeedback = dx < -10 || (isNegative && Math.abs(dx) > 30);

  // Edge colors: cyan forward, amber feedback, red for negative gains
  const edgeColor = isFeedback ? '#f59e0b' : '#00d9ff';
  const labelTextColor = isNegative ? '#ef4444' : (isFeedback ? '#f59e0b' : '#00d9ff');

  // Arrow marker
  const markerRef = isFeedback ? 'url(#sfg-arrow-feedback)' : 'url(#sfg-arrow-forward)';

  let d, labelX, labelY;

  if (isSelfLoop) {
    // Self-loop: larger arc with more clearance, label well above
    const loopR = 50;
    const nr = SFG_NODE_RADIUS[fromNode.type] || 14;
    d = `M ${x1 - 10} ${y1 - nr}
         C ${x1 - loopR} ${y1 - loopR * 2.5}, ${x1 + loopR} ${y1 - loopR * 2.5}, ${x1 + 10} ${y1 - nr}`;
    labelX = x1;
    labelY = y1 - loopR * 2.5 - 8;
  } else {
    // Curvature: stronger base + bigger parallel separation
    const baseCurve = Math.min(70, Math.max(30, dist * 0.15));
    const offset = baseCurve + (parallelOffset || 0) * 50;

    const nx = -dy / (dist || 1);
    const ny = dx / (dist || 1);

    // Forward curves above (sign=-1), feedback curves below (sign=+1)
    const sign = isFeedback ? 1 : -1;
    const curveScale = isFeedback ? offset * 1.8 : offset;

    const cx = (x1 + x2) / 2 + nx * curveScale * sign;
    const cy = (y1 + y2) / 2 + ny * curveScale * sign;

    const fromR = SFG_NODE_RADIUS[fromNode.type] || 14;
    const toR = SFG_NODE_RADIUS[toNode.type] || 14;

    const cdx1 = cx - x1, cdy1 = cy - y1;
    const cLen1 = Math.sqrt(cdx1 * cdx1 + cdy1 * cdy1) || 1;
    const sx = x1 + (cdx1 / cLen1) * fromR;
    const sy = y1 + (cdy1 / cLen1) * fromR;

    const cdx2 = x2 - cx, cdy2 = y2 - cy;
    const cLen2 = Math.sqrt(cdx2 * cdx2 + cdy2 * cdy2) || 1;
    const ex = x2 - (cdx2 / cLen2) * toR;
    const ey = y2 - (cdy2 / cLen2) * toR;

    d = `M ${sx} ${sy} Q ${cx} ${cy}, ${ex} ${ey}`;

    // Shift label position along curve based on parallelOffset to avoid stacking
    const t = parallelOffset ? 0.3 + (parallelOffset % 2) * 0.4 : 0.5;
    const u = 1 - t;
    labelX = u * u * sx + 2 * u * t * cx + t * t * ex;
    labelY = u * u * sy + 2 * u * t * cy + t * t * ey;
  }

  // Push label away from any node it overlaps
  if (allNodes) {
    const LABEL_CLEARANCE = 14;
    for (const node of allNodes) {
      const nr = SFG_NODE_RADIUS[node.type] || 14;
      const clearance = nr + LABEL_CLEARANCE + 8;
      const dlx = labelX - node.x;
      const dly = labelY - node.y;
      const dld = Math.sqrt(dlx * dlx + dly * dly);
      if (dld < clearance) {
        const pushDist = clearance - dld + 4;
        if (dld > 0.1) {
          labelX += (dlx / dld) * pushDist;
          labelY += (dly / dld) * pushDist;
        } else {
          labelY -= pushDist;
        }
      }
    }
  }

  // KaTeX rendering with plain-text fallback
  const needsKatex = edge.gainLatex && (edge.gainLatex.includes('\\') || edge.gainLatex.includes('^') || edge.gainLatex.includes('_') || edge.gainLatex.includes('\\cdot'));
  let labelHtml = '';
  let katexFailed = false;
  if (needsKatex) {
    try {
      labelHtml = katex.renderToString(edge.gainLatex, { throwOnError: true, displayMode: false });
    } catch {
      katexFailed = true;
      labelHtml = '';
    }
  }

  // Always try KaTeX for compound gains (contain ·) even without special LaTeX chars
  const hasMultiply = !needsKatex && edge.gainLatex && edge.gainLatex.includes('\\cdot');
  if (hasMultiply && !labelHtml) {
    try {
      labelHtml = katex.renderToString(edge.gainLatex, { throwOnError: true, displayMode: false });
      if (labelHtml) katexFailed = false;
    } catch {
      katexFailed = true;
    }
  }

  // Plain text label (used when no KaTeX needed, or as fallback)
  const plainLabel = edge.gain || '';
  const labelWidth = Math.max(30, plainLabel.length * 9 + 20);
  const showKatex = (needsKatex || hasMultiply) && labelHtml && !katexFailed;

  // Unity edges: hide label entirely for cleaner look — the dashed line is enough
  const hideLabel = isUnity;

  return (
    <g style={{ pointerEvents: 'none' }}>
      {/* Edge path */}
      <path d={d} fill="none" stroke={edgeColor} strokeWidth={2} strokeLinecap="round"
        opacity={isUnity ? 0.3 : 0.85} markerEnd={markerRef}
        strokeDasharray={isUnity ? '4 6' : 'none'} />
      {/* Gain label — skip for unity edges (dashed line is self-evident) */}
      {!hideLabel && showKatex ? (
        <foreignObject x={labelX - 90} y={labelY - 18} width={180} height={36}
          style={{ overflow: 'visible', pointerEvents: 'none' }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            width: '100%', height: '100%',
            pointerEvents: 'none', userSelect: 'none',
          }}>
            <div style={{
              background: 'rgba(19, 27, 46, 0.95)', borderRadius: 8,
              border: '1px solid rgba(255,255,255,0.1)', padding: '3px 10px',
              whiteSpace: 'nowrap',
            }}>
              <div className="sfg-edge-label-katex" style={{ color: labelTextColor }}
                dangerouslySetInnerHTML={{ __html: labelHtml }} />
            </div>
          </div>
        </foreignObject>
      ) : !hideLabel ? (
        <g>
          <rect x={labelX - labelWidth / 2} y={labelY - 12} width={labelWidth} height={24}
            rx={8} fill="rgba(19, 27, 46, 0.95)" stroke="rgba(255,255,255,0.1)" strokeWidth={1} />
          <text x={labelX} y={labelY + 1} textAnchor="middle" dominantBaseline="central"
            fill={labelTextColor} fontSize={13} fontWeight={700}
            fontFamily="'Fira Code', monospace" style={{ pointerEvents: 'none', userSelect: 'none' }}>
            {plainLabel}
          </text>
        </g>
      ) : null}
    </g>
  );
}

function CustomTfBlock({ block, isSelected, onMouseDown, onPortMouseDown, onPortMouseUp, onTfDoubleClick, flowDir = 'ltr', systemType = 'dt' }) {
  const { x, y } = block.position;
  const flipped = flowDir === 'rtl';
  const hw = BLOCK_SIZES.custom_tf.width / 2, hh = BLOCK_SIZES.custom_tf.height / 2;
  const expression = block.expression || '1';
  const label = block.label || (systemType === 'ct' ? 'H(s)' : 'H(z)');
  const convertedFrom = block.converted_from;
  const latexStr = tfExprToLatex(expression, systemType);

  // Render KaTeX to HTML string
  let latexHtml = '';
  try {
    latexHtml = katex.renderToString(latexStr, { throwOnError: false, displayMode: false });
  } catch {
    const escaped = expression.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    latexHtml = `<span style="font-family:monospace;font-size:11px">${escaped}</span>`;
  }

  const isDefault = expression === '1';

  return (
    <g
      className={`bd-block bd-block-custom-tf ${isSelected ? 'bd-block-selected' : ''}`}
      onMouseDown={(e) => onMouseDown(e, block.id)}
      onDoubleClick={(e) => { e.stopPropagation(); onTfDoubleClick(block.id); }}
      transform={`translate(${x}, ${y})`}
    >
      <rect x={-hw} y={-hh} width={hw*2} height={hh*2} rx={8} className="bd-block-shape bd-block-custom-tf-rect" />
      {/* Label above the block */}
      <text x={0} y={-hh - 6} textAnchor="middle" className="bd-custom-tf-label">
        {label}
      </text>
      {/* Conversion badge */}
      {convertedFrom && (
        <g transform={`translate(${hw - 2}, ${-hh + 2})`}>
          <rect x={-14} y={-8} width={28} height={14} rx={4} className="bd-custom-tf-converted-badge" />
          <text x={0} y={0} textAnchor="middle" dominantBaseline="middle" className="bd-custom-tf-converted-text">
            {convertedFrom}→{systemType === 'dt' ? 'R' : 'A'}
          </text>
        </g>
      )}
      <foreignObject x={-hw + 4} y={-hh + 2} width={hw*2 - 8} height={hh*2 - 4}
        style={{ pointerEvents: 'none', overflow: 'visible' }}>
        <div xmlns="http://www.w3.org/1999/xhtml"
          style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            width: '100%', height: '100%',
            color: isDefault ? 'rgba(148,163,184,0.7)' : 'var(--text-primary, #f1f5f9)',
            fontSize: expression.length > 15 ? '10px' : expression.length > 10 ? '11px' : '13px',
            overflow: 'hidden',
          }}
          dangerouslySetInnerHTML={{ __html: latexHtml }}
        />
      </foreignObject>
      <g className="bd-gain-edit-hint" transform={`translate(${flipped ? -hw + 10 : hw - 10}, -${hh + 4})`}>
        <rect x={-10} y={-10} width={20} height={20} rx={5} className="bd-gain-hint-bg" />
        <text x={0} y={1} textAnchor="middle" dominantBaseline="middle" className="bd-gain-hint-icon">&#9998;</text>
      </g>
      <circle
        cx={-PORT_DIST} cy={0} r={PORT_RADIUS}
        className={`bd-port ${flipped ? 'bd-port-output' : 'bd-port-input'}`}
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 0, x - PORT_DIST, y, 'left'); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 0); }}
      />
      <circle
        cx={PORT_DIST} cy={0} r={PORT_RADIUS}
        className={`bd-port ${flipped ? 'bd-port-input' : 'bd-port-output'}`}
        onMouseDown={(e) => { e.stopPropagation(); onPortMouseDown(e, block.id, 'any', 1, x + PORT_DIST, y, 'right'); }}
        onMouseUp={(e) => { e.stopPropagation(); onPortMouseUp(e, block.id, 'any', 1); }}
      />
    </g>
  );
}

function JunctionBlock({ block, isSelected, onMouseDown, onPortMouseDown, onPortMouseUp, connections = [] }) {
  const { x, y } = block.position;
  const r = BLOCK_SIZES.junction.radius;
  const d = GRID_SIZE;
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
// Wire Components
// ============================================================================

function Wire({ precomputedRoute, crossings, isNew, isSelected, onWireClick, onWireMouseDown, onWireDoubleClick }) {
  if (!precomputedRoute) return null;
  // Build path with bridge arcs at crossing points
  const d = (crossings && crossings.length > 0)
    ? buildPathWithBridges(precomputedRoute, crossings)
    : pointsToPath(precomputedRoute);
  // Hit area always uses simple path (no arcs) for reliable click detection
  const hitD = pointsToPath(precomputedRoute);

  return (
    <g className={`bd-wire-group ${isNew ? 'bd-wire-new' : ''} ${isSelected ? 'bd-wire-selected' : ''}`}>
      <path d={hitD} className="bd-wire-hit" onClick={onWireClick} onMouseDown={onWireMouseDown} onDoubleClick={onWireDoubleClick} />
      <path d={d} className="bd-wire" markerEnd="url(#arrowhead)" />
    </g>
  );
}

function WireInProgress({ startPos, mousePos }) {
  if (!startPos || !mousePos) return null;
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

  // Set explicit pixel dimensions — SVG rendered as <img> ignores width="100%"
  clone.setAttribute('width', CANVAS_WIDTH);
  clone.setAttribute('height', CANVAS_HEIGHT);
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');

  // Resolve all CSS variables used in the document into concrete values,
  // then collect all .bd-* CSS rules and embed them as a <style> block.
  // This is far more robust than walking the DOM tree to inline styles.
  const rootStyle = getComputedStyle(document.documentElement);
  const resolveVar = (value) => {
    // Replace var(--name, fallback) with resolved value or fallback
    return value.replace(/var\(\s*(--[^,)]+)(?:\s*,\s*([^)]+))?\s*\)/g, (_, varName, fallback) => {
      const resolved = rootStyle.getPropertyValue(varName).trim();
      return resolved || (fallback ? fallback.trim() : '');
    });
  };

  // Extract all .bd-* rules from stylesheets
  let cssText = '';
  for (const sheet of document.styleSheets) {
    try {
      for (const rule of sheet.cssRules) {
        if (rule.selectorText && rule.selectorText.includes('.bd-')) {
          // Resolve CSS variables in the rule text
          cssText += resolveVar(rule.cssText) + '\n';
        }
      }
    } catch (e) {
      // Cross-origin stylesheets can't be read — skip
    }
  }

  // Inject <style> into the SVG clone's <defs>
  const styleEl = document.createElementNS('http://www.w3.org/2000/svg', 'style');
  styleEl.textContent = cssText;
  const defs = clone.querySelector('defs');
  if (defs) {
    defs.insertBefore(styleEl, defs.firstChild);
  } else {
    clone.insertBefore(styleEl, clone.firstChild);
  }

  // Also resolve CSS variables in inline attributes (marker fill, pattern stroke)
  clone.querySelectorAll('marker polygon').forEach(m => {
    const fill = m.getAttribute('fill');
    if (fill && fill.includes('var(')) m.setAttribute('fill', resolveVar(fill));
  });
  clone.querySelectorAll('pattern line').forEach(l => {
    const stroke = l.getAttribute('stroke');
    if (stroke && stroke.includes('var(')) l.setAttribute('stroke', resolveVar(stroke));
  });

  const serializer = new XMLSerializer();
  const svgString = serializer.serializeToString(clone);
  const canvas = document.createElement('canvas');
  const scale = 2;
  canvas.width = CANVAS_WIDTH * scale;
  canvas.height = CANVAS_HEIGHT * scale;
  const ctx = canvas.getContext('2d');
  const img = new Image();
  img.onload = () => {
    ctx.fillStyle = rootStyle.getPropertyValue('--background-color').trim() || '#0a0e27';
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
  // Custom TF editing state
  const [tfDialogOpen, setTfDialogOpen] = useState(false);
  const [tfDialogBlockId, setTfDialogBlockId] = useState(null);
  const [tfDialogValue, setTfDialogValue] = useState('');
  const [tfDialogLabel, setTfDialogLabel] = useState('');
  const [tfDialogError, setTfDialogError] = useState('');
  const [selectedTfBlock, setSelectedTfBlock] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);
  // Drag-and-drop from toolbar
  const [dragOver, setDragOver] = useState(false);
  // View mode: 'block' (traditional block diagram) or 'sfg' (Mason's Signal Flow Graph)
  const [viewMode, setViewMode] = useState('block');
  const panStart = useRef({ x: 0, y: 0, ox: 0, oy: 0 });

  const svgRef = useRef(null);
  const dragOffset = useRef({ x: 0, y: 0 });
  const presetRef = useRef(null);
  const draggingRef = useRef(null);
  const blocksRef = useRef(blocks);

  // Undo/Redo stacks
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

  // Clear animations
  useEffect(() => {
    if (newWireIndex !== null) {
      const timer = setTimeout(() => setNewWireIndex(null), 600);
      return () => clearTimeout(timer);
    }
  }, [newWireIndex]);

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
  // Backend API calls
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
    if (viewMode === 'sfg') return;
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
  }, [blocks, getSvgCoords, viewMode]);

  const handleSvgMouseMove = useCallback((e) => {
    const { x: svgX, y: svgY } = getSvgCoords(e.clientX, e.clientY);
    if (dragging) {
      const rawX = svgX - dragOffset.current.x;
      const rawY = svgY - dragOffset.current.y;
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
    if (viewMode === 'sfg') return;
    if (wireStart) return;
    // Don't start a wire from a port already used as input (has incoming wire)
    if (connections.some(c => c.to_block === blockId && c.to_port === portIndex)) return;
    setWireStart({ blockId, portIndex, x: portX, y: portY, dir: portDir || 'right' });
  }, [viewMode, wireStart, connections]);

  const handlePortMouseUp = useCallback((e, blockId, portType, portIndex) => {
    e.preventDefault();
    e.stopPropagation();
    if (viewMode === 'sfg') return;
    if (wireStart && wireStart.blockId !== blockId) {
      const targetBlock = blocks[blockId];
      const targetPos = targetBlock ? getPortPosition(targetBlock, 'input', portIndex) : null;
      const sourceBlock = blocks[wireStart.blockId];
      if (wireStart.blockId === blockId) {
        if (targetPos) setConnectionFlash({ position: targetPos, success: false });
        setWireStart(null); return;
      }
      // Don't drop a wire on a port already used as output (has outgoing wire)
      if (connections.some(c => c.from_block === blockId && c.from_port === portIndex)) {
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
      if (sourceBlock?.type === 'output' || targetBlock?.type === 'input') {
        if (targetPos) setConnectionFlash({ position: targetPos, success: false });
        setWireStart(null); return;
      }
      // Enforce max incoming wire limits per block type (fan-out is unlimited)
      const tgtLimits = MAX_WIRES[targetBlock?.type];
      if (tgtLimits && connections.filter(c => c.to_block === blockId).length >= tgtLimits.in) {
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
  }, [viewMode, wireStart, mutatingAction, blocks, connections]);

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
    if ((e.key === 'Delete' || e.key === 'Backspace') && !gainEditBlock && !tfDialogOpen && !isTyping && viewMode !== 'sfg') {
      e.preventDefault();
      if (selectedWire !== null) {
        mutatingAction('remove_connection', { conn_index: selectedWire });
        setSelectedWire(null);
      } else if (selectedBlock) {
        mutatingAction('remove_block', { block_id: selectedBlock });
        setSelectedBlock(null);
      }
    }
  }, [selectedBlock, selectedWire, gainEditBlock, tfDialogOpen, mutatingAction, handleUndo, handleRedo, viewMode]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Toggle adder sign
  const handleToggleSign = useCallback((blockId, portIndex) => {
    mutatingAction('toggle_adder_sign', { block_id: blockId, port_index: portIndex });
  }, [mutatingAction]);

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
      if (!isNaN(val)) mutatingAction('update_block_value', { block_id: gainEditBlock, value: val });
      setGainEditBlock(null);
    }
  }, [gainEditBlock, gainEditValue, mutatingAction]);

  // Custom TF editing
  const handleTfDoubleClick = useCallback((blockId) => {
    const block = blocks[blockId];
    if (block?.type === 'custom_tf') {
      setTfDialogBlockId(blockId);
      setTfDialogValue(block.expression || '1');
      setTfDialogLabel(block.label || '');
      setTfDialogError('');
      setTfDialogOpen(true);
      setSelectedBlock(blockId);
      setSelectedTfBlock(blockId);
    }
  }, [blocks]);

  const handleTfDialogSubmit = useCallback(async () => {
    if (!tfDialogBlockId || !tfDialogValue.trim()) return;
    setTfDialogError('');
    saveUndoSnapshot();
    setIsLoading(true);
    try {
      const result = await api.executeSimulation(simId, 'update_block_value', {
        block_id: tfDialogBlockId, value: tfDialogValue.trim(),
        ...(tfDialogLabel.trim() && { label: tfDialogLabel.trim() }),
      });
      if (result.success && result.data) {
        const meta = result.data.metadata || result.metadata;
        if (meta) {
          // Check if backend returned an error (parse failure)
          if (meta.error) {
            setTfDialogError(meta.error);
            return; // keep dialog open
          }
          if (meta.blocks !== undefined) setBlocks(meta.blocks);
          if (meta.connections !== undefined) setConnections(meta.connections);
          if (meta.transfer_function !== undefined) setTfResult(meta.transfer_function);
          if (meta.error !== undefined) setError(meta.error);
          if (onMetadataChange) onMetadataChange(meta);
        }
        setTfDialogOpen(false);
        setTfDialogBlockId(null);
      } else if (result.error) {
        setTfDialogError(result.error);
      }
    } catch (err) {
      setTfDialogError(err?.message || 'Invalid transfer function expression');
    } finally {
      setIsLoading(false);
    }
  }, [tfDialogBlockId, tfDialogValue, tfDialogLabel, simId, saveUndoSnapshot, onMetadataChange]);

  const handleTfDialogCancel = useCallback(() => {
    setTfDialogOpen(false);
    setTfDialogBlockId(null);
    setTfDialogError('');
  }, []);

  // Custom TF blocks on canvas (for management panel)
  const customTfBlocks = useMemo(
    () => Object.values(blocks).filter(b => b.type === 'custom_tf'),
    [blocks]
  );

  // Clear stale selectedTfBlock when its block is deleted
  useEffect(() => {
    if (selectedTfBlock && !blocks[selectedTfBlock]) {
      setSelectedTfBlock(null);
    }
  }, [blocks, selectedTfBlock]);

  // Drag-and-drop: convert screen coords to SVG coords
  const screenToSvg = useCallback((clientX, clientY) => {
    const svg = svgRef.current;
    if (!svg) return { x: CANVAS_WIDTH / 2, y: CANVAS_HEIGHT / 2 };
    const pt = svg.createSVGPoint();
    pt.x = clientX;
    pt.y = clientY;
    const ctm = svg.getScreenCTM();
    if (!ctm) return { x: CANVAS_WIDTH / 2, y: CANVAS_HEIGHT / 2 };
    const svgPt = pt.matrixTransform(ctm.inverse());
    return { x: svgPt.x, y: svgPt.y };
  }, []);

  // Mode/system type
  const handleModeChange = useCallback((newMode) => {
    setMode(newMode);
    callAction('set_mode', { mode: newMode });
    // Reset UI state on mode switch
    setSelectedBlock(null); setSelectedWire(null);
    setGainEditBlock(null); setTfDialogOpen(false);
    setError(null); setZoom(1.0); setPanOffset({ x: 0, y: 0 });
    if (onParamChange) onParamChange('mode', newMode);
  }, [callAction, onParamChange]);

  const handleSystemTypeChange = useCallback((newType) => {
    setSystemType(newType);
    callAction('set_system_type', { system_type: newType });
    setBlocks({}); setConnections([]); setSelectedBlock(null); setSelectedWire(null);
    setTfResult(null); setError(null); setZoom(1.0); setPanOffset({ x: 0, y: 0 });
    setViewMode('block'); setGainEditBlock(null); setTfDialogOpen(false); setTfInput('');
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

  // ========================================================================
  // Computed rendering data (the new clean pipeline)
  // Must be before wire interaction handlers that reference adderPortMap
  // ========================================================================

  // 1. Signal flow analysis — per-block LTR/RTL
  const blockFlowDir = useMemo(
    () => analyzeSignalFlow(blocks, connections),
    [blocks, connections]
  );

  // 2. Dynamic adder port positions
  const adderPortMap = useMemo(
    () => computeAdderPorts(blocks, connections),
    [blocks, connections]
  );

  // 3. Signal Flow Graph — derived visualization
  const sfgGraph = useMemo(() => {
    if (viewMode !== 'sfg') return null;
    return convertToSFG(blocks, connections, systemType);
  }, [viewMode, blocks, connections, systemType]);

  // Pre-compute SFG helpers: node map + parallel edge offsets
  const { sfgNodesMap, sfgEdgeOffsets } = useMemo(() => {
    if (!sfgGraph) return { sfgNodesMap: {}, sfgEdgeOffsets: [] };
    const nMap = {};
    for (const n of sfgGraph.nodes) nMap[n.id] = n;
    // Count parallel edges between same node pairs for offset
    // Use directed key so A→B and B→A are treated as separate groups
    const pairCount = {};
    const offsets = sfgGraph.edges.map((edge) => {
      const key = `${edge.from}→${edge.to}`;
      pairCount[key] = (pairCount[key] || 0);
      const offset = pairCount[key];
      pairCount[key]++;
      return offset;
    });
    return { sfgNodesMap: nMap, sfgEdgeOffsets: offsets };
  }, [sfgGraph]);

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
    const startPos = getPortPosition(sourceBlock, 'output', conn.from_port, null, adderPortMap);
    const endPos = getPortPosition(targetBlock, 'input', conn.to_port, null, adderPortMap);
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
  }, [connections, blocks, getSvgCoords, adderPortMap]);

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

  // 3. Branch points for multi-target ports
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

      // Optimal branch point: minimize total distance to all branch targets
      const branchTargetPorts = [];
      for (let i = 1; i < indices.length; i++) {
        const bConn = connections[indices[i]];
        const bTarget = blocks[bConn.to_block];
        if (bTarget) {
          branchTargetPorts.push(getPortPosition(bTarget, 'input', bConn.to_port, blockFlowDir, adderPortMap));
        }
      }

      // Sample candidate points along the main wire
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
      if (candidates.length > 0 && branchTargetPorts.length > 0) {
        let bestScore = Infinity;
        for (const cand of candidates) {
          let totalDist = 0;
          for (const tp of branchTargetPorts) {
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

  // 4. Centralized wire routing — route wires sequentially so each wire
  //    avoids previously-routed wire paths (prevents overlapping wires)
  //    Also detects wire crossings and returns a per-wire crossing map.
  const { wireRoutes, wireCrossingMap } = useMemo(() => {
    const WIRE_PAD = 20; // 20px exclusion zone — nearly one grid cell spacing between parallel wires
    const routes = [];
    const wireZoneBlocks = []; // Fake blocks representing previously-routed wire segments

    // Group connections by source port — sibling wires (same source port) must NOT
    // block each other because branch wires start ON the parent wire's path
    const siblingSet = {};
    const portGroups = {};
    connections.forEach((conn, idx) => {
      const key = `${conn.from_block}:${conn.from_port}`;
      if (!portGroups[key]) portGroups[key] = [];
      portGroups[key].push(idx);
    });
    Object.values(portGroups).forEach(indices => {
      for (const idx of indices) {
        siblingSet[idx] = new Set(indices);
      }
    });

    for (let i = 0; i < connections.length; i++) {
      const conn = connections[i];
      const fromBlock = blocks[conn.from_block];
      const toBlock = blocks[conn.to_block];
      if (!fromBlock || !toBlock) { routes.push(null); continue; }

      const portStart = getPortPosition(fromBlock, 'output', conn.from_port, blockFlowDir, adderPortMap);
      const endPos = getPortPosition(toBlock, 'input', conn.to_port, blockFlowDir, adderPortMap);
      const bp = autoBranchMap[i];
      const startPos = bp ? { x: bp.x, y: bp.y, dir: bp.dir || portStart.dir } : portStart;

      // Build augmented blocks dict: real blocks + wire zone obstacles
      // Skip zones from sibling wires (same source port) to avoid blocking branch points
      const allBlocks = { ...blocks };
      const mySiblings = siblingSet[i] || new Set();
      for (const wzb of wireZoneBlocks) {
        const wireIdx = parseInt(wzb.id.split('_')[2]);
        if (mySiblings.has(wireIdx)) continue;
        allBlocks[wzb.id] = wzb;
      }

      const points = routeWire(startPos, endPos, allBlocks, [conn.from_block, conn.to_block]);
      routes.push(points);

      // Convert this wire's segments into thin zone-blocks for future wires to avoid
      if (points && points.length >= 2) {
        for (let s = 0; s < points.length - 1; s++) {
          const [x1, y1] = points[s];
          const [x2, y2] = points[s + 1];
          const segLen = Math.abs(x2 - x1) + Math.abs(y2 - y1);
          if (segLen < GRID_SIZE) continue; // Skip tiny segments (stubs near ports)
          wireZoneBlocks.push({
            id: `_wz_${i}_${s}`,
            type: '_wire_zone',
            position: { x: (x1 + x2) / 2, y: (y1 + y2) / 2 },
            _bounds: {
              left: Math.min(x1, x2) - WIRE_PAD,
              right: Math.max(x1, x2) + WIRE_PAD,
              top: Math.min(y1, y2) - WIRE_PAD,
              bottom: Math.max(y1, y2) + WIRE_PAD,
            },
          });
        }
      }
    }

    // Post-process: detect wire crossings and build per-wire crossing map
    const crossingMap = detectWireCrossings(routes, siblingSet);

    return { wireRoutes: routes, wireCrossingMap: crossingMap };
  }, [connections, blocks, blockFlowDir, adderPortMap, autoBranchMap]);

  // Available block types
  const availableBlocks = useMemo(() => {
    const base = ['input', 'output', 'gain', 'adder'];
    if (systemType === 'dt') base.push('delay');
    else base.push('integrator');
    base.push('custom_tf');
    return base;
  }, [systemType]);

  const blockLabels = {
    input: 'Input', output: 'Output', gain: 'Gain',
    adder: 'Adder', delay: 'Delay', integrator: 'Integ', junction: 'Junct',
    custom_tf: 'Custom TF',
  };

  const blockIcons = {
    input: '\u2192', output: '\u2190', gain: '\u25B7',
    adder: '\u2295', delay: '\u25FB', integrator: '\u222B', junction: '\u25CF',
    custom_tf: '\u0192',  // ƒ
  };

  // Gain edit position — only recompute when editing a gain block or view changes
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gainEditBlock, zoom, panOffset]);

  // Export handlers
  const handleExportSVG = useCallback(() => exportSVG(svgRef.current), []);
  const handleExportPNG = useCallback(() => exportPNG(svgRef.current), []);
  const handleExportJSON = useCallback(() => {
    const diagramData = JSON.stringify({
      blocks,
      connections,
      system_type: systemType,
    });
    try {
      localStorage.setItem('sfs_diagram', diagramData);
      navigator.clipboard.writeText(diagramData).catch(() => {});
      setToastMessage('Diagram exported — open Signal Flow Scope to import');
      setTimeout(() => setToastMessage(null), 3000);
    } catch (e) {
      // localStorage might be full
      setToastMessage('Export failed');
      setTimeout(() => setToastMessage(null), 2000);
    }
  }, [blocks, connections, systemType]);

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
            <button key={type} className="bd-palette-btn"
              draggable="true"
              onDragStart={(e) => { e.dataTransfer.setData('block-type', type); e.dataTransfer.effectAllowed = 'copy'; }}
              onClick={() => handleAddBlock(type)}
              title={`Add ${blockLabels[type] || type} block — click or drag onto canvas`}
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
            <button className={`bd-toggle-btn ${mode === 'build' ? 'active' : ''}`} onClick={() => handleModeChange('build')} aria-pressed={mode === 'build'} aria-label="Build mode">Build</button>
            <button className={`bd-toggle-btn ${mode === 'parse' ? 'active' : ''}`} onClick={() => handleModeChange('parse')} aria-pressed={mode === 'parse'} aria-label="Parse transfer function mode">Parse TF</button>
          </div>
        </div>

        <div className="bd-toolbar-section">
          <span className="bd-toolbar-label">Type</span>
          <div className="bd-toggle-group">
            <button className={`bd-toggle-btn ${systemType === 'dt' ? 'active' : ''}`} onClick={() => handleSystemTypeChange('dt')} aria-pressed={systemType === 'dt'} aria-label="Discrete-time system">DT</button>
            <button className={`bd-toggle-btn ${systemType === 'ct' ? 'active' : ''}`} onClick={() => handleSystemTypeChange('ct')} aria-pressed={systemType === 'ct'} aria-label="Continuous-time system">CT</button>
          </div>
        </div>

        <div className="bd-toolbar-section">
          <span className="bd-toolbar-label">View</span>
          <div className="bd-toggle-group">
            <button className={`bd-toggle-btn ${viewMode === 'block' ? 'active' : ''}`} onClick={() => { setViewMode('block'); setZoom(1.0); setPanOffset({ x: 0, y: 0 }); setSelectedBlock(null); setSelectedWire(null); }} aria-pressed={viewMode === 'block'} aria-label="Block diagram view">Diagram</button>
            <button className={`bd-toggle-btn ${viewMode === 'sfg' ? 'active' : ''}`} onClick={() => { setViewMode('sfg'); setZoom(1.0); setPanOffset({ x: 0, y: 0 }); setSelectedBlock(null); setSelectedWire(null); }} aria-pressed={viewMode === 'sfg'} aria-label="Signal flow graph view">SFG</button>
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
          <button className="bd-action-btn bd-clear-btn" onClick={handleClear}>
            <span className="bd-btn-icon">&times;</span> Clear
          </button>
          <div className="bd-preset-dropdown" ref={presetRef}>
            <button className={`bd-action-btn bd-preset-toggle ${presetOpen ? 'open' : ''}`} onClick={() => setPresetOpen(!presetOpen)} aria-expanded={presetOpen} aria-haspopup="true" aria-label="Load preset diagram">
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
          <button className="bd-action-btn" onClick={handleExportJSON} title="Export diagram for Signal Flow Scope">Export to Signal Scope</button>
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

      {/* Custom TF Management Panel */}
      {customTfBlocks.length > 0 && mode === 'build' && (
        <div className="bd-tf-panel">
          <span className="bd-tf-panel-label">Transfer Functions</span>
          <select
            className="bd-tf-panel-select"
            value={selectedTfBlock || ''}
            onChange={(e) => {
              const bid = e.target.value || null;
              setSelectedTfBlock(bid);
              if (bid) setSelectedBlock(bid);
            }}
          >
            <option value="">Select a block...</option>
            {customTfBlocks.map(b => (
              <option key={b.id} value={b.id}>
                {b.label || b.id}: {b.expression || '1'}
                {b.converted_from ? ` (${b.converted_from}→R)` : ''}
              </option>
            ))}
          </select>
          <button
            className="bd-tf-panel-edit-btn"
            disabled={!selectedTfBlock}
            onClick={() => { if (selectedTfBlock) handleTfDoubleClick(selectedTfBlock); }}
          >
            Edit
          </button>
        </div>
      )}

      <div className="bd-main-area">
        <div
          className={`bd-canvas-container ${dragOver ? 'bd-canvas-dragover' : ''}`}
          onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'copy'; }}
          onDragEnter={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={(e) => {
            // Only clear if leaving the container (not entering a child)
            if (!e.currentTarget.contains(e.relatedTarget)) setDragOver(false);
          }}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            const blockType = e.dataTransfer.getData('block-type');
            if (!blockType) return;
            const svgPt = screenToSvg(e.clientX, e.clientY);
            const snappedX = snapToGrid(svgPt.x);
            const snappedY = snapToGrid(svgPt.y);
            mutatingAction('add_block', { block_type: blockType, position: { x: snappedX, y: snappedY } });
          }}
        >
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
              {/* SFG arrowheads */}
              <marker id="sfg-arrow-forward" markerWidth="10" markerHeight="8" refX="10" refY="4" orient="auto">
                <polygon points="0 0, 10 4, 0 8" fill="var(--accent-color, #00d9ff)" opacity="0.85" />
              </marker>
              <marker id="sfg-arrow-feedback" markerWidth="10" markerHeight="8" refX="10" refY="4" orient="auto">
                <polygon points="0 0, 10 4, 0 8" fill="var(--warning-color, #f59e0b)" opacity="0.85" />
              </marker>
              {/* SFG node glow filter */}
              <filter id="sfgNodeGlow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            <rect x={visibleRect.x} y={visibleRect.y} width={visibleRect.width} height={visibleRect.height} fill="url(#grid)" className="bd-grid-bg" />

            {viewMode === 'block' ? (
              <>
                {/* Blocked Airspace zones — faint exclusion boundaries */}
                {Object.values(blocks).map(block => {
                  const bounds = getBlockBounds(block, COLLISION_PAD);
                  return (
                    <rect
                      key={`airspace-${block.id}`}
                      x={bounds.left} y={bounds.top}
                      width={bounds.right - bounds.left}
                      height={bounds.bottom - bounds.top}
                      fill="rgba(239, 68, 68, 0.03)"
                      stroke="rgba(239, 68, 68, 0.12)"
                      strokeWidth="0.75"
                      strokeDasharray="4 3"
                      rx={4}
                      pointerEvents="none"
                    />
                  );
                })}

                {/* Wires */}
                {connections.map((conn, i) => (
                  <Wire
                    key={`${conn.from_block}-${conn.to_block}-${conn.to_port}-${i}`}
                    precomputedRoute={wireRoutes[i]}
                    crossings={wireCrossingMap[i]}
                    isNew={i === newWireIndex} isSelected={i === selectedWire}
                    onWireClick={(e) => handleWireClick(e, i)}
                    onWireMouseDown={(e) => handleWireMouseDown(e, i)}
                    onWireDoubleClick={(e) => handleWireBranch(e, i)}
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
                    case 'adder':
                      return <AdderBlock key={block.id} {...commonProps} onToggleSign={handleToggleSign} dynamicPorts={adderPortMap[block.id]} />;
                    case 'delay':
                      return <DelayBlock key={block.id} {...commonProps} flowDir={flowDir} />;
                    case 'integrator':
                      return <IntegratorBlock key={block.id} {...commonProps} flowDir={flowDir} />;
                    case 'junction':
                      return <JunctionBlock key={block.id} {...commonProps} connections={connections} />;
                    case 'custom_tf':
                      return <CustomTfBlock key={block.id} {...commonProps} flowDir={flowDir} onTfDoubleClick={handleTfDoubleClick} systemType={systemType} />;
                    default: return null;
                  }
                })}
              </>
            ) : (
              <>
                {/* Signal Flow Graph view */}
                {sfgGraph && sfgGraph.edges.map((edge, i) => (
                  <SFGEdge key={`sfg-e-${i}`} edge={edge} nodesMap={sfgNodesMap} edgeIndex={i} parallelOffset={sfgEdgeOffsets[i]} allNodes={sfgGraph.nodes} />
                ))}
                {sfgGraph && sfgGraph.nodes.map(node => (
                  <SFGNode key={`sfg-n-${node.id}`} node={node} />
                ))}
                {(!sfgGraph || sfgGraph.nodes.length === 0) && (
                  <text x={CANVAS_WIDTH / 2} y={CANVAS_HEIGHT / 2} textAnchor="middle" dominantBaseline="central" className="sfg-empty-hint" fill="var(--text-muted, #64748b)" fontSize="16" fontFamily="Inter, sans-serif">
                    No diagram to convert — add blocks in Diagram view
                  </text>
                )}
              </>
            )}
          </svg>

          {/* Gain/constant edit overlay (hidden in SFG mode) */}
          {viewMode === 'block' && gainEditBlock && blocks[gainEditBlock] && gainEditPos && (
            <div className="bd-gain-edit-overlay" style={{ left: `${gainEditPos.left}px`, top: `${gainEditPos.top}px` }}>
              <label className="bd-gain-edit-label">Gain value</label>
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
          {Object.keys(blocks).length === 0 && mode === 'build' && viewMode === 'block' && (
            <div className="bd-instructions-overlay">
              <div className="bd-instructions-icon">&#9881;</div>
              <p className="bd-instructions-title">Block Diagram Builder</p>
              <p>Click a block type above to add it, or load a preset.</p>
              <p>Drag from ports to connect blocks. Double-click gain blocks to edit values.</p>
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

      {/* Custom TF Edit Dialog */}
      {tfDialogOpen && (
        <div className="bd-tf-dialog-overlay" onClick={handleTfDialogCancel}>
          <div className="bd-tf-dialog" onClick={(e) => e.stopPropagation()}>
            <h3 className="bd-tf-dialog-title">
              Edit Transfer Function {tfDialogBlockId && <span className="bd-tf-dialog-block-id">({tfDialogBlockId})</span>}
            </h3>
            <div className="bd-tf-dialog-field">
              <label className="bd-tf-dialog-field-label">Label</label>
              <input
                className="bd-tf-dialog-input bd-tf-dialog-label-input"
                value={tfDialogLabel}
                onChange={(e) => setTfDialogLabel(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleTfDialogSubmit();
                  if (e.key === 'Escape') handleTfDialogCancel();
                }}
                placeholder={systemType === 'dt' ? 'e.g. G(z), Plant, Controller' : 'e.g. G(s), Plant, Controller'}
                maxLength={30}
              />
            </div>
            <div className="bd-tf-dialog-field">
              <label className="bd-tf-dialog-field-label">Expression</label>
              <div className="bd-tf-dialog-preview">
                {(() => {
                  try {
                    const latex = tfExprToLatex(tfDialogValue || '1', systemType);
                    return <span dangerouslySetInnerHTML={{ __html: katex.renderToString(latex, { throwOnError: false, displayMode: true }) }} />;
                  } catch {
                    return <span style={{ color: 'var(--text-muted)' }}>Preview unavailable</span>;
                  }
                })()}
              </div>
              <input
                className="bd-tf-dialog-input"
                value={tfDialogValue}
                onChange={(e) => { setTfDialogValue(e.target.value); setTfDialogError(''); }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleTfDialogSubmit();
                  if (e.key === 'Escape') handleTfDialogCancel();
                }}
                placeholder={systemType === 'dt' ? 'e.g. (1+2R)/(1-0.5R) or 1/(s+1)' : 'e.g. (s+1)/(s^2+2s+1)'}
                autoFocus
              />
              {systemType === 'dt' && /(?<![a-zA-Z])s(?![a-zA-Z])/.test(tfDialogValue) && (
                <div className="bd-tf-dialog-hint">
                  s-domain detected — will auto-convert to R-domain (discrete-time)
                </div>
              )}
              {systemType === 'dt' && /(?<![a-zA-Z])z(?![a-zA-Z])/i.test(tfDialogValue) && (
                <div className="bd-tf-dialog-hint">
                  z-domain detected — will auto-convert to R-domain
                </div>
              )}
            </div>
            {tfDialogError && <div className="bd-tf-dialog-error">{tfDialogError}</div>}
            <div className="bd-tf-dialog-actions">
              <button className="bd-tf-dialog-btn bd-tf-dialog-cancel" onClick={handleTfDialogCancel}>Cancel</button>
              <button className="bd-tf-dialog-btn bd-tf-dialog-apply" onClick={handleTfDialogSubmit}>Apply</button>
            </div>
          </div>
        </div>
      )}
      {toastMessage && (
        <div className="bd-toast" style={{
          position: 'absolute', bottom: '20px', left: '50%', transform: 'translateX(-50%)',
          background: 'var(--surface-color, #131b2e)', border: '1px solid var(--primary-color, #14b8a6)',
          borderRadius: 'var(--radius-md, 8px)', padding: '8px 16px',
          color: 'var(--text-primary, #f1f5f9)', fontSize: '13px', zIndex: 100,
          boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
        }}>
          {toastMessage}
        </div>
      )}
    </div>
  );
}

export default BlockDiagramViewer;
