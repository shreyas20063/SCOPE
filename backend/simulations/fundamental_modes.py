"""
Fundamental Modes Superposition Simulator

Demonstrates that any Nth-order DT system's unit-sample response is a weighted
sum of N fundamental modes (geometric sequences): y[n] = sum(A_k * p_k^n).

Default configuration reproduces a worked example:
  y[n] = 4.5*(0.9)^n - 3.5*(0.7)^n
"""

import numpy as np
from typing import Any, Dict, List, Optional
from .base_simulator import BaseSimulator


class FundamentalModesSimulator(BaseSimulator):
    """
    Fundamental Modes Superposition simulation.

    Parameters:
    - system_order: Number of poles/modes (2, 3, or 4)
    - p1..p4: Pole locations on the real line
    - A1..A4: Partial-fraction weights for each mode
    - mode: 'explore' or 'reconstruct'
    - num_samples: Number of discrete samples to display
    - difficulty: Challenge difficulty for reconstruct mode
    """

    # Maximum poles supported
    MAX_ORDER = 4
    NUM_SAMPLES_DEFAULT = 25

    # Colors for each mode (consistent between backend metadata and frontend)
    MODE_COLORS = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b"]  # blue, red, green, amber
    TOTAL_COLOR = "#f1f5f9"
    TARGET_COLOR = "#a855f7"

    # Stability threshold
    STABILITY_TOL = 1e-6

    PARAMETER_SCHEMA = {
        "system_order": {
            "type": "select",
            "label": "System Order",
            "options": [
                {"value": "2", "label": "2 Poles"},
                {"value": "3", "label": "3 Poles"},
                {"value": "4", "label": "4 Poles"},
            ],
            "default": "2",
            "description": "Number of poles (fundamental modes)",
        },
        "mode": {
            "type": "select",
            "label": "Mode",
            "options": [
                {"value": "explore", "label": "Explore"},
                {"value": "reconstruct", "label": "Reconstruct Challenge"},
            ],
            "default": "explore",
            "description": "Explore modes freely or match a mystery signal",
        },
        "num_samples": {
            "type": "slider",
            "label": "Samples",
            "min": 5,
            "max": 50,
            "step": 1,
            "default": 25,
            "unit": "",
            "description": "Number of discrete-time samples to display",
        },
        "p1": {
            "type": "slider",
            "label": "Pole p\u2081",
            "min": -1.5,
            "max": 1.5,
            "step": 0.01,
            "default": 0.9,
            "unit": "",
            "description": "Location of pole 1 on the real line",
        },
        "p2": {
            "type": "slider",
            "label": "Pole p\u2082",
            "min": -1.5,
            "max": 1.5,
            "step": 0.01,
            "default": 0.7,
            "unit": "",
            "description": "Location of pole 2 on the real line",
        },
        "p3": {
            "type": "slider",
            "label": "Pole p\u2083",
            "min": -1.5,
            "max": 1.5,
            "step": 0.01,
            "default": -0.5,
            "unit": "",
            "description": "Location of pole 3 on the real line",
        },
        "p4": {
            "type": "slider",
            "label": "Pole p\u2084",
            "min": -1.5,
            "max": 1.5,
            "step": 0.01,
            "default": 0.3,
            "unit": "",
            "description": "Location of pole 4 on the real line",
        },
        "A1": {
            "type": "slider",
            "label": "Weight A\u2081",
            "min": -5.0,
            "max": 5.0,
            "step": 0.1,
            "default": 4.5,
            "unit": "",
            "description": "Partial-fraction coefficient for mode 1",
        },
        "A2": {
            "type": "slider",
            "label": "Weight A\u2082",
            "min": -5.0,
            "max": 5.0,
            "step": 0.1,
            "default": -3.5,
            "unit": "",
            "description": "Partial-fraction coefficient for mode 2",
        },
        "A3": {
            "type": "slider",
            "label": "Weight A\u2083",
            "min": -5.0,
            "max": 5.0,
            "step": 0.1,
            "default": 1.0,
            "unit": "",
            "description": "Partial-fraction coefficient for mode 3",
        },
        "A4": {
            "type": "slider",
            "label": "Weight A\u2084",
            "min": -5.0,
            "max": 5.0,
            "step": 0.1,
            "default": 1.0,
            "unit": "",
            "description": "Partial-fraction coefficient for mode 4",
        },
        "difficulty": {
            "type": "select",
            "label": "Difficulty",
            "options": [
                {"value": "easy", "label": "Easy (2 poles)"},
                {"value": "medium", "label": "Medium (3 poles)"},
                {"value": "hard", "label": "Hard (4 poles)"},
            ],
            "default": "easy",
            "description": "Challenge difficulty level",
        },
        "new_challenge": {
            "type": "button",
            "label": "New Challenge",
            "default": None,
            "description": "Generate a new mystery signal to reconstruct",
        },
        "show_answer": {
            "type": "button",
            "label": "Reveal Answer",
            "default": None,
            "description": "Show the hidden poles and weights",
        },
    }

    DEFAULT_PARAMS = {
        "system_order": "2",
        "mode": "explore",
        "num_samples": 25,
        "p1": 0.9,
        "p2": 0.7,
        "p3": -0.5,
        "p4": 0.3,
        "A1": 4.5,
        "A2": -3.5,
        "A3": 1.0,
        "A4": 1.0,
        "difficulty": "easy",
        "new_challenge": None,
        "show_answer": None,
    }


    # Plot styling constants
    GRID_COLOR = "rgba(148, 163, 184, 0.2)"
    ZEROLINE_COLOR = "rgba(148, 163, 184, 0.3)"
    LEGEND_BG = "rgba(15, 23, 42, 0.8)"
    LEGEND_BORDER = "rgba(148, 163, 184, 0.2)"
    FILL_STABLE = "rgba(52, 211, 153, 0.08)"
    UNIT_CIRCLE_COLOR = "#a855f7"

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        # Computed data
        self._n: Optional[np.ndarray] = None
        self._modes: Optional[np.ndarray] = None
        self._total: Optional[np.ndarray] = None
        self._envelopes: Optional[np.ndarray] = None
        self._mode_info: List[Dict[str, Any]] = []
        # Reconstruct challenge state
        self._challenge_poles: Optional[np.ndarray] = None
        self._challenge_weights: Optional[np.ndarray] = None
        self._challenge_target: Optional[np.ndarray] = None
        self._challenge_revealed: bool = False
        self._rms_error: float = 0.0
        self._revision_counter: int = 0

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        """Initialize simulation with parameters."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        if params:
            for name, value in params.items():
                if name in self.parameters:
                    self.parameters[name] = self._validate_param(name, value)
        self._initialized = True
        self._compute()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        """Update a single parameter and recompute."""
        old_value = self.parameters.get(name)
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)

            # When entering reconstruct mode, always generate fresh challenge
            if name == "mode" and value == "reconstruct" and old_value != "reconstruct":
                self._generate_challenge()

            # When changing difficulty in reconstruct mode, generate new challenge
            if name == "difficulty" and self.parameters["mode"] == "reconstruct":
                self._generate_challenge()

        self._compute()
        return self.get_state()

    def handle_action(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle custom button actions."""
        if action == "new_challenge":
            self._generate_challenge()
            self._compute()
        elif action == "show_answer":
            self._challenge_revealed = True
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        """Reset simulation to default parameters."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._challenge_poles = None
        self._challenge_weights = None
        self._challenge_target = None
        self._challenge_revealed = False
        self._initialized = True
        self._compute()
        return self.get_state()

    # =========================================================================
    # Core computation
    # =========================================================================

    def _get_active_poles_weights(self) -> tuple:
        """Get active poles and weights based on current system order."""
        order = int(self.parameters["system_order"])
        poles = np.array([
            self.parameters["p1"],
            self.parameters["p2"],
            self.parameters["p3"],
            self.parameters["p4"],
        ])[:order]
        weights = np.array([
            self.parameters["A1"],
            self.parameters["A2"],
            self.parameters["A3"],
            self.parameters["A4"],
        ])[:order]
        return order, poles, weights

    def _compute(self) -> None:
        """Compute all modes, total response, and envelopes."""
        order, poles, weights = self._get_active_poles_weights()
        num_samples = int(self.parameters["num_samples"])

        self._n = np.arange(num_samples)

        # Vectorized: modes[k, n] = A_k * p_k^n
        # Handle 0^0 = 1 (NumPy default behavior)
        self._modes = weights[:, None] * np.power(poles[:, None], self._n[None, :])

        # Total response
        self._total = np.sum(self._modes, axis=0)

        # Amplitude envelopes: |A_k| * |p_k|^n
        self._envelopes = np.abs(weights[:, None]) * np.power(
            np.abs(poles[:, None]), self._n[None, :]
        )

        # Mode analysis info
        self._mode_info = []
        for k in range(order):
            p = poles[k]
            A = weights[k]
            abs_p = abs(p)

            if abs_p < 1.0 - self.STABILITY_TOL:
                convergence = "converges"
                half_life = np.log(0.5) / np.log(abs_p) if abs_p > 0 else 0.0
            elif abs_p > 1.0 + self.STABILITY_TOL:
                convergence = "diverges"
                half_life = None
            else:
                convergence = "marginal"
                half_life = None

            sign_behavior = "alternating" if p < 0 else "monotonic"

            self._mode_info.append({
                "index": k + 1,
                "pole": round(float(p), 4),
                "weight": round(float(A), 4),
                "color": self.MODE_COLORS[k],
                "convergence": convergence,
                "sign_behavior": sign_behavior,
                "half_life": round(float(half_life), 2) if half_life is not None else None,
                "abs_pole": round(float(abs_p), 4),
            })

        # Reconstruct mode: compute RMS error against target
        if self.parameters["mode"] == "reconstruct" and self._challenge_target is not None:
            target_len = len(self._challenge_target)
            user_len = len(self._total)
            compare_len = min(target_len, user_len)
            if compare_len > 0:
                self._rms_error = float(np.sqrt(np.mean(
                    (self._total[:compare_len] - self._challenge_target[:compare_len]) ** 2
                )))
            else:
                self._rms_error = float("inf")

        self._revision_counter += 1

    def _generate_challenge(self) -> None:
        """Generate a random mystery signal for reconstruct mode."""
        difficulty = self.parameters["difficulty"]
        rng = np.random.default_rng()

        if difficulty == "easy":
            n_poles = 2
            pole_range = 0.85
        elif difficulty == "medium":
            n_poles = 3
            pole_range = 0.9
        else:
            n_poles = 4
            pole_range = 0.95

        # Generate random stable poles (spread apart for easier identification)
        poles = rng.uniform(-pole_range, pole_range, size=n_poles)
        # Ensure poles are sufficiently separated
        for attempt in range(50):
            if n_poles <= 1:
                break
            min_sep = np.min(np.abs(np.diff(np.sort(poles))))
            if min_sep > 0.2:
                break
            poles = rng.uniform(-pole_range, pole_range, size=n_poles)

        # Generate random weights (reasonable magnitude, at least one positive and one negative)
        weights = rng.uniform(-4.0, 4.0, size=n_poles)
        # Round to 1 decimal for cleaner answers
        weights = np.round(weights, 1)
        poles = np.round(poles, 2)

        # Ensure non-trivial weights
        weights[np.abs(weights) < 0.5] = rng.choice([-1.0, 1.0], size=np.sum(np.abs(weights) < 0.5))

        self._challenge_poles = poles
        self._challenge_weights = weights
        self._challenge_revealed = False

        # Compute target signal
        num_samples = int(self.parameters["num_samples"])
        n = np.arange(num_samples)
        self._challenge_target = np.sum(
            weights[:, None] * np.power(poles[:, None], n[None, :]),
            axis=0,
        )

        # Update system order to match difficulty
        self.parameters["system_order"] = str(n_poles)

    # =========================================================================
    # Plot generation
    # =========================================================================

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate all Plotly plot dictionaries."""
        if not self._initialized:
            self.initialize()

        return [
            self._create_modes_overlay_plot(),
            self._create_pole_map_plot(),
            self._create_envelopes_plot(),
        ]

    def _create_stem_traces(
        self, n: np.ndarray, y: np.ndarray, color: str, name: str, width: float = 1.5, showlegend: bool = True
    ) -> List[Dict[str, Any]]:
        """Create Plotly traces for a stem plot (markers + vertical lines)."""
        traces = []

        # Vertical lines from 0 to y[n] using None separators
        x_lines = []
        y_lines = []
        for i in range(len(n)):
            x_lines.extend([float(n[i]), float(n[i]), None])
            y_lines.extend([0.0, float(y[i]), None])

        traces.append({
            "x": x_lines,
            "y": y_lines,
            "type": "scatter",
            "mode": "lines",
            "line": {"color": color, "width": width},
            "showlegend": False,
            "hoverinfo": "skip",
        })

        # Markers at tips
        traces.append({
            "x": n.tolist(),
            "y": y.tolist(),
            "type": "scatter",
            "mode": "markers",
            "marker": {"color": color, "size": 7, "line": {"color": color, "width": 1}},
            "name": name,
            "showlegend": showlegend,
            "hovertemplate": f"{name}<br>n = %{{x}}<br>y[n] = %{{y:.4f}}<extra></extra>",
        })

        return traces

    def _create_modes_overlay_plot(self) -> Dict[str, Any]:
        """Create the main stem plot showing individual modes and total."""
        order, poles, weights = self._get_active_poles_weights()
        is_reconstruct = self.parameters["mode"] == "reconstruct"

        traces = []

        # Individual mode stems
        for k in range(order):
            mode_label = f"Mode {k+1}: {weights[k]:.1f}\u00b7({poles[k]:.2f})\u207f"
            traces.extend(self._create_stem_traces(
                self._n, self._modes[k], self.MODE_COLORS[k], mode_label, width=1.5,
            ))

        # Total response stems (thicker)
        traces.extend(self._create_stem_traces(
            self._n, self._total, self.TOTAL_COLOR, "Total y[n]", width=2.5,
        ))

        # Reconstruct mode: show target
        if is_reconstruct and self._challenge_target is not None:
            compare_len = min(len(self._n), len(self._challenge_target))
            traces.extend(self._create_stem_traces(
                self._n[:compare_len],
                self._challenge_target[:compare_len],
                self.TARGET_COLOR,
                "Target (mystery)",
                width=2.0,
            ))

        title = "Fundamental Modes & Total Response"
        if is_reconstruct:
            title = "Reconstruct: Match the Target Signal"

        return {
            "id": "modes_overlay",
            "title": title,
            "plotType": "main",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Sample index n",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "dtick": 5,
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "y[n]",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "zerolinewidth": 1.5,
                    "autorange": True,
                    "fixedrange": False,
                },
                "legend": {
                    "x": 0.98, "y": 0.98,
                    "xanchor": "right", "yanchor": "top",
                    "bgcolor": self.LEGEND_BG,
                    "bordercolor": self.LEGEND_BORDER,
                    "borderwidth": 1,
                    "font": {"size": 11},
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 55},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": f"modes_overlay_{self._revision_counter}",
            },
        }

    def _create_pole_map_plot(self) -> Dict[str, Any]:
        """Create Z-plane pole location plot with unit circle."""
        order, poles, _ = self._get_active_poles_weights()

        traces = []

        # Unit circle (stability boundary)
        theta = np.linspace(0, 2 * np.pi, 200)
        traces.append({
            "x": np.cos(theta).tolist(),
            "y": np.sin(theta).tolist(),
            "type": "scatter",
            "fill": "toself",
            "fillcolor": self.FILL_STABLE,
            "line": {"color": self.UNIT_CIRCLE_COLOR, "width": 2.5},
            "name": "Unit Circle (|z| = 1)",
            "hoverinfo": "skip",
        })

        # Real axis emphasis
        traces.append({
            "x": [-1.8, 1.8],
            "y": [0, 0],
            "type": "scatter",
            "mode": "lines",
            "line": {"color": self.ZEROLINE_COLOR, "width": 1.5},
            "showlegend": False,
            "hoverinfo": "skip",
        })

        # Pole markers (color-coded to match modes)
        for k in range(order):
            p = poles[k]
            is_stable = abs(p) < 1.0
            status = "stable" if is_stable else ("marginal" if abs(abs(p) - 1.0) < self.STABILITY_TOL else "unstable")
            traces.append({
                "x": [float(p)],
                "y": [0],
                "type": "scatter",
                "mode": "markers+text",
                "marker": {
                    "symbol": "x",
                    "size": 16,
                    "color": self.MODE_COLORS[k],
                    "line": {"width": 3, "color": self.MODE_COLORS[k]},
                },
                "text": [f"p{k+1}={p:.2f}"],
                "textposition": "top center",
                "textfont": {"color": self.MODE_COLORS[k], "size": 11},
                "name": f"p{chr(0x2081 + k)}",
                "showlegend": False,
                "hovertemplate": f"Pole {k+1}<br>p = {p:.4f}<br>|p| = {abs(p):.4f}<br>{status}<extra></extra>",
            })

        # Stability boundary markers at -1 and 1
        traces.append({
            "x": [-1, 1],
            "y": [0, 0],
            "type": "scatter",
            "mode": "markers",
            "marker": {"symbol": "line-ns", "size": 12, "color": self.UNIT_CIRCLE_COLOR, "line": {"width": 2}},
            "showlegend": False,
            "hoverinfo": "skip",
        })

        return {
            "id": "pole_map",
            "title": "Pole Locations (Z-Plane)",
            "plotType": "main",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Real (Re)",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": False,
                    "range": [-1.8, 1.8],
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Imaginary (Im)",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": False,
                    "range": [-1.8, 1.8],
                    "scaleanchor": "x",
                    "scaleratio": 1,
                    "fixedrange": False,
                },
                "legend": {
                    "x": 0.02, "y": 0.98,
                    "xanchor": "left", "yanchor": "top",
                    "bgcolor": self.LEGEND_BG,
                    "bordercolor": self.LEGEND_BORDER,
                    "borderwidth": 1,
                    "font": {"size": 11},
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "pole_map",
            },
        }

    def _create_envelopes_plot(self) -> Dict[str, Any]:
        """Create mode competition envelope plot showing |A_k * p_k^n|."""
        order, poles, weights = self._get_active_poles_weights()

        traces = []

        # Continuous envelope lines for smooth visualization
        n_fine = np.linspace(0, int(self.parameters["num_samples"]) - 1, 200)
        for k in range(order):
            env = np.abs(weights[k]) * np.power(np.abs(poles[k]), n_fine)
            traces.append({
                "x": n_fine.tolist(),
                "y": env.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": f"Mode {k+1}: {abs(weights[k]):.1f}\u00b7|{poles[k]:.2f}|\u207f",
                "line": {"color": self.MODE_COLORS[k], "width": 2.5},
                "hovertemplate": f"Mode {k+1}<br>n = %{{x:.1f}}<br>|A\u00b7p\u207f| = %{{y:.4f}}<extra></extra>",
            })

        return {
            "id": "mode_envelopes",
            "title": "Mode Competition (Amplitude Envelopes)",
            "plotType": "main",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Sample index n",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "|A\u2096\u00b7p\u2096\u207f|",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "autorange": True,
                    "rangemode": "tozero",
                    "fixedrange": False,
                },
                "legend": {
                    "x": 0.98, "y": 0.98,
                    "xanchor": "right", "yanchor": "top",
                    "bgcolor": self.LEGEND_BG,
                    "bordercolor": self.LEGEND_BORDER,
                    "borderwidth": 1,
                    "font": {"size": 11},
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 55},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": f"mode_envelopes_{self._revision_counter}",
            },
        }

    # =========================================================================
    # State
    # =========================================================================

    def get_state(self) -> Dict[str, Any]:
        """Return current simulation state with metadata for custom viewer."""
        if not self._initialized:
            self.initialize()

        state = super().get_state()

        order, poles, weights = self._get_active_poles_weights()
        is_reconstruct = self.parameters["mode"] == "reconstruct"

        # Build equation string: y[n] = A1·(p1)ⁿ + A2·(p2)ⁿ + ...
        terms = []
        for k in range(order):
            if k == 0:
                terms.append(f"{weights[k]:.1f}\u00b7({poles[k]:.2f})\u207f")
            elif weights[k] >= 0:
                terms.append(f"+ {weights[k]:.1f}\u00b7({poles[k]:.2f})\u207f")
            else:
                terms.append(f"\u2212 {abs(weights[k]):.1f}\u00b7({poles[k]:.2f})\u207f")
        equation = "y[n] = " + " ".join(terms)

        # Performance rating for reconstruct mode
        reconstruct_info = None
        if is_reconstruct and self._challenge_target is not None:
            if self._rms_error < 0.1:
                rating = "EXCELLENT"
            elif self._rms_error < 0.3:
                rating = "GOOD"
            elif self._rms_error < 0.8:
                rating = "FAIR"
            else:
                rating = "POOR"

            reconstruct_info = {
                "rms_error": round(self._rms_error, 4),
                "rating": rating,
                "revealed": self._challenge_revealed,
                "target_order": len(self._challenge_poles) if self._challenge_poles is not None else 0,
            }
            if self._challenge_revealed and self._challenge_poles is not None:
                reconstruct_info["answer_poles"] = self._challenge_poles.tolist()
                reconstruct_info["answer_weights"] = self._challenge_weights.tolist()

        state["metadata"] = {
            "simulation_type": "fundamental_modes",
            "hub_slots": self.HUB_SLOTS,
            "hub_domain": self.HUB_DOMAIN,
            "hub_dimensions": self.HUB_DIMENSIONS,
            "sticky_controls": True,
            "equation": equation,
            "mode_info": self._mode_info,
            "system_order": int(self.parameters["system_order"]),
            "is_reconstruct": is_reconstruct,
            "reconstruct_info": reconstruct_info,
        }

        return state
