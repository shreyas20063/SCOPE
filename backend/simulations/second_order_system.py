"""
Second-Order System Response Simulator

Implements an interactive second-order system frequency response simulation with:
- Pole-Zero map in S-plane showing stability region
- System information panel (ω₀, Q, ζ, damping type, bandwidth)
- Bode magnitude and phase plots

Applicable to RLC circuits, mass-spring-damper systems, control systems, and more.
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from .base_simulator import BaseSimulator


class SecondOrderSystemSimulator(BaseSimulator):
    """
    Second-Order System frequency response simulation.

    Parameters:
    - omega_0: Natural frequency (rad/s)
    - Q: Quality factor
    """

    # Configuration constants
    FREQ_RANGE = (-1.0, 4.0)  # Log scale: 0.1 to 10000 rad/s
    FREQ_POINTS = 2000

    # Fixed axis ranges (from original visuals.py)
    POLE_ZERO_X_RANGE = [-600, 50]
    POLE_ZERO_Y_RANGE = [-120, 120]
    BODE_MAG_X_RANGE = [0.1, 10000]
    BODE_MAG_Y_RANGE = [-80, 40]
    BODE_PHASE_Y_RANGE = [-200, 10]

    # Colors - Unified with DC Motor simulation
    POLE_COLOR = "#f87171"           # Coral red - poles marker
    OMEGA0_COLOR = "#fbbf24"         # Amber - ω₀ circle (natural frequency)
    RESPONSE_COLOR = "#22d3ee"       # Cyan - main response curve
    STABLE_REGION_COLOR = "#34d399"  # Emerald - stable region
    REFERENCE_COLOR = "#f472b6"      # Pink - reference lines
    IMAGINARY_AXIS_COLOR = "#a855f7" # Purple - stability boundary

    # Parameter schema - Q_slider uses 0-100 range with logarithmic mapping to Q 0.1-10
    # Slider 0-50% → Q 0.1 to 1 (low Q gets more resolution)
    # Slider 50-100% → Q 1 to 10 (high Q range)
    PARAMETER_SCHEMA = {
        "omega_0": {
            "type": "slider",
            "min": 1.0,
            "max": 100.0,
            "step": 0.5,
            "default": 50.0,
            "unit": "rad/s",
        },
        "Q_slider": {
            "type": "slider",
            "min": 0,
            "max": 100,
            "step": 1,
            "default": 50,
            "label": "Quality Factor Q",
            "display_transform": "q_log",
        },
    }

    DEFAULT_PARAMS = {
        "omega_0": 50.0,
        "Q_slider": 50,  # Maps to Q=1.0
    }

    @staticmethod
    def _slider_to_Q(slider_value: float) -> float:
        """
        Transform slider value (0-100) to actual Q (0.1-10) using logarithmic mapping.
        Q = 10^((slider/50) - 1)
        - slider=0 → Q=0.1
        - slider=50 → Q=1.0
        - slider=100 → Q=10.0
        """
        # Clamp slider to valid range
        slider_value = max(0, min(100, slider_value))
        # Logarithmic mapping: Q = 10^((slider/50) - 1)
        Q = 10 ** ((slider_value / 50.0) - 1.0)
        return Q

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._poles = None
        self._damping_type = ""
        self._zeta = 0.0
        self._bandwidth = 0.0
        self._resonant_freq = None
        self._omega = None
        self._magnitude_db = None
        self._phase_deg = None

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
        """Compute all signals based on current parameters."""
        omega_0 = self.parameters["omega_0"]
        Q = self._slider_to_Q(self.parameters["Q_slider"])

        # Analyze system characteristics
        self._analyze_system(omega_0, Q)

        # Compute frequency response
        self._compute_frequency_response(omega_0, Q)

    # =========================================================================
    # Math functions (extracted from rlc_circuit/core/rlc_system.py)
    # =========================================================================

    def _analyze_system(self, omega_0: float, Q: float) -> None:
        """Calculate poles, damping details, and derived metrics."""
        zeta = 1.0 / (2.0 * Q)
        self._zeta = zeta

        if Q > 0.5:
            # Underdamped - complex conjugate poles
            real_part = -omega_0 * zeta
            imag_part = omega_0 * np.sqrt(max(0.0, 1.0 - zeta**2))
            self._poles = np.array([
                complex(real_part, imag_part),
                complex(real_part, -imag_part)
            ])
            self._damping_type = "Underdamped (Complex Conjugate Poles)"
        elif np.isclose(Q, 0.5):
            # Critically damped - repeated real poles
            repeated_pole = -omega_0 / 2.0
            self._poles = np.array([repeated_pole, repeated_pole])
            self._damping_type = "Critically Damped (Repeated Real Poles)"
        else:
            # Overdamped - real distinct poles
            sqrt_term = np.sqrt(zeta**2 - 1.0)
            s1 = -omega_0 * (zeta + sqrt_term)
            s2 = -omega_0 * (zeta - sqrt_term)
            self._poles = np.array([s1, s2])
            self._damping_type = "Overdamped (Real Distinct Poles)"

        # Resonant frequency (only exists for Q > 0.707)
        self._resonant_freq = None
        if Q > 0.707:
            self._resonant_freq = omega_0 * np.sqrt(1.0 - 1.0 / (2.0 * Q**2))

        # Bandwidth
        self._bandwidth = omega_0 / Q

    def _compute_frequency_response(self, omega_0: float, Q: float) -> None:
        """Compute Bode magnitude and phase response."""
        self._omega = np.logspace(
            self.FREQ_RANGE[0],
            self.FREQ_RANGE[1],
            self.FREQ_POINTS
        )

        # Transfer function: H(s) = ω₀² / (s² + (ω₀/Q)s + ω₀²)
        # H(jω) = ω₀² / ((jω)² + (ω₀/Q)(jω) + ω₀²)
        s = 1j * self._omega
        num = omega_0**2
        den = s**2 + (omega_0 / Q) * s + omega_0**2
        response = num / den

        self._magnitude_db = 20 * np.log10(np.abs(response))
        self._phase_deg = np.angle(response, deg=True)

    # =========================================================================
    # Plot generation
    # =========================================================================

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate Plotly plot dictionaries."""
        if not self._initialized:
            self.initialize()

        plots = [
            self._create_pole_zero_plot(),
            self._create_bode_magnitude_plot(),
            self._create_bode_phase_plot(),
        ]
        return plots

    def get_state(self) -> Dict[str, Any]:
        """Return current simulation state with system info metadata."""
        base_state = super().get_state()

        omega_0 = self.parameters["omega_0"]
        Q = self._slider_to_Q(self.parameters["Q_slider"])

        # Format pole information
        if np.iscomplex(self._poles[0]):
            pole_str = f"s = {self._poles[0].real:.2f} ± {abs(self._poles[0].imag):.2f}j"
            pole_magnitude = round(abs(self._poles[0]), 2)
        else:
            pole_str = f"s₁ = {self._poles[0]:.2f}, s₂ = {self._poles[1]:.2f}"
            pole_magnitude = None

        # Add metadata with system info
        base_state["metadata"] = {
            "simulation_type": "second_order_system",
            "sticky_controls": True,  # Keep control panel fixed when scrolling
            "system_info": {
                "omega_0": round(omega_0, 2),
                "Q": round(Q, 3),
                "zeta": round(self._zeta, 4),
                "damping_type": self._damping_type,
                "poles": pole_str,
                "pole_magnitude": pole_magnitude,
                "bandwidth": round(self._bandwidth, 2),
                "resonant_freq": round(self._resonant_freq, 2) if self._resonant_freq else None,
            },
            "current_params": {
                "omega_0": omega_0,
                "Q": Q,
                "Q_slider": self.parameters["Q_slider"],
            },
        }

        return base_state

    def _create_pole_zero_plot(self) -> Dict[str, Any]:
        """Create pole-zero map in S-plane with auto-adjusting axes."""
        omega_0 = self.parameters["omega_0"]
        Q = self._slider_to_Q(self.parameters["Q_slider"])

        # Get damping type for title
        damping_label = "Underdamped" if Q > 0.5 else ("Critical" if abs(Q - 0.5) < 0.01 else "Overdamped")

        # Default fixed axis limits
        default_xlim = [-600, 50]
        default_ylim = [-120, 120]

        # Calculate actual pole bounds for auto-adjusting
        pole_x_values = []
        pole_y_values = []
        for pole in self._poles:
            if np.iscomplex(pole):
                pole_x_values.append(pole.real)
                pole_y_values.append(abs(pole.imag))
            else:
                pole_x_values.append(float(pole))

        # Determine if we need to expand axes (only expand, never shrink)
        margin = 0.15
        xlim = list(default_xlim)
        ylim = list(default_ylim)

        if pole_x_values:
            min_x = min(pole_x_values)
            if min_x < default_xlim[0]:
                xlim[0] = min_x * (1 + margin) if min_x < 0 else min_x - abs(min_x) * margin

        if pole_y_values:
            max_y = max(pole_y_values)
            if max_y > default_ylim[1]:
                ylim[1] = max_y * (1 + margin)
                ylim[0] = -ylim[1]

        traces = []

        # Shade stable region (left half-plane) with emerald green
        traces.append({
            "x": [xlim[0], 0, 0, xlim[0], xlim[0]],
            "y": [ylim[0], ylim[0], ylim[1], ylim[1], ylim[0]],
            "type": "scatter",
            "mode": "lines",
            "fill": "toself",
            "fillcolor": "rgba(52, 211, 153, 0.08)",
            "line": {"color": "rgba(52, 211, 153, 0.4)", "width": 1.5},
            "name": "Stable Region (Re < 0)",
            "showlegend": True,
            "hoverinfo": "skip",
        })

        # Add imaginary axis (jω axis) - the stability boundary
        traces.append({
            "x": [0, 0],
            "y": [ylim[0], ylim[1]],
            "type": "scatter",
            "mode": "lines",
            "line": {"color": self.IMAGINARY_AXIS_COLOR, "width": 2.5, "dash": "solid"},
            "name": "jω axis (Stability Boundary)",
            "showlegend": True,
            "hoverinfo": "name",
        })

        # Add ωn circle only when complex poles exist (underdamped)
        has_complex_poles = len(self._poles) > 0 and np.iscomplex(self._poles[0])
        if has_complex_poles:
            omega_n = np.abs(self._poles[0])
            theta = np.linspace(0, 2 * np.pi, 100)
            circle_x = omega_n * np.cos(theta)
            circle_y = omega_n * np.sin(theta)
            traces.append({
                "x": circle_x.tolist(),
                "y": circle_y.tolist(),
                "type": "scatter",
                "mode": "lines",
                "line": {"color": self.OMEGA0_COLOR, "width": 2, "dash": "dash"},
                "name": f"ωn = {omega_n:.2f} (Natural Freq.)",
                "showlegend": True,
                "hovertemplate": f"ωn = {omega_n:.2f}<extra></extra>",
            })

        # Create pole markers with improved styling
        for i, pole in enumerate(self._poles):
            if np.iscomplex(pole):
                traces.append({
                    "x": [pole.real],
                    "y": [pole.imag],
                    "type": "scatter",
                    "mode": "markers",
                    "marker": {
                        "symbol": "x",
                        "size": 16,
                        "color": self.POLE_COLOR,
                        "line": {"width": 3, "color": self.POLE_COLOR},
                    },
                    "name": "System Poles" if i == 0 else None,
                    "showlegend": i == 0,
                    "hovertemplate": f"Pole<br>σ = {pole.real:.3f}<br>ω = {pole.imag:.3f}j<extra></extra>",
                })
            else:
                traces.append({
                    "x": [float(pole)],
                    "y": [0],
                    "type": "scatter",
                    "mode": "markers",
                    "marker": {
                        "symbol": "x",
                        "size": 16,
                        "color": self.POLE_COLOR,
                        "line": {"width": 3, "color": self.POLE_COLOR},
                    },
                    "name": "System Poles" if i == 0 else None,
                    "showlegend": i == 0,
                    "hovertemplate": f"Pole<br>σ = {float(pole):.3f}<extra></extra>",
                })

        return {
            "id": "pole_zero",
            "title": f"Pole-Zero Map (S-Plane) | Q = {Q:.2f} ({damping_label})",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Real (σ)",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.2)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(0, 0, 0, 0.5)",
                    "zerolinewidth": 1,
                    "range": xlim,
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Imaginary (ω)",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.2)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(0, 0, 0, 0.5)",
                    "zerolinewidth": 1,
                    "range": ylim,
                    "scaleanchor": "x",
                    "scaleratio": 1,
                    "fixedrange": False,
                },
                "legend": {
                    "orientation": "v",
                    "yanchor": "bottom",
                    "y": 0.02,
                    "xanchor": "left",
                    "x": 0.02,
                    "bgcolor": "rgba(15, 23, 42, 0.8)",
                    "bordercolor": "rgba(148, 163, 184, 0.2)",
                    "borderwidth": 1,
                    "font": {"size": 11},
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "constant",
            },
        }

    def _create_bode_magnitude_plot(self) -> Dict[str, Any]:
        """Create Bode magnitude plot with auto-adjusting axes."""
        omega_0 = self.parameters["omega_0"]
        Q = self._slider_to_Q(self.parameters["Q_slider"])

        # Default y-axis limits
        default_ylim = [-80, 40]

        # Auto-adjust if magnitude exceeds bounds
        mag_max = float(np.max(self._magnitude_db))
        mag_min = float(np.min(self._magnitude_db))
        ylim = list(default_ylim)

        if mag_max > default_ylim[1]:
            ylim[1] = mag_max * 1.1
        if mag_min < default_ylim[0]:
            ylim[0] = mag_min * 1.1

        data = [
            # Magnitude response
            {
                "x": self._omega.tolist(),
                "y": self._magnitude_db.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "|H(jω)| Magnitude",
                "line": {"color": self.RESPONSE_COLOR, "width": 2.5, "shape": "spline"},
                "hovertemplate": "ω = %{x:.2f} rad/s<br>|H| = %{y:.2f} dB<extra></extra>",
            },
            # ω₀ vertical line
            {
                "x": [omega_0, omega_0],
                "y": [ylim[0], ylim[1]],
                "type": "scatter",
                "mode": "lines",
                "name": f"ω₀ = {omega_0:.1f} rad/s",
                "line": {"color": self.REFERENCE_COLOR, "width": 2, "dash": "dash"},
            },
        ]

        # Add 0 dB reference as trace
        data.append({
            "x": [self.BODE_MAG_X_RANGE[0], self.BODE_MAG_X_RANGE[1]],
            "y": [0, 0],
            "type": "scatter",
            "mode": "lines",
            "name": "0 dB Reference",
            "line": {"color": "rgba(148, 163, 184, 0.4)", "width": 1.5, "dash": "dot"},
        })

        # Add -3dB bandwidth line if resonant
        if Q > 0.707:
            peak_db = 20 * np.log10(Q / np.sqrt(1.0 - 1.0 / (2.0 * Q)**2))
            data.append({
                "x": [self.BODE_MAG_X_RANGE[0], self.BODE_MAG_X_RANGE[1]],
                "y": [peak_db - 3.0, peak_db - 3.0],
                "type": "scatter",
                "mode": "lines",
                "name": "-3dB Bandwidth",
                "line": {"color": self.STABLE_REGION_COLOR, "width": 1.5, "dash": "dot"},
            })

        return {
            "id": "bode_magnitude",
            "title": f"Bode Plot - Magnitude | ω₀ = {omega_0:.1f} rad/s, Q = {Q:.2f}",
            "data": data,
            "layout": {
                "xaxis": {
                    "title": "Frequency (rad/s)",
                    "type": "log",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.2)",
                    "range": [np.log10(self.BODE_MAG_X_RANGE[0]), np.log10(self.BODE_MAG_X_RANGE[1])],
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Magnitude (dB)",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.2)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "range": ylim,
                    "fixedrange": False,
                },
                "legend": {
                    "orientation": "v",
                    "yanchor": "bottom",
                    "y": 0.02,
                    "xanchor": "left",
                    "x": 0.02,
                    "bgcolor": "rgba(15, 23, 42, 0.8)",
                    "bordercolor": "rgba(148, 163, 184, 0.2)",
                    "borderwidth": 1,
                    "font": {"size": 11},
                },
                "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "uirevision": "bode_mag",
            },
        }

    def _create_bode_phase_plot(self) -> Dict[str, Any]:
        """Create Bode phase plot with unified styling."""
        omega_0 = self.parameters["omega_0"]
        Q = self._slider_to_Q(self.parameters["Q_slider"])

        data = [
            # Phase response
            {
                "x": self._omega.tolist(),
                "y": self._phase_deg.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "∠H(jω) Phase",
                "line": {"color": self.RESPONSE_COLOR, "width": 2.5, "shape": "spline"},
                "hovertemplate": "ω = %{x:.2f} rad/s<br>∠H = %{y:.1f}°<extra></extra>",
            },
            # ω₀ vertical line
            {
                "x": [omega_0, omega_0],
                "y": [self.BODE_PHASE_Y_RANGE[0], self.BODE_PHASE_Y_RANGE[1]],
                "type": "scatter",
                "mode": "lines",
                "name": f"ω₀ = {omega_0:.1f} rad/s",
                "line": {"color": self.REFERENCE_COLOR, "width": 2, "dash": "dash"},
            },
            # -90° reference line
            {
                "x": [self.BODE_MAG_X_RANGE[0], self.BODE_MAG_X_RANGE[1]],
                "y": [-90, -90],
                "type": "scatter",
                "mode": "lines",
                "name": "-90° (At ω₀)",
                "line": {"color": "rgba(148, 163, 184, 0.4)", "width": 1.5, "dash": "dot"},
            },
            # -180° reference line
            {
                "x": [self.BODE_MAG_X_RANGE[0], self.BODE_MAG_X_RANGE[1]],
                "y": [-180, -180],
                "type": "scatter",
                "mode": "lines",
                "name": "-180° (High Freq)",
                "line": {"color": "rgba(148, 163, 184, 0.4)", "width": 1.5, "dash": "dot"},
            },
        ]

        return {
            "id": "bode_phase",
            "title": f"Bode Plot - Phase | ω₀ = {omega_0:.1f} rad/s, Q = {Q:.2f}",
            "data": data,
            "layout": {
                "xaxis": {
                    "title": "Frequency (rad/s)",
                    "type": "log",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.2)",
                    "range": [np.log10(self.BODE_MAG_X_RANGE[0]), np.log10(self.BODE_MAG_X_RANGE[1])],
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Phase (degrees)",
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.2)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "range": self.BODE_PHASE_Y_RANGE,
                    "fixedrange": False,
                },
                "legend": {
                    "orientation": "v",
                    "yanchor": "bottom",
                    "y": 0.02,
                    "xanchor": "left",
                    "x": 0.02,
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
