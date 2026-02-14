"""
Feedback System Analysis Simulator

Analyzes negative feedback effects on amplifier performance.
Compares open-loop vs closed-loop behavior including:
- Step response comparison
- Bode magnitude and phase plots
- S-plane pole visualization
- Performance metrics (gain, bandwidth, rise time)

Math extracted from: feedback_system_analysis/core/calculations.py
Matching PyQt5 app exactly for feature parity.
"""

import numpy as np
from typing import Any, Dict, List, Optional
from .base_simulator import BaseSimulator


class FeedbackAmplifierSimulator(BaseSimulator):
    """
    Feedback Amplifier simulation matching PyQt5 app.

    Parameters (matching PyQt5 exactly):
    - beta: Feedback factor (0 to 0.01, default 0.0041)
    - K0: Open-loop gain (10,000 to 500,000, default 200,000)
    - alpha: Pole location in rad/s (10 to 200, default 40)
    - input_amp: Input amplitude in V (0.1 to 2.0, default 1.0)
    """

    # Configuration matching PyQt5
    TIME_SAMPLES = 1000
    FREQ_SAMPLES = 800
    TIME_MAX = 2.0  # seconds (matching PyQt5)
    OMEGA_MIN = -1  # 10^-1 rad/s
    OMEGA_MAX = 8   # 10^8 rad/s

    # Unified color palette - matches DC Motor and CT/DT Poles simulations
    COLORS = {
        # Primary response colors
        "open_loop": "#f87171",        # Coral red - open-loop (dashed)
        "closed_loop": "#22d3ee",      # Cyan - closed-loop (solid)
        "reference": "#f472b6",        # Pink - reference lines

        # Stability colors
        "stable_region": "rgba(52, 211, 153, 0.08)",  # Light emerald
        "pole_marker": "#f87171",      # Coral red - poles

        # Annotations and accents
        "accent": "#fbbf24",           # Amber - speedup arrows
        "imaginary_axis": "#a855f7",   # Purple - stability boundary

        # Grid and text
        "grid": "rgba(148, 163, 184, 0.2)",
        "text": "#e2e8f0",
    }

    # Parameter schema matching PyQt5 exactly
    PARAMETER_SCHEMA = {
        "beta": {
            "type": "slider",
            "label": "β (Feedback Factor)",
            "min": 0.0,
            "max": 0.01,
            "step": 0.0001,
            "default": 0.0041,
            "unit": "",
            "description": "Feedback strength - affects gain reduction and bandwidth expansion",
        },
        "K0": {
            "type": "slider",
            "label": "K₀ (Open-Loop Gain)",
            "min": 10000,
            "max": 500000,
            "step": 1000,
            "default": 200000,
            "unit": "V/V",
            "description": "Amplifier's open-loop gain",
        },
        "alpha": {
            "type": "slider",
            "label": "α (Pole Location)",
            "min": 10,
            "max": 200,
            "step": 1,
            "default": 40,
            "unit": "rad/s",
            "description": "Open-loop pole location - affects bandwidth and response speed",
        },
        "input_amp": {
            "type": "slider",
            "label": "Input Amplitude",
            "min": 0.1,
            "max": 2.0,
            "step": 0.01,
            "default": 1.0,
            "unit": "V",
            "description": "Input signal amplitude for step response",
        },
    }

    DEFAULT_PARAMS = {
        "beta": 0.0041,
        "K0": 200000,
        "alpha": 40,
        "input_amp": 1.0,
    }

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._time = None
        self._omega = None
        self._ol_step_response = None
        self._cl_step_response = None
        self._ol_bode_mag = None
        self._cl_bode_mag = None
        self._ol_bode_phase = None
        self._cl_bode_phase = None
        self._metrics = {}

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
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
            self._compute()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        """Reset simulation to default parameters."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._initialized = True
        self._compute()
        return self.get_state()

    def _compute(self) -> None:
        """Compute all responses."""
        K0 = self.parameters["K0"]
        alpha = self.parameters["alpha"]
        beta = self.parameters["beta"]
        input_amp = self.parameters["input_amp"]

        # Calculate metrics
        self._metrics = self._calculate_metrics(K0, alpha, beta)

        # Time vector (matching PyQt5: 0 to 2.0 seconds, 1000 points)
        self._time = np.linspace(0, self.TIME_MAX, self.TIME_SAMPLES)

        # Step response
        self._ol_step_response, self._cl_step_response = self._calculate_step_response(
            K0, alpha, beta, input_amp, self._time
        )

        # Frequency vector (log scale, matching PyQt5: 10^-1 to 10^8, 800 points)
        self._omega = np.logspace(self.OMEGA_MIN, self.OMEGA_MAX, self.FREQ_SAMPLES)

        # Bode magnitude
        self._ol_bode_mag, self._cl_bode_mag = self._calculate_bode_magnitude(
            K0, alpha, beta, self._omega
        )

        # Bode phase
        self._ol_bode_phase, self._cl_bode_phase = self._calculate_bode_phase(
            K0, alpha, beta, self._omega
        )

    def _calculate_metrics(self, K0: float, alpha: float, beta: float) -> Dict[str, float]:
        """Calculate key performance metrics matching PyQt5."""
        loop_gain = beta * K0
        loop_gain_factor = 1 + loop_gain
        closed_loop_gain = K0 / loop_gain_factor
        closed_loop_bw = alpha * loop_gain_factor

        return {
            "ol_gain": K0,
            "cl_gain": closed_loop_gain,
            "ol_bw": alpha,
            "cl_bw": closed_loop_bw,
            "ol_rise_time": 2.2 / alpha,
            "cl_rise_time": 2.2 / closed_loop_bw,
            "ol_pole": -alpha,
            "cl_pole": -closed_loop_bw,
            "loop_gain": loop_gain,
            "speedup": loop_gain_factor,
            "gain_reduction": K0 / closed_loop_gain if closed_loop_gain > 0 else float('inf'),
        }

    def _calculate_step_response(self, K0: float, alpha: float, beta: float,
                                  input_amp: float, t: np.ndarray) -> tuple:
        """Calculate step responses matching PyQt5 formulas."""
        metrics = self._metrics

        # Open-loop: y_ol(t) = A_in × K₀ × (1 - exp(-α × t))
        ol_response = input_amp * K0 * (1 - np.exp(-alpha * t))

        # Closed-loop: y_cl(t) = A_in × (K₀/(1+βK₀)) × (1 - exp(-α(1+βK₀) × t))
        cl_response = input_amp * metrics["cl_gain"] * (1 - np.exp(-metrics["cl_bw"] * t))

        return ol_response, cl_response

    def _calculate_bode_magnitude(self, K0: float, alpha: float, beta: float,
                                   omega: np.ndarray) -> tuple:
        """Calculate Bode magnitude responses."""
        metrics = self._metrics

        # Open-loop: H_ol(jω) = (K₀ × α) / (jω + α)
        H_ol = (K0 * alpha) / (1j * omega + alpha)

        # Closed-loop: H_cl(jω) = (cl_gain × cl_bw) / (jω + cl_bw)
        H_cl = (metrics["cl_gain"] * metrics["cl_bw"]) / (1j * omega + metrics["cl_bw"])

        mag_ol = 20 * np.log10(np.abs(H_ol))
        mag_cl = 20 * np.log10(np.abs(H_cl))

        return mag_ol, mag_cl

    def _calculate_bode_phase(self, K0: float, alpha: float, beta: float,
                               omega: np.ndarray) -> tuple:
        """Calculate Bode phase responses."""
        metrics = self._metrics

        # Open-loop phase
        H_ol = (K0 * alpha) / (1j * omega + alpha)

        # Closed-loop phase
        H_cl = (metrics["cl_gain"] * metrics["cl_bw"]) / (1j * omega + metrics["cl_bw"])

        phase_ol = np.angle(H_ol, deg=True)
        phase_cl = np.angle(H_cl, deg=True)

        return phase_ol, phase_cl

    @staticmethod
    def _format_value(value: float, unit: str = "") -> str:
        """Format value with SI prefix (matching PyQt5 format_value)."""
        if value == 0:
            return f"0{unit}"

        abs_val = abs(value)
        if abs_val >= 1e6:
            return f"{value/1e6:.2f}M{unit}"
        elif abs_val >= 1e3:
            return f"{value/1e3:.2f}k{unit}"
        elif abs_val >= 1:
            return f"{value:.2f}{unit}"
        elif abs_val >= 1e-3:
            return f"{value*1e3:.2f}m{unit}"
        elif abs_val >= 1e-6:
            return f"{value*1e6:.2f}µ{unit}"
        else:
            return f"{value*1e9:.2f}n{unit}"

    # =========================================================================
    # Plot generation - matching PyQt5 style
    # =========================================================================

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate Plotly plot dictionaries matching PyQt5 layout."""
        if not self._initialized:
            self.initialize()

        plots = [
            self._create_s_plane_plot(),         # Pole position first
            self._create_bode_magnitude_plot(),  # Then Bode plots
            self._create_bode_phase_plot(),
            self._create_step_response_plot(),   # Then step response
        ]
        return plots

    # Default step response y-range (stays constant unless data exceeds bounds)
    STEP_RESPONSE_DEFAULT_Y_MAX = 250000  # Covers typical OL response with K0=200k

    def _create_step_response_plot(self) -> Dict[str, Any]:
        """Create step response comparison plot (matching PyQt5 Response Tab)."""
        # Calculate y-axis range based on actual data
        ol_max = float(np.max(self._ol_step_response))
        cl_max = float(np.max(self._cl_step_response))
        data_max = max(ol_max, cl_max) * 1.1  # 10% padding

        # Use default unless data exceeds it
        y_max = max(self.STEP_RESPONSE_DEFAULT_Y_MAX, data_max)

        traces = []

        # Open-loop response (red, dashed)
        traces.append({
            "x": self._time.tolist(),
            "y": self._ol_step_response.tolist(),
            "type": "scatter",
            "mode": "lines",
            "name": "Open-Loop",
            "line": {"color": self.COLORS["open_loop"], "width": 2.5, "dash": "dash"},
            "opacity": 0.8,
            "hovertemplate": "t = %{x:.3f}s<br>y = %{y:.2f}V<extra>Open-Loop</extra>",
        })

        # Closed-loop response (cyan, solid)
        traces.append({
            "x": self._time.tolist(),
            "y": self._cl_step_response.tolist(),
            "type": "scatter",
            "mode": "lines",
            "name": "Closed-Loop",
            "line": {"color": self.COLORS["closed_loop"], "width": 2.5},
            "hovertemplate": "t = %{x:.3f}s<br>y = %{y:.2f}V<extra>Closed-Loop</extra>",
        })

        return {
            "id": "step_response",
            "title": "Step Response",
            "plotType": "response",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Time (s)",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "range": [0, self.TIME_MAX],
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Output (V)",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "range": [0, y_max],
                    "fixedrange": False,
                },
                "legend": {
                    "x": 0.02, "y": 0.98,
                    "xanchor": "left", "yanchor": "top",
                    "bgcolor": "rgba(15, 23, 42, 0.8)",
                    "bordercolor": "rgba(148, 163, 184, 0.2)",
                    "borderwidth": 1,
                    "font": {"size": 11},
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "step_response",
            },
        }

    # Default Bode magnitude y-range (stays constant unless data exceeds bounds)
    BODE_MAG_DEFAULT_Y_MIN = -60   # Typical low end
    BODE_MAG_DEFAULT_Y_MAX = 120   # Covers high gain systems

    def _create_bode_magnitude_plot(self) -> Dict[str, Any]:
        """Create Bode magnitude plot with bandwidth markers (matching PyQt5)."""
        ol_bw = self._metrics["ol_bw"]
        cl_bw = self._metrics["cl_bw"]

        # Calculate y-axis range based on actual data
        ol_max = float(np.max(self._ol_bode_mag))
        cl_max = float(np.max(self._cl_bode_mag))
        ol_min = float(np.min(self._ol_bode_mag))
        cl_min = float(np.min(self._cl_bode_mag))

        # Use defaults unless data exceeds bounds
        y_max = max(self.BODE_MAG_DEFAULT_Y_MAX, max(ol_max, cl_max) + 10)
        y_min = min(self.BODE_MAG_DEFAULT_Y_MIN, min(ol_min, cl_min) - 10)

        traces = []

        # Open-loop magnitude (red, dashed)
        traces.append({
            "x": self._omega.tolist(),
            "y": self._ol_bode_mag.tolist(),
            "type": "scatter",
            "mode": "lines",
            "name": "Open-Loop",
            "line": {"color": self.COLORS["open_loop"], "width": 2.5, "dash": "dash"},
            "opacity": 0.8,
            "hovertemplate": "ω = %{x:.2f} rad/s<br>|H| = %{y:.1f} dB<extra>Open-Loop</extra>",
        })

        # Closed-loop magnitude (cyan, solid)
        traces.append({
            "x": self._omega.tolist(),
            "y": self._cl_bode_mag.tolist(),
            "type": "scatter",
            "mode": "lines",
            "name": "Closed-Loop",
            "line": {"color": self.COLORS["closed_loop"], "width": 2.5},
            "hovertemplate": "ω = %{x:.2f} rad/s<br>|H| = %{y:.1f} dB<extra>Closed-Loop</extra>",
        })

        # Bandwidth markers (vertical dotted lines)
        shapes = [
            # Open-loop bandwidth
            {
                "type": "line",
                "x0": ol_bw, "x1": ol_bw,
                "y0": 0, "y1": 1,
                "yref": "paper",
                "line": {"color": self.COLORS["open_loop"], "width": 1.5, "dash": "dot"},
            },
            # Closed-loop bandwidth
            {
                "type": "line",
                "x0": cl_bw, "x1": cl_bw,
                "y0": 0, "y1": 1,
                "yref": "paper",
                "line": {"color": self.COLORS["closed_loop"], "width": 1.5, "dash": "dot"},
            },
        ]

        return {
            "id": "bode_magnitude",
            "title": "Bode Magnitude",
            "plotType": "response",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Frequency (rad/s)",
                    "type": "log",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "range": [self.OMEGA_MIN, self.OMEGA_MAX],
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Magnitude (dB)",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "range": [y_min, y_max],
                    "fixedrange": False,
                },
                "shapes": shapes,
                "legend": {
                    "x": 0.02, "y": 0.02,
                    "xanchor": "left", "yanchor": "bottom",
                    "bgcolor": "rgba(15, 23, 42, 0.8)",
                    "bordercolor": "rgba(148, 163, 184, 0.2)",
                    "borderwidth": 1,
                    "font": {"size": 11},
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "bode_magnitude",
            },
        }

    def _create_bode_phase_plot(self) -> Dict[str, Any]:
        """Create Bode phase plot (matching PyQt5)."""
        traces = []

        # Open-loop phase (red, dashed)
        traces.append({
            "x": self._omega.tolist(),
            "y": self._ol_bode_phase.tolist(),
            "type": "scatter",
            "mode": "lines",
            "name": "Open-Loop",
            "line": {"color": self.COLORS["open_loop"], "width": 2.5, "dash": "dash"},
            "opacity": 0.8,
            "hovertemplate": "ω = %{x:.2f} rad/s<br>∠H = %{y:.1f}°<extra>Open-Loop</extra>",
        })

        # Closed-loop phase (cyan, solid)
        traces.append({
            "x": self._omega.tolist(),
            "y": self._cl_bode_phase.tolist(),
            "type": "scatter",
            "mode": "lines",
            "name": "Closed-Loop",
            "line": {"color": self.COLORS["closed_loop"], "width": 2.5},
            "hovertemplate": "ω = %{x:.2f} rad/s<br>∠H = %{y:.1f}°<extra>Closed-Loop</extra>",
        })

        return {
            "id": "bode_phase",
            "title": "Bode Phase",
            "plotType": "response",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Frequency (rad/s)",
                    "type": "log",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "range": [self.OMEGA_MIN, self.OMEGA_MAX],
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Phase (°)",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "range": [-95, 5],
                    "dtick": 45,
                    "fixedrange": False,
                },
                "legend": {
                    "x": 0.02, "y": 0.02,
                    "xanchor": "left", "yanchor": "bottom",
                    "bgcolor": "rgba(15, 23, 42, 0.8)",
                    "bordercolor": "rgba(148, 163, 184, 0.2)",
                    "borderwidth": 1,
                    "font": {"size": 11},
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "bode_phase",
            },
        }

    # Default S-plane range (stays constant unless poles exceed bounds)
    S_PLANE_DEFAULT_X_MIN = -40000  # Covers typical closed-loop poles
    S_PLANE_DEFAULT_X_MAX = 500     # Small positive region to show jw axis
    S_PLANE_DEFAULT_Y_RANGE = 5000  # Symmetric y-range

    def _create_s_plane_plot(self) -> Dict[str, Any]:
        """Create S-plane pole visualization (matching PyQt5 Analysis Tab)."""
        ol_pole = self._metrics["ol_pole"]
        cl_pole = self._metrics["cl_pole"]
        speedup = self._metrics["speedup"]

        # Use default range, but expand if poles go out of bounds
        min_pole = min(ol_pole, cl_pole)
        max_pole = max(ol_pole, 0)

        # Only expand beyond defaults if needed
        x_min = min(self.S_PLANE_DEFAULT_X_MIN, min_pole * 1.15)  # 15% padding if expanding
        x_max = max(self.S_PLANE_DEFAULT_X_MAX, max_pole + 200)

        # Y-range: use default, or scale if x-range is very large
        y_range = self.S_PLANE_DEFAULT_Y_RANGE
        if abs(x_min) > 50000:
            y_range = abs(x_min) * 0.1  # Scale y with very large x ranges

        traces = []

        # 1. Open-loop pole marker (X, red)
        traces.append({
            "x": [ol_pole],
            "y": [0],
            "type": "scatter",
            "mode": "markers",
            "name": f"OL Pole: s = {ol_pole:.0f}",
            "marker": {
                "symbol": "x",
                "size": 16,
                "color": self.COLORS["open_loop"],
                "line": {"width": 3, "color": self.COLORS["open_loop"]},
            },
            "hovertemplate": f"Open-Loop Pole<br>s = {ol_pole:.1f}<extra></extra>",
        })

        # 2. Closed-loop pole marker (circle, cyan)
        traces.append({
            "x": [cl_pole],
            "y": [0],
            "type": "scatter",
            "mode": "markers",
            "name": f"CL Pole: s = {cl_pole:.0f}",
            "marker": {
                "symbol": "circle-open",
                "size": 14,
                "color": self.COLORS["closed_loop"],
                "line": {"width": 3, "color": self.COLORS["closed_loop"]},
            },
            "hovertemplate": f"Closed-Loop Pole<br>s = {cl_pole:.1f}<extra></extra>",
        })

        # 3. Arrow showing pole movement (from OL to CL) - only if significant movement
        if abs(ol_pole - cl_pole) > 10:
            traces.append({
                "x": [ol_pole, cl_pole],
                "y": [0, 0],  # On real axis
                "type": "scatter",
                "mode": "lines",
                "line": {"color": self.COLORS["accent"], "width": 2, "dash": "dot"},
                "name": f"Pole Shift ({speedup:.1f}x)",
                "hoverinfo": "name",
            })

        # Shapes for stability boundary (jω axis) - use shape so it spans full plot
        shapes = [{
            "type": "line",
            "x0": 0, "x1": 0,
            "y0": 0, "y1": 1,
            "yref": "paper",
            "line": {"color": self.COLORS["imaginary_axis"], "width": 2.5},
        }]

        return {
            "id": "s_plane",
            "title": "S-Plane Pole Location",
            "plotType": "analysis",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Real (σ)",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "zerolinewidth": 1,
                    "range": [x_min, x_max],
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Imaginary (jω)",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "zerolinewidth": 1,
                    "range": [-y_range, y_range],
                    "fixedrange": False,
                },
                "shapes": shapes,
                "legend": {
                    "x": 0.02, "y": 0.98,
                    "xanchor": "left", "yanchor": "top",
                    "bgcolor": "rgba(15, 23, 42, 0.8)",
                    "bordercolor": "rgba(148, 163, 184, 0.2)",
                    "borderwidth": 1,
                    "font": {"size": 11},
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "s_plane",
            },
        }

    def get_computed_values(self) -> Dict[str, Any]:
        """Return computed values for display (matching PyQt5 metrics panel)."""
        m = self._metrics
        return {
            # Open-loop metrics
            "ol_gain": m["ol_gain"],
            "ol_gain_formatted": self._format_value(m["ol_gain"]),
            "ol_bw": m["ol_bw"],
            "ol_bw_formatted": self._format_value(m["ol_bw"], " rad/s"),
            "ol_rise_time": m["ol_rise_time"],
            "ol_rise_time_formatted": self._format_value(m["ol_rise_time"], "s"),
            "ol_pole": m["ol_pole"],

            # Closed-loop metrics
            "cl_gain": m["cl_gain"],
            "cl_gain_formatted": self._format_value(m["cl_gain"]),
            "cl_bw": m["cl_bw"],
            "cl_bw_formatted": self._format_value(m["cl_bw"], " rad/s"),
            "cl_rise_time": m["cl_rise_time"],
            "cl_rise_time_formatted": self._format_value(m["cl_rise_time"], "s"),
            "cl_pole": m["cl_pole"],

            # Feedback metrics
            "loop_gain": m["loop_gain"],
            "speedup": m["speedup"],
            "gain_reduction": m["gain_reduction"],
        }

    def get_state(self) -> Dict[str, Any]:
        """Return current simulation state with computed values and metadata."""
        state = super().get_state()
        state["computed_values"] = self.get_computed_values()

        # Add metadata with system info for info panel
        m = self._metrics
        state["metadata"] = {
            "simulation_type": "feedback_system_analysis",
            "sticky_controls": True,
            "block_diagram_image": "/assets/feedback_system_analysis/image_1dc166.png",
            "system_info": {
                # Current parameters
                "beta": round(self.parameters["beta"], 4),
                "K0": int(self.parameters["K0"]),
                "alpha": round(self.parameters["alpha"], 1),
                "input_amp": round(self.parameters["input_amp"], 2),

                # Open-loop metrics
                "ol_gain": self._format_value(m["ol_gain"]),
                "ol_bw": self._format_value(m["ol_bw"], " rad/s"),
                "ol_rise_time": self._format_value(m["ol_rise_time"], "s"),
                "ol_pole": round(m["ol_pole"], 1),

                # Closed-loop metrics
                "cl_gain": self._format_value(m["cl_gain"]),
                "cl_bw": self._format_value(m["cl_bw"], " rad/s"),
                "cl_rise_time": self._format_value(m["cl_rise_time"], "s"),
                "cl_pole": round(m["cl_pole"], 1),

                # Performance metrics
                "loop_gain": round(m["loop_gain"], 2),
                "speedup": round(m["speedup"], 2),

                # Transfer functions (symbolic)
                "transfer_function": {
                    "open_loop": "K(s) = αK₀ / (s + α)",
                    "closed_loop": "H(s) = αK₀ / (s + α(1+βK₀))",
                },
            },
        }

        return state
