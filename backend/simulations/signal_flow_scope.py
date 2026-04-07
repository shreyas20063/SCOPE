"""
Signal Flow Scope — interactive signal analysis tool.

Import block diagrams from the Block Diagram Builder (or load presets),
apply input signals, and probe any node to visualize signal propagation.

Key features:
- Import diagrams via JSON or load built-in presets
- Compute transfer function from input to every reachable node (Mason's formula)
- Generate input signals: impulse, step, sinusoid, ramp, square, sawtooth, triangle, chirp, noise
- Place up to 6 probes on nodes, view time-domain signals with statistics
- Signal Flow Graph (SFG) visualization data
- Raw signal data output for frontend-driven plot rendering
"""

import copy
import re
import numpy as np
from collections import deque
from itertools import combinations
from typing import Any, Dict, List, Optional, Tuple
from .base_simulator import BaseSimulator


_SUPER_DIGITS = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")

def _superscript(n: int) -> str:
    """Convert integer to Unicode superscript: 2 -> '²', 13 -> '¹³'."""
    return str(n).translate(_SUPER_DIGITS)


class SignalFlowScopeSimulator(BaseSimulator):
    """
    Signal Flow Scope — oscilloscope for block diagrams.

    Users import a diagram, choose an input signal, and probe nodes
    to see the signal at each point in the system.
    """

    # Probe colors (up to 6 probes)
    PROBE_COLORS = [
        "#ef4444",  # red
        "#3b82f6",  # blue
        "#10b981",  # green
        "#f59e0b",  # amber
        "#8b5cf6",  # purple
        "#ec4899",  # pink
    ]

    MAX_PROBES = 6

    # Virtual sample rate for DT frequency mapping.  Keeps digital frequency
    # independent of num_samples (the observation window length).  With
    # DT_SAMPLE_RATE = 100 the freq slider's 50 Hz max maps to Nyquist.
    DT_SAMPLE_RATE = 100

    # Plot styling
    COLORS = {
        "input": "#14b8a6",  # teal for input signal
        "grid": "rgba(148, 163, 184, 0.15)",
        "text": "#e2e8f0",
        "zero": "rgba(148, 163, 184, 0.3)",
    }

    PARAMETER_SCHEMA = {
        "input_type": {
            "type": "select",
            "label": "Input Signal",
            "options": [
                {"label": "Impulse", "value": "impulse"},
                {"label": "Step", "value": "step"},
                {"label": "Sinusoid", "value": "sinusoid"},
                {"label": "Ramp", "value": "ramp"},
                {"label": "Square Wave", "value": "square"},
                {"label": "Sawtooth", "value": "sawtooth"},
                {"label": "Triangle", "value": "triangle"},
                {"label": "Chirp", "value": "chirp"},
                {"label": "White Noise", "value": "white_noise"},
            ],
            "default": "impulse",
        },
        "input_freq": {
            "type": "slider",
            "label": "Frequency",
            "min": 0.01,
            "max": 50.0,
            "step": 0.01,
            "default": 1.0,
            "unit": "Hz",
        },
        "input_amplitude": {
            "type": "slider",
            "label": "Amplitude",
            "min": 0.1,
            "max": 10.0,
            "step": 0.1,
            "default": 5.0,
        },
        "num_samples": {
            "type": "slider",
            "label": "Samples",
            "min": 20,
            "max": 500,
            "step": 10,
            "default": 100,
        },
        "duty_cycle": {
            "type": "slider",
            "label": "Duty Cycle",
            "min": 0.1,
            "max": 0.9,
            "step": 0.05,
            "default": 0.5,
        },
        "chirp_end_freq": {
            "type": "slider",
            "label": "End Frequency",
            "min": 1.0,
            "max": 100.0,
            "step": 1.0,
            "default": 20.0,
            "unit": "Hz",
        },
    }

    DEFAULT_PARAMS = {
        "input_type": "impulse",
        "input_freq": 1.0,
        "input_amplitude": 5.0,
        "num_samples": 100,
        "duty_cycle": 0.5,
        "chirp_end_freq": 20.0,
    }

    HUB_SLOTS = ['control']

    # Built-in diagram presets
    PRESETS = {
        "unity_feedback": {
            "name": "Unity Feedback",
            "description": "G(s) with unity negative feedback: Y = G/(1+G) · X",
            "system_type": "ct",
            "blocks": {
                "b_in": {"id": "b_in", "type": "input", "position": {"x": 50, "y": 200}},
                "b_add": {"id": "b_add", "type": "adder", "position": {"x": 200, "y": 200},
                          "signs": ["+", "-"]},
                "b_gain": {"id": "b_gain", "type": "gain", "position": {"x": 380, "y": 200},
                           "value": 2.0},
                "b_junc": {"id": "b_junc", "type": "junction", "position": {"x": 530, "y": 200}},
                "b_out": {"id": "b_out", "type": "output", "position": {"x": 680, "y": 200}},
            },
            "connections": [
                {"from_block": "b_in", "to_block": "b_add", "from_port": 1, "to_port": 0},
                {"from_block": "b_add", "to_block": "b_gain", "from_port": 1, "to_port": 0},
                {"from_block": "b_gain", "to_block": "b_junc", "from_port": 1, "to_port": 0},
                {"from_block": "b_junc", "to_block": "b_out", "from_port": 1, "to_port": 0},
                {"from_block": "b_junc", "to_block": "b_add", "from_port": 1, "to_port": 1},
            ],
        },
        "cascade": {
            "name": "Cascade System",
            "description": "Two gains in series: Y = G₁·G₂ · X",
            "system_type": "dt",
            "blocks": {
                "b_in": {"id": "b_in", "type": "input", "position": {"x": 50, "y": 200}},
                "b_g1": {"id": "b_g1", "type": "gain", "position": {"x": 230, "y": 200}, "value": 3.0},
                "b_g2": {"id": "b_g2", "type": "gain", "position": {"x": 430, "y": 200}, "value": 0.5},
                "b_out": {"id": "b_out", "type": "output", "position": {"x": 630, "y": 200}},
            },
            "connections": [
                {"from_block": "b_in", "to_block": "b_g1", "from_port": 1, "to_port": 0},
                {"from_block": "b_g1", "to_block": "b_g2", "from_port": 1, "to_port": 0},
                {"from_block": "b_g2", "to_block": "b_out", "from_port": 1, "to_port": 0},
            ],
        },
        "second_order_dt": {
            "name": "Second-Order DT",
            "description": "y[n] = x[n] + 1.5·y[n-1] - 0.7·y[n-2]",
            "system_type": "dt",
            "blocks": {
                "b_in": {"id": "b_in", "type": "input", "position": {"x": 50, "y": 200}},
                "b_add": {"id": "b_add", "type": "adder", "position": {"x": 230, "y": 200},
                          "signs": ["+", "+", "-"]},
                "b_junc": {"id": "b_junc", "type": "junction", "position": {"x": 400, "y": 200}},
                "b_out": {"id": "b_out", "type": "output", "position": {"x": 570, "y": 200}},
                "b_d1": {"id": "b_d1", "type": "delay", "position": {"x": 400, "y": 340}},
                "b_g1": {"id": "b_g1", "type": "gain", "position": {"x": 280, "y": 340}, "value": 1.5},
                "b_d2": {"id": "b_d2", "type": "delay", "position": {"x": 400, "y": 470}},
                "b_g2": {"id": "b_g2", "type": "gain", "position": {"x": 280, "y": 470}, "value": 0.7},
            },
            "connections": [
                {"from_block": "b_in", "to_block": "b_add", "from_port": 1, "to_port": 0},
                {"from_block": "b_add", "to_block": "b_junc", "from_port": 1, "to_port": 0},
                {"from_block": "b_junc", "to_block": "b_out", "from_port": 1, "to_port": 0},
                {"from_block": "b_junc", "to_block": "b_d1", "from_port": 1, "to_port": 0},
                {"from_block": "b_d1", "to_block": "b_g1", "from_port": 1, "to_port": 0},
                {"from_block": "b_g1", "to_block": "b_add", "from_port": 1, "to_port": 1},
                {"from_block": "b_d1", "to_block": "b_d2", "from_port": 1, "to_port": 0},
                {"from_block": "b_d2", "to_block": "b_g2", "from_port": 1, "to_port": 0},
                {"from_block": "b_g2", "to_block": "b_add", "from_port": 1, "to_port": 2},
            ],
        },
        "first_order_lowpass": {
            "name": "First-Order Lowpass",
            "description": "y[n] = 0.3·x[n] + 0.7·y[n-1]",
            "system_type": "dt",
            "blocks": {
                "b_in": {"id": "b_in", "type": "input", "position": {"x": 50, "y": 200}},
                "b_g_in": {"id": "b_g_in", "type": "gain", "position": {"x": 200, "y": 200}, "value": 0.3},
                "b_add": {"id": "b_add", "type": "adder", "position": {"x": 370, "y": 200},
                          "signs": ["+", "+"]},
                "b_junc": {"id": "b_junc", "type": "junction", "position": {"x": 530, "y": 200}},
                "b_out": {"id": "b_out", "type": "output", "position": {"x": 680, "y": 200}},
                "b_d1": {"id": "b_d1", "type": "delay", "position": {"x": 530, "y": 340}},
                "b_g_fb": {"id": "b_g_fb", "type": "gain", "position": {"x": 370, "y": 340}, "value": 0.7},
            },
            "connections": [
                {"from_block": "b_in", "to_block": "b_g_in", "from_port": 1, "to_port": 0},
                {"from_block": "b_g_in", "to_block": "b_add", "from_port": 1, "to_port": 0},
                {"from_block": "b_add", "to_block": "b_junc", "from_port": 1, "to_port": 0},
                {"from_block": "b_junc", "to_block": "b_out", "from_port": 1, "to_port": 0},
                {"from_block": "b_junc", "to_block": "b_d1", "from_port": 1, "to_port": 0},
                {"from_block": "b_d1", "to_block": "b_g_fb", "from_port": 1, "to_port": 0},
                {"from_block": "b_g_fb", "to_block": "b_add", "from_port": 1, "to_port": 1},
            ],
        },
    }

    def __init__(self, simulation_id: str):
        """Initialize signal flow scope simulator."""
        super().__init__(simulation_id)
        # Imported diagram
        self.blocks: Dict[str, Dict[str, Any]] = {}
        self.connections: List[Dict[str, Any]] = []
        self.system_type: str = "dt"

        # Probes
        self.probes: List[Dict[str, Any]] = []
        self._next_probe_id: int = 0

        # Computed data
        self._node_tfs: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}
        self._node_signals: Dict[str, Dict[str, Any]] = {}
        self._node_labels: Dict[str, str] = {}
        self._error: Optional[str] = None

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        """Initialize with default or given parameters."""
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            self.parameters[name] = self._validate_param(name, value)
        self._initialized = True

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        """Update a parameter and recompute signals."""
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)

        # Recompute signals when input params change
        if name in ("input_type", "input_freq", "input_amplitude", "num_samples", "duty_cycle", "chirp_end_freq"):
            if self.blocks:
                self._compute_probed_signals()
                # Also recompute output signal
                for bid, block in self.blocks.items():
                    if block.get("type") == "output" and bid in self._node_tfs:
                        self._compute_signal_for_node(bid)

        return self.get_state()

    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle custom actions."""
        action_map = {
            "import_diagram": self._action_import_diagram,
            "load_preset": self._action_load_preset,
            "add_probe": self._action_add_probe,
            "remove_probe": self._action_remove_probe,
            "clear_probes": self._action_clear_probes,
            "toggle_probe": self._action_toggle_probe,
            "probe_all": self._action_probe_all,
        }

        handler = action_map.get(action)
        if handler:
            return handler(params)

        return self.get_state()

    # =========================================================================
    # Actions
    # =========================================================================

    def _action_import_diagram(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Import a block diagram from JSON data."""
        blocks = params.get("blocks", {})
        connections = params.get("connections", [])
        system_type = params.get("system_type", "dt")

        if not blocks:
            self._error = "No blocks in diagram data."
            return self.get_state()

        # Validate block count
        if len(blocks) > 50:
            self._error = "Diagram too large (max 50 blocks)."
            return self.get_state()

        self.blocks = copy.deepcopy(blocks)
        self.connections = copy.deepcopy(connections)
        self.system_type = system_type
        self.probes = []
        self._next_probe_id = 0
        self._error = None

        # Compute node labels
        self._compute_node_labels()

        # Compute TFs from input to every reachable node
        try:
            self._compute_all_node_tfs()
        except Exception as e:
            self._error = f"Failed to compute transfer functions: {str(e)}"

        # Pre-compute output signal so it's available immediately
        for bid, block in self.blocks.items():
            if block.get("type") == "output" and bid in self._node_tfs:
                self._compute_signal_for_node(bid)

        return self.get_state()

    def _action_load_preset(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Load a built-in preset diagram."""
        preset_id = params.get("preset_id", "")
        preset = self.PRESETS.get(preset_id)
        if not preset:
            self._error = f"Unknown preset: {preset_id}"
            return self.get_state()

        return self._action_import_diagram({
            "blocks": copy.deepcopy(preset["blocks"]),
            "connections": copy.deepcopy(preset["connections"]),
            "system_type": preset["system_type"],
        })

    def _action_probe_all(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Probe all probeable nodes (up to MAX_PROBES)."""
        self.probes = []
        self._next_probe_id = 0
        count = 0
        for node_id in self._node_tfs:
            if count >= self.MAX_PROBES:
                break
            self._next_probe_id += 1
            color = self.PROBE_COLORS[count % len(self.PROBE_COLORS)]
            self.probes.append({
                "id": f"probe_{self._next_probe_id}",
                "node_id": node_id,
                "color": color,
                "label": self._node_labels.get(node_id, node_id),
            })
            self._compute_signal_for_node(node_id)
            count += 1
        return self.get_state()

    def _action_add_probe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a probe at a specific node."""
        node_id = params.get("node_id")
        if not node_id or node_id not in self.blocks:
            return self.get_state()

        # Check if already probed
        if any(p["node_id"] == node_id for p in self.probes):
            return self.get_state()

        if len(self.probes) >= self.MAX_PROBES:
            return self.get_state()

        self._next_probe_id += 1
        color = self.PROBE_COLORS[len(self.probes) % len(self.PROBE_COLORS)]
        probe = {
            "id": f"probe_{self._next_probe_id}",
            "node_id": node_id,
            "color": color,
            "label": self._node_labels.get(node_id, node_id),
        }
        self.probes.append(probe)

        # Compute signal for this probe
        self._compute_signal_for_node(node_id)

        return self.get_state()

    def _action_remove_probe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a probe by ID or node_id."""
        probe_id = params.get("probe_id")
        node_id = params.get("node_id")

        self.probes = [
            p for p in self.probes
            if p["id"] != probe_id and p["node_id"] != node_id
        ]

        return self.get_state()

    def _action_clear_probes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove all probes."""
        self.probes = []
        self._node_signals = {}
        return self.get_state()

    def _action_toggle_probe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Toggle probe on/off at a node."""
        node_id = params.get("node_id")
        if not node_id or node_id not in self.blocks:
            return self.get_state()

        # Input/output nodes are not probeable (already shown by default)
        btype = self.blocks[node_id].get("type")
        if btype in ("input", "output"):
            return self.get_state()

        existing = [p for p in self.probes if p["node_id"] == node_id]
        if existing:
            return self._action_remove_probe({"node_id": node_id})
        else:
            return self._action_add_probe({"node_id": node_id})

    # =========================================================================
    # Node label computation
    # =========================================================================

    def _compute_node_labels(self) -> None:
        """Compute human-readable labels for each node.

        Signal-point blocks (input, output, adder, junction) get SFG-style
        labels.  TF blocks keep descriptive labels for probe display.
        """
        self._node_labels = {}
        var_idx = 0
        for bid, block in self.blocks.items():
            btype = block.get("type", "")
            if btype == "input":
                label = "x[n]" if self.system_type == "dt" else "x(t)"
            elif btype == "output":
                label = "y[n]" if self.system_type == "dt" else "y(t)"
            elif btype == "adder":
                var_idx += 1
                label = f"e{self._subscript(var_idx)}"
            elif btype == "junction":
                var_idx += 1
                label = f"s{self._subscript(var_idx)}"
            elif btype == "gain":
                val = block.get("value", 1.0)
                label = f"Gain({val})"
            elif btype == "delay":
                label = "R (Delay)"
            elif btype == "integrator":
                label = "A (Integrator)"
            elif btype == "custom_tf":
                label = block.get("label", "H(z)")
            else:
                label = bid
            self._node_labels[bid] = label

    # =========================================================================
    # Transfer function computation (Mason's Gain Formula)
    # =========================================================================

    def _find_input_block(self) -> Optional[str]:
        """Find the input block ID."""
        for bid, block in self.blocks.items():
            if block.get("type") == "input":
                return bid
        return None

    def _build_adjacency(self) -> Tuple[Dict, Dict]:
        """Build incoming/outgoing adjacency maps from connections."""
        block_ids = list(self.blocks.keys())
        incoming: Dict[str, List[Dict]] = {bid: [] for bid in block_ids}
        outgoing: Dict[str, List[str]] = {bid: [] for bid in block_ids}

        for conn in self.connections:
            fb, tb = conn.get("from_block"), conn.get("to_block")
            if fb in self.blocks and tb in self.blocks:
                incoming[tb].append({"from": fb, "to_port": conn.get("to_port", 0)})
                if tb not in outgoing[fb]:
                    outgoing[fb].append(tb)

        return incoming, outgoing

    def _find_reachable_nodes(self, start: str, outgoing: Dict[str, List[str]]) -> List[str]:
        """Find all nodes reachable from start using BFS."""
        visited = set()
        stack = [start]
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            for target in outgoing.get(node, []):
                stack.append(target)
        return list(visited)

    def _block_tf(self, bid: str) -> Tuple[np.ndarray, np.ndarray]:
        """Return (num, den) polynomials for a block (low-power-first)."""
        block = self.blocks[bid]
        btype = block.get("type", "")
        if btype == "gain":
            val = block.get("value", 1.0)
            return (np.array([float(val)]), np.array([1.0]))
        elif btype in ("delay", "integrator"):
            return (np.array([0.0, 1.0]), np.array([1.0]))
        elif btype == "custom_tf":
            return (
                np.array(block.get("num_coeffs", [1.0]), dtype=float),
                np.array(block.get("den_coeffs", [1.0]), dtype=float),
            )
        else:
            return (np.array([1.0]), np.array([1.0]))

    def _compute_all_node_tfs(self) -> None:
        """Compute TF from input to every reachable node using Mason's formula."""
        self._node_tfs = {}
        input_id = self._find_input_block()
        if not input_id:
            return

        incoming, outgoing = self._build_adjacency()
        reachable = self._find_reachable_nodes(input_id, outgoing)

        # Find all loops in the entire graph (needed for all Mason computations)
        block_ids = list(self.blocks.keys())
        all_loops: List[List[str]] = []
        seen_loops: set = set()
        for start_bid in block_ids:
            self._dfs_loops(
                start_bid, start_bid, outgoing,
                [start_bid], {start_bid}, all_loops, seen_loops
            )

        # For each reachable node, compute TF from input
        for node_id in reachable:
            if node_id == input_id:
                self._node_tfs[node_id] = (np.array([1.0]), np.array([1.0]))
                continue

            try:
                tf = self._compute_node_tf(
                    input_id, node_id, incoming, outgoing, all_loops
                )
                self._node_tfs[node_id] = tf
            except Exception:
                # If TF computation fails for a node, skip it
                pass

    def _compute_node_tf(
        self,
        input_id: str,
        target_id: str,
        incoming: Dict,
        outgoing: Dict,
        all_loops: List[List[str]],
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Compute TF from input to a specific target node using Mason's formula."""
        # Build connection lookup: (from_block, to_block) -> to_port
        # Uses last matching connection for each pair (handles multi-wire edge case)
        conn_port_map: Dict[Tuple[str, str], int] = {}
        for conn in self.connections:
            key = (conn["from_block"], conn["to_block"])
            conn_port_map[key] = conn.get("to_port", 0)

        # Find forward paths from input to target
        forward_paths: List[List[str]] = []
        self._dfs_forward_paths(
            input_id, target_id, outgoing,
            [input_id], {input_id}, forward_paths
        )

        if not forward_paths:
            return (np.array([0.0]), np.array([1.0]))

        # Compute path gains
        def compute_path_gain(path: List[str]) -> Tuple[np.ndarray, np.ndarray]:
            num = np.array([1.0])
            den = np.array([1.0])
            for i, bid in enumerate(path):
                block = self.blocks[bid]
                if block.get("type") == "adder" and i > 0:
                    prev_bid = path[i - 1]
                    port_idx = conn_port_map.get((prev_bid, bid), 0)
                    signs = block.get("signs", ["+", "+", "+"])
                    if port_idx < len(signs) and signs[port_idx] == "-":
                        num = self._pscale(num, -1.0)

                if block.get("type") not in ("input", "output", "adder", "junction"):
                    bn, bd = self._block_tf(bid)
                    num = self._pmul(num, bn)
                    den = self._pmul(den, bd)

            return (num, den)

        def compute_loop_gain(loop: List[str]) -> Tuple[np.ndarray, np.ndarray]:
            num = np.array([1.0])
            den = np.array([1.0])
            for i, bid in enumerate(loop):
                block = self.blocks[bid]
                if block.get("type") == "adder":
                    prev_bid = loop[i - 1] if i > 0 else loop[-1]
                    port_idx = conn_port_map.get((prev_bid, bid), 0)
                    signs = block.get("signs", ["+", "+", "+"])
                    if port_idx < len(signs) and signs[port_idx] == "-":
                        num = self._pscale(num, -1.0)

                if block.get("type") not in ("input", "output", "adder", "junction"):
                    bn, bd = self._block_tf(bid)
                    num = self._pmul(num, bn)
                    den = self._pmul(den, bd)

            return (num, den)

        def loops_are_non_touching(loop1: List[str], loop2: List[str]) -> bool:
            return set(loop1).isdisjoint(set(loop2))

        def compute_delta(loops: List[List[str]]) -> Tuple[np.ndarray, np.ndarray]:
            """Compute graph determinant Δ from a set of loops.
            Δ = 1 - ΣL_i + Σ(non-touching pairs)L_i·L_j - Σ(triples) + ...
            """
            d_num = np.array([1.0])
            d_den = np.array([1.0])

            if not loops:
                return d_num, d_den

            # Precompute loop gains and node sets
            loop_gains = [compute_loop_gain(lp) for lp in loops]
            n_loops = len(loop_gains)
            loop_sets = [set(lp) for lp in loops]

            for k in range(1, n_loops + 1):
                # Safety cap for very large diagrams
                if n_loops > 20 and k > 4:
                    break
                sign_positive = (k % 2 == 0)  # k=1: subtract, k=2: add
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

                    if not all_non_touching:
                        continue

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

            return (d_num, d_den)

        def path_touches_loop(path: List[str], loop: List[str]) -> bool:
            return not set(path).isdisjoint(set(loop))

        # Compute full delta
        delta_num, delta_den = compute_delta(all_loops)

        # Compute numerator: sum of P_k * delta_k
        total_num = np.array([0.0])
        total_den = np.array([1.0])
        for fp in forward_paths:
            p_n, p_d = compute_path_gain(fp)
            non_touching = [lp for lp in all_loops if not path_touches_loop(fp, lp)]
            cofactor_num, cofactor_den = compute_delta(non_touching)

            term_num = self._pmul(p_n, cofactor_num)
            term_den = self._pmul(p_d, cofactor_den)

            total_num = self._padd(
                self._pmul(total_num, term_den),
                self._pmul(term_num, total_den)
            )
            total_den = self._pmul(total_den, term_den)

        # TF = (total_num * delta_den) / (total_den * delta_num)
        tf_num = self._pmul(total_num, delta_den)
        tf_den = self._pmul(total_den, delta_num)

        tf_num = self._clean_poly(tf_num)
        tf_den = self._clean_poly(tf_den)

        # Normalize
        if len(tf_den) > 0 and abs(tf_den[0]) > 1e-12:
            scale = tf_den[0]
            tf_num = tf_num / scale
            tf_den = tf_den / scale

        return (tf_num, tf_den)

    # =========================================================================
    # Graph traversal (DFS)
    # =========================================================================

    def _dfs_forward_paths(
        self, current: str, target: str,
        outgoing: Dict,
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
                self._dfs_forward_paths(
                    next_block, target, outgoing,
                    path, visited, results
                )
                path.pop()
                if next_block != target:
                    visited.discard(next_block)

    @staticmethod
    def _block_sort_key(bid: str) -> Tuple:
        """Numeric sort key for block IDs."""
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
                loop = list(path)
                min_idx = loop.index(min(loop, key=self._block_sort_key))
                normalized = loop[min_idx:] + loop[:min_idx]
                key = tuple(normalized)
                if key not in seen_loops:
                    seen_loops.add(key)
                    results.append(normalized)
            elif next_block not in visited:
                visited.add(next_block)
                path.append(next_block)
                self._dfs_loops(
                    start, next_block, outgoing, path, visited,
                    results, seen_loops
                )
                path.pop()
                visited.discard(next_block)

    # =========================================================================
    # Polynomial arithmetic (low-power-first)
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

    def _clean_poly(self, coeffs: np.ndarray) -> np.ndarray:
        """Remove trailing near-zero coefficients (low-power-first)."""
        if len(coeffs) == 0:
            return np.array([0.0])
        max_abs = max(abs(coeffs)) if len(coeffs) > 0 else 0
        threshold = 1e-10 * max_abs if max_abs > 0 else 1e-10
        last_nonzero = 0
        for i in range(len(coeffs) - 1, -1, -1):
            if abs(coeffs[i]) > threshold:
                last_nonzero = i
                break
        result = coeffs[:last_nonzero + 1]
        return result if len(result) > 0 else np.array([0.0])

    # =========================================================================
    # Domain conversion
    # =========================================================================

    def _operator_to_z(
        self, num: np.ndarray, den: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Convert R-domain (R=z^{-1}) to z-domain (high-power-first).

        Multiplies N(R) and D(R) by z^k where k = max(num_order, den_order)
        to clear negative powers of z. Strips leading zeros for np.roots
        and scipy.signal compatibility.
        """
        den_order = len(den) - 1
        num_order = len(num) - 1
        k = max(den_order, num_order)

        z_num = np.zeros(k + 1)
        z_den = np.zeros(k + 1)
        z_num[:len(num)] = num
        z_den[:len(den)] = den

        # Strip leading zeros: prevents np.roots from misinterpreting
        # polynomial degree and scipy.signal from length-mismatch errors
        z_num = np.trim_zeros(z_num, 'f')
        z_den = np.trim_zeros(z_den, 'f')

        if len(z_num) == 0:
            z_num = np.array([0.0])
        if len(z_den) == 0:
            z_den = np.array([1.0])

        return z_num, z_den

    def _operator_to_s(
        self, num: np.ndarray, den: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Convert A-domain (A=1/s) to s-domain (high-power-first).

        Same logic as R→z but with A = 1/s. Strips leading zeros.
        """
        den_order = len(den) - 1
        num_order = len(num) - 1
        k = max(den_order, num_order)

        s_num = np.zeros(k + 1)
        s_den = np.zeros(k + 1)
        s_num[:len(num)] = num
        s_den[:len(den)] = den

        # Strip leading zeros for np.roots and scipy.signal compatibility
        s_num = np.trim_zeros(s_num, 'f')
        s_den = np.trim_zeros(s_den, 'f')

        if len(s_num) == 0:
            s_num = np.array([0.0])
        if len(s_den) == 0:
            s_den = np.array([1.0])

        return s_num, s_den

    # =========================================================================
    # Signal generation and propagation
    # =========================================================================

    def _generate_input_signal(self) -> Tuple[np.ndarray, np.ndarray]:
        """Generate the input signal based on current parameters.

        Returns:
            (t, signal) tuple where t is time/sample indices and signal is amplitudes.
        """
        input_type = self.parameters.get("input_type", "impulse")
        amplitude = float(self.parameters.get("input_amplitude", 1.0))
        num_samples = int(self.parameters.get("num_samples", 100))
        freq = float(self.parameters.get("input_freq", 1.0))
        duty = float(self.parameters.get("duty_cycle", 0.5))
        chirp_end = float(self.parameters.get("chirp_end_freq", 20.0))

        if self.system_type == "dt":
            n = np.arange(num_samples)
            signal = self._make_signal_dt(input_type, n, num_samples, amplitude, freq, duty, chirp_end)
            return (n, signal)
        else:
            t_end = self._estimate_ct_time_range()
            t = np.linspace(0, t_end, num_samples)
            signal = self._make_signal_ct(input_type, t, t_end, amplitude, freq, duty, chirp_end)
            return (t, signal)

    def _make_signal_dt(
        self, sig_type: str, n: np.ndarray, N: int,
        amp: float, freq: float, duty: float, chirp_end: float,
    ) -> np.ndarray:
        """Generate a discrete-time signal.

        Frequency-dependent signals use DT_SAMPLE_RATE (not N) so that
        digital frequency is independent of the observation window length.
        With DT_SAMPLE_RATE=100, freq (Hz) maps to digital frequency
        f_d = freq/100 cycles/sample, and the slider max of 50 Hz = Nyquist.
        """
        fs = self.DT_SAMPLE_RATE
        if sig_type == "impulse":
            s = np.zeros(N); s[0] = amp
        elif sig_type == "step":
            s = np.ones(N) * amp
        elif sig_type == "sinusoid":
            s = amp * np.sin(2 * np.pi * freq * n / fs)
        elif sig_type == "ramp":
            s = amp * n / N
        elif sig_type == "square":
            phase = (freq * n / fs) % 1.0
            s = np.where(phase < duty, amp, -amp)
        elif sig_type == "sawtooth":
            phase = (freq * n / fs) % 1.0
            s = amp * (2.0 * phase - 1.0)
        elif sig_type == "triangle":
            phase = (freq * n / fs) % 1.0
            s = amp * (2.0 * np.abs(2.0 * phase - 1.0) - 1.0)
        elif sig_type == "chirp":
            t_norm = n / max(N - 1, 1)
            inst_freq = freq + (chirp_end - freq) * t_norm
            phase_acc = 2 * np.pi * np.cumsum(inst_freq / fs)
            s = amp * np.sin(phase_acc)
        elif sig_type == "white_noise":
            rng = np.random.default_rng(42)
            s = amp * rng.standard_normal(N)
        else:
            s = np.zeros(N); s[0] = amp
        return s

    def _make_signal_ct(
        self, sig_type: str, t: np.ndarray, t_end: float,
        amp: float, freq: float, duty: float, chirp_end: float,
    ) -> np.ndarray:
        """Generate a continuous-time signal."""
        dt = t[1] - t[0] if len(t) > 1 else 0.01
        if sig_type == "impulse":
            s = np.zeros_like(t); s[0] = amp / dt
        elif sig_type == "step":
            s = np.ones_like(t) * amp
        elif sig_type == "sinusoid":
            s = amp * np.sin(2 * np.pi * freq * t)
        elif sig_type == "ramp":
            s = amp * t / t_end
        elif sig_type == "square":
            phase = (freq * t) % 1.0
            s = np.where(phase < duty, amp, -amp)
        elif sig_type == "sawtooth":
            phase = (freq * t) % 1.0
            s = amp * (2.0 * phase - 1.0)
        elif sig_type == "triangle":
            phase = (freq * t) % 1.0
            s = amp * (2.0 * np.abs(2.0 * phase - 1.0) - 1.0)
        elif sig_type == "chirp":
            inst_freq = freq + (chirp_end - freq) * t / t_end
            phase_acc = 2 * np.pi * np.cumsum(inst_freq) * dt
            s = amp * np.sin(phase_acc)
        elif sig_type == "white_noise":
            rng = np.random.default_rng(42)
            s = amp * rng.standard_normal(len(t))
        else:
            s = np.zeros_like(t); s[0] = amp / dt
        return s

    def _estimate_ct_time_range(self) -> float:
        """Estimate appropriate time range for CT system from pole locations."""
        t_end = 10.0
        all_poles = []
        for node_id, (num, den) in self._node_tfs.items():
            s_num, s_den = self._operator_to_s(num, den)
            if len(s_den) > 1:
                try:
                    poles = np.roots(s_den)
                    all_poles.extend(poles.tolist())
                except Exception:
                    pass
        if all_poles:
            real_parts = [abs(complex(p).real) for p in all_poles if np.isfinite(complex(p))]
            if real_parts:
                min_real = min(r for r in real_parts if r > 1e-6) if any(r > 1e-6 for r in real_parts) else 1.0
                t_end = max(10.0, 5.0 / min_real)
                t_end = min(t_end, 100.0)
        return t_end

    def _compute_probed_signals(self) -> None:
        """Compute signals for all probed nodes."""
        for probe in self.probes:
            self._compute_signal_for_node(probe["node_id"])

    def _compute_signal_for_node(self, node_id: str) -> None:
        """Compute the time-domain signal at a specific node."""
        if node_id not in self._node_tfs:
            return

        num, den = self._node_tfs[node_id]
        t_in, input_signal = self._generate_input_signal()

        def _clamp_signal(y: np.ndarray) -> Tuple[np.ndarray, bool]:
            """Clamp signal to prevent NaN/Inf display; return (clamped, was_clipped)."""
            CLIP_LIMIT = 1e6
            clipped = False
            if not np.all(np.isfinite(y)):
                y = np.where(np.isfinite(y), y, 0.0)
                clipped = True
            if np.max(np.abs(y)) > CLIP_LIMIT:
                y = np.clip(y, -CLIP_LIMIT, CLIP_LIMIT)
                clipped = True
            return y, clipped

        try:
            if self.system_type == "dt":
                z_num, z_den = self._operator_to_z(num, den)
                from scipy.signal import dlsim
                system = (z_num, z_den, 1)
                _, y_out = dlsim(system, input_signal.reshape(-1, 1))
                y_out = y_out.flatten()
                y_out, clipped = _clamp_signal(y_out)
                self._node_signals[node_id] = {
                    "t": t_in.tolist(),
                    "y": y_out.tolist(),
                    "clipped": clipped,
                }
            else:
                s_num, s_den = self._operator_to_s(num, den)
                from scipy.signal import lsim, lti
                sys = lti(s_num, s_den)
                t_out, y_out, _ = lsim(sys, input_signal, t_in)
                y_out, clipped = _clamp_signal(y_out)
                self._node_signals[node_id] = {
                    "t": t_out.tolist(),
                    "y": y_out.tolist(),
                    "clipped": clipped,
                }
        except Exception:
            # Fallback: try manual IIR filtering
            try:
                if self.system_type == "dt":
                    z_num, z_den = self._operator_to_z(num, den)
                    from scipy.signal import lfilter
                    y_out = lfilter(z_num, z_den, input_signal)
                    y_out, clipped = _clamp_signal(y_out)
                    self._node_signals[node_id] = {
                        "t": t_in.tolist(),
                        "y": y_out.tolist(),
                        "clipped": clipped,
                    }
                else:
                    self._node_signals[node_id] = {
                        "t": t_in.tolist(),
                        "y": np.zeros_like(t_in).tolist(),
                        "clipped": False,
                    }
            except Exception:
                self._node_signals[node_id] = {
                    "t": t_in.tolist() if hasattr(t_in, 'tolist') else list(t_in),
                    "y": np.zeros(len(t_in)).tolist(),
                    "clipped": False,
                }

    # =========================================================================
    # SFG computation for frontend rendering
    # =========================================================================

    # TF block types — these become edge gains, NOT SFG nodes
    _TF_TYPES = frozenset({"gain", "delay", "integrator", "custom_tf"})

    @staticmethod
    def _subscript(n: int) -> str:
        """Convert integer to Unicode subscript digits."""
        subs = "₀₁₂₃₄₅₆₇₈₉"
        return "".join(subs[int(d)] for d in str(n))

    def _compute_sfg_nodes(self) -> List[Dict[str, Any]]:
        """Compute SFG nodes — only signal points (input, output, adder, junction).

        In a textbook SFG, nodes represent signals and edges represent
        transfer functions.  TF blocks (gain, delay, integrator, custom_tf)
        become edge gains, NOT nodes.

        Labels are read from ``self._node_labels`` (set by
        ``_compute_node_labels``) to avoid duplicate computation.
        """
        if not self.blocks:
            return []

        _TYPE_MAP = {
            "input": "source",
            "output": "sink",
            "adder": "sum",
            "junction": "branch",
        }

        nodes = []
        for bid, block in self.blocks.items():
            btype = block.get("type", "")

            if btype in self._TF_TYPES:
                continue

            node_type = _TYPE_MAP.get(btype, "intermediate")
            pos = block.get("position", {"x": 0, "y": 0})
            label = self._node_labels.get(bid, bid)

            # Input/output nodes are not probeable — input is already plotted
            # by default and output is the overall system response.
            has_tf = bid in self._node_tfs and btype not in ("input", "output")
            tf_info = None
            if has_tf:
                num, den = self._node_tfs[bid]
                tf_info = {"num": num.tolist(), "den": den.tolist()}

            probe_info = None
            for probe in self.probes:
                if probe["node_id"] == bid:
                    probe_info = {"color": probe["color"], "id": probe["id"]}
                    break

            nodes.append({
                "id": bid,
                "type": node_type,
                "block_type": btype,
                "label": label,
                "position": pos,
                "probeable": has_tf,
                "probe": probe_info,
                "tf": tf_info,
            })

        return nodes

    def _get_block_gain_label(self, bid: str) -> str:
        """Get the gain label for a TF block to use as an SFG edge weight."""
        block = self.blocks[bid]
        btype = block.get("type", "")
        if btype == "gain":
            val = block.get("value", 1.0)
            if val == int(val):
                return str(int(val))
            return f"{val:.3g}"
        elif btype == "delay":
            return "z⁻¹" if self.system_type == "dt" else "e⁻ˢᵀ"
        elif btype == "integrator":
            return "z⁻¹" if self.system_type == "dt" else "s⁻¹"
        elif btype == "custom_tf":
            return block.get("label", block.get("expression", "H"))
        return "1"

    def _compute_sfg_edges(self) -> List[Dict[str, Any]]:
        """Compute SFG edges by tracing through TF block chains.

        Signal-node -> TF chain -> signal-node becomes one edge whose gain
        is the product of all TF blocks in the chain.  Direct signal-node ->
        signal-node edges get gain '1'.  Adder negative ports negate the gain.
        """
        if not self.connections:
            return []

        # Build outgoing connection lookup per block
        outgoing: Dict[str, List[Dict]] = {}
        for conn in self.connections:
            fb = conn.get("from_block")
            tb = conn.get("to_block")
            if fb in self.blocks and tb in self.blocks:
                outgoing.setdefault(fb, []).append(conn)

        def trace_forward(
            block_id: str, gains: List[str], visited: set,
        ) -> List[Dict]:
            """Trace through TF blocks to find destination signal-nodes."""
            if block_id in visited:
                return []
            visited.add(block_id)
            results: List[Dict] = []
            for conn in outgoing.get(block_id, []):
                target_id = conn["to_block"]
                target = self.blocks.get(target_id)
                if not target:
                    continue
                if target.get("type") in self._TF_TYPES:
                    gain = self._get_block_gain_label(target_id)
                    results.extend(
                        trace_forward(target_id, gains + [gain], set(visited))
                    )
                else:
                    results.append({
                        "node_id": target_id,
                        "conn": conn,
                        "gains": gains,
                    })
            return results

        def multiply_gains(arr: List[str]) -> str:
            if not arr:
                return "1"
            if len(arr) == 1:
                return arr[0]
            # Separate z⁻¹/1/s terms from numeric gains
            from collections import Counter
            counts = Counter(arr)
            parts = []
            for g, n in counts.items():
                if g == "z⁻¹":
                    parts.append(f"z⁻{_superscript(n)}" if n > 1 else "z⁻¹")
                elif g == "s⁻¹":
                    parts.append(f"s⁻{_superscript(n)}" if n > 1 else "s⁻¹")
                elif n == 1:
                    parts.append(g)
                else:
                    parts.append(f"{g}{_superscript(n)}")
            # Put numeric gains first for readability: "0.05·s⁻²" not "s⁻²·0.05"
            parts.sort(key=lambda p: 0 if p[0].isdigit() or p[0] == '-' else 1)
            return "·".join(parts)

        edges: List[Dict[str, Any]] = []
        edge_idx = 0

        for bid, block in self.blocks.items():
            btype = block.get("type", "")
            if btype in self._TF_TYPES:
                continue  # TF blocks are not edge sources

            for conn in outgoing.get(bid, []):
                target_id = conn["to_block"]
                target = self.blocks.get(target_id)
                if not target:
                    continue

                if target.get("type") in self._TF_TYPES:
                    # Signal-node -> TF chain -> destination signal-node(s)
                    first_gain = self._get_block_gain_label(target_id)
                    destinations = trace_forward(target_id, [first_gain], set())

                    for dest in destinations:
                        dest_block = self.blocks.get(dest["node_id"])
                        gain_str = multiply_gains(dest["gains"])

                        # Check adder sign at destination
                        if (
                            dest_block
                            and dest_block.get("type") == "adder"
                        ):
                            signs = dest_block.get("signs", ["+", "+", "+"])
                            tp = dest["conn"].get("to_port", 0)
                            if tp < len(signs) and signs[tp] == "-":
                                gain_str = (
                                    "-1" if gain_str == "1"
                                    else f"-({gain_str})"
                                )

                        from_pos = block.get("position", {"x": 0, "y": 0})
                        to_pos = (
                            dest_block.get("position", {"x": 0, "y": 0})
                            if dest_block else {"x": 0, "y": 0}
                        )
                        dx = to_pos.get("x", 0) - from_pos.get("x", 0)

                        edges.append({
                            "id": f"edge_{edge_idx}",
                            "from": bid,
                            "to": dest["node_id"],
                            "gain_label": gain_str,
                            "is_feedback": dx < -30,
                        })
                        edge_idx += 1
                else:
                    # Direct signal-node -> signal-node (unity or negative)
                    sign_neg = False
                    if target.get("type") == "adder":
                        signs = target.get("signs", ["+", "+", "+"])
                        tp = conn.get("to_port", 0)
                        if tp < len(signs) and signs[tp] == "-":
                            sign_neg = True

                    from_pos = block.get("position", {"x": 0, "y": 0})
                    to_pos = target.get("position", {"x": 0, "y": 0})
                    dx = to_pos.get("x", 0) - from_pos.get("x", 0)

                    edges.append({
                        "id": f"edge_{edge_idx}",
                        "from": bid,
                        "to": target_id,
                        "gain_label": "-1" if sign_neg else "1",
                        "is_feedback": dx < -30,
                    })
                    edge_idx += 1

        return edges

    # =========================================================================
    # TF formatting for display
    # =========================================================================

    def _format_tf_expression(
        self, num: np.ndarray, den: np.ndarray
    ) -> Dict[str, str]:
        """Format a TF as readable strings."""
        op = "R" if self.system_type == "dt" else "A"
        num_str = self._poly_to_string(num, op)
        den_str = self._poly_to_string(den, op)

        if den_str == "1":
            expr = num_str
        else:
            expr = f"({num_str}) / ({den_str})"

        # Domain version
        if self.system_type == "dt":
            z_num, z_den = self._operator_to_z(num, den)
            domain_var = "z"
            domain_num_str = self._poly_to_string(z_num, domain_var)
            domain_den_str = self._poly_to_string(z_den, domain_var)
        else:
            s_num, s_den = self._operator_to_s(num, den)
            domain_var = "s"
            domain_num_str = self._poly_to_string(s_num, domain_var)
            domain_den_str = self._poly_to_string(s_den, domain_var)

        if domain_den_str == "1":
            domain_expr = domain_num_str
        else:
            domain_expr = f"({domain_num_str}) / ({domain_den_str})"

        return {"operator": expr, "domain": domain_expr}

    def _poly_to_string(self, coeffs: np.ndarray, var: str) -> str:
        """Convert polynomial coefficients to readable string."""
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

    @staticmethod
    def _format_coeff(c: float) -> str:
        """Format a coefficient nicely."""
        if abs(c - round(c)) < 1e-10:
            return str(int(round(c)))
        return f"{c:.4g}"

    # =========================================================================
    # Plots
    # =========================================================================

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate scope plots for probed signals + input signal."""
        plots = []
        layout_base = {
            "paper_bgcolor": "#0a0e27",
            "plot_bgcolor": "#131b2e",
            "font": {"family": "Inter, sans-serif", "size": 12, "color": self.COLORS["text"]},
            "margin": {"t": 40, "r": 25, "b": 55, "l": 60},
            "legend": {"x": 0.01, "y": 0.99, "bgcolor": "rgba(0,0,0,0.3)"},
            "showlegend": True,
        }
        axis_style = {
            "gridcolor": self.COLORS["grid"],
            "zerolinecolor": self.COLORS["zero"],
            "color": self.COLORS["text"],
        }
        x_label = "n (samples)" if self.system_type == "dt" else "Time (s)"
        mode = "markers+lines" if self.system_type == "dt" else "lines"

        # Scope plot: all probed signals overlaid
        if self.probes:
            combined_data = []
            for probe in self.probes:
                sig = self._node_signals.get(probe["node_id"])
                if sig:
                    trace = {
                        "x": sig["t"],
                        "y": sig["y"],
                        "type": "scatter",
                        "mode": mode,
                        "name": probe["label"],
                        "line": {"color": probe["color"], "width": 2},
                    }
                    if self.system_type == "dt":
                        trace["marker"] = {"color": probe["color"], "size": 4}
                    combined_data.append(trace)

            if combined_data:
                plots.append({
                    "id": "scope",
                    "title": "Signal Scope",
                    "data": combined_data,
                    "layout": {
                        **layout_base,
                        "xaxis": {"title": x_label, **axis_style},
                        "yaxis": {"title": "Amplitude", **axis_style},
                    },
                })

        # Input signal plot
        if self.blocks:
            t_in, input_signal = self._generate_input_signal()
            input_trace = {
                "x": t_in.tolist(),
                "y": input_signal.tolist(),
                "type": "scatter",
                "mode": mode,
                "name": "Input",
                "line": {"color": self.COLORS["input"], "width": 2},
            }
            if self.system_type == "dt":
                input_trace["marker"] = {"color": self.COLORS["input"], "size": 4}

            plots.append({
                "id": "input_signal",
                "title": "Input Signal",
                "data": [input_trace],
                "layout": {
                    **layout_base,
                    "xaxis": {"title": x_label, **axis_style},
                    "yaxis": {"title": "Amplitude", **axis_style},
                },
            })

        return plots

    # =========================================================================
    # State
    # =========================================================================

    @staticmethod
    def _signal_stats(values: np.ndarray) -> Dict[str, float]:
        """Compute statistics for a signal array."""
        finite = values[np.isfinite(values)] if len(values) > 0 else np.array([0.0])
        if len(finite) == 0:
            finite = np.array([0.0])
        return {
            "rms": float(np.sqrt(np.mean(finite ** 2))),
            "peak": float(np.max(np.abs(finite))),
            "mean": float(np.mean(finite)),
            "min": float(np.min(finite)),
            "max": float(np.max(finite)),
        }

    def _build_raw_signals(self) -> Dict[str, Any]:
        """Build raw signal data for frontend-driven plot rendering."""
        if not self.blocks:
            return {}

        t_in, input_signal = self._generate_input_signal()

        # Find output node signal
        output_id = None
        for bid, block in self.blocks.items():
            if block.get("type") == "output":
                output_id = bid
                break

        output_values = None
        if output_id and output_id in self._node_signals:
            output_values = np.array(self._node_signals[output_id]["y"])
        elif output_id and output_id in self._node_tfs:
            self._compute_signal_for_node(output_id)
            if output_id in self._node_signals:
                output_values = np.array(self._node_signals[output_id]["y"])

        signals: Dict[str, Any] = {
            "time": t_in.tolist(),
            "input": {
                "values": input_signal.tolist(),
                "label": "x[n]" if self.system_type == "dt" else "x(t)",
                "color": self.COLORS["input"],
                "stats": self._signal_stats(input_signal),
            },
        }

        if output_values is not None:
            signals["output"] = {
                "values": output_values.tolist(),
                "label": "y[n]" if self.system_type == "dt" else "y(t)",
                "color": "#f59e0b",
                "stats": self._signal_stats(output_values),
            }

        # Per-probe signals
        probe_signals = {}
        for probe in self.probes:
            sig = self._node_signals.get(probe["node_id"])
            if sig:
                y = np.array(sig["y"])
                probe_signals[probe["id"]] = {
                    "node_id": probe["node_id"],
                    "label": probe["label"],
                    "color": probe["color"],
                    "values": sig["y"],
                    "stats": self._signal_stats(y),
                }
        signals["probes"] = probe_signals

        return signals

    def get_state(self) -> Dict[str, Any]:
        """Return current state with SFG data, probe info, and raw signals."""
        state = super().get_state()

        # Build node TF info for display
        node_tfs_display = {}
        for nid, (num, den) in self._node_tfs.items():
            tf_expr = self._format_tf_expression(num, den)
            node_tfs_display[nid] = {
                "num": num.tolist(),
                "den": den.tolist(),
                "expression": tf_expr,
            }

        # Preset list for frontend
        preset_list = [
            {"id": k, "name": v["name"], "description": v["description"]}
            for k, v in self.PRESETS.items()
        ]

        state["metadata"] = {
            "simulation_type": "signal_flow_scope",
            "hub_slots": self.HUB_SLOTS,
            "hub_domain": self.HUB_DOMAIN,
            "hub_dimensions": self.HUB_DIMENSIONS,
            "system_type": self.system_type,
            "blocks": self.blocks,
            "connections": self.connections,
            "probes": self.probes,
            "node_tfs": node_tfs_display,
            "diagram_loaded": bool(self.blocks),
            "sfg_nodes": self._compute_sfg_nodes(),
            "sfg_edges": self._compute_sfg_edges(),
            "signals": self._build_raw_signals(),
            "presets": preset_list,
            "error": self._error,
        }
        return state
