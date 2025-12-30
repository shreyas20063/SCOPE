"""
Core calculation modules for the Feedback Amplifier Simulator
"""

from .calculations import (
    calculate_metrics,
    calculate_step_response,
    calculate_bode_magnitude,
    calculate_bode_phase,
    format_value
)

__all__ = [
    'calculate_metrics',
    'calculate_step_response',
    'calculate_bode_magnitude',
    'calculate_bode_phase',
    'format_value'
]
