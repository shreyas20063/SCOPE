"""
PID Controller Module for Furuta Pendulum

This module implements a PID (Proportional-Integral-Derivative) controller
to stabilize the inverted pendulum at the upright position.

Course: Signals and Systems (EE204T)
Instructor: Prof. Ameer Mulla
Authors: Duggimpudi Shreyas Reddy, Prathamesh Nerpagar
"""

import numpy as np


class PIDController:
    """
    PID Controller for stabilizing the Furuta Pendulum.

    The controller uses feedback from the pendulum angle and angular velocity
    to compute the control torque that keeps the pendulum upright.

    Control law:
        τ = -(Kp * error + Ki * integral + Kd * derivative)

    where error = θ (pendulum angle from vertical)
    """

    def __init__(self, kp=150.0, kd=25.0, ki=5.0, dt=0.01):
        """
        Initialize PID controller with specified gains.

        Args:
            kp: Proportional gain (default: 150.0)
            kd: Derivative gain (default: 25.0)
            ki: Integral gain (default: 5.0)
            dt: Time step for integration (default: 0.01)
        """
        self.Kp = kp
        self.Kd = kd
        self.Ki = ki
        self.dt = dt

        # Integral error accumulator
        self.integral_error = 0.0

        # Control limits
        self.torque_limit = 10.0  # Maximum torque in Nm
        self.integral_limit = 1.0  # Anti-windup limit

    def update_gains(self, kp=None, kd=None, ki=None):
        """
        Update PID gains.

        Args:
            kp: New proportional gain (optional)
            kd: New derivative gain (optional)
            ki: New integral gain (optional)
        """
        if kp is not None:
            self.Kp = kp
        if kd is not None:
            self.Kd = kd
        if ki is not None:
            self.Ki = ki

    def compute_control(self, state):
        """
        Compute control torque based on current state.

        Args:
            state: State vector [theta, theta_dot, phi, phi_dot]

        Returns:
            Control torque in Nm (clipped to limits)
        """
        theta = state[0]  # Pendulum angle error (deviation from upright)
        theta_dot = state[1]  # Pendulum angular velocity

        # Proportional term: responds to current error
        error = theta

        # Integral term: accumulates past errors (with anti-windup)
        self.integral_error += error * self.dt
        self.integral_error = np.clip(self.integral_error,
                                       -self.integral_limit,
                                       self.integral_limit)

        # Derivative term: uses angular velocity directly
        derivative = theta_dot

        # Compute total control signal
        # Negative sign because we want to push opposite to the error
        torque = -(self.Kp * error + self.Ki * self.integral_error + self.Kd * derivative)

        # Apply saturation limits
        torque = float(np.clip(torque, -self.torque_limit, self.torque_limit))

        return torque

    def reset(self):
        """Reset the controller state (clears integral error)."""
        self.integral_error = 0.0

    def get_control_components(self, state):
        """
        Get individual PID components for analysis/debugging.

        Args:
            state: State vector [theta, theta_dot, phi, phi_dot]

        Returns:
            Dictionary with:
            - 'proportional': P term
            - 'integral': I term
            - 'derivative': D term
            - 'total': Total control signal (before clipping)
            - 'output': Actual output (after clipping)
        """
        theta = state[0]
        theta_dot = state[1]

        p_term = -self.Kp * theta
        i_term = -self.Ki * self.integral_error
        d_term = -self.Kd * theta_dot

        total = p_term + i_term + d_term
        output = float(np.clip(total, -self.torque_limit, self.torque_limit))

        return {
            'proportional': p_term,
            'integral': i_term,
            'derivative': d_term,
            'total': total,
            'output': output
        }
