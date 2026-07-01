"""Regression tests for nyquist_bode_comparison fixed presets (BUG-099).

The marginally_stable and high_gm_low_pm presets show no pole/zero sliders in
the catalog (fixed textbook systems, only gain K is live), but the backend read
the INVISIBLE sliders' defaults: marginally_stable built K/(s(s+2)(s+5))
(marginal at K=70) instead of the labeled K/(s(s+1)(s+2)) (marginal at K=6),
and high_gm_low_pm's zero read zero_z=1.0, cancelling the pole at s=-1 and
collapsing the system order. Both now hardcode the labeled constants.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from simulations.nyquist_bode_comparison import NyquistBodeComparisonSimulator


def _sim(preset, K):
    s = NyquistBodeComparisonSimulator("nyquist_bode_comparison")
    s.initialize({"preset": preset, "gain_K": K})
    return s


def test_marginally_stable_matches_label():
    s = _sim("marginally_stable", 1.0)
    assert np.allclose(s._den_coeffs, [1.0, 3.0, 2.0, 0.0])   # s(s+1)(s+2)
    assert "s(s + 1)(s + 2)" in s._format_tf_expression()


def test_marginally_stable_is_marginal_at_K6():
    # CL char poly s^3+3s^2+2s+K: stable K<6, jw-axis poles at K=6, unstable K>6
    for K, expect in ((5.9, "stable"), (6.0, "marginal"), (6.5, "unstable")):
        cl = np.roots([1.0, 3.0, 2.0, K])
        mx = max(cl.real)
        got = "unstable" if mx > 1e-9 else ("marginal" if mx > -1e-9 else "stable")
        assert got == expect
    # and the sim builds exactly this char poly (den + K folded into num)
    s = _sim("marginally_stable", 6.0)
    char = np.polyadd(s._den_coeffs, s._num_coeffs)
    assert np.allclose(char, [1.0, 3.0, 2.0, 6.0])


def test_high_gm_low_pm_has_no_pole_zero_cancellation():
    s = _sim("high_gm_low_pm", 1.0)
    zeros = np.roots(s._num_coeffs)
    poles = np.roots(s._den_coeffs)
    assert np.allclose(zeros, [-0.5])                          # labeled zero, not zero_z
    for z in zeros:                                            # no zero coincides with a pole
        assert np.min(np.abs(poles - z)) > 0.4
    assert "(s + 0.5)" in s._format_tf_expression()


def test_fixed_presets_ignore_invisible_sliders():
    # The catalog hides pole_a/pole_b/zero_z for these presets; moving them
    # (e.g. via a stale URL param) must not change the system.
    a = _sim("marginally_stable", 2.0)
    b = NyquistBodeComparisonSimulator("nyquist_bode_comparison")
    b.initialize({"preset": "marginally_stable", "gain_K": 2.0,
                  "pole_a": 7.0, "pole_b": 9.0, "zero_z": 3.0})
    assert np.allclose(a._den_coeffs, b._den_coeffs)
    assert np.allclose(a._num_coeffs, b._num_coeffs)
