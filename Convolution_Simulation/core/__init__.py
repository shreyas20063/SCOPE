"""
Core module for convolution simulation logic.

This module contains the fundamental mathematical operations
and signal processing utilities for the convolution simulator.
"""

from .convolution import ConvolutionEngine
from .signals import SignalGenerator
from .utils import MathUtils, PlotUtils

__all__ = ['ConvolutionEngine', 'SignalGenerator', 'MathUtils', 'PlotUtils']
