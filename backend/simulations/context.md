# Block Diagram Builder — Wire Routing & Layout Context

## Problem Overview

The block diagram builder generates direct-form realizations of transfer functions. The main issues are:
1. **Wire routing** — wires take inefficient paths, cut through blocks, or create massive detours
2. **Auto-arrange** — feedback blocks get scattered instead of forming clean rows below the forward path
3. **Adder fixed ports** — adder blocks have hardcoded port positions that create forced wire angles

## Current Architecture

### Files
- **Frontend**: `frontend/src/components/BlockDiagramViewer.jsx` — SVG rendering, A* wire routing, port positions
- **Backend**: `backend/simulations/block_diagram_builder.py` — diagram generation, auto-arrange, TF parsing
- **CSS**: `frontend/src/styles/BlockDiagramViewer.css` — visual styling

### Port System
Every block type has fixed port positions relative to its center:
- **Gain/Delay/Integrator**: port 0 = left (input, dir='left'), port 1 = right (output, dir='right')
- **Adder**: port 0 = left (input, dir='left'), port 1 = bottom (input, dir='down'), port 2 = right (output, dir='right')
- **Input**: single port on right (dir='right')
- **Output**: single port on left (dir='left')

Port positions defined in `getPortPosition()` (~line 392) and `PORT_OFFSETS` (~line 60) in BlockDiagramViewer.jsx.

### Wire Routing System
Located in `routeWire()` (~line 125) of BlockDiagramViewer.jsx.

Uses A* pathfinding with 5 strategies:
- **Strategies 1-3**: Use port's natural direction + strict obstacles (COLLISION_PAD=48)
- **Strategies 4-5**: Use adaptive direction (computed from relative positions) + relaxed obstacles (RELAXED_PAD=12) + no initial direction penalty

Key constants:
- `GRID_SIZE = 24` — all coordinates snap to 24px grid
- `COLLISION_PAD = 48` — obstacle inflation for strict routing
- `RELAXED_PAD = 12` — obstacle inflation for adaptive routing (allows passing between blocks)
- `PORT_OFFSETS = 48` — port distance from block center
- `BLOCK_SIZES`: most blocks 80x60, adders radius=30

A* cost function (in `astar()` ~line 240):
- Same-direction continuation: 0.75x cost (prefer straight)
- Turn: 1.3x cost
- Right/down preference: 0.95x
- Initial turn against port direction: 3.0x penalty (skipped when `penalizeInitial=false`)

### Auto-Arrange Algorithm
Located in `_action_auto_arrange()` (~line 606) of block_diagram_builder.py.

Algorithm:
1. Detect back-edges via DFS
2. Build acyclic graph (remove back-edges)
3. Find forward path via bidirectional BFS (input→output AND output→input on acyclic graph)
4. Topological sort forward blocks, place left-to-right at y=360 with H_GAP=192
5. Trace feedback chains from entry points (feedback blocks receiving from forward blocks)
6. Layout feedback chains RIGHT-to-LEFT starting from entry_x, at y=576
7. Overlap resolution: push right within same row
8. Center diagram

### RTL Feedback Convention
In direct-form realizations, feedback blocks use **reversed port semantics**:
- Delay/integrator port 1 (right) = INPUT (receives from forward path or previous delay)
- Delay/integrator port 0 (left) = OUTPUT (sends to next delay or gain)
- Gain port 1 (right) = INPUT, port 0 (left) = OUTPUT

This means feedback wires flow RIGHT-to-LEFT. The frontend detects this via port-based analysis and swaps port positions accordingly.

## What Has Been Fixed

### Auto-Arrange (backend)
- **Forward path identification**: BFS from input→output on acyclic graph. Everything on an acyclic path = forward, rest = feedback.
- **Feedback chain tracing**: Directed traversal from entry points (blocks receiving from forward path), laid out RTL.
- **Clean row separation**: Forward at y=360, feedback at y=576+.

### Wire Routing (frontend)
- **Adaptive direction strategies (4-5)**: Compute optimal start/end direction from source→target vector instead of using port's fixed direction. Prevents massive detours where port faces LEFT but target is RIGHT.
- **Two-tier obstacle system**: Strict obstacles (pad=48) for strategies 1-3, relaxed (pad=12) for 4-5. Allows feedback wires to pass through gaps between blocks.
- **No block exclusions**: Source/target blocks are NOT excluded from obstacles. Instead, port corridors (3 bypass cells in port direction) allow A* to reach ports without routing through block bodies.
- **Optional initial penalty**: `penalizeInitial` parameter on `astar()`. Adaptive strategies skip the 3x penalty for initial turn against port direction.

### Block Visual Orientation (frontend) — NEWLY FIXED
- **Port-based RTL detection** (`blockFlowDir` useMemo): Detects RTL blocks by checking port usage pattern:
  - Input on port 1 + output on port 0 → RTL (feedback path convention)
  - Input on port 0 + output on port 1 → LTR (standard forward path)
  - Replaces previous buggy spatial position check that failed for feedback gains connecting to adders to the right
- **Port position swapping** (`getPortPosition()`): Accepts `flowDirMap` and `adderPortMap` parameters. When `flowDirMap[blockId] === 'rtl'`, port 0 and port 1 positions/directions are swapped for gain/delay/integrator blocks.
- **Visual block flipping**: GainBlock, DelayBlock, IntegratorBlock components swap port circle positions when `flowDir='rtl'`. Port CSS classes also swap (bd-port-input ↔ bd-port-output).
- **Wire component updated**: Passes `flowDirMap` and `adderPortMap` to `getPortPosition()` so wires connect to the correct swapped port positions.

### Dynamic Adder Ports (frontend) — NEWLY FIXED
- **`adderPortMap` useMemo**: Computes optimal port positions for each adder based on angle to connected blocks:
  - For each connection to/from the adder, compute angle to the connected block
  - Assign each port to the closest available cardinal direction (left/right/up/down)
  - Output port gets priority in direction assignment
  - Falls back to default positions (left, bottom, right) when no connections exist
- **AdderBlock component**: Accepts `dynamicPorts` prop with `{portIndex: {dx, dy, dir}}` entries. Renders ports at dynamic positions. Sign labels positioned relative to each port.
- **getPortPosition for adders**: Uses `adderPortMap` when available, falls back to fixed positions.

### Hook Ordering
The useMemo hooks are ordered by dependency:
1. `adderPortMap` — depends on blocks, connections
2. `blockFlowDir` — depends on blocks, connections
3. `branchPoints` — depends on connections, blocks, blockFlowDir, adderPortMap (calls getPortPosition)

## What Remains To Fix

### 1. Wire-Block Collision Post-Check
**Problem**: Even with the corridor system, some edge cases still allow wires to pass very close to blocks (within the relaxed obstacle zone).

**Possible fix**: After all wires are routed, check each wire segment against all block bounds. If overlap detected, re-route that specific wire with stricter constraints.

### 2. Wire Channel System
**Problem**: Multiple feedback wires at similar y-coordinates can overlap or run parallel too closely.

**Ideal solution**: Designate specific y-coordinates as "wire channels" between the forward and feedback rows. Assign each wire to a different channel to prevent overlap.

### 3. Numerator Feedback Gain Orientation
**Problem**: Numerator feedback gains (e.g., gain(13.26) in `(-13.26*s^2+0.1667)/(s^3+9.5*s)`) use standard LTR port convention (input=port0, output=port1) even though they're in the feedback path. This is because the backend generates them with LTR ports. They display as LTR which is technically correct for their port wiring but may not match textbook convention where all feedback blocks face RTL.

**Possible fix**: Backend could annotate blocks with `flow_direction: 'rtl'` metadata, OR frontend could detect feedback row membership (y > forward row y) as an additional RTL signal.

## Key Debugging Tips

### Testing auto-arrange
```python
from simulations.block_diagram_builder import BlockDiagramSimulator
s = BlockDiagramSimulator('t')
s.initialize()
s.system_type = 'ct'
s.parameters['system_type'] = 'ct'
s.handle_action('parse_tf', {'tf_string': '(-13.26*s^2 + 0.1667) / (s^3 + 9.5*s)'})
state = s.handle_action('auto_arrange', {})
blocks = state['metadata']['blocks']
for bid, b in sorted(blocks.items(), key=lambda t: t[1]['position']['x']):
    print(f"{b['type']:12s} x={b['position']['x']:7.0f} y={b['position']['y']:6.0f}")
```

### Testing wire paths (browser console)
```javascript
document.querySelectorAll('.bd-wire').forEach((w, i) => {
  console.log('W' + i + ': ' + w.getAttribute('d'));
});
```

### Problem transfer functions for testing
- 3rd order: `(-13.26*s^2 + 0.1667) / (s^3 + 9.5*s)` — tests feedback return wires
- 4th order: `(s^4 + 2) / (s^4 + 7*s^3 + 3*s^2 - 45*s)` — tests complex multi-chain feedback
- 1st order: `1/(s+1)` — simple baseline
- DT presets: `accumulator`, `first_order_dt`, `second_order_dt`

### Build and verify
```bash
cd frontend && npx vite build  # must succeed
cd backend && python -m uvicorn main:app --reload --port 8000
cd frontend && npm run dev
```
