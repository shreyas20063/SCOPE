"""
Cyclic Path Detector Simulator

Detect cyclic signal paths in block diagrams. Identify feedback loops,
classify systems as FIR (acyclic) or IIR (cyclic), and quiz students
on their understanding.
"""

import random
import time
import numpy as np
from typing import Any, Dict, List, Optional, Set, Tuple
from .base_simulator import BaseSimulator


class CyclicPathDetectorSimulator(BaseSimulator):
    """
    Cyclic Path Detector — visualizes feedback structure in block diagrams.

    Provides 7 preset block diagrams:
    - 3 classic systems (Difference, Accumulator, Cascaded Difference)
    - 4 quiz systems (the "Check Yourself" exercise)

    Features cycle detection, FIR/IIR classification, impulse response,
    and an interactive quiz mode.
    """

    # Cycle highlight colors from project palette
    CYCLE_COLORS = ["#ef4444", "#10b981", "#8b5cf6", "#f59e0b"]

    # Plot colors
    COLORS = {
        "impulse": "#3b82f6",
        "zero_line": "rgba(148, 163, 184, 0.3)",
        "grid": "rgba(148, 163, 184, 0.1)",
        "annotation_fir": "#10b981",
        "annotation_iir": "#f59e0b",
    }

    PARAMETER_SCHEMA = {
        "preset": {
            "type": "select",
            "options": [
                {"value": "difference", "label": "Difference Machine"},
                {"value": "accumulator", "label": "Accumulator"},
                {"value": "cascaded_diff", "label": "Cascaded Difference"},
                {"value": "slide48_a", "label": "Quiz — System A"},
                {"value": "slide48_b", "label": "Quiz — System B"},
                {"value": "slide48_c", "label": "Quiz — System C"},
                {"value": "slide48_d", "label": "Quiz — System D"},
            ],
            "default": "difference",
        },
        "mode": {
            "type": "select",
            "options": [
                {"value": "explore", "label": "Explore"},
                {"value": "quiz", "label": "Quiz"},
            ],
            "default": "explore",
        },
        "show_cycles": {
            "type": "checkbox",
            "default": True,
        },
        "impulse_steps": {
            "type": "slider",
            "min": 5,
            "max": 30,
            "step": 1,
            "default": 15,
        },
    }

    DEFAULT_PARAMS = {
        "preset": "difference",
        "mode": "explore",
        "show_cycles": True,
        "impulse_steps": 15,
    }


    # ── Preset Definitions ──────────────────────────────────────

    @staticmethod
    def _build_presets() -> Dict[str, Dict]:
        """Build all 7 preset block diagram definitions."""
        presets = {}

        # ── 1. Difference Machine ──
        # y[n] = x[n] - x[n-1],  Y = (1 - R)X
        presets["difference"] = {
            "name": "Difference Machine",
            "equation": "y[n] = x[n] − x[n−1]",
            "operator_form": "Y = (1 − R) X",
            "coeffs": {"b": [1.0, -1.0], "a": []},
            "nodes": [
                {"id": "in", "type": "input", "label": "X", "x": 50, "y": 130},
                {"id": "gain", "type": "gain", "label": "−1", "x": 210, "y": 230},
                {"id": "delay", "type": "delay", "label": "R", "x": 350, "y": 230},
                {"id": "add", "type": "adder", "label": "+", "x": 500, "y": 130},
                {"id": "out", "type": "output", "label": "Y", "x": 650, "y": 130},
            ],
            "edges": [
                {"id": "e1", "from": "in", "to": "add",
                 "waypoints": [[90, 130], [480, 130]]},
                {"id": "e2", "from": "in", "to": "gain",
                 "waypoints": [[90, 130], [90, 230], [185, 230]]},
                {"id": "e3", "from": "gain", "to": "delay",
                 "waypoints": [[235, 230], [325, 230]]},
                {"id": "e4", "from": "delay", "to": "add",
                 "waypoints": [[375, 230], [500, 230], [500, 150]]},
                {"id": "e5", "from": "add", "to": "out",
                 "waypoints": [[520, 130], [630, 130]]},
            ],
        }

        # ── 2. Accumulator ──
        # y[n] = x[n] + y[n-1],  Y = X / (1 - R)
        presets["accumulator"] = {
            "name": "Accumulator",
            "equation": "y[n] = x[n] + y[n−1]",
            "operator_form": "Y = X / (1 − R)",
            "coeffs": {"b": [1.0], "a": [1.0]},
            "nodes": [
                {"id": "in", "type": "input", "label": "X", "x": 50, "y": 130},
                {"id": "add", "type": "adder", "label": "+", "x": 250, "y": 130},
                {"id": "out", "type": "output", "label": "Y", "x": 650, "y": 130},
                {"id": "delay", "type": "delay", "label": "R", "x": 450, "y": 250},
            ],
            "edges": [
                {"id": "e1", "from": "in", "to": "add",
                 "waypoints": [[90, 130], [230, 130]]},
                {"id": "e2", "from": "add", "to": "out",
                 "waypoints": [[270, 130], [630, 130]]},
                {"id": "e3", "from": "add", "to": "delay",
                 "waypoints": [[270, 130], [450, 130], [475, 130], [475, 232]]},
                {"id": "e4", "from": "delay", "to": "add",
                 "waypoints": [[425, 250], [250, 250], [250, 150]]},
            ],
        }

        # ── 3. Cascaded Difference ──
        # y[n] = x[n] - 2x[n-1] + x[n-2],  Y = (1-R)^2 X
        presets["cascaded_diff"] = {
            "name": "Cascaded Difference",
            "equation": "y[n] = x[n] − 2x[n−1] + x[n−2]",
            "operator_form": "Y = (1 − R)² X",
            "coeffs": {"b": [1.0, -2.0, 1.0], "a": []},
            "nodes": [
                {"id": "in", "type": "input", "label": "X", "x": 30, "y": 100},
                {"id": "g1", "type": "gain", "label": "−1", "x": 120, "y": 200},
                {"id": "d1", "type": "delay", "label": "R", "x": 230, "y": 200},
                {"id": "a1", "type": "adder", "label": "+", "x": 310, "y": 100},
                {"id": "g2", "type": "gain", "label": "−1", "x": 400, "y": 200},
                {"id": "d2", "type": "delay", "label": "R", "x": 510, "y": 200},
                {"id": "a2", "type": "adder", "label": "+", "x": 590, "y": 100},
                {"id": "out", "type": "output", "label": "Y", "x": 680, "y": 100},
            ],
            "edges": [
                {"id": "e1", "from": "in", "to": "a1",
                 "waypoints": [[65, 100], [290, 100]]},
                {"id": "e2", "from": "in", "to": "g1",
                 "waypoints": [[65, 100], [65, 200], [95, 200]]},
                {"id": "e3", "from": "g1", "to": "d1",
                 "waypoints": [[145, 200], [205, 200]]},
                {"id": "e4", "from": "d1", "to": "a1",
                 "waypoints": [[255, 200], [310, 200], [310, 120]]},
                {"id": "e5", "from": "a1", "to": "a2",
                 "waypoints": [[330, 100], [570, 100]]},
                {"id": "e6", "from": "a1", "to": "g2",
                 "waypoints": [[330, 100], [345, 100], [345, 200], [375, 200]]},
                {"id": "e7", "from": "g2", "to": "d2",
                 "waypoints": [[425, 200], [485, 200]]},
                {"id": "e8", "from": "d2", "to": "a2",
                 "waypoints": [[535, 200], [590, 200], [590, 120]]},
                {"id": "e9", "from": "a2", "to": "out",
                 "waypoints": [[610, 100], [660, 100]]},
            ],
        }

        # ── 4. Quiz System A (top-left): feedback on first adder ──
        # X → (+₁) → R₁ → (+₂) → Y, with R₂ feedback: (+₁) out → R₂ → (+₁) in
        # Equation: Let W = X + R·W → W = X/(1-R), Y = R·W + W = W(1+R)
        # Simplified: y[n] = x[n] + 2y[n-1] (effectively)
        presets["slide48_a"] = {
            "name": "Quiz — System A",
            "equation": "Feedback on first adder",
            "operator_form": "Y = R·X/(1−R) + X/(1−R)",
            "coeffs": {"b": [1.0], "a": [1.0]},
            "nodes": [
                {"id": "in", "type": "input", "label": "X", "x": 30, "y": 130},
                {"id": "a1", "type": "adder", "label": "+", "x": 170, "y": 130},
                {"id": "r1", "type": "delay", "label": "R", "x": 320, "y": 130},
                {"id": "a2", "type": "adder", "label": "+", "x": 480, "y": 130},
                {"id": "out", "type": "output", "label": "Y", "x": 630, "y": 130},
                {"id": "r2", "type": "delay", "label": "R", "x": 170, "y": 250},
            ],
            "edges": [
                {"id": "e1", "from": "in", "to": "a1",
                 "waypoints": [[65, 130], [150, 130]]},
                {"id": "e2", "from": "a1", "to": "r1",
                 "waypoints": [[190, 130], [295, 130]]},
                {"id": "e3", "from": "r1", "to": "a2",
                 "waypoints": [[345, 130], [460, 130]]},
                {"id": "e4", "from": "a2", "to": "out",
                 "waypoints": [[500, 130], [610, 130]]},
                {"id": "e5", "from": "a1", "to": "r2",
                 "waypoints": [[190, 150], [190, 160], [195, 232]]},
                {"id": "e6", "from": "r2", "to": "a1",
                 "waypoints": [[145, 250], [100, 250], [100, 145], [150, 145]]},
            ],
        }

        # ── 5. Quiz System B (top-right): feedforward only ──
        # X → (+₁) → (+₂) → Y, with R blocks feeding forward from X
        # No cycles — purely feedforward
        presets["slide48_b"] = {
            "name": "Quiz — System B",
            "equation": "Two feedforward delays",
            "operator_form": "Y = (1 + R + R²) X",
            "coeffs": {"b": [1.0, 1.0, 1.0], "a": []},
            "nodes": [
                {"id": "in", "type": "input", "label": "X", "x": 30, "y": 130},
                {"id": "a1", "type": "adder", "label": "+", "x": 280, "y": 130},
                {"id": "a2", "type": "adder", "label": "+", "x": 480, "y": 130},
                {"id": "out", "type": "output", "label": "Y", "x": 630, "y": 130},
                {"id": "r1", "type": "delay", "label": "R", "x": 180, "y": 240},
                {"id": "r2", "type": "delay", "label": "R", "x": 380, "y": 240},
            ],
            "edges": [
                {"id": "e1", "from": "in", "to": "a1",
                 "waypoints": [[65, 130], [260, 130]]},
                {"id": "e2", "from": "a1", "to": "a2",
                 "waypoints": [[300, 130], [460, 130]]},
                {"id": "e3", "from": "a2", "to": "out",
                 "waypoints": [[500, 130], [610, 130]]},
                {"id": "e4", "from": "in", "to": "r1",
                 "waypoints": [[65, 130], [65, 240], [155, 240]]},
                {"id": "e5", "from": "r1", "to": "a1",
                 "waypoints": [[205, 240], [280, 240], [280, 150]]},
                {"id": "e6", "from": "r1", "to": "r2",
                 "waypoints": [[205, 240], [240, 240], [240, 275], [355, 275], [355, 240]]},
                {"id": "e7", "from": "r2", "to": "a2",
                 "waypoints": [[405, 240], [480, 240], [480, 150]]},
            ],
        }

        # ── 6. Quiz System C (bottom-left): long feedback loop ──
        # X → (+₁) → (+₂) → Y, with R from (+₂) out back to (+₁) in
        # 1 cycle: a1 → a2 → R → a1
        presets["slide48_c"] = {
            "name": "Quiz — System C",
            "equation": "Long feedback loop",
            "operator_form": "Y = X / (1 − R)",
            "coeffs": {"b": [1.0], "a": [1.0]},
            "nodes": [
                {"id": "in", "type": "input", "label": "X", "x": 30, "y": 130},
                {"id": "a1", "type": "adder", "label": "+", "x": 220, "y": 130},
                {"id": "a2", "type": "adder", "label": "+", "x": 420, "y": 130},
                {"id": "out", "type": "output", "label": "Y", "x": 630, "y": 130},
                {"id": "r1", "type": "delay", "label": "R", "x": 320, "y": 250},
            ],
            "edges": [
                {"id": "e1", "from": "in", "to": "a1",
                 "waypoints": [[65, 130], [200, 130]]},
                {"id": "e2", "from": "a1", "to": "a2",
                 "waypoints": [[240, 130], [400, 130]]},
                {"id": "e3", "from": "a2", "to": "out",
                 "waypoints": [[440, 130], [610, 130]]},
                {"id": "e4", "from": "a2", "to": "r1",
                 "waypoints": [[440, 150], [440, 250], [345, 250]]},
                {"id": "e5", "from": "r1", "to": "a1",
                 "waypoints": [[295, 250], [220, 250], [220, 150]]},
            ],
        }

        # ── 7. Quiz System D (bottom-right): two independent feedback loops ──
        # X → (+₁) → (+₂) → Y, with R₁ from (+₁) back to (+₁), R₂ from (+₂) back to (+₂)
        # 2 cycles: {a1, r1} and {a2, r2}
        presets["slide48_d"] = {
            "name": "Quiz — System D",
            "equation": "Two independent feedback loops",
            "operator_form": "Y = X / (1−R)²",
            "coeffs": {"b": [1.0], "a": [2.0, -1.0]},
            "nodes": [
                {"id": "in", "type": "input", "label": "X", "x": 30, "y": 130},
                {"id": "a1", "type": "adder", "label": "+", "x": 200, "y": 130},
                {"id": "a2", "type": "adder", "label": "+", "x": 440, "y": 130},
                {"id": "out", "type": "output", "label": "Y", "x": 630, "y": 130},
                {"id": "r1", "type": "delay", "label": "R", "x": 200, "y": 250},
                {"id": "r2", "type": "delay", "label": "R", "x": 440, "y": 250},
            ],
            "edges": [
                {"id": "e1", "from": "in", "to": "a1",
                 "waypoints": [[65, 130], [180, 130]]},
                {"id": "e2", "from": "a1", "to": "a2",
                 "waypoints": [[220, 130], [420, 130]]},
                {"id": "e3", "from": "a2", "to": "out",
                 "waypoints": [[460, 130], [610, 130]]},
                {"id": "e4", "from": "a1", "to": "r1",
                 "waypoints": [[220, 150], [225, 232]]},
                {"id": "e5", "from": "r1", "to": "a1",
                 "waypoints": [[175, 250], [120, 250], [120, 145], [180, 145]]},
                {"id": "e6", "from": "a2", "to": "r2",
                 "waypoints": [[460, 150], [465, 232]]},
                {"id": "e7", "from": "r2", "to": "a2",
                 "waypoints": [[415, 250], [360, 250], [360, 145], [420, 145]]},
            ],
        }

        return presets

    # ── Cycle Detection ─────────────────────────────────────────

    @staticmethod
    def _find_cycles(nodes: List[Dict], edges: List[Dict]) -> List[List[str]]:
        """
        Find all elementary cycles in a directed graph using DFS.

        Returns list of cycles, each cycle is a list of edge IDs.
        Excludes input/output nodes from cycle consideration.
        """
        # Build adjacency: node_id -> [(neighbor_id, edge_id)]
        adj: Dict[str, List[Tuple[str, str]]] = {n["id"]: [] for n in nodes}
        for e in edges:
            adj[e["from"]].append((e["to"], e["id"]))

        # Internal nodes only (skip input/output for cycle search)
        internal = {n["id"] for n in nodes if n["type"] not in ("input", "output")}

        cycles: List[List[str]] = []
        visited_global: Set[str] = set()

        def dfs(start: str, current: str, path_edges: List[str],
                path_nodes: List[str], visited: Set[str]) -> None:
            """DFS to find cycles starting from 'start'."""
            for neighbor, edge_id in adj.get(current, []):
                if neighbor not in internal:
                    continue
                if neighbor == start and len(path_edges) > 0:
                    # Found a cycle
                    cycle = path_edges + [edge_id]
                    # Avoid duplicate cycles: normalize by sorting edge IDs
                    cycle_key = tuple(sorted(cycle))
                    if cycle_key not in seen_cycles:
                        seen_cycles.add(cycle_key)
                        cycles.append(cycle)
                    continue
                if neighbor not in visited:
                    visited.add(neighbor)
                    path_nodes.append(neighbor)
                    path_edges.append(edge_id)
                    dfs(start, neighbor, path_edges, path_nodes, visited)
                    path_edges.pop()
                    path_nodes.pop()
                    visited.discard(neighbor)

        seen_cycles: Set[Tuple[str, ...]] = set()

        for node in nodes:
            if node["id"] not in internal:
                continue
            if node["id"] in visited_global:
                continue
            visited = {node["id"]}
            dfs(node["id"], node["id"], [], [node["id"]], visited)

        return cycles

    # ── Impulse Response ────────────────────────────────────────

    @staticmethod
    def _compute_impulse_response(coeffs: Dict, n_steps: int) -> np.ndarray:
        """
        Compute impulse response h[n] via step-by-step difference equation.

        coeffs: {"b": [b0, b1, ...], "a": [a1, a2, ...]}
        Equation: y[n] = sum(b[j]*x[n-j]) + sum(a[i]*y[n-i])
        where i is 1-indexed for a (feedback) and j is 0-indexed for b (feedforward).
        """
        b = coeffs.get("b", [1.0])
        a = coeffs.get("a", [])

        x = np.zeros(n_steps + max(len(b), 1))
        y = np.zeros(n_steps + max(len(a) + 1, 1))
        x[0] = 1.0  # impulse

        for n in range(n_steps):
            val = 0.0
            # Feedforward: sum of b[j] * x[n - j]
            for j, bj in enumerate(b):
                idx = n - j
                if 0 <= idx < len(x):
                    val += bj * x[idx]
            # Feedback: sum of a[i] * y[n - 1 - i + 1] = a[i] * y[n - i]
            for i, ai in enumerate(a):
                idx = n - (i + 1)
                if 0 <= idx < len(y):
                    val += ai * y[idx]
            y[n] = val

        return y[:n_steps]

    # ── Initialization ──────────────────────────────────────────

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._presets = self._build_presets()
        # Quiz state
        self._quiz_preset: Optional[str] = None
        self._quiz_answered: bool = False
        self._quiz_correct: Optional[bool] = None
        self._quiz_correct_answer: int = 0
        self._quiz_options: List[int] = [0, 1, 2, 3]

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            self.parameters[name] = self._validate_param(name, value)
        self._reset_quiz_state()
        self._initialized = True

    def reset(self) -> Dict[str, Any]:
        """Reset ALL state — parameters AND quiz."""
        self._reset_quiz_state()
        return super().reset()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
        # When switching TO quiz mode, generate a fresh quiz
        if name == "mode" and value == "quiz":
            self._generate_quiz()
        # When switching FROM quiz to explore, clear quiz state
        if name == "mode" and value == "explore":
            self._reset_quiz_state()
        # When changing preset in explore mode, no special action needed
        # (get_state() reads the current preset each time)
        return self.get_state()

    def _reset_quiz_state(self) -> None:
        """Clear all quiz state back to defaults."""
        self._quiz_preset = None
        self._quiz_answered = False
        self._quiz_correct = None
        self._quiz_correct_answer = 0

    # ── Quiz Logic ──────────────────────────────────────────────

    def _generate_quiz(self) -> None:
        """Generate a new quiz question by picking a random preset."""
        preset_keys = list(self._presets.keys())
        self._quiz_preset = random.choice(preset_keys)
        self._quiz_answered = False
        self._quiz_correct = None

        # Compute correct answer (number of cycles)
        preset = self._presets[self._quiz_preset]
        cycles = self._find_cycles(preset["nodes"], preset["edges"])
        self._quiz_correct_answer = len(cycles)
        self._quiz_options = [0, 1, 2, 3]

    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle custom actions for quiz mode."""
        if action == "new_quiz":
            self._generate_quiz()
        elif action == "check_answer":
            answer_index = params.get("answer_index", -1)
            self._quiz_answered = True
            self._quiz_correct = (answer_index == self._quiz_correct_answer)
        return self.get_state()

    # ── State & Plots ───────────────────────────────────────────

    def get_plots(self) -> List[Dict[str, Any]]:
        mode = self.parameters["mode"]
        if mode == "quiz" and self._quiz_preset:
            preset_key = self._quiz_preset
        else:
            preset_key = self.parameters["preset"]

        preset = self._presets.get(preset_key, self._presets["difference"])
        n_steps = int(self.parameters["impulse_steps"])
        h = self._compute_impulse_response(preset["coeffs"], n_steps)
        cycles = self._find_cycles(preset["nodes"], preset["edges"])
        is_cyclic = len(cycles) > 0

        return [self._create_impulse_plot(h, n_steps, is_cyclic, preset_key)]

    def get_state(self) -> Dict[str, Any]:
        state = super().get_state()
        mode = self.parameters["mode"]

        if mode == "quiz" and self._quiz_preset:
            preset_key = self._quiz_preset
        else:
            preset_key = self.parameters["preset"]

        preset = self._presets.get(preset_key, self._presets["difference"])
        cycles = self._find_cycles(preset["nodes"], preset["edges"])
        is_cyclic = len(cycles) > 0

        # Build cycle data with colors
        cycle_data = []
        for i, cycle_edges in enumerate(cycles):
            cycle_data.append({
                "edge_ids": cycle_edges,
                "color": self.CYCLE_COLORS[i % len(self.CYCLE_COLORS)],
            })

        # In quiz mode, hide cycles until answered
        show_cycles_in_response = True
        if mode == "quiz" and not self._quiz_answered:
            show_cycles_in_response = False

        state["metadata"] = {
            "simulation_type": "cyclic_path_detector",
            "hub_slots": self.HUB_SLOTS,
            "hub_domain": self.HUB_DOMAIN,
            "hub_dimensions": self.HUB_DIMENSIONS,
            "mode": mode,
            "preset_key": preset_key,
            "preset_name": preset["name"],
            "equation": preset["equation"],
            "operator_form": preset["operator_form"],
            "nodes": preset["nodes"],
            "edges": preset["edges"],
            "cycles": cycle_data if show_cycles_in_response else [],
            "num_cycles": len(cycles),
            "classification": "IIR" if is_cyclic else "FIR",
            "is_cyclic": is_cyclic,
            "show_cycles": self.parameters.get("show_cycles", True),
        }

        # Quiz metadata
        if mode == "quiz":
            if not self._quiz_preset:
                self._generate_quiz()
                # Re-fetch after generating
                return self.get_state()

            state["metadata"]["quiz"] = {
                "options": self._quiz_options,
                "answered": self._quiz_answered,
                "correct": self._quiz_correct,
                "correct_answer": self._quiz_correct_answer if self._quiz_answered else None,
            }

        return state

    # ── Plot Builders ───────────────────────────────────────────

    def _create_impulse_plot(self, h: np.ndarray, n_steps: int,
                             is_cyclic: bool, preset_key: str) -> Dict:
        """Build impulse response stem plot."""
        n = np.arange(len(h))

        # Clamp extreme values for display (IIR can blow up)
        h_display = np.clip(h, -1000, 1000)

        # Stem plot: markers + vertical lines to zero
        stem_lines_x = []
        stem_lines_y = []
        for ni, hi in zip(n, h_display):
            stem_lines_x.extend([float(ni), float(ni), None])
            stem_lines_y.extend([0.0, float(hi), None])

        classification = "IIR (Infinite)" if is_cyclic else "FIR (Finite)"
        cls_color = self.COLORS["annotation_iir"] if is_cyclic else self.COLORS["annotation_fir"]

        # Compute y-axis range with padding
        y_min = float(np.min(h_display))
        y_max = float(np.max(h_display))
        y_pad = max(abs(y_max - y_min) * 0.15, 0.5)

        # Unique datarevision forces Plotly to re-render on every change
        data_rev = f"impulse-{preset_key}-{n_steps}-{time.time()}"

        return {
            "id": "impulse_response",
            "title": f"Impulse Response h[n]  —  {classification}",
            "data": [
                # Stem lines
                {
                    "x": stem_lines_x,
                    "y": stem_lines_y,
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Stems",
                    "line": {"color": self.COLORS["impulse"], "width": 2},
                    "showlegend": False,
                    "hoverinfo": "skip",
                },
                # Markers at sample values
                {
                    "x": n.tolist(),
                    "y": h_display.tolist(),
                    "type": "scatter",
                    "mode": "markers",
                    "name": "h[n]",
                    "marker": {
                        "color": self.COLORS["impulse"],
                        "size": 8,
                        "line": {"color": "#1e3a5f", "width": 1},
                    },
                },
            ],
            "layout": {
                "xaxis": {
                    "title": "n (sample index)",
                    "dtick": max(1, n_steps // 15),
                    "range": [-0.5, n_steps - 0.5],
                    "gridcolor": self.COLORS["grid"],
                    "zerolinecolor": self.COLORS["zero_line"],
                    "color": "#f1f5f9",
                },
                "yaxis": {
                    "title": "h[n]",
                    "autorange": True,
                    "range": [y_min - y_pad, y_max + y_pad],
                    "gridcolor": self.COLORS["grid"],
                    "zerolinecolor": self.COLORS["zero_line"],
                    "color": "#f1f5f9",
                },
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "font": {
                    "family": "Inter, sans-serif",
                    "size": 12,
                    "color": "#f1f5f9",
                },
                "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
                "showlegend": False,
                "datarevision": data_rev,
                "uirevision": "impulse_response",
                "annotations": [
                    {
                        "x": 0.98,
                        "y": 0.95,
                        "xref": "paper",
                        "yref": "paper",
                        "text": classification,
                        "showarrow": False,
                        "font": {
                            "size": 14,
                            "color": cls_color,
                            "family": "Inter, sans-serif",
                        },
                        "bgcolor": "rgba(0,0,0,0.5)",
                        "bordercolor": cls_color,
                        "borderwidth": 1,
                        "borderpad": 6,
                        "xanchor": "right",
                    }
                ],
            },
        }
