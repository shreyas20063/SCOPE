"""
GUI Components for Lens Simulation
===================================

PyQt5-based graphical user interface components.

Modules:
--------
- main_window: Main application window
- control_widgets: Parameter and image control widgets
- results_display: Results visualization and display components
"""

from .main_window import MainWindow, SimulationWorker
from .control_widgets import ParameterControls, ImageControls, AdvancedControls
from .results_display import ResultsDisplay

__all__ = [
    'MainWindow',
    'SimulationWorker',
    'ParameterControls',
    'ImageControls',
    'AdvancedControls',
    'ResultsDisplay'
]
