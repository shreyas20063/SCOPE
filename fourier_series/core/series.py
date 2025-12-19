"""Computation and descriptive helpers for Fourier series expansions."""

from __future__ import annotations

from typing import Literal, Tuple

import numpy as np

from .waveforms import square_wave_harmonic, triangle_wave_harmonic

WaveType = Literal["Square Wave", "Triangle Wave"]


def fourier_series(t: np.ndarray, n: int, wave_type: WaveType) -> np.ndarray:
    """Return the truncated Fourier series approximation for the requested wave."""
    result = np.zeros_like(t)
    harmonic_fn = square_wave_harmonic if wave_type == "Square Wave" else triangle_wave_harmonic
    for k in range(1, n + 1):
        result += harmonic_fn(t, k)
    return result


def describe_series(n: int, wave_type: WaveType) -> Tuple[str, str, str]:
    """Return shorthand descriptions of the Fourier series in LaTeX-friendly strings."""
    window_size = 3
    half_window = window_size // 2
    start_k = max(1, n - half_window)
    end_k = min(n + half_window, n)

    if n <= half_window:
        start_k = 1
        end_k = min(window_size, n)
    elif n == 1:
        start_k = 1
        end_k = 1
    else:
        start_k = max(1, n - 1)
        end_k = n

    if wave_type == "Square Wave":
        formula_main = (
            r"$f(t) = \frac{{4}}{{\pi}} \sum_{{k=1}}^{{{}}}"
            r" \frac{{\sin((2k-1) \cdot 2\pi t)}}{{2k-1}}$".format(n)
        )

        terms = []
        if start_k > 1:
            terms.append(r"\cdots")

        for k in range(start_k, end_k + 1):
            coef = 4 / (np.pi * (2 * k - 1))
            harm = 2 * k - 1
            terms.append("{:.3f}\\sin({} \\cdot 2\\pi t)".format(coef, harm))

        if end_k < n:
            terms.append(r"\cdots")

        expanded = " + ".join(terms)
        expanded = r"$f(t) \approx {}$".format(expanded)
        properties = r"Decay: $\mathcal{{O}}(1/n)$ | Gibbs: $\sim$9% overshoot"
    else:
        formula_main = (
            r"$f(t) = -\frac{{8}}{{\pi^2}} \sum_{{k=1}}^{{{}}}"
            r" \frac{{\cos((2k-1) \cdot 2\pi t)}}{{(2k-1)^2}}$".format(n)
        )

        terms = []
        if start_k > 1:
            terms.append(r"\cdots")

        for k in range(start_k, end_k + 1):
            coef = -8 / (np.pi**2 * (2 * k - 1) ** 2)
            harm = 2 * k - 1
            if coef >= 0:
                terms.append("+{:.3f}\\cos({} \\cdot 2\\pi t)".format(coef, harm))
            else:
                terms.append("{:.3f}\\cos({} \\cdot 2\\pi t)".format(coef, harm))

        if end_k < n:
            terms.append(r"\cdots")

        expanded = " ".join(terms).replace("+ -", "- ").replace("+-", "-")
        expanded = r"$f(t) \approx {}$".format(expanded)
        properties = r"Decay: $\mathcal{{O}}(1/n^2)$ | Fast Convergence"

    return formula_main, expanded, properties
