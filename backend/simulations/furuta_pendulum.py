"""
Furuta Pendulum Simulator

Interactive simulation of a rotary inverted pendulum (Furuta Pendulum)
with PID control. Shows real-time 3D visualization, angle tracking,
and control torque plots.

Physics: The pendulum swings perpendicular to the rotating arm.
State: [theta, theta_dot, phi, phi_dot] where theta is pendulum angle
from vertical (0 = upright), phi is arm rotation in XY plane.
"""

import numpy as np
from typing import Any, Dict, List, Optional
from .base_simulator import BaseSimulator
from core.controllers import (
    numerical_jacobian, controllability_matrix,
    compute_lqr, compute_pole_placement, compute_lqg, compute_pid_gains,
    simulate_pid, simulate_state_feedback, simulate_lqg,
    compute_performance_metrics, compute_energy,
    ss2tf_siso, auto_tune_zn_closed, auto_tune_itae, auto_tune_lqr_itae,
)


class FurutaPendulumSimulator(BaseSimulator):
    """
    Furuta Pendulum simulation with PID control.

    State vector: [theta, theta_dot, phi, phi_dot]
    - theta: Pendulum angle from vertical (0 = upright, positive = leaning outward)
    - theta_dot: Pendulum angular velocity
    - phi: Arm rotation angle (horizontal plane)
    - phi_dot: Arm angular velocity

    The pendulum swings in a plane perpendicular to the arm.
    """

    # Configuration
    SIMULATION_TIME = 20.0  # seconds (extended for longer observation)
    DT = 0.01  # 10ms time step
    NUM_STEPS = int(SIMULATION_TIME / DT)
    G = 9.81  # gravity
    TORQUE_LIMIT = 5.0  # Max motor torque (Nm)
    INTEGRAL_LIMIT = 2.0  # Anti-windup limit

    # Damping coefficients (realistic for tabletop device, Quanser SRV02 scale)
    PENDULUM_DAMPING = 0.005  # Pendulum joint viscous friction (N·m·s/rad)
    ARM_DAMPING = 0.01  # Arm bearing viscous friction (N·m·s/rad)

    # Unified color palette
    COLORS = {
        "pendulum_angle": "#22d3ee",    # Cyan
        "control_torque": "#f472b6",    # Pink
        "arm_rotation": "#a855f7",      # Purple
        "reference": "#34d399",         # Emerald
        "stable": "#34d399",
        "unstable": "#f87171",
        "grid": "rgba(148, 163, 184, 0.2)",
    }

    # Default parameters
    DEFAULT_PARAMS = {
        "mass": 0.1,           # 100g pendulum mass
        "pendulum_length": 0.3, # 30cm pendulum
        "arm_length": 0.2,      # 20cm arm
        "controller": "pid",   # Default to PID
        "Kp": 80,              # Proportional gain (from LQR K[0,0] ≈ 83)
        "Kd": 16,              # Derivative gain (from LQR K[0,1] ≈ 16)
        "Ki": 2.0,             # Integral gain
        "initial_angle": 15,   # Start 15 degrees from vertical
        # LQR weights
        "lqr_q_theta": 10.0, "lqr_q_phi": 1.0, "lqr_r": 0.1,
        # Pole placement
        "pp_real": -3.0, "pp_spread": 1.5,
        # LQG
        "lqg_q_theta": 10.0, "lqg_q_phi": 1.0, "lqg_r": 0.1,
        "lqg_process_noise": 0.01, "lqg_sensor_noise": 0.01,
    }


    PARAMETER_SCHEMA = {
        "mass": {
            "type": "slider", "label": "Pendulum Mass",
            "min": 0.05, "max": 0.3, "step": 0.01, "default": 0.1,
            "unit": "kg", "description": "Mass at end of pendulum",
            "group": "Plant",
        },
        "pendulum_length": {
            "type": "slider", "label": "Pendulum Length",
            "min": 0.15, "max": 0.5, "step": 0.01, "default": 0.3,
            "unit": "m", "description": "Length of pendulum rod",
            "group": "Plant",
        },
        "arm_length": {
            "type": "slider", "label": "Arm Length",
            "min": 0.1, "max": 0.3, "step": 0.01, "default": 0.2,
            "unit": "m", "description": "Length of rotating arm",
            "group": "Plant",
        },
        "initial_angle": {
            "type": "slider", "label": "Initial Angle",
            "min": -90, "max": 90, "step": 1, "default": 15,
            "unit": "deg", "description": "Starting pendulum angle from vertical",
            "group": "Plant",
        },
        "controller": {
            "type": "select", "label": "Controller",
            "options": [
                {"value": "none", "label": "No Control"},
                {"value": "pid", "label": "PID"},
                {"value": "zn_closed", "label": "Auto-Tune (Fast)"},
                {"value": "itae_optimal", "label": "Auto-Tune (ITAE)"},
                {"value": "lqr", "label": "LQR (Optimal)"},
                {"value": "pole_placement", "label": "Pole Placement"},
                {"value": "lqg", "label": "LQG (Observer)"},
            ],
            "default": "pid", "group": "Controller",
        },
        "Kp": {
            "type": "slider", "label": "Kp (Proportional)",
            "min": 0, "max": 100, "step": 1, "default": 80,
            "unit": "", "description": "Proportional gain - main restoring force",
            "group": "PID Gains",
            "visible_when": {"controller": "pid"},
        },
        "Kd": {
            "type": "slider", "label": "Kd (Derivative)",
            "min": 0, "max": 20, "step": 0.5, "default": 16,
            "unit": "", "description": "Derivative gain - damping",
            "group": "PID Gains",
            "visible_when": {"controller": "pid"},
        },
        "Ki": {
            "type": "slider", "label": "Ki (Integral)",
            "min": 0, "max": 10, "step": 0.5, "default": 2,
            "unit": "", "description": "Integral gain - steady-state correction",
            "group": "PID Gains",
            "visible_when": {"controller": "pid"},
        },
        # LQR weights
        "lqr_q_theta": {
            "type": "slider", "label": "Q₁₁ (θ weight)", "min": 0.1, "max": 100,
            "step": 0.1, "default": 10.0, "group": "LQR Weights",
            "visible_when": {"controller": "lqr"},
        },
        "lqr_q_phi": {
            "type": "slider", "label": "Q₃₃ (φ weight)", "min": 0.1, "max": 100,
            "step": 0.1, "default": 1.0, "group": "LQR Weights",
            "visible_when": {"controller": "lqr"},
        },
        "lqr_r": {
            "type": "slider", "label": "R (effort cost)", "min": 0.01, "max": 10,
            "step": 0.01, "default": 0.1, "group": "LQR Weights",
            "visible_when": {"controller": "lqr"},
        },
        # Pole Placement
        "pp_real": {
            "type": "slider", "label": "Dominant pole real part", "min": -10, "max": -0.5,
            "step": 0.1, "default": -3.0, "group": "Pole Placement",
            "visible_when": {"controller": "pole_placement"},
        },
        "pp_spread": {
            "type": "slider", "label": "Pole spread factor", "min": 1.0, "max": 3.0,
            "step": 0.1, "default": 1.5, "group": "Pole Placement",
            "visible_when": {"controller": "pole_placement"},
        },
        # LQG
        "lqg_q_theta": {
            "type": "slider", "label": "Q₁₁ (θ weight)", "min": 0.1, "max": 100,
            "step": 0.1, "default": 10.0, "group": "LQG Design",
            "visible_when": {"controller": "lqg"},
        },
        "lqg_q_phi": {
            "type": "slider", "label": "Q₃₃ (φ weight)", "min": 0.1, "max": 100,
            "step": 0.1, "default": 1.0, "group": "LQG Design",
            "visible_when": {"controller": "lqg"},
        },
        "lqg_r": {
            "type": "slider", "label": "R (effort cost)", "min": 0.01, "max": 10,
            "step": 0.01, "default": 0.1, "group": "LQG Design",
            "visible_when": {"controller": "lqg"},
        },
        "lqg_process_noise": {
            "type": "slider", "label": "Process noise σ²", "min": 0.001, "max": 1.0,
            "step": 0.001, "default": 0.01, "group": "LQG Design",
            "visible_when": {"controller": "lqg"},
        },
        "lqg_sensor_noise": {
            "type": "slider", "label": "Sensor noise σ²", "min": 0.001, "max": 1.0,
            "step": 0.001, "default": 0.01, "group": "LQG Design",
            "visible_when": {"controller": "lqg"},
        },
    }

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._time = None
        self._theta = None
        self._theta_dot = None
        self._phi = None
        self._phi_dot = None
        self._torque = None
        self._is_stable = False
        self._settling_time = None

        # Full trajectory storage for animation
        self._arm_positions = []
        self._pendulum_positions = []
        self._current_arm_pos = [0.0, 0.0, 0.0]
        self._current_pendulum_pos = [0.0, 0.0, 0.3]

        # Enhanced physics data for visualization
        self._velocities = []  # Pendulum velocity vectors
        self._energies = []    # Total energy at each timestep
        self._angular_velocities = []  # [theta_dot, phi_dot] per frame

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
        """Simulate pendulum dynamics with selected controller."""
        mass = self.parameters["mass"]
        l = self.parameters["pendulum_length"]
        r = self.parameters["arm_length"]
        ctrl = self.parameters.get("controller", "pid")
        initial_angle_deg = self.parameters["initial_angle"]

        # Moments of inertia (proper rigid-body values)
        # Pendulum: uniform rod about pivot end → m·l²/3
        I_p = mass * l**2 / 3.0
        # Arm: uniform rod about center pivot → M_arm·r²/3, fixed arm mass 0.15 kg
        ARM_MASS = 0.15
        I_r = ARM_MASS * r**2 / 3.0

        # Initial state: [theta, theta_dot, phi, phi_dot]
        initial_angle = np.radians(initial_angle_deg)
        x0 = np.array([initial_angle, 0.0, 0.0, 0.0])

        # Equilibrium: upright (theta=0, phi=0)
        x_eq = np.array([0.0, 0.0, 0.0, 0.0])
        u_eq = np.array([0.0])

        # Controller info for metadata
        self._controller_info = {"type": ctrl}

        # For LQR/PP/LQG/auto-tune: linearize at equilibrium
        if ctrl in ("lqr", "pole_placement", "lqg", "none", "zn_closed", "itae_optimal"):
            try:
                A, B = numerical_jacobian(self._dynamics_wrapper, x_eq, u_eq)
                Wc = controllability_matrix(A, B)
                ctrl_rank = int(np.linalg.matrix_rank(Wc))
                self._controller_info["A"] = A.tolist()
                self._controller_info["B"] = B.tolist()
                self._controller_info["controllability_rank"] = ctrl_rank
                self._controller_info["is_controllable"] = ctrl_rank == 4
                self._controller_info["ol_eigenvalues"] = np.linalg.eigvals(A).tolist()

                if ctrl == "none":
                    self._run_uncontrolled(x0)
                elif ctrl == "lqr":
                    p = self.parameters
                    Q = np.diag([p["lqr_q_theta"], 1.0, p["lqr_q_phi"], 1.0])
                    R = np.array([[p["lqr_r"]]])
                    K, P, cl_eigs = compute_lqr(A, B, Q, R)
                    self._run_with_state_feedback(x0, K, x_eq, u_eq)
                    self._controller_info["K"] = K.tolist()
                    self._controller_info["cl_eigenvalues"] = cl_eigs.tolist()
                elif ctrl == "pole_placement":
                    p = self.parameters
                    s = p["pp_real"]
                    spread = p["pp_spread"]
                    poles = np.array([s, s * spread, s * spread**2, s * spread**3])
                    K, cl_eigs = compute_pole_placement(A, B, poles)
                    self._run_with_state_feedback(x0, K, x_eq, u_eq)
                    self._controller_info["K"] = K.tolist()
                    self._controller_info["cl_eigenvalues"] = cl_eigs.tolist()
                    self._controller_info["desired_poles"] = poles.tolist()
                elif ctrl == "lqg":
                    p = self.parameters
                    n = 4
                    C = np.eye(n)  # Full-state observation (C=I required by compute_lqg)
                    Q_lqr = np.diag([p["lqg_q_theta"], 1.0, p["lqg_q_phi"], 1.0])
                    R_lqr = np.array([[p["lqg_r"]]])
                    Q_kalman = p["lqg_process_noise"] * np.eye(n)
                    R_kalman = p["lqg_sensor_noise"] * np.eye(n)
                    K, L, _, _ = compute_lqg(A, B, C, Q_lqr, R_lqr, Q_kalman, R_kalman)
                    self._run_with_lqg(x0, K, L, A, B, C, x_eq, u_eq)
                    self._controller_info["K"] = K.tolist()
                    self._controller_info["L"] = L.tolist()
                    self._controller_info["cl_eigenvalues"] = np.linalg.eigvals(A - B @ K).tolist()
                    self._controller_info["est_eigenvalues"] = np.linalg.eigvals(A - L @ C).tolist()

                elif ctrl in ("zn_closed", "itae_optimal"):
                    # Auto-tune: optimize LQR Q/R to minimize ITAE
                    tuned = auto_tune_lqr_itae(
                        self._dynamics_wrapper, x0, A, B, x_eq, u_eq,
                        output_index=0, x_ref=0.0,
                        u_max=self.TORQUE_LIMIT,
                        duration=self.SIMULATION_TIME, dt=self.DT)
                    if tuned is not None:
                        K_auto, q_diag, r_val = tuned
                        self._run_with_state_feedback(x0, K_auto, x_eq, u_eq)
                        self._controller_info["K"] = K_auto.tolist()
                        self._controller_info["cl_eigenvalues"] = np.linalg.eigvals(
                            A - B @ K_auto).tolist()
                        self._controller_info["Q"] = np.diag(q_diag).tolist()
                        self._controller_info["R"] = [[r_val]]
                    else:
                        # Fallback to default LQR
                        Q = np.diag([10.0, 1.0, 1.0, 1.0])
                        R = np.array([[0.1]])
                        K_auto, _, cl_eigs = compute_lqr(A, B, Q, R)
                        self._run_with_state_feedback(x0, K_auto, x_eq, u_eq)
                        self._controller_info["K"] = K_auto.tolist()
                        self._controller_info["cl_eigenvalues"] = cl_eigs.tolist()
                        self._controller_info["auto_tune_fallback"] = True
                    self._controller_info["auto_tune_method"] = ctrl

                # Compute stability and settling
                self._peak_angle = float(np.max(np.abs(self._theta)))
                self._peak_angle_deg = float(np.degrees(self._peak_angle))
                last_samples = min(200, len(self._theta))
                self._is_stable = np.all(np.abs(self._theta[-last_samples:]) < np.radians(5))
                if self._peak_angle > np.radians(90):
                    self._is_stable = False
                within_tolerance = np.abs(self._theta) < np.radians(5)
                self._settling_time = None
                settling_window = min(100, len(self._theta) // 2)
                if np.any(within_tolerance) and self._is_stable and settling_window > 0:
                    for i in range(len(within_tolerance) - settling_window):
                        if np.all(within_tolerance[i:i + settling_window]):
                            self._settling_time = self._time[i]
                            break
                return

            except Exception as e:
                self._controller_info["error"] = str(e)
                # Fall through to PID as fallback

        # PID path — uses solve_ivp with augmented state for integral term
        # Augmented state: [theta, theta_dot, phi, phi_dot, integral_error]
        from scipy.integrate import solve_ivp

        Kp = self.parameters["Kp"]
        Ki = self.parameters["Ki"]
        Kd = self.parameters["Kd"]

        # Arm feedback gains (essential for underactuated stability):
        # The Furuta pendulum requires full-state feedback for stabilization.
        # Pure theta-only PID cannot stabilize it because the arm (phi) dynamics
        # are strongly coupled through the off-diagonal mass matrix term m·r·l·cos(θ).
        arm_position_gain = 3.0   # ≈ |K[0,2]| from default LQR
        arm_damping_gain = 5.0    # ≈ |K[0,3]| from default LQR

        def pid_rhs(t, z):
            theta_v, theta_dot_v, phi_v, phi_dot_v, ie = z
            error = theta_v
            # PID + arm feedback
            u = (Kp * error + Ki * ie + Kd * theta_dot_v
                 + arm_position_gain * phi_v + arm_damping_gain * phi_dot_v)
            u = np.clip(u, -self.TORQUE_LIMIT, self.TORQUE_LIMIT)
            dxdt = self._compute_dynamics(
                np.array([theta_v, theta_dot_v, phi_v, phi_dot_v]),
                u, mass, l, r, I_p, I_r)
            # Integral of error with anti-windup
            die = error if abs(ie) < self.INTEGRAL_LIMIT else 0.0
            return [dxdt[0], dxdt[1], dxdt[2], dxdt[3], die]

        z0 = [x0[0], x0[1], x0[2], x0[3], 0.0]
        t_eval = np.linspace(0, self.SIMULATION_TIME, self.NUM_STEPS)
        sol = solve_ivp(pid_rhs, [0, self.SIMULATION_TIME], z0,
                        method='RK45', t_eval=t_eval,
                        rtol=1e-8, atol=1e-10, max_step=0.01)

        if not sol.success:
            # Retry with stiff solver
            sol = solve_ivp(pid_rhs, [0, self.SIMULATION_TIME], z0,
                            method='LSODA', t_eval=t_eval,
                            rtol=1e-6, atol=1e-8)

        n_pts = len(sol.t)
        self._time = sol.t
        self._theta = sol.y[0]
        self._theta_dot = sol.y[1]
        self._phi = sol.y[2]
        self._phi_dot = sol.y[3]

        # Reconstruct torque
        self._torque = np.zeros(n_pts)
        for i in range(n_pts):
            ie_val = sol.y[4, i]
            self._torque[i] = np.clip(
                Kp * self._theta[i] + Ki * ie_val + Kd * self._theta_dot[i]
                + arm_position_gain * self._phi[i] + arm_damping_gain * self._phi_dot[i],
                -self.TORQUE_LIMIT, self.TORQUE_LIMIT)

        # Build 3D trajectory from result
        self._arm_positions = []
        self._pendulum_positions = []
        self._velocities = []
        self._energies = []
        self._angular_velocities = []

        for i in range(n_pts):
            theta_v = self._theta[i]
            phi_v = self._phi[i]
            theta_dot_v = self._theta_dot[i]
            phi_dot_v = self._phi_dot[i]

            arm_x = r * np.cos(phi_v)
            arm_y = r * np.sin(phi_v)
            perp_x = -np.sin(phi_v)
            perp_y = np.cos(phi_v)
            pend_x = arm_x + l * np.sin(theta_v) * perp_x
            pend_y = arm_y + l * np.sin(theta_v) * perp_y
            pend_z = l * np.cos(theta_v)

            self._arm_positions.append([float(arm_x), float(arm_y), 0.0])
            self._pendulum_positions.append([float(pend_x), float(pend_y), float(pend_z)])

            if i > 0:
                prev = self._pendulum_positions[-2]
                dt_val = max(sol.t[i] - sol.t[i - 1], 1e-6)
                vel_x = (pend_x - prev[0]) / dt_val
                vel_y = (pend_y - prev[1]) / dt_val
                vel_z = (pend_z - prev[2]) / dt_val
                speed = np.sqrt(vel_x**2 + vel_y**2 + vel_z**2)
            else:
                vel_x, vel_y, vel_z, speed = 0.0, 0.0, 0.0, 0.0
            self._velocities.append([float(vel_x), float(vel_y), float(vel_z), float(speed)])

            # Energy from mass matrix
            I_p_loc = mass * l**2 / 3.0
            ARM_M = 0.15
            I_r_loc = ARM_M * r**2 / 3.0
            M11_ = I_p_loc + mass * l**2
            M12_ = mass * r * l * np.cos(theta_v)
            M22_ = I_r_loc + mass * r**2 + mass * l**2 * np.sin(theta_v)**2
            ke = 0.5 * (M11_ * theta_dot_v**2 + 2 * M12_ * theta_dot_v * phi_dot_v + M22_ * phi_dot_v**2)
            pe = mass * self.G * l * np.cos(theta_v)
            self._energies.append(float(ke + pe))
            self._angular_velocities.append([float(theta_dot_v), float(phi_dot_v)])

        self._current_arm_pos = self._arm_positions[-1] if self._arm_positions else [0, 0, 0]
        self._current_pendulum_pos = self._pendulum_positions[-1] if self._pendulum_positions else [0, 0, 0.3]

        # Stability metrics
        self._peak_angle = float(np.max(np.abs(self._theta)))
        self._peak_angle_deg = float(np.degrees(self._peak_angle))
        last_samples = min(200, n_pts)
        self._is_stable = np.all(np.abs(self._theta[-last_samples:]) < np.radians(5))
        if self._peak_angle > np.radians(90):
            self._is_stable = False

        within_tolerance = np.abs(self._theta) < np.radians(5)
        self._settling_time = None
        settling_window = min(100, n_pts // 2)
        if np.any(within_tolerance) and self._is_stable and settling_window > 0:
            for i in range(len(within_tolerance) - settling_window):
                if np.all(within_tolerance[i:i + settling_window]):
                    self._settling_time = float(self._time[i])
                    break

    def _compute_dynamics(self, state: np.ndarray, torque: float,
                          mass: float, l: float, r: float,
                          I_p: float, I_r: float) -> np.ndarray:
        """
        Compute state derivatives using full Euler-Lagrange mass matrix formulation.

        Derived from the Lagrangian L = T - V for a rotary inverted pendulum.
        State: [theta, theta_dot, phi, phi_dot]
          theta: pendulum angle from upright (0 = up)
          phi: arm rotation angle (horizontal plane)

        Mass matrix M(q):
          M11 = I_p + m·l²        (pendulum inertia about pivot)
          M12 = m·r·l·cos(theta)  (coupling: arm ↔ pendulum)
          M21 = M12
          M22 = I_r + m·r² + m·l²·sin²(theta)  (effective arm inertia)

        Equations: M(q)·[theta_dd, phi_dd]' = tau_gen
        Solved via 2×2 matrix inversion: [theta_dd, phi_dd]' = M⁻¹ · tau_gen

        References: Furuta (1992), Quanser SRV02 documentation,
                    Åström & Furuta (2000) "Swinging up a pendulum by energy control"
        """
        theta, theta_dot, phi, phi_dot = state

        l_safe = max(l, 0.01)
        sin_theta = np.sin(theta)
        cos_theta = np.cos(theta)

        # Mass matrix elements
        M11 = I_p + mass * l_safe**2
        M12 = mass * r * l_safe * cos_theta
        M22 = I_r + mass * r**2 + mass * l_safe**2 * sin_theta**2

        # Determinant of mass matrix (always positive for physical params)
        det_M = M11 * M22 - M12 * M12
        det_M = max(abs(det_M), 1e-10)

        # Generalized forces (RHS before M⁻¹)
        # Pendulum equation: gravity + centrifugal from arm rotation - damping
        tau_theta = (mass * self.G * l_safe * sin_theta
                     + mass * r * l_safe * sin_theta * phi_dot**2
                     - self.PENDULUM_DAMPING * theta_dot)

        # Arm equation: motor torque - Coriolis - damping
        tau_phi = (torque
                   - 2.0 * mass * l_safe**2 * sin_theta * cos_theta * theta_dot * phi_dot
                   - self.ARM_DAMPING * phi_dot)

        # Solve M·[theta_dd, phi_dd]' = [tau_theta, tau_phi]' via Cramer's rule
        theta_acc = (M22 * tau_theta - M12 * tau_phi) / det_M
        phi_acc = (-M12 * tau_theta + M11 * tau_phi) / det_M

        return np.array([theta_dot, theta_acc, phi_dot, phi_acc])

    def _integrate_rk4(self, state: np.ndarray, torque: float,
                       mass: float, l: float, r: float,
                       I_p: float, I_r: float) -> np.ndarray:
        """RK4 integration step."""
        k1 = self._compute_dynamics(state, torque, mass, l, r, I_p, I_r)
        k2 = self._compute_dynamics(state + 0.5 * self.DT * k1, torque, mass, l, r, I_p, I_r)
        k3 = self._compute_dynamics(state + 0.5 * self.DT * k2, torque, mass, l, r, I_p, I_r)
        k4 = self._compute_dynamics(state + self.DT * k3, torque, mass, l, r, I_p, I_r)

        return state + (self.DT / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)

    def _dynamics_wrapper(self, x: np.ndarray, u: np.ndarray) -> np.ndarray:
        """Wrap physics as f(x, u) for controllers.py compatibility."""
        mass = self.parameters["mass"]
        l = self.parameters["pendulum_length"]
        r = self.parameters["arm_length"]
        I_p = mass * l**2 / 3.0  # Uniform rod about pivot end
        ARM_MASS = 0.15
        I_r = ARM_MASS * r**2 / 3.0  # Uniform rod about center pivot
        torque = u[0] if len(u) > 0 else 0.0
        return self._compute_dynamics(x, torque, mass, l, r, I_p, I_r)

    def _run_with_state_feedback(self, x0, K, x_eq, u_eq):
        """Run simulation with state feedback controller via controllers.py."""
        result = simulate_state_feedback(
            self._dynamics_wrapper, x0, (0.0, self.SIMULATION_TIME),
            K, x_eq, u_eq, u_max=self.TORQUE_LIMIT, dt=self.DT)
        self._populate_from_result(result)

    def _run_with_lqg(self, x0, K, L, A, B, C, x_eq, u_eq):
        """Run simulation with LQG controller via controllers.py."""
        result = simulate_lqg(
            self._dynamics_wrapper, x0, (0.0, self.SIMULATION_TIME),
            K, L, A, B, C, x_eq, u_eq, u_max=self.TORQUE_LIMIT, dt=self.DT)
        self._populate_from_result(result)

    def _run_uncontrolled(self, x0):
        """Run simulation with no control."""
        from core.controllers import simulate_uncontrolled
        result = simulate_uncontrolled(
            self._dynamics_wrapper, x0, (0.0, self.SIMULATION_TIME),
            n_inputs=1, dt=self.DT)
        self._populate_from_result(result)

    def _populate_from_result(self, result):
        """Fill internal arrays from a controllers.py simulation result."""
        t = result["t"]
        x = result["x"]
        u = result["u"]
        n_pts = len(t)

        self._time = t
        self._theta = x[:, 0]
        self._theta_dot = x[:, 1]
        self._phi = x[:, 2]
        self._phi_dot = x[:, 3]
        self._torque = u[:, 0]

        # Rebuild 3D trajectory data
        mass = self.parameters["mass"]
        l = self.parameters["pendulum_length"]
        r = self.parameters["arm_length"]
        self._arm_positions = []
        self._pendulum_positions = []
        self._velocities = []
        self._energies = []
        self._angular_velocities = []

        for i in range(n_pts):
            theta = self._theta[i]
            phi = self._phi[i]
            theta_dot = self._theta_dot[i]
            phi_dot = self._phi_dot[i]

            arm_x = r * np.cos(phi)
            arm_y = r * np.sin(phi)
            perp_x = -np.sin(phi)
            perp_y = np.cos(phi)
            pend_x = arm_x + l * np.sin(theta) * perp_x
            pend_y = arm_y + l * np.sin(theta) * perp_y
            pend_z = l * np.cos(theta)

            self._arm_positions.append([float(arm_x), float(arm_y), 0.0])
            self._pendulum_positions.append([float(pend_x), float(pend_y), float(pend_z)])

            if i > 0:
                prev = self._pendulum_positions[-2]
                dt_val = t[i] - t[i - 1] if i > 0 else self.DT
                dt_val = max(dt_val, 1e-6)
                vel_x = (pend_x - prev[0]) / dt_val
                vel_y = (pend_y - prev[1]) / dt_val
                vel_z = (pend_z - prev[2]) / dt_val
                speed = np.sqrt(vel_x**2 + vel_y**2 + vel_z**2)
            else:
                vel_x, vel_y, vel_z, speed = 0.0, 0.0, 0.0, 0.0
            self._velocities.append([float(vel_x), float(vel_y), float(vel_z), float(speed)])

            # Energy from mass matrix (consistent with _compute_dynamics)
            I_p_loc = mass * l**2 / 3.0
            ARM_M = 0.15
            I_r_loc = ARM_M * r**2 / 3.0
            M11_ = I_p_loc + mass * l**2
            M12_ = mass * r * l * np.cos(theta)
            M22_ = I_r_loc + mass * r**2 + mass * l**2 * np.sin(theta)**2
            ke = 0.5 * (M11_ * theta_dot**2 + 2 * M12_ * theta_dot * phi_dot + M22_ * phi_dot**2)
            pe = mass * self.G * l * np.cos(theta)
            self._energies.append(float(ke + pe))
            self._angular_velocities.append([float(theta_dot), float(phi_dot)])

        self._current_arm_pos = self._arm_positions[-1] if self._arm_positions else [0, 0, 0]
        self._current_pendulum_pos = self._pendulum_positions[-1] if self._pendulum_positions else [0, 0, 0.3]

    # =========================================================================
    # Plot generation
    # =========================================================================

    def get_plots(self) -> List[Dict[str, Any]]:
        """Generate Plotly plot dictionaries."""
        if not self._initialized:
            self.initialize()

        return [
            self._create_pendulum_angle_plot(),
            self._create_control_torque_plot(),
            self._create_arm_position_plot(),
        ]

    def _create_pendulum_angle_plot(self) -> Dict[str, Any]:
        """Create pendulum angle vs time plot."""
        theta_deg = np.degrees(self._theta)
        status = "STABLE" if self._is_stable else "UNSTABLE"
        settling_info = f" | Ts={self._settling_time:.2f}s" if self._settling_time else ""

        # Calculate y-axis range with padding
        y_min = float(np.min(theta_deg))
        y_max = float(np.max(theta_deg))
        y_padding = max(10, (y_max - y_min) * 0.1)  # At least 10 degrees padding
        y_range = [min(y_min - y_padding, -10), max(y_max + y_padding, 10)]

        return {
            "id": "pendulum_angle",
            "title": f"Pendulum Angle ({status}){settling_info}",
            "plotType": "response",
            "data": [
                {
                    "x": self._time.tolist(),
                    "y": theta_deg.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "θ (pendulum)",
                    "line": {"color": self.COLORS["pendulum_angle"], "width": 2.5},
                    "hovertemplate": "t=%{x:.2f}s<br>θ=%{y:.1f}°<extra></extra>",
                },
                {
                    "x": [0, self.SIMULATION_TIME],
                    "y": [0, 0],
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Target (0°)",
                    "line": {"color": self.COLORS["reference"], "width": 2, "dash": "dash"},
                    "hoverinfo": "skip",
                },
                {
                    "x": [0, self.SIMULATION_TIME],
                    "y": [5, 5],
                    "type": "scatter",
                    "mode": "lines",
                    "name": "±5° band",
                    "line": {"color": "#64748b", "width": 1, "dash": "dot"},
                    "hoverinfo": "skip",
                },
                {
                    "x": [0, self.SIMULATION_TIME],
                    "y": [-5, -5],
                    "type": "scatter",
                    "mode": "lines",
                    "showlegend": False,
                    "line": {"color": "#64748b", "width": 1, "dash": "dot"},
                    "hoverinfo": "skip",
                },
            ],
            "layout": {
                "xaxis": {"title": "Time (s)", "range": [0, self.SIMULATION_TIME], "showgrid": True, "gridcolor": self.COLORS["grid"]},
                "yaxis": {"title": "Angle (°)", "range": y_range, "showgrid": True, "gridcolor": self.COLORS["grid"], "zeroline": True},
                "legend": {"x": 0.02, "y": 0.98, "xanchor": "left", "yanchor": "top", "bgcolor": "rgba(15, 23, 42, 0.8)"},
                "margin": {"l": 55, "r": 25, "t": 45, "b": 45},
                "uirevision": "pendulum_angle",
            },
        }

    def _create_control_torque_plot(self) -> Dict[str, Any]:
        """Create control torque vs time plot."""
        peak = float(np.max(np.abs(self._torque)))

        # Check if torque is saturating (hitting the limits)
        saturation_time = np.sum(np.abs(self._torque) >= self.TORQUE_LIMIT * 0.99) * self.DT
        is_saturating = saturation_time > 0.1  # Saturating for more than 0.1s

        # Calculate y-axis range based on actual data with padding
        y_max = max(peak * 1.2, self.TORQUE_LIMIT * 1.2, 0.1)
        y_range = [-y_max, y_max]

        # Title shows saturation info if applicable
        title = f"Control Torque (Peak: {peak:.2f} Nm)"
        if is_saturating:
            title = f"Control Torque (Peak: {peak:.2f} Nm, Saturated: {saturation_time:.1f}s)"

        return {
            "id": "control_torque",
            "title": title,
            "plotType": "response",
            "data": [
                {
                    "x": self._time.tolist(),
                    "y": self._torque.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "τ (torque)",
                    "line": {"color": self.COLORS["control_torque"], "width": 2.5},
                    "hovertemplate": "t=%{x:.2f}s<br>τ=%{y:.3f}Nm<extra></extra>",
                },
                {
                    "x": [0, self.SIMULATION_TIME],
                    "y": [0, 0],
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Zero",
                    "line": {"color": self.COLORS["reference"], "width": 1.5, "dash": "dash"},
                    "hoverinfo": "skip",
                },
                {
                    "x": [0, self.SIMULATION_TIME],
                    "y": [self.TORQUE_LIMIT, self.TORQUE_LIMIT],
                    "type": "scatter",
                    "mode": "lines",
                    "name": f"±{self.TORQUE_LIMIT} Nm limit",
                    "line": {"color": "#f87171", "width": 1.5, "dash": "dot"},
                    "hoverinfo": "skip",
                },
                {
                    "x": [0, self.SIMULATION_TIME],
                    "y": [-self.TORQUE_LIMIT, -self.TORQUE_LIMIT],
                    "type": "scatter",
                    "mode": "lines",
                    "showlegend": False,
                    "line": {"color": "#f87171", "width": 1.5, "dash": "dot"},
                    "hoverinfo": "skip",
                },
            ],
            "layout": {
                "xaxis": {"title": "Time (s)", "range": [0, self.SIMULATION_TIME], "showgrid": True, "gridcolor": self.COLORS["grid"]},
                "yaxis": {"title": "Torque (Nm)", "range": y_range, "showgrid": True, "gridcolor": self.COLORS["grid"], "zeroline": True},
                "legend": {"x": 0.02, "y": 0.98, "xanchor": "left", "yanchor": "top", "bgcolor": "rgba(15, 23, 42, 0.8)"},
                "margin": {"l": 55, "r": 25, "t": 45, "b": 45},
                "uirevision": "control_torque",
            },
        }

    def _create_arm_position_plot(self) -> Dict[str, Any]:
        """Create arm rotation angle vs time plot."""
        phi_deg = np.degrees(self._phi)
        final = float(phi_deg[-1])

        # Calculate y-axis range with padding
        y_min = float(np.min(phi_deg))
        y_max = float(np.max(phi_deg))
        y_padding = max(10, (y_max - y_min) * 0.1)  # At least 10 degrees padding
        y_range = [y_min - y_padding, y_max + y_padding]

        return {
            "id": "arm_position",
            "title": f"Arm Rotation (Final: {final:.1f}°)",
            "plotType": "response",
            "data": [
                {
                    "x": self._time.tolist(),
                    "y": phi_deg.tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "φ (arm)",
                    "line": {"color": self.COLORS["arm_rotation"], "width": 2.5},
                    "hovertemplate": "t=%{x:.2f}s<br>φ=%{y:.1f}°<extra></extra>",
                },
            ],
            "layout": {
                "xaxis": {"title": "Time (s)", "range": [0, self.SIMULATION_TIME], "showgrid": True, "gridcolor": self.COLORS["grid"]},
                "yaxis": {"title": "Angle (°)", "range": y_range, "showgrid": True, "gridcolor": self.COLORS["grid"], "zeroline": True},
                "legend": {"x": 0.02, "y": 0.98, "xanchor": "left", "yanchor": "top", "bgcolor": "rgba(15, 23, 42, 0.8)"},
                "margin": {"l": 55, "r": 25, "t": 45, "b": 45},
                "uirevision": "arm_position",
            },
        }

    def get_state(self) -> Dict[str, Any]:
        """Return current simulation state with 3D visualization data."""
        state = super().get_state()

        # Current state values
        if self._theta is not None and len(self._theta) > 0:
            theta_deg = float(np.degrees(self._theta[-1]))
            phi_deg = float(np.degrees(self._phi[-1]))
            theta_dot_deg = float(np.degrees(self._theta_dot[-1]))
            phi_dot_deg = float(np.degrees(self._phi_dot[-1]))
            torque = float(self._torque[-1])
            l = self.parameters["pendulum_length"]
            height = float(l * np.cos(self._theta[-1]))
        else:
            theta_deg = 0.0
            phi_deg = 0.0
            theta_dot_deg = 0.0
            phi_dot_deg = 0.0
            torque = 0.0
            height = self.parameters["pendulum_length"]

        # Get peak angle (with default for uninitialized state)
        peak_angle_deg = getattr(self, '_peak_angle_deg', 0.0)

        state["computed_values"] = {
            "theta_deg": round(theta_deg, 2),
            "phi_deg": round(phi_deg, 2),
            "theta_dot_deg": round(theta_dot_deg, 2),
            "phi_dot_deg": round(phi_dot_deg, 2),
            "torque": round(torque, 4),
            "height": round(height, 4),
            "is_stable": self._is_stable,
            "settling_time": self._settling_time,
            "peak_angle_deg": round(peak_angle_deg, 1),
        }

        # Sample trajectory for smooth animation (every 2nd frame = 50 FPS equivalent)
        sample_rate = 2
        sampled_arm = self._arm_positions[::sample_rate] if self._arm_positions else []
        sampled_pend = self._pendulum_positions[::sample_rate] if self._pendulum_positions else []
        sampled_vel = self._velocities[::sample_rate] if self._velocities else []
        sampled_energy = self._energies[::sample_rate] if self._energies else []
        sampled_angular_vel = self._angular_velocities[::sample_rate] if self._angular_velocities else []

        # Calculate energy statistics for normalization
        max_energy = max(self._energies) if self._energies else 1.0
        min_energy = min(self._energies) if self._energies else 0.0
        max_speed = max(v[3] for v in self._velocities) if self._velocities else 1.0

        # Sample theta and phi for dynamic info panel updates
        sampled_theta = np.degrees(self._theta[::sample_rate]).tolist() if self._theta is not None else []
        sampled_phi = np.degrees(self._phi[::sample_rate]).tolist() if self._phi is not None else []

        # 3D visualization data for Three.js frontend
        state["visualization_3d"] = {
            "current_arm_pos": self._current_arm_pos,
            "current_pendulum_pos": self._current_pendulum_pos,
            "arm_length": self.parameters["arm_length"],
            "pendulum_length": self.parameters["pendulum_length"],
            "origin": [0.0, 0.0, 0.0],
            "arm_trajectory": sampled_arm,
            "pendulum_trajectory": sampled_pend,
            "dt": self.DT * sample_rate,  # Time step for animation
            "total_time": self.SIMULATION_TIME,
            # Enhanced physics data
            "velocities": sampled_vel,  # [vx, vy, vz, speed] per frame
            "energies": sampled_energy,  # Total energy per frame
            "angular_velocities": sampled_angular_vel,  # [theta_dot, phi_dot] per frame
            "max_energy": max_energy,
            "min_energy": min_energy,
            "max_speed": max_speed,
            "torques": self._torque[::sample_rate].tolist() if self._torque is not None else [],
            # Angle data for dynamic info panel
            "theta_series": sampled_theta,  # Pendulum angle (degrees) per frame
            "phi_series": sampled_phi,  # Arm rotation (degrees) per frame
        }

        # Metadata for info panel
        ctrl_info = getattr(self, '_controller_info', {"type": "pid"})
        state["metadata"] = {
            "simulation_type": "furuta_pendulum",
            "hub_slots": self.HUB_SLOTS,
            "hub_domain": self.HUB_DOMAIN,
            "hub_dimensions": self.HUB_DIMENSIONS,
            "sticky_controls": True,
            "has_3d_visualization": True,
            "visualization_3d": state["visualization_3d"],
            "controller_info": ctrl_info,
            "metrics": {
                "is_stable": self._is_stable,
                "settling_time": round(self._settling_time, 2) if self._settling_time else None,
                "peak_angle_deg": round(peak_angle_deg, 1),
            },
            "system_info": {
                "mass": self.parameters["mass"],
                "pendulum_length": self.parameters["pendulum_length"],
                "arm_length": self.parameters["arm_length"],
                "Kp": self.parameters["Kp"],
                "Kd": self.parameters["Kd"],
                "Ki": self.parameters["Ki"],
                "theta_deg": round(theta_deg, 1),
                "phi_deg": round(phi_deg, 1),
                "theta_dot_deg": round(theta_dot_deg, 1),
                "phi_dot_deg": round(phi_dot_deg, 1),
                "torque": round(torque, 3),
                "height": round(height, 3),
                "peak_angle_deg": round(peak_angle_deg, 1),
                "is_stable": self._is_stable,
                "settling_time": round(self._settling_time, 2) if self._settling_time else None,
                "arm_direction": "CCW" if phi_dot_deg > 5 else ("CW" if phi_dot_deg < -5 else "STOPPED"),
                "torque_direction": "CCW" if torque > 0.01 else ("CW" if torque < -0.01 else "ZERO"),
            },
        }

        return state
