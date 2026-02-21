"""
Feedback & Convergence Explorer Simulator

Interactive exploration of a single feedback loop with adjustable gain p₀.
Demonstrates how feedback creates geometric sequences (fundamental modes)
and when they converge vs. diverge.

Based on MIT 6.003 Lecture 2, slides 36-56:
- System: y[n] = x[n] + p₀ · y[n-1]
- Impulse response: y[n] = p₀ⁿ for n ≥ 0
- Converges when |p₀| < 1, diverges when |p₀| > 1
"""

import time
from typing import Any, Dict, List, Optional

import numpy as np

from .base_simulator import BaseSimulator


class FeedbackConvergenceSimulator(BaseSimulator):
    """Simulator for feedback loop convergence/divergence exploration."""

    MAX_DISPLAY_VALUE = 50.0
    MARGINAL_EPSILON = 0.005

    PARAMETER_SCHEMA = {
        "p0": {
            "type": "slider",
            "min": -2.0,
            "max": 2.0,
            "step": 0.01,
            "default": 0.5,
        },
        "num_samples": {
            "type": "slider",
            "min": 5,
            "max": 30,
            "step": 1,
            "default": 15,
        },
        "show_envelope": {
            "type": "checkbox",
            "default": True,
        },
        "show_unit_circle": {
            "type": "checkbox",
            "default": False,
        },
    }

    DEFAULT_PARAMS = {
        "p0": 0.5,
        "num_samples": 15,
        "show_envelope": True,
        "show_unit_circle": False,
    }

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._animation_step: int = 0
        self._animation_active: bool = False

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            if name in self.PARAMETER_SCHEMA:
                self.parameters[name] = self._validate_param(name, value)
        self._animation_step = 0
        self._animation_active = False
        self._initialized = True

    def reset(self) -> Dict[str, Any]:
        """Reset ALL state: parameters AND animation."""
        self._animation_step = 0
        self._animation_active = False
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._initialized = True
        return self.get_state()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
            # Reset animation when any parameter changes so plots refresh cleanly
            self._animation_step = 0
            self._animation_active = False
        return self.get_state()

    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle custom actions for animation."""
        num_samples = int(self.parameters["num_samples"])

        if action == "animate_cycles":
            self._animation_active = True
            if self._animation_step < num_samples:
                self._animation_step += 1
            else:
                self._animation_step = 1
        elif action == "reset_animation":
            self._animation_step = 0
            self._animation_active = False
        elif action == "step_forward":
            self._animation_active = True
            if self._animation_step < num_samples:
                self._animation_step += 1
        elif action == "step_backward":
            if self._animation_step > 0:
                self._animation_step -= 1
            if self._animation_step == 0:
                self._animation_active = False

        return self.get_state()

    def get_plots(self) -> List[Dict[str, Any]]:
        data = self._compute()
        return [
            self._create_impulse_response_plot(data),
            self._create_geometric_sum_plot(data),
        ]

    def get_state(self) -> Dict[str, Any]:
        p0 = float(self.parameters["p0"])
        abs_p0 = abs(p0)
        num_samples = int(self.parameters["num_samples"])

        # Convergence classification
        if abs_p0 < 1.0 - self.MARGINAL_EPSILON:
            convergence = "converging"
        elif abs_p0 > 1.0 + self.MARGINAL_EPSILON:
            convergence = "diverging"
        else:
            convergence = "marginal"

        # Geometric sum limit
        geometric_sum_limit = None
        if abs_p0 < 1.0 - self.MARGINAL_EPSILON:
            geometric_sum_limit = 1.0 / (1.0 - p0)

        # Current sample value at animation step
        step = self._animation_step if self._animation_active else num_samples - 1
        current_sample_value = p0 ** step if step >= 0 else 0.0

        return {
            "parameters": self.parameters.copy(),
            "plots": self.get_plots(),
            "metadata": {
                "simulation_type": "feedback_convergence",
                "p0": p0,
                "convergence": convergence,
                "abs_p0": abs_p0,
                "geometric_sum_limit": geometric_sum_limit,
                "animation_step": self._animation_step,
                "animation_active": self._animation_active,
                "current_sample_value": float(current_sample_value),
                "num_samples": num_samples,
            },
        }

    # ── Computation ──────────────────────────────────────────────

    def _compute(self) -> Dict[str, Any]:
        """Compute impulse response and partial sums."""
        p0 = float(self.parameters["p0"])
        num_samples = int(self.parameters["num_samples"])
        abs_p0 = abs(p0)

        n = np.arange(num_samples)

        # Impulse response: y[n] = p₀ⁿ
        # Handle p0=0 edge: 0^0 = 1, 0^n = 0 for n>0
        if p0 == 0.0:
            y = np.where(n == 0, 1.0, 0.0)
        else:
            y = p0 ** n

        # Clip for display (preserve sign)
        y_clipped = np.clip(y, -self.MAX_DISPLAY_VALUE, self.MAX_DISPLAY_VALUE)
        is_clipped = np.abs(y) > self.MAX_DISPLAY_VALUE

        # Envelope: |p₀|ⁿ
        if abs_p0 == 0.0:
            envelope = np.where(n == 0, 1.0, 0.0)
        else:
            envelope = abs_p0 ** n
        envelope_clipped = np.clip(envelope, 0, self.MAX_DISPLAY_VALUE)

        # Partial sums: S[n] = sum_{k=0}^{n} p₀^k
        # Use clipped y for partial sums so they don't overflow
        partial_sums = np.cumsum(y_clipped)
        partial_sums_clipped = np.clip(
            partial_sums, -self.MAX_DISPLAY_VALUE * 2, self.MAX_DISPLAY_VALUE * 2
        )

        return {
            "n": n,
            "y": y_clipped,
            "y_raw": y,
            "is_clipped": is_clipped,
            "envelope": envelope_clipped,
            "partial_sums": partial_sums_clipped,
            "p0": p0,
            "abs_p0": abs_p0,
        }

    # ── Plot Construction ────────────────────────────────────────

    def _get_base_layout(self, xtitle: str, ytitle: str, plot_id: str) -> Dict[str, Any]:
        """Standard Plotly layout with proper datarevision/uirevision."""
        p0 = float(self.parameters["p0"])
        return {
            "xaxis": {
                "title": {"text": xtitle, "font": {"color": "#f1f5f9", "size": 13}},
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#94a3b8",
                "dtick": 1,
            },
            "yaxis": {
                "title": {"text": ytitle, "font": {"color": "#f1f5f9", "size": 13}},
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "color": "#94a3b8",
                "autorange": False,
            },
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
            "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
            "showlegend": True,
            "legend": {
                "font": {"color": "#94a3b8", "size": 11},
                "bgcolor": "rgba(0,0,0,0)",
            },
            # Force Plotly re-render on every state change
            "datarevision": f"{plot_id}-{p0}-{self._animation_step}-{time.time()}",
            # Reset zoom/pan when p0 changes significantly
            "uirevision": plot_id,
        }

    def _get_stem_color(self) -> str:
        """Get color based on convergence status."""
        abs_p0 = abs(float(self.parameters["p0"]))
        if abs_p0 < 1.0 - self.MARGINAL_EPSILON:
            return "#10b981"  # green — converging
        elif abs_p0 > 1.0 + self.MARGINAL_EPSILON:
            return "#ef4444"  # red — diverging
        else:
            return "#f59e0b"  # amber — marginal

    def _compute_y_range(self, values: List[float], extra_values: Optional[List[float]] = None) -> List[float]:
        """Compute robust y-axis range from data values with padding."""
        all_vals = list(values)
        if extra_values:
            all_vals.extend(extra_values)

        if not all_vals:
            return [-1.5, 1.5]

        y_min = min(all_vals)
        y_max = max(all_vals)

        # Always include zero in view
        y_min = min(y_min, 0.0)
        y_max = max(y_max, 0.0)

        span = y_max - y_min
        if span < 0.1:
            # Near-zero span: use a reasonable default
            return [y_min - 1.0, y_max + 1.0]

        pad = span * 0.15
        return [y_min - pad, y_max + pad]

    def _create_impulse_response_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build stem plot for y[n] = p₀ⁿ."""
        n = data["n"]
        y = data["y"]
        envelope = data["envelope"]
        p0 = data["p0"]
        abs_p0 = data["abs_p0"]
        num_samples = int(self.parameters["num_samples"])
        show_envelope = bool(self.parameters["show_envelope"])
        show_unit_circle = bool(self.parameters["show_unit_circle"])
        color = self._get_stem_color()

        traces = []

        # Determine which samples to show based on animation state
        if self._animation_active and self._animation_step > 0:
            visible_count = self._animation_step
        else:
            visible_count = num_samples

        n_visible = n[:visible_count].tolist()
        y_visible = y[:visible_count].tolist()

        # Build stem plot: vertical lines from y=0 to y[n]
        stem_x = []
        stem_y = []
        for i in range(len(n_visible)):
            stem_x.extend([n_visible[i], n_visible[i], None])
            stem_y.extend([0, y_visible[i], None])

        # Stem lines
        traces.append({
            "x": stem_x,
            "y": stem_y,
            "type": "scatter",
            "mode": "lines",
            "name": "Stems",
            "line": {"color": color, "width": 2},
            "showlegend": False,
            "hoverinfo": "skip",
        })

        # Stem markers (dots at tips)
        traces.append({
            "x": n_visible,
            "y": y_visible,
            "type": "scatter",
            "mode": "markers",
            "name": f"y[n] = ({p0:g})ⁿ",
            "marker": {"color": color, "size": 10, "line": {"color": "#0a0e27", "width": 1.5}},
            "hovertemplate": "n=%{x}<br>y[n]=%{y:.4f}<extra></extra>",
        })

        # Grayed-out future samples during animation
        if self._animation_active and visible_count < num_samples:
            n_future = n[visible_count:].tolist()
            traces.append({
                "x": n_future,
                "y": [0] * len(n_future),
                "type": "scatter",
                "mode": "markers",
                "name": "Pending",
                "marker": {"color": "rgba(148,163,184,0.25)", "size": 7},
                "showlegend": False,
                "hoverinfo": "skip",
            })

        # Collect all y-values for range computation
        all_y_for_range = list(y_visible)

        # Envelope traces
        if show_envelope and abs_p0 > 0 and abs(abs_p0 - 1.0) > self.MARGINAL_EPSILON:
            n_full = n.tolist()
            env_upper = envelope.tolist()
            env_lower = (-envelope).tolist()
            traces.append({
                "x": n_full,
                "y": env_upper,
                "type": "scatter",
                "mode": "lines",
                "name": "|p₀|ⁿ envelope",
                "line": {"color": color, "width": 1, "dash": "dash"},
                "opacity": 0.4,
            })
            traces.append({
                "x": n_full,
                "y": env_lower,
                "type": "scatter",
                "mode": "lines",
                "name": "-|p₀|ⁿ envelope",
                "line": {"color": color, "width": 1, "dash": "dash"},
                "opacity": 0.4,
                "showlegend": False,
            })
            all_y_for_range.extend(env_upper)
            all_y_for_range.extend(env_lower)

        # |p₀|=1 reference lines
        if show_unit_circle:
            traces.append({
                "x": [0, num_samples - 1],
                "y": [1, 1],
                "type": "scatter",
                "mode": "lines",
                "name": "|p₀|=1 boundary",
                "line": {"color": "#ef4444", "width": 1.5, "dash": "dot"},
                "opacity": 0.6,
            })
            traces.append({
                "x": [0, num_samples - 1],
                "y": [-1, -1],
                "type": "scatter",
                "mode": "lines",
                "name": "-1 boundary",
                "line": {"color": "#ef4444", "width": 1.5, "dash": "dot"},
                "opacity": 0.6,
                "showlegend": False,
            })
            all_y_for_range.extend([1.0, -1.0])

        layout = self._get_base_layout("n (sample index)", "y[n]", "impulse_response")
        layout["xaxis"]["range"] = [-0.5, num_samples - 0.5]
        layout["yaxis"]["range"] = self._compute_y_range(all_y_for_range)

        return {
            "id": "impulse_response",
            "title": f"Impulse Response: y[n] = p₀ⁿ = ({p0:g})ⁿ",
            "data": traces,
            "layout": layout,
        }

    def _create_geometric_sum_plot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build partial sum plot: S[n] = Σ p₀ᵏ for k=0..n."""
        n = data["n"]
        partial_sums = data["partial_sums"]
        p0 = data["p0"]
        abs_p0 = data["abs_p0"]
        num_samples = int(self.parameters["num_samples"])
        color = self._get_stem_color()

        traces = []

        # Determine visible count
        if self._animation_active and self._animation_step > 0:
            visible_count = self._animation_step
        else:
            visible_count = num_samples

        n_visible = n[:visible_count].tolist()
        sums_visible = partial_sums[:visible_count].tolist()

        # Build stem plot for partial sums
        stem_x = []
        stem_y = []
        for i in range(len(n_visible)):
            stem_x.extend([n_visible[i], n_visible[i], None])
            stem_y.extend([0, sums_visible[i], None])

        traces.append({
            "x": stem_x,
            "y": stem_y,
            "type": "scatter",
            "mode": "lines",
            "name": "Stems",
            "line": {"color": color, "width": 2},
            "showlegend": False,
            "hoverinfo": "skip",
        })

        traces.append({
            "x": n_visible,
            "y": sums_visible,
            "type": "scatter",
            "mode": "markers+lines",
            "name": "S[n] = \u03a3 p\u2080\u1d4f",
            "marker": {"color": color, "size": 8, "line": {"color": "#0a0e27", "width": 1.5}},
            "line": {"color": color, "width": 1.5, "dash": "dot"},
            "hovertemplate": "n=%{x}<br>S[n]=%{y:.4f}<extra></extra>",
        })

        # Collect all y-values for range computation
        all_y_for_range = list(sums_visible)

        # Show convergence limit line when |p₀| < 1
        if abs_p0 < 1.0 - self.MARGINAL_EPSILON and abs(1.0 - p0) > 1e-10:
            limit_val = 1.0 / (1.0 - p0)
            traces.append({
                "x": [0, num_samples - 1],
                "y": [limit_val, limit_val],
                "type": "scatter",
                "mode": "lines",
                "name": f"1/(1-p\u2080) = {limit_val:.3f}",
                "line": {"color": "#3b82f6", "width": 2, "dash": "dash"},
            })
            all_y_for_range.append(limit_val)

        layout = self._get_base_layout("n (sample index)", "S[n] = \u03a3 p\u2080\u1d4f", "geometric_sum")
        layout["xaxis"]["range"] = [-0.5, num_samples - 0.5]
        layout["yaxis"]["range"] = self._compute_y_range(all_y_for_range)

        return {
            "id": "geometric_sum",
            "title": "Partial Sum: S[n] = \u03a3 p\u2080\u1d4f (Geometric Series)",
            "data": traces,
            "layout": layout,
        }
