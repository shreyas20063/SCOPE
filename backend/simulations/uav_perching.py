"""
UAV Perching Trajectory Simulator

Simulates a fixed-wing glider performing a perching maneuver by pitching up
to extreme angles of attack. Uses 2D equations of motion with flat-plate
aerodynamic fits from MIT 6.003 Lecture 10.

Governing equations:
  mẍ = -½ρV²S [C_D(α)cosγ + C_L(α)sinγ]
  mz̈ =  ½ρV²S [C_L(α)cosγ - C_D(α)sinγ] - mg

Flat-plate aero:
  C_L(α) = 2 sin(α) cos(α) = sin(2α)
  C_D(α) = 2 sin²(α) + C_D0
"""

import numpy as np
from typing import Any, Dict, List, Optional
from .base_simulator import BaseSimulator


class UAVPerchingSimulator(BaseSimulator):
    """UAV perching trajectory simulation with flat-plate aerodynamics."""

    # ── Physical constants (MIT perching glider) ──────────────────────────
    MASS = 0.08           # kg
    WING_AREA = 0.10      # m² (large flat-plate wings)
    RHO = 1.225           # kg/m³ (sea level)
    G = 9.81              # m/s²
    C_D0 = 0.02           # parasitic drag coefficient
    INERTIA = 1e-3        # kg·m² (pitch moment of inertia)
    CHORD = 0.10          # m (mean aerodynamic chord)
    C_M_ALPHA = -0.3      # pitch stiffness (stabilizing, negative)
    PITCH_BW = 40.0       # pitch rate tracking bandwidth (s⁻¹)
    RATE_GAIN = 1.2       # commanded rate multiplier (θ̇_ss = RATE_GAIN * φ̇_cmd)
    D_CG = 0.025          # m (CG forward of aero center — gravity pitch moment)
    MAX_ELEVATOR = 60.0   # max elevator deflection (deg)

    # ── Simulation settings ───────────────────────────────────────────────
    DT = 0.001            # integration time step (s)
    MAX_TIME = 3.0        # maximum simulation time (s)
    SAMPLE_RATE = 5       # save every Nth step for animation
    PERCH_X = 3.5         # perch horizontal position (m)
    PERCH_Z = 1.5         # perch height (m)
    # Graded success thresholds
    PERCH_RADIUS_GOLD = 0.05    # m — Gold: "PERCHED!"
    PERCH_SPEED_GOLD = 2.8      # m/s
    PERCH_RADIUS_SILVER = 0.20  # m — Silver: "Good landing!"
    PERCH_SPEED_SILVER = 3.5    # m/s
    PERCH_RADIUS_BRONZE = 0.50  # m — Bronze: "Close pass"
    PERCH_SPEED_BRONZE = 5.0    # m/s

    # ── Colors ────────────────────────────────────────────────────────────
    COLORS = {
        "trajectory": "#3b82f6",
        "alpha": "#14b8a6",
        "cl": "#3b82f6",
        "cd": "#ef4444",
        "speed": "#3b82f6",
        "perch": "#10b981",
        "threshold": "#ef4444",
        "capture": "#10b981",
        "grid": "rgba(148, 163, 184, 0.1)",
        "zeroline": "rgba(148, 163, 184, 0.3)",
    }

    # ── Parameter schema ──────────────────────────────────────────────────
    PARAMETER_SCHEMA = {
        "phi_dot": {
            "type": "slider", "label": "Elevator Pitch-Up Rate",
            "min": 0, "max": 300, "step": 5, "default": 100,
            "unit": "deg/s",
        },
        "initial_speed": {
            "type": "slider", "label": "Initial Speed",
            "min": 2, "max": 10, "step": 0.5, "default": 6.0,
            "unit": "m/s",
        },
        "initial_altitude": {
            "type": "slider", "label": "Initial Altitude",
            "min": 0.5, "max": 4.0, "step": 0.1, "default": 2.0,
            "unit": "m",
        },
    }

    DEFAULT_PARAMS = {
        "phi_dot": 100,
        "initial_speed": 6.0,
        "initial_altitude": 2.0,
    }

    def __init__(self, simulation_id: str):
        super().__init__(simulation_id)
        self._trajectory: Dict[str, Any] = {}
        self._result: Dict[str, Any] = {}
        self._system_info: Dict[str, Any] = {}

    # ── BaseSimulator interface ───────────────────────────────────────────

    def initialize(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.parameters = {**self.DEFAULT_PARAMS, **(params or {})}
        for name, value in self.parameters.items():
            self.parameters[name] = self._validate_param(name, value)
        self._initialized = True
        self._compute()

    def update_parameter(self, name: str, value: Any) -> Dict[str, Any]:
        if name in self.parameters:
            self.parameters[name] = self._validate_param(name, value)
            self._compute()
        return self.get_state()

    def reset(self) -> Dict[str, Any]:
        self.parameters = self.DEFAULT_PARAMS.copy()
        self._initialized = True
        self._compute()
        return self.get_state()

    # ── Aerodynamics ──────────────────────────────────────────────────────

    @staticmethod
    def _aero_cl(alpha: float) -> float:
        """Flat-plate lift coefficient: C_L = sin(2α)."""
        return np.sin(2.0 * alpha)

    @staticmethod
    def _aero_cd(alpha: float, cd0: float = 0.02) -> float:
        """Flat-plate drag coefficient: C_D = 2sin²(α) + C_D0."""
        return 2.0 * np.sin(alpha) ** 2 + cd0

    # ── Dynamics ──────────────────────────────────────────────────────────

    def _compute_derivatives(self, state: np.ndarray, phi_dot_rad: float) -> np.ndarray:
        """
        Compute state derivatives.

        State: [x, z, Vx, Vz, theta, omega, phi]
          x, z:      position (m)
          Vx, Vz:    velocity (m/s)
          theta:     pitch angle (rad)
          omega:     pitch rate (rad/s)
          phi:       elevator deflection (rad)
        """
        x, z, Vx, Vz, theta, omega, phi = state

        V = np.sqrt(Vx**2 + Vz**2)
        V_safe = max(V, 1e-6)

        gamma = np.arctan2(Vz, Vx)
        alpha = theta - gamma

        # Aerodynamic coefficients
        cl = self._aero_cl(alpha)
        cd = self._aero_cd(alpha, self.C_D0)

        # Dynamic pressure * wing area / mass
        q_S_over_m = 0.5 * self.RHO * V_safe**2 * self.WING_AREA / self.MASS

        # Translational accelerations (lecture equations)
        ax = -q_S_over_m * (cd * np.cos(gamma) + cl * np.sin(gamma))
        az = q_S_over_m * (cl * np.cos(gamma) - cd * np.sin(gamma)) - self.G

        # Pitch dynamics: rate-tracking + aero stiffness + gravity
        # θ̈ = K_bw*(GAIN*φ̇_cmd - ω) + (qSc̄/I)*C_mα*α - (mg*d_cg/I)*sin(θ)
        q_S_c = 0.5 * self.RHO * V_safe**2 * self.WING_AREA * self.CHORD
        # Rate tracking: pitch rate follows commanded rate with fast bandwidth
        rate_cmd = self.RATE_GAIN * phi_dot_rad
        rate_tracking = self.PITCH_BW * (rate_cmd - omega)
        # Aerodynamic pitch stiffness (stabilizing)
        aero_stiffness = q_S_c * self.C_M_ALPHA * alpha / self.INERTIA
        # Gravity pitch moment: CG forward → nose-down at positive θ
        gravity_pitch = -self.MASS * self.G * self.D_CG * np.sin(theta) / self.INERTIA
        theta_ddot = rate_tracking + aero_stiffness + gravity_pitch

        # Elevator rate (clipped if at limit)
        phi_max = np.radians(self.MAX_ELEVATOR)
        if abs(phi) >= phi_max and np.sign(phi_dot_rad) == np.sign(phi):
            actual_phi_dot = 0.0
        else:
            actual_phi_dot = phi_dot_rad

        return np.array([Vx, Vz, ax, az, omega, theta_ddot, actual_phi_dot])

    def _integrate_rk4(self, state: np.ndarray, phi_dot_rad: float) -> np.ndarray:
        """RK4 integration step."""
        k1 = self._compute_derivatives(state, phi_dot_rad)
        k2 = self._compute_derivatives(state + 0.5 * self.DT * k1, phi_dot_rad)
        k3 = self._compute_derivatives(state + 0.5 * self.DT * k2, phi_dot_rad)
        k4 = self._compute_derivatives(state + self.DT * k3, phi_dot_rad)
        new_state = state + (self.DT / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)

        # Clip elevator deflection
        phi_max = np.radians(self.MAX_ELEVATOR)
        new_state[6] = np.clip(new_state[6], -phi_max, phi_max)

        return new_state

    # ── Main computation ──────────────────────────────────────────────────

    def _compute(self) -> None:
        """Integrate the full trajectory and store results."""
        phi_dot_deg = self.parameters["phi_dot"]
        V0 = self.parameters["initial_speed"]
        z0 = self.parameters["initial_altitude"]
        phi_dot_rad = np.radians(phi_dot_deg)

        # Initial state: [x, z, Vx, Vz, theta, omega, phi]
        state = np.array([0.0, z0, V0, 0.0, 0.0, 0.0, 0.0])

        max_steps = int(self.MAX_TIME / self.DT)

        # Pre-allocate storage at sample rate
        max_samples = max_steps // self.SAMPLE_RATE + 1
        t_arr = np.zeros(max_samples)
        x_arr = np.zeros(max_samples)
        z_arr = np.zeros(max_samples)
        theta_arr = np.zeros(max_samples)
        alpha_arr = np.zeros(max_samples)
        gamma_arr = np.zeros(max_samples)
        speed_arr = np.zeros(max_samples)
        cl_arr = np.zeros(max_samples)
        cd_arr = np.zeros(max_samples)
        lift_arr = np.zeros(max_samples)
        drag_arr = np.zeros(max_samples)
        phi_arr = np.zeros(max_samples)

        sample_idx = 0
        closest_dist = float('inf')
        closest_frame = 0
        closest_speed = float('inf')
        termination = "timeout"
        peak_alpha = 0.0

        for step in range(max_steps):
            t = step * self.DT
            x, z, Vx, Vz, theta, omega, phi = state

            V = np.sqrt(Vx**2 + Vz**2)
            gamma = np.arctan2(Vz, Vx)
            alpha = theta - gamma
            cl = self._aero_cl(alpha)
            cd = self._aero_cd(alpha, self.C_D0)
            q = 0.5 * self.RHO * max(V, 1e-6)**2
            lift_force = q * self.WING_AREA * cl
            drag_force = q * self.WING_AREA * cd

            # Track peak alpha
            if abs(np.degrees(alpha)) > peak_alpha:
                peak_alpha = abs(np.degrees(alpha))

            # Track closest approach to perch
            dist = np.sqrt((x - self.PERCH_X)**2 + (z - self.PERCH_Z)**2)
            if dist < closest_dist:
                closest_dist = dist
                closest_frame = sample_idx
                closest_speed = V

            # Sample for animation
            if step % self.SAMPLE_RATE == 0 and sample_idx < max_samples:
                t_arr[sample_idx] = t
                x_arr[sample_idx] = x
                z_arr[sample_idx] = z
                theta_arr[sample_idx] = np.degrees(theta)
                alpha_arr[sample_idx] = np.degrees(alpha)
                gamma_arr[sample_idx] = np.degrees(gamma)
                speed_arr[sample_idx] = V
                cl_arr[sample_idx] = cl
                cd_arr[sample_idx] = cd
                lift_arr[sample_idx] = lift_force
                drag_arr[sample_idx] = drag_force
                phi_arr[sample_idx] = np.degrees(phi)
                sample_idx += 1

            # ── Termination checks ──
            if z < 0:
                termination = "crashed"
                break
            if x > self.PERCH_X + 1.5:
                termination = "overshot"
                break
            if V < 0.05 and step > 10:
                termination = "stopped"
                break

            # Integrate
            state = self._integrate_rk4(state, phi_dot_rad)

        # Trim arrays to actual length
        t_arr = t_arr[:sample_idx]
        x_arr = x_arr[:sample_idx]
        z_arr = z_arr[:sample_idx]
        theta_arr = theta_arr[:sample_idx]
        alpha_arr = alpha_arr[:sample_idx]
        gamma_arr = gamma_arr[:sample_idx]
        speed_arr = speed_arr[:sample_idx]
        cl_arr = cl_arr[:sample_idx]
        cd_arr = cd_arr[:sample_idx]
        lift_arr = lift_arr[:sample_idx]
        drag_arr = drag_arr[:sample_idx]
        phi_arr = phi_arr[:sample_idx]

        # Determine outcome (graded)
        gold = closest_dist < self.PERCH_RADIUS_GOLD and closest_speed < self.PERCH_SPEED_GOLD
        silver = closest_dist < self.PERCH_RADIUS_SILVER and closest_speed < self.PERCH_SPEED_SILVER
        bronze = closest_dist < self.PERCH_RADIUS_BRONZE and closest_speed < self.PERCH_SPEED_BRONZE
        if gold:
            grade = "gold"
            message = "PERCHED!"
        elif silver:
            grade = "silver"
            message = "Good landing!"
        elif bronze:
            grade = "bronze"
            message = "Close pass"
        elif termination == "crashed":
            grade = "fail"
            message = "Crashed!"
        elif termination == "overshot":
            grade = "fail"
            message = "Missed — too fast" if closest_speed > self.PERCH_SPEED_BRONZE else "Overshot"
        elif termination == "stopped":
            grade = "fail"
            message = "Fell short" if closest_dist > self.PERCH_RADIUS_BRONZE else "Wrong altitude"
        else:
            grade = "fail"
            message = "Timed out"
        success = grade in ("gold", "silver")

        # Store results
        self._trajectory = {
            "x": x_arr.tolist(),
            "z": z_arr.tolist(),
            "theta": theta_arr.tolist(),
            "alpha": alpha_arr.tolist(),
            "gamma": gamma_arr.tolist(),
            "speed": speed_arr.tolist(),
            "cl": cl_arr.tolist(),
            "cd": cd_arr.tolist(),
            "lift": lift_arr.tolist(),
            "drag": drag_arr.tolist(),
            "phi": phi_arr.tolist(),
            "time": t_arr.tolist(),
            "dt": self.DT * self.SAMPLE_RATE,
        }

        self._result = {
            "success": bool(success),
            "grade": grade,
            "final_distance": round(float(closest_dist), 4),
            "final_speed": round(float(closest_speed), 3),
            "closest_frame": int(closest_frame),
            "message": message,
        }

        self._system_info = {
            "mass": self.MASS,
            "wing_area": self.WING_AREA,
            "peak_alpha": round(float(peak_alpha), 1),
            "peak_speed": round(float(np.max(speed_arr)), 2) if len(speed_arr) > 0 else 0,
            "stall_occurred": bool(peak_alpha > 45.0),
            "termination_reason": termination,
        }

    # ── Plot generation ───────────────────────────────────────────────────

    def get_plots(self) -> List[Dict[str, Any]]:
        if not self._initialized:
            self.initialize()
        return [
            self._plot_trajectory(),
            self._plot_alpha(),
            self._plot_forces(),
            self._plot_speed(),
        ]

    def _base_layout(self, x_title: str, y_title: str, uid: str) -> Dict:
        fp = f"{uid}-{self.parameters['phi_dot']}-{self.parameters['initial_speed']}-{self.parameters['initial_altitude']}"
        return {
            "xaxis": {
                "title": x_title, "gridcolor": self.COLORS["grid"],
                "zerolinecolor": self.COLORS["zeroline"], "color": "#f1f5f9",
            },
            "yaxis": {
                "title": y_title, "gridcolor": self.COLORS["grid"],
                "zerolinecolor": self.COLORS["zeroline"], "color": "#f1f5f9",
                "autorange": True,
            },
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"family": "Inter, sans-serif", "size": 12, "color": "#f1f5f9"},
            "margin": {"t": 45, "r": 25, "b": 55, "l": 60},
            "showlegend": True,
            "legend": {"font": {"color": "#94a3b8"}, "bgcolor": "rgba(15,23,42,0.8)"},
            "uirevision": fp,
        }

    def _plot_trajectory(self) -> Dict[str, Any]:
        traj = self._trajectory
        layout = self._base_layout("Horizontal Distance [m]", "Height [m]", "trajectory")
        layout["yaxis"]["scaleanchor"] = "x"
        layout["yaxis"]["scaleratio"] = 1
        return {
            "id": "trajectory",
            "title": f"Flight Path — {self._result.get('message', '')}",
            "data": [
                {
                    "x": traj["x"], "y": traj["z"],
                    "type": "scatter", "mode": "lines",
                    "name": "Trajectory",
                    "line": {"color": self.COLORS["trajectory"], "width": 2.5},
                    "hovertemplate": "x=%{x:.2f}m<br>z=%{y:.2f}m<extra></extra>",
                },
                {
                    "x": [self.PERCH_X], "y": [self.PERCH_Z],
                    "type": "scatter", "mode": "markers",
                    "name": "Perch",
                    "marker": {
                        "color": self.COLORS["perch"], "size": 14,
                        "symbol": "x", "line": {"width": 3, "color": self.COLORS["perch"]},
                    },
                },
                {
                    "x": [traj["x"][0]] if traj["x"] else [],
                    "y": [traj["z"][0]] if traj["z"] else [],
                    "type": "scatter", "mode": "markers",
                    "name": "Start",
                    "marker": {"color": "#f59e0b", "size": 10, "symbol": "circle"},
                },
            ],
            "layout": layout,
        }

    def _plot_alpha(self) -> Dict[str, Any]:
        traj = self._trajectory
        layout = self._base_layout("Time [s]", "Angle of Attack [deg]", "alpha")
        t_max = traj["time"][-1] if traj["time"] else 1.0
        return {
            "id": "alpha_vs_time",
            "title": "Angle of Attack vs Time",
            "data": [
                {
                    "x": traj["time"], "y": traj["alpha"],
                    "type": "scatter", "mode": "lines",
                    "name": "α",
                    "line": {"color": self.COLORS["alpha"], "width": 2.5},
                    "hovertemplate": "t=%{x:.3f}s<br>α=%{y:.1f}°<extra></extra>",
                },
                {
                    "x": [0, t_max], "y": [45, 45],
                    "type": "scatter", "mode": "lines",
                    "name": "Stall ~45°",
                    "line": {"color": self.COLORS["threshold"], "width": 1.5, "dash": "dash"},
                    "hoverinfo": "skip",
                },
            ],
            "layout": layout,
        }

    def _plot_forces(self) -> Dict[str, Any]:
        traj = self._trajectory
        layout = self._base_layout("Time [s]", "Coefficient", "forces")
        return {
            "id": "forces_vs_time",
            "title": "Lift & Drag Coefficients vs Time",
            "data": [
                {
                    "x": traj["time"], "y": traj["cl"],
                    "type": "scatter", "mode": "lines",
                    "name": "C_L",
                    "line": {"color": self.COLORS["cl"], "width": 2.5},
                    "hovertemplate": "t=%{x:.3f}s<br>C_L=%{y:.3f}<extra></extra>",
                },
                {
                    "x": traj["time"], "y": traj["cd"],
                    "type": "scatter", "mode": "lines",
                    "name": "C_D",
                    "line": {"color": self.COLORS["cd"], "width": 2.5},
                    "hovertemplate": "t=%{x:.3f}s<br>C_D=%{y:.3f}<extra></extra>",
                },
            ],
            "layout": layout,
        }

    def _plot_speed(self) -> Dict[str, Any]:
        traj = self._trajectory
        layout = self._base_layout("Time [s]", "Speed [m/s]", "speed")
        t_max = traj["time"][-1] if traj["time"] else 1.0
        return {
            "id": "speed_vs_time",
            "title": "Speed vs Time",
            "data": [
                {
                    "x": traj["time"], "y": traj["speed"],
                    "type": "scatter", "mode": "lines",
                    "name": "|V|",
                    "line": {"color": self.COLORS["speed"], "width": 2.5},
                    "hovertemplate": "t=%{x:.3f}s<br>V=%{y:.2f}m/s<extra></extra>",
                },
                {
                    "x": [0, t_max], "y": [self.PERCH_SPEED_GOLD, self.PERCH_SPEED_GOLD],
                    "type": "scatter", "mode": "lines",
                    "name": f"Gold ≤{self.PERCH_SPEED_GOLD} m/s",
                    "line": {"color": self.COLORS["capture"], "width": 1.5, "dash": "dash"},
                    "hoverinfo": "skip",
                },
            ],
            "layout": layout,
        }

    # ── State ─────────────────────────────────────────────────────────────

    def get_state(self) -> Dict[str, Any]:
        if not self._initialized:
            self.initialize()
        return {
            "parameters": self.parameters.copy(),
            "plots": self.get_plots(),
            "metadata": {
                "simulation_type": "uav_perching",
                "sticky_controls": True,
                "trajectory": self._trajectory,
                "perch": {"x": self.PERCH_X, "z": self.PERCH_Z},
                "result": self._result,
                "system_info": self._system_info,
            },
        }
