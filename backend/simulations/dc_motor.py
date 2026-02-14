"""
DC Motor Feedback Control Simulator

Simulates feedback control systems for DC motors using transfer function analysis.
Features First-Order and Second-Order models with pole-zero visualization.

Math based on: dc_motor/core/motor_system.py
Transfer Functions:
- First-Order: H(s) = αγ/(s + αβγ)
- Second-Order: H(s) = αγp/(s² + ps + αβγp)
"""

import numpy as np
from typing import Any, Dict, List, Optional
from scipy import signal
from .base_simulator import BaseSimulator


class DCMotorSimulator(BaseSimulator):
    """
    DC Motor Feedback Control simulation.

    Parameters (matching PyQt5 exactly):
    - alpha: Amplifier gain (1-500, default 10, scaled by 100)
    - beta: Feedback gain (0.01-1.0, default 0.5, scaled by 100)
    - gamma: Motor constant (0.1-5.0, default 1.0, scaled by 10)
    - p: Lag pole location (0.5-30, default 10, scaled by 10) - only for Second-Order
    - model_type: "first_order" or "second_order"
    """

    # Configuration
    SIMULATION_TIME = 5.0  # seconds (fixed as in PyQt5)
    NUM_SAMPLES = 2000  # Same as PyQt5

    # Colors - Professional, visually distinct palette
    STEP_RESPONSE_COLOR = "#22d3ee"  # Cyan - main response (vivid, distinct)
    FINAL_VALUE_COLOR = "#f472b6"    # Pink - final value line (clearly different)
    ENVELOPE_COLOR = "#fbbf24"       # Amber - envelope curves (warm contrast)
    POLE_COLOR = "#f87171"           # Coral red - poles marker
    STABLE_REGION_COLOR = "#34d399"  # Emerald - stable region shading

    # Parameter schema - ranges expanded to include PyQt5 defaults
    # PyQt5 defaults: alpha=10.0, beta=0.5, gamma=1.0, p=10.0
    PARAMETER_SCHEMA = {
        "alpha": {
            "type": "slider",
            "min": 0.1,
            "max": 50.0,
            "step": 0.1,
            "default": 10.0,
            "unit": "",
            "label": "α (Amplifier gain)",
            "group": "Parameters",
        },
        "beta": {
            "type": "slider",
            "min": 0.01,
            "max": 1.0,
            "step": 0.01,
            "default": 0.5,
            "unit": "",
            "label": "β (Feedback gain)",
            "group": "Parameters",
        },
        "gamma": {
            "type": "slider",
            "min": 0.1,
            "max": 5.0,
            "step": 0.1,
            "default": 1.0,
            "unit": "",
            "label": "γ (Motor constant)",
            "group": "Parameters",
        },
        "p": {
            "type": "slider",
            "min": 1.0,
            "max": 30.0,
            "step": 0.1,
            "default": 10.0,
            "unit": "",
            "label": "p (Lag pole)",
            "group": "Parameters",
            "visible_when": {"model_type": "second_order"},
        },
        "model_type": {
            "type": "select",
            "options": [
                {"value": "first_order", "label": "First-Order"},
                {"value": "second_order", "label": "Second-Order"},
            ],
            "default": "first_order",
            "label": "Model Selection",
            "group": "Model",
        },
    }

    DEFAULT_PARAMS = {
        "alpha": 10.0,
        "beta": 0.5,
        "gamma": 1.0,
        "p": 10.0,
        "model_type": "first_order",
    }

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._time = None
        self._step_response = None
        self._poles = None
        self._zeros = None
        self._transfer_function = None

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
        """Calculate system transfer function and step response."""
        # Extract parameters
        alpha = self.parameters["alpha"]
        beta = self.parameters["beta"]
        gamma = self.parameters["gamma"]
        p = self.parameters["p"]
        model_type = self.parameters["model_type"]

        # Calculate transfer function and poles
        if model_type == "first_order":
            self._transfer_function, self._poles, self._zeros = self._first_order_system(
                alpha, beta, gamma
            )
        else:
            self._transfer_function, self._poles, self._zeros = self._second_order_system(
                alpha, beta, gamma, p
            )

        # Calculate step response (fixed time span as in PyQt5)
        self._time = np.linspace(0, self.SIMULATION_TIME, self.NUM_SAMPLES)
        t_step, y_step = signal.step(self._transfer_function, T=self._time)
        self._step_response = y_step

    def _first_order_system(self, alpha, beta, gamma):
        """
        Calculate first-order closed-loop system.
        Transfer function: H(s) = αγ/(s + αβγ)
        """
        num = [alpha * gamma]
        den = [1, alpha * beta * gamma]
        poles = np.array([-alpha * beta * gamma])
        zeros = np.array([])
        return signal.TransferFunction(num, den), poles, zeros

    def _second_order_system(self, alpha, beta, gamma, p):
        """
        Calculate second-order closed-loop system.
        Transfer function: H(s) = αγp/(s² + ps + αβγp)
        """
        num = [alpha * gamma * p]
        den = [1, p, alpha * beta * gamma * p]

        # Calculate poles: s = -p/2 ± sqrt((p/2)² - αβγp)
        discriminant = (p / 2) ** 2 - alpha * beta * gamma * p

        if discriminant >= 0:
            # Real poles (overdamped)
            poles = np.array([
                -p / 2 + np.sqrt(discriminant),
                -p / 2 - np.sqrt(discriminant)
            ])
        else:
            # Complex conjugate poles (underdamped)
            real_part = -p / 2
            imag_part = np.sqrt(-discriminant)
            poles = np.array([
                complex(real_part, imag_part),
                complex(real_part, -imag_part)
            ])

        zeros = np.array([])
        return signal.TransferFunction(num, den), poles, zeros

    # =========================================================================
    # Plot generation
    # =========================================================================

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate Plotly plot dictionaries."""
        if not self._initialized:
            self.initialize()

        plots = [
            self._create_pole_zero_plot(),
            self._create_step_response_plot(),
        ]
        return plots

    def get_state(self) -> Dict[str, Any]:
        """Return current simulation state with extra info."""
        base_state = super().get_state()

        # Add system information
        alpha = self.parameters["alpha"]
        beta = self.parameters["beta"]
        gamma = self.parameters["gamma"]
        p = self.parameters["p"]
        model_type = self.parameters["model_type"]

        # Calculate transfer function strings
        if model_type == "first_order":
            tf_num = f"{alpha * gamma:.1f}"
            tf_den = f"s + {alpha * beta * gamma:.2f}"
            pole_str = f"s = {self._poles[0]:.2f}"
            pole_type = "Real → Stable"
            tf_symbolic = "αγ / (s + αβγ)"
        else:
            tf_num = f"{alpha * gamma * p:.1f}"
            tf_den = f"s² + {p:.1f}s + {alpha * beta * gamma * p:.2f}"
            tf_symbolic = "αγp / (s² + ps + αβγp)"
            if np.iscomplex(self._poles[0]):
                pole_str = f"s = {self._poles[0].real:.2f} ± {abs(self._poles[0].imag):.2f}j"
                pole_type = "Complex conjugate → Oscillatory"
            else:
                pole_str = f"s₁ = {self._poles[0]:.2f}, s₂ = {self._poles[1]:.2f}"
                pole_type = "Real → Overdamped"

        # Steady-state value
        steady_state = 1.0 / beta if beta > 0 else float('inf')

        # Block diagram image path
        if model_type == "first_order":
            block_diagram = "/assets/dc_motor/image_389368.png"
        else:
            block_diagram = "/assets/dc_motor/image_389387.png"

        # Put all extra info in metadata (frontend expects it here)
        base_state["metadata"] = {
            "simulation_type": "dc_motor_feedback_control",
            "sticky_controls": True,  # Keep control panel fixed when scrolling
            "block_diagram_image": block_diagram,
            "system_info": {
                "transfer_function": {
                    "symbolic": tf_symbolic,
                    "numerator": tf_num,
                    "denominator": tf_den,
                },
                "poles": pole_str,
                "pole_type": pole_type,
                "steady_state_value": round(steady_state, 4),
                "model_type": "First-Order" if model_type == "first_order" else "Second-Order",
            },
            "current_params": {
                "alpha": alpha,
                "beta": beta,
                "gamma": gamma,
                "p": p if model_type == "second_order" else None,
            },
        }

        return base_state

    def _create_pole_zero_plot(self) -> Dict[str, Any]:
        """Create pole-zero map with auto-adjusting axis limits."""
        # Default fixed axis limits
        default_xlim = [-60, 10]
        default_ylim = [-35, 35]

        # Calculate actual pole bounds
        pole_x_values = []
        pole_y_values = []
        for pole in self._poles:
            if np.iscomplex(pole):
                pole_x_values.append(pole.real)
                pole_y_values.append(abs(pole.imag))
            else:
                pole_x_values.append(float(pole))

        # Determine if we need to expand axes (only expand, never shrink)
        margin = 0.15  # 15% margin when expanding
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
                ylim[0] = -ylim[1]  # Keep symmetric

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
            "line": {"color": "#a855f7", "width": 2.5, "dash": "solid"},  # Purple - stability boundary
            "name": "jω axis (Stability Boundary)",
            "showlegend": True,
            "hoverinfo": "name",
        })

        # Add circle around complex conjugate poles (when they exist)
        # The circle has radius ωn (natural frequency) = |pole|
        has_complex_poles = len(self._poles) > 0 and np.iscomplex(self._poles[0])
        if has_complex_poles:
            # Calculate natural frequency (radius of circle through poles)
            pole = self._poles[0]
            omega_n = np.abs(pole)  # Natural frequency = |pole|

            # Generate circle points
            theta_circle = np.linspace(0, 2 * np.pi, 100)
            x_circle = omega_n * np.cos(theta_circle)
            y_circle = omega_n * np.sin(theta_circle)

            traces.append({
                "x": x_circle.tolist(),
                "y": y_circle.tolist(),
                "type": "scatter",
                "mode": "lines",
                "line": {"color": "#fbbf24", "width": 2, "dash": "dash"},  # Amber
                "name": f"ωn = {omega_n:.2f} (Natural Freq.)",
                "showlegend": True,
                "hovertemplate": f"ωn = {omega_n:.2f}<extra></extra>",
            })

        # Plot poles with improved styling
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
            "id": "pole_zero_map",
            "title": "Pole-Zero Map (s-plane)",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Real (σ)",
                    "range": xlim,
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.2)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(0, 0, 0, 0.5)",
                    "zerolinewidth": 1,
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Imaginary (ω)",
                    "range": ylim,
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.2)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(0, 0, 0, 0.5)",
                    "zerolinewidth": 1,
                    "fixedrange": False,
                    "scaleanchor": "x",
                    "scaleratio": 1,
                },
                "legend": {
                    "orientation": "v",
                    "yanchor": "bottom",
                    "y": 0.02,
                    "xanchor": "right",
                    "x": 0.98,
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

    def _create_step_response_plot(self) -> Dict[str, Any]:
        """Create step response plot with auto-adjusting axis limits."""
        beta = self.parameters["beta"]
        model_type = self.parameters["model_type"]

        # Default fixed y-axis limits
        default_ylim = [-0.5, 3.5]

        # Calculate actual response bounds
        response_min = float(np.min(self._step_response))
        response_max = float(np.max(self._step_response))
        final_value = 1.0 / beta if beta > 0 else 0

        # Determine if we need to expand y-axis (only expand, never shrink)
        margin = 0.15  # 15% margin when expanding
        ylim = list(default_ylim)

        # Check if response goes below default min
        if response_min < default_ylim[0]:
            ylim[0] = response_min * (1 + margin) if response_min < 0 else response_min - abs(response_min) * margin

        # Check if response or final value goes above default max
        max_val = max(response_max, final_value)
        if max_val > default_ylim[1]:
            ylim[1] = max_val * (1 + margin)

        traces = []

        # Step response with improved styling
        traces.append({
            "x": self._time.tolist(),
            "y": self._step_response.tolist(),
            "type": "scatter",
            "mode": "lines",
            "name": "Step Response θ(t)",
            "line": {"color": self.STEP_RESPONSE_COLOR, "width": 2.5, "shape": "spline"},
            "hovertemplate": "t = %{x:.3f}s<br>θ = %{y:.4f}<extra></extra>",
        })

        # Final value line (steady-state)
        if beta > 0:
            traces.append({
                "x": [0, self.SIMULATION_TIME],
                "y": [final_value, final_value],
                "type": "scatter",
                "mode": "lines",
                "name": f"Steady-State (1/β = {final_value:.2f})",
                "line": {"color": self.FINAL_VALUE_COLOR, "width": 2, "dash": "dash"},
                "hoverinfo": "name",
            })

        # Add envelope for second-order with complex poles
        if model_type == "second_order" and np.iscomplex(self._poles[0]):
            real_part = self._poles[0].real
            envelope_decay = np.exp(real_part * self._time)

            if beta > 0:
                envelope_upper = (1 / beta) * (1 + envelope_decay)
                envelope_lower = (1 / beta) * (1 - envelope_decay)

                traces.append({
                    "x": self._time.tolist(),
                    "y": envelope_upper.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": f"Envelope: e^({real_part:.2f}t)",
                    "line": {"color": self.ENVELOPE_COLOR, "width": 1.5, "dash": "dash"},
                    "opacity": 0.5,
                })
                traces.append({
                    "x": self._time.tolist(),
                    "y": envelope_lower.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": None,
                    "showlegend": False,
                    "line": {"color": self.ENVELOPE_COLOR, "width": 1.5, "dash": "dash"},
                    "opacity": 0.5,
                })

        return {
            "id": "step_response",
            "title": "Step Response",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Time (seconds)",
                    "range": [0, self.SIMULATION_TIME],
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.2)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "θ(t)",
                    "range": ylim,
                    "showgrid": True,
                    "gridcolor": "rgba(148, 163, 184, 0.2)",
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "fixedrange": False,
                },
                "legend": {
                    "orientation": "v",
                    "yanchor": "bottom",
                    "y": 0.02,
                    "xanchor": "right",
                    "x": 0.98,
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
