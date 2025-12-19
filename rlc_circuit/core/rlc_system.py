"""
RLC system modelling utilities for the interactive frequency response simulator.

Developed for the Signals and Systems (EE204T) course project under
Prof. Ameer Mulla by Duggimpudi Shreyas Reddy and Prathamesh Nerpagar.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy import signal


@dataclass
class RLCSystemParameters:
    """Container for the adjustable simulator parameters."""

    omega_0: float = 10.0
    Q: float = 1.0


@dataclass
class SystemCharacteristics:
    """Computed properties of the RLC system."""

    poles: np.ndarray
    damping_type: str
    zeta: float
    bandwidth: float
    resonant_frequency: Optional[float]
    transfer_function: signal.TransferFunction


def build_transfer_function(params: RLCSystemParameters) -> signal.TransferFunction:
    """Return the continuous-time transfer function H(s) for the series RLC circuit."""
    num = [params.omega_0**2]
    den = [1.0, params.omega_0 / params.Q, params.omega_0**2]
    return signal.TransferFunction(num, den)


def analyze_system(params: RLCSystemParameters) -> SystemCharacteristics:
    """Calculate poles, damping details, and derived metrics for the current parameters."""
    omega_0 = params.omega_0
    Q = params.Q
    zeta = 1.0 / (2.0 * Q)

    if Q > 0.5:
        real_part = -omega_0 * zeta
        imag_part = omega_0 * np.sqrt(max(0.0, 1.0 - zeta**2))
        poles = np.array(
            [complex(real_part, imag_part), complex(real_part, -imag_part)]
        )
        damping_type = "Underdamped (Complex Conjugate Poles)"
    elif np.isclose(Q, 0.5):
        repeated_pole = -omega_0 / 2.0
        poles = np.array([repeated_pole, repeated_pole])
        damping_type = "Critically Damped (Repeated Real Poles)"
    else:
        sqrt_term = np.sqrt(zeta**2 - 1.0)
        s1 = -omega_0 * (zeta + sqrt_term)
        s2 = -omega_0 * (zeta - sqrt_term)
        poles = np.array([s1, s2])
        damping_type = "Overdamped (Real Distinct Poles)"

    resonant_freq: Optional[float] = None
    if Q > 0.707:
        resonant_freq = omega_0 * np.sqrt(1.0 - 1.0 / (2.0 * Q**2))

    bandwidth = omega_0 / Q

    transfer_fn = build_transfer_function(params)

    return SystemCharacteristics(
        poles=poles,
        damping_type=damping_type,
        zeta=zeta,
        bandwidth=bandwidth,
        resonant_frequency=resonant_freq,
        transfer_function=transfer_fn,
    )


def frequency_response(
    transfer_fn: signal.TransferFunction, start_exp: float = -1.0, stop_exp: float = 4.0
) -> tuple[np.ndarray, np.ndarray]:
    """Compute the frequency response over a log-spaced grid."""
    omega = np.logspace(start_exp, stop_exp, 2000)
    _, response = signal.freqs(transfer_fn.num, transfer_fn.den, worN=omega)
    return omega, response
