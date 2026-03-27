"""Ball & Beam 3D Physics Lab simulation.

Full nonlinear dynamics with swappable controllers (None, PID, LQR,
Pole Placement, LQG). Server-side RK45 integration for textbook accuracy.
Frontend receives trajectory arrays for Three.js 3D animation + Plotly plots.

Physics (Lagrangian-derived):
    State: [r, r_dot, alpha, alpha_dot]
    where r = ball position on beam, alpha = beam tilt angle
    Ball: m(r_ddot - r * alpha_dot^2) = -mg sin(alpha)
    Beam: (J + m*r^2) alpha_ddot + 2*m*r*r_dot*alpha_dot + m*g*r*cos(alpha) = tau

References: Hauser, Sastry & Kokotovic (1992), Ogata Ch 12, Khalil Ch 12.
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


class BallBeam3DSimulator(BaseSimulator):
    """Ball on a tilting beam with 3D visualization and swappable controllers."""

    # Physics constants
    G = 9.81

    # Simulation config
    SIM_TIME = 10.0
    DT = 0.01

    # Plot colors
    COLORS = {
        "ball_pos": "#3b82f6",
        "ball_vel": "#60a5fa",
        "beam_angle": "#22d3ee",
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
        "beam_length": {
            "type": "slider", "min": 0.5, "max": 2.0, "step": 0.1,
            "default": 1.0, "unit": "m", "label": "Beam Length",
            "group": "Plant",
        },
        "ball_mass": {
            "type": "slider", "min": 0.05, "max": 0.5, "step": 0.01,
            "default": 0.1, "unit": "kg", "label": "Ball Mass m",
            "group": "Plant",
        },
        "ball_radius": {
            "type": "slider", "min": 0.01, "max": 0.05, "step": 0.005,
            "default": 0.015, "unit": "m", "label": "Ball Radius",
            "group": "Plant",
        },
        "initial_ball_pos": {
            "type": "slider", "min": -0.4, "max": 0.4, "step": 0.01,
            "default": 0.2, "unit": "m", "label": "Initial Ball Position",
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
            "type": "slider", "min": 0, "max": 50, "step": 0.5,
            "default": 15, "label": "Kp", "group": "PID Gains",
            "visible_when": {"controller": "pid"},
        },
        "pid_Ki": {
            "type": "slider", "min": 0, "max": 20, "step": 0.5,
            "default": 2, "label": "Ki", "group": "PID Gains",
            "visible_when": {"controller": "pid"},
        },
        "pid_Kd": {
            "type": "slider", "min": 0, "max": 20, "step": 0.5,
            "default": 8, "label": "Kd", "group": "PID Gains",
            "visible_when": {"controller": "pid"},
        },
        # --- LQR weights ---
        "lqr_q_r": {
            "type": "slider", "min": 0.1, "max": 100, "step": 0.1,
            "default": 10.0, "label": "Q11 (ball pos weight)", "group": "LQR Weights",
            "visible_when": {"controller": "lqr"},
        },
        "lqr_q_alpha": {
            "type": "slider", "min": 0.1, "max": 100, "step": 0.1,
            "default": 1.0, "label": "Q33 (beam angle weight)", "group": "LQR Weights",
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
            "default": -2.0, "label": "Dominant pole real part", "group": "Pole Placement",
            "visible_when": {"controller": "pole_placement"},
        },
        "pp_spread": {
            "type": "slider", "min": 1.0, "max": 3.0, "step": 0.1,
            "default": 1.5, "label": "Pole spread factor", "group": "Pole Placement",
            "visible_when": {"controller": "pole_placement"},
        },
        # --- LQG noise ---
        "lqg_q_r": {
            "type": "slider", "min": 0.1, "max": 100, "step": 0.1,
            "default": 10.0, "label": "Q11 (ball pos weight)", "group": "LQG Design",
            "visible_when": {"controller": "lqg"},
        },
        "lqg_q_alpha": {
            "type": "slider", "min": 0.1, "max": 100, "step": 0.1,
            "default": 1.0, "label": "Q33 (beam angle weight)", "group": "LQG Design",
            "visible_when": {"controller": "lqg"},
        },
        "lqg_r": {
            "type": "slider", "min": 0.01, "max": 10, "step": 0.01,
            "default": 0.1, "label": "R (effort cost)", "group": "LQG Design",
            "visible_when": {"controller": "lqg"},
        },
        "lqg_process_noise": {
            "type": "slider", "min": 0.001, "max": 1.0, "step": 0.001,
            "default": 0.01, "label": "Process noise \u03c3\u00b2", "group": "LQG Design",
            "visible_when": {"controller": "lqg"},
        },
        "lqg_sensor_noise": {
            "type": "slider", "min": 0.001, "max": 1.0, "step": 0.001,
            "default": 0.01, "label": "Sensor noise \u03c3\u00b2", "group": "LQG Design",
            "visible_when": {"controller": "lqg"},
        },
    }

    DEFAULT_PARAMS = {
        "beam_length": 1.0,
        "ball_mass": 0.1,
        "ball_radius": 0.015,
        "initial_ball_pos": 0.2,
        "controller": "lqr",
        "pid_Kp": 15, "pid_Ki": 2, "pid_Kd": 8,
        "lqr_q_r": 10.0, "lqr_q_alpha": 1.0, "lqr_r": 0.1,
        "pp_real": -2.0, "pp_spread": 1.5,
        "lqg_q_r": 10.0, "lqg_q_alpha": 1.0, "lqg_r": 0.1,
        "lqg_process_noise": 0.01, "lqg_sensor_noise": 0.01,
    }

    HUB_SLOTS = ["control"]

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

        State: [r, r_dot, alpha, alpha_dot]
        r = ball position along beam (0 = center)
        alpha = beam tilt angle from horizontal (positive = CW)
        """
        m = self.parameters["ball_mass"]
        beam_length = self.parameters.get("beam_length", 1.0)
        # Beam inertia scales with length²: J = M_beam·L²/12 for uniform beam
        # about center pivot. Using fixed beam mass of 0.5 kg.
        BEAM_MASS = 0.5
        J = BEAM_MASS * beam_length**2 / 12.0
        g = self.G

        r, r_dot, alpha, alpha_dot = x
        tau = u[0] if len(u) > 0 else 0.0

        sin_a = np.sin(alpha)
        cos_a = np.cos(alpha)

        # Ball equation: m(r_ddot - r * alpha_dot^2) = -mg sin(alpha)
        r_ddot = r * alpha_dot**2 - g * sin_a

        # Beam equation: (J + m*r^2) alpha_ddot + 2*m*r*r_dot*alpha_dot
        #                + m*g*r*cos(alpha) = tau
        J_eff = J + m * r**2
        alpha_ddot = (tau - 2 * m * r * r_dot * alpha_dot
                      - m * g * r * cos_a) / J_eff

        return np.array([r_dot, r_ddot, alpha_dot, alpha_ddot])

    # ------------------------------------------------------------------ #
    #  Main computation                                                   #
    # ------------------------------------------------------------------ #

    def _compute(self) -> None:
        """Run simulation with selected controller."""
        p = self.parameters
        ctrl = p["controller"]

        # Equilibrium: ball at center, beam level
        x_eq = np.array([0.0, 0.0, 0.0, 0.0])
        u_eq = np.array([0.0])

        # Initial condition: ball displaced from center
        r0 = p["initial_ball_pos"]
        x0 = np.array([r0, 0.0, 0.0, 0.0])

        t_span = (0.0, self.SIM_TIME)

        # Linearize at equilibrium
        A, B = numerical_jacobian(self._dynamics, x_eq, u_eq)
        n = 4
        C = np.eye(n)  # full state output for LQG

        # Controllability check
        Wc = controllability_matrix(A, B)
        ctrl_rank = int(np.linalg.matrix_rank(Wc))
        is_controllable = ctrl_rank == n

        controller_info: Dict[str, Any] = {
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
                    output_index=0, x_ref=0.0,  # track r = 0 (ball at center)
                    n_inputs=1, u_max=50.0, dt=self.DT)
                controller_info["gains"] = gains

            elif ctrl == "lqr":
                Q = np.diag([p["lqr_q_r"], 1.0, p["lqr_q_alpha"], 1.0])
                R = np.array([[p["lqr_r"]]])
                K, P, cl_eigs = compute_lqr(A, B, Q, R)
                result = simulate_state_feedback(
                    self._dynamics, x0, t_span, K, x_eq, u_eq,
                    u_max=50.0, dt=self.DT)
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
                    u_max=50.0, dt=self.DT)
                controller_info["K"] = K.tolist()
                controller_info["cl_eigenvalues"] = cl_eigs.tolist()
                controller_info["desired_poles"] = poles.tolist()

            elif ctrl in ("zn_closed", "itae_optimal"):
                # Auto-tune: optimize LQR Q/R weights to minimize ITAE
                tuned = auto_tune_lqr_itae(
                    self._dynamics, x0, A, B, x_eq, u_eq,
                    output_index=0, x_ref=0.0,
                    u_max=50.0, duration=5.0, dt=self.DT)
                if tuned is not None:
                    K_auto, q_diag, r_val = tuned
                    result = simulate_state_feedback(
                        self._dynamics, x0, t_span, K_auto, x_eq, u_eq,
                        u_max=50.0, dt=self.DT)
                    controller_info["K"] = K_auto.tolist()
                    controller_info["cl_eigenvalues"] = np.linalg.eigvals(
                        A - B @ K_auto).tolist()
                    controller_info["Q"] = np.diag(q_diag).tolist()
                    controller_info["R"] = [[r_val]]
                else:
                    # Fallback to default LQR
                    Q = np.diag([10.0, 1.0, 1.0, 1.0])
                    R = np.array([[0.1]])
                    K_auto, _, cl_eigs = compute_lqr(A, B, Q, R)
                    result = simulate_state_feedback(
                        self._dynamics, x0, t_span, K_auto, x_eq, u_eq,
                        u_max=50.0, dt=self.DT)
                    controller_info["K"] = K_auto.tolist()
                    controller_info["cl_eigenvalues"] = cl_eigs.tolist()
                    controller_info["auto_tune_fallback"] = True
                controller_info["auto_tune_method"] = ctrl

            elif ctrl == "lqg":
                Q_lqr = np.diag([p["lqg_q_r"], 1.0, p["lqg_q_alpha"], 1.0])
                R_lqr = np.array([[p["lqg_r"]]])
                Q_kalman = p["lqg_process_noise"] * np.eye(n)
                R_kalman = p["lqg_sensor_noise"] * np.eye(n)

                K, L, P_ctrl, P_est = compute_lqg(
                    A, B, C, Q_lqr, R_lqr, Q_kalman, R_kalman)
                result = simulate_lqg(
                    self._dynamics, x0, t_span, K, L, A, B, C,
                    x_eq, u_eq, u_max=50.0, dt=self.DT)
                controller_info["K"] = K.tolist()
                controller_info["L"] = L.tolist()
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

        # Check stability: did ball converge to r=0 without oscillation?
        r_traj = result["x"][:, 0]
        beam_half = p["beam_length"] / 2
        ball_fell_off = bool(np.any(np.abs(r_traj) > beam_half))
        final_err = abs(r_traj[-1])
        tail = max(1, len(r_traj) // 5)  # last 20%
        tail_std = float(np.std(r_traj[-tail:]))
        # Must converge within 5cm AND not oscillate AND stay on beam
        is_stable = (final_err < 0.05
                     and tail_std < 0.02
                     and not ball_fell_off)

        # Performance metrics (ball position tracking r=0)
        metrics = compute_performance_metrics(
            result["t"], result["x"], state_index=0, x_ref=0.0)
        metrics["control_energy"] = compute_energy(result["u"], result["t"])
        metrics["is_stable"] = is_stable

        # Subsample for 3D animation (every 2nd point)
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
                "ball_r": x_anim[:, 0].tolist(),
                "beam_alpha": x_anim[:, 2].tolist(),
                "control_torque": u_anim[:, 0].tolist(),
                "dt": self.DT * skip,
                "num_frames": len(t_anim),
                "beam_length": p["beam_length"],
                "ball_radius": p["ball_radius"],
                "is_stable": is_stable,
                "ball_fell_off": ball_fell_off,
                "ball_fell_off_warning": (
                    "Ball rolled off the beam — dynamics are unphysical beyond the beam edge."
                ) if ball_fell_off else None,
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

        # 1. Ball position
        ball_plot = {
            "id": "ball_pos",
            "title": "Ball Position r(t)",
            "data": [
                {
                    "x": t.tolist(), "y": x[:, 0].tolist(),
                    "type": "scatter", "mode": "lines",
                    "name": "r(t)", "line": {"color": C["ball_pos"], "width": 2},
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
                "yaxis": {**layout_base["yaxis"], "title": "Position (m)"},
                "xaxis": {**layout_base["xaxis"], "title": "Time (s)"},
                "datarevision": f"ball-{id(self._result)}",
                "uirevision": "ball_pos",
            },
        }
        plots.append(ball_plot)

        # 2. Beam angle
        alpha_deg = np.degrees(x[:, 2])
        angle_plot = {
            "id": "beam_angle",
            "title": "Beam Angle \u03b1(t)",
            "data": [
                {
                    "x": t.tolist(), "y": alpha_deg.tolist(),
                    "type": "scatter", "mode": "lines",
                    "name": "\u03b1(t)", "line": {"color": C["beam_angle"], "width": 2},
                },
                {
                    "x": [t[0], t[-1]], "y": [0, 0],
                    "type": "scatter", "mode": "lines",
                    "name": "Level", "line": {"color": C["reference"],
                                               "width": 1, "dash": "dash"},
                },
            ],
            "layout": {
                **layout_base,
                "yaxis": {**layout_base["yaxis"], "title": "Angle (deg)"},
                "xaxis": {**layout_base["xaxis"], "title": "Time (s)"},
                "datarevision": f"angle-{id(self._result)}",
                "uirevision": "beam_angle",
            },
        }
        plots.append(angle_plot)

        # 3. Control torque
        ctrl_plot = {
            "id": "control",
            "title": "Control Torque \u03c4(t)",
            "data": [
                {
                    "x": t.tolist(), "y": u[:, 0].tolist(),
                    "type": "scatter", "mode": "lines",
                    "name": "\u03c4(t)", "line": {"color": C["control"], "width": 2},
                },
            ],
            "layout": {
                **layout_base,
                "yaxis": {**layout_base["yaxis"], "title": "Torque (N\u00b7m)"},
                "xaxis": {**layout_base["xaxis"], "title": "Time (s)"},
                "datarevision": f"ctrl-{id(self._result)}",
                "uirevision": "control",
            },
        }
        plots.append(ctrl_plot)

        # 4. Phase portrait (r vs r_dot)
        phase_plot = {
            "id": "phase",
            "title": "Phase Portrait (r, \u1e59)",
            "data": [
                {
                    "x": x[:, 0].tolist(),
                    "y": x[:, 1].tolist(),
                    "type": "scatter", "mode": "lines",
                    "name": "Trajectory",
                    "line": {"color": C["ball_pos"], "width": 2},
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
                "xaxis": {**layout_base["xaxis"], "title": "r (m)"},
                "yaxis": {**layout_base["yaxis"], "title": "\u1e59 (m/s)"},
                "datarevision": f"phase-{id(self._result)}",
                "uirevision": "phase",
            },
        }
        plots.append(phase_plot)

        # 5. Pole map
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
                "simulation_type": "ball_beam_3d",
                "hub_slots": self.HUB_SLOTS,
                "hub_domain": self.HUB_DOMAIN,
                "hub_dimensions": self.HUB_DIMENSIONS,
                "animation": self._result["animation"] if self._result else None,
                "controller_info": self._result["controller_info"] if self._result else {},
                "metrics": self._result["metrics"] if self._result else {},
            },
        }
