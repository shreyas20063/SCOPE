"""
Signal generation and analysis helpers for the RC Lowpass Filter simulator.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np

from utils import constants


def time_vector(time_offset: float, window_seconds: float, samples: int) -> np.ndarray:
    """Return an absolute time axis."""
    return np.linspace(time_offset, time_offset + window_seconds, samples)


def square_wave(amplitude: float, frequency: float, t: np.ndarray) -> np.ndarray:
    """Generate a bipolar square wave with the given amplitude and frequency."""
    return amplitude * np.sign(np.sin(2 * np.pi * frequency * t))


def simulate_rc_output(t: np.ndarray, input_signal: np.ndarray, rc_seconds: float) -> np.ndarray:
    """Simulate the RC filter using fourth-order Runge-Kutta integration."""
    if len(t) != len(input_signal):
        raise ValueError("Time and input arrays must have matching lengths.")

    if len(t) < 2:
        return np.array(input_signal, copy=True)

    output = np.zeros_like(input_signal)
    output[0] = 0.0
    dt = t[1] - t[0]

    for i in range(1, len(t)):
        y_prev = output[i - 1]
        u_prev = input_signal[i - 1]
        u_curr = input_signal[i]

        k1 = (u_prev - y_prev) / rc_seconds
        k2 = (u_prev - (y_prev + 0.5 * dt * k1)) / rc_seconds
        k3 = (u_prev - (y_prev + 0.5 * dt * k2)) / rc_seconds
        k4 = (u_curr - (y_prev + dt * k3)) / rc_seconds

        output[i] = y_prev + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)

    return output


def bode_response(rc_seconds: float, num_points: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
    """Return the magnitude response of the RC filter in dB."""
    f_min = 10 ** constants.BODE_FREQUENCY_DECADE_RANGE[0]
    f_max = 10 ** constants.BODE_FREQUENCY_DECADE_RANGE[1]
    frequencies = np.logspace(np.log10(f_min), np.log10(f_max), num_points)
    omega = 2 * np.pi * frequencies
    magnitude = 1 / np.sqrt(1 + (omega * rc_seconds) ** 2)
    magnitude_db = 20 * np.log10(magnitude)
    return frequencies, magnitude_db


def square_wave_harmonics(fundamental_hz: float, amplitude_v: float) -> Tuple[np.ndarray, np.ndarray]:
    """Return harmonic frequencies and magnitudes for a square wave."""
    if fundamental_hz <= 0:
        return np.array([]), np.array([])

    odd_indices = np.arange(1, constants.MAX_HARMONIC_ORDER + 1, 2)
    harmonic_freqs = odd_indices * fundamental_hz
    harmonic_magnitudes = (4 * amplitude_v) / (np.pi * odd_indices)
    harmonic_db = 20 * np.log10(harmonic_magnitudes)
    return harmonic_freqs, harmonic_db


def cutoff_frequency(rc_seconds: float = constants.DEFAULT_RC_SECONDS) -> float:
    """Return the cutoff frequency for the RC filter."""
    return 1.0 / (2 * np.pi * rc_seconds)
