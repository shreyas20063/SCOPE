"""
Core numerical helpers for the RC Lowpass Filter simulator.
"""

from .signals import (  # noqa: F401
    bode_response,
    cutoff_frequency,
    simulate_rc_output,
    square_wave,
    square_wave_harmonics,
    time_vector,
)
