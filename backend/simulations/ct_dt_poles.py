"""
CT/DT Poles Conversion Simulator

Demonstrates continuous-time to discrete-time pole transformations
using Forward Euler, Backward Euler, and Trapezoidal methods.

Features:
- S-Plane visualization with stability regions
- Z-Plane with unit circle and pole trajectory
- Step response comparison with RMS error
- Stability analysis map
- Pole trajectory visualization
- Theory/Learning panel with method explanations

Math extracted from: ct_dt_poles/core/math_handler.py
"""

import numpy as np
from typing import Any, Dict, List, Optional
from .base_simulator import BaseSimulator


class CTDTPolesSimulator(BaseSimulator):
    """
    CT/DT Poles Conversion simulation.

    Parameters:
    - t_tau_ratio: T/τ ratio (step size relative to time constant)
    - method: Transformation method (forward_euler, backward_euler, trapezoidal)

    Internal:
    - tau is fixed at 1.0 (matching PyQt5)
    - T = t_tau_ratio * tau
    """

    # Configuration - fixed tau as in PyQt5
    TAU = 1.0
    NUM_SAMPLES = 100
    T_TAU_RANGE = np.linspace(0.01, 3.0, 150)
    TRAJECTORY_T_TAU_VALUES = np.linspace(0.1, 3.0, 60)

    # Unified color palette - matches DC Motor simulation
    COLORS = {
        # Primary response colors
        "continuous": "#22d3ee",       # Cyan - CT system (matches DC Motor step response)
        "reference": "#f472b6",        # Pink - reference lines (matches DC Motor final value)
        "envelope": "#fbbf24",         # Amber - envelope/accent curves

        # Stability colors
        "stable_discrete": "#34d399",  # Emerald green - stable DT
        "unstable_discrete": "#f87171", # Coral red - unstable DT/poles
        "pole_marker": "#f87171",      # Coral red - poles (matches DC Motor)

        # S-plane/Z-plane colors
        "imaginary_axis": "#a855f7",   # Purple - stability boundary (matches DC Motor)
        "unit_circle": "#a855f7",      # Purple for unit circle (same as imaginary axis)
        "omega_circle": "#fbbf24",     # Amber - natural frequency circle

        # Region fills
        "fill_stable": "rgba(52, 211, 153, 0.08)",   # Light emerald (matches DC Motor)
        "fill_unstable": "rgba(248, 113, 113, 0.08)",

        # Trajectory colors
        "trajectory_stable": "#34d399",
        "trajectory_marginal": "#fbbf24",
        "trajectory_unstable": "#f87171",

        # Grid and text
        "grid": "rgba(148, 163, 184, 0.2)",
        "text": "#e2e8f0",
    }

    # Method explanations from PyQt5 Config.METHOD_EXPLANATIONS
    METHOD_EXPLANATIONS = {
        "forward_euler": {
            "name": "Forward Euler",
            "formula": "z = 1 + sT",
            "concept": "Estimates derivatives by looking forward in time",
            "strength": "Simple and intuitive implementation",
            "weakness": "Can become unstable for large step sizes",
            "stability_limit": "Stable only when T/τ < 2",
            "real_world": "Used in real-time systems where simplicity matters",
        },
        "backward_euler": {
            "name": "Backward Euler",
            "formula": "z = 1/(1-sT)",
            "concept": "Estimates derivatives by looking backward in time",
            "strength": "Inherently stable for all step sizes",
            "weakness": "Can be overly conservative (too damped)",
            "stability_limit": "Always stable if CT system is stable",
            "real_world": "Preferred for stiff differential equations",
        },
        "trapezoidal": {
            "name": "Trapezoidal (Bilinear)",
            "formula": "z = (1+sT/2)/(1-sT/2)",
            "concept": "Averages forward and backward estimates",
            "strength": "Best accuracy and stability balance",
            "weakness": "Slightly more complex to implement",
            "stability_limit": "Maps imaginary axis to unit circle exactly",
            "real_world": "Industry standard for most applications",
        },
    }

    # Guided scenarios from PyQt5 Config.GUIDED_SCENARIOS
    GUIDED_SCENARIOS = [
        {"t_tau": 0.3, "method": "forward_euler", "message": "Start here: Small step size, very stable"},
        {"t_tau": 1.0, "method": "forward_euler", "message": "Moderate step size, still stable but see the difference"},
        {"t_tau": 1.8, "method": "forward_euler", "message": "Getting close to instability limit"},
        {"t_tau": 2.2, "method": "forward_euler", "message": "UNSTABLE! See the oscillations"},
        {"t_tau": 2.2, "method": "backward_euler", "message": "Same step size, but now stable with Backward Euler"},
        {"t_tau": 2.2, "method": "trapezoidal", "message": "Trapezoidal also handles large steps well"},
    ]

    # Parameter schema - T/τ ratio slider matching PyQt5 (0.01 to 3.0, default 0.50)
    PARAMETER_SCHEMA = {
        "t_tau_ratio": {
            "type": "slider",
            "label": "T/τ Ratio",
            "min": 0.01,
            "max": 3.0,
            "step": 0.01,
            "default": 0.50,
            "unit": "",
            "description": "Sampling period relative to time constant",
        },
        "method": {
            "type": "select",
            "label": "Transformation Method",
            "options": [
                {"value": "forward_euler", "label": "Forward Euler"},
                {"value": "backward_euler", "label": "Backward Euler"},
                {"value": "trapezoidal", "label": "Trapezoidal (Bilinear)"},
            ],
            "default": "forward_euler",
            "description": "Numerical integration method for CT to DT conversion",
        },
        "guided_scenario": {
            "type": "select",
            "label": "Guided Scenario",
            "options": [
                {"value": "none", "label": "Free Exploration"},
                {"value": "0", "label": "1: Small Step (Stable)"},
                {"value": "1", "label": "2: Moderate Step"},
                {"value": "2", "label": "3: Near Limit"},
                {"value": "3", "label": "4: FE Unstable"},
                {"value": "4", "label": "5: BE Stable"},
                {"value": "5", "label": "6: Trapezoidal"},
            ],
            "default": "none",
            "description": "Select a guided learning scenario",
        },
    }

    DEFAULT_PARAMS = {
        "t_tau_ratio": 0.50,
        "method": "forward_euler",
        "guided_scenario": "none",
    }

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._tau = self.TAU
        self._T = 0.5
        self._s_pole = None
        self._z_pole = None
        self._ct_response = None
        self._dt_response = None
        self._t_continuous = None
        self._t_discrete = None
        self._stability_curve = None
        self._pole_trajectory = None
        self._trajectory_t_tau = None
        self._is_stable = True
        self._rms_error = 0.0
        self._performance_rating = "GOOD"

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
        if name == "guided_scenario" and value != "none":
            # Apply guided scenario settings
            try:
                scenario_idx = int(value)
                if 0 <= scenario_idx < len(self.GUIDED_SCENARIOS):
                    scenario = self.GUIDED_SCENARIOS[scenario_idx]
                    self.parameters["t_tau_ratio"] = scenario["t_tau"]
                    self.parameters["method"] = scenario["method"]
                    self.parameters["guided_scenario"] = value
            except (ValueError, TypeError):
                pass
        elif name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
            # Reset guided scenario if manually changing parameters
            if name in ["t_tau_ratio", "method"]:
                self.parameters["guided_scenario"] = "none"

        self._compute()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        """Reset simulation to default parameters."""
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._initialized = True
        self._compute()
        return self.get_state()

    def _compute(self) -> None:
        """Compute CT/DT transformation."""
        t_tau_ratio = self.parameters["t_tau_ratio"]
        method = self.parameters["method"]

        # Compute T from T/τ ratio (τ is fixed at 1.0)
        self._T = t_tau_ratio * self._tau

        # CT pole: s = -1/τ
        self._s_pole = -1.0 / self._tau

        # DT pole using selected method
        self._z_pole = self._get_dt_pole(self._s_pole, self._T, method)

        # Check stability
        self._is_stable = abs(self._z_pole) < 1.0

        # Compute step responses
        self._compute_step_responses(self._tau, self._T, method)

        # Compute RMS error
        self._compute_rms_error()

        # Compute stability curve
        self._compute_stability_curve(self._tau, method)

        # Compute pole trajectory
        self._compute_pole_trajectory(self._tau, method)

    def _get_dt_pole(self, s_pole: float, T: float, method: str) -> complex:
        """Compute DT pole using selected method."""
        if method == "forward_euler":
            return 1 + s_pole * T
        elif method == "backward_euler":
            return 1 / (1 - s_pole * T)
        elif method == "trapezoidal":
            return (1 + s_pole * T / 2) / (1 - s_pole * T / 2)
        return 1 + s_pole * T

    def _compute_step_responses(self, tau: float, T: float, method: str) -> None:
        """Compute CT and DT step responses."""
        # Time range depends on stability
        if self._is_stable:
            t_max = min(6 * tau, 15)
        else:
            t_max = min(3 * tau, 8)

        # Continuous-time response
        self._t_continuous = np.linspace(0, t_max, 1000)
        self._ct_response = (1 - np.exp(-self._t_continuous / tau)) * (self._t_continuous >= 0)

        # Discrete-time response
        n_samples = min(int(t_max / T) + 1, 300)
        self._t_discrete = np.arange(n_samples) * T

        y = np.zeros(n_samples)
        if method == "forward_euler":
            y_val = 0.0
            for i in range(n_samples):
                y_val = (1 - T / tau) * y_val + (T / tau)
                y[i] = y_val
                if abs(y_val) > 50:  # Prevent explosion
                    y[i:] = np.nan
                    break
        elif method == "backward_euler":
            y_prev = 0.0
            for i in range(n_samples):
                y_val = (y_prev + T / tau) / (1 + T / tau)
                y[i] = y_val
                y_prev = y_val
        elif method == "trapezoidal":
            y_prev = 0.0
            x_prev = 0.0
            for i in range(n_samples):
                x_current = 1.0
                numerator = y_prev * (1 - T / (2 * tau)) + (T / (2 * tau)) * (x_current + x_prev)
                denominator = 1 + T / (2 * tau)
                y_val = numerator / denominator
                y[i] = y_val
                y_prev = y_val
                x_prev = x_current

        self._dt_response = y

    def _compute_rms_error(self) -> None:
        """Calculate RMS error between CT and DT responses."""
        try:
            # Only compute if we have valid data
            valid_dt = ~np.isnan(self._dt_response)
            if not np.any(valid_dt):
                self._rms_error = float("inf")
                self._performance_rating = "UNSTABLE"
                return

            # Interpolate discrete response for comparison
            t_valid = self._t_discrete[valid_dt]
            y_dt_valid = self._dt_response[valid_dt]

            if len(t_valid) < 2:
                self._rms_error = float("inf")
                self._performance_rating = "UNSTABLE"
                return

            # Get CT values at discrete time points
            y_ct_at_discrete = np.interp(t_valid, self._t_continuous, self._ct_response)

            # Calculate RMS error
            self._rms_error = np.sqrt(np.mean((y_ct_at_discrete - y_dt_valid) ** 2))

            # Performance categories matching PyQt5
            if self._rms_error < 0.05:
                self._performance_rating = "EXCELLENT"
            elif self._rms_error < 0.15:
                self._performance_rating = "GOOD"
            elif self._rms_error < 0.3:
                self._performance_rating = "FAIR"
            else:
                self._performance_rating = "POOR"

        except Exception:
            self._rms_error = float("inf")
            self._performance_rating = "ERROR"

    def _compute_stability_curve(self, tau: float, method: str) -> None:
        """Compute pole magnitude across T/τ range."""
        s_pole = -1.0 / tau
        magnitudes = []
        for T_tau in self.T_TAU_RANGE:
            T_temp = T_tau * tau
            z_pole = self._get_dt_pole(s_pole, T_temp, method)
            magnitudes.append(abs(z_pole))
        self._stability_curve = np.array(magnitudes)

    def _compute_pole_trajectory(self, tau: float, method: str) -> None:
        """Compute pole positions for trajectory visualization."""
        s_pole = -1.0 / tau
        trajectory = []
        self._trajectory_t_tau = self.TRAJECTORY_T_TAU_VALUES
        for T_tau in self._trajectory_t_tau:
            T_temp = T_tau * tau
            z_pole = self._get_dt_pole(s_pole, T_temp, method)
            trajectory.append(z_pole)
        self._pole_trajectory = trajectory

    # =========================================================================
    # Plot generation - matching PyQt5 exactly
    # =========================================================================

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate Plotly plot dictionaries matching PyQt5 layout."""
        if not self._initialized:
            self.initialize()

        plots = [
            # Main Tab plots
            self._create_s_plane_plot(),
            self._create_z_plane_plot(),
            self._create_step_response_plot(),
            # Stability Tab plots
            self._create_stability_map_plot(),
            self._create_pole_trajectory_plot(),
        ]
        return plots

    def _create_s_plane_plot(self) -> Dict[str, Any]:
        """Create S-plane pole plot with stability regions (matching DC Motor style)."""
        method = self.parameters["method"]
        T = self._T

        traces = []

        # 1. Left half-plane stability region (filled) - matches DC Motor
        traces.append({
            "x": [-5, 0, 0, -5, -5],
            "y": [-4, -4, 4, 4, -4],
            "type": "scatter",
            "mode": "lines",
            "fill": "toself",
            "fillcolor": self.COLORS["fill_stable"],
            "line": {"color": "rgba(52, 211, 153, 0.4)", "width": 1.5},
            "name": "Stable Region (Re < 0)",
            "showlegend": True,
            "hoverinfo": "skip",
        })

        # 2. Imaginary axis (jω axis) - the stability boundary (purple like DC Motor)
        traces.append({
            "x": [0, 0],
            "y": [-4, 4],
            "type": "scatter",
            "mode": "lines",
            "line": {"color": self.COLORS["imaginary_axis"], "width": 2.5, "dash": "solid"},
            "name": "jω axis (Stability Boundary)",
            "showlegend": True,
            "hoverinfo": "name",
        })

        # 3. Forward Euler stability boundary circle (if applicable)
        if method == "forward_euler" and T > 0 and (1/T) < 5:
            center_x = -1/T
            radius = 1/T
            theta = np.linspace(0, 2 * np.pi, 100)
            circle_x = center_x + radius * np.cos(theta)
            circle_y = radius * np.sin(theta)
            traces.append({
                "x": circle_x.tolist(),
                "y": circle_y.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": f"FE Limit (r=1/T={1/T:.2f})",
                "line": {"color": self.COLORS["envelope"], "width": 2, "dash": "dash"},
            })

        # 4. CT Pole marker (styled like DC Motor)
        traces.append({
            "x": [self._s_pole],
            "y": [0],
            "type": "scatter",
            "mode": "markers",
            "name": f"CT Pole: s = {self._s_pole:.2f}",
            "marker": {
                "symbol": "x",
                "size": 16,
                "color": self.COLORS["pole_marker"],
                "line": {"width": 3, "color": self.COLORS["pole_marker"]},
            },
            "hovertemplate": f"CT Pole<br>σ = {self._s_pole:.3f}<extra></extra>",
        })

        return {
            "id": "s_plane",
            "title": f"S-Domain Analysis | Method: {self.METHOD_EXPLANATIONS[method]['name']}",
            "plotType": "main",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Real (σ)",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "zeroline": True,
                    "zerolinecolor": "rgba(0, 0, 0, 0.5)",
                    "zerolinewidth": 1,
                    "range": [-5, 3],
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Imaginary (ω)",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "zeroline": True,
                    "zerolinecolor": "rgba(0, 0, 0, 0.5)",
                    "zerolinewidth": 1,
                    "range": [-4, 4],
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
                "uirevision": "s_plane",
            },
        }

    def _create_z_plane_plot(self) -> Dict[str, Any]:
        """Create Z-plane pole plot with unit circle (matching DC Motor style)."""
        z_real = float(np.real(self._z_pole))
        z_imag = float(np.imag(self._z_pole))
        z_magnitude = abs(self._z_pole)

        status = "STABLE" if self._is_stable else "UNSTABLE"
        status_color = self.COLORS["stable_discrete"] if self._is_stable else self.COLORS["unstable_discrete"]

        traces = []

        # 1. Unit circle filled (stability region) - matches DC Motor style
        theta = np.linspace(0, 2 * np.pi, 200)
        circle_x = np.cos(theta)
        circle_y = np.sin(theta)

        traces.append({
            "x": circle_x.tolist(),
            "y": circle_y.tolist(),
            "type": "scatter",
            "fill": "toself",
            "fillcolor": self.COLORS["fill_stable"],
            "line": {"color": self.COLORS["unit_circle"], "width": 2.5},
            "name": "Unit Circle (Stability Boundary)",
        })

        # 2. Distance line from origin to pole
        if self._z_pole != 0:
            traces.append({
                "x": [0, z_real],
                "y": [0, z_imag],
                "type": "scatter",
                "mode": "lines",
                "line": {"color": self.COLORS["reference"], "width": 2, "dash": "dash"},
                "name": f"|z| = {z_magnitude:.3f}",
            })

        # 3. DT Pole marker (styled like DC Motor)
        traces.append({
            "x": [z_real],
            "y": [z_imag],
            "type": "scatter",
            "mode": "markers",
            "name": f"DT Pole: z = {z_real:.3f}",
            "marker": {
                "symbol": "x",
                "size": 16,
                "color": status_color,
                "line": {"width": 3, "color": status_color},
            },
            "hovertemplate": f"DT Pole<br>Re = {z_real:.3f}<br>Im = {z_imag:.3f}<br>|z| = {z_magnitude:.3f}<extra></extra>",
        })

        # Annotations for stability info
        annotations = [{
            "x": 0.02,
            "y": 0.98,
            "xref": "paper",
            "yref": "paper",
            "text": f"<b>|z| = {z_magnitude:.3f} | {status}</b>",
            "showarrow": False,
            "font": {"color": status_color, "size": 11},
            "bgcolor": "rgba(15, 23, 42, 0.9)",
            "bordercolor": status_color,
            "borderwidth": 1,
            "borderpad": 4,
            "xanchor": "left",
            "yanchor": "top",
        }]

        return {
            "id": "z_plane",
            "title": f"Z-Domain Analysis | {status} (|z| = {z_magnitude:.3f})",
            "plotType": "main",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Real (Re)",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "zeroline": True,
                    "zerolinecolor": "rgba(0, 0, 0, 0.5)",
                    "zerolinewidth": 1,
                    "range": [-2.2, 2.2],
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Imaginary (Im)",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "zeroline": True,
                    "zerolinecolor": "rgba(0, 0, 0, 0.5)",
                    "zerolinewidth": 1,
                    "range": [-2.2, 2.2],
                    "scaleanchor": "x",
                    "scaleratio": 1,
                    "fixedrange": False,
                },
                "annotations": annotations,
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
                "uirevision": "z_plane",
            },
        }

    def _create_step_response_plot(self) -> Dict[str, Any]:
        """Create step response comparison plot with RMS error (matching DC Motor style)."""
        method_info = self.METHOD_EXPLANATIONS.get(self.parameters["method"], {})
        method_name = method_info.get("name", "Unknown")

        traces = []

        # 1. Continuous-time analytical solution (cyan like DC Motor)
        traces.append({
            "x": self._t_continuous.tolist(),
            "y": self._ct_response.tolist(),
            "type": "scatter",
            "mode": "lines",
            "name": "CT Analytical Solution",
            "line": {"color": self.COLORS["continuous"], "width": 2.5, "shape": "spline"},
            "hovertemplate": "t = %{x:.3f}s<br>y = %{y:.4f}<extra></extra>",
        })

        # 2. Final value line (pink like DC Motor)
        traces.append({
            "x": [0, float(self._t_continuous[-1])],
            "y": [1.0, 1.0],
            "type": "scatter",
            "mode": "lines",
            "name": "Steady-State (y = 1)",
            "line": {"color": self.COLORS["reference"], "width": 2, "dash": "dash"},
            "hoverinfo": "name",
        })

        # 3. Discrete-time approximation
        valid_mask = ~np.isnan(self._dt_response)
        t_valid = self._t_discrete[valid_mask].tolist()
        y_valid = self._dt_response[valid_mask].tolist()

        if self._is_stable:
            line_color = self.COLORS["stable_discrete"]
            method_label = f"{method_name} (DT)"
        else:
            line_color = self.COLORS["unstable_discrete"]
            method_label = f"{method_name} (UNSTABLE)"

        if len(y_valid) > 0 and max(abs(v) for v in y_valid if not np.isnan(v)) < 20:
            traces.append({
                "x": t_valid,
                "y": y_valid,
                "type": "scatter",
                "mode": "lines+markers",
                "name": method_label,
                "line": {"color": line_color, "width": 2},
                "marker": {"color": line_color, "size": 4},
                "hovertemplate": "n·T = %{x:.3f}s<br>y[n] = %{y:.4f}<extra></extra>",
            })

        # Performance annotation
        perf_colors = {
            "EXCELLENT": self.COLORS["stable_discrete"],
            "GOOD": self.COLORS["envelope"],
            "FAIR": self.COLORS["envelope"],
            "POOR": self.COLORS["unstable_discrete"],
            "UNSTABLE": self.COLORS["unstable_discrete"],
            "ERROR": self.COLORS["unstable_discrete"],
        }
        perf_color = perf_colors.get(self._performance_rating, "#94a3b8")

        annotations = [{
            "x": 0.02,
            "y": 0.98,
            "xref": "paper",
            "yref": "paper",
            "text": f"<b>Quality: {self._performance_rating} | RMS: {self._rms_error:.4f}</b>",
            "showarrow": False,
            "font": {"color": perf_color, "size": 11},
            "bgcolor": "rgba(15, 23, 42, 0.9)",
            "bordercolor": perf_color,
            "borderwidth": 1,
            "borderpad": 4,
            "xanchor": "left",
            "yanchor": "top",
        }]

        # Y-axis range based on stability
        y_range = [-0.1, 1.3] if self._is_stable else [-2, 2]

        return {
            "id": "step_response",
            "title": f"Step Response Comparison | {method_name}",
            "plotType": "main",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Time (s)",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "y(t)",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "range": y_range,
                    "fixedrange": False,
                },
                "annotations": annotations,
                "legend": {
                    "x": 0.98, "y": 0.02,
                    "xanchor": "right", "yanchor": "bottom",
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

    def _create_stability_map_plot(self) -> Dict[str, Any]:
        """Create stability analysis plot (matching DC Motor style)."""
        t_tau_current = self.parameters["t_tau_ratio"]
        z_magnitude = abs(self._z_pole)
        method = self.parameters["method"]
        method_name = self.METHOD_EXPLANATIONS[method]["name"]

        traces = []

        # 1. Stable region fill (|z| < 1)
        traces.append({
            "x": self.T_TAU_RANGE.tolist() + self.T_TAU_RANGE[::-1].tolist(),
            "y": [0] * len(self.T_TAU_RANGE) + [1] * len(self.T_TAU_RANGE),
            "type": "scatter",
            "fill": "toself",
            "fillcolor": self.COLORS["fill_stable"],
            "line": {"color": "rgba(52, 211, 153, 0.4)", "width": 1},
            "name": "Stable Region (|z| < 1)",
            "hoverinfo": "skip",
        })

        # 2. Stability curve (cyan like DC Motor step response)
        traces.append({
            "x": self.T_TAU_RANGE.tolist(),
            "y": self._stability_curve.tolist(),
            "type": "scatter",
            "mode": "lines",
            "name": "|z| Pole Magnitude",
            "line": {"color": self.COLORS["continuous"], "width": 2.5},
            "hovertemplate": "T/τ = %{x:.2f}<br>|z| = %{y:.3f}<extra></extra>",
        })

        # 3. Stability boundary line at |z| = 1 (pink like DC Motor final value)
        traces.append({
            "x": [0, 3],
            "y": [1, 1],
            "type": "scatter",
            "mode": "lines",
            "name": "Stability Boundary (|z| = 1)",
            "line": {"color": self.COLORS["reference"], "width": 2, "dash": "dash"},
        })

        # 4. Critical point marker for Forward Euler at T/τ = 2
        if method == "forward_euler":
            traces.append({
                "x": [2.0, 2.0],
                "y": [0, 2.5],
                "type": "scatter",
                "mode": "lines",
                "name": "FE Critical (T/τ = 2)",
                "line": {"color": self.COLORS["unstable_discrete"], "width": 2, "dash": "dot"},
            })

        # 5. Current operating point
        point_color = self.COLORS["stable_discrete"] if z_magnitude <= 1 else self.COLORS["unstable_discrete"]
        traces.append({
            "x": [t_tau_current],
            "y": [z_magnitude],
            "type": "scatter",
            "mode": "markers",
            "name": f"Current (T/τ = {t_tau_current:.2f})",
            "marker": {
                "symbol": "circle",
                "color": point_color,
                "size": 14,
                "line": {"color": "white", "width": 2},
            },
            "hovertemplate": f"T/τ = {t_tau_current:.3f}<br>|z| = {z_magnitude:.3f}<extra></extra>",
        })

        # Y-axis max
        y_max = min(2.5, float(np.max(self._stability_curve) * 1.1))

        return {
            "id": "stability_map",
            "title": f"Stability Analysis | {method_name}",
            "plotType": "stability",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "T/τ Ratio",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "zeroline": True,
                    "zerolinecolor": "rgba(148, 163, 184, 0.3)",
                    "range": [0, 3],
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "|z| (Pole Magnitude)",
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
                "uirevision": "stability_map",
            },
        }

    def _create_pole_trajectory_plot(self) -> Dict[str, Any]:
        """Create pole movement visualization (matching DC Motor style)."""
        current_pole = self._z_pole
        current_magnitude = abs(current_pole)
        method_name = self.METHOD_EXPLANATIONS[self.parameters["method"]]["name"]

        traces = []

        # 1. Unit circle (stability boundary) - purple like DC Motor imaginary axis
        theta = np.linspace(0, 2 * np.pi, 100)
        unit_x = np.cos(theta)
        unit_y = np.sin(theta)

        traces.append({
            "x": unit_x.tolist(),
            "y": unit_y.tolist(),
            "type": "scatter",
            "fill": "toself",
            "fillcolor": self.COLORS["fill_stable"],
            "line": {"color": self.COLORS["unit_circle"], "width": 2.5},
            "name": "Unit Circle (Stability)",
        })

        # 2. Pole trajectory with color coding
        for i in range(len(self._pole_trajectory) - 1):
            z_current = self._pole_trajectory[i]
            z_next = self._pole_trajectory[i + 1]
            magnitude = abs(z_current)

            if magnitude <= 1.0:
                color = self.COLORS["trajectory_stable"]
                width = 2
            elif magnitude <= 1.5:
                color = self.COLORS["trajectory_marginal"]
                width = 2.5
            else:
                color = self.COLORS["trajectory_unstable"]
                width = 3

            traces.append({
                "x": [float(np.real(z_current)), float(np.real(z_next))],
                "y": [float(np.imag(z_current)), float(np.imag(z_next))],
                "type": "scatter",
                "mode": "lines",
                "line": {"color": color, "width": width},
                "opacity": 0.7,
                "showlegend": False,
                "hoverinfo": "skip",
            })

        # 3. Start point (small T/τ)
        if len(self._pole_trajectory) > 0:
            start_point = self._pole_trajectory[0]
            traces.append({
                "x": [float(np.real(start_point))],
                "y": [float(np.imag(start_point))],
                "type": "scatter",
                "mode": "markers",
                "name": "Start (small T/τ)",
                "marker": {"color": self.COLORS["continuous"], "size": 8, "symbol": "circle", "line": {"color": "white", "width": 1}},
            })

        # 4. End point (large T/τ - if unstable)
        if len(self._pole_trajectory) > 0:
            end_point = self._pole_trajectory[-1]
            if abs(end_point) > 1.5:
                traces.append({
                    "x": [float(np.real(end_point))],
                    "y": [float(np.imag(end_point))],
                    "type": "scatter",
                    "mode": "markers",
                    "name": "End (large T/τ)",
                    "marker": {"color": self.COLORS["unstable_discrete"], "size": 8, "symbol": "circle", "line": {"color": "white", "width": 1}},
                })

        # 5. Current pole position (styled like DC Motor)
        current_color = self.COLORS["stable_discrete"] if current_magnitude <= 1 else self.COLORS["unstable_discrete"]
        traces.append({
            "x": [float(np.real(current_pole))],
            "y": [float(np.imag(current_pole))],
            "type": "scatter",
            "mode": "markers",
            "name": f"Current (|z| = {current_magnitude:.3f})",
            "marker": {
                "symbol": "x",
                "size": 16,
                "color": current_color,
                "line": {"width": 3, "color": current_color},
            },
            "hovertemplate": f"Current Pole<br>Re = {float(np.real(current_pole)):.3f}<br>|z| = {current_magnitude:.3f}<extra></extra>",
        })

        return {
            "id": "pole_trajectory",
            "title": f"Pole Trajectory | {method_name}",
            "plotType": "stability",
            "data": traces,
            "layout": {
                "xaxis": {
                    "title": "Real (Re)",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "zeroline": True,
                    "zerolinecolor": "rgba(0, 0, 0, 0.5)",
                    "zerolinewidth": 1,
                    "range": [-2, 2],
                    "fixedrange": False,
                },
                "yaxis": {
                    "title": "Imaginary (Im)",
                    "showgrid": True,
                    "gridcolor": self.COLORS["grid"],
                    "zeroline": True,
                    "zerolinecolor": "rgba(0, 0, 0, 0.5)",
                    "zerolinewidth": 1,
                    "range": [-2, 2],
                    "scaleanchor": "x",
                    "scaleratio": 1,
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
                "uirevision": "pole_trajectory",
            },
        }

    def get_computed_values(self) -> Dict[str, Any]:
        """Return computed values for display (matching PyQt5 status display)."""
        return {
            "s_pole": self._s_pole,
            "z_pole_real": float(np.real(self._z_pole)),
            "z_pole_imag": float(np.imag(self._z_pole)),
            "z_magnitude": abs(self._z_pole),
            "t_tau_ratio": self.parameters["t_tau_ratio"],
            "T": self._T,
            "tau": self._tau,
            "is_stable": self._is_stable,
            "stability_status": "STABLE" if self._is_stable else "UNSTABLE",
            "rms_error": self._rms_error,
            "performance_rating": self._performance_rating,
            "method": self.parameters["method"],
            "method_info": self.METHOD_EXPLANATIONS.get(self.parameters["method"], {}),
        }

    def get_state(self) -> Dict[str, Any]:
        """Return current simulation state with computed values and metadata."""
        state = super().get_state()
        state["computed_values"] = self.get_computed_values()
        state["guided_scenarios"] = self.GUIDED_SCENARIOS

        # Add metadata with sticky_controls flag
        state["metadata"] = {
            "simulation_type": "ct_dt_poles",
            "sticky_controls": True,  # Keep control panel fixed when scrolling
            "system_info": {
                "method": self.parameters["method"],
                "t_tau_ratio": round(self.parameters["t_tau_ratio"], 3),
                "T": round(self._T, 4),
                "tau": self._tau,
                "s_pole": round(self._s_pole, 3),
                "z_pole_real": round(float(np.real(self._z_pole)), 4),
                "z_pole_imag": round(float(np.imag(self._z_pole)), 4),
                "z_magnitude": round(abs(self._z_pole), 4),
                "is_stable": self._is_stable,
                "rms_error": round(self._rms_error, 4) if self._rms_error != float("inf") else None,
                "performance_rating": self._performance_rating,
            },
        }

        return state
