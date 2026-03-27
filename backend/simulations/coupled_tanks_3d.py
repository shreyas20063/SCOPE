"""Coupled Tanks — 3D Physics Lab simulation.

Full nonlinear MIMO dynamics with swappable controllers (None, Dual PID,
LQR, Pole Placement, LQG). Server-side RK45 integration for textbook accuracy.
Frontend receives trajectory arrays for Three.js 3D animation + Plotly plots.

Physics:
    State: [h₁, h₂] where h₁=tank 1 level, h₂=tank 2 level
    ḣ₁ = (q₁ − a₁√(2g·h₁)) / A₁
    ḣ₂ = (q₂ + a₁√(2g·h₁) − a₂√(2g·h₂)) / A₂
    Tank 1 drains into Tank 2. Both have independent inflow pumps.

References: Johansson (2000) "The Quadruple-Tank Process", Åström & Murray Ch 3.
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple

from .base_simulator import BaseSimulator
from core.controllers import (
    numerical_jacobian, controllability_matrix, observability_matrix,
    compute_lqr, compute_pole_placement, compute_lqg,
    simulate_uncontrolled, simulate_state_feedback,
    simulate_lqg, compute_performance_metrics, compute_energy,
)


class CoupledTanks3DSimulator(BaseSimulator):
    """Coupled tanks MIMO system with 3D visualization and swappable controllers."""

    # Physics constants
    G = 9.81

    # Simulation config
    SIM_TIME = 20.0
    DT = 0.02

    # Default input saturation (overridden by pump_capacity parameter)
    _DEFAULT_U_MAX = 5.0

    # Plot colors
    COLORS = {
        "h1": "#22d3ee",       # cyan — tank 1 level
        "h2": "#f472b6",       # pink — tank 2 level
        "q1": "#3b82f6",       # blue — pump 1
        "q2": "#a855f7",       # purple — pump 2
        "reference": "#34d399",  # green — target lines
        "estimate": "#f59e0b",   # amber — observer estimate
        "stable": "#10b981",
        "unstable": "#ef4444",
        "grid": "rgba(148, 163, 184, 0.1)",
        "zeroline": "rgba(148, 163, 184, 0.3)",
    }

    PARAMETER_SCHEMA = {
        # --- Plant ---
        "tank_area": {
            "type": "slider", "min": 0.5, "max": 2.0, "step": 0.1,
            "default": 1.0, "unit": "m²", "label": "Tank Cross-Section A",
            "group": "Plant",
        },
        "orifice_area": {
            "type": "slider", "min": 0.1, "max": 0.5, "step": 0.01,
            "default": 0.2, "unit": "m²", "label": "Orifice Area a",
            "group": "Plant",
        },
        "initial_h1": {
            "type": "slider", "min": 0.2, "max": 2.0, "step": 0.05,
            "default": 0.5, "unit": "m", "label": "Initial h₁",
            "group": "Plant",
        },
        "initial_h2": {
            "type": "slider", "min": 0.1, "max": 2.0, "step": 0.05,
            "default": 0.3, "unit": "m", "label": "Initial h₂",
            "group": "Plant",
        },
        "pump_capacity": {
            "type": "slider", "min": 0.5, "max": 10.0, "step": 0.1,
            "default": 5.0, "unit": "m³/s", "label": "Pump Capacity (U_MAX)",
            "group": "Plant",
        },
        "disturbance": {
            "type": "slider", "min": 0.0, "max": 2.0, "step": 0.01,
            "default": 0.0, "unit": "m³/s", "label": "Tank 1 Leak Rate",
            "group": "Plant",
        },
        # --- Setpoints ---
        "h1_ref": {
            "type": "slider", "min": 0.2, "max": 2.5, "step": 0.05,
            "default": 0.5, "unit": "m", "label": "h₁ Reference",
            "group": "Setpoints",
        },
        "h2_ref": {
            "type": "slider", "min": 0.2, "max": 2.5, "step": 0.05,
            "default": 1.0, "unit": "m", "label": "h₂ Reference",
            "group": "Setpoints",
        },
        # --- Controller Selection ---
        "controller": {
            "type": "select",
            "options": [
                {"value": "none", "label": "No Control"},
                {"value": "pid", "label": "Dual PID"},
                {"value": "lqr", "label": "LQR (Optimal)"},
                {"value": "pole_placement", "label": "Pole Placement"},
                {"value": "lqg", "label": "LQG (Observer)"},
            ],
            "default": "lqr", "label": "Controller", "group": "Controller",
        },
        # --- PID gains (loop 1: h₁ → q₁) ---
        "pid1_Kp": {
            "type": "slider", "min": 0, "max": 20, "step": 0.1,
            "default": 5.0, "label": "PID₁ Kp", "group": "PID Gains (h₁→q₁)",
            "visible_when": {"controller": "pid"},
        },
        "pid1_Ki": {
            "type": "slider", "min": 0, "max": 10, "step": 0.1,
            "default": 2.0, "label": "PID₁ Ki", "group": "PID Gains (h₁→q₁)",
            "visible_when": {"controller": "pid"},
        },
        "pid1_Kd": {
            "type": "slider", "min": 0, "max": 10, "step": 0.1,
            "default": 1.0, "label": "PID₁ Kd", "group": "PID Gains (h₁→q₁)",
            "visible_when": {"controller": "pid"},
        },
        # --- PID gains (loop 2: h₂ → q₂) ---
        "pid2_Kp": {
            "type": "slider", "min": 0, "max": 20, "step": 0.1,
            "default": 5.0, "label": "PID₂ Kp", "group": "PID Gains (h₂→q₂)",
            "visible_when": {"controller": "pid"},
        },
        "pid2_Ki": {
            "type": "slider", "min": 0, "max": 10, "step": 0.1,
            "default": 2.0, "label": "PID₂ Ki", "group": "PID Gains (h₂→q₂)",
            "visible_when": {"controller": "pid"},
        },
        "pid2_Kd": {
            "type": "slider", "min": 0, "max": 10, "step": 0.1,
            "default": 1.0, "label": "PID₂ Kd", "group": "PID Gains (h₂→q₂)",
            "visible_when": {"controller": "pid"},
        },
        # --- LQR weights ---
        "lqr_q_h1": {
            "type": "slider", "min": 0.1, "max": 100, "step": 0.1,
            "default": 10.0, "label": "Q₁₁ (h₁ weight)", "group": "LQR Weights",
            "visible_when": {"controller": "lqr"},
        },
        "lqr_q_h2": {
            "type": "slider", "min": 0.1, "max": 100, "step": 0.1,
            "default": 10.0, "label": "Q₂₂ (h₂ weight)", "group": "LQR Weights",
            "visible_when": {"controller": "lqr"},
        },
        "lqr_r1": {
            "type": "slider", "min": 0.01, "max": 10, "step": 0.01,
            "default": 1.0, "label": "R₁₁ (q₁ effort)", "group": "LQR Weights",
            "visible_when": {"controller": "lqr"},
        },
        "lqr_r2": {
            "type": "slider", "min": 0.01, "max": 10, "step": 0.01,
            "default": 1.0, "label": "R₂₂ (q₂ effort)", "group": "LQR Weights",
            "visible_when": {"controller": "lqr"},
        },
        # --- Pole Placement ---
        "pp_real": {
            "type": "slider", "min": -5, "max": -0.2, "step": 0.1,
            "default": -1.5, "label": "Dominant pole real part", "group": "Pole Placement",
            "visible_when": {"controller": "pole_placement"},
        },
        "pp_spread": {
            "type": "slider", "min": 1.0, "max": 3.0, "step": 0.1,
            "default": 1.5, "label": "Pole spread factor", "group": "Pole Placement",
            "visible_when": {"controller": "pole_placement"},
        },
        # --- LQG noise ---
        "lqg_q_h1": {
            "type": "slider", "min": 0.1, "max": 100, "step": 0.1,
            "default": 10.0, "label": "Q₁₁ (h₁ weight)", "group": "LQG Design",
            "visible_when": {"controller": "lqg"},
        },
        "lqg_q_h2": {
            "type": "slider", "min": 0.1, "max": 100, "step": 0.1,
            "default": 10.0, "label": "Q₂₂ (h₂ weight)", "group": "LQG Design",
            "visible_when": {"controller": "lqg"},
        },
        "lqg_r1": {
            "type": "slider", "min": 0.01, "max": 10, "step": 0.01,
            "default": 1.0, "label": "R₁₁ (q₁ effort)", "group": "LQG Design",
            "visible_when": {"controller": "lqg"},
        },
        "lqg_r2": {
            "type": "slider", "min": 0.01, "max": 10, "step": 0.01,
            "default": 1.0, "label": "R₂₂ (q₂ effort)", "group": "LQG Design",
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
        "tank_area": 1.0,
        "orifice_area": 0.2,
        "initial_h1": 0.5,
        "initial_h2": 0.3,
        "pump_capacity": 5.0,
        "disturbance": 0.0,
        "h1_ref": 0.5,
        "h2_ref": 1.0,
        "controller": "lqr",
        "pid1_Kp": 5.0, "pid1_Ki": 2.0, "pid1_Kd": 1.0,
        "pid2_Kp": 5.0, "pid2_Ki": 2.0, "pid2_Kd": 1.0,
        "lqr_q_h1": 10.0, "lqr_q_h2": 10.0, "lqr_r1": 1.0, "lqr_r2": 1.0,
        "pp_real": -1.5, "pp_spread": 1.5,
        "lqg_q_h1": 10.0, "lqg_q_h2": 10.0, "lqg_r1": 1.0, "lqg_r2": 1.0,
        "lqg_process_noise": 0.01, "lqg_sensor_noise": 0.01,
    }

    HUB_SLOTS = ["control"]
    HUB_DIMENSIONS = {"n": None, "m": None, "p": None}

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._result: Optional[Dict] = None

    @property
    def _h1_ref(self) -> float:
        return self.parameters.get("h1_ref", 0.5) if hasattr(self, 'parameters') and self.parameters else 0.5

    @property
    def _h2_ref(self) -> float:
        return self.parameters.get("h2_ref", 1.0) if hasattr(self, 'parameters') and self.parameters else 1.0

    @property
    def _u_max(self) -> float:
        return self.parameters.get("pump_capacity", 5.0) if hasattr(self, 'parameters') and self.parameters else 5.0

    @property
    def _disturbance(self) -> float:
        return self.parameters.get("disturbance", 0.0) if hasattr(self, 'parameters') and self.parameters else 0.0

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

    def _safe_sqrt(self, h: float) -> float:
        """Protected sqrt for water level — avoids negative arguments."""
        return np.sqrt(max(h, 0.001))

    def _equilibrium_inputs(self) -> np.ndarray:
        """Compute equilibrium flow rates for h₁_eq, h₂_eq.

        At equilibrium:
            q₁_eq = a √(2g h₁_eq) + leak
            q₂_eq = a √(2g h₂_eq) − a √(2g h₁_eq)

        Note: q₂_eq < 0 when h₁_ref > h₂_ref — physically impossible
        with pump-only control (u ≥ 0 clamp), causing true instability.
        """
        a = self.parameters["orifice_area"]
        leak = self._disturbance
        flow_1_out = a * np.sqrt(2 * self.G * max(self._h1_ref, 0.001))
        flow_2_out = a * np.sqrt(2 * self.G * max(self._h2_ref, 0.001))
        q1_eq = flow_1_out + leak  # must compensate for leak
        q2_eq = flow_2_out - flow_1_out
        return np.array([q1_eq, q2_eq])

    def _dynamics(self, x: np.ndarray, u: np.ndarray) -> np.ndarray:
        """Full nonlinear coupled-tank equations of motion.

        State: [h₁, h₂]
        Inputs: [q₁, q₂] — inflow rates to each tank

        ḣ₁ = (q₁ − a√(2g·h₁) − leak) / A
        ḣ₂ = (q₂ + a√(2g·h₁) − a√(2g·h₂)) / A
        """
        A_tank = self.parameters["tank_area"]
        a = self.parameters["orifice_area"]
        g = self.G
        leak = self._disturbance

        h1, h2 = x[0], x[1]
        q1 = u[0] if len(u) > 0 else 0.0
        q2 = u[1] if len(u) > 1 else 0.0

        # Protected sqrt to avoid domain errors
        sqrt_h1 = np.sqrt(max(h1, 0.001))
        sqrt_h2 = np.sqrt(max(h2, 0.001))

        flow_1_out = a * np.sqrt(2 * g) * sqrt_h1    # tank 1 outflow (→ tank 2)
        flow_2_out = a * np.sqrt(2 * g) * sqrt_h2    # tank 2 outflow (→ drain)

        dh1 = (q1 - flow_1_out - leak) / A_tank      # leak drains tank 1
        dh2 = (q2 + flow_1_out - flow_2_out) / A_tank

        return np.array([dh1, dh2])

    # ------------------------------------------------------------------ #
    #  Dual PID simulation (custom — 2 independent loops)                 #
    # ------------------------------------------------------------------ #

    def _simulate_dual_pid(
        self, x0: np.ndarray, t_span: Tuple[float, float],
    ) -> Dict[str, np.ndarray]:
        """Simulate two independent PID loops on the MIMO plant.

        PID1: tracks h₁ → H1_REF via q₁
        PID2: tracks h₂ → H2_REF via q₂

        Augmented state: [h₁, h₂, int_err₁, filt_d₁, int_err₂, filt_d₂]
        """
        from scipy.integrate import solve_ivp

        p = self.parameters
        Kp1, Ki1, Kd1 = p["pid1_Kp"], p["pid1_Ki"], p["pid1_Kd"]
        Kp2, Ki2, Kd2 = p["pid2_Kp"], p["pid2_Ki"], p["pid2_Kd"]
        N = 100.0  # derivative filter coefficient

        u_eq = self._equilibrium_inputs()
        n_states = 2

        # Augmented: [h1, h2, ie1, fd1, ie2, fd2]
        x0_aug = np.zeros(n_states + 4)
        x0_aug[:n_states] = x0

        t_eval = np.arange(t_span[0], t_span[1], self.DT)

        def rhs(t, z):
            h1, h2 = z[0], z[1]
            ie1, fd1, ie2, fd2 = z[2], z[3], z[4], z[5]

            e1 = self._h1_ref - h1
            e2 = self._h2_ref - h2

            # PID1 → q₁ (Kd term uses filtered derivative: N*(e-fd) ≈ de/dt)
            u1 = u_eq[0] + Kp1 * e1 + Ki1 * ie1 + Kd1 * N * (e1 - fd1)
            u1 = np.clip(u1, 0.0, self._u_max)

            # PID2 → q₂
            u2 = u_eq[1] + Kp2 * e2 + Ki2 * ie2 + Kd2 * N * (e2 - fd2)
            u2 = np.clip(u2, 0.0, self._u_max)

            dx = self._dynamics(z[:n_states], np.array([u1, u2]))

            dz = np.zeros(n_states + 4)
            dz[:n_states] = dx
            dz[2] = e1              # d(ie1)/dt
            dz[3] = N * (e1 - fd1)  # filtered derivative 1
            dz[4] = e2              # d(ie2)/dt
            dz[5] = N * (e2 - fd2)  # filtered derivative 2
            return dz

        sol = solve_ivp(rhs, t_span, x0_aug, method='RK45',
                        t_eval=t_eval, max_step=self.DT, rtol=1e-8, atol=1e-10)

        x_traj = sol.y[:n_states, :].T
        ie1_traj = sol.y[2, :]
        fd1_traj = sol.y[3, :]
        ie2_traj = sol.y[4, :]
        fd2_traj = sol.y[5, :]

        # Reconstruct control signals
        u_traj = np.zeros((len(sol.t), 2))
        for i in range(len(sol.t)):
            e1 = self._h1_ref - x_traj[i, 0]
            e2 = self._h2_ref - x_traj[i, 1]
            u1 = u_eq[0] + Kp1 * e1 + Ki1 * ie1_traj[i] + Kd1 * N * (e1 - fd1_traj[i])
            u2 = u_eq[1] + Kp2 * e2 + Ki2 * ie2_traj[i] + Kd2 * N * (e2 - fd2_traj[i])
            u_traj[i, 0] = np.clip(u1, 0.0, self._u_max)
            u_traj[i, 1] = np.clip(u2, 0.0, self._u_max)

        return {
            "t": sol.t,
            "x": x_traj,
            "u": u_traj,
        }

    # ------------------------------------------------------------------ #
    #  Main computation                                                   #
    # ------------------------------------------------------------------ #

    def _compute(self) -> None:
        """Run simulation with selected controller."""
        p = self.parameters
        ctrl = p["controller"]

        # Equilibrium
        x_eq = np.array([self._h1_ref, self._h2_ref])
        u_eq = self._equilibrium_inputs()

        # Initial condition
        x0 = np.array([p["initial_h1"], p["initial_h2"]])

        t_span = (0.0, self.SIM_TIME)

        # Linearize at equilibrium
        A, B = numerical_jacobian(self._dynamics, x_eq, u_eq)
        n = 2
        C = np.eye(n)  # full state output

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
            "h1_ref": self._h1_ref,
            "h2_ref": self._h2_ref,
            "u_eq": u_eq.tolist(),
        }

        try:
            if ctrl == "none":
                # Uncontrolled: apply constant equilibrium inputs
                def _dyn_eq(x, u):
                    return self._dynamics(x, u_eq)
                result = simulate_uncontrolled(
                    _dyn_eq, x0, t_span, n_inputs=2, dt=self.DT)
                # Override u with equilibrium values
                result["u"][:] = u_eq
                controller_info["K"] = None

            elif ctrl == "pid":
                result = self._simulate_dual_pid(x0, t_span)
                controller_info["gains"] = {
                    "loop1": {"Kp": p["pid1_Kp"], "Ki": p["pid1_Ki"], "Kd": p["pid1_Kd"]},
                    "loop2": {"Kp": p["pid2_Kp"], "Ki": p["pid2_Ki"], "Kd": p["pid2_Kd"]},
                }

            elif ctrl == "lqr":
                Q = np.diag([p["lqr_q_h1"], p["lqr_q_h2"]])
                R = np.diag([p["lqr_r1"], p["lqr_r2"]])
                K, P, cl_eigs = compute_lqr(A, B, Q, R)
                # Wrap dynamics to clamp u to [0, U_MAX]
                result = self._simulate_clamped_state_feedback(
                    x0, t_span, K, x_eq, u_eq)
                controller_info["K"] = K.tolist()
                controller_info["cl_eigenvalues"] = cl_eigs.tolist()
                controller_info["Q"] = Q.tolist()
                controller_info["R"] = R.tolist()

            elif ctrl == "pole_placement":
                s = p["pp_real"]
                spread = p["pp_spread"]
                poles = np.array([s, s * spread])
                K, cl_eigs = compute_pole_placement(A, B, poles)
                result = self._simulate_clamped_state_feedback(
                    x0, t_span, K, x_eq, u_eq)
                controller_info["K"] = K.tolist()
                controller_info["cl_eigenvalues"] = cl_eigs.tolist()
                controller_info["desired_poles"] = poles.tolist()

            elif ctrl == "lqg":
                Q_lqr = np.diag([p["lqg_q_h1"], p["lqg_q_h2"]])
                R_lqr = np.diag([p["lqg_r1"], p["lqg_r2"]])
                Q_kalman = p["lqg_process_noise"] * np.eye(n)
                R_kalman = p["lqg_sensor_noise"] * np.eye(n)

                K, L, P_ctrl, P_est = compute_lqg(
                    A, B, C, Q_lqr, R_lqr, Q_kalman, R_kalman)
                result = self._simulate_clamped_lqg(
                    x0, t_span, K, L, A, B, C, x_eq, u_eq)
                controller_info["K"] = K.tolist()
                controller_info["L"] = L.tolist()
                controller_info["cl_eigenvalues"] = np.linalg.eigvals(
                    A - B @ K).tolist()
                controller_info["est_eigenvalues"] = np.linalg.eigvals(
                    A - L @ C).tolist()

            else:
                def _dyn_eq(x, u):
                    return self._dynamics(x, u_eq)
                result = simulate_uncontrolled(
                    _dyn_eq, x0, t_span, n_inputs=2, dt=self.DT)
                result["u"][:] = u_eq

        except Exception as e:
            # Fallback to uncontrolled
            def _dyn_eq(x, u):
                return self._dynamics(x, u_eq)
            result = simulate_uncontrolled(
                _dyn_eq, x0, t_span, n_inputs=2, dt=self.DT)
            result["u"][:] = u_eq
            controller_info["error"] = str(e)

        # Check stability: did levels converge to targets?
        h1_traj = result["x"][:, 0]
        h2_traj = result["x"][:, 1]
        tail = max(1, len(h1_traj) // 10)
        h1_err = float(np.mean(np.abs(h1_traj[-tail:] - self._h1_ref)))
        h2_err = float(np.mean(np.abs(h2_traj[-tail:] - self._h2_ref)))
        is_stable = h1_err < 0.1 and h2_err < 0.1

        # Performance metrics (track h₁ → H1_REF)
        metrics = compute_performance_metrics(
            result["t"], result["x"], state_index=0, x_ref=self._h1_ref)
        metrics["control_energy"] = compute_energy(result["u"], result["t"])
        metrics["is_stable"] = is_stable
        metrics["h1_ss_error"] = h1_err
        metrics["h2_ss_error"] = h2_err

        # Subsample for 3D animation
        skip = 2
        t_anim = result["t"][::skip]
        x_anim = result["x"][::skip]
        u_anim = result["u"][::skip]

        # Track overflow and saturation for frontend visual effects
        h1_max = float(np.max(h1_traj))
        h2_max = float(np.max(h2_traj))
        u_traj_full = result["u"]
        any_saturated = bool(
            np.any(u_traj_full >= self._u_max - 0.01)
            or np.any(u_traj_full <= 0.01)
        )

        self._result = {
            "sim": result,
            "controller_info": controller_info,
            "metrics": metrics,
            "animation": {
                "t": t_anim.tolist(),
                "h1": x_anim[:, 0].tolist(),
                "h2": x_anim[:, 1].tolist(),
                "q1": u_anim[:, 0].tolist(),
                "q2": u_anim[:, 1].tolist(),
                "dt": self.DT * skip,
                "num_frames": len(t_anim),
                "tank_area": self.parameters["tank_area"],
                "orifice_area": self.parameters["orifice_area"],
                "h1_ref": self._h1_ref,
                "h2_ref": self._h2_ref,
                "is_stable": is_stable,
                "overflow_1": h1_max > 2.5,
                "overflow_2": h2_max > 2.5,
                "any_saturated": any_saturated,
                "q2_eq": float(u_eq[1]),
                "infeasible_equilibrium": bool(u_eq[1] < -1e-6),
                "infeasible_warning": (
                    f"Equilibrium requires negative pump flow q₂={u_eq[1]:.3f} L/s "
                    f"(h₁_ref={self._h1_ref:.2f} > h₂_ref={self._h2_ref:.2f}). "
                    "Physical pumps cannot extract fluid. Controller may not converge."
                ) if u_eq[1] < -1e-6 else None,
            },
        }
        if ctrl == "lqg" and "x_hat" in result:
            x_hat_anim = result["x_hat"][::skip]
            self._result["animation"]["x_hat"] = x_hat_anim.tolist()

    # ------------------------------------------------------------------ #
    #  Clamped simulation helpers (flow rates must be ≥ 0)                #
    # ------------------------------------------------------------------ #

    def _simulate_clamped_state_feedback(
        self, x0: np.ndarray, t_span: Tuple[float, float],
        K: np.ndarray, x_eq: np.ndarray, u_eq: np.ndarray,
    ) -> Dict[str, np.ndarray]:
        """State feedback with non-negative flow rate clamping."""
        from scipy.integrate import solve_ivp

        K = np.atleast_2d(K)
        t_eval = np.arange(t_span[0], t_span[1], self.DT)

        def rhs(t, x):
            dx = np.array(x) - x_eq
            u = u_eq - K @ dx
            u = np.clip(u.flatten(), 0.0, self._u_max)
            return self._dynamics(np.array(x), u)

        sol = solve_ivp(rhs, t_span, x0, method='RK45',
                        t_eval=t_eval, max_step=self.DT, rtol=1e-8, atol=1e-10)

        x_traj = sol.y.T
        u_traj = np.zeros((len(sol.t), 2))
        for i in range(len(sol.t)):
            dx = x_traj[i] - x_eq
            u = u_eq - K @ dx
            u_traj[i] = np.clip(u.flatten(), 0.0, self._u_max)

        return {"t": sol.t, "x": x_traj, "u": u_traj}

    def _simulate_clamped_lqg(
        self, x0: np.ndarray, t_span: Tuple[float, float],
        K: np.ndarray, L: np.ndarray,
        A: np.ndarray, B: np.ndarray, C: np.ndarray,
        x_eq: np.ndarray, u_eq: np.ndarray,
    ) -> Dict[str, np.ndarray]:
        """LQG simulation with non-negative flow rate clamping."""
        from scipy.integrate import solve_ivp

        K = np.atleast_2d(K)
        L = np.atleast_2d(L)
        n = len(x_eq)
        t_eval = np.arange(t_span[0], t_span[1], self.DT)

        x0_aug = np.zeros(2 * n)
        x0_aug[:n] = x0
        x0_aug[n:] = x_eq  # observer starts at equilibrium

        def rhs(t, z):
            x_true = z[:n]
            x_hat = z[n:]

            dx_hat = x_hat - x_eq
            u = u_eq - K @ dx_hat
            u = np.clip(u.flatten(), 0.0, self._u_max)

            dx_true = self._dynamics(x_true, u)

            y = C @ (x_true - x_eq)
            y_hat = C @ dx_hat
            innovation = y.flatten() - y_hat.flatten()

            dx_hat_dot = A @ dx_hat + B @ (u - u_eq) + L @ innovation

            dz = np.zeros(2 * n)
            dz[:n] = dx_true
            dz[n:] = dx_hat_dot
            return dz

        sol = solve_ivp(rhs, t_span, x0_aug, method='RK45',
                        t_eval=t_eval, max_step=self.DT, rtol=1e-8, atol=1e-10)

        x_traj = sol.y[:n, :].T
        x_hat_traj = sol.y[n:, :].T

        u_traj = np.zeros((len(sol.t), 2))
        for i in range(len(sol.t)):
            dx_hat = x_hat_traj[i] - x_eq
            u = u_eq - K @ dx_hat
            u_traj[i] = np.clip(u.flatten(), 0.0, self._u_max)

        return {"t": sol.t, "x": x_traj, "x_hat": x_hat_traj, "u": u_traj}

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

        # 1. Tank levels
        level_plot = {
            "id": "levels",
            "title": "Tank Water Levels",
            "data": [
                {
                    "x": t.tolist(), "y": x[:, 0].tolist(),
                    "type": "scatter", "mode": "lines",
                    "name": "h₁", "line": {"color": C["h1"], "width": 2},
                },
                {
                    "x": t.tolist(), "y": x[:, 1].tolist(),
                    "type": "scatter", "mode": "lines",
                    "name": "h₂", "line": {"color": C["h2"], "width": 2},
                },
                {
                    "x": [t[0], t[-1]], "y": [self._h1_ref, self._h1_ref],
                    "type": "scatter", "mode": "lines",
                    "name": "h₁ ref", "line": {"color": C["h1"],
                                                 "width": 1, "dash": "dash"},
                },
                {
                    "x": [t[0], t[-1]], "y": [self._h2_ref, self._h2_ref],
                    "type": "scatter", "mode": "lines",
                    "name": "h₂ ref", "line": {"color": C["h2"],
                                                 "width": 1, "dash": "dash"},
                },
            ],
            "layout": {
                **layout_base,
                "yaxis": {**layout_base["yaxis"], "title": "Level (m)"},
                "xaxis": {**layout_base["xaxis"], "title": "Time (s)"},
                "datarevision": f"levels-{id(self._result)}",
                "uirevision": "levels",
            },
        }
        plots.append(level_plot)

        # 2. Control inputs (flow rates)
        ctrl_plot = {
            "id": "control",
            "title": "Pump Flow Rates",
            "data": [
                {
                    "x": t.tolist(), "y": u[:, 0].tolist(),
                    "type": "scatter", "mode": "lines",
                    "name": "q₁", "line": {"color": C["q1"], "width": 2},
                },
                {
                    "x": t.tolist(), "y": u[:, 1].tolist(),
                    "type": "scatter", "mode": "lines",
                    "name": "q₂", "line": {"color": C["q2"], "width": 2},
                },
            ],
            "layout": {
                **layout_base,
                "yaxis": {**layout_base["yaxis"], "title": "Flow (m³/s)"},
                "xaxis": {**layout_base["xaxis"], "title": "Time (s)"},
                "datarevision": f"ctrl-{id(self._result)}",
                "uirevision": "control",
            },
        }
        plots.append(ctrl_plot)

        # 3. Phase portrait (h₁ vs h₂)
        phase_plot = {
            "id": "phase",
            "title": "Phase Portrait (h₁ vs h₂)",
            "data": [
                {
                    "x": x[:, 0].tolist(), "y": x[:, 1].tolist(),
                    "type": "scatter", "mode": "lines",
                    "name": "Trajectory",
                    "line": {"color": C["h1"], "width": 2},
                },
                {
                    "x": [self._h1_ref], "y": [self._h2_ref],
                    "type": "scatter", "mode": "markers",
                    "name": "Equilibrium",
                    "marker": {"color": C["stable"], "size": 10, "symbol": "x"},
                },
                {
                    "x": [x[0, 0]], "y": [x[0, 1]],
                    "type": "scatter", "mode": "markers",
                    "name": "Start",
                    "marker": {"color": C["unstable"], "size": 8, "symbol": "circle"},
                },
            ],
            "layout": {
                **layout_base,
                "xaxis": {**layout_base["xaxis"], "title": "h₁ (m)",
                          "scaleanchor": "y"},
                "yaxis": {**layout_base["yaxis"], "title": "h₂ (m)"},
                "datarevision": f"phase-{id(self._result)}",
                "uirevision": "phase",
            },
        }
        plots.append(phase_plot)

        # 4. Pole-zero map
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
                "marker": {"color": C["estimate"], "size": 10, "symbol": "diamond"},
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
                    "y0": -5, "y1": 5,
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
                "simulation_type": "coupled_tanks_3d",
                "hub_slots": self.HUB_SLOTS,
                "hub_domain": self.HUB_DOMAIN,
                "hub_dimensions": self.HUB_DIMENSIONS,
                "animation": self._result["animation"] if self._result else None,
                "controller_info": self._result["controller_info"] if self._result else {},
                "metrics": self._result["metrics"] if self._result else {},
            },
        }
