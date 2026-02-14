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

    # Damping coefficients (realistic friction)
    PENDULUM_DAMPING = 0.02  # Pendulum joint friction
    ARM_DAMPING = 0.05  # Arm bearing friction

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
        "Kp": 1,               # Proportional gain
        "Kd": 0,               # Derivative gain
        "Ki": 0.5,             # Integral gain
        "initial_angle": 15,   # Start 15 degrees from vertical
    }

    PARAMETER_SCHEMA = {
        "mass": {
            "type": "slider", "label": "Pendulum Mass",
            "min": 0.05, "max": 0.3, "step": 0.01, "default": 0.1,
            "unit": "kg", "description": "Mass at end of pendulum",
        },
        "pendulum_length": {
            "type": "slider", "label": "Pendulum Length",
            "min": 0.15, "max": 0.5, "step": 0.01, "default": 0.3,
            "unit": "m", "description": "Length of pendulum rod",
        },
        "arm_length": {
            "type": "slider", "label": "Arm Length",
            "min": 0.1, "max": 0.3, "step": 0.01, "default": 0.2,
            "unit": "m", "description": "Length of rotating arm",
        },
        "Kp": {
            "type": "slider", "label": "Kp (Proportional)",
            "min": 0, "max": 100, "step": 1, "default": 1,
            "unit": "", "description": "Proportional gain - main restoring force",
        },
        "Kd": {
            "type": "slider", "label": "Kd (Derivative)",
            "min": 0, "max": 20, "step": 0.5, "default": 0,
            "unit": "", "description": "Derivative gain - damping",
        },
        "Ki": {
            "type": "slider", "label": "Ki (Integral)",
            "min": 0, "max": 10, "step": 0.5, "default": 0.5,
            "unit": "", "description": "Integral gain - steady-state correction",
        },
        "initial_angle": {
            "type": "slider", "label": "Initial Angle",
            "min": -90, "max": 90, "step": 1, "default": 15,
            "unit": "deg", "description": "Starting pendulum angle from vertical",
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
        """Simulate pendulum dynamics with PID control."""
        mass = self.parameters["mass"]
        l = self.parameters["pendulum_length"]
        r = self.parameters["arm_length"]
        Kp = self.parameters["Kp"]
        Ki = self.parameters["Ki"]
        Kd = self.parameters["Kd"]
        initial_angle_deg = self.parameters["initial_angle"]

        # Moments of inertia
        I_p = mass * l**2  # Pendulum about pivot
        I_r = 0.005 + 0.5 * mass * r**2  # Arm + effect of pendulum mass

        # Initial state: [theta, theta_dot, phi, phi_dot]
        initial_angle = np.radians(initial_angle_deg)
        state = np.array([initial_angle, 0.0, 0.0, 0.0])

        # Storage arrays
        self._time = np.zeros(self.NUM_STEPS)
        self._theta = np.zeros(self.NUM_STEPS)
        self._theta_dot = np.zeros(self.NUM_STEPS)
        self._phi = np.zeros(self.NUM_STEPS)
        self._phi_dot = np.zeros(self.NUM_STEPS)
        self._torque = np.zeros(self.NUM_STEPS)

        # PID state
        integral_error = 0.0
        prev_error = 0.0

        # Full trajectory storage (for animation)
        self._arm_positions = []
        self._pendulum_positions = []
        self._velocities = []
        self._energies = []
        self._angular_velocities = []

        for i in range(self.NUM_STEPS):
            t = i * self.DT
            theta, theta_dot, phi, phi_dot = state

            # PID control (target: theta = 0, upright)
            error = theta
            integral_error += error * self.DT
            integral_error = np.clip(integral_error, -self.INTEGRAL_LIMIT, self.INTEGRAL_LIMIT)

            derivative_error = theta_dot  # Use actual velocity for better derivative

            # PID output with sign convention: positive torque should push pendulum back
            torque = -(Kp * error + Ki * integral_error + Kd * derivative_error)
            torque = np.clip(torque, -self.TORQUE_LIMIT, self.TORQUE_LIMIT)

            # Store values
            self._time[i] = t
            self._theta[i] = theta
            self._theta_dot[i] = theta_dot
            self._phi[i] = phi
            self._phi_dot[i] = phi_dot
            self._torque[i] = torque

            # Calculate 3D positions for visualization
            # Arm endpoint (rotates in XY plane at height 0)
            arm_x = r * np.cos(phi)
            arm_y = r * np.sin(phi)
            arm_z = 0.0

            # Pendulum swings PERPENDICULAR to arm direction
            # perp direction in XY plane
            perp_x = -np.sin(phi)
            perp_y = np.cos(phi)

            # Pendulum mass position
            # When theta=0 (upright): pendulum points straight up (+Z)
            # When theta>0: pendulum leans in the perpendicular direction
            pend_x = arm_x + l * np.sin(theta) * perp_x
            pend_y = arm_y + l * np.sin(theta) * perp_y
            pend_z = l * np.cos(theta)  # Height above arm level

            # Store positions for animation (every frame for smooth animation)
            self._arm_positions.append([float(arm_x), float(arm_y), float(arm_z)])
            self._pendulum_positions.append([float(pend_x), float(pend_y), float(pend_z)])

            # Calculate and store physics data for visualization
            # Velocity vector of pendulum mass (for visual effects)
            if i > 0:
                prev_pend = self._pendulum_positions[-2]
                vel_x = (pend_x - prev_pend[0]) / self.DT
                vel_y = (pend_y - prev_pend[1]) / self.DT
                vel_z = (pend_z - prev_pend[2]) / self.DT
                speed = np.sqrt(vel_x**2 + vel_y**2 + vel_z**2)
            else:
                vel_x, vel_y, vel_z, speed = 0.0, 0.0, 0.0, 0.0
            self._velocities.append([float(vel_x), float(vel_y), float(vel_z), float(speed)])

            # Calculate total energy (kinetic + potential)
            # Kinetic energy: 0.5 * m * v^2 + 0.5 * I * omega^2
            ke_translational = 0.5 * mass * speed**2
            ke_rotational = 0.5 * (mass * l**2) * theta_dot**2 + 0.5 * (mass * r**2) * phi_dot**2
            # Potential energy: m * g * h (relative to lowest point)
            pe = mass * self.G * (l * np.cos(theta))  # Height = l * cos(theta)
            total_energy = ke_translational + ke_rotational + pe
            self._energies.append(float(total_energy))

            # Store angular velocities
            self._angular_velocities.append([float(theta_dot), float(phi_dot)])

            # Current position (final frame)
            if i == self.NUM_STEPS - 1:
                self._current_arm_pos = [float(arm_x), float(arm_y), float(arm_z)]
                self._current_pendulum_pos = [float(pend_x), float(pend_y), float(pend_z)]

            # Integrate dynamics using RK4
            state = self._integrate_rk4(state, torque, mass, l, r, I_p, I_r)
            prev_error = error

        # Track peak angle reached during simulation
        self._peak_angle = float(np.max(np.abs(self._theta)))
        self._peak_angle_deg = float(np.degrees(self._peak_angle))

        # Check stability (within 5 degrees for last 2 seconds)
        last_samples = 200  # 2 seconds at 100 Hz
        self._is_stable = np.all(np.abs(self._theta[-last_samples:]) < np.radians(5))

        # Also mark as unstable if pendulum ever exceeds 90 degrees (fell over)
        if self._peak_angle > np.radians(90):
            self._is_stable = False

        # Find settling time (first time pendulum stays within 5° for 1 second)
        within_tolerance = np.abs(self._theta) < np.radians(5)
        self._settling_time = None
        settling_window = 100  # 1 second at 100 Hz
        if np.any(within_tolerance) and self._is_stable:
            for i in range(len(within_tolerance) - settling_window):
                if np.all(within_tolerance[i:i + settling_window]):
                    self._settling_time = self._time[i]
                    break

    def _compute_dynamics(self, state: np.ndarray, torque: float,
                          mass: float, l: float, r: float,
                          I_p: float, I_r: float) -> np.ndarray:
        """
        Compute state derivatives using proper Furuta pendulum equations.

        The dynamics are derived from Lagrangian mechanics.
        Pendulum swings perpendicular to the arm.
        """
        theta, theta_dot, phi, phi_dot = state

        # Safety bounds
        l_safe = max(l, 0.01)

        # Pendulum angular acceleration
        # Gravity restoring torque + coupling from arm rotation
        sin_theta = np.sin(theta)
        cos_theta = np.cos(theta)

        # Gravitational torque (tries to pull pendulum down)
        gravity_term = (self.G / l_safe) * sin_theta

        # Coupling from arm acceleration (torque effect on pendulum)
        # When arm accelerates, pendulum feels a reaction torque
        coupling_term = (r / l_safe) * cos_theta * (torque / (I_r + mass * r**2))

        # Centripetal effect from arm rotation
        centripetal_term = -phi_dot**2 * sin_theta * cos_theta * (r / l_safe)

        # Damping
        damping_term = -self.PENDULUM_DAMPING * theta_dot / (mass * l_safe**2)

        theta_acc = gravity_term + coupling_term + centripetal_term + damping_term

        # Arm angular acceleration
        # Effective inertia includes pendulum contribution
        I_eff = I_r + mass * r**2 * cos_theta**2
        arm_damping = -self.ARM_DAMPING * phi_dot
        phi_acc = (torque + arm_damping) / max(I_eff, 0.001)

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
        state["metadata"] = {
            "simulation_type": "furuta_pendulum",
            "sticky_controls": True,
            "has_3d_visualization": True,
            "visualization_3d": state["visualization_3d"],
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
