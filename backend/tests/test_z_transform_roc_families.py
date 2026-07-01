"""Regression tests for z_transform_roc single-sided exponential families (BUG-094).

`right_exponential` / `left_exponential` are real a^n u[n] signals. The imaginary
part of the pole must be ignored so that the plotted x[n], the time-domain title,
and H(z) stay mutually consistent (one real pole) for any pole_imag value.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from simulations.z_transform_roc import ZTransformROCSimulator


def _run(family, pole_real, pole_imag):
    sim = ZTransformROCSimulator("z_transform_roc")
    sim.initialize({"signal_family": family, "pole_real": pole_real, "pole_imag": pole_imag})
    return sim


def test_right_exponential_plots_a_pow_n():
    sim = _run("right_exponential", 0.7, 0.0)
    x = np.real(sim._x_full)
    assert np.allclose(x, [0.7 ** n for n in range(len(x))])
    assert sim._poles.shape == (1,)


def test_right_exponential_ignores_pole_imag():
    # Before BUG-094 a complex pole silently built a 2-pole conjugate system
    # (x[n] = impulse response of 1/(1 - z^-1 + 0.5z^-2)) while the label still
    # claimed a^n u[n]. It must now be the real single-pole signal a^n u[n].
    sim = _run("right_exponential", 0.5, 0.5)
    x = np.real(sim._x_full[:8])
    assert np.allclose(x, [0.5 ** n for n in range(8)])          # plotted == labeled closed form
    assert sim._poles.shape == (1,)                               # single pole, not a conjugate pair
    assert abs(sim._poles[0].imag) < 1e-12                        # real
    assert np.allclose(sim._den_coeffs, [1.0, -0.5])              # H(z) = 1/(1 - 0.5 z^-1)
    title = sim._get_signal_title()
    assert "0.5" in title and "j" not in title                   # title consistent, no complex label
    assert sim._format_hz().count("(") == 1                       # single factor, not a 2-pole product


def test_left_exponential_ignores_pole_imag():
    sim = _run("left_exponential", 0.5, 0.5)
    assert sim._poles.shape == (1,)
    assert abs(sim._poles[0].imag) < 1e-12
    assert "j" not in sim._get_signal_title()
    assert sim._format_hz().count("(") == 1
