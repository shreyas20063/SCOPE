"""Waveform definitions and harmonic helpers."""

from __future__ import annotations

import numpy as np


def square_wave(t: np.ndarray) -> np.ndarray:
    """Return a unit-amplitude square wave with period 1."""
    t_mod = np.mod(t, 1.0)
    return np.where(t_mod < 0.5, 1.0, -1.0)


def triangle_wave(t: np.ndarray) -> np.ndarray:
    """Return a unit-amplitude triangle wave with period 1."""
    t_mod = np.mod(t, 1.0)
    return np.where(t_mod < 0.5, -1 + 4 * t_mod, 3 - 4 * t_mod)


def square_wave_harmonic(t: np.ndarray, k: int) -> np.ndarray:
    """k-th harmonic contribution for the square wave Fourier series."""
    basis = 2 * k - 1
    return (4 / np.pi) * np.sin(basis * 2 * np.pi * t) / basis


def triangle_wave_harmonic(t: np.ndarray, k: int) -> np.ndarray:
    """k-th harmonic contribution for the triangle wave Fourier series."""
    basis = 2 * k - 1
    return -(8 / np.pi**2) * np.cos(basis * 2 * np.pi * t) / (basis**2)
