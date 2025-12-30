"""
GUI module for DC Motor Simulation
Contains PyQt5 interface components
"""

from .main_window import MainWindow
from .control_panel import ControlPanel
from .plot_canvas import PlotCanvas

__all__ = ['MainWindow', 'ControlPanel', 'PlotCanvas']
