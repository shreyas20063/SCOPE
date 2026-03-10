"""
Signal Flow Scope Simulator

Import block diagrams from the Block Diagram Builder, apply input signals,
and probe any node to visualize signal propagation through the system.

Key features:
- Import diagrams via JSON (blocks + connections)
- Compute transfer function from input to every reachable node (Mason's formula)
- Generate input signals: impulse, step, sinusoid, ramp
- Place up to 6 probes on nodes, view time-domain signals
- Signal Flow Graph (SFG) visualization data
"""

import copy
import re
import numpy as np
from collections import deque
from itertools import combinations
from typing import Any, Dict, List, Optional, Tuple
from .base_simulator import BaseSimulator


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
            "visible_when": {"input_type": "sinusoid"},
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
    }

    DEFAULT_PARAMS = {
        "input_type": "impulse",
        "input_freq": 1.0,
        "input_amplitude": 5.0,
        "num_samples": 100,
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
        if name in ("input_type", "input_freq", "input_amplitude", "num_samples"):
            if self.blocks:
                self._compute_probed_signals()

        return self.get_state()

    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle custom actions."""
        action_map = {
            "import_diagram": self._action_import_diagram,
            "add_probe": self._action_add_probe,
            "remove_probe": self._action_remove_probe,
            "clear_probes": self._action_clear_probes,
            "toggle_probe": self._action_toggle_probe,
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
        """Compute human-readable labels for each node."""
        self._node_labels = {}
        for bid, block in self.blocks.items():
            btype = block.get("type", "")
            if btype == "input":
                label = "x[n]" if self.system_type == "dt" else "x(t)"
            elif btype == "output":
                label = "y[n]" if self.system_type == "dt" else "y(t)"
            elif btype == "gain":
                val = block.get("value", 1.0)
                label = f"Gain({val})"
            elif btype == "adder":
                label = "Sum"
            elif btype == "delay":
                label = "R (Delay)"
            elif btype == "integrator":
                label = "A (Integrator)"
            elif btype == "junction":
                label = "Junction"
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
        # Find forward paths from input to target
        forward_paths: List[List[str]] = []
        self._dfs_forward_paths(
            input_id, target_id, incoming, outgoing,
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
                    port_idx = 0
                    for conn in self.connections:
                        if conn["from_block"] == prev_bid and conn["to_block"] == bid:
                            port_idx = conn.get("to_port", 0)
                            break
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
                    port_idx = 0
                    for conn in self.connections:
                        if conn["from_block"] == prev_bid and conn["to_block"] == bid:
                            port_idx = conn.get("to_port", 0)
                            break
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
            delta_num = np.array([1.0])
            delta_den = np.array([1.0])

            for size in range(1, len(loops) + 1):
                for combo in combinations(range(len(loops)), size):
                    # Check all pairs are non-touching
                    is_valid = True
                    for i in range(len(combo)):
                        for j in range(i + 1, len(combo)):
                            if not loops_are_non_touching(loops[combo[i]], loops[combo[j]]):
                                is_valid = False
                                break
                        if not is_valid:
                            break

                    if not is_valid:
                        continue

                    # Product of loop gains
                    prod_num = np.array([1.0])
                    prod_den = np.array([1.0])
                    for idx in combo:
                        ln, ld = compute_loop_gain(loops[idx])
                        prod_num = self._pmul(prod_num, ln)
                        prod_den = self._pmul(prod_den, ld)

                    sign = (-1.0) ** size
                    term_num = self._pscale(prod_num, sign)
                    new_num = self._padd(
                        self._pmul(delta_num, prod_den),
                        self._pmul(term_num, delta_den)
                    )
                    new_den = self._pmul(delta_den, prod_den)
                    delta_num = new_num
                    delta_den = new_den

            return (delta_num, delta_den)

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
                self._dfs_forward_paths(
                    next_block, target, incoming, outgoing,
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
        """Convert R-domain (R=z^{-1}) to z-domain (high-power-first)."""
        den_order = len(den) - 1
        num_order = len(num) - 1
        k = max(den_order, num_order)

        z_num = np.zeros(k + 1)
        z_den = np.zeros(k + 1)
        z_num[:len(num)] = num
        z_den[:len(den)] = den

        if not np.any(z_num != 0):
            z_num = np.array([0.0])
        if not np.any(z_den != 0):
            z_den = np.array([1.0])

        return z_num, z_den

    def _operator_to_s(
        self, num: np.ndarray, den: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Convert A-domain (A=1/s) to s-domain (high-power-first)."""
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

        if self.system_type == "dt":
            n = np.arange(num_samples)
            if input_type == "impulse":
                signal = np.zeros(num_samples)
                signal[0] = amplitude
            elif input_type == "step":
                signal = np.ones(num_samples) * amplitude
            elif input_type == "sinusoid":
                signal = amplitude * np.sin(2 * np.pi * freq * n / num_samples)
            elif input_type == "ramp":
                signal = amplitude * n / num_samples
            else:
                signal = np.zeros(num_samples)
                signal[0] = amplitude
            return (n, signal)
        else:
            # CT: determine time range from poles
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

            t = np.linspace(0, t_end, num_samples)
            if input_type == "impulse":
                # Approximate impulse as narrow Gaussian
                dt = t[1] - t[0] if len(t) > 1 else 0.01
                signal = np.zeros_like(t)
                signal[0] = amplitude / dt
            elif input_type == "step":
                signal = np.ones_like(t) * amplitude
            elif input_type == "sinusoid":
                signal = amplitude * np.sin(2 * np.pi * freq * t)
            elif input_type == "ramp":
                signal = amplitude * t / t_end
            else:
                signal = np.zeros_like(t)
                signal[0] = amplitude
            return (t, signal)

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

        try:
            if self.system_type == "dt":
                z_num, z_den = self._operator_to_z(num, den)
                from scipy.signal import dlsim
                system = (z_num, z_den, 1)
                _, y_out = dlsim(system, input_signal.reshape(-1, 1))
                y_out = y_out.flatten()
                self._node_signals[node_id] = {
                    "t": t_in.tolist(),
                    "y": y_out.tolist(),
                }
            else:
                s_num, s_den = self._operator_to_s(num, den)
                from scipy.signal import lsim, lti
                sys = lti(s_num, s_den)
                t_out, y_out, _ = lsim(sys, input_signal, t_in)
                self._node_signals[node_id] = {
                    "t": t_out.tolist(),
                    "y": y_out.tolist(),
                }
        except Exception:
            # Fallback: try manual IIR filtering
            try:
                if self.system_type == "dt":
                    z_num, z_den = self._operator_to_z(num, den)
                    from scipy.signal import lfilter
                    y_out = lfilter(z_num, z_den, input_signal)
                    self._node_signals[node_id] = {
                        "t": t_in.tolist(),
                        "y": y_out.tolist(),
                    }
                else:
                    self._node_signals[node_id] = {
                        "t": t_in.tolist(),
                        "y": np.zeros_like(t_in).tolist(),
                    }
            except Exception:
                self._node_signals[node_id] = {
                    "t": t_in.tolist() if hasattr(t_in, 'tolist') else list(t_in),
                    "y": np.zeros(len(t_in)).tolist(),
                }

    # =========================================================================
    # SFG computation for frontend rendering
    # =========================================================================

    def _compute_sfg_nodes(self) -> List[Dict[str, Any]]:
        """Compute SFG nodes from block diagram blocks."""
        if not self.blocks:
            return []

        nodes = []
        for bid, block in self.blocks.items():
            btype = block.get("type", "")
            pos = block.get("position", {"x": 0, "y": 0})

            node_type = "intermediate"
            if btype == "input":
                node_type = "source"
            elif btype == "output":
                node_type = "sink"
            elif btype == "adder":
                node_type = "sum"
            elif btype == "junction":
                node_type = "branch"

            # Check if this node is probeable (has a TF computed)
            # Input/output nodes are not probeable — input is already plotted
            # by default and output is the overall system response, so probing
            # them is redundant.
            has_tf = bid in self._node_tfs and btype not in ("input", "output")
            tf_info = None
            if has_tf:
                num, den = self._node_tfs[bid]
                tf_info = {
                    "num": num.tolist(),
                    "den": den.tolist(),
                }

            # Check if probed
            probe_info = None
            for probe in self.probes:
                if probe["node_id"] == bid:
                    probe_info = {"color": probe["color"], "id": probe["id"]}
                    break

            nodes.append({
                "id": bid,
                "type": node_type,
                "block_type": btype,
                "label": self._node_labels.get(bid, bid),
                "position": pos,
                "probeable": has_tf,
                "probe": probe_info,
                "tf": tf_info,
            })

        return nodes

    def _compute_sfg_edges(self) -> List[Dict[str, Any]]:
        """Compute SFG edges from connections with gain labels."""
        if not self.connections:
            return []

        edges = []
        for i, conn in enumerate(self.connections):
            fb = conn.get("from_block")
            tb = conn.get("to_block")
            if fb not in self.blocks or tb not in self.blocks:
                continue

            from_block = self.blocks[fb]
            to_block = self.blocks[tb]

            # Determine edge gain label
            gain_label = "1"
            gain_value = 1.0
            from_type = from_block.get("type", "")

            if from_type == "gain":
                val = from_block.get("value", 1.0)
                gain_label = str(val) if val != int(val) else str(int(val))
                gain_value = float(val)
            elif from_type == "delay":
                gain_label = "R" if self.system_type == "dt" else "z⁻¹"
            elif from_type == "integrator":
                gain_label = "A" if self.system_type == "ct" else "1/s"
            elif from_type == "custom_tf":
                gain_label = from_block.get("label", from_block.get("expression", "H"))

            # Check for negative adder port
            to_port = conn.get("to_port", 0)
            if to_block.get("type") == "adder":
                signs = to_block.get("signs", ["+", "+", "+"])
                if to_port < len(signs) and signs[to_port] == "-":
                    if gain_label == "1":
                        gain_label = "-1"
                    else:
                        gain_label = f"-({gain_label})"
                    gain_value *= -1

            # Determine if forward or feedback edge
            from_pos = from_block.get("position", {"x": 0, "y": 0})
            to_pos = to_block.get("position", {"x": 0, "y": 0})
            is_feedback = to_pos.get("x", 0) < from_pos.get("x", 0)

            edges.append({
                "id": f"edge_{i}",
                "from": fb,
                "to": tb,
                "from_port": conn.get("from_port", 0),
                "to_port": to_port,
                "gain_label": gain_label,
                "gain_value": gain_value,
                "is_feedback": is_feedback,
            })

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
                    if c > 0:
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

    def get_state(self) -> Dict[str, Any]:
        """Return current state with SFG data and probe info."""
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

        state["metadata"] = {
            "simulation_type": "signal_flow_scope",
            "system_type": self.system_type,
            "blocks": self.blocks,
            "connections": self.connections,
            "probes": self.probes,
            "node_tfs": node_tfs_display,
            "diagram_loaded": bool(self.blocks),
            "sfg_nodes": self._compute_sfg_nodes(),
            "sfg_edges": self._compute_sfg_edges(),
            "error": self._error,
        }
        return state
