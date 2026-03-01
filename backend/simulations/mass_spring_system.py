"""
Mass-Spring System Visualizer

Animated mass-spring-damper system showing how physical systems transform
input signals. The input x(t) is a base/ceiling displacement; the output
y(t) is the mass displacement.  Students see both the physical animation
and the time-domain signals evolve together.

Equation of motion (base excitation):
    m * y'' + b * y' + k * y = b * x' + k * x
"""

from typing import Any, Dict, List, Optional, Callable
import numpy as np
from scipy.integrate import solve_ivp

from .base_simulator import BaseSimulator


class MassSpringSimulator(BaseSimulator):
    """
    Mass-spring-damper simulator with animated 2-D visualization.

    Pre-computes the full trajectory via solve_ivp (RK45) and returns
    both Plotly plots and sampled animation data in metadata.
    """

    NUM_POINTS = 2000          # ODE evaluation points
    ANIMATION_SAMPLE_RATE = 4  # every 4th point → ~500 frames

    PARAMETER_SCHEMA = {
        "mass": {
            "type": "slider", "min": 0.1, "max": 5.0, "step": 0.1,
            "default": 1.0, "unit": "kg",
        },
        "spring_constant": {
            "type": "slider", "min": 1.0, "max": 100.0, "step": 1.0,
            "default": 10.0, "unit": "N/m",
        },
        "damping": {
            "type": "slider", "min": 0.0, "max": 10.0, "step": 0.1,
            "default": 0.5, "unit": "Ns/m",
        },
        "input_type": {
            "type": "select",
            "options": [
                {"value": "step", "label": "Step Input"},
                {"value": "sinusoid", "label": "Sinusoidal"},
                {"value": "impulse", "label": "Impulse"},
                {"value": "none", "label": "Free Response"},
            ],
            "default": "step",
        },
        "input_frequency": {
            "type": "slider", "min": 0.1, "max": 10.0, "step": 0.1,
            "default": 1.0, "unit": "Hz",
        },
        "input_amplitude": {
            "type": "slider", "min": 0.1, "max": 2.0, "step": 0.1,
            "default": 1.0, "unit": "m",
        },
        "simulation_time": {
            "type": "slider", "min": 2.0, "max": 20.0, "step": 1.0,
            "default": 10.0, "unit": "s",
        },
    }

    DEFAULT_PARAMS = {
        "mass": 1.0,
        "spring_constant": 10.0,
        "damping": 0.5,
        "input_type": "step",
        "input_frequency": 1.0,
        "input_amplitude": 1.0,
        "simulation_time": 10.0,
    }

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._time: Optional[np.ndarray] = None
        self._x: Optional[np.ndarray] = None       # input signal
        self._y: Optional[np.ndarray] = None       # mass displacement
        self._y_dot: Optional[np.ndarray] = None   # mass velocity
        # derived quantities
        self._omega_n: float = 0.0
        self._f_n: float = 0.0
        self._zeta: float = 0.0
        self._damping_type: str = ""

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = self.DEFAULT_PARAMS.copy()
        if params:
            for name, value in params.items():
                if name in self.PARAMETER_SCHEMA:
                    self.parameters[name] = self._validate_param(name, value)
        self._initialized = True
        self._compute()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
            self._compute()
        return self.get_state()

    # ------------------------------------------------------------------
    # Input signal builders
    # ------------------------------------------------------------------

    @staticmethod
    def _build_input_functions(
        input_type: str, amplitude: float, frequency: float,
    ) -> tuple:
        """Return (x_func, xdot_func) callables for the chosen input."""
        A = amplitude
        eps = 0.005  # smoothing width for step/impulse

        if input_type == "step":
            # Smooth sigmoid step
            def x_func(t: float) -> float:
                return float(A / (1.0 + np.exp(-t / eps)))

            def xdot_func(t: float) -> float:
                s = 1.0 / (1.0 + np.exp(-t / eps))
                return float(A * s * (1.0 - s) / eps)

        elif input_type == "sinusoid":
            omega = 2.0 * np.pi * frequency

            def x_func(t: float) -> float:
                return float(A * np.sin(omega * t))

            def xdot_func(t: float) -> float:
                return float(A * omega * np.cos(omega * t))

        elif input_type == "impulse":
            sigma = 0.02
            # Normalize so the Gaussian area = A (matches unit impulse response)
            scale = A / (sigma * np.sqrt(2.0 * np.pi))

            def x_func(t: float) -> float:
                return float(scale * np.exp(-0.5 * (t / sigma) ** 2))

            def xdot_func(t: float) -> float:
                return float(-t / (sigma ** 2) * scale * np.exp(-0.5 * (t / sigma) ** 2))

        else:  # "none" — free response
            def x_func(t: float) -> float:
                return 0.0

            def xdot_func(t: float) -> float:
                return 0.0

        return x_func, xdot_func

    # ------------------------------------------------------------------
    # Core computation
    # ------------------------------------------------------------------

    def _compute(self) -> None:
        m = float(self.parameters["mass"])
        k = float(self.parameters["spring_constant"])
        b = float(self.parameters["damping"])
        input_type = self.parameters["input_type"]
        freq = float(self.parameters["input_frequency"])
        amp = float(self.parameters["input_amplitude"])
        sim_time = float(self.parameters["simulation_time"])

        # Derived system quantities
        self._omega_n = np.sqrt(k / m)
        self._f_n = self._omega_n / (2.0 * np.pi)
        denom = 2.0 * np.sqrt(k * m)
        self._zeta = b / denom if denom > 0 else 0.0

        if self._zeta < 0.99:
            self._damping_type = "underdamped"
        elif self._zeta <= 1.01:
            self._damping_type = "critically_damped"
        else:
            self._damping_type = "overdamped"

        # Input functions
        x_func, xdot_func = self._build_input_functions(input_type, amp, freq)

        # Initial conditions
        if input_type == "none":
            y0 = [amp, 0.0]  # displaced from rest
        else:
            y0 = [0.0, 0.0]  # at rest

        # ODE: m*y'' + b*y' + k*y = b*x' + k*x
        def ode(t: float, q: np.ndarray) -> list:
            y_val, y_dot_val = q
            y_ddot = (b * xdot_func(t) + k * x_func(t)
                      - b * y_dot_val - k * y_val) / m
            return [y_dot_val, y_ddot]

        t_eval = np.linspace(0.0, sim_time, self.NUM_POINTS)

        sol = solve_ivp(
            ode,
            (0.0, sim_time),
            y0,
            method="RK45",
            t_eval=t_eval,
            rtol=1e-8,
            atol=1e-10,
            max_step=0.01,
        )

        self._time = sol.t
        self._y = sol.y[0]
        self._y_dot = sol.y[1]

        # Vectorised input signal for plotting
        self._x = np.array([x_func(ti) for ti in self._time])

    # ------------------------------------------------------------------
    # Plots
    # ------------------------------------------------------------------

    def get_plots(self) -> List[Dict[str, Any]]:
        if self._time is None:
            self._compute()
        return [
            self._create_response_plot(),
            self._create_phase_portrait(),
            self._create_energy_plot(),
        ]

    def _get_base_layout(self) -> Dict[str, Any]:
        return {
            "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
            "plot_bgcolor": "rgba(0,0,0,0)",
            "paper_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#e2e8f0", "family": "Inter, sans-serif", "size": 12},
        }

    def _create_response_plot(self) -> Dict[str, Any]:
        sim_time = self.parameters["simulation_time"]
        title = "System Response"

        # Auto-range with padding
        all_vals = np.concatenate([self._x, self._y])
        ymin, ymax = float(np.min(all_vals)), float(np.max(all_vals))
        pad = max(0.1, (ymax - ymin) * 0.1)

        data = [
            {
                "x": self._time.tolist(),
                "y": self._x.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Input x(t) \u2014 Base",
                "line": {"color": "#3b82f6", "width": 2.5},
            },
            {
                "x": self._time.tolist(),
                "y": self._y.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Output y(t) \u2014 Mass",
                "line": {"color": "#ef4444", "width": 2.5},
            },
        ]

        layout = {
            **self._get_base_layout(),
            "xaxis": {
                "title": "Time (s)",
                "showgrid": True,
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "range": [0, sim_time],
            },
            "yaxis": {
                "title": "Displacement (m)",
                "showgrid": True,
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "range": [ymin - pad, ymax + pad],
            },
            "legend": {"orientation": "h", "y": 1.12, "x": 0.5, "xanchor": "center"},
            "showlegend": True,
        }

        return {"id": "response", "title": title, "data": data, "layout": layout}

    def _create_phase_portrait(self) -> Dict[str, Any]:
        data = [
            {
                "x": self._y.tolist(),
                "y": self._y_dot.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Trajectory",
                "line": {"color": "#14b8a6", "width": 2},
            },
            {
                "x": [float(self._y[0])],
                "y": [float(self._y_dot[0])],
                "type": "scatter",
                "mode": "markers",
                "name": "Start",
                "marker": {"color": "#10b981", "size": 10, "symbol": "circle"},
            },
            {
                "x": [float(self._y[-1])],
                "y": [float(self._y_dot[-1])],
                "type": "scatter",
                "mode": "markers",
                "name": "End",
                "marker": {"color": "#ef4444", "size": 10, "symbol": "diamond"},
            },
        ]

        layout = {
            **self._get_base_layout(),
            "xaxis": {
                "title": "Displacement y (m)",
                "showgrid": True,
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
            },
            "yaxis": {
                "title": "Velocity y\u2032 (m/s)",
                "showgrid": True,
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
            },
            "legend": {"x": 0.02, "y": 0.98, "xanchor": "left", "yanchor": "top"},
            "showlegend": True,
        }

        return {"id": "phase_portrait", "title": "Phase Portrait", "data": data, "layout": layout}

    def _create_energy_plot(self) -> Dict[str, Any]:
        """Kinetic, potential, dissipated, and total energy over time."""
        m = float(self.parameters["mass"])
        k = float(self.parameters["spring_constant"])
        b = float(self.parameters["damping"])

        ke = 0.5 * m * self._y_dot ** 2
        pe = 0.5 * k * (self._y - self._x) ** 2

        # Dissipated energy: cumulative integral of b*(y' - x')^2 dt
        x_dot = np.gradient(self._x, self._time)
        rel_vel = self._y_dot - x_dot
        dt_arr = np.gradient(self._time)
        dissipated = np.cumsum(b * rel_vel ** 2 * dt_arr)

        total_e = ke + pe + dissipated

        ymax = float(np.max(total_e)) if len(total_e) > 0 else 1.0
        pad = max(0.01, ymax * 0.1)

        data = [
            {
                "x": self._time.tolist(),
                "y": ke.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Kinetic (\u00bdmv\u00b2)",
                "line": {"color": "#3b82f6", "width": 2},
                "fill": "tozeroy",
                "fillcolor": "rgba(59, 130, 246, 0.1)",
            },
            {
                "x": self._time.tolist(),
                "y": pe.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Potential (\u00bdk\u03b4\u00b2)",
                "line": {"color": "#f59e0b", "width": 2},
                "fill": "tozeroy",
                "fillcolor": "rgba(245, 158, 11, 0.1)",
            },
            {
                "x": self._time.tolist(),
                "y": dissipated.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Dissipated (damper)",
                "line": {"color": "#ef4444", "width": 2, "dash": "dash"},
            },
            {
                "x": self._time.tolist(),
                "y": total_e.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "KE + PE + Dissipated",
                "line": {"color": "#10b981", "width": 2.5, "dash": "dot"},
            },
        ]

        layout = {
            **self._get_base_layout(),
            "xaxis": {
                "title": "Time (s)",
                "showgrid": True,
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "range": [0, float(self.parameters["simulation_time"])],
            },
            "yaxis": {
                "title": "Energy (J)",
                "showgrid": True,
                "gridcolor": "rgba(148,163,184,0.1)",
                "zerolinecolor": "rgba(148,163,184,0.3)",
                "range": [0, ymax + pad],
            },
            "legend": {"orientation": "h", "y": 1.12, "x": 0.5, "xanchor": "center"},
            "showlegend": True,
        }

        return {"id": "energy", "title": "Energy Analysis", "data": data, "layout": layout}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _compute_steady_state(self) -> Optional[float]:
        """Return the analytical steady-state value, or None if not applicable."""
        input_type = self.parameters["input_type"]
        if input_type == "step":
            # Step: y_ss = x_ss = amplitude (spring force balances)
            return round(float(self.parameters["input_amplitude"]), 4)
        if input_type in ("none", "impulse"):
            # Free/impulse: system returns to 0
            return 0.0
        # Sinusoidal: no static steady state
        return None

    # ------------------------------------------------------------------
    # State + animation metadata
    # ------------------------------------------------------------------

    def get_state(self) -> Dict[str, Any]:
        if self._time is None:
            self._compute()

        plots = self.get_plots()

        # Subsample trajectory for animation
        s = self.ANIMATION_SAMPLE_RATE
        idx = slice(0, None, s)
        sampled_time = self._time[idx]
        dt = float(sampled_time[1] - sampled_time[0]) if len(sampled_time) > 1 else 0.02

        # Damped frequency / period (only if underdamped)
        f_d = None
        period = None
        if self._zeta < 1.0:
            omega_d = self._omega_n * np.sqrt(1.0 - self._zeta ** 2)
            period = round(2.0 * np.pi / omega_d, 4) if omega_d > 0 else None
            f_d = round(omega_d / (2.0 * np.pi), 4)  # Hz

        return {
            "parameters": self.parameters.copy(),
            "plots": plots,
            "metadata": {
                "simulation_type": "mass_spring_system",
                "visualization_2d": {
                    "time": sampled_time.tolist(),
                    "input_position": self._x[idx].tolist(),
                    "mass_position": self._y[idx].tolist(),
                    "velocity": self._y_dot[idx].tolist(),
                    "dt": dt,
                    "total_time": float(self.parameters["simulation_time"]),
                    "num_frames": len(sampled_time),
                },
                "system_info": {
                    "natural_frequency_hz": round(self._f_n, 4),
                    "natural_frequency_rad": round(self._omega_n, 4),
                    "damping_ratio": round(self._zeta, 4),
                    "damping_type": self._damping_type,
                    "damped_frequency_hz": f_d,
                    "period": period,
                    "input_type": self.parameters["input_type"],
                    "peak_output": round(float(np.max(np.abs(self._y))), 4),
                    "steady_state": self._compute_steady_state(),
                },
            },
        }
