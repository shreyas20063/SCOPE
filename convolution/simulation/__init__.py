"""
Simulation module for the Convolution Simulator.

This module contains higher-level simulation control and orchestration
for both continuous and discrete convolution operations.
"""

from .continuous import ContinuousSimulation
from .discrete import DiscreteSimulation
from .playback import PlaybackController

__all__ = ['ContinuousSimulation', 'DiscreteSimulation', 'PlaybackController']
