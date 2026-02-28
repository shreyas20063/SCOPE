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
        self._history: List[Tuple[Dict, List, int]] = []
        self._max_history = 30

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
        if len(self._history) > self._max_history:
            self._history.pop(0)

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
            self.parameters[name] = self._validate_param(name, value)

        if name == "system_type":
            self.system_type = value
            # Recompute TF when switching system type
            self._recompute_tf()
        elif name == "mode":
            self.mode = value

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
            "split_wire": self._action_split_wire,
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
        self._save_history()
        block_type = params.get("block_type", "gain")
        position = params.get("position", {"x": 400, "y": 250})
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
            block["value"] = float(value) if value is not None else type_def.get("default_value", 1.0)
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
        """Update a block's value (e.g., gain constant)."""
        self._save_history()
        block_id = params.get("block_id")
        value = params.get("value")
        if block_id not in self.blocks:
            raise ValueError(f"Block not found: {block_id}")
        block = self.blocks[block_id]
        if block["type"] == "gain":
            block["value"] = float(value)
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

    def _action_set_mode(self, params: Dict[str, Any]) -> None:
        """Switch between build and parse mode."""
        mode = params.get("mode", "build")
        self.mode = mode
        self.parameters["mode"] = mode

    def _action_set_system_type(self, params: Dict[str, Any]) -> None:
        """Switch between DT and CT. Clears the diagram since block types differ."""
        self._save_history()
        system_type = params.get("system_type", "dt")
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

        self._center_diagram()
        self._recompute_tf()

    def _action_undo(self, params: Dict[str, Any]) -> None:
        """Undo the last mutating action by restoring previous state."""
        if not self._history:
            raise ValueError("Nothing to undo")
        blocks, connections, next_id = self._history.pop()
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
        self._save_undo()
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

    # =========================================================================
    # Preset builders
    # =========================================================================

    def _build_accumulator_preset(self) -> None:
        """y[n] = y[n-1] + x[n]: input → adder → output, delay feedback."""
        inp = self._gen_block_id()
        self.blocks[inp] = {"id": inp, "type": "input", "position": {"x": 120, "y": 240}}

        adder = self._gen_block_id()
        self.blocks[adder] = {"id": adder, "type": "adder", "position": {"x": 320, "y": 240}, "signs": ["+", "+", "+"]}

        out = self._gen_block_id()
        self.blocks[out] = {"id": out, "type": "output", "position": {"x": 600, "y": 240}}

        delay = self._gen_block_id()
        self.blocks[delay] = {"id": delay, "type": "delay", "position": {"x": 460, "y": 380}}

        # Port numbering: gain/delay port 0=left, 1=right; adder port 0=left, 1=bottom, 2=right
        self.connections = [
            {"from_block": inp, "from_port": 0, "to_block": adder, "to_port": 0},
            {"from_block": adder, "from_port": 2, "to_block": out, "to_port": 0},
            {"from_block": adder, "from_port": 2, "to_block": delay, "to_port": 0},
            {"from_block": delay, "from_port": 1, "to_block": adder, "to_port": 1},
        ]

    def _build_difference_preset(self) -> None:
        """y[n] = x[n] - x[n-1]: input splits to adder and delay→adder."""
        inp = self._gen_block_id()
        self.blocks[inp] = {"id": inp, "type": "input", "position": {"x": 120, "y": 220}}

        delay = self._gen_block_id()
        self.blocks[delay] = {"id": delay, "type": "delay", "position": {"x": 320, "y": 380}}

        adder = self._gen_block_id()
        self.blocks[adder] = {"id": adder, "type": "adder", "position": {"x": 460, "y": 220}, "signs": ["+", "-", "+"]}

        out = self._gen_block_id()
        self.blocks[out] = {"id": out, "type": "output", "position": {"x": 640, "y": 220}}

        self.connections = [
            {"from_block": inp, "from_port": 0, "to_block": adder, "to_port": 0},
            {"from_block": inp, "from_port": 0, "to_block": delay, "to_port": 0},
            {"from_block": delay, "from_port": 1, "to_block": adder, "to_port": 1},
            {"from_block": adder, "from_port": 2, "to_block": out, "to_port": 0},
        ]

    def _build_first_order_dt_preset(self) -> None:
        """y[n] = x[n] + 0.5·y[n-1]: adder → output, with delay→gain(0.5) feedback."""
        inp = self._gen_block_id()
        self.blocks[inp] = {"id": inp, "type": "input", "position": {"x": 100, "y": 220}}

        adder = self._gen_block_id()
        self.blocks[adder] = {"id": adder, "type": "adder", "position": {"x": 300, "y": 220}, "signs": ["+", "+", "+"]}

        out = self._gen_block_id()
        self.blocks[out] = {"id": out, "type": "output", "position": {"x": 600, "y": 220}}

        delay = self._gen_block_id()
        self.blocks[delay] = {"id": delay, "type": "delay", "position": {"x": 500, "y": 380}}

        gain = self._gen_block_id()
        self.blocks[gain] = {"id": gain, "type": "gain", "position": {"x": 340, "y": 380}, "value": 0.5}

        self.connections = [
            {"from_block": inp, "from_port": 0, "to_block": adder, "to_port": 0},
            {"from_block": adder, "from_port": 2, "to_block": out, "to_port": 0},
            {"from_block": adder, "from_port": 2, "to_block": delay, "to_port": 0},
            {"from_block": delay, "from_port": 1, "to_block": gain, "to_port": 1},
            {"from_block": gain, "from_port": 0, "to_block": adder, "to_port": 1},
        ]

    def _build_second_order_dt_preset(self) -> None:
        """y[n] = x[n] + 1.6·y[n-1] - 0.63·y[n-2].

        Clean horizontal layout:
          Forward:  x[n] → [adder1] ─────────── [adder2] → y[n]
                             ↑(+)                 ↑(-)
                           [gain1]◁             ▷[gain2]
                             ↑                    ↑
                           [delay1] ─────→ [delay2]
                      (from output tap) ──────────┘
        """
        inp = self._gen_block_id()
        self.blocks[inp] = {"id": inp, "type": "input", "position": {"x": 70, "y": 160}}

        adder1 = self._gen_block_id()
        self.blocks[adder1] = {"id": adder1, "type": "adder", "position": {"x": 240, "y": 160}, "signs": ["+", "+", "+"]}

        adder2 = self._gen_block_id()
        self.blocks[adder2] = {"id": adder2, "type": "adder", "position": {"x": 560, "y": 160}, "signs": ["+", "-", "+"]}

        out = self._gen_block_id()
        self.blocks[out] = {"id": out, "type": "output", "position": {"x": 740, "y": 160}}

        # Feedback: delay chain below forward path, gains bridge up to adders
        delay1 = self._gen_block_id()
        self.blocks[delay1] = {"id": delay1, "type": "delay", "position": {"x": 320, "y": 330}}

        delay2 = self._gen_block_id()
        self.blocks[delay2] = {"id": delay2, "type": "delay", "position": {"x": 490, "y": 330}}

        gain1 = self._gen_block_id()
        self.blocks[gain1] = {"id": gain1, "type": "gain", "position": {"x": 200, "y": 330}, "value": 1.6}

        gain2 = self._gen_block_id()
        self.blocks[gain2] = {"id": gain2, "type": "gain", "position": {"x": 640, "y": 330}, "value": 0.63}

        self.connections = [
            # Forward path
            {"from_block": inp, "from_port": 0, "to_block": adder1, "to_port": 0},
            {"from_block": adder1, "from_port": 2, "to_block": adder2, "to_port": 0},
            {"from_block": adder2, "from_port": 2, "to_block": out, "to_port": 0},
            # Output taps down to delay1: adder2 right → delay1 left (input)
            {"from_block": adder2, "from_port": 2, "to_block": delay1, "to_port": 0},
            # delay1 right branches: → gain1 left (RTL) and → delay2 left (LTR)
            {"from_block": delay1, "from_port": 1, "to_block": gain1, "to_port": 0},
            {"from_block": delay1, "from_port": 1, "to_block": delay2, "to_port": 0},
            # Feedback 1: gain1 right → adder1 bottom
            {"from_block": gain1, "from_port": 1, "to_block": adder1, "to_port": 1},
            # Feedback 2: delay2 right → gain2 left, gain2 right → adder2 bottom
            {"from_block": delay2, "from_port": 1, "to_block": gain2, "to_port": 0},
            {"from_block": gain2, "from_port": 1, "to_block": adder2, "to_port": 1},
        ]

    def _build_first_order_ct_preset(self) -> None:
        """dy/dt = -2y + x(t): input → adder → integrator → output, gain(-2) feedback."""
        inp = self._gen_block_id()
        self.blocks[inp] = {"id": inp, "type": "input", "position": {"x": 100, "y": 220}}

        adder = self._gen_block_id()
        self.blocks[adder] = {"id": adder, "type": "adder", "position": {"x": 300, "y": 220}, "signs": ["+", "-", "+"]}

        integ = self._gen_block_id()
        self.blocks[integ] = {"id": integ, "type": "integrator", "position": {"x": 460, "y": 220}}

        out = self._gen_block_id()
        self.blocks[out] = {"id": out, "type": "output", "position": {"x": 640, "y": 220}}

        gain = self._gen_block_id()
        self.blocks[gain] = {"id": gain, "type": "gain", "position": {"x": 380, "y": 380}, "value": 2.0}

        self.connections = [
            {"from_block": inp, "from_port": 0, "to_block": adder, "to_port": 0},
            {"from_block": adder, "from_port": 2, "to_block": integ, "to_port": 0},
            {"from_block": integ, "from_port": 1, "to_block": out, "to_port": 0},
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
        self._dfs_forward_paths(
            input_id, output_id, incoming, outgoing,
            [input_id], set([input_id]), forward_paths
        )
        for start_bid in block_ids:
            self._dfs_loops(
                start_bid, start_bid, outgoing,
                [start_bid], set([start_bid]), all_loops
            )

        if not forward_paths:
            raise ValueError("No forward path from Input to Output found.")

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
            Δ = 1 - Σ L_i + Σ (non-touching pairs) L_i·L_j - ...
            Cap at triples for performance (sufficient for most diagrams).
            """
            # Start with Δ = 1
            d_num = np.array([1.0])
            d_den = np.array([1.0])

            if not loops:
                return d_num, d_den

            # Precompute loop gains
            loop_gains = [compute_loop_gain(lp) for lp in loops]
            n_loops = len(loop_gains)

            # Subtract individual loop gains: - Σ L_i
            for ln, ld in loop_gains:
                d_num = self._psub(
                    self._pmul(d_num, ld),
                    self._pmul(ln, d_den)
                )
                d_den = self._pmul(d_den, ld)

            # Add non-touching pairs: + Σ L_i · L_j
            if n_loops >= 2 and n_loops <= 20:
                for i in range(n_loops):
                    for j in range(i + 1, n_loops):
                        if loops_are_non_touching(loops[i], loops[j]):
                            pair_num = self._pmul(loop_gains[i][0], loop_gains[j][0])
                            pair_den = self._pmul(loop_gains[i][1], loop_gains[j][1])
                            d_num = self._padd(
                                self._pmul(d_num, pair_den),
                                self._pmul(pair_num, d_den)
                            )
                            d_den = self._pmul(d_den, pair_den)

            # Subtract non-touching triples: - Σ L_i · L_j · L_k
            if n_loops >= 3 and n_loops <= 20:
                for i in range(n_loops):
                    for j in range(i + 1, n_loops):
                        if not loops_are_non_touching(loops[i], loops[j]):
                            continue
                        for k in range(j + 1, n_loops):
                            if (loops_are_non_touching(loops[i], loops[k]) and
                                    loops_are_non_touching(loops[j], loops[k])):
                                tri_num = self._pmul(
                                    self._pmul(loop_gains[i][0], loop_gains[j][0]),
                                    loop_gains[k][0]
                                )
                                tri_den = self._pmul(
                                    self._pmul(loop_gains[i][1], loop_gains[j][1]),
                                    loop_gains[k][1]
                                )
                                d_num = self._psub(
                                    self._pmul(d_num, tri_den),
                                    self._pmul(tri_num, d_den)
                                )
                                d_den = self._pmul(d_den, tri_den)

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

        return {
            "expression": f"H({op}) = {expression}",
            "domain_expression": domain_expr,
            "operator": op,
            "numerator": tf_num.tolist(),
            "denominator": tf_den.tolist(),
            "poles": poles_formatted,
            "zeros": zeros_formatted,
            "is_stable": is_stable,
            "stability": stability,
            "num_forward_paths": len(forward_paths),
            "num_loops": len(all_loops),
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

    def _dfs_loops(
        self, start: str, current: str,
        outgoing: Dict,
        path: List[str], visited: set,
        results: List[List[str]]
    ) -> None:
        """Find all loops starting from start via DFS."""
        for next_block in outgoing.get(current, []):
            if next_block == start and len(path) > 1:
                # Found a loop - normalize to avoid duplicates
                loop = list(path)
                # Normalize: rotate so smallest ID is first
                min_idx = loop.index(min(loop))
                normalized = loop[min_idx:] + loop[:min_idx]
                if normalized not in results:
                    results.append(normalized)
            elif next_block not in visited:
                visited.add(next_block)
                path.append(next_block)
                self._dfs_loops(start, next_block, outgoing, path, visited, results)
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
        Generate a direct-form-II transposed block diagram from TF coefficients.

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

        # Dynamic layout constants — scale with order, centered on 900×650 canvas
        canvas_w, canvas_h = 900, 650
        if order <= 2:
            spacing_x = 160
            delay_y_offset = 120
        elif order <= 4:
            spacing_x = 140
            delay_y_offset = 105
        else:
            spacing_x = 120
            delay_y_offset = 90

        # Auto-shrink if diagram won't fit horizontally
        total_w = (order + 4) * spacing_x
        if total_w > canvas_w - 120:
            spacing_x = max(110, (canvas_w - 120) // (order + 4))

        main_y = canvas_h // 2  # 800 — centered vertically

        # Create input
        inp = self._gen_block_id()
        self.blocks[inp] = {
            "id": inp, "type": "input",
            "position": {"x": 50, "y": main_y},
        }

        # Create output
        out_x = 50 + (order + 3) * spacing_x
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
                    "position": {"x": 300, "y": main_y},
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
        ff_signals = []  # list of (block_id, sign) to be summed

        # b0 * x[n]: direct path
        if abs(num_coeffs[0]) > 1e-10:
            if abs(abs(num_coeffs[0]) - 1.0) < 1e-10:
                sign = "+" if num_coeffs[0] > 0 else "-"
                ff_signals.append((inp, sign))
            else:
                g = self._gen_block_id()
                self.blocks[g] = {
                    "id": g, "type": "gain",
                    "position": {"x": 50 + spacing_x, "y": main_y - delay_y_offset - 65},
                    "value": abs(num_coeffs[0]),
                }
                connect(inp, g, 0)
                sign = "+" if num_coeffs[0] > 0 else "-"
                ff_signals.append((g, sign))

        # Delayed feedforward: bk * R^k * x
        prev_ff_delay = None
        for k in range(1, order + 1):
            d = self._gen_block_id()
            self.blocks[d] = {
                "id": d, "type": delay_type,
                "position": {"x": 50 + k * spacing_x, "y": main_y - delay_y_offset},
            }
            source = prev_ff_delay if prev_ff_delay is not None else inp
            connect(source, d, 0)
            prev_ff_delay = d

            if abs(num_coeffs[k]) > 1e-10:
                if abs(abs(num_coeffs[k]) - 1.0) < 1e-10:
                    sign = "+" if num_coeffs[k] > 0 else "-"
                    ff_signals.append((d, sign))
                else:
                    g = self._gen_block_id()
                    self.blocks[g] = {
                        "id": g, "type": "gain",
                        "position": {"x": 50 + k * spacing_x + 70, "y": main_y - delay_y_offset - 65},
                        "value": abs(num_coeffs[k]),
                    }
                    connect(d, g, 0)
                    sign = "+" if num_coeffs[k] > 0 else "-"
                    ff_signals.append((g, sign))

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

        fb_signals = []  # (block_id, sign) — block_id will be gain or delay
        fb_delays = []   # delay block ids in order, for chaining from output

        # We'll create the feedback blocks but connect them to the output later
        # (after we know which block is the output adder)

        fb_delay_blocks = []
        fb_gain_info = []  # (delay_block, gain_block_or_none, sign, coeff)

        for k in range(1, order + 1):
            d = self._gen_block_id()
            self.blocks[d] = {
                "id": d, "type": delay_type,
                "position": {"x": 50 + k * spacing_x, "y": main_y + delay_y_offset},
            }
            fb_delay_blocks.append(d)

            # Chain delays left-to-right
            if k >= 2:
                connect(fb_delay_blocks[k - 2], d, 0)

            if abs(den_coeffs[k]) > 1e-10:
                # Determine sign: we subtract den_coeffs[k]*R^k*y
                # So if den_coeffs[k] > 0, the adder sign should be "-"
                # If den_coeffs[k] < 0, sign is "+"
                if abs(abs(den_coeffs[k]) - 1.0) < 1e-10:
                    sign = "-" if den_coeffs[k] > 0 else "+"
                    fb_signals.append((d, sign))
                else:
                    g = self._gen_block_id()
                    self.blocks[g] = {
                        "id": g, "type": "gain",
                        "position": {
                            "x": 50 + k * spacing_x + 70,
                            "y": main_y + delay_y_offset + 65,
                        },
                        "value": abs(den_coeffs[k]),
                    }
                    connect(d, g, 0)
                    sign = "-" if den_coeffs[k] > 0 else "+"
                    fb_signals.append((g, sign))

        # --- Cascade-add all signals using 2-input adders ---
        all_signals = ff_signals + fb_signals

        if len(all_signals) == 0:
            # Degenerate: just wire input to output
            connect(inp, out, 0)
            return

        if len(all_signals) == 1:
            # Single signal path — just one wire (possibly with sign inversion)
            sig_id, sig_sign = all_signals[0]
            if sig_sign == "-":
                # Need a gain of -1
                neg = self._gen_block_id()
                self.blocks[neg] = {
                    "id": neg, "type": "gain",
                    "position": {"x": out_x - spacing_x, "y": main_y},
                    "value": -1.0,
                }
                connect(sig_id, neg, 0)
                connect(neg, out, 0)
            else:
                connect(sig_id, out, 0)

            # Connect feedback delays from output
            if fb_delay_blocks:
                connect(sig_id, fb_delay_blocks[0], 0)
            return

        # Build a cascade of 2-input adders
        adder_x_start = 50 + (order + 1) * spacing_x
        adder_spacing = max(100, int(spacing_x * 0.6))
        adders = []

        for i in range(len(all_signals) - 1):
            adder_id = self._gen_block_id()
            adder_x = adder_x_start + (i * adder_spacing)
            self.blocks[adder_id] = {
                "id": adder_id, "type": "adder",
                "position": {"x": adder_x, "y": main_y},
                "signs": ["+", "+", "+"],  # default, will be set below
            }
            adders.append(adder_id)

        # Wire the cascade
        # First adder: port 0 (left) = first signal, port 1 (bottom) = second signal
        sig0_id, sig0_sign = all_signals[0]
        sig1_id, sig1_sign = all_signals[1]

        connect(sig0_id, adders[0], 0)
        connect(sig1_id, adders[0], 1)
        self.blocks[adders[0]]["signs"] = [sig0_sign, sig1_sign, "+"]

        # Subsequent adders: port 0 (left) = previous adder output, port 1 (bottom) = next signal
        for i in range(1, len(adders)):
            sig_id, sig_sign = all_signals[i + 1]
            connect(adders[i - 1], adders[i], 0)
            connect(sig_id, adders[i], 1)
            self.blocks[adders[i]]["signs"] = ["+", sig_sign, "+"]

        # Last adder output → output block
        last_adder = adders[-1]
        connect(last_adder, out, 0)

        # Connect feedback delay chain from the last adder output (= y[n])
        if fb_delay_blocks:
            connect(last_adder, fb_delay_blocks[0], 0)

        # Reposition output to the right of the last adder
        last_adder_x = self.blocks[last_adder]["position"]["x"]
        self.blocks[out]["position"]["x"] = last_adder_x + spacing_x

        # Center diagram on canvas
        self._center_diagram()

    def _center_diagram(self) -> None:
        """Center all blocks within the 900×650 canvas."""
        if not self.blocks:
            return
        cw, ch = 900, 650
        xs = [b["position"]["x"] for b in self.blocks.values()]
        ys = [b["position"]["y"] for b in self.blocks.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        offset_x = (cw - (max_x - min_x)) / 2 - min_x
        offset_y = (ch - (max_y - min_y)) / 2 - min_y

        # Clamp to keep within canvas with margins
        offset_x = max(70 - min_x, min(offset_x, cw - 70 - max_x))
        offset_y = max(50 - min_y, min(offset_y, ch - 50 - max_y))

        for b in self.blocks.values():
            b["position"]["x"] += offset_x
            b["position"]["y"] += offset_y

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
            t_imp, imp_resp = impulse(sys, N=500)
            t_step, step_resp = step(sys, N=500)
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
        """Apply IIR filter (difference equation) to signal x."""
        N = len(x)
        y = np.zeros(N)
        nb = len(b)
        na = len(a)
        for n in range(N):
            # Feedforward
            for k in range(min(nb, n + 1)):
                y[n] += b[k] * x[n - k]
            # Feedback
            for k in range(1, min(na, n + 1)):
                y[n] -= a[k] * y[n - k]
            if abs(a[0]) > 1e-12:
                y[n] /= a[0]
        return y

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
