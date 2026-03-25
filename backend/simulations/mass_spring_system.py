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
from core.controllers import (
    numerical_jacobian, controllability_matrix,
    compute_lqr, compute_pole_placement, compute_lqg,
    simulate_pid, simulate_state_feedback, simulate_lqg,
    simulate_uncontrolled,
    compute_performance_metrics, compute_energy,
)


class MassSpringSimulator(BaseSimulator):
    """
    Mass-spring-damper simulator with animated 2-D visualization.

    Pre-computes the full trajectory via solve_ivp (RK45) and returns
    both Plotly plots and sampled animation data in metadata.
    """

    NUM_POINTS = 2000          # ODE evaluation points
    ANIMATION_SAMPLE_RATE = 4  # every 4th point → ~500 frames

    FORCE_LIMIT = 50.0  # Max control force (N)

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
        "controller": {
            "type": "select",
            "options": [
                {"value": "none", "label": "No Control (Passive)"},
                {"value": "pid", "label": "PID"},
                {"value": "lqr", "label": "LQR (Optimal)"},
                {"value": "pole_placement", "label": "Pole Placement"},
                {"value": "lqg", "label": "LQG (Observer)"},
            ],
            "default": "none",
        },
        # PID gains
        "pid_Kp": {
            "type": "slider", "min": 0, "max": 200, "step": 1, "default": 50,
            "visible_when": {"controller": "pid"},
        },
        "pid_Ki": {
            "type": "slider", "min": 0, "max": 50, "step": 0.5, "default": 10,
            "visible_when": {"controller": "pid"},
        },
        "pid_Kd": {
            "type": "slider", "min": 0, "max": 50, "step": 0.5, "default": 15,
            "visible_when": {"controller": "pid"},
        },
        # LQR weights
        "lqr_q_y": {
            "type": "slider", "min": 0.1, "max": 100, "step": 0.1, "default": 10.0,
            "visible_when": {"controller": "lqr"},
        },
        "lqr_q_ydot": {
            "type": "slider", "min": 0.1, "max": 100, "step": 0.1, "default": 1.0,
            "visible_when": {"controller": "lqr"},
        },
        "lqr_r": {
            "type": "slider", "min": 0.01, "max": 10, "step": 0.01, "default": 0.1,
            "visible_when": {"controller": "lqr"},
        },
        # Pole placement
        "pp_real": {
            "type": "slider", "min": -20, "max": -0.5, "step": 0.1, "default": -5.0,
            "visible_when": {"controller": "pole_placement"},
        },
        "pp_spread": {
            "type": "slider", "min": 1.0, "max": 3.0, "step": 0.1, "default": 1.5,
            "visible_when": {"controller": "pole_placement"},
        },
        # LQG
        "lqg_q_y": {
            "type": "slider", "min": 0.1, "max": 100, "step": 0.1, "default": 10.0,
            "visible_when": {"controller": "lqg"},
        },
        "lqg_q_ydot": {
            "type": "slider", "min": 0.1, "max": 100, "step": 0.1, "default": 1.0,
            "visible_when": {"controller": "lqg"},
        },
        "lqg_r": {
            "type": "slider", "min": 0.01, "max": 10, "step": 0.01, "default": 0.1,
            "visible_when": {"controller": "lqg"},
        },
        "lqg_process_noise": {
            "type": "slider", "min": 0.001, "max": 1.0, "step": 0.001, "default": 0.01,
            "visible_when": {"controller": "lqg"},
        },
        "lqg_sensor_noise": {
            "type": "slider", "min": 0.001, "max": 1.0, "step": 0.001, "default": 0.01,
            "visible_when": {"controller": "lqg"},
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
        "controller": "none",
        "pid_Kp": 50, "pid_Ki": 10, "pid_Kd": 15,
        "lqr_q_y": 10.0, "lqr_q_ydot": 1.0, "lqr_r": 0.1,
        "pp_real": -5.0, "pp_spread": 1.5,
        "lqg_q_y": 10.0, "lqg_q_ydot": 1.0, "lqg_r": 0.1,
        "lqg_process_noise": 0.01, "lqg_sensor_noise": 0.01,
    }

    HUB_SLOTS = ['control']

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._time: Optional[np.ndarray] = None
        self._x: Optional[np.ndarray] = None       # input/reference signal
        self._y: Optional[np.ndarray] = None       # mass displacement
        self._y_dot: Optional[np.ndarray] = None   # mass velocity
        self._force: Optional[np.ndarray] = None   # control force (active controllers only)
        # derived quantities
        self._omega_n: float = 0.0
        self._f_n: float = 0.0
        self._zeta: float = 0.0
        self._damping_type: str = ""
        self._controller_info: Dict[str, Any] = {"type": "none"}

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

    def _dynamics_wrapper(self, x: np.ndarray, u: np.ndarray) -> np.ndarray:
        """Force-control model: m*y'' = -k*y - b*y' + F."""
        m = float(self.parameters["mass"])
        k = float(self.parameters["spring_constant"])
        b = float(self.parameters["damping"])
        y, yd = x
        F = u[0] if len(u) > 0 else 0.0
        ydd = (-k * y - b * yd + F) / m
        return np.array([yd, ydd])

    def _compute(self) -> None:
        """Simulate system with selected controller."""
        m = float(self.parameters["mass"])
        k = float(self.parameters["spring_constant"])
        b = float(self.parameters["damping"])
        input_type = self.parameters["input_type"]
        freq = float(self.parameters["input_frequency"])
        amp = float(self.parameters["input_amplitude"])
        sim_time = float(self.parameters["simulation_time"])
        ctrl = self.parameters.get("controller", "none")

        # Derived system quantities (always compute)
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

        self._controller_info = {"type": ctrl}
        self._force = None

        if ctrl != "none":
            try:
                self._run_controlled(ctrl, m, k, b, input_type, freq, amp, sim_time)
                return
            except Exception as e:
                self._controller_info["error"] = str(e)
                # Fall through to passive

        # Passive base-excitation model (original behavior)
        x_func, xdot_func = self._build_input_functions(input_type, amp, freq)

        if input_type == "none":
            y0 = [amp, 0.0]
        else:
            y0 = [0.0, 0.0]

        def ode(t: float, q: np.ndarray) -> list:
            y_val, y_dot_val = q
            y_ddot = (b * xdot_func(t) + k * x_func(t)
                      - b * y_dot_val - k * y_val) / m
            return [y_dot_val, y_ddot]

        t_eval = np.linspace(0.0, sim_time, self.NUM_POINTS)
        sol = solve_ivp(ode, (0.0, sim_time), y0, method="RK45",
                        t_eval=t_eval, rtol=1e-8, atol=1e-10, max_step=0.01)

        self._time = sol.t
        self._y = sol.y[0]
        self._y_dot = sol.y[1]
        self._x = np.array([x_func(ti) for ti in self._time])

    def _run_controlled(self, ctrl: str, m: float, k: float, b: float,
                        input_type: str, freq: float, amp: float,
                        sim_time: float) -> None:
        """Active force-control: controller applies force to track reference."""
        # System matrices for gain computation
        A = np.array([[0.0, 1.0], [-k / m, -b / m]])
        B = np.array([[0.0], [1.0 / m]])
        n = 2

        Wc = controllability_matrix(A, B)
        ctrl_rank = int(np.linalg.matrix_rank(Wc))
        self._controller_info["controllability_rank"] = ctrl_rank
        self._controller_info["is_controllable"] = ctrl_rank == n
        self._controller_info["ol_eigenvalues"] = np.linalg.eigvals(A).tolist()

        # Reference: step → track amplitude; free → regulate from displaced IC to 0
        if input_type == "step":
            x_ref = amp
            x0 = np.array([0.0, 0.0])
        elif input_type == "none":
            x_ref = 0.0
            x0 = np.array([amp, 0.0])
        elif input_type == "impulse":
            # Impulse disturbance rejection: regulate to 0 after kick
            x_ref = 0.0
            x0 = np.array([amp * 0.5, 0.0])  # approximate impulse as displaced IC
        else:
            # Sinusoidal: regulate to 0 (controller fights the oscillation)
            x_ref = 0.0
            x0 = np.array([0.0, 0.0])

        x_eq = np.array([x_ref, 0.0])
        u_eq = np.array([k * x_ref])  # feedforward: spring force at equilibrium
        t_span = (0.0, sim_time)
        dt = sim_time / self.NUM_POINTS

        p = self.parameters

        if ctrl == "pid":
            gains = {"Kp": p["pid_Kp"], "Ki": p["pid_Ki"], "Kd": p["pid_Kd"], "N": 20.0}
            result = simulate_pid(
                self._dynamics_wrapper, x0, t_span, gains,
                output_index=0, x_ref=x_ref, n_inputs=1,
                u_max=self.FORCE_LIMIT, dt=dt)
        elif ctrl == "lqr":
            Q = np.diag([p["lqr_q_y"], p["lqr_q_ydot"]])
            R = np.array([[p["lqr_r"]]])
            K, _, cl_eigs = compute_lqr(A, B, Q, R)
            self._controller_info["K"] = K.tolist()
            self._controller_info["cl_eigenvalues"] = cl_eigs.tolist()
            result = simulate_state_feedback(
                self._dynamics_wrapper, x0, t_span, K, x_eq, u_eq,
                u_max=self.FORCE_LIMIT, dt=dt)
        elif ctrl == "pole_placement":
            s = p["pp_real"]
            spread = p["pp_spread"]
            poles = np.array([s, s * spread])
            K, cl_eigs = compute_pole_placement(A, B, poles)
            self._controller_info["K"] = K.tolist()
            self._controller_info["cl_eigenvalues"] = cl_eigs.tolist()
            self._controller_info["desired_poles"] = poles.tolist()
            result = simulate_state_feedback(
                self._dynamics_wrapper, x0, t_span, K, x_eq, u_eq,
                u_max=self.FORCE_LIMIT, dt=dt)
        elif ctrl == "lqg":
            C = np.eye(n)
            Q_lqr = np.diag([p["lqg_q_y"], p["lqg_q_ydot"]])
            R_lqr = np.array([[p["lqg_r"]]])
            Q_kalman = p["lqg_process_noise"] * np.eye(n)
            R_kalman = p["lqg_sensor_noise"] * np.eye(n)
            K, L, _, _ = compute_lqg(A, B, C, Q_lqr, R_lqr, Q_kalman, R_kalman)
            self._controller_info["K"] = K.tolist()
            self._controller_info["L"] = L.tolist()
            self._controller_info["cl_eigenvalues"] = np.linalg.eigvals(A - B @ K).tolist()
            self._controller_info["est_eigenvalues"] = np.linalg.eigvals(A - L @ C).tolist()
            result = simulate_lqg(
                self._dynamics_wrapper, x0, t_span, K, L, A, B, C, x_eq, u_eq,
                u_max=self.FORCE_LIMIT, dt=dt)

        # Store results
        self._time = result["t"]
        self._y = result["x"][:, 0]
        self._y_dot = result["x"][:, 1]
        self._force = result["u"][:, 0]

        # Build reference signal for plotting
        self._x = np.full_like(self._time, x_ref)
        if input_type == "none":
            self._x = np.zeros_like(self._time)  # target is origin

    # ------------------------------------------------------------------
    # Plots
    # ------------------------------------------------------------------

    def get_plots(self) -> List[Dict[str, Any]]:
        if self._time is None:
            self._compute()
        plots = [
            self._create_response_plot(),
            self._create_phase_portrait(),
            self._create_energy_plot(),
        ]
        if self._force is not None:
            plots.append(self._create_force_plot())
        return plots

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

    def _create_force_plot(self) -> Dict[str, Any]:
        """Control force vs time (only shown when a controller is active)."""
        peak = float(np.max(np.abs(self._force)))
        sim_time = float(self.parameters["simulation_time"])
        y_max = max(peak * 1.2, 1.0)

        data = [
            {
                "x": self._time.tolist(),
                "y": self._force.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "F (control)",
                "line": {"color": "#f472b6", "width": 2.5},
            },
            {
                "x": [0, sim_time],
                "y": [0, 0],
                "type": "scatter",
                "mode": "lines",
                "name": "Zero",
                "line": {"color": "#34d399", "width": 1.5, "dash": "dash"},
                "hoverinfo": "skip",
            },
        ]

        layout = {
            **self._get_base_layout(),
            "xaxis": {
                "title": "Time (s)", "range": [0, sim_time],
                "showgrid": True, "gridcolor": "rgba(148,163,184,0.1)",
            },
            "yaxis": {
                "title": "Force (N)", "range": [-y_max, y_max],
                "showgrid": True, "gridcolor": "rgba(148,163,184,0.1)",
            },
            "legend": {"orientation": "h", "y": 1.12, "x": 0.5, "xanchor": "center"},
            "showlegend": True,
        }

        return {"id": "control_force", "title": f"Control Force (Peak: {peak:.1f} N)",
                "data": data, "layout": layout}

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

        # Control force for animation (if active controller)
        force_data = self._force[idx].tolist() if self._force is not None else None

        return {
            "parameters": self.parameters.copy(),
            "plots": plots,
            "metadata": {
                "simulation_type": "mass_spring_system",
                "hub_slots": self.HUB_SLOTS,
                "hub_domain": self.HUB_DOMAIN,
                "hub_dimensions": self.HUB_DIMENSIONS,
                "controller_info": self._controller_info,
                "visualization_2d": {
                    "time": sampled_time.tolist(),
                    "input_position": self._x[idx].tolist(),
                    "mass_position": self._y[idx].tolist(),
                    "velocity": self._y_dot[idx].tolist(),
                    "force": force_data,
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
