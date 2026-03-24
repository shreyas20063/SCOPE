"""
Complex Poles & Sinusoidal Modes Simulator

Visualizes how complex conjugate poles of a CT second-order system (mass-spring-damper)
produce sinusoidal oscillation from the superposition of two complex exponential modes.
Shows s-plane pole locations, mode decomposition, Taylor series convergence, and a 3D
helix view of the complex exponential.
"""

import math
import numpy as np
from typing import Any, Dict, List, Optional
from .base_simulator import BaseSimulator


class ComplexPolesModesSimulator(BaseSimulator):
    """
    Complex Poles & Sinusoidal Modes simulation.

    Models: M y'' + b y' + K y = delta(t)
    Poles: s = -sigma +/- j omega_d
    Impulse response: h(t) = (1/(M omega_d)) e^(-sigma t) sin(omega_d t) u(t)

    Parameters:
    - K: Spring constant (N/m)
    - M: Mass (kg)
    - b: Damping coefficient (Ns/m)
    - num_taylor_terms: Number of Taylor series terms to display
    - time_window: Duration of time axis (s)
    """

    NUM_SAMPLES = 1000
    TAYLOR_CLAMP_FACTOR = 5.0

    # Plot colors (project palette)
    BLUE = "#3b82f6"
    RED = "#ef4444"
    GREEN = "#10b981"
    TEAL = "#14b8a6"
    WHITE = "#f1f5f9"
    AMBER = "#f59e0b"
    PURPLE = "#a855f7"
    CYAN = "#06b6d4"
    PINK = "#ec4899"

    TAYLOR_COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#a855f7",
                     "#06b6d4", "#ec4899", "#14b8a6", "#8b5cf6", "#f97316",
                     "#22d3ee", "#e879f9", "#34d399", "#fb923c", "#818cf8"]

    # Plot styling
    GRID_COLOR = "rgba(148, 163, 184, 0.2)"
    ZEROLINE_COLOR = "rgba(148, 163, 184, 0.3)"
    LEGEND_BG = "rgba(15, 23, 42, 0.8)"
    LEGEND_BORDER = "rgba(148, 163, 184, 0.2)"
    FILL_STABLE = "rgba(52, 211, 153, 0.08)"

    PARAMETER_SCHEMA = {
        "K": {
            "type": "slider", "label": "Spring Constant (K)",
            "min": 1.0, "max": 100.0, "step": 1.0, "default": 10.0,
            "unit": "N/m",
        },
        "M": {
            "type": "slider", "label": "Mass (M)",
            "min": 0.1, "max": 5.0, "step": 0.1, "default": 1.0,
            "unit": "kg",
        },
        "b": {
            "type": "slider", "label": "Damping (b)",
            "min": 0.0, "max": 10.0, "step": 0.1, "default": 0.0,
            "unit": "Ns/m",
        },
        "num_taylor_terms": {
            "type": "slider", "label": "Taylor Terms",
            "min": 1, "max": 15, "step": 1, "default": 5,
        },
        "time_window": {
            "type": "slider", "label": "Time Window",
            "min": 1.0, "max": 20.0, "step": 0.5, "default": 5.0,
            "unit": "s",
        },
    }

    DEFAULT_PARAMS = {
        "K": 10.0,
        "M": 1.0,
        "b": 0.0,
        "num_taylor_terms": 5,
        "time_window": 5.0,
    }

    HUB_SLOTS = ['control']

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._omega_0: float = 0.0
        self._sigma: float = 0.0
        self._zeta: float = 0.0
        self._omega_d: Optional[float] = None
        self._damping_type: str = "undamped"
        self._pole_s1: complex = 0j
        self._pole_s2: complex = 0j
        self._t: Optional[np.ndarray] = None
        self._revision: int = 0

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            self.parameters[name] = self._validate_param(name, value)
        self._initialized = True
        self._compute_system()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
        self._compute_system()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        """Reset to default parameters and recompute system."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._initialized = True
        self._revision = 0
        self._compute_system()
        return self.get_state()

    # =========================================================================
    # Core computation
    # =========================================================================

    def _compute_system(self) -> None:
        """Compute system parameters from K, M, b."""
        K = float(self.parameters["K"])
        M = float(self.parameters["M"])
        b = float(self.parameters["b"])

        self._omega_0 = np.sqrt(K / M)
        self._sigma = b / (2.0 * M)
        self._zeta = b / (2.0 * np.sqrt(M * K))

        discriminant = self._sigma**2 - self._omega_0**2

        if self._zeta < 1.0 - 1e-6:
            self._damping_type = "undamped" if self._zeta < 1e-6 else "underdamped"
            self._omega_d = np.sqrt(self._omega_0**2 - self._sigma**2)
            self._pole_s1 = complex(-self._sigma, self._omega_d)
            self._pole_s2 = complex(-self._sigma, -self._omega_d)
        elif self._zeta <= 1.0 + 1e-6:
            self._damping_type = "critically_damped"
            self._omega_d = None
            self._pole_s1 = complex(-self._sigma, 0)
            self._pole_s2 = complex(-self._sigma, 0)
        else:
            self._damping_type = "overdamped"
            self._omega_d = None
            sqrt_term = np.sqrt(discriminant)
            self._pole_s1 = complex(-self._sigma + sqrt_term, 0)
            self._pole_s2 = complex(-self._sigma - sqrt_term, 0)

        T = float(self.parameters["time_window"])
        self._t = np.linspace(0, T, self.NUM_SAMPLES)
        self._revision += 1

    # =========================================================================
    # Plot generation
    # =========================================================================

    def get_plots(self) -> List[Dict[str, Any]]:
        if not self._initialized:
            self.initialize()
        plots = [
            self._create_s_plane_plot(),
            self._create_mode_decomposition_plot(),
        ]
        # Taylor and helix only meaningful for oscillatory systems
        if self._damping_type in ("undamped", "underdamped"):
            plots.append(self._create_taylor_plot())
            plots.append(self._create_helix_3d_plot())
        return plots

    def _create_s_plane_plot(self) -> Dict[str, Any]:
        """S-plane with conjugate poles, stability regions, omega_0 circle."""
        traces = []

        # Determine axis range
        max_val = max(abs(self._pole_s1.real), abs(self._pole_s1.imag),
                      self._omega_0, 1.0) * 1.5

        # Left half-plane shading (stable region)
        traces.append({
            "x": [-max_val, 0, 0, -max_val],
            "y": [-max_val, -max_val, max_val, max_val],
            "type": "scatter",
            "fill": "toself",
            "fillcolor": self.FILL_STABLE,
            "line": {"width": 0},
            "name": "Stable (LHP)",
            "hoverinfo": "skip",
            "showlegend": True,
        })

        # Imaginary axis (stability boundary)
        traces.append({
            "x": [0, 0],
            "y": [-max_val, max_val],
            "type": "scatter",
            "mode": "lines",
            "line": {"color": self.PURPLE, "width": 1.5, "dash": "dash"},
            "name": "jω axis",
            "hoverinfo": "skip",
        })

        # Real axis
        traces.append({
            "x": [-max_val, max_val],
            "y": [0, 0],
            "type": "scatter",
            "mode": "lines",
            "line": {"color": self.ZEROLINE_COLOR, "width": 1},
            "showlegend": False,
            "hoverinfo": "skip",
        })

        # ω₀ circle
        theta = np.linspace(0, 2 * np.pi, 200)
        traces.append({
            "x": (self._omega_0 * np.cos(theta)).tolist(),
            "y": (self._omega_0 * np.sin(theta)).tolist(),
            "type": "scatter",
            "mode": "lines",
            "line": {"color": self.AMBER, "width": 1.5, "dash": "dot"},
            "name": f"|s| = ω₀ = {self._omega_0:.2f}",
            "hoverinfo": "skip",
        })

        # Pole markers
        s1_r, s1_i = self._pole_s1.real, self._pole_s1.imag
        s2_r, s2_i = self._pole_s2.real, self._pole_s2.imag

        traces.append({
            "x": [s1_r],
            "y": [s1_i],
            "type": "scatter",
            "mode": "markers+text",
            "marker": {"symbol": "x", "size": 14, "color": self.BLUE,
                       "line": {"width": 3, "color": self.BLUE}},
            "text": [f"s₁ = {s1_r:.2f}{'+' if s1_i >= 0 else ''}{s1_i:.2f}j"],
            "textposition": "top right",
            "textfont": {"color": self.BLUE, "size": 11},
            "name": "Pole s₁",
        })

        traces.append({
            "x": [s2_r],
            "y": [s2_i],
            "type": "scatter",
            "mode": "markers+text",
            "marker": {"symbol": "x", "size": 14, "color": self.RED,
                       "line": {"width": 3, "color": self.RED}},
            "text": [f"s₂ = {s2_r:.2f}{'+' if s2_i >= 0 else ''}{s2_i:.2f}j"],
            "textposition": "bottom right",
            "textfont": {"color": self.RED, "size": 11},
            "name": "Pole s₂",
        })

        # Annotation lines from poles to axes (σ and ωd decomposition)
        if self._damping_type in ("undamped", "underdamped"):
            # Horizontal line from pole to imaginary axis (shows σ)
            traces.append({
                "x": [s1_r, 0],
                "y": [s1_i, s1_i],
                "type": "scatter",
                "mode": "lines",
                "line": {"color": "rgba(148,163,184,0.5)", "width": 1, "dash": "dot"},
                "showlegend": False,
                "hoverinfo": "skip",
            })
            # Vertical line from pole to real axis (shows ωd)
            traces.append({
                "x": [s1_r, s1_r],
                "y": [0, s1_i],
                "type": "scatter",
                "mode": "lines",
                "line": {"color": "rgba(148,163,184,0.5)", "width": 1, "dash": "dot"},
                "showlegend": False,
                "hoverinfo": "skip",
            })

        return {
            "id": "s_plane",
            "title": "S-Plane Pole Locations",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Real (σ)",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "range": [-max_val, max_val],
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Imaginary (jω)",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "range": [-max_val, max_val],
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
                "margin": {"l": 60, "r": 30, "t": 50, "b": 55},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": f"s_plane_{self._revision}",
            },
        }

    def _create_mode_decomposition_plot(self) -> Dict[str, Any]:
        """Time-domain mode decomposition: Re{c₁e^(s₁t)}, Re{c₂e^(s₂t)}, h(t)."""
        t = self._t
        M = float(self.parameters["M"])
        traces = []

        if self._damping_type in ("undamped", "underdamped"):
            omega_d = self._omega_d
            sigma = self._sigma
            # c₁ = 1/(2j·M·ωd), c₂ = -1/(2j·M·ωd) = conj(c₁)
            # Mode 1: Re{c₁·e^(s₁t)} = (1/(2Mωd))·e^(-σt)·sin(ωd·t)...
            # Actually: c₁ = 1/(2j·M·ωd), e^(s₁t) = e^(-σt)·e^(jωd·t)
            # c₁·e^(s₁t) = (1/(2j·M·ωd))·e^(-σt)·(cos(ωd·t) + j·sin(ωd·t))
            # Re{c₁·e^(s₁t)} = (1/(2M·ωd))·e^(-σt)·sin(ωd·t)
            # But let's show the full complex exponential modes more intuitively:
            # e^(s₁t) = e^(-σt)·cos(ωd·t) + j·e^(-σt)·sin(ωd·t)
            # Re{e^(s₁t)} = e^(-σt)·cos(ωd·t)
            # Re{e^(s₂t)} = e^(-σt)·cos(ωd·t) (same real part for conjugate)
            # Instead show the two complex exponential contributions to h(t):
            # h(t) = (1/(Mωd))·e^(-σt)·sin(ωd·t)
            #       = (1/(2jMωd))·e^(s₁t) + (-1/(2jMωd))·e^(s₂t)

            decay = np.exp(-sigma * t)
            cos_part = decay * np.cos(omega_d * t)
            sin_part = decay * np.sin(omega_d * t)

            scale = 1.0 / (M * omega_d) if omega_d > 1e-10 else 0.0

            # Mode 1: Re{c₁·e^(s₁t)} = scale/2 · sin(ωd·t)·e^(-σt)
            mode1 = (scale / 2.0) * sin_part
            # Mode 2: Re{c₂·e^(s₂t)} = scale/2 · sin(ωd·t)·e^(-σt)
            # Actually these are equal! Let's instead show the cosine and sine decomposition:
            # Show Re{e^(s₁t)} and Re{e^(s₂t)} (which are both cos),
            # and then show their combination with proper weights gives sin.

            # Better approach: show the two complex exponentials directly
            # Re{e^(s₁t)} = e^(-σt)·cos(ωd·t)
            # Im{e^(s₁t)} = e^(-σt)·sin(ωd·t)
            # h(t) = Im{e^(s₁t)} / (M·ωd) = the impulse response

            # For pedagogical clarity, show:
            # 1. e^(-σt)·cos(ωd·t) -- the real part of the mode
            # 2. e^(-σt)·sin(ωd·t) -- the imaginary part of the mode
            # 3. h(t) = (1/(Mωd))·e^(-σt)·sin(ωd·t) -- weighted sine = impulse response

            traces.append({
                "x": t.tolist(),
                "y": cos_part.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": f"Re{{e^(s₁t)}} = e^(-{sigma:.2f}t)·cos({omega_d:.2f}t)",
                "line": {"color": self.BLUE, "width": 2},
            })

            traces.append({
                "x": t.tolist(),
                "y": sin_part.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": f"Im{{e^(s₁t)}} = e^(-{sigma:.2f}t)·sin({omega_d:.2f}t)",
                "line": {"color": self.RED, "width": 2},
            })

            h_t = scale * sin_part
            traces.append({
                "x": t.tolist(),
                "y": h_t.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": f"h(t) = ({scale:.3f})·e^(-σt)·sin(ωd·t)",
                "line": {"color": self.WHITE, "width": 2.5},
            })

            # Decay envelope
            if sigma > 1e-6:
                envelope_pos = scale * decay
                envelope_neg = -scale * decay
                traces.append({
                    "x": t.tolist(),
                    "y": envelope_pos.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Envelope ±(1/Mωd)·e^(-σt)",
                    "line": {"color": self.GREEN, "width": 1.5, "dash": "dash"},
                })
                traces.append({
                    "x": t.tolist(),
                    "y": envelope_neg.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "showlegend": False,
                    "line": {"color": self.GREEN, "width": 1.5, "dash": "dash"},
                })

        elif self._damping_type == "critically_damped":
            sigma = self._sigma
            # h(t) = (1/M)·t·e^(-σt)
            h_t = (1.0 / M) * t * np.exp(-sigma * t)
            mode1 = np.exp(-sigma * t)
            mode2 = t * np.exp(-sigma * t)

            traces.append({
                "x": t.tolist(),
                "y": mode1.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": f"Mode 1: e^(-{sigma:.2f}t)",
                "line": {"color": self.BLUE, "width": 2},
            })
            traces.append({
                "x": t.tolist(),
                "y": mode2.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": f"Mode 2: t·e^(-{sigma:.2f}t)",
                "line": {"color": self.RED, "width": 2},
            })
            traces.append({
                "x": t.tolist(),
                "y": h_t.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": f"h(t) = (1/M)·t·e^(-σt)",
                "line": {"color": self.WHITE, "width": 2.5},
            })

        else:  # overdamped
            s1 = self._pole_s1.real
            s2 = self._pole_s2.real
            diff = s1 - s2 if abs(s1 - s2) > 1e-10 else 1.0
            scale = 1.0 / (M * diff)

            mode1 = np.exp(s1 * t)
            mode2 = np.exp(s2 * t)
            h_t = scale * (mode1 - mode2)

            traces.append({
                "x": t.tolist(),
                "y": (scale * mode1).tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": f"Mode 1: ({scale:.3f})·e^({s1:.2f}t)",
                "line": {"color": self.BLUE, "width": 2},
            })
            traces.append({
                "x": t.tolist(),
                "y": (-scale * mode2).tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": f"Mode 2: ({-scale:.3f})·e^({s2:.2f}t)",
                "line": {"color": self.RED, "width": 2},
            })
            traces.append({
                "x": t.tolist(),
                "y": h_t.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "h(t) — sum of modes",
                "line": {"color": self.WHITE, "width": 2.5},
            })

        return {
            "id": "mode_decomposition",
            "title": "Mode Decomposition → Impulse Response h(t)",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Time (s)",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "range": [0, float(self.parameters["time_window"])],
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Amplitude",
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
                    "font": {"size": 10},
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 55},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": f"modes_{self._revision}",
            },
        }

    def _create_taylor_plot(self) -> Dict[str, Any]:
        """Taylor series partial sums converging to sin(ω₀t)."""
        t = self._t
        omega_0 = self._omega_0
        num_terms = int(self.parameters["num_taylor_terms"])

        # True function: (1/(M*ωd)) * sin(ωd*t) for undamped → (1/(M*ω₀)) * sin(ω₀*t)
        # For Taylor view, show sin(ω₀t) directly (the oscillatory core)
        true_sin = np.sin(omega_0 * t)
        clamp_val = self.TAYLOR_CLAMP_FACTOR * max(np.max(np.abs(true_sin)), 1.0)

        traces = []

        # True sin (reference)
        traces.append({
            "x": t.tolist(),
            "y": true_sin.tolist(),
            "type": "scatter",
            "mode": "lines",
            "name": f"sin({omega_0:.2f}·t)",
            "line": {"color": self.WHITE, "width": 2.5, "dash": "dash"},
        })

        # Partial sums: sin(x) ≈ Σ (-1)^k x^(2k+1) / (2k+1)!
        x = omega_0 * t
        partial_sum = np.zeros_like(t)
        for k in range(num_terms):
            power = 2 * k + 1
            # Use log-space computation to avoid overflow for large arguments
            term = ((-1.0) ** k) * np.power(x, power) / float(math.factorial(power))
            partial_sum = partial_sum + term

            # Only show a subset of partial sums to avoid clutter
            # Show first 3 terms, then every other, plus always the last
            show = (k < 3) or (k % 2 == 0) or (k == num_terms - 1)
            if show:
                clamped = np.clip(partial_sum, -clamp_val, clamp_val)
                color = self.TAYLOR_COLORS[k % len(self.TAYLOR_COLORS)]
                is_last = (k == num_terms - 1)
                traces.append({
                    "x": t.tolist(),
                    "y": clamped.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": f"N={power} terms",
                    "line": {
                        "color": color,
                        "width": 2.5 if is_last else 1.5,
                    },
                    "opacity": 1.0 if is_last else 0.7,
                })

        return {
            "id": "taylor_convergence",
            "title": f"Taylor Series: sin({omega_0:.1f}·t) ≈ Σ(-1)^k (ω₀t)^(2k+1)/(2k+1)!",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Time (s)",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "range": [0, float(self.parameters["time_window"])],
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Amplitude",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "range": [-clamp_val, clamp_val],
                    "fixedrange": False,
                },
                "legend": {
                    "x": 0.98, "y": 0.98,
                    "xanchor": "right", "yanchor": "top",
                    "bgcolor": self.LEGEND_BG,
                    "bordercolor": self.LEGEND_BORDER,
                    "borderwidth": 1,
                    "font": {"size": 10},
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 55},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": f"taylor_{self._revision}",
            },
        }

    def _create_helix_3d_plot(self) -> Dict[str, Any]:
        """3D helix: e^(jω₀t) in (t, Re, Im) space with projections."""
        omega = self._omega_d if self._omega_d is not None else self._omega_0
        sigma = self._sigma
        T = float(self.parameters["time_window"])

        t = np.linspace(0, T, self.NUM_SAMPLES)
        decay = np.exp(-sigma * t)
        re_part = decay * np.cos(omega * t)
        im_part = decay * np.sin(omega * t)

        traces = []

        # Main helix trace
        traces.append({
            "type": "scatter3d",
            "x": t.tolist(),
            "y": re_part.tolist(),
            "z": im_part.tolist(),
            "mode": "lines",
            "name": "e^(st)" if sigma > 1e-6 else "e^(jω₀t)",
            "line": {"color": self.TEAL, "width": 4},
            "hovertemplate": "t=%{x:.2f}s<br>Re=%{y:.3f}<br>Im=%{z:.3f}<extra></extra>",
        })

        # Real projection on floor (z = floor_val)
        floor_val = -1.3
        traces.append({
            "type": "scatter3d",
            "x": t.tolist(),
            "y": re_part.tolist(),
            "z": [floor_val] * len(t),
            "mode": "lines",
            "name": "Re projection → cos(ωt)",
            "line": {"color": self.BLUE, "width": 2, "dash": "dot"},
        })

        # Imaginary projection on wall (y = wall_val)
        wall_val = -1.3
        traces.append({
            "type": "scatter3d",
            "x": t.tolist(),
            "y": [wall_val] * len(t),
            "z": im_part.tolist(),
            "mode": "lines",
            "name": "Im projection → sin(ωt)",
            "line": {"color": self.RED, "width": 2, "dash": "dot"},
        })

        # Start marker
        traces.append({
            "type": "scatter3d",
            "x": [0],
            "y": [1.0],
            "z": [0.0],
            "mode": "markers",
            "name": "t = 0",
            "marker": {"color": self.GREEN, "size": 5},
        })

        helix_label = f"e^(j{omega:.1f}t)" if sigma < 1e-6 else f"e^((-{sigma:.1f}+j{omega:.1f})t)"

        return {
            "id": "helix_3d",
            "title": f"3D Helix: {helix_label}",
            "data": traces,
            "layout": {
                "scene": {
                    "xaxis": {
                        "title": "Time t (s)",
                        "gridcolor": self.GRID_COLOR,
                        "backgroundcolor": "rgba(0,0,0,0)",
                    },
                    "yaxis": {
                        "title": "Re",
                        "gridcolor": self.GRID_COLOR,
                        "range": [-1.3, 1.3],
                        "backgroundcolor": "rgba(0,0,0,0)",
                    },
                    "zaxis": {
                        "title": "Im",
                        "gridcolor": self.GRID_COLOR,
                        "range": [-1.3, 1.3],
                        "backgroundcolor": "rgba(0,0,0,0)",
                    },
                    "camera": {
                        "eye": {"x": 1.6, "y": 1.4, "z": 0.7},
                        "up": {"x": 0, "y": 0, "z": 1},
                    },
                    "aspectmode": "manual",
                    "aspectratio": {"x": 2.5, "y": 1, "z": 1},
                    "bgcolor": "rgba(0,0,0,0)",
                },
                "margin": {"l": 0, "r": 0, "t": 40, "b": 0},
                "paper_bgcolor": "rgba(0,0,0,0)",
                "showlegend": True,
                "legend": {
                    "x": 0.02, "y": 0.98,
                    "bgcolor": self.LEGEND_BG,
                    "bordercolor": self.LEGEND_BORDER,
                    "borderwidth": 1,
                    "font": {"size": 11},
                },
                "uirevision": f"helix_{self._damping_type}",
            },
        }

    # =========================================================================
    # State
    # =========================================================================

    def get_state(self) -> Dict[str, Any]:
        if not self._initialized:
            self.initialize()

        state = super().get_state()

        M = float(self.parameters["M"])
        K = float(self.parameters["K"])
        b = float(self.parameters["b"])

        # Helper: clean number formatting (no trailing .0, no -0)
        def _fn(v, decimals=3):
            r = round(v, decimals)
            if r == 0.0:
                r = 0.0  # remove -0.0
            if r == int(r):
                return str(int(r))
            return f"{r:.{decimals}f}".rstrip('0').rstrip('.')

        def _coeff(v, var):
            """Format coefficient*variable, omitting coefficient of 1."""
            if abs(v - 1.0) < 1e-9:
                return var
            return f"{_fn(v, 1)}{var}"

        # Format pole strings
        s1_r, s1_i = self._pole_s1.real, self._pole_s1.imag
        s2_r, s2_i = self._pole_s2.real, self._pole_s2.imag
        # Clean -0.0 artifacts
        s1_r = 0.0 if abs(s1_r) < 1e-10 else s1_r
        s2_r = 0.0 if abs(s2_r) < 1e-10 else s2_r

        if self._damping_type in ("undamped", "underdamped"):
            poles_str = f"s = {s1_r:.3f} ± j{abs(s1_i):.3f}"
            omega_d_val = round(self._omega_d, 4) if self._omega_d else None
            period = round(2 * np.pi / self._omega_d, 4) if self._omega_d and self._omega_d > 1e-10 else None
            if self._damping_type == "undamped":
                impulse_str = f"h(t) = ({1.0/(M*self._omega_0):.4f})·sin({self._omega_0:.2f}·t)"
            else:
                impulse_str = f"h(t) = ({1.0/(M*self._omega_d):.4f})·e^(-{self._sigma:.2f}t)·sin({self._omega_d:.2f}·t)"
        elif self._damping_type == "critically_damped":
            poles_str = f"s = {s1_r:.3f} (repeated)"
            omega_d_val = None
            period = None
            impulse_str = f"h(t) = ({1.0/M:.4f})·t·e^(-{self._sigma:.2f}t)"
        else:
            poles_str = f"s₁ = {s1_r:.3f}, s₂ = {s2_r:.3f}"
            omega_d_val = None
            period = None
            impulse_str = "h(t) = exponential decay (no oscillation)"

        # Build clean ODE string — omit zero-coefficient terms
        ode_parts = [_coeff(M, "y''")]
        if b > 1e-9:
            ode_parts.append(_coeff(b, "y'"))
        ode_parts.append(_coeff(K, "y"))
        ode_str = " + ".join(ode_parts) + " = δ(t)"

        char_parts = [_coeff(M, "s²")]
        if b > 1e-9:
            char_parts.append(_coeff(b, "s"))
        char_parts.append(_fn(K, 1))
        char_str = " + ".join(char_parts) + " = 0"

        state["metadata"] = {
            "simulation_type": "complex_poles_modes",
            "hub_slots": self.HUB_SLOTS,
            "hub_domain": self.HUB_DOMAIN,
            "hub_dimensions": self.HUB_DIMENSIONS,
            "sticky_controls": True,
            "system_info": {
                "omega_0": round(self._omega_0, 4),
                "omega_0_hz": round(self._omega_0 / (2 * np.pi), 4),
                "sigma": round(self._sigma, 4) if abs(self._sigma) > 1e-10 else 0.0,
                "omega_d": omega_d_val,
                "zeta": round(self._zeta, 4) if abs(self._zeta) > 1e-10 else 0.0,
                "damping_type": self._damping_type,
                "pole_s1": {"real": round(s1_r, 4), "imag": round(s1_i, 4)},
                "pole_s2": {"real": round(s2_r, 4), "imag": round(s2_i, 4)},
                "period": period,
                "M": M,
                "K": K,
                "b": b,
            },
            "equations": {
                "ode": ode_str,
                "char_eq": char_str,
                "poles_str": poles_str,
                "impulse_response": impulse_str,
            },
        }

        return state
