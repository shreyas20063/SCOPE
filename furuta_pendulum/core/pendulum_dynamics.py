"""
Furuta Pendulum Physics and Dynamics Module

This module contains the mathematical model and physical equations
governing the Furuta Pendulum (Rotary Inverted Pendulum) system.

Course: Signals and Systems (EE204T)
Instructor: Prof. Ameer Mulla
Authors: Duggimpudi Shreyas Reddy, Prathamesh Nerpagar
"""

import numpy as np


class FurutaPendulumPhysics:
    """
    Handles the physical parameters and dynamics equations for the Furuta Pendulum.

    The Furuta Pendulum consists of:
    - A rotating arm that moves in the horizontal (XY) plane
    - A pendulum hanging from the end of the arm that swings vertically

    State vector: [theta, theta_dot, phi, phi_dot]
    - theta: pendulum angle from vertical (0 = upright)
    - theta_dot: pendulum angular velocity
    - phi: arm rotation angle
    - phi_dot: arm angular velocity
    """

    def __init__(self, mass=0.05, pendulum_length=0.2, arm_length=0.15):
        """
        Initialize physical parameters of the Furuta Pendulum.

        Args:
            mass: Pendulum mass in kg (default: 0.05)
            pendulum_length: Length of pendulum in meters (default: 0.2)
            arm_length: Length of rotating arm in meters (default: 0.15)
        """
        # Physical constants
        self.g = 9.81  # gravity (m/s^2)

        # Configurable parameters
        self.m = mass  # pendulum mass (kg)
        self.l = pendulum_length  # pendulum length (m)
        self.r = arm_length  # arm length (m)

        # Derived parameters
        self.I_p = self.m * self.l**2  # pendulum moment of inertia
        self.I_r = 0.01  # arm moment of inertia (base value)

        self.update_inertia()

    def update_parameters(self, mass=None, pendulum_length=None, arm_length=None):
        """
        Update physical parameters and recalculate derived quantities.

        Args:
            mass: New pendulum mass (optional)
            pendulum_length: New pendulum length (optional)
            arm_length: New arm length (optional)
        """
        if mass is not None:
            self.m = max(0.005, mass)
        if pendulum_length is not None:
            self.l = max(0.05, pendulum_length)
        if arm_length is not None:
            self.r = max(0.05, arm_length)

        self.update_inertia()

    def update_inertia(self):
        """Recalculate moments of inertia based on current parameters."""
        self.I_p = self.m * self.l**2
        self.I_r = 0.01 + 0.05 * self.m * self.r**2

    def compute_dynamics(self, state, torque):
        """
        Compute the system dynamics (state derivatives) for the Furuta Pendulum.

        This implements the equations of motion derived from Lagrangian mechanics.
        The system is nonlinear and unstable at the upright equilibrium.

        Args:
            state: State vector [theta, theta_dot, phi, phi_dot]
            torque: Control torque applied to the arm (Nm)

        Returns:
            State derivative vector [theta_dot, theta_acc, phi_dot, phi_acc]
        """
        theta, theta_dot, phi, phi_dot = state

        # Safety bounds to prevent numerical issues
        l_safe = max(self.l, 0.01)
        I_p_safe = max(self.I_p, 0.0001)
        I_r_safe = max(self.I_r, 0.0001)
        r_safe = max(self.r, 0.01)

        # Pendulum angular acceleration (simplified model)
        # Combines gravitational torque and coupling from arm rotation
        theta_acc = (self.g / l_safe) * np.sin(theta) + \
                    (torque / I_p_safe) * np.cos(theta) * r_safe / l_safe

        # Arm angular acceleration
        # Torque divided by effective rotational inertia
        phi_acc = torque / (I_r_safe + self.m * r_safe**2)

        return np.array([theta_dot, theta_acc, phi_dot, phi_acc])

    def integrate_rk4(self, state, torque, dt):
        """
        Integrate the system dynamics using 4th-order Runge-Kutta method.

        RK4 provides better accuracy than simple Euler integration while
        maintaining computational efficiency.

        Args:
            state: Current state vector
            torque: Control torque
            dt: Time step

        Returns:
            New state after time step dt
        """
        k1 = self.compute_dynamics(state, torque)
        k2 = self.compute_dynamics(state + 0.5 * dt * k1, torque)
        k3 = self.compute_dynamics(state + 0.5 * dt * k2, torque)
        k4 = self.compute_dynamics(state + dt * k3, torque)

        new_state = state + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
        return new_state

    def compute_positions_3d(self, state):
        """
        Compute 3D Cartesian positions of key points for visualization.

        Args:
            state: State vector [theta, theta_dot, phi, phi_dot]

        Returns:
            Dictionary with 3D coordinates:
            - 'arm_end': End of rotating arm (joint position)
            - 'pendulum_end': End of pendulum (mass position)
            - 'pendulum_height': Height of pendulum mass
        """
        theta, _, phi, _ = state

        # Arm end position (joint where pendulum attaches)
        arm_x = self.r * np.cos(phi)
        arm_y = self.r * np.sin(phi)
        arm_z = 0.0

        # Perpendicular direction to arm (in XY plane)
        perp_x = -np.sin(phi)
        perp_y = np.cos(phi)

        # Pendulum mass position
        pend_x = arm_x + self.l * np.sin(theta) * perp_x
        pend_y = arm_y + self.l * np.sin(theta) * perp_y
        pend_z = arm_z + self.l * np.cos(theta)

        return {
            'arm_end': (arm_x, arm_y, arm_z),
            'pendulum_end': (pend_x, pend_y, pend_z),
            'pendulum_height': pend_z
        }

    def is_stable(self, state, tolerance=0.3):
        """
        Check if pendulum is in stable upright position.

        Args:
            state: State vector
            tolerance: Angular tolerance in radians (default: 0.3 rad ≈ 17°)

        Returns:
            True if pendulum angle is within tolerance of upright
        """
        theta = state[0]
        return abs(theta) < tolerance
