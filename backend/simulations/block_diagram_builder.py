"""
Block Diagram Builder Simulator

Interactive block diagram builder supporting two modes:
1. Build Mode: User constructs block diagrams → system computes transfer function
2. Parse Mode: User enters transfer function → system generates block diagram

Block types (from MIT 6.003 Lectures 2-4):
- Gain: multiplies signal by a constant
- Adder: sums inputs with configurable +/- signs
- Delay (R): unit delay for discrete-time systems
- Integrator (A): integration for continuous-time systems
- Input/Output: signal source and sink

Uses Mason's gain formula for cyclic (feedback) graphs and
direct cascade for acyclic graphs.
"""

import copy
import numpy as np
from collections import deque
from itertools import combinations
from typing import Any, Dict, List, Optional, Tuple
from .base_simulator import BaseSimulator
import re
import uuid


class BlockDiagramSimulator(BaseSimulator):
    """
    Block Diagram Builder — Simulink-like interactive block diagram tool.

    Supports both discrete-time (DT) and continuous-time (CT) systems.
    DT uses Delay (R operator, z^-1), CT uses Integrator (A operator, 1/s).
    """

    # Block type definitions with port configurations
    BLOCK_TYPES = {
        "input": {"inputs": 0, "outputs": 1, "label": "x[n]", "label_ct": "x(t)"},
        "output": {"inputs": 1, "outputs": 0, "label": "y[n]", "label_ct": "y(t)"},
        "gain": {"inputs": 1, "outputs": 1, "default_value": 2.0},
        "adder": {"inputs": 2, "outputs": 1, "max_inputs": 2},
        "delay": {"inputs": 1, "outputs": 1, "label": "R", "system": "dt"},
        "integrator": {"inputs": 1, "outputs": 1, "label": "∫", "system": "ct"},
        "junction": {"inputs": 1, "outputs": 8, "label": ""},
    }

    # Preset diagrams
    PRESETS = {
        "accumulator": {
            "name": "Accumulator",
            "equation": "y[n] = y[n-1] + x[n]",
            "system_type": "dt",
        },
        "difference": {
            "name": "Difference Machine",
            "equation": "y[n] = x[n] - x[n-1]",
            "system_type": "dt",
        },
        "first_order_dt": {
            "name": "First-Order DT",
            "equation": "y[n] = x[n] + 0.5·y[n-1]",
            "system_type": "dt",
        },
        "second_order_dt": {
            "name": "Second-Order DT",
            "equation": "y[n] = x[n] + 1.6·y[n-1] - 0.63·y[n-2]",
            "system_type": "dt",
        },
        "first_order_ct": {
            "name": "First-Order CT",
            "equation": "dy/dt = -a·y + x(t)",
            "system_type": "ct",
        },
    }

    # Plot colors
    COLORS = {
        "step": "#3b82f6",
        "impulse": "#ef4444",
        "grid": "rgba(148, 163, 184, 0.15)",
        "text": "#e2e8f0",
        "zero": "rgba(148, 163, 184, 0.3)",
    }

    PARAMETER_SCHEMA = {
        "system_type": {
            "type": "select",
            "label": "System Type",
            "options": [
                {"label": "Discrete-Time (DT)", "value": "dt"},
                {"label": "Continuous-Time (CT)", "value": "ct"},
            ],
            "default": "dt",
        },
        "mode": {
            "type": "select",
            "label": "Mode",
            "options": [
                {"label": "Build Diagram → TF", "value": "build"},
                {"label": "Enter TF → Diagram", "value": "parse"},
            ],
            "default": "build",
        },
    }

    DEFAULT_PARAMS = {
        "system_type": "dt",
        "mode": "build",
    }

    def __init__(self, simulation_id: str):
        """Initialize block diagram simulator."""
        super().__init__(simulation_id)
        self.blocks: Dict[str, Dict[str, Any]] = {}
        self.connections: List[Dict[str, Any]] = []
        self.mode = "build"
        self.system_type = "dt"
        self.tf_input = ""
        self._tf_result: Optional[Dict[str, Any]] = None
        self._error: Optional[str] = None
        self._next_block_id = 0
        self._history: deque = deque(maxlen=30)
        self._redo_history: deque = deque(maxlen=30)

    def _gen_block_id(self) -> str:
        """Generate unique block ID."""
        self._next_block_id += 1
        return f"block_{self._next_block_id}"

    def _save_history(self) -> None:
        """Save current state to history stack for undo."""
        self._history.append((
            copy.deepcopy(self.blocks),
            copy.deepcopy(self.connections),
            self._next_block_id,
        ))
        # deque(maxlen=30) auto-evicts oldest entries
        # Clear redo on new action
        self._redo_history.clear()

    def _max_port_index(self, block_type: str, block_id: str = None) -> int:
        """Maximum valid port index for a given block type."""
        if block_type == "junction":
            # Dynamic: max used port + 1, minimum 1
            if block_id and hasattr(self, 'connections'):
                used = [c["from_port"] for c in self.connections if c["from_block"] == block_id]
                return max(used + [1]) + 1
            return 8
        if block_type == "adder":
            return 2   # ports 0=left, 1=bottom, 2=right
        if block_type in ("gain", "delay", "integrator"):
            return 1   # ports 0=left, 1=right
        return 0       # input/output: single port (index 0)

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        """Initialize with default or given parameters."""
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        self.system_type = self.parameters.get("system_type", "dt")
        self.mode = self.parameters.get("mode", "build")
        self.blocks = {}
        self.connections = []
        self.tf_input = ""
        self._tf_result = None
        self._error = None
        self._next_block_id = 0
        self._initialized = True

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        """Update a parameter (system_type or mode)."""
        if name in self.parameters:
            sanitized = self._validate_param(name, value)
            self.parameters[name] = sanitized
        else:
            sanitized = value

        if name == "system_type":
            self.system_type = sanitized
            # Recompute TF when switching system type
            self._recompute_tf()
        elif name == "mode":
            self.mode = sanitized

        return self.get_state()

    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle custom block diagram actions.

        Dispatches to the appropriate method based on action name.
        """
        action_map = {
            "add_block": self._action_add_block,
            "remove_block": self._action_remove_block,
            "move_block": self._action_move_block,
            "update_block_value": self._action_update_block_value,
            "add_connection": self._action_add_connection,
            "remove_connection": self._action_remove_connection,
            "toggle_adder_sign": self._action_toggle_adder_sign,
            "compute_tf": self._action_compute_tf,
            "parse_tf": self._action_parse_tf,
            "set_mode": self._action_set_mode,
            "set_system_type": self._action_set_system_type,
            "clear": self._action_clear,
            "load_preset": self._action_load_preset,
            "undo": self._action_undo,
            "redo": self._action_redo,
            "split_wire": self._action_split_wire,
            "auto_arrange": self._action_auto_arrange,
        }

        handler = action_map.get(action)
        if handler is None:
            self._error = f"Unknown action: {action}"
            return self.get_state()

        try:
            self._error = None
            handler(params)
        except Exception as e:
            self._error = str(e)

        return self.get_state()

    # =========================================================================
    # Action handlers
    # =========================================================================

    def _action_add_block(self, params: Dict[str, Any]) -> None:
        """Add a new block to the diagram."""
        if len(self.blocks) >= 30:
            raise ValueError("Maximum 30 blocks allowed.")
        self._save_history()
        block_type = params.get("block_type", "gain")
        position = params.get("position", {"x": 408, "y": 240})
        value = params.get("value")

        if block_type not in self.BLOCK_TYPES:
            raise ValueError(f"Unknown block type: {block_type}")

        # Check system-specific blocks
        type_def = self.BLOCK_TYPES[block_type]
        if "system" in type_def and type_def["system"] != self.system_type:
            other = "integrator" if block_type == "delay" else "delay"
            raise ValueError(
                f"Block '{block_type}' is not available in "
                f"{'CT' if self.system_type == 'ct' else 'DT'} mode. "
                f"Use '{other}' instead."
            )

        block_id = self._gen_block_id()

        block = {
            "id": block_id,
            "type": block_type,
            "position": {"x": float(position.get("x", 400)), "y": float(position.get("y", 250))},
        }

        # Set default value for gain blocks
        if block_type == "gain":
            raw_val = float(value) if value is not None else type_def.get("default_value", 1.0)
            if not np.isfinite(raw_val):
                raise ValueError("Gain value must be a finite number.")
            block["value"] = raw_val
        elif block_type == "adder":
            # Signs for each input port: default both positive
            block["signs"] = params.get("signs", ["+", "+", "+"])

        self.blocks[block_id] = block
        self._recompute_tf()

    def _action_remove_block(self, params: Dict[str, Any]) -> None:
        """Remove a block and all its connections."""
        self._save_history()
        block_id = params.get("block_id")
        if block_id not in self.blocks:
            raise ValueError(f"Block not found: {block_id}")

        del self.blocks[block_id]
        # Remove all connections involving this block
        self.connections = [
            c for c in self.connections
            if c["from_block"] != block_id and c["to_block"] != block_id
        ]
        self._recompute_tf()

    def _action_move_block(self, params: Dict[str, Any]) -> None:
        """Move a block to a new position."""
        block_id = params.get("block_id")
        position = params.get("position", {})
        if block_id not in self.blocks:
            raise ValueError(f"Block not found: {block_id}")
        self.blocks[block_id]["position"] = {
            "x": float(position.get("x", 0)),
            "y": float(position.get("y", 0)),
        }
        # No TF recomputation needed — position is visual only

    def _action_update_block_value(self, params: Dict[str, Any]) -> None:
        """Update a block's value (e.g., gain)."""
        self._save_history()
        block_id = params.get("block_id")
        value = params.get("value")
        if block_id not in self.blocks:
            raise ValueError(f"Block not found: {block_id}")
        block = self.blocks[block_id]
        if block["type"] == "gain":
            val = float(value)
            if not np.isfinite(val):
                raise ValueError("Gain value must be a finite number.")
            block["value"] = val
        self._recompute_tf()

    def _action_add_connection(self, params: Dict[str, Any]) -> None:
        """Add a connection (wire) between two blocks with full validation."""
        from_block = params.get("from_block")
        from_port = params.get("from_port", 0)
        to_block = params.get("to_block")
        to_port = params.get("to_port", 0)

        # --- Basic existence checks ---
        if from_block not in self.blocks:
            raise ValueError(f"Source block not found: {from_block}")
        if to_block not in self.blocks:
            raise ValueError(f"Target block not found: {to_block}")

        from_block_data = self.blocks[from_block]
        to_block_data = self.blocks[to_block]

        # --- 1. Self-connection prevention ---
        if from_block == to_block:
            raise ValueError("Cannot connect a block to itself")

        # --- 2. Port index validation for ALL block types ---
        from_port = int(from_port)
        to_port = int(to_port)
        max_from = self._max_port_index(from_block_data["type"], from_block)
        max_to = self._max_port_index(to_block_data["type"], to_block)
        if from_port < 0 or from_port > max_from:
            raise ValueError(
                f"Invalid source port {from_port} for {from_block_data['type']} "
                f"(valid: 0–{max_from})"
            )
        if to_port < 0 or to_port > max_to:
            raise ValueError(
                f"Invalid target port {to_port} for {to_block_data['type']} "
                f"(valid: 0–{max_to})"
            )

        # --- 3. Role enforcement ---
        # Output blocks have no outgoing signals — they are sinks
        if from_block_data["type"] == "output":
            raise ValueError("Output blocks cannot be wire sources")
        # Input blocks have no incoming signals — they are sources
        if to_block_data["type"] == "input":
            raise ValueError("Input blocks cannot be wire targets")

        # --- 3b. Max wire enforcement based on block type definitions ---
        from_type_def = self.BLOCK_TYPES.get(from_block_data["type"], {})
        max_outgoing = from_type_def.get("outputs", 1)
        # Junctions are fan-out nodes — no outgoing limit
        outgoing_count = sum(1 for c in self.connections if c["from_block"] == from_block)
        if from_block_data["type"] != "junction" and outgoing_count >= max_outgoing:
            raise ValueError(
                f"{from_block_data['type'].capitalize()} block already has "
                f"the maximum {max_outgoing} outgoing connection(s)"
            )

        to_type_def = self.BLOCK_TYPES.get(to_block_data["type"], {})
        max_incoming = to_type_def.get("inputs", 1)
        incoming_count = sum(1 for c in self.connections if c["to_block"] == to_block)
        if incoming_count >= max_incoming:
            raise ValueError(
                f"{to_block_data['type'].capitalize()} block already has "
                f"the maximum {max_incoming} incoming connection(s)"
            )

        # --- 4. Exact duplicate prevention ---
        for conn in self.connections:
            if (conn["from_block"] == from_block and
                    conn["from_port"] == from_port and
                    conn["to_block"] == to_block and
                    conn["to_port"] == to_port):
                raise ValueError("This exact connection already exists")

        # --- 5. Reverse connection prevention (same port pair) ---
        for conn in self.connections:
            if (conn["from_block"] == to_block and conn["from_port"] == to_port and
                    conn["to_block"] == from_block and conn["to_port"] == from_port):
                raise ValueError(
                    f"A reverse connection already exists on the same ports "
                    f"({to_block}:{to_port} -> {from_block}:{from_port})"
                )

        # --- 5b. Port role collapse (bidirectional → locked) ---
        # Once a port is used as output (from_port), it cannot also be an input,
        # and vice versa. This enforces "collapse" semantics for bidirectional ports.
        for conn in self.connections:
            if conn["from_block"] == to_block and conn["from_port"] == to_port:
                raise ValueError(
                    f"Port {to_port} on block {to_block} is already used as an "
                    "output and cannot also be used as an input"
                )
            if conn["to_block"] == from_block and conn["to_port"] == from_port:
                raise ValueError(
                    f"Port {from_port} on block {from_block} is already used as an "
                    "input and cannot also be used as an output"
                )

        # --- 6. Input port already occupied ---
        # Each port can only receive one incoming wire
        for conn in self.connections:
            if conn["to_block"] == to_block and conn["to_port"] == to_port:
                raise ValueError(
                    f"Input port {to_port} on {to_block} is already connected"
                )

        self._save_history()
        connection = {
            "from_block": from_block,
            "from_port": from_port,
            "to_block": to_block,
            "to_port": to_port,
        }
        # Store visual branch point if provided (for rendering branch wires)
        branch_point = params.get("branch_point")
        if branch_point and isinstance(branch_point, dict):
            connection["branch_point"] = {
                "x": branch_point.get("x", 0),
                "y": branch_point.get("y", 0),
                "dir": branch_point.get("dir", "right"),
            }
        self.connections.append(connection)
        self._recompute_tf()

    def _action_remove_connection(self, params: Dict[str, Any]) -> None:
        """Remove a connection by index or by from/to specification."""
        self._save_history()
        conn_index = params.get("conn_index")
        if conn_index is not None:
            idx = int(conn_index)
            if 0 <= idx < len(self.connections):
                self.connections.pop(idx)
            else:
                raise ValueError(f"Connection index out of range: {idx}")
        else:
            # Remove by from/to block
            from_block = params.get("from_block")
            to_block = params.get("to_block")
            to_port = params.get("to_port", 0)
            self.connections = [
                c for c in self.connections
                if not (c["from_block"] == from_block and
                        c["to_block"] == to_block and
                        c["to_port"] == to_port)
            ]
        self._recompute_tf()

    def _action_toggle_adder_sign(self, params: Dict[str, Any]) -> None:
        """Toggle the sign (+/-) on an adder input port."""
        self._save_history()
        block_id = params.get("block_id")
        port_index = int(params.get("port_index", 0))
        if block_id not in self.blocks:
            raise ValueError(f"Block not found: {block_id}")
        block = self.blocks[block_id]
        if block["type"] != "adder":
            raise ValueError("Can only toggle sign on adder blocks")
        if port_index >= 3:
            raise ValueError("Adder only has 3 ports (index 0, 1, and 2)")
        signs = block.get("signs", ["+", "+", "+"])
        # Ensure exactly 3 signs
        while len(signs) < 3:
            signs.append("+")
        signs = signs[:3]
        signs[port_index] = "-" if signs[port_index] == "+" else "+"
        block["signs"] = signs
        self._recompute_tf()

    def _action_compute_tf(self, params: Dict[str, Any]) -> None:
        """Explicitly compute the transfer function."""
        self._recompute_tf()

    def _action_parse_tf(self, params: Dict[str, Any]) -> None:
        """Parse a transfer function string and generate block diagram."""
        self._save_history()
        tf_string = params.get("tf_string", "")
        self.tf_input = tf_string
        self._parse_transfer_function(tf_string)
        # NOTE: Do NOT call _action_auto_arrange here — _parse_transfer_function
        # already produces a carefully aligned layout where feedback delays sit
        # directly below their target adders.  The generic auto-arrange algorithm
        # doesn't understand this alignment and would scatter the feedback row.

    def _action_set_mode(self, params: Dict[str, Any]) -> None:
        """Switch between build and parse mode."""
        mode = params.get("mode", "build")
        if mode not in ("build", "parse"):
            raise ValueError(f"Invalid mode: {mode}")
        self.mode = mode
        self.parameters["mode"] = mode

    def _action_set_system_type(self, params: Dict[str, Any]) -> None:
        """Switch between DT and CT. Clears the diagram since block types differ."""
        self._save_history()
        system_type = params.get("system_type", "dt")
        if system_type not in ("dt", "ct"):
            raise ValueError(f"Invalid system type: {system_type}")
        self.system_type = system_type
        self.parameters["system_type"] = system_type
        # Clear diagram — delay blocks are invalid in CT, integrators in DT
        self.blocks = {}
        self.connections = []
        self._tf_result = None
        self._error = None
        self._next_block_id = 0

    def _action_clear(self, params: Dict[str, Any]) -> None:
        """Clear all blocks and connections."""
        self._save_history()
        self.blocks = {}
        self.connections = []
        self._tf_result = None
        self._error = None
        self._next_block_id = 0
        self.tf_input = ""

    def _action_load_preset(self, params: Dict[str, Any]) -> None:
        """Load a preset diagram."""
        self._save_history()
        preset_name = params.get("preset", "accumulator")
        if preset_name not in self.PRESETS:
            raise ValueError(f"Unknown preset: {preset_name}")

        preset = self.PRESETS[preset_name]
        self.system_type = preset["system_type"]
        self.parameters["system_type"] = preset["system_type"]

        # Clear current diagram
        self.blocks = {}
        self.connections = []
        self._next_block_id = 0

        # Build preset diagram
        if preset_name == "accumulator":
            self._build_accumulator_preset()
        elif preset_name == "difference":
            self._build_difference_preset()
        elif preset_name == "first_order_dt":
            self._build_first_order_dt_preset()
        elif preset_name == "second_order_dt":
            self._build_second_order_dt_preset()
        elif preset_name == "first_order_ct":
            self._build_first_order_ct_preset()

        self._fix_port_directions()
        self._center_diagram()
        self._recompute_tf()

    def _action_undo(self, params: Dict[str, Any]) -> None:
        """Undo the last mutating action by restoring previous state."""
        if not self._history:
            raise ValueError("Nothing to undo")
        # Save current state to redo stack
        self._redo_history.append((
            copy.deepcopy(self.blocks),
            copy.deepcopy(self.connections),
            self._next_block_id,
        ))
        blocks, connections, next_id = self._history.pop()
        self.blocks = blocks
        self.connections = connections
        self._next_block_id = next_id
        self._recompute_tf()

    def _action_redo(self, params: Dict[str, Any]) -> None:
        """Redo a previously undone action."""
        if not self._redo_history:
            raise ValueError("Nothing to redo")
        # Save current state to undo stack (without clearing redo)
        self._history.append((
            copy.deepcopy(self.blocks),
            copy.deepcopy(self.connections),
            self._next_block_id,
        ))
        blocks, connections, next_id = self._redo_history.pop()
        self.blocks = blocks
        self.connections = connections
        self._next_block_id = next_id
        self._recompute_tf()

    def _action_split_wire(self, params: Dict[str, Any]) -> None:
        """Split a wire by inserting a junction node at the given position.

        Takes conn_index (which wire to split) and position {x, y}.
        Removes the original A→B connection and creates:
          A → junction(port 0)  and  junction(port 1) → B
        The user can then draw more wires from the junction's output ports.
        """
        self._save_history()
        conn_index = params.get("conn_index")
        position = params.get("position", {})

        if conn_index is None or conn_index < 0 or conn_index >= len(self.connections):
            raise ValueError(f"Invalid connection index: {conn_index}")

        conn = self.connections[conn_index]
        from_block = conn["from_block"]
        from_port = conn["from_port"]
        to_block = conn["to_block"]
        to_port = conn["to_port"]

        # Create junction block at the specified position
        junc_id = self._gen_block_id()
        self.blocks[junc_id] = {
            "id": junc_id,
            "type": "junction",
            "position": {
                "x": position.get("x", 400),
                "y": position.get("y", 300),
            },
        }

        # Remove original connection
        self.connections.pop(conn_index)

        # Create two new connections: A → junction(port 0), junction(port 1) → B
        self.connections.append({
            "from_block": from_block,
            "from_port": from_port,
            "to_block": junc_id,
            "to_port": 0,
        })
        self.connections.append({
            "from_block": junc_id,
            "from_port": 1,
            "to_block": to_block,
            "to_port": to_port,
        })

        self._recompute_tf()

    def _action_auto_arrange(self, params: Dict[str, Any]) -> None:
        """Auto-arrange using chain-traced layout.

        1. Forward path: BFS input→output, laid out left→right
        2. Feedback: trace chains from forward-path entry points, lay out below
           mirroring forward path structure
        """
        if not self.blocks:
            return
        self._save_history()

        GRID = 24
        H_GAP = 240
        MAIN_Y = 408
        FB_Y = 648

        block_ids = list(self.blocks.keys())
        if not block_ids:
            return

        # --- Build full adjacency ---
        outgoing = {bid: set() for bid in block_ids}
        incoming = {bid: set() for bid in block_ids}
        for conn in self.connections:
            fb, tb = conn["from_block"], conn["to_block"]
            if fb in self.blocks and tb in self.blocks:
                outgoing[fb].add(tb)
                incoming[tb].add(fb)

        # --- Detect back-edges via iterative DFS ---
        back_edges = set()
        visited = set()
        rec_stack = set()
        dfs_stack = []

        input_ids = [b for b in block_ids if self.blocks[b]["type"] == "input"]
        output_ids = [b for b in block_ids if self.blocks[b]["type"] == "output"]

        for start in input_ids + [b for b in block_ids if b not in input_ids]:
            if start in visited:
                continue
            dfs_stack = [(start, iter(outgoing.get(start, set())))]
            visited.add(start)
            rec_stack.add(start)
            while dfs_stack:
                node, children = dfs_stack[-1]
                try:
                    child = next(children)
                    if child in rec_stack:
                        back_edges.add((node, child))
                    elif child not in visited:
                        visited.add(child)
                        rec_stack.add(child)
                        dfs_stack.append((child, iter(outgoing.get(child, set()))))
                except StopIteration:
                    rec_stack.discard(node)
                    dfs_stack.pop()

        # --- Build acyclic graph ---
        acyclic_out = {bid: set() for bid in block_ids}
        acyclic_in = {bid: set() for bid in block_ids}
        for conn in self.connections:
            fb, tb = conn["from_block"], conn["to_block"]
            if fb in self.blocks and tb in self.blocks and (fb, tb) not in back_edges:
                acyclic_out[fb].add(tb)
                acyclic_in[tb].add(fb)

        # --- Find forward path: blocks on ANY acyclic path from input to output ---
        fwd_from_input = set(input_ids)
        q = deque(input_ids)
        while q:
            n = q.popleft()
            for nb in acyclic_out.get(n, set()):
                if nb not in fwd_from_input:
                    fwd_from_input.add(nb)
                    q.append(nb)

        bwd_from_output = set(output_ids)
        q = deque(output_ids)
        while q:
            n = q.popleft()
            for nb in acyclic_in.get(n, set()):
                if nb not in bwd_from_output:
                    bwd_from_output.add(nb)
                    q.append(nb)

        forward_set = fwd_from_input & bwd_from_output
        feedback_set = set(block_ids) - forward_set

        # --- Topological sort + level assignment for forward blocks ---
        fw_in_deg = {b: 0 for b in forward_set}
        fw_out = {b: set() for b in forward_set}
        for conn in self.connections:
            fb, tb = conn["from_block"], conn["to_block"]
            if fb in forward_set and tb in forward_set and (fb, tb) not in back_edges:
                fw_out[fb].add(tb)
                fw_in_deg[tb] += 1

        q = deque(sorted([b for b in forward_set if fw_in_deg[b] == 0],
                         key=lambda b: (0 if self.blocks[b]["type"] == "input" else 1, b)))
        fw_topo = []
        while q:
            n = q.popleft()
            fw_topo.append(n)
            for nb in fw_out.get(n, set()):
                fw_in_deg[nb] -= 1
                if fw_in_deg[nb] == 0:
                    q.append(nb)
        for b in forward_set:
            if b not in fw_topo:
                fw_topo.append(b)

        fw_level = {}
        for bid in fw_topo:
            mx = -1
            for pred in acyclic_in.get(bid, set()):
                if pred in fw_level:
                    mx = max(mx, fw_level[pred])
            fw_level[bid] = mx + 1

        # --- Position forward blocks ---
        fw_x = {}
        start_x = 216
        by_level = {}
        for bid in fw_topo:
            lv = fw_level[bid]
            by_level.setdefault(lv, []).append(bid)

        for lv in sorted(by_level.keys()):
            bids = by_level[lv]
            x = round((start_x + lv * H_GAP) / GRID) * GRID
            for i, bid in enumerate(bids):
                y_off = (i - len(bids) // 2) * 192
                y = round((MAIN_Y + y_off) / GRID) * GRID
                self.blocks[bid]["position"] = {"x": float(x), "y": float(y)}
                fw_x[bid] = x

        # --- Trace feedback chains using DIRECTED traversal, lay out RIGHT-to-LEFT ---
        fb_positioned = set()

        # Build directed adjacency within feedback set
        fb_outgoing = {bid: [] for bid in feedback_set}
        fb_incoming = {bid: [] for bid in feedback_set}
        for conn in self.connections:
            fb, tb = conn["from_block"], conn["to_block"]
            if fb in feedback_set and tb in feedback_set:
                fb_outgoing[fb].append(tb)
                fb_incoming[tb].append(fb)

        # Find chain ENTRY points: feedback blocks that RECEIVE from a forward block
        # These are the start of each feedback chain (signal enters feedback here)
        entry_points = []
        for bid in feedback_set:
            for conn in self.connections:
                if conn["to_block"] == bid and conn["from_block"] in fw_x:
                    # This block receives from forward path — it's an entry
                    entry_x = fw_x[conn["from_block"]]
                    entry_points.append((bid, entry_x))
                    break

        # Sort: rightmost entry first (output-side feedback chains first)
        entry_points.sort(key=lambda t: -t[1])

        # Trace each chain in signal-flow order and lay out RIGHT → LEFT
        row_idx = 0
        for entry_bid, entry_x in entry_points:
            if entry_bid in fb_positioned:
                continue

            # Follow outgoing connections to build ordered chain
            chain = []
            current = entry_bid
            visited_chain = set()
            while current and current not in visited_chain and current in feedback_set:
                visited_chain.add(current)
                chain.append(current)
                fb_positioned.add(current)
                # Follow outgoing within feedback set
                nexts = [n for n in fb_outgoing.get(current, []) if n not in visited_chain and n in feedback_set]
                current = nexts[0] if nexts else None

            if not chain:
                continue

            # Layout: entry block at rightmost x (near forward block it connects from)
            # Each subsequent block goes H_GAP to the LEFT
            chain_y = round((FB_Y + row_idx * 216) / GRID) * GRID
            for i, bid in enumerate(chain):
                x = round((entry_x - i * H_GAP) / GRID) * GRID
                self.blocks[bid]["position"] = {"x": float(x), "y": float(chain_y)}
            row_idx += 1

        # Any remaining unpositioned feedback blocks — place below
        remaining_fb = [b for b in feedback_set if b not in fb_positioned]
        if remaining_fb:
            remaining_y = round((FB_Y + row_idx * 216) / GRID) * GRID
            for i, bid in enumerate(remaining_fb):
                x = round((start_x + i * H_GAP) / GRID) * GRID
                self.blocks[bid]["position"] = {"x": float(x), "y": float(remaining_y)}

        # --- Overlap resolution: only push RIGHT within same row ---
        for _pass in range(8):
            moved = False
            blist = sorted(self.blocks.values(), key=lambda b: b["position"]["x"])
            for i in range(len(blist)):
                for j in range(i + 1, len(blist)):
                    bi, bj = blist[i], blist[j]
                    dx = abs(bi["position"]["x"] - bj["position"]["x"])
                    dy = abs(bi["position"]["y"] - bj["position"]["y"])
                    if dx < 192 and dy < 120:
                        # Push right
                        bj["position"]["x"] = round((bi["position"]["x"] + 240) / GRID) * GRID
                        moved = True
            if not moved:
                break

        self._center_diagram()
        self._recompute_tf()

    # =========================================================================
    # Preset builders
    # =========================================================================

    def _build_accumulator_preset(self) -> None:
        """y[n] = y[n-1] + x[n]: input → adder → output, delay feedback.

        Layout for 1400x800 canvas:
          x[n] ──→ (+) ──────────→ y[n]
                    ↑
                   [R◁]   (feedback below, RTL: port 1 in, port 0 out)
        """
        inp = self._gen_block_id()
        self.blocks[inp] = {"id": inp, "type": "input", "position": {"x": 264, "y": 360}}

        adder = self._gen_block_id()
        self.blocks[adder] = {"id": adder, "type": "adder", "position": {"x": 504, "y": 360}, "signs": ["+", "+", "+"]}

        out = self._gen_block_id()
        self.blocks[out] = {"id": out, "type": "output", "position": {"x": 888, "y": 360}}

        delay = self._gen_block_id()
        self.blocks[delay] = {"id": delay, "type": "delay", "position": {"x": 696, "y": 552}}

        self.connections = [
            {"from_block": inp, "from_port": 0, "to_block": adder, "to_port": 0},
            {"from_block": adder, "from_port": 2, "to_block": out, "to_port": 0},
            # Feedback RTL: adder right → delay RIGHT (port 1), delay LEFT (port 0) → adder bottom
            {"from_block": adder, "from_port": 2, "to_block": delay, "to_port": 1},
            {"from_block": delay, "from_port": 0, "to_block": adder, "to_port": 1},
        ]

    def _build_difference_preset(self) -> None:
        """y[n] = x[n] - x[n-1]: input splits to adder and delay→adder.

        Layout for 1400x800 canvas — feedforward (LTR):
          x[n] ─────────→ (+) ──→ y[n]
            |               ↑(-)
            └──→ [R▷] ─────┘   (feedforward below, LTR: port 0 in, port 1 out)
        """
        inp = self._gen_block_id()
        self.blocks[inp] = {"id": inp, "type": "input", "position": {"x": 264, "y": 360}}

        delay = self._gen_block_id()
        self.blocks[delay] = {"id": delay, "type": "delay", "position": {"x": 504, "y": 552}}

        adder = self._gen_block_id()
        self.blocks[adder] = {"id": adder, "type": "adder", "position": {"x": 744, "y": 360}, "signs": ["+", "-", "+"]}

        out = self._gen_block_id()
        self.blocks[out] = {"id": out, "type": "output", "position": {"x": 984, "y": 360}}

        self.connections = [
            {"from_block": inp, "from_port": 0, "to_block": adder, "to_port": 0},
            # Feedforward LTR: input → delay LEFT (port 0), delay RIGHT (port 1) → adder bottom
            {"from_block": inp, "from_port": 0, "to_block": delay, "to_port": 0},
            {"from_block": delay, "from_port": 1, "to_block": adder, "to_port": 1},
            {"from_block": adder, "from_port": 2, "to_block": out, "to_port": 0},
        ]

    def _build_first_order_dt_preset(self) -> None:
        """y[n] = x[n] + 0.5·y[n-1]: adder → output, with delay→gain(0.5) feedback.

        Layout for 1400x800 canvas — feedback RTL:
          x[n] ──→ (+) ─────────────────→ y[n]
                    ↑                       |
                    |                       ↓
                  [0.5◁] ◁──── [◁R] ◁─────┘
        """
        inp = self._gen_block_id()
        self.blocks[inp] = {"id": inp, "type": "input", "position": {"x": 216, "y": 360}}

        adder = self._gen_block_id()
        self.blocks[adder] = {"id": adder, "type": "adder", "position": {"x": 456, "y": 360}, "signs": ["+", "+", "+"]}

        out = self._gen_block_id()
        self.blocks[out] = {"id": out, "type": "output", "position": {"x": 936, "y": 360}}

        delay = self._gen_block_id()
        self.blocks[delay] = {"id": delay, "type": "delay", "position": {"x": 744, "y": 552}}

        gain = self._gen_block_id()
        self.blocks[gain] = {"id": gain, "type": "gain", "position": {"x": 504, "y": 552}, "value": 0.5}

        self.connections = [
            {"from_block": inp, "from_port": 0, "to_block": adder, "to_port": 0},
            {"from_block": adder, "from_port": 2, "to_block": out, "to_port": 0},
            # Feedback RTL: output → delay port 1 (right), delay port 0 (left) → gain port 1 (right), gain port 0 (left) → adder bottom
            {"from_block": adder, "from_port": 2, "to_block": delay, "to_port": 1},
            {"from_block": delay, "from_port": 0, "to_block": gain, "to_port": 1},
            {"from_block": gain, "from_port": 0, "to_block": adder, "to_port": 1},
        ]

    def _build_second_order_dt_preset(self) -> None:
        """y[n] = x[n] + 1.6·y[n-1] - 0.63·y[n-2].

        Layout: gains above delays, each gain directly below its target adder.
        - All feedback blocks use RTL: port 1 (right) = input, port 0 (left) = output
        - Delay chain flows right-to-left (delay1 rightmost, delay2 to its left)
        - Gains between main path and delay row, aligned with their adders

          Forward:  x[n] → [adder1] ────────────── [adder2] → y[n]
                              ↑(-)                    ↑(+)
                           [◁0.63]                 [◁1.60]
                                [◁delay2] ◁── [◁delay1] ◁──┘
        """
        inp = self._gen_block_id()
        self.blocks[inp] = {"id": inp, "type": "input", "position": {"x": 168, "y": 312}}

        adder1 = self._gen_block_id()
        self.blocks[adder1] = {"id": adder1, "type": "adder", "position": {"x": 432, "y": 312}, "signs": ["+", "-", "+"]}

        adder2 = self._gen_block_id()
        self.blocks[adder2] = {"id": adder2, "type": "adder", "position": {"x": 840, "y": 312}, "signs": ["+", "+", "+"]}

        out = self._gen_block_id()
        self.blocks[out] = {"id": out, "type": "output", "position": {"x": 1104, "y": 312}}

        # Gains above delays, directly below their target adders
        gain_a = self._gen_block_id()
        self.blocks[gain_a] = {"id": gain_a, "type": "gain", "position": {"x": 432, "y": 480}, "value": 0.63}

        gain_b = self._gen_block_id()
        self.blocks[gain_b] = {"id": gain_b, "type": "gain", "position": {"x": 840, "y": 480}, "value": 1.6}

        # Delay row (RTL, right-to-left): delay1 near output, delay2 to its left
        delay1 = self._gen_block_id()
        self.blocks[delay1] = {"id": delay1, "type": "delay", "position": {"x": 840, "y": 624}}

        delay2 = self._gen_block_id()
        self.blocks[delay2] = {"id": delay2, "type": "delay", "position": {"x": 600, "y": 624}}

        self.connections = [
            # Forward path
            {"from_block": inp, "from_port": 0, "to_block": adder1, "to_port": 0},
            {"from_block": adder1, "from_port": 2, "to_block": adder2, "to_port": 0},
            {"from_block": adder2, "from_port": 2, "to_block": out, "to_port": 0},
            # Feedback tap RTL: adder2 output → delay1 port 1 (right in)
            {"from_block": adder2, "from_port": 2, "to_block": delay1, "to_port": 1},
            # Delay chain RTL: delay1 port 0 (left out) → delay2 port 1 (right in)
            {"from_block": delay1, "from_port": 0, "to_block": delay2, "to_port": 1},
            # FB1: delay1 → gain_b(1.6) → adder2 bottom (+)
            {"from_block": delay1, "from_port": 0, "to_block": gain_b, "to_port": 1},
            {"from_block": gain_b, "from_port": 0, "to_block": adder2, "to_port": 1},
            # FB2: delay2 → gain_a(0.63) → adder1 bottom (-)
            {"from_block": delay2, "from_port": 0, "to_block": gain_a, "to_port": 1},
            {"from_block": gain_a, "from_port": 0, "to_block": adder1, "to_port": 1},
        ]

    def _build_first_order_ct_preset(self) -> None:
        """dy/dt = -2y + x(t): input → adder → integrator → output, gain(2) feedback.

        Layout for 1400x800 canvas:
          x(t) ──→ (+) ──→ [∫] ──→ y(t)
                    ↑(-)
                   [◁2]              (gain RTL, below)
        """
        inp = self._gen_block_id()
        self.blocks[inp] = {"id": inp, "type": "input", "position": {"x": 216, "y": 360}}

        adder = self._gen_block_id()
        self.blocks[adder] = {"id": adder, "type": "adder", "position": {"x": 456, "y": 360}, "signs": ["+", "-", "+"]}

        integ = self._gen_block_id()
        self.blocks[integ] = {"id": integ, "type": "integrator", "position": {"x": 744, "y": 360}}

        out = self._gen_block_id()
        self.blocks[out] = {"id": out, "type": "output", "position": {"x": 984, "y": 360}}

        gain = self._gen_block_id()
        self.blocks[gain] = {"id": gain, "type": "gain", "position": {"x": 600, "y": 552}, "value": 2.0}

        self.connections = [
            {"from_block": inp, "from_port": 0, "to_block": adder, "to_port": 0},
            {"from_block": adder, "from_port": 2, "to_block": integ, "to_port": 0},
            {"from_block": integ, "from_port": 1, "to_block": out, "to_port": 0},
            # Feedback RTL: integ port 1 (right out) → gain port 1 (right in), gain port 0 (left out) → adder bottom
            {"from_block": integ, "from_port": 1, "to_block": gain, "to_port": 1},
            {"from_block": gain, "from_port": 0, "to_block": adder, "to_port": 1},
        ]

    # =========================================================================
    # Polynomial arithmetic helpers (LOW-POWER-FIRST convention)
    # coeffs[i] = coefficient of R^i, e.g. [1, -0.5] = 1 - 0.5R
    # =========================================================================

    @staticmethod
    def _pmul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """Multiply two polynomials (low-power-first)."""
        return np.convolve(a, b)

    @staticmethod
    def _padd(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """Add two polynomials (low-power-first)."""
        n = max(len(a), len(b))
        result = np.zeros(n)
        result[:len(a)] += a
        result[:len(b)] += b
        return result

    @staticmethod
    def _psub(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """Subtract two polynomials: a - b (low-power-first)."""
        n = max(len(a), len(b))
        result = np.zeros(n)
        result[:len(a)] += a
        result[:len(b)] -= b
        return result

    @staticmethod
    def _pscale(a: np.ndarray, scalar: float) -> np.ndarray:
        """Scale polynomial by scalar."""
        return a * scalar

    # =========================================================================
    # Transfer function computation
    # =========================================================================

    def _recompute_tf(self) -> None:
        """Recompute transfer function from current diagram."""
        if not self.blocks:
            self._tf_result = None
            return

        try:
            self._tf_result = self._compute_transfer_function()
            self._error = None
        except Exception as e:
            self._tf_result = None
            self._error = str(e)

    def _compute_transfer_function(self) -> Dict[str, Any]:
        """
        Compute the transfer function from the block diagram.

        Uses signal flow analysis:
        1. Find input and output blocks
        2. Build adjacency representation
        3. Use Mason's gain formula for general graphs
        """
        input_blocks = [bid for bid, b in self.blocks.items() if b["type"] == "input"]
        output_blocks = [bid for bid, b in self.blocks.items() if b["type"] == "output"]

        if not input_blocks:
            raise ValueError("No input block found. Add an Input block.")
        if not output_blocks:
            raise ValueError("No output block found. Add an Output block.")
        if len(input_blocks) > 1:
            raise ValueError("Multiple input blocks found. Only one is supported.")
        if len(output_blocks) > 1:
            raise ValueError("Multiple output blocks found. Only one is supported.")

        input_id = input_blocks[0]
        output_id = output_blocks[0]

        return self._solve_signal_flow(input_id, output_id)

    def _solve_signal_flow(self, input_id: str, output_id: str) -> Dict[str, Any]:
        """
        Solve the signal flow graph using Mason's gain formula.

        Polynomials use LOW-POWER-FIRST convention:
        coeffs[i] = coefficient of R^i (or A^i).
        E.g., [1, -0.5] represents 1 - 0.5R
        """
        block_ids = list(self.blocks.keys())

        # Build connection maps
        incoming = {bid: [] for bid in block_ids}
        outgoing = {bid: set() for bid in block_ids}
        for conn in self.connections:
            fb, tb = conn["from_block"], conn["to_block"]
            if fb in self.blocks and tb in self.blocks:
                incoming[tb].append({"from": fb, "to_port": conn["to_port"]})
                outgoing[fb].add(tb)
        # Convert outgoing sets to lists for consistent iteration
        outgoing = {bid: list(targets) for bid, targets in outgoing.items()}

        # Check connectivity
        visited = set()
        stack = [input_id]
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            for target in outgoing.get(node, []):
                stack.append(target)

        if output_id not in visited:
            raise ValueError("Output is not reachable from Input. Connect them with wires.")

        # Block transfer function (low-power-first)
        def block_tf(bid: str) -> Tuple[np.ndarray, np.ndarray]:
            """Return (num, den) polynomials for a block."""
            block = self.blocks[bid]
            btype = block["type"]
            if btype == "gain":
                val = block.get("value", 1.0)
                return (np.array([val]), np.array([1.0]))
            elif btype in ("delay", "integrator"):
                # R or A operator: [0, 1] = 0 + 1*R = R
                return (np.array([0.0, 1.0]), np.array([1.0]))
            else:
                # input, output, adder, junction: unity (pass-through)
                return (np.array([1.0]), np.array([1.0]))

        # Find all forward paths and loops
        forward_paths = []
        all_loops = []
        seen_loops: set = set()
        self._dfs_forward_paths(
            input_id, output_id, incoming, outgoing,
            [input_id], set([input_id]), forward_paths
        )
        for start_bid in block_ids:
            self._dfs_loops(
                start_bid, start_bid, outgoing,
                [start_bid], set([start_bid]), all_loops, seen_loops
            )

        if not forward_paths:
            raise ValueError("No forward path from Input to Output found.")

        # ── Algebraic loop detection ──
        # A loop is "algebraic" if it contains NO delay or integrator blocks,
        # meaning it has direct feedthrough (instantaneous feedback).
        algebraic_loops = []
        for loop in all_loops:
            has_memory = any(
                self.blocks[bid]["type"] in ("delay", "integrator")
                for bid in loop if bid in self.blocks
            )
            if not has_memory:
                algebraic_loops.append(loop)

        def compute_path_gain(path: List[str]) -> Tuple[np.ndarray, np.ndarray]:
            """Compute gain along a path as product of block TFs."""
            num = np.array([1.0])
            den = np.array([1.0])
            for i, bid in enumerate(path):
                block = self.blocks[bid]
                # Handle adder sign
                if block["type"] == "adder" and i > 0:
                    prev_bid = path[i - 1]
                    port_idx = 0
                    for conn in self.connections:
                        if conn["from_block"] == prev_bid and conn["to_block"] == bid:
                            port_idx = conn["to_port"]
                            break
                    signs = block.get("signs", ["+", "+", "+"])
                    if port_idx < len(signs) and signs[port_idx] == "-":
                        num = self._pscale(num, -1.0)

                # Multiply by block's transfer function
                if block["type"] not in ("input", "output", "adder", "junction"):
                    bn, bd = block_tf(bid)
                    num = self._pmul(num, bn)
                    den = self._pmul(den, bd)

            return (num, den)

        def compute_loop_gain(loop: List[str]) -> Tuple[np.ndarray, np.ndarray]:
            """Compute gain around a loop."""
            num = np.array([1.0])
            den = np.array([1.0])
            for i, bid in enumerate(loop):
                block = self.blocks[bid]
                if block["type"] == "adder":
                    prev_bid = loop[i - 1] if i > 0 else loop[-1]
                    port_idx = 0
                    for conn in self.connections:
                        if conn["from_block"] == prev_bid and conn["to_block"] == bid:
                            port_idx = conn["to_port"]
                            break
                    signs = block.get("signs", ["+", "+", "+"])
                    if port_idx < len(signs) and signs[port_idx] == "-":
                        num = self._pscale(num, -1.0)

                if block["type"] not in ("input", "output", "adder", "junction"):
                    bn, bd = block_tf(bid)
                    num = self._pmul(num, bn)
                    den = self._pmul(den, bd)

            return (num, den)

        # ── Full Mason's gain formula ──
        # T = Σ(P_k · Δ_k) / Δ
        # Δ = 1 - Σ L_i + Σ L_i·L_j (non-touching pairs) - Σ L_i·L_j·L_k (non-touching triples) + ...
        # Δ_k = graph determinant with all loops touching forward path k removed

        def loops_are_non_touching(loop1: List[str], loop2: List[str]) -> bool:
            """Two loops are non-touching if they share no common nodes."""
            return set(loop1).isdisjoint(set(loop2))

        def compute_delta(loops: List[List[str]]) -> Tuple[np.ndarray, np.ndarray]:
            """Compute graph determinant Δ from a set of loops.
            Δ = 1 - Σ L_i + Σ (non-touching pairs) L_i·L_j - Σ (triples) + ...
            Generalized to all group sizes using itertools.combinations.
            """
            # Start with Δ = 1
            d_num = np.array([1.0])
            d_den = np.array([1.0])

            if not loops:
                return d_num, d_den

            # Precompute loop gains
            loop_gains = [compute_loop_gain(lp) for lp in loops]
            n_loops = len(loop_gains)

            # Precompute loop node sets for fast non-touching checks
            loop_sets = [set(lp) for lp in loops]

            # For k = 1, 2, ..., n_loops: add (-1)^k * sum of products
            # of non-touching k-tuples
            for k in range(1, n_loops + 1):
                # Safety cap for very large diagrams
                if n_loops > 20 and k > 4:
                    break
                sign_positive = (k % 2 == 0)  # k=1: subtract, k=2: add, ...
                found_any = False

                for combo in combinations(range(n_loops), k):
                    # Check all pairs in combo are mutually non-touching
                    all_non_touching = True
                    for ci in range(len(combo)):
                        for cj in range(ci + 1, len(combo)):
                            if not loop_sets[combo[ci]].isdisjoint(loop_sets[combo[cj]]):
                                all_non_touching = False
                                break
                        if not all_non_touching:
                            break

                    if all_non_touching:
                        found_any = True
                        prod_num = np.array([1.0])
                        prod_den = np.array([1.0])
                        for idx in combo:
                            prod_num = self._pmul(prod_num, loop_gains[idx][0])
                            prod_den = self._pmul(prod_den, loop_gains[idx][1])

                        if sign_positive:
                            d_num = self._padd(
                                self._pmul(d_num, prod_den),
                                self._pmul(prod_num, d_den)
                            )
                        else:
                            d_num = self._psub(
                                self._pmul(d_num, prod_den),
                                self._pmul(prod_num, d_den)
                            )
                        d_den = self._pmul(d_den, prod_den)

                # If no non-touching groups of size k exist, no larger groups can either
                if not found_any:
                    break

            return d_num, d_den

        def path_touches_loop(path: List[str], loop: List[str]) -> bool:
            """A forward path touches a loop if they share any node."""
            return not set(path).isdisjoint(set(loop))

        def compute_cofactor(path: List[str], loops: List[List[str]]) -> Tuple[np.ndarray, np.ndarray]:
            """Compute Δ_k — the graph determinant using only loops that don't touch path k."""
            non_touching = [lp for lp in loops if not path_touches_loop(path, lp)]
            return compute_delta(non_touching)

        # Compute full Δ
        delta_num, delta_den = compute_delta(all_loops)

        # Compute numerator: Σ P_k · Δ_k
        total_num = np.array([0.0])
        total_den = np.array([1.0])
        for fp in forward_paths:
            p_n, p_d = compute_path_gain(fp)
            cofactor_num, cofactor_den = compute_cofactor(fp, all_loops)
            # P_k · Δ_k = (p_n · cofactor_num) / (p_d · cofactor_den)
            term_num = self._pmul(p_n, cofactor_num)
            term_den = self._pmul(p_d, cofactor_den)
            # Add to running total
            total_num = self._padd(
                self._pmul(total_num, term_den),
                self._pmul(term_num, total_den)
            )
            total_den = self._pmul(total_den, term_den)

        # TF = (total_num · delta_den) / (total_den · delta_num)
        tf_num = self._pmul(total_num, delta_den)
        tf_den = self._pmul(total_den, delta_num)

        # Clean up trailing near-zero coefficients
        tf_num = self._clean_poly(tf_num)
        tf_den = self._clean_poly(tf_den)

        # Check for degenerate denominator (algebraic loop made Δ ≈ 0)
        if len(tf_den) == 0 or np.all(np.abs(tf_den) < 1e-10):
            raise ValueError(
                "Algebraic loop detected: feedback path has no delay or "
                "integrator, causing a degenerate transfer function. "
                "Add a Delay (DT) or Integrator (CT) block in the feedback path."
            )

        # Check for NaN/Inf in numerator or denominator
        if np.any(~np.isfinite(tf_num)) or np.any(~np.isfinite(tf_den)):
            raise ValueError(
                "Transfer function has invalid coefficients (NaN/Inf). "
                "This is likely caused by an algebraic loop. "
                "Add a Delay (DT) or Integrator (CT) block in the feedback path."
            )

        # Normalize so constant term of denominator is 1 (if nonzero)
        if len(tf_den) > 0 and abs(tf_den[0]) > 1e-12:
            scale = tf_den[0]
            tf_num = tf_num / scale
            tf_den = tf_den / scale

        # Build expression string
        op = "R" if self.system_type == "dt" else "A"
        expression = self._poly_ratio_to_string(tf_num, tf_den, op)

        # Convert to z-domain or s-domain for poles/zeros
        if self.system_type == "dt":
            z_num, z_den = self._operator_to_z(tf_num, tf_den)
            # Normalize so leading coeff of denominator = 1
            if len(z_den) > 0 and abs(z_den[0]) > 1e-12:
                scale = z_den[0]
                z_num = z_num / scale
                z_den = z_den / scale
            domain_expr = self._poly_ratio_to_string(z_num, z_den, "z")
            poles = np.roots(z_den).tolist() if len(z_den) > 1 else []
            zeros = np.roots(z_num).tolist() if len(z_num) > 1 else []
        else:
            s_num, s_den = self._operator_to_s(tf_num, tf_den)
            if len(s_den) > 0 and abs(s_den[0]) > 1e-12:
                scale = s_den[0]
                s_num = s_num / scale
                s_den = s_den / scale
            domain_expr = self._poly_ratio_to_string(s_num, s_den, "s")
            poles = np.roots(s_den).tolist() if len(s_den) > 1 else []
            zeros = np.roots(s_num).tolist() if len(s_num) > 1 else []

        poles_formatted = self._format_roots(poles)
        zeros_formatted = self._format_roots(zeros)

        # Three-state stability classification
        EPS = 1e-6
        if poles:
            if self.system_type == "dt":
                max_mag = max(abs(complex(p)) for p in poles)
                if max_mag < 1.0 - EPS:
                    stability = "stable"
                elif max_mag > 1.0 + EPS:
                    stability = "unstable"
                else:
                    stability = "marginally_stable"
            else:
                max_real = max(complex(p).real for p in poles)
                if max_real < -EPS:
                    stability = "stable"
                elif max_real > EPS:
                    stability = "unstable"
                else:
                    stability = "marginally_stable"
        else:
            stability = "stable"
        is_stable = stability == "stable"

        # LaTeX versions
        latex_expr = self._poly_ratio_to_latex(tf_num, tf_den, op)
        if self.system_type == "dt":
            domain_latex = self._poly_ratio_to_latex(z_num, z_den, "z")
        else:
            domain_latex = self._poly_ratio_to_latex(s_num, s_den, "s")

        return {
            "expression": f"H({op}) = {expression}",
            "domain_expression": domain_expr,
            "latex": f"H({op}) = {latex_expr}",
            "domain_latex": domain_latex,
            "operator": op,
            "numerator": tf_num.tolist(),
            "denominator": tf_den.tolist(),
            "poles": poles_formatted,
            "zeros": zeros_formatted,
            "is_stable": is_stable,
            "stability": stability,
            "num_forward_paths": len(forward_paths),
            "num_loops": len(all_loops),
            "algebraic_loop_warning": (
                "Warning: algebraic loop detected (feedback without delay/integrator). "
                "Results may be approximate. Add a Delay or Integrator in the feedback path."
            ) if algebraic_loops else None,
        }

    def _dfs_forward_paths(
        self, current: str, target: str,
        incoming: Dict, outgoing: Dict,
        path: List[str], visited: set,
        results: List[List[str]]
    ) -> None:
        """Find all forward paths from current to target via DFS."""
        if current == target and len(path) > 1:
            results.append(list(path))
            return

        for next_block in outgoing.get(current, []):
            if next_block not in visited or next_block == target:
                visited.add(next_block)
                path.append(next_block)
                self._dfs_forward_paths(next_block, target, incoming, outgoing, path, visited, results)
                path.pop()
                if next_block != target:
                    visited.discard(next_block)

    @staticmethod
    def _block_sort_key(bid: str) -> Tuple:
        """Numeric sort key for block IDs to avoid lexicographic ordering bugs."""
        m = re.search(r'\d+$', bid)
        return (int(m.group()) if m else 0, bid)

    def _dfs_loops(
        self, start: str, current: str,
        outgoing: Dict,
        path: List[str], visited: set,
        results: List[List[str]],
        seen_loops: set
    ) -> None:
        """Find all loops starting from start via DFS."""
        for next_block in outgoing.get(current, []):
            if next_block == start and len(path) > 1:
                # Found a loop - normalize to avoid duplicates
                loop = list(path)
                # Normalize: rotate so numerically-smallest ID is first
                min_idx = loop.index(min(loop, key=self._block_sort_key))
                normalized = loop[min_idx:] + loop[:min_idx]
                key = tuple(normalized)
                if key not in seen_loops:
                    seen_loops.add(key)
                    results.append(normalized)
            elif next_block not in visited:
                visited.add(next_block)
                path.append(next_block)
                self._dfs_loops(start, next_block, outgoing, path, visited, results, seen_loops)
                path.pop()
                visited.discard(next_block)

    def _clean_poly(self, coeffs: np.ndarray) -> np.ndarray:
        """Remove trailing near-zero coefficients from polynomial (low-power-first)."""
        if len(coeffs) == 0:
            return np.array([0.0])
        max_abs = max(abs(coeffs)) if len(coeffs) > 0 else 0
        threshold = 1e-10 * max_abs if max_abs > 0 else 1e-10
        # Find last non-negligible coefficient
        last_nonzero = 0
        for i in range(len(coeffs) - 1, -1, -1):
            if abs(coeffs[i]) > threshold:
                last_nonzero = i
                break
        result = coeffs[:last_nonzero + 1]
        return result if len(result) > 0 else np.array([0.0])

    def _operator_to_z(self, num: np.ndarray, den: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert from R-domain (R = z^{-1}) to z-domain.

        H(R) = N(R)/D(R) where R = z^{-1}.
        Multiply both num and den by z^(max_order) to clear negative powers.

        Example: H(R) = 1/(1-R), num=[1], den=[1,-1]
          den order = 1 (highest R power in denominator)
          Multiply by z^1: num becomes z*1 = z, den becomes z*(1-z^{-1}) = z-1
          So H(z) = z/(z-1)

        Returns HIGH-power-first arrays (for np.roots and display).
        """
        # The max order to multiply by = max(len(num), len(den)) - 1
        # But we need the denominator order to properly clear negatives
        den_order = len(den) - 1
        num_order = len(num) - 1
        multiply_order = max(den_order, num_order)

        # Multiplying N(z^{-1}) by z^k is equivalent to
        # padding the coefficient array to length k+1 and reversing.
        # N(R) = [a0, a1, ..., an] = a0 + a1*R + ... + an*R^n
        # z^k * N(z^{-1}) = a0*z^k + a1*z^{k-1} + ... + an*z^{k-n}
        # In high-power-first: [a0, a1, ..., an, 0, ..., 0] with total length k+1
        # Wait, that's just pad to k+1 and DON'T reverse.

        # Actually: z^k * (a0 + a1*z^{-1} + ... + an*z^{-n})
        #         = a0*z^k + a1*z^{k-1} + ... + an*z^{k-n}
        # High-power-first coefficients of z^k, z^{k-1}, ..., z^0:
        # = a0, a1, ..., an, 0, 0, ... (padded to k+1 entries)
        # This is just the original low-power-first array without reversal!

        k = multiply_order
        z_num = np.zeros(k + 1)
        z_den = np.zeros(k + 1)
        z_num[:len(num)] = num
        z_den[:len(den)] = den

        # z_num and z_den are now HIGH-power-first (a0 is coeff of z^k)
        # Strip trailing zeros (which are leading zeros in polynomial sense)
        # Actually these are already in the right format.

        # But wait — np.roots expects [a_n, a_{n-1}, ..., a_0] where a_n is highest.
        # Our z_num = [a0, a1, ..., an, 0, ...] where a0 is coeff of z^k.
        # So z_num IS in high-power-first format already. Good.

        # Don't trim — trailing zeros represent lower-power z terms
        # Only ensure non-empty
        if not np.any(z_num != 0):
            z_num = np.array([0.0])
        if not np.any(z_den != 0):
            z_den = np.array([1.0])

        return z_num, z_den

    def _operator_to_s(self, num: np.ndarray, den: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert from A-domain (A = 1/s) to s-domain.
        Same logic as R→z but with A = 1/s.
        Returns HIGH-power-first arrays.
        """
        den_order = len(den) - 1
        num_order = len(num) - 1
        k = max(den_order, num_order)

        s_num = np.zeros(k + 1)
        s_den = np.zeros(k + 1)
        s_num[:len(num)] = num
        s_den[:len(den)] = den

        if not np.any(s_num != 0):
            s_num = np.array([0.0])
        if not np.any(s_den != 0):
            s_den = np.array([1.0])

        return s_num, s_den

    def _poly_ratio_to_string(self, num: np.ndarray, den: np.ndarray, var: str) -> str:
        """Convert polynomial ratio to readable string.
        Handles both low-power-first (R/A domain) and high-power-first (z/s domain).
        """
        num_str = self._poly_to_string(num, var)
        den_str = self._poly_to_string(den, var)

        if den_str == "1":
            return num_str
        return f"({num_str}) / ({den_str})"

    def _poly_to_string(self, coeffs: np.ndarray, var: str) -> str:
        """Convert polynomial coefficients to readable string.

        For R and A: low-power-first (coeffs[i] = coeff of var^i)
        For z and s: high-power-first (coeffs[0] = coeff of var^(n-1))
        """
        if len(coeffs) == 0:
            return "0"
        if len(coeffs) == 1:
            return self._format_coeff(coeffs[0])

        # Determine convention based on variable
        high_power_first = var in ("z", "s")

        terms = []
        for i, c in enumerate(coeffs):
            if abs(c) < 1e-10:
                continue

            if high_power_first:
                power = len(coeffs) - 1 - i  # highest power first
            else:
                power = i  # lowest power first

            if power == 0:
                term = self._format_coeff(c)
            elif power == 1:
                if abs(c - 1.0) < 1e-10:
                    term = var
                elif abs(c + 1.0) < 1e-10:
                    term = f"-{var}"
                else:
                    term = f"{self._format_coeff(c)}{var}"
            else:
                if abs(c - 1.0) < 1e-10:
                    term = f"{var}^{power}"
                elif abs(c + 1.0) < 1e-10:
                    term = f"-{var}^{power}"
                else:
                    term = f"{self._format_coeff(c)}{var}^{power}"
            terms.append(term)

        if not terms:
            return "0"

        result = terms[0]
        for t in terms[1:]:
            if t.startswith("-"):
                result += f" - {t[1:]}"
            else:
                result += f" + {t}"
        return result if result else "0"

    def _format_coeff(self, c: float) -> str:
        """Format a coefficient nicely."""
        if abs(c - round(c)) < 1e-10:
            return str(int(round(c)))
        return f"{c:.4g}"

    def _poly_to_latex(self, coeffs: np.ndarray, var: str) -> str:
        """Convert polynomial coefficients to LaTeX string."""
        if len(coeffs) == 0:
            return "0"
        if len(coeffs) == 1:
            return self._format_coeff(coeffs[0])

        high_power_first = var in ("z", "s")
        terms = []
        for i, c in enumerate(coeffs):
            if abs(c) < 1e-10:
                continue
            power = (len(coeffs) - 1 - i) if high_power_first else i

            if power == 0:
                term = self._format_coeff(c)
            elif power == 1:
                if abs(c - 1.0) < 1e-10:
                    term = var
                elif abs(c + 1.0) < 1e-10:
                    term = f"-{var}"
                else:
                    term = f"{self._format_coeff(c)}{var}"
            else:
                if abs(c - 1.0) < 1e-10:
                    term = f"{var}^{{{power}}}"
                elif abs(c + 1.0) < 1e-10:
                    term = f"-{var}^{{{power}}}"
                else:
                    term = f"{self._format_coeff(c)}{var}^{{{power}}}"
            terms.append(term)

        if not terms:
            return "0"
        result = terms[0]
        for t in terms[1:]:
            if t.startswith("-"):
                result += f" - {t[1:]}"
            else:
                result += f" + {t}"
        return result if result else "0"

    def _poly_ratio_to_latex(self, num: np.ndarray, den: np.ndarray, var: str) -> str:
        """Convert polynomial ratio to LaTeX fraction."""
        num_str = self._poly_to_latex(num, var)
        den_str = self._poly_to_latex(den, var)
        if den_str == "1":
            return num_str
        return f"\\frac{{{num_str}}}{{{den_str}}}"

    def _format_roots(self, roots: List) -> List[Dict[str, Any]]:
        """Format complex roots for display."""
        formatted = []
        for r in roots:
            if isinstance(r, complex) or (isinstance(r, np.complexfloating)):
                r = complex(r)
                if abs(r.imag) < 1e-10:
                    formatted.append({"real": round(r.real, 6), "imag": 0, "magnitude": abs(r.real)})
                else:
                    formatted.append({
                        "real": round(r.real, 6),
                        "imag": round(r.imag, 6),
                        "magnitude": round(abs(r), 6),
                    })
            else:
                formatted.append({"real": round(float(r), 6), "imag": 0, "magnitude": abs(float(r))})
        return formatted

    # =========================================================================
    # Transfer function parsing (TF → Diagram)
    # =========================================================================

    def _parse_transfer_function(self, tf_string: str) -> None:
        """
        Parse a transfer function string and generate a block diagram.

        Supports formats:
        - "(1 - R) / (1 - 0.5R)" for DT (R operator)
        - "(s + 2) / (s^2 + 3s + 1)" for CT (s domain)
        - "1 / (1 - 0.5 z^-1)" for z-domain
        """
        if not tf_string.strip():
            raise ValueError("Please enter a transfer function expression.")
        if len(tf_string) > 500:
            raise ValueError("Expression too long (max 500 characters).")

        # Clean up input
        tf_clean = tf_string.strip()

        # Detect variable and system type using word-boundary-aware regex
        # Look for standalone R, z, or s used as operator variables
        if re.search(r'(?<![a-zA-Z])R(?![a-zA-Z])', tf_clean):
            var = "R"
            self.system_type = "dt"
            self.parameters["system_type"] = "dt"
        elif re.search(r'(?<![a-zA-Z])z(?![a-zA-Z])', tf_clean, re.IGNORECASE):
            var = "z"
            self.system_type = "dt"
            self.parameters["system_type"] = "dt"
        elif re.search(r'(?<![a-zA-Z])s(?![a-zA-Z])', tf_clean) or \
             re.search(r'(?<![a-zA-Z])A(?![a-zA-Z])', tf_clean):
            var = "s"
            self.system_type = "ct"
            self.parameters["system_type"] = "ct"
        else:
            var = "R"  # default to DT

        try:
            num_coeffs, den_coeffs = self._parse_ratio(tf_clean, var)
        except Exception as e:
            raise ValueError(f"Could not parse expression: {e}")

        # For s-domain and z-domain inputs, convert to operator-domain
        # before building the block diagram.
        # - s-domain (CT): A = 1/s, so convert N(s)/D(s) to N_A(A)/D_A(A)
        # - z-domain (DT) with positive powers: R = z^{-1}, convert N(z)/D(z) to N_R(R)/D_R(R)
        # - z-domain with z^{-1} notation: parser already outputs R-domain, no conversion
        # - R-domain: already in operator form, no conversion needed
        if var == "s":
            num_coeffs, den_coeffs = self._s_to_a_coeffs(num_coeffs, den_coeffs)
        elif var == "z":
            # Only convert if user used positive z-powers (e.g., z, z^2)
            # If user used z^-1 notation, parser already produced R-domain coefficients
            uses_negative_z = bool(re.search(r'z\s*\^\s*-', tf_clean, re.IGNORECASE))
            if not uses_negative_z:
                num_coeffs, den_coeffs = self._z_to_r_coeffs(num_coeffs, den_coeffs)

        # Generate direct-form block diagram from operator-domain coefficients
        self._generate_direct_form_diagram(num_coeffs, den_coeffs)

        # Compute the TF result
        self._recompute_tf()

    @staticmethod
    def _s_to_a_coeffs(
        num_s: List[float], den_s: List[float]
    ) -> Tuple[List[float], List[float]]:
        """Convert s-domain coefficients to A-domain (A = 1/s).

        H(s) = N(s)/D(s) where N(s) = n0 + n1*s + n2*s^2 + ...
        Substituting s = 1/A:
            N(1/A) = n0 + n1/A + n2/A^2 + ...
        Multiply by A^k (k = max order across num and den):
            A^k * N(1/A) = n0*A^k + n1*A^(k-1) + ... + nk
        This gives coefficients in DESCENDING powers of A.
        In LOW-POWER-FIRST convention, we reverse: [nk, ..., n1, n0]

        Returns (num_A, den_A) in low-power-first A convention.
        """
        k = max(len(num_s) - 1, len(den_s) - 1)

        # Pad to length k+1
        ns = list(num_s) + [0.0] * (k + 1 - len(num_s))
        ds = list(den_s) + [0.0] * (k + 1 - len(den_s))

        # After multiplying by A^k, high-power-first coeffs are [n0, n1, ..., nk]
        # In low-power-first A: reverse it -> [nk, ..., n1, n0]
        num_a = list(reversed(ns[:k + 1]))
        den_a = list(reversed(ds[:k + 1]))

        return num_a, den_a

    @staticmethod
    def _z_to_r_coeffs(
        num_z: List[float], den_z: List[float]
    ) -> Tuple[List[float], List[float]]:
        """Convert z-domain coefficients (low-power-first in z) to R-domain (R = z^{-1}).

        If the parser already handled z^-1 as positive R powers, the coefficients
        may already be in R-domain. But if the user entered z-domain (positive powers
        of z), we need to convert.

        For z-domain: N(z) = n0 + n1*z + n2*z^2 + ...
        R = z^{-1}, so z = 1/R:
            N(1/R) = n0 + n1/R + n2/R^2 + ...
        Multiply by R^k: n0*R^k + n1*R^(k-1) + ... + nk
        Low-power-first in R: [nk, ..., n1, n0]

        This is the same reversal as s-to-A.
        """
        k = max(len(num_z) - 1, len(den_z) - 1)

        nz = list(num_z) + [0.0] * (k + 1 - len(num_z))
        dz = list(den_z) + [0.0] * (k + 1 - len(den_z))

        num_r = list(reversed(nz[:k + 1]))
        den_r = list(reversed(dz[:k + 1]))

        return num_r, den_r

    @staticmethod
    def _strip_outer_parens(s: str) -> str:
        """Strip matched outer parentheses only if they wrap the entire expression.

        '(s+2)' -> 's+2'
        '((s+2))' -> 's+2'
        '(s+1)(s+2)' -> '(s+1)(s+2)' (unchanged, parens don't wrap whole expr)
        """
        s = s.strip()
        while len(s) >= 2 and s[0] == '(' and s[-1] == ')':
            # Check if the opening paren at 0 matches the closing paren at -1
            depth = 0
            matched = True
            for i, ch in enumerate(s):
                if ch == '(':
                    depth += 1
                elif ch == ')':
                    depth -= 1
                if depth == 0 and i < len(s) - 1:
                    # The opening paren closed before the end
                    matched = False
                    break
            if matched:
                s = s[1:-1].strip()
            else:
                break
        return s

    def _parse_ratio(self, expr: str, var: str) -> Tuple[List[float], List[float]]:
        """Parse a ratio of polynomials like '(1 - R) / (1 - 0.5R)'.

        Properly handles parenthesized and unparenthesized expressions.
        """
        # Remove H(R)= or H(z)= prefix
        expr = re.sub(r'H\([^)]*\)\s*=\s*', '', expr).strip()

        # Find the division point — must be a '/' that is NOT inside parentheses
        split_idx = -1
        depth = 0
        for i, ch in enumerate(expr):
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
            elif ch == '/' and depth == 0:
                split_idx = i
                break

        if split_idx >= 0:
            num_str = self._strip_outer_parens(expr[:split_idx])
            den_str = self._strip_outer_parens(expr[split_idx + 1:])
        else:
            num_str = self._strip_outer_parens(expr)
            den_str = "1"

        num_coeffs = self._parse_polynomial(num_str, var)
        den_coeffs = self._parse_polynomial(den_str, var)

        return num_coeffs, den_coeffs

    def _parse_polynomial(self, poly_str: str, var: str) -> List[float]:
        """
        Parse polynomial string like '1 - 0.5R' or 's^2 + 3s + 1'.

        Returns coefficients [c0, c1, c2, ...] where c_i is coefficient of var^i
        (low-power-first).
        """
        poly_str = poly_str.strip()

        if not poly_str or poly_str == "0":
            return [0.0]

        # Handle pure number
        try:
            val = float(poly_str)
            return [val]
        except ValueError:
            pass

        # Tokenize into signed terms properly.
        # Insert a '+' before every '-' or '+' that acts as a term separator
        # (not as part of an exponent like s^-1).
        # Strategy: split on +/- that are preceded by a digit, letter, or ')'
        # and NOT inside an exponent context.
        terms = self._tokenize_polynomial(poly_str, var)

        coeffs = {}
        for term in terms:
            term = term.strip()
            if not term:
                continue

            # Check if this term contains the variable
            has_var = bool(re.search(rf'{re.escape(var)}', term, re.IGNORECASE))

            if not has_var:
                # Constant term
                try:
                    coeffs[0] = coeffs.get(0, 0) + float(term.replace(" ", ""))
                except ValueError:
                    pass
                continue

            # Find the power of the variable
            power_match = re.search(
                rf'{re.escape(var)}\s*\^\s*(-?\d+)',
                term, re.IGNORECASE
            )
            if power_match:
                power = int(power_match.group(1))
                # Handle z^-1 -> power 1 in R-domain
                if var.lower() == "z" and power < 0:
                    power = -power
            else:
                # Just var with no exponent -> power = 1
                power = 1

            # Extract coefficient: remove the variable and its exponent
            coeff_str = re.sub(
                rf'\s*\*?\s*{re.escape(var)}(\s*\^\s*-?\d+)?',
                '', term, flags=re.IGNORECASE
            ).strip()

            # Remove trailing multiplication signs
            coeff_str = coeff_str.rstrip("*·").strip()
            # Remove internal spaces (e.g., "- 0.5" -> "-0.5")
            coeff_str = coeff_str.replace(" ", "")

            if coeff_str in ("", "+"):
                coeff = 1.0
            elif coeff_str == "-":
                coeff = -1.0
            else:
                try:
                    coeff = float(coeff_str)
                except ValueError:
                    coeff = 1.0

            coeffs[power] = coeffs.get(power, 0) + coeff

        if not coeffs:
            return [1.0]

        max_power = max(coeffs.keys())
        if max_power < 0:
            # All powers negative — shouldn't happen for well-formed polys
            return [0.0]
        result = [coeffs.get(i, 0.0) for i in range(max_power + 1)]
        return result

    @staticmethod
    def _tokenize_polynomial(poly_str: str, var: str) -> List[str]:
        """Split polynomial string into signed terms.

        Handles expressions like:
          '1 - 0.5R'     -> ['1', '-0.5R']
          's^2 + 3s + 1' -> ['s^2', '3s', '1']
          '-s^2 + 3s'    -> ['-s^2', '3s']
          '4658s^2 + s'  -> ['4658s^2', 's']

        Correctly preserves signs on exponents like s^-1.
        """
        terms = []
        current = ""
        i = 0
        s = poly_str.strip()

        while i < len(s):
            ch = s[i]

            if ch in ('+', '-') and i > 0:
                # Check if this +/- is part of an exponent (e.g., s^-1)
                # Look back to see if preceded by '^' (possibly with spaces)
                j = i - 1
                while j >= 0 and s[j] == ' ':
                    j -= 1
                if j >= 0 and s[j] == '^':
                    # This sign is part of an exponent — don't split
                    current += ch
                    i += 1
                    continue

                # This is a term separator
                if current.strip():
                    terms.append(current.strip())
                current = ch if ch == '-' else ""
                i += 1
                continue

            current += ch
            i += 1

        if current.strip():
            terms.append(current.strip())

        return terms

    @staticmethod
    def _output_port(block_type: str) -> int:
        """Get the default output port index (right side) for a block type.

        Port numbering: gain/delay/integrator: 0=left, 1=right.
        Adder: 0=left, 1=bottom, 2=right. Junction: port 1 (first output).
        Input/output: 0 (single port).
        """
        if block_type == "adder":
            return 2
        if block_type in ("gain", "delay", "integrator"):
            return 1
        if block_type == "junction":
            return 1
        return 0  # input, output

    def _generate_direct_form_diagram(
        self, num_coeffs: List[float], den_coeffs: List[float]
    ) -> None:
        """
        Generate a Direct Form I block diagram from TF coefficients.

        For H(R) = (b0 + b1*R + b2*R^2) / (1 + a1*R + a2*R^2)
        (note: den_coeffs stores as-is, e.g. '1 - 0.5R' -> [1, -0.5])

        Uses only 2-input adders in a cascaded chain. The structure:
        - Input feeds through b0 gain into the first adder
        - Each subsequent adder combines delayed numerator and denominator terms
        - Output is taken from the first adder (after the forward chain)

        Direct Form I produces a clean cascaded layout with separate
        feedforward (numerator) and feedback (denominator) delay chains:

          x ──[b0]──┐
          │         (+)──> y
          [R]─[b1]──┘     │
          │               [R]─[-a1]──┐
          [R]─[b2]──┐     │         (+)
                    (+)   [R]─[-a2]──┘
                    ...

        All adders have exactly 2 inputs.
        """
        self.blocks = {}
        self.connections = []
        self._next_block_id = 0

        delay_type = "delay" if self.system_type == "dt" else "integrator"

        def connect(from_id: str, to_id: str, to_port: int = 0) -> None:
            """Add connection using correct output port for the source block type."""
            from_type = self.blocks[from_id]["type"]
            self.connections.append({
                "from_block": from_id,
                "from_port": self._output_port(from_type),
                "to_block": to_id,
                "to_port": to_port,
            })

        # Determine order
        num_order = len(num_coeffs) - 1
        den_order = len(den_coeffs) - 1
        order = max(num_order, den_order)

        # Pad coefficients to same length
        while len(num_coeffs) <= order:
            num_coeffs.append(0.0)
        while len(den_coeffs) <= order:
            den_coeffs.append(0.0)

        # Normalize: divide all by den_coeffs[0] so denominator starts with 1
        if abs(den_coeffs[0]) > 1e-12 and abs(den_coeffs[0] - 1.0) > 1e-12:
            scale = den_coeffs[0]
            num_coeffs = [c / scale for c in num_coeffs]
            den_coeffs = [c / scale for c in den_coeffs]

        # Compute actual needed chain lengths — skip trailing zero coefficients
        # This prevents creating orphan delay blocks with no signal output
        ff_chain_len = 0  # how many feedforward delays actually needed
        for k in range(order, 0, -1):
            if abs(num_coeffs[k]) > 1e-10:
                ff_chain_len = k
                break

        fb_chain_len = 0  # how many feedback delays actually needed
        for k in range(order, 0, -1):
            if abs(den_coeffs[k]) > 1e-10:
                fb_chain_len = k
                break

        # Dynamic layout — adaptive spacing to fit 1800x1000 canvas
        # Row 1 (top): feedforward delays, with gains stacked below them
        # Row 2 (middle): main signal path — input, adders, output
        # Row 3 (bottom): feedback delays, with gains stacked below them
        GRID = 24

        # Count how many columns we need: delays + adders + input + output
        num_ff_signals = sum(1 for c in num_coeffs if abs(c) > 1e-10)
        num_fb_signals = sum(1 for c in den_coeffs[1:] if abs(c) > 1e-10)
        num_adders = max(0, num_ff_signals + num_fb_signals - 1)
        max_chain = max(ff_chain_len, fb_chain_len)
        total_columns = max_chain + num_adders + 2  # delays + adders + in/out

        # Adaptive horizontal spacing: fit into ~1500px usable width
        # Minimum 192px (8 grid cells) so blocks have room for vertical wires between them
        spacing_x = max(192, min(240, int(1500 / max(total_columns, 4) / GRID) * GRID))

        # Row spacing — generous vertical separation for clean wire routing
        row_spacing = 336  # 14 grid cells between main path and delay rows

        main_y = 480  # center of 1000px canvas
        start_x = 96  # 4 grid cells from left edge

        # Create input
        inp = self._gen_block_id()
        self.blocks[inp] = {
            "id": inp, "type": "input",
            "position": {"x": start_x, "y": main_y},
        }

        # Create output
        out_x = start_x + (order + 3) * spacing_x
        out = self._gen_block_id()
        self.blocks[out] = {
            "id": out, "type": "output",
            "position": {"x": out_x, "y": main_y},
        }

        if order == 0:
            # Simple gain: H = b0 / a0 (a0 already normalized to 1)
            gain_val = num_coeffs[0]
            if abs(gain_val - 1.0) > 1e-10:
                gain = self._gen_block_id()
                self.blocks[gain] = {
                    "id": gain, "type": "gain",
                    "position": {"x": 288, "y": main_y},
                    "value": gain_val,
                }
                connect(inp, gain, 0)
                connect(gain, out, 0)
            else:
                connect(inp, out, 0)
            return

        # =====================================================================
        # Direct Form I realization
        # =====================================================================
        #
        # The difference equation in DF-II transposed form is:
        #   y[n] = b0*x[n] + w1[n]
        #   w1[n] = b1*x[n] - a1*y[n] + w2[n-1]   (delayed)
        #   w2[n] = b2*x[n] - a2*y[n] + w3[n-1]   (delayed)
        #   ...
        #
        # Each stage: adder(bk*x - ak*y, delayed_from_next_stage)
        #
        # But to use strictly 2-input adders, we chain:
        #   Stage 0: output_adder: b0*x + delay_chain_output → y
        #   Stage k (k=1..order): ff_gain(bk) and fb_gain(-ak) feed
        #     into adders that combine with the chain from higher stages.
        #
        # Simplified approach: use direct form I with cascaded 2-input adders
        # for the summation of all feedforward and feedback contributions.
        # =====================================================================

        # Collect all signal contributions that need to be summed:
        # - Feedforward: b0*x, b1*R*x, b2*R^2*x, ...
        # - Feedback:    -a1*R*y, -a2*R^2*y, ...
        #
        # Build these as signal sources, then cascade-add them with 2-input adders.

        # --- Build feedforward delay chain (from input) ---
        # Signals: (block_id, sign, from_port) — from_port is which port to wire out of
        ff_signals = []

        # b0 * x[n]: direct path
        ff_row_y = main_y - row_spacing       # feedforward delay row
        if abs(num_coeffs[0]) > 1e-10:
            if abs(abs(num_coeffs[0]) - 1.0) < 1e-10:
                sign = "+" if num_coeffs[0] > 0 else "-"
                ff_signals.append((inp, sign, self._output_port("input")))
            else:
                g = self._gen_block_id()
                self.blocks[g] = {
                    "id": g, "type": "gain",
                    "position": {"x": start_x + spacing_x, "y": ff_row_y - 216},
                    "value": abs(num_coeffs[0]),
                }
                connect(inp, g, 0)
                sign = "+" if num_coeffs[0] > 0 else "-"
                ff_signals.append((g, sign, 1))  # LTR gain: port 1 output

        # Delayed feedforward: bk * R^k * x (LTR: port 0 in, port 1 out)
        prev_ff_delay = None
        for k in range(1, ff_chain_len + 1):
            d = self._gen_block_id()
            self.blocks[d] = {
                "id": d, "type": delay_type,
                "position": {"x": start_x + k * spacing_x, "y": ff_row_y},
            }
            source = prev_ff_delay if prev_ff_delay is not None else inp
            connect(source, d, 0)
            prev_ff_delay = d

            if abs(num_coeffs[k]) > 1e-10:
                if abs(abs(num_coeffs[k]) - 1.0) < 1e-10:
                    sign = "+" if num_coeffs[k] > 0 else "-"
                    ff_signals.append((d, sign, 1))  # LTR delay: port 1 output
                else:
                    g = self._gen_block_id()
                    self.blocks[g] = {
                        "id": g, "type": "gain",
                        # Gain stacked BELOW its delay (same x, offset y)
                        "position": {"x": start_x + k * spacing_x, "y": ff_row_y - 216},
                        "value": abs(num_coeffs[k]),
                    }
                    connect(d, g, 0)
                    sign = "+" if num_coeffs[k] > 0 else "-"
                    ff_signals.append((g, sign, 1))  # LTR gain: port 1 output

        # --- Build feedback delay chain (from output) ---
        # We will connect these from the output adder. The output adder
        # will be created as part of the cascaded sum chain.
        # For now, collect feedback signals as placeholders.
        # den_coeffs are in form [1, a1, a2, ...] where the equation is
        # y * (1 + a1*R + a2*R^2 + ...) = num, so:
        # y = num_out => y + a1*R*y + a2*R^2*y = num_out
        # => num_out = y(1 + a1*R + ...) => y = num_out / (1 + a1*R + ...)
        # The feedback subtracts ak*R^k*y from the sum, so:
        # y = (sum of ff) - a1*R*y - a2*R^2*y - ...
        # Sign: if den_coeffs[k] is negative (e.g., -0.5 in 1-0.5R),
        #   then we subtract a negative = add, so sign = "+"
        # If den_coeffs[k] is positive, we subtract, so sign = "-"

        fb_signals = []  # (block_id, sign, from_port) — RTL: port 0 output
        fb_delays = []   # delay block ids in order, for chaining from output

        # We'll create the feedback blocks but connect them to the output later
        # (after we know which block is the output adder)

        fb_delay_blocks = []
        fb_gain_blocks = []   # (gain_id, delay_idx) pairs for repositioning
        fb_row_y = main_y + row_spacing       # feedback delay row

        # Placeholder x positions — will be repositioned right-to-left after adder chain
        for k in range(1, fb_chain_len + 1):
            d = self._gen_block_id()
            self.blocks[d] = {
                "id": d, "type": delay_type,
                "position": {"x": 0, "y": fb_row_y},  # x set later
            }
            fb_delay_blocks.append(d)

            # Chain feedback delays RTL: previous delay port 0 (left out) → next delay port 1 (right in)
            if k >= 2:
                self.connections.append({
                    "from_block": fb_delay_blocks[k - 2],
                    "from_port": 0,  # left output (RTL)
                    "to_block": d,
                    "to_port": 1,    # right input (RTL)
                })

            if abs(den_coeffs[k]) > 1e-10:
                if abs(abs(den_coeffs[k]) - 1.0) < 1e-10:
                    sign = "-" if den_coeffs[k] > 0 else "+"
                    fb_signals.append((d, sign, 0))  # RTL: port 0 output
                else:
                    g = self._gen_block_id()
                    self.blocks[g] = {
                        "id": g, "type": "gain",
                        # Gain ABOVE its delay (between main path and delay row)
                        "position": {"x": 0, "y": fb_row_y - 168},  # x set later
                        "value": abs(den_coeffs[k]),
                    }
                    fb_gain_blocks.append((g, k - 1))  # delay index 0-based
                    # RTL: delay port 0 (left out) → gain port 1 (right in)
                    self.connections.append({
                        "from_block": d,
                        "from_port": 0,
                        "to_block": g,
                        "to_port": 1,
                    })
                    sign = "-" if den_coeffs[k] > 0 else "+"
                    fb_signals.append((g, sign, 0))  # RTL gain: port 0 output

        # --- Cascade-add all signals using 2-input adders ---
        # Reverse fb_signals so that fb_delay[last] (furthest from output, leftmost)
        # feeds the leftmost feedback adder, and fb_delay[0] (nearest output, rightmost)
        # feeds the rightmost feedback adder.  This aligns each feedback delay
        # vertically under its target adder, producing short vertical wires
        # instead of long diagonal crossings.
        all_signals = ff_signals + list(reversed(fb_signals))

        if len(all_signals) == 0:
            # Degenerate: just wire input to output
            connect(inp, out, 0)
            return

        if len(all_signals) == 1:
            sig_id, sig_sign, sig_port = all_signals[0]
            if sig_sign == "-":
                neg = self._gen_block_id()
                self.blocks[neg] = {
                    "id": neg, "type": "gain",
                    "position": {"x": out_x - spacing_x, "y": main_y},
                    "value": -1.0,
                }
                self.connections.append({
                    "from_block": sig_id, "from_port": sig_port,
                    "to_block": neg, "to_port": 0,
                })
                connect(neg, out, 0)
            else:
                self.connections.append({
                    "from_block": sig_id, "from_port": sig_port,
                    "to_block": out, "to_port": 0,
                })

            # Connect feedback delays from output RTL: output → delay port 1 (right in)
            if fb_delay_blocks:
                self.connections.append({
                    "from_block": sig_id,
                    "from_port": sig_port,
                    "to_block": fb_delay_blocks[0],
                    "to_port": 1,
                })
            return

        # Build a cascade of 2-input adders — use same spacing as delays for uniform rhythm
        adder_x_start = start_x + (order + 1) * spacing_x
        adder_spacing = spacing_x  # uniform with delay chain
        adders = []

        for i in range(len(all_signals) - 1):
            adder_id = self._gen_block_id()
            adder_x = adder_x_start + (i * adder_spacing)
            self.blocks[adder_id] = {
                "id": adder_id, "type": "adder",
                "position": {"x": adder_x, "y": main_y},
                "signs": ["+", "+", "+"],
            }
            adders.append(adder_id)

        # Wire the cascade using explicit from_port from signal tuples
        sig0_id, sig0_sign, sig0_port = all_signals[0]
        sig1_id, sig1_sign, sig1_port = all_signals[1]

        self.connections.append({
            "from_block": sig0_id, "from_port": sig0_port,
            "to_block": adders[0], "to_port": 0,
        })
        self.connections.append({
            "from_block": sig1_id, "from_port": sig1_port,
            "to_block": adders[0], "to_port": 1,
        })
        self.blocks[adders[0]]["signs"] = [sig0_sign, sig1_sign, "+"]

        for i in range(1, len(adders)):
            sig_id, sig_sign, sig_from_port = all_signals[i + 1]
            connect(adders[i - 1], adders[i], 0)
            self.connections.append({
                "from_block": sig_id, "from_port": sig_from_port,
                "to_block": adders[i], "to_port": 1,
            })
            self.blocks[adders[i]]["signs"] = ["+", sig_sign, "+"]

        # Last adder output → output block
        last_adder = adders[-1]
        connect(last_adder, out, 0)

        # Reposition output to the right of the last adder
        last_adder_x = self.blocks[last_adder]["position"]["x"]
        self.blocks[out]["position"]["x"] = last_adder_x + spacing_x

        # Reposition feedback delays RIGHT-TO-LEFT: fb_delay[0] near output, chain flows left
        # Use wider spacing for feedback to avoid clutter with gains below
        if fb_delay_blocks:
            out_x_final = self.blocks[out]["position"]["x"]
            fb_spacing = max(spacing_x, 288)  # wider than main path spacing
            for i, d_id in enumerate(fb_delay_blocks):
                # fb_delay[0] directly below output, subsequent delays to the left
                self.blocks[d_id]["position"]["x"] = out_x_final - (i + 1) * fb_spacing
            # Stagger gain blocks horizontally between delays (offset left by half fb_spacing)
            # This avoids gains stacking directly below delays and reduces wire crossings
            for g_id, delay_idx in fb_gain_blocks:
                delay_x = self.blocks[fb_delay_blocks[delay_idx]]["position"]["x"]
                self.blocks[g_id]["position"]["x"] = delay_x - fb_spacing // 2
                # Snap to grid
                self.blocks[g_id]["position"]["x"] = round(self.blocks[g_id]["position"]["x"] / GRID) * GRID

            # Connect feedback: last adder output → first delay port 1 (right in, RTL)
            self.connections.append({
                "from_block": last_adder,
                "from_port": self._output_port("adder"),
                "to_block": fb_delay_blocks[0],
                "to_port": 1,  # right input (RTL)
            })

        # Fix gain/delay port directions based on actual spatial positions.
        # After repositioning, some blocks may have their output port pointing
        # away from their target. Flip port assignments so the output side
        # faces the target block (shorter, cleaner wires).
        self._fix_port_directions()

        # Center diagram on canvas
        self._center_diagram()

    def _fix_port_directions(self) -> None:
        """Fix gain/delay/integrator port directions based on actual block positions.

        For each directional block (gain/delay/integrator), determines whether
        its output should go left or right based on where its target blocks are.
        Flips both incoming and outgoing connection ports so the block's
        visual orientation matches the actual signal flow direction.

        Only flips blocks where the MAJORITY of outgoing signal weight goes in
        the opposite direction to current orientation. Skips blocks that have
        mixed targets (some left, some right) to avoid breaking chain wiring.

        Port convention:
          LTR: port 0 (left) = input, port 1 (right) = output
          RTL: port 0 (left) = output, port 1 (right) = input
        """
        directional_types = {"gain", "delay", "integrator"}

        for block_id, block in self.blocks.items():
            if block["type"] not in directional_types:
                continue

            bx = block["position"]["x"]

            outgoing = [c for c in self.connections if c["from_block"] == block_id]
            incoming = [c for c in self.connections if c["to_block"] == block_id]

            if not outgoing:
                continue

            # Count how many outgoing targets are to the left vs right
            # Only consider targets with significant horizontal offset
            right_count = 0
            left_count = 0
            for conn in outgoing:
                target = self.blocks.get(conn["to_block"])
                if not target:
                    continue
                tx = target["position"]["x"]
                dx = tx - bx
                if dx > 24:  # target meaningfully to the right (> 1 grid cell)
                    right_count += 1
                elif dx < -24:  # target meaningfully to the left
                    left_count += 1
                # Targets at roughly same x: don't count (vertical connections)

            # Skip if no clear horizontal preference (ambiguous or all vertical)
            if right_count == 0 and left_count == 0:
                continue
            # Skip if mixed directions (would break some wires)
            if right_count > 0 and left_count > 0:
                continue

            want_ltr = right_count > 0  # output should go right

            # Check current direction from incoming connection port
            if incoming:
                current_input_port = incoming[0]["to_port"]
                is_currently_ltr = (current_input_port == 0)
            else:
                is_currently_ltr = True

            if want_ltr == is_currently_ltr:
                continue  # Already correct

            # Flip: swap port numbers on all connections involving this block
            for conn in incoming:
                conn["to_port"] = 1 - conn["to_port"]
            for conn in outgoing:
                conn["from_port"] = 1 - conn["from_port"]

    def _center_diagram(self) -> None:
        """Center all blocks on the canvas viewport center.

        Snaps the centering offset to grid (24px) so all blocks remain
        grid-aligned after centering.
        """
        if not self.blocks:
            return
        GRID = 24
        cw, ch = 1800, 1100
        center_x, center_y = cw / 2, ch / 2

        xs = [b["position"]["x"] for b in self.blocks.values()]
        ys = [b["position"]["y"] for b in self.blocks.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        diagram_cx = (min_x + max_x) / 2
        diagram_cy = (min_y + max_y) / 2
        # Snap offset to grid so all blocks stay grid-aligned
        offset_x = round((center_x - diagram_cx) / GRID) * GRID
        offset_y = round((center_y - diagram_cy) / GRID) * GRID

        for b in self.blocks.values():
            b["position"]["x"] += offset_x
            b["position"]["y"] += offset_y

        self._resolve_overlaps()

    def _resolve_overlaps(self) -> None:
        """Detect and resolve overlapping blocks by shifting them apart.

        Uses block bounding boxes with 48px padding (2 grid cells).
        All shifted positions are snapped to grid.
        """
        GRID = 24
        OVERLAP_PAD = 48  # 2 grid cells
        block_list = list(self.blocks.values())

        for _pass in range(3):
            moved = False
            for i in range(len(block_list)):
                for j in range(i + 1, len(block_list)):
                    bi, bj = block_list[i], block_list[j]
                    wi = self._block_width(bi["type"]) + OVERLAP_PAD
                    hi = self._block_height(bi["type"]) + OVERLAP_PAD
                    wj = self._block_width(bj["type"]) + OVERLAP_PAD
                    hj = self._block_height(bj["type"]) + OVERLAP_PAD

                    xi, yi = bi["position"]["x"], bi["position"]["y"]
                    xj, yj = bj["position"]["x"], bj["position"]["y"]

                    if (abs(xi - xj) < (wi + wj) / 2 and
                            abs(yi - yj) < (hi + hj) / 2):
                        # Shift and snap to grid
                        if xj >= xi:
                            bj["position"]["x"] = round((xi + (wi + wj) / 2) / GRID) * GRID
                        else:
                            bi["position"]["x"] = round((xj + (wi + wj) / 2) / GRID) * GRID
                        moved = True
            if not moved:
                break

    @staticmethod
    def _block_width(block_type: str) -> int:
        """Get block width for overlap detection (synced with frontend BLOCK_SIZES)."""
        sizes = {
            "input": 80, "output": 80, "gain": 80,
            "adder": 60, "delay": 80, "integrator": 80, "junction": 12,
        }
        return sizes.get(block_type, 80)

    @staticmethod
    def _block_height(block_type: str) -> int:
        """Get block height for overlap detection (synced with frontend BLOCK_SIZES)."""
        sizes = {
            "input": 60, "output": 60, "gain": 60,
            "adder": 60, "delay": 60, "integrator": 60, "junction": 12,
        }
        return sizes.get(block_type, 60)

    # =========================================================================
    # Plot generation
    # =========================================================================

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate step/impulse response plots if TF is computed."""
        if not self._tf_result:
            return []

        try:
            return [self._generate_response_plot()]
        except Exception:
            return []

    def _generate_response_plot(self) -> Dict[str, Any]:
        """Generate step and impulse response plot."""
        tf = self._tf_result
        num = np.array(tf["numerator"])
        den = np.array(tf["denominator"])

        if self.system_type == "dt":
            # Convert R-polynomial to z-polynomial for scipy
            z_num, z_den = self._operator_to_z(num, den)
            return self._dt_response_plot(z_num, z_den)
        else:
            s_num, s_den = self._operator_to_s(num, den)
            return self._ct_response_plot(s_num, s_den)

    def _dt_response_plot(self, z_num: np.ndarray, z_den: np.ndarray) -> Dict[str, Any]:
        """Generate DT step and impulse response."""
        N = 50  # number of samples

        # Compute impulse response by long division / filtering
        impulse = np.zeros(N)
        impulse[0] = 1.0
        step = np.ones(N)

        try:
            from scipy.signal import dlsim, dimpulse, dstep
            # Use scipy for proper computation
            system = (z_num, z_den, 1)  # dt=1
            _, impulse_resp = dimpulse(system, n=N)
            _, step_resp = dstep(system, n=N)
            impulse_resp = impulse_resp[0].flatten()
            step_resp = step_resp[0].flatten()
        except Exception:
            # Fallback: manual convolution
            impulse_resp = self._filter_signal(z_num, z_den, impulse)
            step_resp = self._filter_signal(z_num, z_den, step)

        n_vals = list(range(N))

        return {
            "id": "response",
            "title": "System Response",
            "data": [
                {
                    "x": n_vals,
                    "y": impulse_resp.tolist() if hasattr(impulse_resp, 'tolist') else list(impulse_resp),
                    "type": "scatter",
                    "mode": "markers+lines",
                    "name": "Impulse Response",
                    "marker": {"color": self.COLORS["impulse"], "size": 5},
                    "line": {"color": self.COLORS["impulse"], "width": 1.5, "dash": "solid"},
                },
                {
                    "x": n_vals,
                    "y": step_resp.tolist() if hasattr(step_resp, 'tolist') else list(step_resp),
                    "type": "scatter",
                    "mode": "markers+lines",
                    "name": "Step Response",
                    "marker": {"color": self.COLORS["step"], "size": 5},
                    "line": {"color": self.COLORS["step"], "width": 1.5, "dash": "solid"},
                },
            ],
            "layout": {
                "xaxis": {
                    "title": "n (samples)",
                    "gridcolor": self.COLORS["grid"],
                    "zerolinecolor": self.COLORS["zero"],
                    "color": self.COLORS["text"],
                },
                "yaxis": {
                    "title": "Amplitude",
                    "gridcolor": self.COLORS["grid"],
                    "zerolinecolor": self.COLORS["zero"],
                    "color": self.COLORS["text"],
                },
                "paper_bgcolor": "#0a0e27",
                "plot_bgcolor": "#131b2e",
                "font": {"family": "Inter, sans-serif", "size": 12, "color": self.COLORS["text"]},
                "margin": {"t": 40, "r": 25, "b": 55, "l": 60},
                "legend": {"x": 0.7, "y": 0.95, "bgcolor": "rgba(0,0,0,0.3)"},
                "showlegend": True,
            },
        }

    def _ct_response_plot(self, s_num: np.ndarray, s_den: np.ndarray) -> Dict[str, Any]:
        """Generate CT step and impulse response."""
        try:
            from scipy.signal import impulse, step, lti
            sys = lti(s_num, s_den)
            # Estimate suitable time range from poles
            poles = np.roots(s_den)
            real_parts = np.abs(np.real(poles[np.isfinite(poles)]))
            if len(real_parts) > 0 and np.max(real_parts) > 1e-6:
                t_end = max(10.0, 5.0 / np.min(real_parts[real_parts > 1e-6]) if np.any(real_parts > 1e-6) else 10.0)
            else:
                t_end = 10.0
            t_end = min(t_end, 100.0)  # Cap at 100s
            T = np.linspace(0, t_end, 500)
            t_imp, imp_resp = impulse(sys, T=T)
            t_step, step_resp = step(sys, T=T)
        except Exception:
            # Fallback with simple time vector
            t_imp = np.linspace(0, 10, 500)
            imp_resp = np.zeros_like(t_imp)
            t_step = t_imp
            step_resp = np.zeros_like(t_step)

        return {
            "id": "response",
            "title": "System Response",
            "data": [
                {
                    "x": t_imp.tolist(),
                    "y": imp_resp.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Impulse Response",
                    "line": {"color": self.COLORS["impulse"], "width": 2},
                },
                {
                    "x": t_step.tolist(),
                    "y": step_resp.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Step Response",
                    "line": {"color": self.COLORS["step"], "width": 2},
                },
            ],
            "layout": {
                "xaxis": {
                    "title": "Time (s)",
                    "gridcolor": self.COLORS["grid"],
                    "zerolinecolor": self.COLORS["zero"],
                    "color": self.COLORS["text"],
                },
                "yaxis": {
                    "title": "Amplitude",
                    "gridcolor": self.COLORS["grid"],
                    "zerolinecolor": self.COLORS["zero"],
                    "color": self.COLORS["text"],
                },
                "paper_bgcolor": "#0a0e27",
                "plot_bgcolor": "#131b2e",
                "font": {"family": "Inter, sans-serif", "size": 12, "color": self.COLORS["text"]},
                "margin": {"t": 40, "r": 25, "b": 55, "l": 60},
                "legend": {"x": 0.7, "y": 0.95, "bgcolor": "rgba(0,0,0,0.3)"},
                "showlegend": True,
            },
        }

    def _filter_signal(self, b: np.ndarray, a: np.ndarray, x: np.ndarray) -> np.ndarray:
        """Apply IIR filter (difference equation) to signal x using scipy."""
        from scipy.signal import lfilter
        return lfilter(b, a, x)

    # =========================================================================
    # State
    # =========================================================================

    def get_state(self) -> Dict[str, Any]:
        """Return current state with diagram data and computed TF."""
        state = super().get_state()
        state["metadata"] = {
            "simulation_type": "block_diagram_builder",
            "mode": self.mode,
            "system_type": self.system_type,
            "blocks": self.blocks,
            "connections": self.connections,
            "transfer_function": self._tf_result,
            "tf_input": self.tf_input,
            "error": self._error,
            "presets": {k: {"name": v["name"], "equation": v["equation"], "system_type": v["system_type"]}
                       for k, v in self.PRESETS.items()},
            "block_types": {
                k: {
                    "inputs": v["inputs"],
                    "outputs": v["outputs"],
                    "available": v.get("system") is None or v.get("system") == self.system_type,
                }
                for k, v in self.BLOCK_TYPES.items()
            },
        }
        return state
