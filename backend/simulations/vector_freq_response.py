"""
Vector Diagram Frequency Response Builder Simulator

Recreates the animated vector-diagram-to-frequency-response construction from
MIT 6.003 Lecture 9 (slides 26–56). Users configure poles, zeros, and gain.
The backend computes the full frequency response and per-factor contributions.
The frontend custom viewer animates the ω sweep with synchronized vectors.

Based on MIT 6.003 Lecture 09: Frequency Response.
"""

import numpy as np
from typing import Any, Dict, List, Optional
from .base_simulator import BaseSimulator


class VectorFreqResponseSimulator(BaseSimulator):
    """
    Vector Diagram Frequency Response simulation.

    For H(s) = K × ∏(s - zᵢ) / ∏(s - pⱼ), computes:
    - Full |H(jω)| and ∠H(jω) over a frequency sweep
    - Per-factor magnitudes and phases for individual contribution views
    - Static s-plane plot with poles and zeros

    Parameters:
    - preset: Pedagogical preset (single_zero, single_pole, pole_zero_pair,
              conjugate_poles, custom)
    - gain: Overall gain constant K
    - zero1_real/imag, pole1_real/imag, pole2_real/imag: Pole/zero positions
    - omega_max: Sweep range ±ω_max
    - show_individual: Show per-vector contribution traces
    """

    # Colors
    POLE_COLOR = "#ef4444"
    ZERO_COLOR = "#3b82f6"
    JW_AXIS_COLOR = "#a855f7"
    PHASE_COLOR = "#ef4444"
    MAG_COLOR = "#3b82f6"
    TEAL_COLOR = "#14b8a6"
    GREEN_COLOR = "#10b981"
    GRID_COLOR = "rgba(148, 163, 184, 0.15)"
    ZEROLINE_COLOR = "rgba(148, 163, 184, 0.3)"
    LEGEND_BG = "rgba(15, 23, 42, 0.8)"
    LEGEND_BORDER = "rgba(148, 163, 184, 0.2)"

    # Numerical constants
    NUM_POINTS = 500
    MAX_MAG_CLIP = 50.0
    MIN_AXIS_RANGE = 2.0
    MAX_AXIS_RANGE = 8.0
    AXIS_PADDING = 1.0

    # Preset configurations: {poles: [(real, imag), ...], zeros: [...], gain: K}
    PRESETS = {
        "single_zero": {
            "poles": [],
            "zeros": [(-3.0, 0.0)],
            "gain": 1.0,
            "name": "Single Zero",
            "expression_template": "s + {z1}",
        },
        "single_pole": {
            "poles": [(-3.0, 0.0)],
            "zeros": [],
            "gain": 9.0,
            "name": "Single Pole",
            "expression_template": "{K} / (s + {p1})",
        },
        "pole_zero_pair": {
            "poles": [(-4.0, 0.0)],
            "zeros": [(-2.0, 0.0)],
            "gain": 3.0,
            "name": "Pole-Zero Pair",
            "expression_template": "{K}(s + {z1}) / (s + {p1})",
        },
        "conjugate_poles": {
            "poles": [(-1.0, 3.0)],  # Will be mirrored to create conjugate
            "zeros": [],
            "gain": 15.0,
            "name": "Conjugate Pole Pair",
            "expression_template": "{K} / ((s - p₁)(s - p₁*))",
        },
        "custom": {
            "poles": [(-3.0, 0.0)],
            "zeros": [(-1.0, 0.0)],
            "gain": 1.0,
            "name": "Custom",
            "expression_template": "",
        },
    }

    PARAMETER_SCHEMA = {
        "preset": {
            "type": "select",
            "options": [
                {"value": "single_zero", "label": "Single Zero: H(s) = s − z₁"},
                {"value": "single_pole", "label": "Single Pole: H(s) = K/(s − p₁)"},
                {"value": "pole_zero_pair", "label": "Pole-Zero: H(s) = K(s − z₁)/(s − p₁)"},
                {"value": "conjugate_poles", "label": "Conjugate Poles: H(s) = K/((s − p₁)(s − p₁*))"},
                {"value": "custom", "label": "Custom Configuration"},
            ],
            "default": "single_zero",
        },
        "gain": {"type": "slider", "min": 0.1, "max": 20.0, "step": 0.1, "default": 1.0},
        "zero1_real": {"type": "slider", "min": -5.0, "max": 5.0, "step": 0.1, "default": -3.0},
        "zero1_imag": {"type": "slider", "min": -5.0, "max": 5.0, "step": 0.1, "default": 0.0},
        "pole1_real": {"type": "slider", "min": -5.0, "max": 1.0, "step": 0.1, "default": -3.0},
        "pole1_imag": {"type": "slider", "min": 0.0, "max": 5.0, "step": 0.1, "default": 3.0},
        "pole2_real": {"type": "slider", "min": -5.0, "max": 1.0, "step": 0.1, "default": -1.0},
        "pole2_imag": {"type": "slider", "min": -5.0, "max": 5.0, "step": 0.1, "default": 0.0},
        "omega_max": {"type": "slider", "min": 2.0, "max": 15.0, "step": 0.5, "default": 5.0},
        "show_individual": {"type": "checkbox", "default": False},
    }

    DEFAULT_PARAMS = {
        "preset": "single_zero",
        "gain": 1.0,
        "zero1_real": -3.0,
        "zero1_imag": 0.0,
        "pole1_real": -3.0,
        "pole1_imag": 3.0,
        "pole2_real": -1.0,
        "pole2_imag": 0.0,
        "omega_max": 5.0,
        "show_individual": False,
    }

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._poles: List[complex] = []
        self._zeros: List[complex] = []
        self._gain: float = 1.0
        self._omega: np.ndarray = np.array([])
        self._h_jw: np.ndarray = np.array([])
        self._magnitude: np.ndarray = np.array([])
        self._phase: np.ndarray = np.array([])
        self._individual_zero_mags: List[np.ndarray] = []
        self._individual_zero_phases: List[np.ndarray] = []
        self._individual_pole_mags: List[np.ndarray] = []
        self._individual_pole_phases: List[np.ndarray] = []

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        """Initialize simulation with parameters."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        if params:
            for name, value in params.items():
                if name in self.parameters:
                    self.parameters[name] = self._validate_param(name, value)
        self._initialized = True
        self._apply_preset_defaults()
        self._compute()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        """Update a single parameter and recompute."""
        old_preset = self.parameters.get("preset")

        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)

        # When preset changes, reset to lecture defaults
        if name == "preset" and value != old_preset:
            self._apply_preset_defaults()

        self._compute()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        """Reset to default parameters."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._initialized = True
        self._apply_preset_defaults()
        self._compute()
        return self.get_state()

    # =========================================================================
    # Preset management
    # =========================================================================

    def _apply_preset_defaults(self) -> None:
        """Apply preset-specific pole/zero/gain defaults."""
        preset = self.parameters["preset"]
        if preset not in self.PRESETS or preset == "custom":
            return

        config = self.PRESETS[preset]

        self.parameters["gain"] = config["gain"]

        # Set zero1 if preset has zeros
        if config["zeros"]:
            self.parameters["zero1_real"] = config["zeros"][0][0]
            self.parameters["zero1_imag"] = config["zeros"][0][1]

        # Set pole1 if preset has poles
        if config["poles"]:
            self.parameters["pole1_real"] = config["poles"][0][0]
            self.parameters["pole1_imag"] = config["poles"][0][1]

    # =========================================================================
    # Core computation
    # =========================================================================

    def _build_poles_zeros(self) -> None:
        """Build pole/zero lists from current parameters and preset."""
        preset = self.parameters["preset"]
        self._gain = float(self.parameters["gain"])

        self._zeros = []
        self._poles = []

        if preset == "single_zero":
            z1 = complex(float(self.parameters["zero1_real"]),
                         float(self.parameters["zero1_imag"]))
            self._zeros = [z1]
            self._gain = 1.0  # Single zero always gain 1

        elif preset == "single_pole":
            p1 = complex(float(self.parameters["pole1_real"]), 0.0)
            self._poles = [p1]

        elif preset == "pole_zero_pair":
            z1 = complex(float(self.parameters["zero1_real"]), 0.0)
            p1 = complex(float(self.parameters["pole1_real"]), 0.0)
            self._zeros = [z1]
            self._poles = [p1]

        elif preset == "conjugate_poles":
            sigma = float(self.parameters["pole1_real"])
            omega_p = float(self.parameters["pole1_imag"])
            if abs(omega_p) < 1e-6:
                # Degenerate: single real pole
                self._poles = [complex(sigma, 0.0)]
            else:
                p1 = complex(sigma, omega_p)
                p2 = complex(sigma, -omega_p)
                self._poles = [p1, p2]

        elif preset == "custom":
            z1 = complex(float(self.parameters["zero1_real"]),
                         float(self.parameters["zero1_imag"]))
            p1 = complex(float(self.parameters["pole1_real"]),
                         float(self.parameters["pole1_imag"]))
            p2 = complex(float(self.parameters["pole2_real"]),
                         float(self.parameters["pole2_imag"]))

            # Only include if not at origin (convention: zero at origin = unused)
            if abs(z1) > 1e-10:
                self._zeros = [z1]
            if abs(p1) > 1e-10:
                self._poles = [p1]
            if abs(p2) > 1e-10:
                self._poles.append(p2)
            # If custom with pole1 having nonzero imag, add conjugate
            if abs(p1.imag) > 1e-6 and len(self._poles) == 1:
                self._poles.append(complex(p1.real, -p1.imag))

    def _compute(self) -> None:
        """Compute the full frequency response and per-factor data."""
        self._build_poles_zeros()

        omega_max = float(self.parameters["omega_max"])
        self._omega = np.linspace(-omega_max, omega_max, self.NUM_POINTS)
        s = 1j * self._omega  # s₀ = jω for all ω values

        # Compute H(jω) as product of factors
        # H(s) = K × ∏(s - zᵢ) / ∏(s - pⱼ)
        numerator = np.ones(self.NUM_POINTS, dtype=complex) * self._gain
        denominator = np.ones(self.NUM_POINTS, dtype=complex)

        # Per-zero contributions
        self._individual_zero_mags = []
        self._individual_zero_phases = []
        for z in self._zeros:
            factor = s - z  # vector from zero to jω
            numerator *= factor
            self._individual_zero_mags.append(np.abs(factor))
            self._individual_zero_phases.append(np.angle(factor))

        # Per-pole contributions
        self._individual_pole_mags = []
        self._individual_pole_phases = []
        for p in self._poles:
            factor = s - p  # vector from pole to jω
            denominator *= factor
            self._individual_pole_mags.append(np.abs(factor))
            self._individual_pole_phases.append(np.angle(factor))

        # Compute H(jω) with safeguard against zero denominator
        with np.errstate(divide='ignore', invalid='ignore'):
            self._h_jw = np.where(
                np.abs(denominator) < 1e-12,
                self.MAX_MAG_CLIP * np.exp(1j * np.angle(numerator)),
                numerator / denominator
            )

        self._magnitude = np.clip(np.abs(self._h_jw), 0, self.MAX_MAG_CLIP)
        self._phase = np.angle(self._h_jw)
        # Unwrap phase for smooth curves
        self._phase = np.unwrap(self._phase)

    # =========================================================================
    # Expression formatting
    # =========================================================================

    def _format_hs(self) -> str:
        """Format H(s) expression as readable string."""
        preset = self.parameters["preset"]
        K = self._gain

        if preset == "single_zero":
            z = self._zeros[0] if self._zeros else complex(-3, 0)
            if abs(z.imag) < 1e-6:
                if z.real >= 0:
                    return f"s \u2212 {abs(z.real):.3g}"
                else:
                    return f"s + {abs(z.real):.3g}"
            return f"s \u2212 ({self._format_complex(z)})"

        elif preset == "single_pole":
            p = self._poles[0] if self._poles else complex(-3, 0)
            den = self._format_factor(p)
            return f"{K:.3g} / ({den})"

        elif preset == "pole_zero_pair":
            z = self._zeros[0] if self._zeros else complex(-2, 0)
            p = self._poles[0] if self._poles else complex(-4, 0)
            num = self._format_factor(z)
            den = self._format_factor(p)
            return f"{K:.3g}\u00b7({num}) / ({den})"

        elif preset == "conjugate_poles":
            if len(self._poles) >= 2:
                sigma = self._poles[0].real
                omega = abs(self._poles[0].imag)
                # Display as K / (s² + as + b) polynomial form
                a = -2 * sigma
                b = sigma**2 + omega**2
                a_str = f"+ {a:.3g}" if a >= 0 else f"\u2212 {abs(a):.3g}"
                return f"{K:.3g} / (s\u00b2 {a_str}s + {b:.3g})"
            elif len(self._poles) == 1:
                p1 = self._poles[0]
                den = self._format_factor(p1)
                return f"{K:.3g} / ({den})"
            return f"{K:.3g}"

        elif preset == "custom":
            parts_num = []
            parts_den = []
            if abs(K - 1.0) > 1e-6:
                parts_num.append(f"{K:.3g}")
            for z in self._zeros:
                parts_num.append(f"({self._format_factor(z)})")
            for p in self._poles:
                parts_den.append(f"({self._format_factor(p)})")
            num_str = "\u00b7".join(parts_num) if parts_num else "1"
            den_str = "\u00b7".join(parts_den) if parts_den else "1"
            if parts_den:
                return f"{num_str} / {den_str}"
            return num_str

        return "H(s)"

    def _format_factor(self, z: complex) -> str:
        """Format a single (s - z) factor."""
        if abs(z.imag) < 1e-6:
            r = z.real
            if r >= 0:
                return f"s \u2212 {r:.3g}"
            else:
                return f"s + {abs(r):.3g}"
        return f"s \u2212 ({self._format_complex(z)})"

    def _format_complex(self, z: complex) -> str:
        """Format a complex number for display."""
        if abs(z.imag) < 1e-6:
            return f"{z.real:.3g}"
        elif abs(z.real) < 1e-6:
            return f"{z.imag:.3g}j"
        sign = "+" if z.imag >= 0 else "\u2212"
        return f"{z.real:.3g} {sign} {abs(z.imag):.3g}j"

    def _get_preset_display_name(self) -> str:
        """Get human-readable name for current preset."""
        preset = self.parameters["preset"]
        return self.PRESETS.get(preset, {}).get("name", preset)

    # =========================================================================
    # s-Plane axis range
    # =========================================================================

    def _compute_axis_range(self) -> float:
        """Compute dynamic axis range based on poles and zeros."""
        max_r = self.MIN_AXIS_RANGE
        for p in self._poles:
            max_r = max(max_r, abs(p.real) + self.AXIS_PADDING)
            max_r = max(max_r, abs(p.imag) + self.AXIS_PADDING)
        for z in self._zeros:
            max_r = max(max_r, abs(z.real) + self.AXIS_PADDING)
            max_r = max(max_r, abs(z.imag) + self.AXIS_PADDING)
        return min(max_r, self.MAX_AXIS_RANGE)

    # =========================================================================
    # Plot generation
    # =========================================================================

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate all Plotly plot dictionaries."""
        if not self._initialized:
            self.initialize()
        return [
            self._create_s_plane_plot(),
            self._create_magnitude_plot(),
            self._create_phase_plot(),
        ]

    def _create_s_plane_plot(self) -> Dict[str, Any]:
        """Create s-plane plot with poles and zeros."""
        traces = []
        axis_range = self._compute_axis_range()

        # jω axis
        traces.append({
            "x": [0, 0],
            "y": [-axis_range, axis_range],
            "type": "scatter",
            "mode": "lines",
            "line": {"color": self.JW_AXIS_COLOR, "width": 2.5, "dash": "dash"},
            "name": "j\u03c9 axis",
            "hoverinfo": "skip",
        })

        # σ axis
        traces.append({
            "x": [-axis_range, axis_range],
            "y": [0, 0],
            "type": "scatter",
            "mode": "lines",
            "line": {"color": self.ZEROLINE_COLOR, "width": 1},
            "name": "\u03c3 axis",
            "showlegend": False,
            "hoverinfo": "skip",
        })

        # Zero markers
        for i, z in enumerate(self._zeros):
            label = self._format_complex(z)
            traces.append({
                "x": [float(z.real)],
                "y": [float(z.imag)],
                "type": "scatter",
                "mode": "markers",
                "marker": {
                    "symbol": "circle-open",
                    "size": 14,
                    "color": self.ZERO_COLOR,
                    "line": {"width": 3, "color": self.ZERO_COLOR},
                },
                "name": f"Zero: s = {label}",
                "showlegend": True,
                "hovertemplate": f"Zero {i + 1}<br>s = {label}<extra></extra>",
            })

        # Pole markers
        for i, p in enumerate(self._poles):
            label = self._format_complex(p)
            traces.append({
                "x": [float(p.real)],
                "y": [float(p.imag)],
                "type": "scatter",
                "mode": "markers",
                "marker": {
                    "symbol": "x",
                    "size": 14,
                    "color": self.POLE_COLOR,
                    "line": {"width": 3, "color": self.POLE_COLOR},
                },
                "name": f"Pole: s = {label}",
                "showlegend": True,
                "hovertemplate": f"Pole {i + 1}<br>s = {label}<extra></extra>",
            })

        # UI revision fingerprint
        preset = self.parameters["preset"]
        gain = self._gain
        poles_str = ",".join(f"{p.real:.2f}{p.imag:.2f}" for p in self._poles)
        zeros_str = ",".join(f"{z.real:.2f}{z.imag:.2f}" for z in self._zeros)
        ui_fp = f"splane-{preset}-{gain}-{poles_str}-{zeros_str}"

        return {
            "id": "s_plane",
            "title": "s-Plane: Poles & Zeros",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "\u03c3 (Real)",
                    "range": [-axis_range, axis_range],
                    "scaleanchor": "y",
                    "scaleratio": 1,
                    "constrain": "domain",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": False,
                    "fixedrange": False,
                    "color": "#f1f5f9",
                },
                "yaxis": {
                    "title": "j\u03c9 (Imaginary)",
                    "range": [-axis_range, axis_range],
                    "constrain": "domain",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": False,
                    "fixedrange": False,
                    "color": "#f1f5f9",
                },
                "legend": {
                    "x": 0.02, "y": 0.98,
                    "xanchor": "left", "yanchor": "top",
                    "bgcolor": self.LEGEND_BG,
                    "bordercolor": self.LEGEND_BORDER,
                    "borderwidth": 1,
                    "font": {"size": 10, "color": "#94a3b8"},
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
                "uirevision": ui_fp,
            },
        }

    def _create_magnitude_plot(self) -> Dict[str, Any]:
        """Create magnitude response |H(jω)| plot."""
        traces = []

        # Main magnitude trace
        traces.append({
            "x": self._omega.tolist(),
            "y": self._magnitude.tolist(),
            "type": "scatter",
            "mode": "lines",
            "line": {"color": self.MAG_COLOR, "width": 2.5},
            "name": "|H(j\u03c9)|",
            "hovertemplate": "\u03c9 = %{x:.2f}<br>|H| = %{y:.3f}<extra></extra>",
        })

        # Individual zero contributions (faded)
        if self.parameters["show_individual"]:
            for i, mag in enumerate(self._individual_zero_mags):
                traces.append({
                    "x": self._omega.tolist(),
                    "y": mag.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "line": {"color": self.TEAL_COLOR, "width": 1.5, "dash": "dot"},
                    "name": f"|j\u03c9 \u2212 z{i + 1}|",
                    "opacity": 0.6,
                })
            for i, mag in enumerate(self._individual_pole_mags):
                traces.append({
                    "x": self._omega.tolist(),
                    "y": mag.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "line": {"color": self.POLE_COLOR, "width": 1.5, "dash": "dot"},
                    "name": f"|j\u03c9 \u2212 p{i + 1}|",
                    "opacity": 0.6,
                })

        preset = self.parameters["preset"]
        gain = self._gain
        poles_str = ",".join(f"{p.real:.2f}" for p in self._poles)
        zeros_str = ",".join(f"{z.real:.2f}" for z in self._zeros)
        ui_fp = f"mag-{preset}-{gain}-{poles_str}-{zeros_str}"

        return {
            "id": "magnitude_response",
            "title": "|H(j\u03c9)| Magnitude Response",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "\u03c9 (rad/s)",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "zerolinewidth": 1,
                    "autorange": True,
                    "fixedrange": False,
                    "color": "#f1f5f9",
                },
                "yaxis": {
                    "title": "|H(j\u03c9)|",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "zerolinewidth": 1,
                    "autorange": True,
                    "fixedrange": False,
                    "rangemode": "tozero",
                    "color": "#f1f5f9",
                },
                "legend": {
                    "x": 0.98, "y": 0.98,
                    "xanchor": "right", "yanchor": "top",
                    "bgcolor": self.LEGEND_BG,
                    "bordercolor": self.LEGEND_BORDER,
                    "borderwidth": 1,
                    "font": {"size": 10, "color": "#94a3b8"},
                },
                "margin": {"l": 60, "r": 30, "t": 45, "b": 55},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
                "showlegend": bool(self.parameters["show_individual"]),
                "uirevision": ui_fp,
            },
        }

    def _create_phase_plot(self) -> Dict[str, Any]:
        """Create phase response ∠H(jω) plot."""
        traces = []

        # Main phase trace
        traces.append({
            "x": self._omega.tolist(),
            "y": self._phase.tolist(),
            "type": "scatter",
            "mode": "lines",
            "line": {"color": self.PHASE_COLOR, "width": 2.5},
            "name": "\u2220H(j\u03c9)",
            "hovertemplate": "\u03c9 = %{x:.2f}<br>\u2220H = %{y:.3f} rad<extra></extra>",
        })

        # Individual phase contributions (faded)
        if self.parameters["show_individual"]:
            for i, ph in enumerate(self._individual_zero_phases):
                traces.append({
                    "x": self._omega.tolist(),
                    "y": ph.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "line": {"color": self.TEAL_COLOR, "width": 1.5, "dash": "dot"},
                    "name": f"\u2220(j\u03c9 \u2212 z{i + 1})",
                    "opacity": 0.6,
                })
            for i, ph in enumerate(self._individual_pole_phases):
                traces.append({
                    "x": self._omega.tolist(),
                    "y": (-ph).tolist(),  # Negate: pole phases subtract
                    "type": "scatter",
                    "mode": "lines",
                    "line": {"color": self.POLE_COLOR, "width": 1.5, "dash": "dot"},
                    "name": f"\u2212\u2220(j\u03c9 \u2212 p{i + 1})",
                    "opacity": 0.6,
                })

        preset = self.parameters["preset"]
        gain = self._gain
        poles_str = ",".join(f"{p.real:.2f}" for p in self._poles)
        zeros_str = ",".join(f"{z.real:.2f}" for z in self._zeros)
        ui_fp = f"phase-{preset}-{gain}-{poles_str}-{zeros_str}"

        return {
            "id": "phase_response",
            "title": "\u2220H(j\u03c9) Phase Response",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "\u03c9 (rad/s)",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "zerolinewidth": 1,
                    "autorange": True,
                    "fixedrange": False,
                    "color": "#f1f5f9",
                },
                "yaxis": {
                    "title": "\u2220H(j\u03c9) [rad]",
                    "showgrid": True,
                    "gridcolor": self.GRID_COLOR,
                    "zeroline": True,
                    "zerolinecolor": self.ZEROLINE_COLOR,
                    "zerolinewidth": 1,
                    "autorange": True,
                    "fixedrange": False,
                    "color": "#f1f5f9",
                },
                "legend": {
                    "x": 0.98, "y": 0.98,
                    "xanchor": "right", "yanchor": "top",
                    "bgcolor": self.LEGEND_BG,
                    "bordercolor": self.LEGEND_BORDER,
                    "borderwidth": 1,
                    "font": {"size": 10, "color": "#94a3b8"},
                },
                "margin": {"l": 60, "r": 30, "t": 45, "b": 55},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
                "showlegend": bool(self.parameters["show_individual"]),
                "uirevision": ui_fp,
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

        state["metadata"] = {
            "simulation_type": "vector_freq_response",
            "sticky_controls": True,
            "hs_expression": self._format_hs(),
            "preset_name": self._get_preset_display_name(),
            "poles": [
                {"real": float(p.real), "imag": float(p.imag)}
                for p in self._poles
            ],
            "zeros": [
                {"real": float(z.real), "imag": float(z.imag)}
                for z in self._zeros
            ],
            "gain": float(self._gain),
            "omega": self._omega.tolist(),
            "magnitude": self._magnitude.tolist(),
            "phase": self._phase.tolist(),
            "individual_zero_mags": [m.tolist() for m in self._individual_zero_mags],
            "individual_zero_phases": [p.tolist() for p in self._individual_zero_phases],
            "individual_pole_mags": [m.tolist() for m in self._individual_pole_mags],
            "individual_pole_phases": [p.tolist() for p in self._individual_pole_phases],
            "axis_range": float(self._compute_axis_range()),
        }

        return state
