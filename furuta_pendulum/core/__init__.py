"""
Core modules for Furuta Pendulum Simulation.

This package contains the physics model and control system implementation.

Course: Signals and Systems (EE204T)
Instructor: Prof. Ameer Mulla
Authors: Duggimpudi Shreyas Reddy, Prathamesh Nerpagar
"""

from .pendulum_dynamics import FurutaPendulumPhysics
from .pid_controller import PIDController

__all__ = ['FurutaPendulumPhysics', 'PIDController']
