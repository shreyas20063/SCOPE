"""Inverted Pendulum on Cart — 3D Physics Lab simulation.

Full nonlinear dynamics with swappable controllers (None, PID, LQR,
Pole Placement, LQG). Server-side RK45 integration for textbook accuracy.
Frontend receives trajectory arrays for Three.js 3D animation + Plotly plots.

Physics (Lagrangian-derived):
    State: [x, ẋ, θ, θ̇] where θ measured from downward vertical (π = upright)
    (M+m)ẍ + ml(θ̈ cosθ − θ̇² sinθ) = F
    l θ̈ + ẍ cosθ − g sinθ = 0

References: Ogata Ch 12, Khalil Ch 12.4, Åström & Murray Ch 3.
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple

from .base_simulator import BaseSimulator
from core.controllers import (
    numerical_jacobian, controllability_matrix, observability_matrix,
    compute_lqr, compute_pole_placement, compute_lqg, compute_pid_gains,
    simulate_uncontrolled, simulate_pid, simulate_state_feedback,
    simulate_lqg, compute_performance_metrics, compute_energy,
    ss2tf_siso, auto_tune_zn_closed, auto_tune_itae, auto_tune_lqr_itae,
)


class InvertedPendulum3DSimulator(BaseSimulator):
    """Inverted pendulum on cart with 3D visualization and swappable controllers."""

    # Physics constants
    G = 9.81

    # Simulation config
    SIM_TIME = 10.0
    DT = 0.01

    # Plot colors
    COLORS = {
        "cart_pos": "#3b82f6",
        "cart_vel": "#60a5fa",
        "angle": "#22d3ee",
        "ang_vel": "#67e8f9",
        "control": "#f472b6",
        "reference": "#34d399",
        "estimate": "#a855f7",
        "stable": "#10b981",
        "unstable": "#ef4444",
        "grid": "rgba(148, 163, 184, 0.1)",
        "zeroline": "rgba(148, 163, 184, 0.3)",
    }

    PARAMETER_SCHEMA = {
        # --- Plant ---
        "cart_mass": {
            "type": "slider", "min": 0.5, "max": 5.0, "step": 0.1,
            "default": 1.0, "unit": "kg", "label": "Cart Mass M",
            "group": "Plant",
        },
        "pend_mass": {
            "type": "slider", "min": 0.05, "max": 1.0, "step": 0.05,
            "default": 0.2, "unit": "kg", "label": "Pendulum Mass m",
            "group": "Plant",
        },
        "pend_length": {
            "type": "slider", "min": 0.2, "max": 1.5, "step": 0.1,
            "default": 0.5, "unit": "m", "label": "Pendulum Length l",
            "group": "Plant",
        },
        "initial_angle": {
            "type": "slider", "min": -30, "max": 30, "step": 1,
            "default": 10, "unit": "deg", "label": "Initial Angle from Upright",
            "group": "Plant",
        },
        # --- Controller Selection ---
        "controller": {
            "type": "select",
            "options": [
                {"value": "none", "label": "No Control"},
                {"value": "pid", "label": "PID"},
                {"value": "zn_closed", "label": "Auto-Tune (Fast)"},
                {"value": "itae_optimal", "label": "Auto-Tune (ITAE)"},
                {"value": "lqr", "label": "LQR (Optimal)"},
                {"value": "pole_placement", "label": "Pole Placement"},
                {"value": "lqg", "label": "LQG (Observer)"},
            ],
            "default": "lqr", "label": "Controller", "group": "Controller",
        },
        # --- PID gains ---
        "pid_Kp": {
            "type": "slider", "min": 0, "max": 200, "step": 1,
            "default": 100, "label": "Kp", "group": "PID Gains",
            "visible_when": {"controller": "pid"},
        },
        "pid_Ki": {
            "type": "slider", "min": 0, "max": 50, "step": 0.5,
            "default": 10, "label": "Ki", "group": "PID Gains",
            "visible_when": {"controller": "pid"},
        },
        "pid_Kd": {
            "type": "slider", "min": 0, "max": 50, "step": 0.5,
            "default": 20, "label": "Kd", "group": "PID Gains",
            "visible_when": {"controller": "pid"},
        },
        # --- LQR weights ---
        "lqr_q_x": {
            "type": "slider", "min": 0.1, "max": 100, "step": 0.1,
            "default": 1.0, "label": "Q₁₁ (cart pos weight)", "group": "LQR Weights",
            "visible_when": {"controller": "lqr"},
        },
        "lqr_q_theta": {
            "type": "slider", "min": 0.1, "max": 100, "step": 0.1,
            "default": 10.0, "label": "Q₃₃ (angle weight)", "group": "LQR Weights",
            "visible_when": {"controller": "lqr"},
        },
        "lqr_r": {
            "type": "slider", "min": 0.01, "max": 10, "step": 0.01,
            "default": 0.1, "label": "R (effort cost)", "group": "LQR Weights",
            "visible_when": {"controller": "lqr"},
        },
        # --- Pole Placement ---
        "pp_real": {
            "type": "slider", "min": -10, "max": -0.5, "step": 0.1,
            "default": -3.0, "label": "Dominant pole real part", "group": "Pole Placement",
            "visible_when": {"controller": "pole_placement"},
        },
        "pp_spread": {
            "type": "slider", "min": 1.0, "max": 3.0, "step": 0.1,
            "default": 1.5, "label": "Pole spread factor", "group": "Pole Placement",
            "visible_when": {"controller": "pole_placement"},
        },
        # --- LQG noise ---
        "lqg_q_x": {
            "type": "slider", "min": 0.1, "max": 100, "step": 0.1,
            "default": 1.0, "label": "Q₁₁ (cart pos weight)", "group": "LQG Design",
            "visible_when": {"controller": "lqg"},
        },
        "lqg_q_theta": {
            "type": "slider", "min": 0.1, "max": 100, "step": 0.1,
            "default": 10.0, "label": "Q₃₃ (angle weight)", "group": "LQG Design",
            "visible_when": {"controller": "lqg"},
        },
        "lqg_r": {
            "type": "slider", "min": 0.01, "max": 10, "step": 0.01,
            "default": 0.1, "label": "R (effort cost)", "group": "LQG Design",
            "visible_when": {"controller": "lqg"},
        },
        "lqg_process_noise": {
            "type": "slider", "min": 0.001, "max": 1.0, "step": 0.001,
            "default": 0.01, "label": "Process noise σ²", "group": "LQG Design",
            "visible_when": {"controller": "lqg"},
        },
        "lqg_sensor_noise": {
            "type": "slider", "min": 0.001, "max": 1.0, "step": 0.001,
            "default": 0.01, "label": "Sensor noise σ²", "group": "LQG Design",
            "visible_when": {"controller": "lqg"},
        },
    }

    DEFAULT_PARAMS = {
        "cart_mass": 1.0,
        "pend_mass": 0.2,
        "pend_length": 0.5,
        "initial_angle": 10,
        "controller": "lqr",
        "pid_Kp": 100, "pid_Ki": 10, "pid_Kd": 20,
        "lqr_q_x": 1.0, "lqr_q_theta": 10.0, "lqr_r": 0.1,
        "pp_real": -3.0, "pp_spread": 1.5,
        "lqg_q_x": 1.0, "lqg_q_theta": 10.0, "lqg_r": 0.1,
        "lqg_process_noise": 0.01, "lqg_sensor_noise": 0.01,
    }


    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._result: Optional[Dict] = None

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
            if name in self.PARAMETER_SCHEMA:
                value = self._validate_param(name, value)
            self.parameters[name] = value
        self._compute()
        return self.get_state()

    # ------------------------------------------------------------------ #
    #  Physics                                                            #
    # ------------------------------------------------------------------ #

    def _dynamics(self, x: np.ndarray, u: np.ndarray) -> np.ndarray:
        """Full nonlinear equations of motion.

        State: [x_cart, x_dot, theta, theta_dot]
        θ measured from downward vertical: θ=π is upright.
        """
        M = self.parameters["cart_mass"]
        m = self.parameters["pend_mass"]
        l = self.parameters["pend_length"]
        g = self.G

        _, x_dot, theta, theta_dot = x
        F = u[0] if len(u) > 0 else 0.0

        sin_t = np.sin(theta)
        cos_t = np.cos(theta)
        denom = M + m * sin_t**2

        x_ddot = (F + m * sin_t * (l * theta_dot**2 + g * cos_t)) / denom
        theta_ddot = (-F * cos_t - m * l * theta_dot**2 * sin_t * cos_t
                      - (M + m) * g * sin_t) / (l * denom)

        return np.array([x_dot, x_ddot, theta_dot, theta_ddot])

    # ------------------------------------------------------------------ #
    #  Main computation                                                   #
    # ------------------------------------------------------------------ #

    def _compute(self) -> None:
        """Run simulation with selected controller."""
        p = self.parameters
        ctrl = p["controller"]

        # Equilibrium: upright (θ = π)
        x_eq = np.array([0.0, 0.0, np.pi, 0.0])
        u_eq = np.array([0.0])

        # Initial condition: small perturbation from upright
        angle_deg = p["initial_angle"]
        x0 = np.array([0.0, 0.0, np.pi + np.radians(angle_deg), 0.0])

        t_span = (0.0, self.SIM_TIME)

        # Linearize at upright equilibrium
        A, B = numerical_jacobian(self._dynamics, x_eq, u_eq)
        n = 4
        C = np.eye(n)  # full state output for LQG

        # Controllability check
        Wc = controllability_matrix(A, B)
        ctrl_rank = int(np.linalg.matrix_rank(Wc))
        is_controllable = ctrl_rank == n

        controller_info = {
            "type": ctrl,
            "A": A.tolist(),
            "B": B.tolist(),
            "controllability_rank": ctrl_rank,
            "is_controllable": is_controllable,
            "ol_eigenvalues": np.linalg.eigvals(A).tolist(),
        }

        try:
            if ctrl == "none":
                result = simulate_uncontrolled(
                    self._dynamics, x0, t_span, n_inputs=1, dt=self.DT)
                controller_info["K"] = None

            elif ctrl == "pid":
                gains = compute_pid_gains(p["pid_Kp"], p["pid_Ki"], p["pid_Kd"])
                result = simulate_pid(
                    self._dynamics, x0, t_span, gains,
                    output_index=2, x_ref=np.pi,  # track θ = π (upright)
                    n_inputs=1, u_max=200.0, dt=self.DT)
                controller_info["gains"] = gains

            elif ctrl == "lqr":
                Q = np.diag([p["lqr_q_x"], 1.0, p["lqr_q_theta"], 1.0])
                R = np.array([[p["lqr_r"]]])
                K, P, cl_eigs = compute_lqr(A, B, Q, R)
                result = simulate_state_feedback(
                    self._dynamics, x0, t_span, K, x_eq, u_eq,
                    u_max=200.0, dt=self.DT)
                controller_info["K"] = K.tolist()
                controller_info["cl_eigenvalues"] = cl_eigs.tolist()
                controller_info["Q"] = Q.tolist()
                controller_info["R"] = R.tolist()

            elif ctrl == "pole_placement":
                s = p["pp_real"]
                spread = p["pp_spread"]
                poles = np.array([s, s * spread, s * spread**2, s * spread**3])
                K, cl_eigs = compute_pole_placement(A, B, poles)
                result = simulate_state_feedback(
                    self._dynamics, x0, t_span, K, x_eq, u_eq,
                    u_max=200.0, dt=self.DT)
                controller_info["K"] = K.tolist()
                controller_info["cl_eigenvalues"] = cl_eigs.tolist()
                controller_info["desired_poles"] = poles.tolist()

            elif ctrl in ("zn_closed", "itae_optimal"):
                # Auto-tune: optimize LQR Q/R weights to minimize ITAE
                tuned = auto_tune_lqr_itae(
                    self._dynamics, x0, A, B, x_eq, u_eq,
                    output_index=2, x_ref=np.pi,
                    u_max=200.0, duration=5.0, dt=self.DT)
                if tuned is not None:
                    K_auto, q_diag, r_val = tuned
                    result = simulate_state_feedback(
                        self._dynamics, x0, t_span, K_auto, x_eq, u_eq,
                        u_max=200.0, dt=self.DT)
                    controller_info["K"] = K_auto.tolist()
                    controller_info["cl_eigenvalues"] = np.linalg.eigvals(
                        A - B @ K_auto).tolist()
                    controller_info["Q"] = np.diag(q_diag).tolist()
                    controller_info["R"] = [[r_val]]
                else:
                    # Fallback to default LQR
                    Q = np.diag([1.0, 1.0, 10.0, 1.0])
                    R = np.array([[0.1]])
                    K_auto, _, cl_eigs = compute_lqr(A, B, Q, R)
                    result = simulate_state_feedback(
                        self._dynamics, x0, t_span, K_auto, x_eq, u_eq,
                        u_max=200.0, dt=self.DT)
                    controller_info["K"] = K_auto.tolist()
                    controller_info["cl_eigenvalues"] = cl_eigs.tolist()
                    controller_info["auto_tune_fallback"] = True
                controller_info["auto_tune_method"] = ctrl

            elif ctrl == "lqg":
                Q_lqr = np.diag([p["lqg_q_x"], 1.0, p["lqg_q_theta"], 1.0])
                R_lqr = np.array([[p["lqg_r"]]])
                Q_kalman = p["lqg_process_noise"] * np.eye(n)
                R_kalman = p["lqg_sensor_noise"] * np.eye(n)

                K, L, P_ctrl, P_est = compute_lqg(
                    A, B, C, Q_lqr, R_lqr, Q_kalman, R_kalman)
                result = simulate_lqg(
                    self._dynamics, x0, t_span, K, L, A, B, C,
                    x_eq, u_eq, u_max=200.0, dt=self.DT)
                controller_info["K"] = K.tolist()
                controller_info["L"] = L.tolist()
                cl_A = np.block([
                    [A - B @ K, B @ K],
                    [L @ C, A - B @ K - L @ C],
                ])
                controller_info["cl_eigenvalues"] = np.linalg.eigvals(
                    A - B @ K).tolist()
                controller_info["est_eigenvalues"] = np.linalg.eigvals(
                    A - L @ C).tolist()

            else:
                result = simulate_uncontrolled(
                    self._dynamics, x0, t_span, n_inputs=1, dt=self.DT)

        except Exception as e:
            # Fallback to uncontrolled on any numerical failure
            result = simulate_uncontrolled(
                self._dynamics, x0, t_span, n_inputs=1, dt=self.DT)
            controller_info["error"] = str(e)

        # Check stability: did θ converge near π (upright)?
        theta_traj = result["x"][:, 2]
        final_err = abs(theta_traj[-1] - np.pi)
        tail = max(1, len(theta_traj) // 5)  # last 20%
        tail_err = np.abs(theta_traj[-tail:] - np.pi)
        tail_std = float(np.std(tail_err))
        # Must converge within 5.7° AND not oscillate AND never fall past 90°
        is_stable = (final_err < 0.1
                     and tail_std < 0.05
                     and np.all(np.abs(theta_traj - np.pi) < np.pi / 2))

        # Performance metrics (angle tracking π)
        metrics = compute_performance_metrics(
            result["t"], result["x"], state_index=2, x_ref=np.pi)
        metrics["control_energy"] = compute_energy(result["u"], result["t"])
        metrics["is_stable"] = is_stable

        # Subsample for 3D animation (every 2nd point → 50fps feel)
        skip = 2
        t_anim = result["t"][::skip]
        x_anim = result["x"][::skip]
        u_anim = result["u"][::skip]

        self._result = {
            "sim": result,
            "controller_info": controller_info,
            "metrics": metrics,
            "animation": {
                "t": t_anim.tolist(),
                "cart_x": x_anim[:, 0].tolist(),
                "theta": x_anim[:, 2].tolist(),
                "control_force": u_anim[:, 0].tolist(),
                "dt": self.DT * skip,
                "num_frames": len(t_anim),
                "pend_length": self.parameters["pend_length"],
                "is_stable": is_stable,
            },
        }
        if ctrl == "lqg" and "x_hat" in result:
            x_hat_anim = result["x_hat"][::skip]
            self._result["animation"]["x_hat"] = x_hat_anim.tolist()

    # ------------------------------------------------------------------ #
    #  Plots                                                              #
    # ------------------------------------------------------------------ #

    def get_plots(self) -> List[Dict[str, Any]]:
        if not self._result:
            return []

        r = self._result["sim"]
        t = r["t"]
        x = r["x"]
        u = r["u"]
        ctrl = self.parameters["controller"]
        C = self.COLORS

        layout_base = {
            "paper_bgcolor": "#0a0e27",
            "plot_bgcolor": "#131b2e",
            "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
            "xaxis": {"gridcolor": C["grid"], "zerolinecolor": C["zeroline"]},
            "yaxis": {"gridcolor": C["grid"], "zerolinecolor": C["zeroline"]},
            "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
            "legend": {"bgcolor": "rgba(15, 23, 42, 0.8)",
                       "bordercolor": "rgba(148, 163, 184, 0.2)"},
        }

        plots = []

        # 1. Pendulum angle
        theta_deg = np.degrees(x[:, 2] - np.pi)  # deviation from upright
        angle_plot = {
            "id": "angle",
            "title": "Pendulum Angle (from upright)",
            "data": [
                {
                    "x": t.tolist(), "y": theta_deg.tolist(),
                    "type": "scatter", "mode": "lines",
                    "name": "θ − π", "line": {"color": C["angle"], "width": 2},
                },
                {
                    "x": [t[0], t[-1]], "y": [0, 0],
                    "type": "scatter", "mode": "lines",
                    "name": "Target", "line": {"color": C["reference"],
                                                "width": 1, "dash": "dash"},
                },
            ],
            "layout": {
                **layout_base,
                "yaxis": {**layout_base["yaxis"], "title": "Angle (deg)"},
                "xaxis": {**layout_base["xaxis"], "title": "Time (s)"},
                "datarevision": f"angle-{id(self._result)}",
                "uirevision": "angle",
            },
        }
        plots.append(angle_plot)

        # 2. Cart position
        cart_plot = {
            "id": "cart_pos",
            "title": "Cart Position",
            "data": [
                {
                    "x": t.tolist(), "y": x[:, 0].tolist(),
                    "type": "scatter", "mode": "lines",
                    "name": "x(t)", "line": {"color": C["cart_pos"], "width": 2},
                },
            ],
            "layout": {
                **layout_base,
                "yaxis": {**layout_base["yaxis"], "title": "Position (m)"},
                "xaxis": {**layout_base["xaxis"], "title": "Time (s)"},
                "datarevision": f"cart-{id(self._result)}",
                "uirevision": "cart_pos",
            },
        }
        plots.append(cart_plot)

        # 3. Control effort
        ctrl_plot = {
            "id": "control",
            "title": "Control Force",
            "data": [
                {
                    "x": t.tolist(), "y": u[:, 0].tolist(),
                    "type": "scatter", "mode": "lines",
                    "name": "F(t)", "line": {"color": C["control"], "width": 2},
                },
            ],
            "layout": {
                **layout_base,
                "yaxis": {**layout_base["yaxis"], "title": "Force (N)"},
                "xaxis": {**layout_base["xaxis"], "title": "Time (s)"},
                "datarevision": f"ctrl-{id(self._result)}",
                "uirevision": "control",
            },
        }
        plots.append(ctrl_plot)

        # 4. Phase portrait (θ vs θ̇)
        phase_plot = {
            "id": "phase",
            "title": "Phase Portrait (θ, θ̇)",
            "data": [
                {
                    "x": theta_deg.tolist(),
                    "y": np.degrees(x[:, 3]).tolist(),
                    "type": "scatter", "mode": "lines",
                    "name": "Trajectory",
                    "line": {"color": C["angle"], "width": 2},
                },
                {
                    "x": [0], "y": [0],
                    "type": "scatter", "mode": "markers",
                    "name": "Equilibrium",
                    "marker": {"color": C["stable"], "size": 10, "symbol": "x"},
                },
            ],
            "layout": {
                **layout_base,
                "xaxis": {**layout_base["xaxis"], "title": "θ (deg from upright)"},
                "yaxis": {**layout_base["yaxis"], "title": "θ̇ (deg/s)"},
                "datarevision": f"phase-{id(self._result)}",
                "uirevision": "phase",
            },
        }
        plots.append(phase_plot)

        # 5. Pole-zero map (if controller provides eigenvalues)
        ci = self._result["controller_info"]
        ol_eigs = np.array(ci["ol_eigenvalues"])
        pz_data = [
            {
                "x": ol_eigs.real.tolist(), "y": ol_eigs.imag.tolist(),
                "type": "scatter", "mode": "markers",
                "name": "Open-loop",
                "marker": {"color": C["unstable"], "size": 10, "symbol": "x"},
            },
        ]
        if "cl_eigenvalues" in ci and ci["cl_eigenvalues"]:
            cl_eigs = np.array(ci["cl_eigenvalues"])
            pz_data.append({
                "x": cl_eigs.real.tolist(), "y": cl_eigs.imag.tolist(),
                "type": "scatter", "mode": "markers",
                "name": "Closed-loop",
                "marker": {"color": C["stable"], "size": 10, "symbol": "circle"},
            })
        if "est_eigenvalues" in ci and ci["est_eigenvalues"]:
            est_eigs = np.array(ci["est_eigenvalues"])
            pz_data.append({
                "x": est_eigs.real.tolist(), "y": est_eigs.imag.tolist(),
                "type": "scatter", "mode": "markers",
                "name": "Estimator",
                "marker": {"color": C["estimate"], "size": 10,
                           "symbol": "diamond"},
            })

        pz_plot = {
            "id": "poles",
            "title": "Pole Map",
            "data": pz_data,
            "layout": {
                **layout_base,
                "xaxis": {**layout_base["xaxis"], "title": "Real",
                          "scaleanchor": "y"},
                "yaxis": {**layout_base["yaxis"], "title": "Imag"},
                "shapes": [{
                    "type": "line", "x0": 0, "x1": 0,
                    "y0": -20, "y1": 20,
                    "line": {"color": C["zeroline"], "width": 1, "dash": "dash"},
                }],
                "datarevision": f"poles-{id(self._result)}",
                "uirevision": "poles",
            },
        }
        plots.append(pz_plot)

        return plots

    def get_state(self) -> Dict[str, Any]:
        if not self._initialized:
            self.initialize()
        return {
            "parameters": self.parameters.copy(),
            "plots": self.get_plots(),
            "metadata": {
                "simulation_type": "inverted_pendulum_3d",
            "hub_slots": self.HUB_SLOTS,
            "hub_domain": self.HUB_DOMAIN,
            "hub_dimensions": self.HUB_DIMENSIONS,
                "animation": self._result["animation"] if self._result else None,
                "controller_info": self._result["controller_info"] if self._result else {},
                "metrics": self._result["metrics"] if self._result else {},
            },
        }
