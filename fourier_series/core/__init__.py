"""Core waveform generation and Fourier series helpers."""

from .waveforms import (
    square_wave,
    triangle_wave,
    square_wave_harmonic,
    triangle_wave_harmonic,
)
from .series import fourier_series, describe_series

__all__ = [
    "square_wave",
    "triangle_wave",
    "square_wave_harmonic",
    "triangle_wave_harmonic",
    "fourier_series",
    "describe_series",
]
